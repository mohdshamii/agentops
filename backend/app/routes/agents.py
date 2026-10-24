from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from app.agents.multi_agent import global_multi_agent_team
from app.schemas import MultiAgentRequest

router = APIRouter(prefix="/api/agents", tags=["multi_agent"])

@router.get("/team")
async def get_team_info() -> Dict[str, Any]:
    """Get active multi-agent team roles and capabilities"""
    roles = []
    for k, a in global_multi_agent_team.agents.items():
        roles.append({
            "id": k,
            "name": a.name,
            "role": a.role_title,
            "persona": a.persona,
            "allowed_tools": a.allowed_tools
        })
    return {
        "status": "ready",
        "team_size": len(roles),
        "agents": roles
    }

@router.post("/run")
async def run_multi_agent_task(request: MultiAgentRequest):
    """
    Execute a collaborative task with the multi-agent swarm:
    Supervisor -> Domain Specialists (Researcher / Coder / Data Analyst) -> Reviewer Critic.
    """
    if not request.task.strip():
        raise HTTPException(status_code=400, detail="Task description cannot be empty")

    result = global_multi_agent_team.execute_team_task(
        task=request.task,
        active_roles=request.agent_roles
    )
    return result
