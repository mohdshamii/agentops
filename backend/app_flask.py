import os
import sys
import json
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import get_settings
from app.database import SessionLocal, init_db
from app.models import Conversation, Message
from app.adapters.factory import ModelAdapterFactory
from app.intelligence.prompts import PromptEngineeringSystem
from app.intelligence.reasoning import ReasoningEngine
from app.tools.registry import global_tool_registry
from app.memory.memory_manager import global_memory_manager
from app.agents.multi_agent import global_multi_agent_team
from app.workflows.autonomous import global_workflow_engine
from app.utils.logger import logger

settings = get_settings()

def create_app():
    app = Flask(__name__)
    CORS(app, origins=settings.ALLOWED_ORIGINS)

    # Initialize DB tables
    with app.app_context():
        init_db()

    reasoning_engine = ReasoningEngine(max_iterations=4)

    # --- Health & Models Endpoints ---
    @app.route("/health/", methods=["GET"])
    def health():
        return jsonify({
            "status": "healthy",
            "backend": "Flask",
            "version": settings.API_VERSION,
            "models": ModelAdapterFactory.list_all_models(),
            "default_model": settings.HF_DEFAULT_MODEL
        })

    @app.route("/api/models/", methods=["GET"])
    def list_models():
        return jsonify(ModelAdapterFactory.list_all_models())

    # --- Chat Endpoint (Synchronous) ---
    @app.route("/api/chat/send", methods=["POST"])
    def chat_send():
        data = request.get_json() or {}
        user_message = data.get("message", "").strip()
        conv_id = data.get("conversation_id")
        selected_model = data.get("model") or settings.HF_DEFAULT_MODEL
        persona = data.get("persona") or "assistant"
        enable_reasoning = data.get("enable_reasoning", True)
        enable_tools = data.get("enable_tools", True)

        if not user_message:
            return jsonify({"error": "Message cannot be empty"}), 400

        with SessionLocal() as db:
            # Create or fetch conversation
            if conv_id:
                conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
                if not conv:
                    conv = Conversation(id=conv_id, title=user_message[:30] + "...")
                    db.add(conv)
                    db.commit()
            else:
                conv_id = str(uuid.uuid4())
                conv = Conversation(id=conv_id, title=user_message[:30] + "...")
                db.add(conv)
                db.commit()

            # Record user message
            user_msg = Message(
                id=str(uuid.uuid4()),
                conversation_id=conv_id,
                role="user",
                content=user_message,
                created_at=datetime.utcnow()
            )
            db.add(user_msg)
            conv.updated_at = datetime.utcnow()
            db.commit()

            # Retrieve context & vector memories
            history_messages = [
                {"role": m.role, "content": m.content}
                for m in conv.messages[:-1]
            ]
            memory_bundle = global_memory_manager.retrieve_context_and_memories(
                query=user_message,
                history=history_messages,
                system_prompt=""
            )
            relevant_memories = memory_bundle["relevant_memories"]

            # Prompt Construction
            tools_desc = global_tool_registry.get_tools_description_for_prompt() if enable_tools else ""
            tool_names = global_tool_registry.get_tool_names() if enable_tools else ""

            system_prompt = PromptEngineeringSystem.build_system_prompt(
                persona=persona,
                tools_description=tools_desc,
                tool_names=tool_names,
                relevant_memories=relevant_memories,
                enable_reasoning=enable_reasoning
            )

            # Resolve Adapter
            adapter = ModelAdapterFactory.get_adapter(model=selected_model)

            # Execution
            trace = []
            tool_calls = []
            final_text = ""
            tokens_used = 0

            if enable_reasoning and enable_tools:
                exec_res = reasoning_engine.execute_react_loop(
                    llm_fn=lambda msgs: adapter.generate(msgs, model=selected_model),
                    system_prompt=system_prompt,
                    user_message=user_message,
                    tool_executor_fn=global_tool_registry.execute,
                    conversation_history=history_messages[-6:]
                )
                final_text = exec_res["final_answer"]
                trace = exec_res["reasoning_trace"]
                tool_calls = exec_res["tool_calls"]
                tokens_used = exec_res["tokens_used"]
            else:
                messages = [{"role": "system", "content": system_prompt}] + history_messages[-6:] + [{"role": "user", "content": user_message}]
                gen_res = adapter.generate(messages, model=selected_model)
                final_text = gen_res["content"]
                tokens_used = gen_res.get("tokens_used", 0)

            # Store assistant response
            assistant_msg = Message(
                id=str(uuid.uuid4()),
                conversation_id=conv_id,
                role="assistant",
                content=final_text,
                reasoning_trace=json.dumps(trace) if trace else None,
                tool_calls=json.dumps(tool_calls) if tool_calls else None,
                tokens_used=tokens_used,
                created_at=datetime.utcnow()
            )
            db.add(assistant_msg)
            conv.updated_at = datetime.utcnow()
            db.commit()

            return jsonify({
                "conversation_id": conv_id,
                "message_id": assistant_msg.id,
                "response": final_text,
                "reasoning_trace": trace,
                "tool_calls": tool_calls,
                "tokens_used": tokens_used,
                "model": selected_model,
                "timestamp": datetime.utcnow().isoformat()
            })

    # --- Chat Endpoint (SSE Streaming) ---
    @app.route("/api/chat/stream", methods=["POST"])
    def chat_stream():
        data = request.get_json() or {}
        user_message = data.get("message", "").strip()
        conv_id = data.get("conversation_id")
        selected_model = data.get("model") or settings.HF_DEFAULT_MODEL
        persona = data.get("persona") or "assistant"

        def generate_events():
            with SessionLocal() as db:
                nonlocal conv_id
                if conv_id:
                    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
                else:
                    conv_id = str(uuid.uuid4())
                    conv = Conversation(id=conv_id, title=user_message[:30] + "...")
                    db.add(conv)
                    db.commit()

                user_msg = Message(
                    id=str(uuid.uuid4()),
                    conversation_id=conv_id,
                    role="user",
                    content=user_message,
                    created_at=datetime.utcnow()
                )
                db.add(user_msg)
                db.commit()

                yield f"data: {json.dumps({'type': 'init', 'conversation_id': conv_id, 'message_id': user_msg.id})}\n\n"

                adapter = ModelAdapterFactory.get_adapter(model=selected_model)
                system_prompt = PromptEngineeringSystem.build_system_prompt(persona=persona)

                # Execute ReAct loop
                exec_res = reasoning_engine.execute_react_loop(
                    llm_fn=lambda msgs: adapter.generate(msgs, model=selected_model),
                    system_prompt=system_prompt,
                    user_message=user_message,
                    tool_executor_fn=global_tool_registry.execute
                )

                if exec_res.get("reasoning_trace"):
                    yield f"data: {json.dumps({'type': 'reasoning_trace', 'trace': exec_res['reasoning_trace']})}\n\n"

                # Stream response tokens
                words = exec_res["final_answer"].split(" ")
                for i, w in enumerate(words):
                    chunk = w if i == 0 else " " + w
                    yield f"data: {json.dumps({'type': 'token', 'token': chunk})}\n\n"

                # Save assistant record
                asst_msg = Message(
                    id=str(uuid.uuid4()),
                    conversation_id=conv_id,
                    role="assistant",
                    content=exec_res["final_answer"],
                    reasoning_trace=json.dumps(exec_res["reasoning_trace"]) if exec_res.get("reasoning_trace") else None,
                    tool_calls=json.dumps(exec_res["tool_calls"]) if exec_res.get("tool_calls") else None,
                    tokens_used=exec_res["tokens_used"],
                    created_at=datetime.utcnow()
                )
                db.add(asst_msg)
                db.commit()

                yield f"data: {json.dumps({'type': 'done', 'tokens_used': exec_res['tokens_used'], 'model': selected_model})}\n\n"

        return Response(stream_with_context(generate_events()), mimetype="text/event-stream")

    # --- Conversations Endpoints ---
    @app.route("/api/conversations/", methods=["GET"])
    def get_conversations():
        with SessionLocal() as db:
            convs = db.query(Conversation).order_by(Conversation.updated_at.desc()).all()
            result = []
            for c in convs:
                msgs = []
                for m in c.messages:
                    r_trace = None
                    t_calls = None
                    if m.reasoning_trace:
                        try:
                            r_trace = json.loads(m.reasoning_trace)
                        except Exception:
                            r_trace = m.reasoning_trace
                    if m.tool_calls:
                        try:
                            t_calls = json.loads(m.tool_calls)
                        except Exception:
                            t_calls = m.tool_calls
                    msgs.append({
                        "id": m.id,
                        "conversation_id": m.conversation_id,
                        "role": m.role,
                        "content": m.content,
                        "reasoning_trace": r_trace,
                        "tool_calls": t_calls,
                        "tokens_used": m.tokens_used,
                        "created_at": m.created_at.isoformat()
                    })
                result.append({
                    "id": c.id,
                    "title": c.title,
                    "created_at": c.created_at.isoformat(),
                    "updated_at": c.updated_at.isoformat(),
                    "messages": msgs
                })
            return jsonify(result)

    @app.route("/api/conversations/<conv_id>", methods=["GET"])
    def get_conversation(conv_id):
        with SessionLocal() as db:
            c = db.query(Conversation).filter(Conversation.id == conv_id).first()
            if not c:
                return jsonify({"error": "Conversation not found"}), 404
            msgs = []
            for m in c.messages:
                r_trace = json.loads(m.reasoning_trace) if m.reasoning_trace else None
                t_calls = json.loads(m.tool_calls) if m.tool_calls else None
                msgs.append({
                    "id": m.id,
                    "conversation_id": m.conversation_id,
                    "role": m.role,
                    "content": m.content,
                    "reasoning_trace": r_trace,
                    "tool_calls": t_calls,
                    "tokens_used": m.tokens_used,
                    "created_at": m.created_at.isoformat()
                })
            return jsonify({
                "id": c.id,
                "title": c.title,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat(),
                "messages": msgs
            })

    @app.route("/api/conversations/create", methods=["POST"])
    def create_conv():
        with SessionLocal() as db:
            new_id = str(uuid.uuid4())
            conv = Conversation(id=new_id, title="New Conversation")
            db.add(conv)
            db.commit()
            return jsonify({
                "id": conv.id,
                "title": conv.title,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
                "messages": []
            })

    @app.route("/api/conversations/<conv_id>", methods=["DELETE"])
    def delete_conv(conv_id):
        with SessionLocal() as db:
            c = db.query(Conversation).filter(Conversation.id == conv_id).first()
            if c:
                db.delete(c)
                db.commit()
                return jsonify({"status": "success", "message": f"Deleted {conv_id}"})
            return jsonify({"error": "Not found"}), 404

    # --- Tools Endpoints ---
    @app.route("/api/tools/", methods=["GET"])
    def list_tools():
        return jsonify(global_tool_registry.list_tools())

    @app.route("/api/tools/execute", methods=["POST"])
    def execute_tool():
        data = request.get_json() or {}
        tool_name = data.get("tool_name")
        params = data.get("params", {})
        res = global_tool_registry.execute(tool_name, params)
        status = "error" if isinstance(res, dict) and res.get("status") == "error" else "success"
        return jsonify({
            "tool_name": tool_name,
            "status": status,
            "result": res
        })

    # --- Memory Endpoints ---
    @app.route("/api/memory/", methods=["GET"])
    def get_memories():
        return jsonify(global_memory_manager.list_all_memories())

    @app.route("/api/memory/create", methods=["POST"])
    def add_memory():
        data = request.get_json() or {}
        content = data.get("content", "")
        category = data.get("category", "general")
        res = global_memory_manager.store_user_fact(content, category=category)
        return jsonify({"status": "success", "memory": res})

    @app.route("/api/memory/search", methods=["POST"])
    def search_mem():
        data = request.get_json() or {}
        q = data.get("query", "")
        top_k = data.get("top_k", 4)
        matches = global_memory_manager.search_memories(q, top_k=top_k)
        return jsonify({"query": q, "count": len(matches), "matches": matches})

    # --- Multi-Agent Swarm Endpoints ---
    @app.route("/api/agents/team", methods=["GET"])
    def get_agents():
        roles = [
            {"id": k, "name": a.name, "role": a.role_title, "persona": a.persona, "allowed_tools": a.allowed_tools}
            for k, a in global_multi_agent_team.agents.items()
        ]
        return jsonify({"status": "ready", "agents": roles})

    @app.route("/api/agents/run", methods=["POST"])
    def run_agent():
        data = request.get_json() or {}
        task = data.get("task", "")
        roles = data.get("agent_roles")
        res = global_multi_agent_team.execute_team_task(task, active_roles=roles)
        return jsonify(res)

    # --- Workflows Endpoints ---
    @app.route("/api/workflows/", methods=["GET"])
    def get_workflows():
        from app.models import WorkflowExecution
        with SessionLocal() as db:
            wfs = db.query(WorkflowExecution).order_by(WorkflowExecution.created_at.desc()).all()
            return jsonify([{
                "id": w.id,
                "title": w.title,
                "goal": w.goal,
                "status": w.status,
                "plan": json.loads(w.plan_json) if w.plan_json else [],
                "results": json.loads(w.results_json) if w.results_json else [],
                "final_output": w.final_output,
                "created_at": w.created_at.isoformat(),
                "updated_at": w.updated_at.isoformat()
            } for w in wfs])

    @app.route("/api/workflows/create", methods=["POST"])
    def create_wf():
        data = request.get_json() or {}
        title = data.get("title", "Autonomous Goal Workflow")
        goal = data.get("goal", "")
        return jsonify(global_workflow_engine.create_workflow(title=title, goal=goal))

    @app.route("/api/workflows/<wf_id>/run", methods=["POST"])
    def run_wf(wf_id):
        return jsonify(global_workflow_engine.run_workflow(wf_id))

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("FLASK_PORT", 8000))
    logger.info(f"Starting AgentOps Flask Server on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=True)
