"""Chat routes for handling user queries."""
from fastapi import APIRouter, HTTPException
from typing import Optional
from ..models.chat import ChatRequest, ChatResponse, ChatMessage
from ..services.rag_service import RAGService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize RAG service (singleton pattern)
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create the RAG service instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle a chat message and return RAG-based response."""
    try:
        rag_service = get_rag_service()
        result = rag_service.query(request.message)
        
        return ChatResponse(
            response=result["answer"],
            sources=result.get("sources", [])
        )
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
