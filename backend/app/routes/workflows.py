import json
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.database import SessionLocal
from app.models import WorkflowExecution
from app.workflows.autonomous import global_workflow_engine
from app.schemas import WorkflowCreateRequest

router = APIRouter(prefix="/api/workflows", tags=["workflows"])

def _format_workflow(wf: WorkflowExecution) -> Dict[str, Any]:
    plan = []
    results = []
    if wf.plan_json:
        try:
            plan = json.loads(wf.plan_json)
        except Exception:
            plan = []
    if wf.results_json:
        try:
            results = json.loads(wf.results_json)
        except Exception:
            results = []

    return {
        "id": wf.id,
        "title": wf.title,
        "goal": wf.goal,
        "status": wf.status,
        "plan": plan,
        "results": results,
        "final_output": wf.final_output,
        "created_at": wf.created_at,
        "updated_at": wf.updated_at
    }

@router.get("/")
async def list_workflows():
    """List all autonomous workflows"""
    with SessionLocal() as db:
        wfs = db.query(WorkflowExecution).order_by(WorkflowExecution.created_at.desc()).all()
        return [_format_workflow(w) for w in wfs]

@router.post("/create")
async def create_workflow(request: WorkflowCreateRequest):
    """Decompose user goal into an autonomous multi-step plan"""
    if not request.goal.strip():
        raise HTTPException(status_code=400, detail="Goal cannot be empty")
    return global_workflow_engine.create_workflow(
        title=request.title or "Autonomous Workflow",
        goal=request.goal,
        max_steps=request.max_steps
    )

@router.post("/{workflow_id}/run")
async def run_workflow(workflow_id: str):
    """Execute all planned workflow steps autonomously"""
    return global_workflow_engine.run_workflow(workflow_id)

@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get workflow progress, step results, and final output"""
    with SessionLocal() as db:
        wf = db.query(WorkflowExecution).filter(WorkflowExecution.id == workflow_id).first()
        if not wf:
            raise HTTPException(status_code=404, detail="Workflow not found")
        return _format_workflow(wf)
