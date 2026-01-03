import logging
import io
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from langdetect import detect, LangDetectException
import PyPDF2
import docx

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/upload",
    tags=["Upload"],
)

class TextExtractionResponse(BaseModel):
    text: str
    language_code: str
    suggested_engine: str

@router.post("/extract-text", response_model=TextExtractionResponse)
async def extract_text_from_file(file: UploadFile = File(...)):
    """
    Uploads a file, extracts text, detects language, and suggests a TTS engine.
    Supports .txt, .pdf, and .docx files.
    """
    try:
        # Read file content
        content = await file.read()
        filename = file.filename.lower() if file.filename else ""
        text = ""
        
        if filename.endswith(".pdf"):
            try:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
                for page in pdf_reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            except Exception as e:
                logger.error(f"Error parsing PDF: {e}")
                raise HTTPException(status_code=400, detail="Failed to extract text from PDF.")
        
        elif filename.endswith(".docx"):
            try:
                doc = docx.Document(io.BytesIO(content))
                text = "\n".join([para.text for para in doc.paragraphs])
            except Exception as e:
                logger.error(f"Error parsing DOCX: {e}")
                raise HTTPException(status_code=400, detail="Failed to extract text from DOCX.")
        
        else:
            # Default to text decoding for .txt or others
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail="Invalid file encoding. Please upload a UTF-8 text file, PDF, or DOCX.")

        if not text.strip():
            raise HTTPException(status_code=400, detail="File is empty or contains no readable text.")

        # Detect Language
        try:
            lang_code = detect(text)
        except LangDetectException:
            lang_code = "unknown"

        # Determine Priority
        if lang_code == "ar":
            suggested_engine = "piper" # Prioritize Piper for Arabic
        else:
            suggested_engine = "kokoro" # Prioritize Kokoro for En/Hi/Others

        return {"text": text, "language_code": lang_code, "suggested_engine": suggested_engine}

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Error processing file upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))