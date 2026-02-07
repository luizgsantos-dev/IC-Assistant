"""Chat routes for handling user queries with streaming support."""
import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from sse_starlette.sse import EventSourceResponse

from ..models.chat import ChatRequest, ChatResponse, ChatMessage
from ..services.rag_service import RAGService
from ..main import get_rag_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    rag_service: RAGService = Depends(get_rag_service),
):
    """Handle a chat message and return RAG-based response.
    
    This endpoint returns the complete response at once.
    For streaming responses, use POST /chat/stream.
    """
    try:
        # Convert conversation history to dict format
        history = None
        if request.conversation_history:
            history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]
        
        result = rag_service.query(
            question=request.message,
            conversation_history=history,
        )
        
        return ChatResponse(
            response=result["answer"],
            sources=result.get("sources", []),
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar sua pergunta: {str(e)}",
        )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    rag_service: RAGService = Depends(get_rag_service),
):
    """Handle a chat message with streaming response via SSE.
    
    Returns Server-Sent Events with the following event types:
    - sources: List of source documents (sent first)
    - token: Individual response tokens
    - done: Signals completion
    - error: Error message
    """
    async def event_generator():
        try:
            # Convert conversation history to dict format
            history = None
            if request.conversation_history:
                history = [
                    {"role": msg.role, "content": msg.content}
                    for msg in request.conversation_history
                ]
            
            # Stream the response
            async for event in rag_service.query_stream(
                question=request.message,
                conversation_history=history,
            ):
                event_type = event.get("type", "token")
                content = event.get("content", "")
                
                if event_type == "sources":
                    yield {
                        "event": "sources",
                        "data": json.dumps(content),
                    }
                elif event_type == "token":
                    yield {
                        "event": "token",
                        "data": content,
                    }
                elif event_type == "done":
                    yield {
                        "event": "done",
                        "data": "",
                    }
                elif event_type == "error":
                    yield {
                        "event": "error",
                        "data": content,
                    }
                    
        except Exception as e:
            logger.error(f"Error in stream: {e}")
            yield {
                "event": "error",
                "data": f"Erro ao processar sua pergunta: {str(e)}",
            }
    
    return EventSourceResponse(event_generator())


@router.get("/health")
async def health_check():
    """Health check endpoint for chat service."""
    return {"status": "ok", "service": "chat"}
