"""
Document Processor Service
Handles PDF and DOCX file parsing and text extraction using non-blocking I/O.
"""
import asyncio
import logging
from pathlib import Path
from typing import Union

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    import docx
except ImportError:
    docx = None

logger = logging.getLogger(__name__)


class DocumentProcessorError(Exception):
    """Custom exception for document processing errors."""
    pass


class DocumentProcessor:
    """Extracts text content from PDF and DOCX files asynchronously."""

    def __init__(self):
        self.supported_formats = ['.pdf', '.docx', '.doc']
        if PdfReader is None:
            logger.warning("PyPDF2 is not installed. PDF processing will not be available.")
        if docx is None:
            logger.warning("python-docx is not installed. DOCX processing will not be available.")

    async def process(self, file_path: Union[str, Path]) -> str:
        """
        Extracts text from a document file asynchronously.

        Args:
            file_path: Path to the PDF or DOCX file.

        Returns:
            The extracted text content.

        Raises:
            DocumentProcessorError: If the file format is not supported or an error occurs.
            ImportError: If a required library is not installed for the given file type.
        """
        file_path = Path(file_path)
        file_suffix = file_path.suffix.lower()

        if file_suffix == '.pdf':
            if PdfReader is None:
                raise ImportError("PyPDF2 is not installed. Please run: pip install PyPDF2")
            return await self._extract_from_pdf(file_path)
        elif file_suffix in ['.docx', '.doc']:
            if docx is None:
                raise ImportError("python-docx is not installed. Please run: pip install python-docx")
            return await self._extract_from_docx(file_path)
        else:
            raise DocumentProcessorError(f"Unsupported file format: {file_suffix}")

    def _read_pdf_sync(self, file_path: Path) -> str:
        """Synchronous function to read and extract text from a PDF."""
        try:
            text_content = []
            reader = PdfReader(file_path)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)
            return "\n\n".join(text_content)
        except Exception as e:
            logger.error(f"Error reading PDF file at {file_path}: {e}", exc_info=True)
            raise DocumentProcessorError(f"Failed to read PDF file: {file_path.name}") from e

    async def _extract_from_pdf(self, file_path: Path) -> str:
        """Asynchronously extracts text from a PDF by running sync code in a thread."""
        return await asyncio.to_thread(self._read_pdf_sync, file_path)

    def _read_docx_sync(self, file_path: Path) -> str:
        """Synchronous function to read and extract text from a DOCX."""
        try:
            doc = docx.Document(file_path)
            text_content = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(text_content)
        except Exception as e:
            logger.error(f"Error reading DOCX file at {file_path}: {e}", exc_info=True)
            raise DocumentProcessorError(f"Failed to read DOCX file: {file_path.name}") from e

    async def _extract_from_docx(self, file_path: Path) -> str:
        """Asynchronously extracts text from a DOCX by running sync code in a thread."""
        return await asyncio.to_thread(self._read_docx_sync, file_path)