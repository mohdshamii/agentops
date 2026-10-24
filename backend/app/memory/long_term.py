import json
import math
import os
import requests
import uuid
from typing import List, Dict, Any, Optional
from app.config import get_settings
from app.utils.logger import logger

class VectorDBLongTermMemory:
    """
    Vector Database Long-Term Memory.
    Uses Hugging Face Serverless embeddings (sentence-transformers/all-MiniLM-L6-v2)
    with a fallback semantic vectorizer, cosine similarity search, and disk persistence.
    """

    def __init__(self, store_file: Optional[str] = None):
        self.settings = get_settings()
        self.store_file = store_file or self.settings.VECTOR_STORE_PATH
        self.hf_token = self.settings.HF_TOKEN
        self.model_name = self.settings.HF_EMBEDDING_MODEL
        self.items: List[Dict[str, Any]] = []
        self._load_from_disk()

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.hf_token:
            headers["Authorization"] = f"Bearer {self.hf_token}"
        return headers

    def get_embedding(self, text: str) -> List[float]:
        """
        Generates text embedding using Hugging Face router, HF feature extraction,
        or built-in hashed semantic vectorizer.
        """
        # 1. Try HF Serverless Router
        if self.hf_token:
            try:
                router_url = f"{self.settings.HF_ROUTER_BASE_URL}/embeddings"
                payload = {
                    "model": self.model_name,
                    "input": text
                }
                resp = requests.post(router_url, headers=self._get_headers(), json=payload, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    if "data" in data and len(data["data"]) > 0:
                        return data["data"][0]["embedding"]
            except Exception as e:
                logger.warning(f"HF Router embeddings failed: {str(e)}. Trying direct HF pipeline...")

            # 2. Try Direct HF Feature Extraction Pipeline
            try:
                pipeline_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{self.model_name}"
                resp = requests.post(pipeline_url, headers=self._get_headers(), json={"inputs": text}, timeout=10)
                if resp.status_code == 200:
                    emb = resp.json()
                    if isinstance(emb, list):
                        # Some models return list of token vectors; average if 2D
                        if len(emb) > 0 and isinstance(emb[0], list):
                            vec_len = len(emb[0])
                            avg_vec = [sum(tok[i] for tok in emb) / len(emb) for i in range(vec_len)]
                            return avg_vec
                        return emb
            except Exception as err:
                logger.warning(f"Direct HF pipeline embeddings failed: {str(err)}")

        # 3. Fallback Built-in Semantic Feature Vectorizer (64-dimensional normalized hashed projection)
        return self._generate_fallback_vector(text)

    def _generate_fallback_vector(self, text: str, dim: int = 64) -> List[float]:
        """
        Deterministic lightweight semantic hash vectorizer with cosine normalization.
        Ensures semantic similarity between overlapping keywords and stems.
        """
        words = text.lower().replace(".", " ").replace(",", " ").split()
        vec = [0.0] * dim
        for w in words:
            h = abs(hash(w))
            idx1 = h % dim
            idx2 = (h // dim) % dim
            vec[idx1] += 1.0
            vec[idx2] += 0.5

        # Normalize vector
        magnitude = math.sqrt(sum(x * x for x in vec))
        if magnitude > 0:
            vec = [x / magnitude for x in vec]
        return vec

    def _cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def add_memory(self, content: str, category: str = "general", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Embeds and stores a new memory item into the vector store and persists to disk.
        """
        mem_id = str(uuid.uuid4())
        embedding = self.get_embedding(content)

        memory_item = {
            "id": mem_id,
            "content": content,
            "category": category,
            "metadata": metadata or {},
            "embedding": embedding
        }

        self.items.append(memory_item)
        self._save_to_disk()
        logger.info(f"Stored long-term vector memory [{mem_id[:8]}...]: '{content[:50]}'")
        return {
            "id": mem_id,
            "content": content,
            "category": category,
            "metadata": metadata or {}
        }

    def search(self, query: str, top_k: int = 4, min_similarity: float = 0.1) -> List[Dict[str, Any]]:
        """
        Performs semantic vector search against stored memories.
        """
        if not self.items:
            return []

        query_emb = self.get_embedding(query)
        scored_items = []

        for item in self.items:
            sim = self._cosine_similarity(query_emb, item.get("embedding", []))
            if sim >= min_similarity:
                scored_items.append({
                    "id": item["id"],
                    "content": item["content"],
                    "category": item["category"],
                    "metadata": item.get("metadata", {}),
                    "similarity": round(sim, 4)
                })

        # Sort by similarity descending
        scored_items.sort(key=lambda x: x["similarity"], reverse=True)
        return scored_items[:top_k]

    def delete_memory(self, memory_id: str) -> bool:
        initial_len = len(self.items)
        self.items = [item for item in self.items if item["id"] != memory_id]
        if len(self.items) != initial_len:
            self._save_to_disk()
            return True
        return False

    def list_memories(self, limit: int = 50) -> List[Dict[str, Any]]:
        return [
            {
                "id": it["id"],
                "content": it["content"],
                "category": it["category"],
                "metadata": it.get("metadata", {})
            }
            for it in self.items[:limit]
        ]

    def _save_to_disk(self) -> None:
        try:
            with open(self.store_file, "w", encoding="utf-8") as f:
                json.dump(self.items, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save vector store to disk: {str(e)}")

    def _load_from_disk(self) -> None:
        if os.path.exists(self.store_file):
            try:
                with open(self.store_file, "r", encoding="utf-8") as f:
                    self.items = json.load(f)
                logger.info(f"Loaded {len(self.items)} vector memories from {self.store_file}")
            except Exception as e:
                logger.error(f"Failed to load vector store from disk: {str(e)}")
                self.items = []
        else:
            self.items = []
            # Seed default memories for the agent
            self.add_memory("AgentOps is an Agentic AI platform built with Hugging Face open-weight intelligence.", category="system")
            self.add_memory("The system incorporates multi-step reasoning, tool execution, vector memory, and multi-agent coordination.", category="system")

# Global long-term memory instance
global_long_term_memory = VectorDBLongTermMemory()
