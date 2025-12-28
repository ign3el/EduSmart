"""
Document Processor Service
Handles PDF and DOCX file parsing and text extraction
"""

import io
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


class DocumentProcessor:
    """Extracts text content from PDF and DOCX files"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.docx', '.doc']
    
    async def process(self, file_path: Union[str, Path]) -> str:
        """
        Extract text from document file
        
        Args:
            file_path: Path to PDF or DOCX file
        
        Returns:
            Extracted text content
        
        Raises:
            ValueError: If file format is not supported
            ImportError: If required library is not installed
        """
        file_path = Path(file_path)
        
        if file_path.suffix.lower() == '.pdf':
            return await self._extract_from_pdf(file_path)
        elif file_path.suffix.lower() in ['.docx', '.doc']:
            return await self._extract_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
    async def _extract_from_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file"""
        if PdfReader is None:
            raise ImportError("PyPDF2 is not installed. Install with: pip install PyPDF2")
        
        try:
            text_content = []
            reader = PdfReader(str(file_path))
            
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)
            
            return "\n\n".join(text_content)
        
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")
    
    async def _extract_from_docx(self, file_path: Path) -> str:
        """Extract text from DOCX file"""
        if docx is None:
            raise ImportError("python-docx is not installed. Install with: pip install python-docx")
        
        try:
            doc = docx.Document(str(file_path))
            text_content = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)
            
            return "\n\n".join(text_content)
        
        except Exception as e:
            raise Exception(f"Error reading DOCX: {str(e)}")
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text
        
        Args:
            text: Raw extracted text
        
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]
        
        # Join with proper spacing
        cleaned = '\n\n'.join(lines)
        
        return cleaned
