"""
Configuration management using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import Optional
from enum import Enum


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OLLAMA = "ollama"
    OPENAI = "openai"
    GROQ = "groq"
    LOCAL = "local"


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # LLM Provider Selection
    llm_provider: LLMProvider = LLMProvider.OLLAMA  # ollama, openai, groq, local
    
    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    ollama_embed_model: str = "nomic-embed-text"
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    openai_embed_model: str = "text-embedding-3-small"
    
    # Groq Configuration
    groq_api_key: Optional[str] = None
    groq_model: str = "mixtral-8x7b-32768"
    
    # Local Model Configuration
    local_model_path: Optional[str] = None  # Path to local model file
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    
    # FastAPI Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    log_level: str = "INFO"
    
    # Streamlit Configuration
    streamlit_api_url: str = "http://localhost:8000"
    
    # LLM Parameters
    llm_temperature: float = 0.0
    llm_max_tokens: int = 2048
    llm_timeout: int = 60
    
    # Vector Store & Embeddings
    vector_db_path: str = "./data/vector_db"
    embedding_provider: str = "ollama"  # ollama, openai
    
    # File Upload
    upload_dir: str = "./data/uploads"
    max_file_size_mb: int = 50
    
    # Feature Flags
    enable_langsmith: bool = False
    enable_structured_output: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
