"""RAG service for semantic search and response generation."""
import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
import chromadb

from .llm_provider import LLMProvider
from .document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

# IC-UFMT specific prompt template with zero-hallucination guardrails
IC_UFMT_PROMPT_TEMPLATE = """Voce e o Assistente Inteligente do Instituto de Computacao (IC) da Universidade Federal de Mato Grosso (UFMT).

Seu papel e auxiliar servidores, docentes e discentes com informacoes precisas sobre:
- Processos administrativos e burocraticos (SEI, solicitacoes de material, resolucoes CONSEP/UFMT)
- Processos academicos (aproveitamento de materias, matriculas, prazos, requisitos de graduacao)
- Informacoes institucionais (laboratorios de pesquisa, eventos como IC-NEXUS, iniciativas estudantis como CACOMP)
- Calendario academico e procedimentos oficiais

REGRAS CRITICAS DE RESPOSTA (ZERO ALUCINACAO):
1. RESPONDA APENAS com base nas informacoes contidas no contexto fornecido abaixo.
2. Se a informacao nao estiver no contexto, diga claramente: "Nao encontrei essa informacao nos documentos disponiveis."
3. NUNCA invente informacoes, datas, numeros de processos, resolucoes ou procedimentos.
4. Quando citar uma resolucao ou normativa, mencione a fonte especifica do documento.
5. Se a pergunta for ambigua, peca esclarecimentos antes de responder.

FORMATO DE RESPOSTA:
- Para processos administrativos: Explique O QUE fazer, ONDE fazer (sistema/setor), COMO fazer (passos) e POR QUE (normativa aplicavel).
- Para processos academicos: Indique requisitos, prazos e documentacao necessaria conforme os documentos.
- Seja objetivo e direto, mas completo nas explicacoes.

CONTEXTO DOS DOCUMENTOS:
{context}

PERGUNTA DO USUARIO:
{question}

RESPOSTA (baseada APENAS no contexto acima):"""


class RAGService:
    """RAG service using ChromaDB for vector storage and semantic search."""
    
    def __init__(
        self,
        vectorstore_path: Optional[str] = None,
        data_dir: Optional[str] = None,
        embedding_provider: Optional[str] = None
    ):
        self.vectorstore_path = Path(vectorstore_path or os.getenv("VECTORSTORE_DIR", "backend/vectorstore"))
        self.vectorstore_path.mkdir(parents=True, exist_ok=True)
        self.data_dir = Path(data_dir or os.getenv("DATA_DIR", "backend/data"))
        self.embedding_provider = embedding_provider or os.getenv("EMBEDDING_PROVIDER", "huggingface")
        self.document_processor = DocumentProcessor(data_dir=str(self.data_dir))
        self.llm_provider = LLMProvider()
        self.vectorstore: Optional[Chroma] = None
        self.embeddings = None
        self._initialize_embeddings()
        self._initialize_vectorstore()
        self._setup_file_watcher()
    
    def _initialize_embeddings(self):
        """Initialize embeddings based on provider."""
        logger.info(f"Initializing embeddings with provider: {self.embedding_provider}")
        
        if self.embedding_provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY is required for OpenAI embeddings")
            self.embeddings = OpenAIEmbeddings(api_key=api_key)
        elif self.embedding_provider == "huggingface":
            model_name = os.getenv("HUGGINGFACE_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
            logger.info(f"Loading HuggingFace embeddings model: {model_name}")
            self.embeddings = HuggingFaceEmbeddings(model_name=model_name)
        else:
            raise ValueError(f"Unsupported embedding provider: {self.embedding_provider}")
        
        logger.info("Embeddings initialized successfully")
    
    def _initialize_vectorstore(self):
        """Initialize or load the ChromaDB vector store."""
        try:
            # Try to load existing vectorstore
            if (self.vectorstore_path / "chroma.sqlite3").exists():
                logger.info("Loading existing vectorstore...")
                self.vectorstore = Chroma(
                    persist_directory=str(self.vectorstore_path),
                    embedding_function=self.embeddings
                )
                logger.info("Vectorstore loaded successfully")
            else:
                logger.info("Creating new vectorstore...")
                # Create empty vectorstore first
                self.vectorstore = Chroma(
                    persist_directory=str(self.vectorstore_path),
                    embedding_function=self.embeddings
                )
                # Process and add initial documents (if any)
                try:
                    self.update_documents()
                except Exception as e:
                    logger.warning(f"No documents found or error processing documents: {e}")
                    # Continue with empty vectorstore
        except Exception as e:
            logger.error(f"Error initializing vectorstore: {e}")
            raise
    
    def update_documents(self):
        """Process all documents and update the vector store."""
        try:
            logger.info("Processing documents and updating vectorstore...")
            chunks = self.document_processor.process_all_documents()
            
            if not chunks:
                logger.warning("No documents found to process")
                return
            
            # Convert chunks to LangChain documents
            documents = []
            for chunk in chunks:
                doc = Document(
                    page_content=chunk["text"],
                    metadata={
                        "source": chunk["source"],
                        "chunk_index": chunk["chunk_index"],
                        "file_path": chunk["file_path"]
                    }
                )
                documents.append(doc)
            
            # Clear existing collection and add new documents
            if self.vectorstore:
                # Delete the collection and recreate it
                try:
                    client = chromadb.PersistentClient(path=str(self.vectorstore_path))
                    client.delete_collection("langchain")
                except Exception:
                    pass  # Collection might not exist
                
                self.vectorstore = Chroma.from_documents(
                    documents=documents,
                    embedding=self.embeddings,
                    persist_directory=str(self.vectorstore_path)
                )
            
            logger.info(f"Vectorstore updated with {len(documents)} document chunks")
        except Exception as e:
            logger.error(f"Error updating documents: {e}")
            raise
    
    def _setup_file_watcher(self):
        """Setup file watcher to automatically update vectorstore on document changes."""
        def on_document_change():
            logger.info("Documents changed, updating vectorstore...")
            try:
                self.update_documents()
            except Exception as e:
                logger.error(f"Error updating vectorstore after file change: {e}")
        
        self.document_processor.start_file_watcher(on_document_change)
    
    def query(self, question: str, k: int = 4) -> Dict[str, Any]:
        """Query the RAG system with a question."""
        if not self.vectorstore:
            raise RuntimeError("Vectorstore not initialized")
        
        # Create a retrieval chain
        llm = self.llm_provider.get_llm()
        
        # Use IC-UFMT specific prompt with zero-hallucination guardrails
        PROMPT = PromptTemplate(
            template=IC_UFMT_PROMPT_TEMPLATE,
            input_variables=["context", "question"]
        )
        
        # Create retrieval QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": k}),
            chain_type_kwargs={"prompt": PROMPT},
            return_source_documents=True
        )
        
        # Execute query
        result = qa_chain.invoke({"query": question})
        
        # Extract sources
        sources = []
        if "source_documents" in result:
            sources = list(set([
                doc.metadata.get("source", "Unknown")
                for doc in result["source_documents"]
            ]))
        
        return {
            "answer": result.get("result", ""),
            "sources": sources
        }
    
    def get_document_count(self) -> int:
        """Get the number of documents in the vectorstore."""
        if not self.vectorstore:
            return 0
        try:
            return self.vectorstore._collection.count()
        except Exception:
            return 0
    
    def get_provider_info(self) -> Dict[str, str]:
        """Get information about the current LLM and embedding providers."""
        return {
            "llm_provider": self.llm_provider.get_provider_name(),
            "embedding_provider": self.embedding_provider
        }
