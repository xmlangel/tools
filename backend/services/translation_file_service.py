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
