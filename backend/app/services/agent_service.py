import json
import uuid
from typing import Dict, Any, List, Optional, Generator
from sqlalchemy.orm import Session
from datetime import datetime
from app.intelligence.huggingface_llm import HuggingFaceLLMService
from app.intelligence.prompts import PromptEngineeringSystem
from app.intelligence.reasoning import ReasoningEngine
from app.tools.registry import global_tool_registry
from app.memory.memory_manager import global_memory_manager
from app.services.conversation_service import ConversationService
from app.services.vision_service import global_vision_service
from app.services.voice_service import global_voice_service
from app.models import Message
from app.utils.logger import logger

class AgentService:
    """
    Master Agent Orchestrator.
    Combines Prompt Engineering, Multi-Step Reasoning, External Tools,
    Dual Memory, Voice/Vision, and DB persistence.
    """

    def __init__(self):
        self.llm = HuggingFaceLLMService()
        self.reasoning_engine = ReasoningEngine(max_iterations=4)
        self.tools = global_tool_registry
        self.memory = global_memory_manager
        self.vision = global_vision_service
        self.voice = global_voice_service

    def process_chat_message(
        self,
        db: Session,
        message: str,
        conversation_id: Optional[str] = None,
        model: Optional[str] = None,
        persona: str = "assistant",
        enable_reasoning: bool = True,
        enable_tools: bool = True,
        image_base64: Optional[str] = None,
        audio_base64: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes complete agent lifecycle for a user message.
        """
        # 1. Handle Voice Input (Speech-to-Text)
        effective_message = message
        if audio_base64:
            voice_result = self.voice.transcribe_audio(audio_base64)
            if voice_result.get("transcription"):
                effective_message = f"{voice_result['transcription']} ({message})".strip()

        # 2. Handle Vision Input (Image Captioning & Context)
        vision_context = ""
        if image_base64:
            vision_analysis = self.vision.analyze_image(image_base64=image_base64, prompt=effective_message)
            vision_context = f"\n[User attached an image. Visual analysis: {vision_analysis.get('description', '')}]\n"
            effective_message = f"{effective_message}\n{vision_context}"

        # 3. Create or Fetch Conversation
        if conversation_id:
            conversation = ConversationService.get_conversation(db, conversation_id)
        else:
            first_words = " ".join(effective_message.split()[:4])
            title = f"Chat: {first_words}..." if first_words else "New Conversation"
            conversation = ConversationService.create_conversation(db, title=title)

        # 4. Save User Message to Database
        ConversationService.add_message(db, conversation.id, "user", effective_message)

        # 5. Retrieve Short-term Context and Long-term Vector Memories
        history = ConversationService.get_conversation_history(db, conversation.id)
        
        # Tools configuration for prompt
        tools_desc = self.tools.get_tools_description_for_prompt() if enable_tools else ""
        tool_names = self.tools.get_tool_names() if enable_tools else ""

        memory_bundle = self.memory.retrieve_context_and_memories(
            query=effective_message,
            history=history,
            system_prompt=""
        )
        relevant_memories = memory_bundle["relevant_memories"]
        pruned_history = memory_bundle["pruned_history"]

        # 6. Build Dynamic System Prompt with Persona & Memories
        system_prompt = PromptEngineeringSystem.build_system_prompt(
            persona=persona,
            tools_description=tools_desc,
            tool_names=tool_names,
            relevant_memories=relevant_memories,
            enable_reasoning=enable_reasoning
        )

        selected_model = model or self.llm.default_model

        # 7. Execute Multi-step Reasoning / ReAct or Direct Generation
        reasoning_trace = []
        tool_calls = []
        tokens_used = 0
        final_response_text = ""

        if enable_reasoning and enable_tools:
            exec_result = self.reasoning_engine.execute_react_loop(
                llm_fn=lambda msgs: self.llm.generate_chat_completion(msgs, model=selected_model),
                system_prompt=system_prompt,
                user_message=effective_message,
                tool_executor_fn=self.tools.execute,
                conversation_history=pruned_history[:-1]  # exclude current user msg since passed separately
            )
            final_response_text = exec_result["final_answer"]
            reasoning_trace = exec_result["reasoning_trace"]
            tool_calls = exec_result["tool_calls"]
            tokens_used = exec_result["tokens_used"]
        else:
            # Direct generation without iterative ReAct loop
            messages = [{"role": "system", "content": system_prompt}]
            for h in pruned_history:
                messages.append({"role": h["role"], "content": h["content"]})
            
            gen_res = self.llm.generate_chat_completion(messages, model=selected_model)
            final_response_text = gen_res["content"]
            tokens_used = gen_res.get("tokens_used", 0)

        # 8. Save Assistant Response and Reasoning Trace to DB
        assistant_msg = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            role="assistant",
            content=final_response_text,
            reasoning_trace=json.dumps(reasoning_trace) if reasoning_trace else None,
            tool_calls=json.dumps(tool_calls) if tool_calls else None,
            tokens_used=tokens_used,
            created_at=datetime.utcnow()
        )
        db.add(assistant_msg)
        conversation.updated_at = datetime.utcnow()
        db.commit()

        # 9. Asynchronously extract and store learned facts to long-term memory
        if "remember" in effective_message.lower() or "my name is" in effective_message.lower():
            self.memory.store_user_fact(effective_message, category="user_preference")

        return {
            "conversation_id": conversation.id,
            "message_id": assistant_msg.id,
            "response": final_response_text,
            "reasoning_trace": reasoning_trace,
            "tool_calls": tool_calls,
            "tokens_used": tokens_used,
            "model": selected_model,
            "timestamp": datetime.utcnow()
        }

    def stream_chat_message(
        self,
        db: Session,
        message: str,
        conversation_id: Optional[str] = None,
        model: Optional[str] = None,
        persona: str = "assistant"
    ) -> Generator[str, None, None]:
        """
        Server-Sent Events (SSE) streaming generator for real-time responses.
        Yields JSON event chunks for frontend consumption.
        """
        # Run standard reasoning and tool resolution
        result = self.process_chat_message(
            db=db,
            message=message,
            conversation_id=conversation_id,
            model=model,
            persona=persona,
            enable_reasoning=True,
            enable_tools=True
        )

        # 1. Send conversation and metadata header
        yield f"data: {json.dumps({'type': 'init', 'conversation_id': result['conversation_id'], 'message_id': result['message_id']})}\n\n"

        # 2. Send reasoning trace if tools or multi-step reasoning occurred
        if result.get("reasoning_trace"):
            yield f"data: {json.dumps({'type': 'reasoning_trace', 'trace': result['reasoning_trace']})}\n\n"

        # 3. Stream response text in token chunks
        words = result["response"].split(" ")
        for i, word in enumerate(words):
            chunk = word if i == 0 else " " + word
            yield f"data: {json.dumps({'type': 'token', 'token': chunk})}\n\n"

        # 4. Send complete signal
        yield f"data: {json.dumps({'type': 'done', 'tokens_used': result['tokens_used'], 'model': result['model']})}\n\n"

global_agent_service = AgentService()
