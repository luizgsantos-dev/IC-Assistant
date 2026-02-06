"""LLM provider abstraction for OpenAI, Anthropic, Ollama, and Google Gemini."""
import os
import logging
from typing import Optional, Union
from langchain_core.language_models import BaseChatModel

logger = logging.getLogger(__name__)


class LLMProvider:
    """Abstracted LLM provider supporting multiple backends.
    
    Supports:
    - OpenAI (gpt-4o-mini, gpt-4o, gpt-3.5-turbo, etc.)
    - Anthropic (claude-3-5-sonnet, claude-3-opus, etc.)
    - Google Gemini (gemini-1.5-flash, gemini-1.5-pro, etc.)
    - Ollama (llama3.2, mistral, etc. - local models)
    """
    
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.llm: Optional[BaseChatModel] = None
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the LLM based on provider configuration."""
        logger.info(f"Initializing LLM provider: {self.provider}")
        
        if self.provider == "openai":
            self._init_openai()
        elif self.provider == "anthropic":
            self._init_anthropic()
        elif self.provider == "ollama":
            self._init_ollama()
        elif self.provider in ("gemini", "google"):
            self._init_gemini()
        else:
            raise ValueError(
                f"Unsupported LLM provider: {self.provider}. "
                "Supported providers: openai, anthropic, ollama, gemini"
            )
        
        logger.info(f"LLM provider {self.provider} initialized successfully")
    
    def _init_openai(self):
        """Initialize OpenAI ChatGPT."""
        from langchain_openai import ChatOpenAI
        
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required when using OpenAI provider. "
                "Get your API key at: https://platform.openai.com/api-keys"
            )
        
        self.llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            temperature=0.7
        )
        logger.info(f"OpenAI initialized with model: {model}")
    
    def _init_anthropic(self):
        """Initialize Anthropic Claude."""
        from langchain_anthropic import ChatAnthropic
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is required when using Anthropic provider. "
                "Get your API key at: https://console.anthropic.com/"
            )
        
        self.llm = ChatAnthropic(
            model=model,
            api_key=api_key,
            temperature=0.7
        )
        logger.info(f"Anthropic initialized with model: {model}")
    
    def _init_ollama(self):
        """Initialize Ollama for local models."""
        from langchain_community.chat_models import ChatOllama
        
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model = os.getenv("OLLAMA_MODEL", "llama3.2")
        
        self.llm = ChatOllama(
            model=model,
            base_url=base_url,
            temperature=0.7
        )
        logger.info(f"Ollama initialized with model: {model} at {base_url}")
    
    def _init_gemini(self):
        """Initialize Google Gemini."""
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        api_key = os.getenv("GOOGLE_API_KEY")
        model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable is required when using Gemini provider. "
                "Get your API key at: https://aistudio.google.com/"
            )
        
        self.llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=0.7,
            convert_system_message_to_human=True
        )
        logger.info(f"Google Gemini initialized with model: {model}")
    
    def get_llm(self) -> BaseChatModel:
        """Get the initialized LLM instance."""
        if self.llm is None:
            raise RuntimeError("LLM not initialized")
        return self.llm
    
    def get_provider_name(self) -> str:
        """Get the current provider name."""
        return self.provider
