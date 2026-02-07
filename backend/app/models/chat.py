"""Pydantic models for chat API."""
from pydantic import BaseModel, Field
from typing import Optional, List


class ChatMessage(BaseModel):
    """Single chat message."""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., description="User's question or message")
    conversation_history: Optional[List[ChatMessage]] = Field(
        default=None,
        description="Previous messages in the conversation for context"
    )


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str = Field(..., description="Assistant's response")
    sources: List[str] = Field(default_factory=list, description="Source documents used")


class StreamEvent(BaseModel):
    """Event for streaming responses."""
    type: str = Field(..., description="Event type: 'token', 'sources', 'done', 'error'")
    content: Optional[str | List[str]] = Field(default=None, description="Event content")


class DocumentInfo(BaseModel):
    """Information about a document."""
    filename: str = Field(..., description="Document filename")
    file_type: str = Field(..., description="File extension")
    size_bytes: Optional[int] = Field(default=None, description="File size in bytes")
    processed: bool = Field(default=True, description="Whether document was processed")


class DocumentListResponse(BaseModel):
    """Response model for document list."""
    documents: List[DocumentInfo] = Field(default_factory=list)
    total_chunks: int = Field(default=0, description="Total chunks in vectorstore")


class ProviderInfo(BaseModel):
    """Information about active providers."""
    llm_provider: str = Field(..., description="Active LLM provider name")
    llm_model: str = Field(..., description="Active LLM model name")
    embedding_provider: str = Field(..., description="Active embedding provider")
    document_count: int = Field(default=0, description="Number of document chunks")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(default="healthy")
    version: str = Field(default="2.0.0")
    provider: Optional[ProviderInfo] = None
