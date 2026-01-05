"""Document processing service for extracting and chunking documents."""
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Process documents from various formats and create text chunks."""
    
    def __init__(self, data_dir: str = "backend/data", chunk_size: int = 1000, chunk_overlap: int = 200):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        self.observer: Optional[Observer] = None
        self.on_document_change_callback = None
    
    def extract_text_from_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file."""
        try:
            text = ""
            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {e}")
            raise
    
    def extract_text_from_txt(self, file_path: Path) -> str:
        """Extract text from TXT file."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error reading TXT file {file_path}: {e}")
            raise
    
    def extract_text_from_md(self, file_path: Path) -> str:
        """Extract text from Markdown file."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error reading Markdown file {file_path}: {e}")
            raise
    
    def extract_text(self, file_path: Path) -> str:
        """Extract text from a document based on its extension."""
        suffix = file_path.suffix.lower()
        
        if suffix == ".pdf":
            return self.extract_text_from_pdf(file_path)
        elif suffix == ".txt":
            return self.extract_text_from_txt(file_path)
        elif suffix in [".md", ".markdown"]:
            return self.extract_text_from_md(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")
    
    def process_document(self, file_path: Path) -> List[Dict[str, any]]:
        """Process a document and return chunks with metadata."""
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        text = self.extract_text(file_path)
        chunks = self.text_splitter.split_text(text)
        
        # Create chunks with metadata
        chunks_with_metadata = []
        for i, chunk in enumerate(chunks):
            chunks_with_metadata.append({
                "text": chunk,
                "source": str(file_path.name),
                "chunk_index": i,
                "file_path": str(file_path)
            })
        
        logger.info(f"Processed {file_path.name}: {len(chunks)} chunks created")
        return chunks_with_metadata
    
    def process_all_documents(self) -> List[Dict[str, any]]:
        """Process all supported documents in the data directory."""
        all_chunks = []
        supported_extensions = {".pdf", ".txt", ".md", ".markdown"}
        
        for file_path in self.data_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                try:
                    chunks = self.process_document(file_path)
                    all_chunks.extend(chunks)
                except Exception as e:
                    logger.error(f"Failed to process {file_path}: {e}")
        
        return all_chunks
    
    def start_file_watcher(self, callback):
        """Start watching the data directory for file changes."""
        self.on_document_change_callback = callback
        
        class DocumentEventHandler(FileSystemEventHandler):
            def __init__(self, processor):
                self.processor = processor
            
            def on_created(self, event):
                if not event.is_directory:
                    self._handle_file_change(event.src_path)
            
            def on_modified(self, event):
                if not event.is_directory:
                    self._handle_file_change(event.src_path)
            
            def _handle_file_change(self, file_path):
                path = Path(file_path)
                if path.suffix.lower() in {".pdf", ".txt", ".md", ".markdown"}:
                    logger.info(f"Document changed: {file_path}")
                    if self.processor.on_document_change_callback:
                        self.processor.on_document_change_callback()
        
        event_handler = DocumentEventHandler(self)
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.data_dir), recursive=False)
        self.observer.start()
        logger.info(f"Started file watcher for {self.data_dir}")
    
    def stop_file_watcher(self):
        """Stop watching the data directory."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("Stopped file watcher")
