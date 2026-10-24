from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from typing import List

class Settings(BaseSettings):
    # API Config
    API_TITLE: str = "AgentOps - Intelligent Agentic Platform"
    API_VERSION: str = "2.0.0"
    DEBUG: bool = True
    
    # Hugging Face Settings
    HF_TOKEN: str = os.getenv("HF_TOKEN", os.getenv("HUGGINGFACE_API_KEY", ""))
    HF_ROUTER_BASE_URL: str = "https://router.huggingface.co/v1"
    HF_DEFAULT_MODEL: str = "meta-llama/Llama-3.2-3B-Instruct"
    HF_REASONING_MODEL: str = "deepseek-ai/DeepSeek-R1"
    HF_CODER_MODEL: str = "Qwen/Qwen2.5-Coder-32B-Instruct"
    HF_EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    HF_VISION_MODEL: str = "Salesforce/blip-image-captioning"
    HF_AUDIO_MODEL: str = "openai/whisper-large-v3-turbo"
    
    # Fallback & OpenAI compatibility
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Database & Storage
    DATABASE_URL: str = "sqlite:///./ai_agent.db"
    VECTOR_STORE_PATH: str = "./vector_store.json"
    
    # Memory Settings
    SHORT_TERM_MEMORY_LIMIT: int = 10
    MAX_TOKENS: int = 2048
    TEMPERATURE: float = 0.7
    
    # Server & CORS
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "*"
    ]
    
    class Config:
        env_file = ".env"
        extra = "allow"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()