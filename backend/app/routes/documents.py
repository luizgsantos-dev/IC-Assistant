"""Document management routes."""
import logging

from fastapi import APIRouter, HTTPException, Depends

from ..models.chat import DocumentInfo, DocumentListResponse, ProviderInfo
from ..services.rag_service import RAGService
from ..main import get_rag_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    rag_service: RAGService = Depends(get_rag_service),
):
    """List all documents in the data directory."""
    try:
        # Get document list from processor
        docs = rag_service.document_processor.get_document_list()
        
        documents = [
            DocumentInfo(
                filename=doc["filename"],
                file_type=doc["file_type"],
                size_bytes=doc.get("size_bytes"),
                processed=True,
            )
            for doc in docs
        ]
        
        return DocumentListResponse(
            documents=documents,
            total_chunks=rag_service.get_document_count(),
        )
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao listar documentos: {str(e)}",
        )


@router.post("/refresh")
async def refresh_documents(
    rag_service: RAGService = Depends(get_rag_service),
):
    """Manually trigger document processing and vectorstore update."""
    try:
        chunks_count = rag_service.update_documents()
        
        return {
            "status": "success",
            "message": f"Documentos processados com sucesso",
            "chunks_count": chunks_count,
        }
        
    except Exception as e:
        logger.error(f"Error refreshing documents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao atualizar documentos: {str(e)}",
        )


@router.get("/info", response_model=ProviderInfo)
async def get_info(
    rag_service: RAGService = Depends(get_rag_service),
):
    """Get information about the current configuration."""
    try:
        info = rag_service.get_provider_info()
        return ProviderInfo(**info)
        
    except Exception as e:
        logger.error(f"Error getting info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter informacoes: {str(e)}",
        )
