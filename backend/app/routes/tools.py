from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.tools.registry import global_tool_registry
from app.schemas import ToolRunRequest, ToolRunResponse
from app.database import SessionLocal
from app.models import ToolExecutionLog

router = APIRouter(prefix="/api/tools", tags=["tools"])

@router.get("/")
async def list_tools() -> List[Dict[str, Any]]:
    """List all available tools in the Agent registry"""
    return global_tool_registry.list_tools()

@router.post("/execute", response_model=ToolRunResponse)
async def execute_tool(request: ToolRunRequest):
    """Directly execute any registered tool with custom parameters"""
    tool = global_tool_registry.get_tool(request.tool_name)
    if not tool:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{request.tool_name}' not found. Available: {global_tool_registry.get_tool_names()}"
        )

    res = global_tool_registry.execute(request.tool_name, request.params)
    status = "error" if isinstance(res, dict) and res.get("status") == "error" else "success"

    return ToolRunResponse(
        tool_name=request.tool_name,
        status=status,
        result=res
    )

@router.get("/logs")
async def get_tool_logs(limit: int = 50):
    """Retrieve execution logs of all tool calls made by the agent"""
    with SessionLocal() as db:
        logs = db.query(ToolExecutionLog).order_by(ToolExecutionLog.created_at.desc()).limit(limit).all()
        return [
            {
                "id": l.id,
                "tool_name": l.tool_name,
                "input_params": l.input_params,
                "output_result": l.output_result,
                "status": l.status,
                "duration_ms": l.duration_ms,
                "created_at": l.created_at
            }
            for l in logs
        ]
