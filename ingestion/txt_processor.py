from typing import List, Dict, Any

def process_txt(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    """
    Extract text from plain text (.txt) file.
    Returns page structure [{"page": 1, "text": "..."}]
    """
    try:
        # Try UTF-8 decoding, fallback to latin-1
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = file_bytes.decode("latin-1")
            
        cleaned_text = text.strip()
        if not cleaned_text:
            cleaned_text = f"Text document {filename} was empty."
            
        return [{
            "page": 1,
            "text": cleaned_text
        }]
    except Exception as e:
        return [{
            "page": 1,
            "text": f"Error parsing txt document {filename}: {str(e)}"
        }]
