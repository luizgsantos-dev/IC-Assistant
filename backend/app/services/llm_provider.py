"""LLM provider factory with support for OpenAI, Anthropic, Gemini, and Ollama.

Includes streaming support via async generators.
"""
import logging
from typing import Optional, AsyncGenerator, Any
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage

from ..config import Settings, get_settings

logger = logging.getLogger(__name__)


class LLMProvider:
    """Factory for creating LLM instances with streaming support.
    
    Supports:
    - OpenAI (gpt-4o-mini, gpt-4o, etc.)
    - Anthropic (claude-3-5-sonnet, etc.)
    - Google Gemini (gemini-1.5-flash, gemini-1.5-pro)
    - Ollama (llama3.2, mistral, etc.)
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        """Initialize the LLM provider.
        
        Args:
            settings: Application settings. If None, will use global settings.
        """
        self.settings = settings or get_settings()
        self._llm: Optional[BaseChatModel] = None
        self._provider_name: Optional[str] = None
    
    def _create_openai(self) -> BaseChatModel:
        """Create OpenAI ChatGPT instance."""
        from langchain_openai import ChatOpenAI
        
        config = self.settings.get_llm_config()
        logger.info(f"Initializing OpenAI with model: {config['model']}")
        
        return ChatOpenAI(
            model=config["model"],
            api_key=config["api_key"],
            temperature=0.7,
            streaming=True,
        )
    
    def _create_anthropic(self) -> BaseChatModel:
        """Create Anthropic Claude instance."""
        from langchain_anthropic import ChatAnthropic
        
        config = self.settings.get_llm_config()
        logger.info(f"Initializing Anthropic with model: {config['model']}")
        
        return ChatAnthropic(
            model=config["model"],
            api_key=config["api_key"],
            temperature=0.7,
            streaming=True,
        )
    
    def _create_gemini(self) -> BaseChatModel:
        """Create Google Gemini instance."""
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        config = self.settings.get_llm_config()
        logger.info(f"Initializing Gemini with model: {config['model']}")
        
        return ChatGoogleGenerativeAI(
            model=config["model"],
            google_api_key=config["api_key"],
            temperature=0.7,
            streaming=True,
            convert_system_message_to_human=True,
        )
    
    def _create_ollama(self) -> BaseChatModel:
        """Create Ollama instance for local models."""
        from langchain_community.chat_models import ChatOllama
        
        config = self.settings.get_llm_config()
        logger.info(f"Initializing Ollama with model: {config['model']} at {config['base_url']}")
        
        return ChatOllama(
            model=config["model"],
            base_url=config["base_url"],
            temperature=0.7,
        )
    
    def get_llm(self) -> BaseChatModel:
        """Get or create the LLM instance.
        
        Returns:
            The configured LLM instance.
        """
        if self._llm is not None:
            return self._llm
        
        provider = self.settings.get_active_provider()
        self._provider_name = provider
        
        if provider == "openai":
            self._llm = self._create_openai()
        elif provider == "anthropic":
            self._llm = self._create_anthropic()
        elif provider == "gemini":
            self._llm = self._create_gemini()
        elif provider == "ollama":
            self._llm = self._create_ollama()
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        logger.info(f"LLM provider '{provider}' initialized successfully")
        return self._llm
    
    def get_provider_name(self) -> str:
        """Get the name of the active provider."""
        if self._provider_name:
            return self._provider_name
        return self.settings.get_active_provider()
    
    def get_model_name(self) -> str:
        """Get the model name being used."""
        config = self.settings.get_llm_config()
        return config.get("model", "unknown")
    
    async def stream(
        self,
        messages: list[BaseMessage],
    ) -> AsyncGenerator[str, None]:
        """Stream response tokens from the LLM.
        
        Args:
            messages: List of messages to send to the LLM.
            
        Yields:
            Response tokens as strings.
        """
        llm = self.get_llm()
        
        try:
            async for chunk in llm.astream(messages):
                if hasattr(chunk, "content") and chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"Error streaming from LLM: {e}")
            yield f"\n\n[Erro ao gerar resposta: {str(e)}]"
    
    async def invoke_async(self, messages: list[BaseMessage]) -> str:
        """Invoke the LLM asynchronously and return full response.
        
        Args:
            messages: List of messages to send to the LLM.
            
        Returns:
            The complete response text.
        """
        llm = self.get_llm()
        
        try:
            response = await llm.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Error invoking LLM: {e}")
            raise
    
    def invoke(self, messages: list[BaseMessage]) -> str:
        """Invoke the LLM synchronously and return full response.
        
        Args:
            messages: List of messages to send to the LLM.
            
        Returns:
            The complete response text.
        """
        llm = self.get_llm()
        
        try:
            response = llm.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Error invoking LLM: {e}")
            raise


def create_messages(
    system_prompt: str,
    user_message: str,
    conversation_history: Optional[list[dict]] = None,
) -> list[BaseMessage]:
    """Create a list of messages for the LLM.
    
    Args:
        system_prompt: The system prompt to use.
        user_message: The current user message.
        conversation_history: Optional list of previous messages.
        
    Returns:
        List of LangChain message objects.
    """
    messages: list[BaseMessage] = [SystemMessage(content=system_prompt)]
    
    if conversation_history:
        for msg in conversation_history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
    
    messages.append(HumanMessage(content=user_message))
    
    return messages
