from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.memory.memory_manager import global_memory_manager
from app.schemas import MemoryCreateRequest, MemorySearchRequest

router = APIRouter(prefix="/api/memory", tags=["memory"])

@router.get("/")
async def list_memories(limit: int = 50) -> List[Dict[str, Any]]:
    """List stored long-term vector memories"""
    return global_memory_manager.list_all_memories(limit=limit)

@router.post("/create")
async def create_memory(request: MemoryCreateRequest):
    """Store a new fact, observation, or preference into the vector memory system"""
    res = global_memory_manager.store_user_fact(
        content=request.content,
        category=request.category,
        metadata=request.metadata
    )
    return {
        "status": "success",
        "memory": res
    }

@router.post("/search")
async def search_memories(request: MemorySearchRequest):
    """Semantic vector search against memories using Hugging Face embeddings"""
    results = global_memory_manager.search_memories(request.query, top_k=request.top_k)
    return {
        "query": request.query,
        "count": len(results),
        "matches": results
    }

@router.delete("/{memory_id}")
async def delete_memory(memory_id: str):
    """Delete a memory item by ID"""
    deleted = global_memory_manager.delete_memory(memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory item not found")
    return {"status": "success", "message": f"Memory {memory_id} deleted"}
