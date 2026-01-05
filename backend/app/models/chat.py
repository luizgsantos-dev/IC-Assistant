"""Pydantic models for chat API."""
from pydantic import BaseModel
from typing import Optional, List


class ChatMessage(BaseModel):
    """Single chat message."""
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str
    conversation_history: Optional[List[ChatMessage]] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str
    sources: Optional[List[str]] = None


class DocumentInfo(BaseModel):
    """Information about a document."""
    filename: str
    file_type: str
    processed: bool
    chunks_count: Optional[int] = None


class DocumentListResponse(BaseModel):
    """Response model for document list."""
    documents: List[DocumentInfo]
