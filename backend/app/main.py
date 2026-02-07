"""Main FastAPI application with dependency injection."""
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings, Settings
from .services.rag_service import RAGService
from .routes import chat, documents

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global RAG service instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Dependency to get the RAG service instance."""
    global _rag_service
    if _rag_service is None:
        raise RuntimeError("RAG service not initialized. Application may not have started correctly.")
    return _rag_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    global _rag_service
    
    logger.info("=" * 50)
    logger.info("Starting IC-UFMT Smart Agent...")
    logger.info("=" * 50)
    
    # Initialize settings and log configuration
    try:
        settings = get_settings()
        logger.info(f"LLM Provider: {settings.get_active_provider()}")
        logger.info(f"Embedding Provider: {settings.embedding_provider}")
        logger.info(f"Data Directory: {settings.data_dir}")
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please check your .env file and configure at least one LLM provider")
        raise
    
    # Initialize RAG service
    try:
        logger.info("Initializing RAG service...")
        _rag_service = RAGService(settings=settings)
        
        # Start file watcher for automatic document updates
        _rag_service.start_file_watcher()
        
        info = _rag_service.get_provider_info()
        logger.info(f"RAG service initialized successfully")
        logger.info(f"  - LLM: {info['llm_provider']} ({info['llm_model']})")
        logger.info(f"  - Documents: {info['document_count']} chunks loaded")
        
    except Exception as e:
        logger.error(f"Failed to initialize RAG service: {e}")
        raise
    
    logger.info("=" * 50)
    logger.info("IC-UFMT Smart Agent is ready!")
    logger.info(f"API available at http://{settings.host}:{settings.port}")
    logger.info("=" * 50)
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("Shutting down IC-UFMT Smart Agent...")
    
    if _rag_service:
        _rag_service.stop_file_watcher()
    
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="IC-UFMT Smart Agent API",
    description="RAG-based AI Assistant for Instituto de Computacao - UFMT",
    version="2.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with dependency injection
app.include_router(
    chat.router,
    dependencies=[Depends(get_rag_service)],
)
app.include_router(
    documents.router,
    dependencies=[Depends(get_rag_service)],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "IC-UFMT Smart Agent API",
        "version": "2.0.0",
        "docs": "/docs",
    }


@app.get("/api/health")
async def health(rag_service: RAGService = Depends(get_rag_service)):
    """Health check endpoint with provider information."""
    try:
        info = rag_service.get_provider_info()
        return {
            "status": "healthy",
            "version": "2.0.0",
            "provider": info,
        }
    except Exception as e:
        return {
            "status": "degraded",
            "version": "2.0.0",
            "error": str(e),
        }


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
