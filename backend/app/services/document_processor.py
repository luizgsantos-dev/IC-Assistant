"""Document processing service for extracting and chunking documents.

Supports PDF, TXT, and Markdown files.
"""
import logging
from pathlib import Path
from typing import List, Dict, Optional, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ..config import Settings, get_settings

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Process documents from various formats and create text chunks."""
    
    SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".markdown"}
    
    def __init__(
        self,
        settings: Optional[Settings] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        """Initialize the document processor.
        
        Args:
            settings: Application settings. If None, will use global settings.
            chunk_size: Size of text chunks in characters.
            chunk_overlap: Overlap between chunks in characters.
        """
        self.settings = settings or get_settings()
        self.data_dir = Path(self.settings.data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        
        self.observer: Optional[Observer] = None
        self._on_change_callback: Optional[Callable] = None
    
    def extract_text_from_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file using pypdf.
        
        Args:
            file_path: Path to the PDF file.
            
        Returns:
            Extracted text content.
        """
        try:
            text_parts = []
            reader = PdfReader(file_path)
            
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            
            return "\n".join(text_parts)
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {e}")
            raise
    
    def extract_text_from_txt(self, file_path: Path) -> str:
        """Extract text from TXT file.
        
        Args:
            file_path: Path to the TXT file.
            
        Returns:
            File content.
        """
        try:
            # Try UTF-8 first, fall back to latin-1
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    return file.read()
            except UnicodeDecodeError:
                with open(file_path, "r", encoding="latin-1") as file:
                    return file.read()
        except Exception as e:
            logger.error(f"Error reading TXT file {file_path}: {e}")
            raise
    
    def extract_text_from_md(self, file_path: Path) -> str:
        """Extract text from Markdown file.
        
        Args:
            file_path: Path to the Markdown file.
            
        Returns:
            File content.
        """
        return self.extract_text_from_txt(file_path)
    
    def extract_text(self, file_path: Path) -> str:
        """Extract text from a document based on its extension.
        
        Args:
            file_path: Path to the document.
            
        Returns:
            Extracted text content.
            
        Raises:
            ValueError: If file format is not supported.
        """
        suffix = file_path.suffix.lower()
        
        if suffix == ".pdf":
            return self.extract_text_from_pdf(file_path)
        elif suffix == ".txt":
            return self.extract_text_from_txt(file_path)
        elif suffix in (".md", ".markdown"):
            return self.extract_text_from_md(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")
    
    def process_document(self, file_path: Path) -> List[Dict[str, any]]:
        """Process a document and return chunks with metadata.
        
        Args:
            file_path: Path to the document.
            
        Returns:
            List of chunks with metadata.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        text = self.extract_text(file_path)
        
        if not text.strip():
            logger.warning(f"Empty content in document: {file_path}")
            return []
        
        chunks = self.text_splitter.split_text(text)
        
        # Create chunks with metadata
        chunks_with_metadata = []
        for i, chunk in enumerate(chunks):
            chunks_with_metadata.append({
                "text": chunk,
                "source": file_path.name,
                "chunk_index": i,
                "file_path": str(file_path),
                "total_chunks": len(chunks),
            })
        
        logger.info(f"Processed {file_path.name}: {len(chunks)} chunks created")
        return chunks_with_metadata
    
    def process_all_documents(self) -> List[Dict[str, any]]:
        """Process all supported documents in the data directory.
        
        Returns:
            List of all chunks with metadata.
        """
        all_chunks = []
        processed_count = 0
        error_count = 0
        
        for file_path in self.data_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                try:
                    chunks = self.process_document(file_path)
                    all_chunks.extend(chunks)
                    processed_count += 1
                except Exception as e:
                    logger.error(f"Failed to process {file_path}: {e}")
                    error_count += 1
        
        logger.info(
            f"Document processing complete: {processed_count} files processed, "
            f"{error_count} errors, {len(all_chunks)} total chunks"
        )
        
        return all_chunks
    
    def get_document_list(self) -> List[Dict[str, str]]:
        """Get list of documents in the data directory.
        
        Returns:
            List of document information dicts.
        """
        documents = []
        
        for file_path in self.data_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                documents.append({
                    "filename": file_path.name,
                    "file_type": file_path.suffix.lower(),
                    "size_bytes": file_path.stat().st_size,
                })
        
        return documents
    
    def start_file_watcher(self, callback: Callable) -> None:
        """Start watching the data directory for file changes.
        
        Args:
            callback: Function to call when documents change.
        """
        self._on_change_callback = callback
        
        class DocumentEventHandler(FileSystemEventHandler):
            def __init__(self, processor: "DocumentProcessor"):
                self.processor = processor
                self._debounce_timer = None
            
            def _trigger_callback(self):
                if self.processor._on_change_callback:
                    self.processor._on_change_callback()
            
            def on_created(self, event):
                if not event.is_directory:
                    self._handle_file_change(event.src_path)
            
            def on_modified(self, event):
                if not event.is_directory:
                    self._handle_file_change(event.src_path)
            
            def on_deleted(self, event):
                if not event.is_directory:
                    self._handle_file_change(event.src_path)
            
            def _handle_file_change(self, file_path: str):
                path = Path(file_path)
                if path.suffix.lower() in DocumentProcessor.SUPPORTED_EXTENSIONS:
                    logger.info(f"Document changed: {file_path}")
                    self._trigger_callback()
        
        event_handler = DocumentEventHandler(self)
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.data_dir), recursive=False)
        self.observer.start()
        logger.info(f"Started file watcher for {self.data_dir}")
    
    def stop_file_watcher(self) -> None:
        """Stop watching the data directory."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            logger.info("Stopped file watcher")
