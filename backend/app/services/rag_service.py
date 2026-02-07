"""RAG service for semantic search and response generation.

Supports conversation history and streaming responses.
"""
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, AsyncGenerator
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from ..config import Settings, get_settings
from .llm_provider import LLMProvider
from .document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

# Portuguese RAG prompt for IC-UFMT
RAG_SYSTEM_PROMPT = """Voce e o assistente do Instituto de Computacao (IC) da Universidade Federal de Mato Grosso (UFMT).

Seu papel e ajudar alunos, professores e funcionarios com informacoes sobre:
- Processos administrativos e burocraticos (SEI, solicitacoes de material, resolucoes CONSEP/UFMT)
- Processos academicos (aproveitamento de materias, matriculas, prazos, requisitos de graduacao)
- Informacoes institucionais (laboratorios de pesquisa, eventos, iniciativas estudantis como CACOMP)
- Calendario academico e procedimentos oficiais

REGRAS IMPORTANTES:
1. Use APENAS as informacoes do contexto abaixo para responder.
2. Se a informacao NAO estiver no contexto, diga claramente: "Nao encontrei essa informacao nos documentos disponiveis."
3. NUNCA invente informacoes, datas, numeros de processos ou procedimentos.
4. Quando citar uma resolucao ou normativa, mencione a fonte do documento.
5. Responda sempre em portugues de forma clara e objetiva.

FORMATO DE RESPOSTA:
- Para processos: Explique O QUE fazer, ONDE fazer (sistema/setor), COMO fazer (passos).
- Para informacoes: Seja direto e cite a fonte quando possivel.

CONTEXTO DOS DOCUMENTOS:
{context}"""


