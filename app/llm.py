"""
LLM client initialization and management with support for multiple providers
"""
from typing import Optional, Union
from app.config import settings, LLMProvider
from app.logger import logger
import time


class LLMClient:
    """Unified LLM client supporting multiple providers: Ollama, OpenAI, Groq, Local"""
    
    def __init__(self):
        """Initialize LLM client based on configured provider"""
        self.provider = settings.llm_provider
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
        self.timeout = settings.llm_timeout
        
        logger.info(f"Initializing LLM client with provider: {self.provider}")
        
        # Initialize appropriate client
        self.client = self._create_client()
    
    def _create_client(self):
        """Create LLM client based on provider"""
        try:
            if self.provider == LLMProvider.OLLAMA:
                return self._create_ollama_client()
            elif self.provider == LLMProvider.OPENAI:
                return self._create_openai_client()
            elif self.provider == LLMProvider.GROQ:
                return self._create_groq_client()
            elif self.provider == LLMProvider.LOCAL:
                return self._create_local_client()
            else:
                raise ValueError(f"Unknown LLM provider: {self.provider}")
        except Exception as e:
            logger.error(f"Error creating LLM client: {str(e)}")
            raise
    
    def _create_ollama_client(self):
        """Create Ollama client"""
        try:
            from langchain_ollama import ChatOllama
            
            logger.info(f"Creating Ollama client: {settings.ollama_model}")
            return ChatOllama(
                model=settings.ollama_model,
                base_url=settings.ollama_base_url,
                temperature=self.temperature,
                top_k=40,
                top_p=0.9,
                repeat_penalty=1.1,
                num_predict=self.max_tokens,
                stop=["<|eot_id|>", "<|end_header_id|>"]
            )
        except ImportError:
            raise ImportError("langchain-ollama not installed. Install with: pip install langchain-ollama")
    
    def _create_openai_client(self):
        """Create OpenAI client"""
        try:
            from langchain_openai import ChatOpenAI
            
            if not settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            
            logger.info(f"Creating OpenAI client: {settings.openai_model}")
            return ChatOpenAI(
                model=settings.openai_model,
                api_key=settings.openai_api_key,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout
            )
        except ImportError:
            raise ImportError("langchain-openai not installed. Install with: pip install langchain-openai")
    
    def _create_groq_client(self):
        """Create Groq client"""
        try:
            from langchain_groq import ChatGroq
            
            if not settings.groq_api_key:
                raise ValueError("GROQ_API_KEY environment variable not set")
            
            logger.info(f"Creating Groq client: {settings.groq_model}")
            return ChatGroq(
                model=settings.groq_model,
                api_key=settings.groq_api_key,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout
            )
        except ImportError:
            raise ImportError("langchain-groq not installed. Install with: pip install langchain-groq")
    
    def _create_local_client(self):
        """Create local model client using HuggingFace or similar"""
        try:
            from langchain_huggingface import HuggingFaceEndpoint
            
            if not settings.local_model_path:
                raise ValueError("LOCAL_MODEL_PATH environment variable not set")
            
            logger.info(f"Creating local model client: {settings.local_model_path}")
            return HuggingFaceEndpoint(
                repo_id=settings.local_model_path,
                temperature=self.temperature,
                max_new_tokens=self.max_tokens,
                timeout=self.timeout
            )
        except ImportError:
            raise ImportError("langchain-huggingface not installed. Install with: pip install langchain-huggingface")
    
    def get_client(self):
        """Get the LLM client"""
        return self.client
    
    def invoke(self, messages: list, **kwargs) -> str:
        """
        Invoke LLM with messages
        
        Args:
            messages: List of message dicts or LangChain Message objects
            **kwargs: Additional arguments for LLM invocation
        
        Returns:
            LLM response text
        """
        try:
            response = self.client.invoke(messages, **kwargs)
            return response.content
        except Exception as e:
            logger.error(f"Error invoking LLM: {str(e)}")
            raise
    
    def invoke_with_retry(
        self,
        messages: list,
        max_retries: int = 3,
        **kwargs
    ) -> Optional[str]:
        """
        Invoke LLM with retry logic
        
        Args:
            messages: List of messages
            max_retries: Number of retries on failure
            **kwargs: Additional arguments
        
        Returns:
            LLM response or None if all retries fail
        """
        for attempt in range(max_retries):
            try:
                logger.debug(f"LLM invoke attempt {attempt + 1}/{max_retries}")
                return self.invoke(messages, **kwargs)
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {max_retries} attempts failed")
                    return None
        
        return None


# Global LLM client instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create global LLM client instance"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


def get_llm():
    """Get the LLM client directly"""
    return get_llm_client().get_client()


def get_embedding_client():
    """Get the embeddings client"""
    try:
        if settings.embedding_provider == "openai":
            from langchain_openai import OpenAIEmbeddings
            if not settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY not set")
            logger.info("Using OpenAI embeddings")
            return OpenAIEmbeddings(
                model=settings.openai_embed_model,
                api_key=settings.openai_api_key
            )
        else:  # Default to Ollama
            from langchain_ollama import OllamaEmbeddings
            logger.info(f"Using Ollama embeddings: {settings.ollama_embed_model}")
            return OllamaEmbeddings(
                model=settings.ollama_embed_model,
                base_url=settings.ollama_base_url
            )
    except ImportError as e:
        logger.error(f"Required embedding package not installed: {str(e)}")
        raise
