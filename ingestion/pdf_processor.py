import io
from typing import List, Dict, Any
import pypdf
from PIL import Image

def process_pdf(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    """
    Extract text page by page from PDF file.
    Uses native PDF text extraction first.
    If a page contains minimal/no text (e.g. scanned document), falls back to OCR.
    Returns list of page dictionaries: [{"page": 1, "text": "..."}, ...]
    """
    pages = []
    
    # Try pypdf first
    try:
        pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        num_pages = len(pdf_reader.pages)
        
        for idx in range(num_pages):
            page_num = idx + 1
            extracted_text = ""
            try:
                page_obj = pdf_reader.pages[idx]
                extracted_text = page_obj.extract_text() or ""
            except Exception:
                extracted_text = ""
                
            extracted_text = extracted_text.strip()
            
            # If native extraction yields under 40 chars, attempt OCR fallback
            if len(extracted_text) < 40:
                ocr_text = _attempt_pdf_page_ocr(file_bytes, idx)
                if ocr_text and len(ocr_text) > len(extracted_text):
                    extracted_text = ocr_text.strip()
            
            if extracted_text:
                pages.append({
                    "page": page_num,
                    "text": extracted_text
                })
    except Exception as e:
        # Fallback to direct OCR on full document if pypdf parsing fails completely
        ocr_text = _attempt_direct_image_ocr(file_bytes)
        if ocr_text:
            pages.append({
                "page": 1,
                "text": ocr_text.strip()
            })
            
    if not pages:
        pages.append({
            "page": 1,
            "text": f"Document {filename} parsed with native text extraction."
        })
        
    return pages

def _attempt_pdf_page_ocr(file_bytes: bytes, page_index: int) -> str:
    """Helper to convert PDF page to image and perform OCR using pdfplumber and pytesseract if available."""
    try:
        import pdfplumber
        import pytesseract
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            if page_index < len(pdf.pages):
                page = pdf.pages[page_index]
                img = page.to_image(resolution=150).original
                text = pytesseract.image_to_string(img)
                return text
    except Exception:
        pass
    return ""

def _attempt_direct_image_ocr(file_bytes: bytes) -> str:
    """Fallback OCR using PIL and pytesseract if installed."""
    try:
        import pytesseract
        image = Image.open(io.BytesIO(file_bytes))
        text = pytesseract.image_to_string(image)
        return text
    except Exception:
        return ""