class RAGService:
    """RAG service using ChromaDB for vector storage and semantic search.
    
    Supports conversation history and streaming responses.
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        """Initialize the RAG service.
        
        Args:
            settings: Application settings. If None, will use global settings.
        """
        self.settings = settings or get_settings()
        self.vectorstore_path = Path(self.settings.vectorstore_dir)
        self.vectorstore_path.mkdir(parents=True, exist_ok=True)
        
        self.document_processor = DocumentProcessor(settings=self.settings)
        self.llm_provider = LLMProvider(settings=self.settings)
        
        self.vectorstore: Optional[Chroma] = None
        self.embeddings = None
        
        self._initialize_embeddings()
        self._initialize_vectorstore()
    
    def _initialize_embeddings(self) -> None:
        """Initialize embeddings based on provider setting."""
        provider = self.settings.embedding_provider
        logger.info(f"Initializing embeddings with provider: {provider}")
        
        if provider == "openai":
            api_key = self.settings.openai_api_key
            if not api_key:
                raise ValueError("OPENAI_API_KEY is required for OpenAI embeddings")
            self.embeddings = OpenAIEmbeddings(api_key=api_key)
        elif provider == "huggingface":
            model_name = self.settings.huggingface_embedding_model
            logger.info(f"Loading HuggingFace embeddings model: {model_name}")
            logger.info("First load may take a few minutes to download the model...")
            self.embeddings = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")
        
        logger.info("Embeddings initialized successfully")
    
    def _initialize_vectorstore(self) -> None:
        """Initialize or load the ChromaDB vector store."""
        try:
            chroma_db_path = self.vectorstore_path / "chroma.sqlite3"
            
            if chroma_db_path.exists():
                logger.info("Loading existing vectorstore...")
                self.vectorstore = Chroma(
                    persist_directory=str(self.vectorstore_path),
                    embedding_function=self.embeddings,
                )
                count = self.get_document_count()
                logger.info(f"Vectorstore loaded with {count} chunks")
            else:
                logger.info("Creating new vectorstore...")
                self.vectorstore = Chroma(
                    persist_directory=str(self.vectorstore_path),
                    embedding_function=self.embeddings,
                )
                
                # Process initial documents if any exist
                try:
                    self.update_documents()
                except Exception as e:
                    logger.warning(f"No documents to process or error: {e}")
                    
        except Exception as e:
            logger.error(f"Error initializing vectorstore: {e}")
            raise
    
    def update_documents(self) -> int:
        """Process all documents and update the vector store.
        
        Returns:
            Number of chunks added to the vectorstore.
        """
        logger.info("Processing documents and updating vectorstore...")
        chunks = self.document_processor.process_all_documents()
        
        if not chunks:
            logger.warning("No documents found to process")
            return 0
        
        # Convert to LangChain documents
        documents = []
        for chunk in chunks:
            doc = Document(
                page_content=chunk["text"],
                metadata={
                    "source": chunk["source"],
                    "chunk_index": chunk["chunk_index"],
                    "file_path": chunk["file_path"],
                },
            )
            documents.append(doc)
        
        # Clear and recreate vectorstore
        if self.vectorstore:
            try:
                # Delete existing collection
                self.vectorstore.delete_collection()
            except Exception:
                pass
        
        # Create new vectorstore with documents
        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=str(self.vectorstore_path),
        )
        
        logger.info(f"Vectorstore updated with {len(documents)} chunks")
        return len(documents)
    
    def _retrieve_context(self, question: str, k: int = 4) -> tuple[str, List[str]]:
        """Retrieve relevant context for a question.
        
        Args:
            question: The user's question.
            k: Number of documents to retrieve.
            
        Returns:
            Tuple of (context_text, list_of_sources)
        """
        if not self.vectorstore:
            return "", []
        
        try:
            docs = self.vectorstore.similarity_search(question, k=k)
            
            if not docs:
                return "", []
            
            context_parts = []
            sources = set()
            
            for doc in docs:
                context_parts.append(doc.page_content)
                source = doc.metadata.get("source", "Documento desconhecido")
                sources.add(source)
            
            context = "\n\n---\n\n".join(context_parts)
            return context, list(sources)
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return "", []
    
    def query(
        self,
        question: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        k: int = 4,
    ) -> Dict[str, Any]:
        """Query the RAG system with a question.
        
        Args:
            question: The user's question.
            conversation_history: Optional list of previous messages.
            k: Number of documents to retrieve.
            
        Returns:
            Dict with answer and sources.
        """
        # Check if vectorstore has documents
        if self.get_document_count() == 0:
            return {
                "answer": "Nenhum documento foi carregado ainda. Por favor, adicione documentos na pasta 'data/' e atualize o sistema.",
                "sources": [],
            }
        
        # Retrieve context
        context, sources = self._retrieve_context(question, k=k)
        
        if not context:
            return {
                "answer": "Nao encontrei informacoes relevantes nos documentos disponiveis para responder sua pergunta.",
                "sources": [],
            }
        
        # Build messages
        system_prompt = RAG_SYSTEM_PROMPT.format(context=context)
        messages = [SystemMessage(content=system_prompt)]
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history[-6:]:  # Last 6 messages for context
                role = msg.get("role", "")
                content = msg.get("content", "")
                
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))
        
        messages.append(HumanMessage(content=question))
        
        # Get response from LLM
        try:
            answer = self.llm_provider.invoke(messages)
            return {
                "answer": answer,
                "sources": sources,
            }
        except Exception as e:
            logger.error(f"Error getting LLM response: {e}")
            return {
                "answer": f"Erro ao processar sua pergunta: {str(e)}",
                "sources": [],
            }
    
    async def query_stream(
        self,
        question: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        k: int = 4,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Query the RAG system with streaming response.
        
        Args:
            question: The user's question.
            conversation_history: Optional list of previous messages.
            k: Number of documents to retrieve.
            
        Yields:
            Dicts with token chunks and metadata.
        """
        # Check if vectorstore has documents
        if self.get_document_count() == 0:
            yield {
                "type": "error",
                "content": "Nenhum documento foi carregado ainda. Por favor, adicione documentos na pasta 'data/' e atualize o sistema.",
            }
            return
        
        # Retrieve context
        context, sources = self._retrieve_context(question, k=k)
        
        if not context:
            yield {
                "type": "error",
                "content": "Nao encontrei informacoes relevantes nos documentos disponiveis para responder sua pergunta.",
            }
            return
        
        # Send sources first
        yield {
            "type": "sources",
            "content": sources,
        }
        
        # Build messages
        system_prompt = RAG_SYSTEM_PROMPT.format(context=context)
        messages = [SystemMessage(content=system_prompt)]
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history[-6:]:
                role = msg.get("role", "")
                content = msg.get("content", "")
                
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))
        
        messages.append(HumanMessage(content=question))
        
        # Stream response
        try:
            async for token in self.llm_provider.stream(messages):
                yield {
                    "type": "token",
                    "content": token,
                }
            
            yield {"type": "done"}
            
        except Exception as e:
            logger.error(f"Error streaming LLM response: {e}")
            yield {
                "type": "error",
                "content": f"Erro ao processar sua pergunta: {str(e)}",
            }
    
    def get_document_count(self) -> int:
        """Get the number of document chunks in the vectorstore."""
        if not self.vectorstore:
            return 0
        try:
            collection = self.vectorstore._collection
            if collection:
                return collection.count()
            return 0
        except Exception:
            return 0
    
    def get_provider_info(self) -> Dict[str, str]:
        """Get information about the current providers."""
        return {
            "llm_provider": self.llm_provider.get_provider_name(),
            "llm_model": self.llm_provider.get_model_name(),
            "embedding_provider": self.settings.embedding_provider,
            "document_count": self.get_document_count(),
        }
    
    def start_file_watcher(self) -> None:
        """Start watching for document changes."""
        def on_change():
            logger.info("Documents changed, updating vectorstore...")
            try:
                self.update_documents()
            except Exception as e:
                logger.error(f"Error updating vectorstore: {e}")
        
        self.document_processor.start_file_watcher(on_change)
    
    def stop_file_watcher(self) -> None:
        """Stop watching for document changes."""
        self.document_processor.stop_file_watcher()
