"""Document management routes."""
from fastapi import APIRouter, HTTPException
from pathlib import Path
from typing import List, Optional
import os
import logging
from ..models.chat import DocumentInfo, DocumentListResponse
from ..services.rag_service import RAGService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

# Initialize RAG service (singleton pattern)
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create the RAG service instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service


@router.get("", response_model=DocumentListResponse)
async def list_documents():
    """List all documents in the data directory."""
    try:
        data_dir = Path(os.getenv("DATA_DIR", "backend/data"))
        data_dir.mkdir(parents=True, exist_ok=True)
        
        supported_extensions = {".pdf", ".txt", ".md", ".markdown"}
        documents = []
        
        for file_path in data_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                documents.append(DocumentInfo(
                    filename=file_path.name,
                    file_type=file_path.suffix.lower(),
                    processed=True  # Could check vectorstore to verify
                ))
        
        return DocumentListResponse(documents=documents)
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh")
async def refresh_documents():
    """Manually trigger document processing and vectorstore update."""
    try:
        rag_service = get_rag_service()
        rag_service.update_documents()
        return {"status": "success", "message": "Documents processed and vectorstore updated"}
    except Exception as e:
        logger.error(f"Error refreshing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))
