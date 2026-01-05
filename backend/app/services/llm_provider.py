"""LLM provider abstraction for OpenAI, Anthropic, and Ollama."""
import os
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.llms import Ollama
from langchain.schema import BaseLanguageModel


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
            model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required when using OpenAI provider")
            self.llm = ChatOpenAI(
                model=model,
                openai_api_key=api_key,
                temperature=0.7
            )
        elif self.provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            model = os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable is required when using Anthropic provider")
            self.llm = ChatAnthropic(
                model=model,
                anthropic_api_key=api_key,
                temperature=0.7
            )
        elif self.provider == "ollama":
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            model = os.getenv("OLLAMA_MODEL", "llama2")
            self.llm = Ollama(
                model=model,
                base_url=base_url,
                temperature=0.7
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}. Supported: openai, anthropic, ollama")
    
    def get_llm(self) -> BaseLanguageModel:
        """Get the initialized LLM instance."""
        if self.llm is None:
            raise RuntimeError("LLM not initialized")
        return self.llm
