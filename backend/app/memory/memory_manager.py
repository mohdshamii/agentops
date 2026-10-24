from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.memory.short_term import ShortTermMemory
from app.memory.long_term import global_long_term_memory, VectorDBLongTermMemory
from app.models import MemoryItem
from app.database import SessionLocal
from app.utils.logger import logger
import json

class MemoryManager:
    """
    Unified Memory Manager coordinating:
    1. Short-Term Memory (sliding context window, token budgeting)
    2. Long-Term Vector Memory (Hugging Face semantic embeddings & retrieval)
    3. Conversation History (SQL database persistence)
    """

    def __init__(self):
        self.short_term = ShortTermMemory()
        self.vector_db = global_long_term_memory

    def retrieve_context_and_memories(
        self,
        query: str,
        history: List[Dict[str, str]],
        system_prompt: str = ""
    ) -> Dict[str, Any]:
        """
        Retrieves pruned short-term dialogue history and semantically relevant long-term memories.
        """
        # 1. Prune short-term history to fit token budget
        pruned_history = self.short_term.get_pruned_context(history, system_prompt)

        # 2. Query vector database for relevant long-term memories
        memories = self.vector_db.search(query, top_k=3, min_similarity=0.15)
        memory_strings = [m["content"] for m in memories]

        return {
            "pruned_history": pruned_history,
            "relevant_memories": memory_strings,
            "memory_objects": memories
        }

    def store_user_fact(self, content: str, category: str = "user_fact", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Stores memory item in vector store and relational database.
        """
        vector_res = self.vector_db.add_memory(content, category, metadata)
        
        # Mirror to relational DB
        try:
            with SessionLocal() as db:
                db_item = MemoryItem(
                    id=vector_res["id"],
                    content=content,
                    category=category,
                    metadata_json=json.dumps(metadata or {})
                )
                db.add(db_item)
                db.commit()
        except Exception as e:
            logger.warning(f"Could not persist memory to SQL: {str(e)}")

        return vector_res

    def search_memories(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        return self.vector_db.search(query, top_k=top_k)

    def list_all_memories(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.vector_db.list_memories(limit=limit)

    def delete_memory(self, memory_id: str) -> bool:
        # Delete from vector store
        deleted = self.vector_db.delete_memory(memory_id)
        # Delete from SQL
        try:
            with SessionLocal() as db:
                item = db.query(MemoryItem).filter(MemoryItem.id == memory_id).first()
                if item:
                    db.delete(item)
                    db.commit()
        except Exception as e:
            logger.warning(f"Could not delete memory from SQL: {str(e)}")
        return deleted

global_memory_manager = MemoryManager()
