import os
import io
import logging
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)

def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """
    Extracts text from a file based on its extension.
    Supported: .txt, .md, .pdf
    """
    ext = os.path.splitext(filename)[1].lower()
    
    if ext in ['.txt', '.md']:
        return file_content.decode('utf-8', errors='ignore')
    
    elif ext == '.pdf':
        try:
            pdf_file = io.BytesIO(file_content)
            reader = PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
            
    else:
        raise ValueError(f"Unsupported file extension: {ext}")

def extract_text_from_image(file_content: bytes, filename: str) -> str:
    """
    Placeholder for image text extraction.
    Currently returns a message since OCR/Vision logic needs to be integrated with LLM or local library.
    """
    # For now, we will return a descriptive text that the frontend can display or the LLM can process if it's a vision model.
    # If the user is using a vision model, we should ideally pass the image bytes to the LLM directly.
    return "[Image processing requested. This feature requires a Vision-capable LLM or OCR integration.]"
