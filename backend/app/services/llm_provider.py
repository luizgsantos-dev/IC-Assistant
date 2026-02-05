"""LLM provider abstraction for OpenAI, Anthropic, Ollama, and Google Gemini."""
import os
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.llms import Ollama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models.base import BaseLanguageModel


class LLMProvider:
    """Abstracted LLM provider supporting multiple backends."""
    
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.llm: Optional[BaseLanguageModel] = None
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the LLM based on provider configuration."""
        if self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required when using OpenAI provider")
            self.llm = ChatOpenAI(
                model=model,
                api_key=api_key,
                temperature=0.7
            )
        elif self.provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable is required when using Anthropic provider")
            self.llm = ChatAnthropic(
                model=model,
                api_key=api_key,
                temperature=0.7
            )
        elif self.provider == "ollama":
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            model = os.getenv("OLLAMA_MODEL", "llama3.2")
            self.llm = Ollama(
                model=model,
                base_url=base_url,
                temperature=0.7
            )
        elif self.provider == "gemini" or self.provider == "google":
            api_key = os.getenv("GOOGLE_API_KEY")
            model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable is required when using Gemini provider")
            self.llm = ChatGoogleGenerativeAI(
                model=model,
                google_api_key=api_key,
                temperature=0.7,
                convert_system_message_to_human=True
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}. Supported: openai, anthropic, ollama, gemini")
    
    def get_llm(self) -> BaseLanguageModel:
        """Get the initialized LLM instance."""
        if self.llm is None:
            raise RuntimeError("LLM not initialized")
        return self.llm
