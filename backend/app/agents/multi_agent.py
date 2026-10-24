from typing import List, Dict, Any, Optional
from app.intelligence.huggingface_llm import HuggingFaceLLMService
from app.intelligence.prompts import PromptEngineeringSystem
from app.intelligence.reasoning import ReasoningEngine
from app.tools.registry import global_tool_registry
from app.utils.logger import logger

class AgentRole:
    """Specialized Agent Definition within the Multi-Agent Team"""
    def __init__(self, name: str, role_title: str, persona: str, allowed_tools: List[str]):
        self.name = name
        self.role_title = role_title
        self.persona = persona
        self.allowed_tools = allowed_tools

class MultiAgentTeam:
    """
    Collaborative Multi-Agent System.
    Coordinates specialized agents (Supervisor, Researcher, Coder, Data Analyst, Reviewer)
    to solve complex, multi-domain tasks through delegation, execution, and synthesis.
    """

    def __init__(self):
        self.llm_service = HuggingFaceLLMService()
        self.reasoning_engine = ReasoningEngine(max_iterations=3)
        self.tools = global_tool_registry

        # Register specialized agents
        self.agents: Dict[str, AgentRole] = {
            "supervisor": AgentRole(
                name="Supervisor",
                role_title="Lead Orchestrator & Task Decomposer",
                persona="planner",
                allowed_tools=["database_query", "web_search"]
            ),
            "researcher": AgentRole(
                name="Researcher",
                role_title="Web Intelligence & Scraping Specialist",
                persona="researcher",
                allowed_tools=["web_search", "web_scrape", "api_caller"]
            ),
            "coder": AgentRole(
                name="Coder",
                role_title="Principal Software Engineer",
                persona="coder",
                allowed_tools=["code_executor", "api_caller"]
            ),
            "data_analyst": AgentRole(
                name="DataAnalyst",
                role_title="Database & SQL Analytics Expert",
                persona="data_analyst",
                allowed_tools=["database_query", "code_executor"]
            ),
            "reviewer": AgentRole(
                name="Reviewer",
                role_title="Quality Assurance & Verification Critic",
                persona="assistant",
                allowed_tools=[]
            )
        }

    def execute_team_task(
        self,
        task: str,
        active_roles: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Executes a multi-agent workflow:
        1. Supervisor analyzes and decomposes the task.
        2. Specialized domain agent(s) (Researcher / Coder / Data Analyst) execute sub-tasks.
        3. Reviewer critiques and synthesizes the final comprehensive answer.
        """
        roles_to_run = active_roles or ["supervisor", "researcher", "coder", "data_analyst", "reviewer"]
        logger.info(f"Initiating Multi-Agent Team execution for task: '{task[:60]}...' with roles: {roles_to_run}")

        agent_outputs: List[Dict[str, Any]] = []

        # Step 1: Supervisor Decomposes the Task
        supervisor_prompt = (
            f"You are the Lead Supervisor Agent. Break down the following user request into specific subtasks "
            f"for specialized team members (Researcher, Coder, Data Analyst):\n\n"
            f"Task: {task}\n\n"
            f"Provide an execution outline identifying key requirements and delegated objectives."
        )
        sup_messages = [
            {"role": "system", "content": PromptEngineeringSystem.build_system_prompt("planner")},
            {"role": "user", "content": supervisor_prompt}
        ]
        sup_res = self.llm_service.generate_chat_completion(sup_messages, model=self.llm_service.settings.HF_DEFAULT_MODEL)
        sup_plan = sup_res["content"]
        agent_outputs.append({
            "agent": "Supervisor",
            "role": "Lead Orchestrator",
            "output": sup_plan,
            "status": "completed"
        })

        # Step 2: Domain Agent Execution based on keywords in task
        task_lower = task.lower()

        # Researcher Agent
        if "researcher" in roles_to_run and any(k in task_lower for k in ["search", "web", "scrape", "latest", "what is", "price", "find"]):
            research_tool_desc = "\n".join([t.format_description_for_prompt() for t in [self.tools.get_tool("web_search"), self.tools.get_tool("web_scrape")] if t])
            res_system = PromptEngineeringSystem.build_system_prompt(
                persona="researcher",
                tools_description=research_tool_desc,
                tool_names="web_search, web_scrape",
                enable_reasoning=True
            )
            res_result = self.reasoning_engine.execute_react_loop(
                llm_fn=lambda msgs: self.llm_service.generate_chat_completion(msgs),
                system_prompt=res_system,
                user_message=f"Supervisor Directive:\n{sup_plan}\n\nOriginal Task: {task}",
                tool_executor_fn=self.tools.execute
            )
            agent_outputs.append({
                "agent": "Researcher",
                "role": "Web Intelligence",
                "output": res_result["final_answer"],
                "reasoning_trace": res_result["reasoning_trace"],
                "tool_calls": res_result["tool_calls"],
                "status": "completed"
            })

        # Data Analyst Agent
        if "data_analyst" in roles_to_run and any(k in task_lower for k in ["data", "db", "sql", "database", "table", "records", "analytics"]):
            db_tool_desc = "\n".join([t.format_description_for_prompt() for t in [self.tools.get_tool("database_query")] if t])
            da_system = PromptEngineeringSystem.build_system_prompt(
                persona="data_analyst",
                tools_description=db_tool_desc,
                tool_names="database_query",
                enable_reasoning=True
            )
            da_result = self.reasoning_engine.execute_react_loop(
                llm_fn=lambda msgs: self.llm_service.generate_chat_completion(msgs),
                system_prompt=da_system,
                user_message=f"Supervisor Directive:\n{sup_plan}\n\nOriginal Task: {task}",
                tool_executor_fn=self.tools.execute
            )
            agent_outputs.append({
                "agent": "DataAnalyst",
                "role": "SQL & Analytics",
                "output": da_result["final_answer"],
                "reasoning_trace": da_result["reasoning_trace"],
                "tool_calls": da_result["tool_calls"],
                "status": "completed"
            })

        # Coder Agent
        if "coder" in roles_to_run and any(k in task_lower for k in ["code", "function", "program", "python", "script", "build", "api"]):
            coder_tool_desc = "\n".join([t.format_description_for_prompt() for t in [self.tools.get_tool("code_executor"), self.tools.get_tool("api_caller")] if t])
            coder_system = PromptEngineeringSystem.build_system_prompt(
                persona="coder",
                tools_description=coder_tool_desc,
                tool_names="code_executor, api_caller",
                enable_reasoning=True
            )
            coder_result = self.reasoning_engine.execute_react_loop(
                llm_fn=lambda msgs: self.llm_service.generate_chat_completion(msgs, model=self.llm_service.settings.HF_CODER_MODEL),
                system_prompt=coder_system,
                user_message=f"Supervisor Directive:\n{sup_plan}\n\nOriginal Task: {task}",
                tool_executor_fn=self.tools.execute
            )
            agent_outputs.append({
                "agent": "Coder",
                "role": "Principal Software Engineer",
                "output": coder_result["final_answer"],
                "reasoning_trace": coder_result["reasoning_trace"],
                "tool_calls": coder_result["tool_calls"],
                "status": "completed"
            })

        # Step 3: Reviewer Critic synthesizes final team response
        collected_findings = "\n\n".join([f"### [{a['agent']} - {a['role']}]:\n{a['output']}" for a in agent_outputs])
        reviewer_prompt = (
            f"You are the Lead Reviewer Agent. Synthesize the findings and contributions from the team members "
            f"into a unified, cohesive, high-quality final response for the user.\n\n"
            f"Original Task: {task}\n\n"
            f"Team Contributions:\n{collected_findings}\n\n"
            f"Provide the final polished answer, resolving any inconsistencies and highlighting key insights."
        )
        rev_messages = [
            {"role": "system", "content": PromptEngineeringSystem.build_system_prompt("assistant")},
            {"role": "user", "content": reviewer_prompt}
        ]
        rev_res = self.llm_service.generate_chat_completion(rev_messages, model=self.llm_service.settings.HF_DEFAULT_MODEL)
        final_synthesis = rev_res["content"]

        agent_outputs.append({
            "agent": "Reviewer",
            "role": "Quality Assurance & Synthesis",
            "output": final_synthesis,
            "status": "completed"
        })

        return {
            "task": task,
            "final_synthesis": final_synthesis,
            "agent_team_steps": agent_outputs,
            "total_agents_involved": len(agent_outputs)
        }

# Global multi-agent team instance
global_multi_agent_team = MultiAgentTeam()
