"""Centralized configuration management with auto-detect LLM provider."""
import os
import logging
from typing import Optional, Literal
from pydantic_settings import BaseSettings
from pydantic import Field, model_validator

logger = logging.getLogger(__name__)

LLMProviderType = Literal["openai", "anthropic", "gemini", "ollama"]


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # LLM Provider - if not set, will auto-detect based on available API keys
    llm_provider: Optional[LLMProviderType] = Field(default=None, alias="LLM_PROVIDER")
    
    # OpenAI
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    
    # Anthropic
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-3-5-sonnet-20241022", alias="ANTHROPIC_MODEL")
    
    # Google Gemini
    google_api_key: Optional[str] = Field(default=None, alias="GOOGLE_API_KEY")
    gemini_model: str = Field(default="gemini-1.5-flash", alias="GEMINI_MODEL")
    
    # Ollama (local)
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3.2", alias="OLLAMA_MODEL")
    
    # Embeddings
    embedding_provider: Literal["openai", "huggingface"] = Field(
        default="huggingface", alias="EMBEDDING_PROVIDER"
    )
    huggingface_embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        alias="HUGGINGFACE_EMBEDDING_MODEL"
    )
    
    # Directories
    data_dir: str = Field(default="backend/data", alias="DATA_DIR")
    vectorstore_dir: str = Field(default="backend/vectorstore", alias="VECTORSTORE_DIR")
    
    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    
    # Detected provider (set by auto-detect logic)
    detected_provider: Optional[LLMProviderType] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    @model_validator(mode="after")
    def auto_detect_provider(self) -> "Settings":
        """Auto-detect LLM provider if not explicitly set."""
        if self.llm_provider:
            # Explicit provider set, validate the required API key
            self.detected_provider = self.llm_provider
            self._validate_provider_config(self.llm_provider)
            logger.info(f"Using explicitly configured LLM provider: {self.llm_provider}")
        else:
            # Auto-detect based on available API keys
            self.detected_provider = self._detect_provider()
            if self.detected_provider:
                logger.info(f"Auto-detected LLM provider: {self.detected_provider}")
            else:
                logger.warning("No LLM provider configured. Please set API keys in .env")
        
        return self
    
    def _detect_provider(self) -> Optional[LLMProviderType]:
        """Detect available LLM provider based on API keys.
        
        Priority order: OpenAI > Anthropic > Gemini > Ollama
        """
        if self.openai_api_key:
            logger.info("Found OPENAI_API_KEY, using OpenAI")
            return "openai"
        
        if self.anthropic_api_key:
            logger.info("Found ANTHROPIC_API_KEY, using Anthropic")
            return "anthropic"
        
        if self.google_api_key:
            logger.info("Found GOOGLE_API_KEY, using Gemini")
            return "gemini"
        
        if self.ollama_base_url:
            logger.info("Found OLLAMA_BASE_URL, using Ollama")
            return "ollama"
        
        return None
    
    def _validate_provider_config(self, provider: LLMProviderType) -> None:
        """Validate that the required configuration exists for a provider."""
        if provider == "openai" and not self.openai_api_key:
            raise ValueError(
                "LLM_PROVIDER is set to 'openai' but OPENAI_API_KEY is not configured. "
                "Get your API key at: https://platform.openai.com/api-keys"
            )
        
        if provider == "anthropic" and not self.anthropic_api_key:
            raise ValueError(
                "LLM_PROVIDER is set to 'anthropic' but ANTHROPIC_API_KEY is not configured. "
                "Get your API key at: https://console.anthropic.com/"
            )
        
        if provider == "gemini" and not self.google_api_key:
            raise ValueError(
                "LLM_PROVIDER is set to 'gemini' but GOOGLE_API_KEY is not configured. "
                "Get your API key at: https://aistudio.google.com/"
            )
    
    def get_active_provider(self) -> LLMProviderType:
        """Get the active LLM provider."""
        if not self.detected_provider:
            raise ValueError(
                "No LLM provider available. Please configure at least one of: "
                "OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, or OLLAMA_BASE_URL"
            )
        return self.detected_provider
    
    def get_llm_config(self) -> dict:
        """Get configuration for the active LLM provider."""
        provider = self.get_active_provider()
        
        if provider == "openai":
            return {
                "provider": "openai",
                "api_key": self.openai_api_key,
                "model": self.openai_model,
            }
        elif provider == "anthropic":
            return {
                "provider": "anthropic",
                "api_key": self.anthropic_api_key,
                "model": self.anthropic_model,
            }
        elif provider == "gemini":
            return {
                "provider": "gemini",
                "api_key": self.google_api_key,
                "model": self.gemini_model,
            }
        elif provider == "ollama":
            return {
                "provider": "ollama",
                "base_url": self.ollama_base_url,
                "model": self.ollama_model,
            }
        
        raise ValueError(f"Unknown provider: {provider}")


# Global settings instance - lazy loaded
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset settings - useful for testing."""
    global _settings
    _settings = None
