import os
from typing import List, Dict, Any
from ingestion.pdf_processor import process_pdf
from ingestion.image_processor import process_image
from ingestion.docx_processor import process_docx
from ingestion.txt_processor import process_txt

SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".docx", ".txt"}

class IngestionPipeline:
    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def process_file(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Main ingestion entry point.
        Detects format, executes format processor, normalizes text into common format,
        and generates text chunks with page number metadata.
        """
        ext = os.path.splitext(filename)[1].lower()
        if not ext:
            ext = ".txt"

        if ext not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file format '{ext}'. Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")

        # Format routing
        if ext == ".pdf":
            pages = process_pdf(file_bytes, filename)
        elif ext in [".jpg", ".jpeg", ".png"]:
            pages = process_image(file_bytes, filename)
        elif ext == ".docx":
            pages = process_docx(file_bytes, filename)
        elif ext == ".txt":
            pages = process_txt(file_bytes, filename)
        else:
            # Future hooks for DICOM / Handwritten OCR
            pages = self._future_format_hook(file_bytes, filename, ext)

        # Normalize text and create RAG chunks
        full_text = "\n\n".join([f"[Page {p['page']}]\n{p['text']}" for p in pages])
        chunks = self.chunk_pages(pages)

        return {
            "filename": filename,
            "file_type": ext.lstrip("."),
            "page_count": len(pages),
            "full_text": full_text,
            "pages": pages,
            "chunks": chunks
        }

    def chunk_pages(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Splits page text into overlapping chunks, maintaining page_number metadata.
        """
        chunks = []
        chunk_counter = 1

        for page in pages:
            page_num = page["page"]
            text = page["text"]

            if not text:
                continue

            # Paragraph or sliding window chunking
            words = text.split()
            if not words:
                continue

            current_words = []
            current_len = 0

            for word in words:
                current_words.append(word)
                current_len += len(word) + 1

                if current_len >= self.chunk_size:
                    chunk_text = " ".join(current_words)
                    chunks.append({
                        "chunk_index": chunk_counter,
                        "page_number": page_num,
                        "content": chunk_text
                    })
                    chunk_counter += 1
                    # Keep overlap words
                    overlap_words_count = max(1, int(len(current_words) * (self.chunk_overlap / self.chunk_size)))
                    current_words = current_words[-overlap_words_count:]
                    current_len = sum(len(w) + 1 for w in current_words)

            if current_words:
                chunk_text = " ".join(current_words)
                chunks.append({
                    "chunk_index": chunk_counter,
                    "page_number": page_num,
                    "content": chunk_text
                })
                chunk_counter += 1

        return chunks

    def _future_format_hook(self, file_bytes: bytes, filename: str, ext: str) -> List[Dict[str, Any]]:
        """
        Extensibility hook for future features (e.g. DICOM, TrOCR handwritten reports).
        """
        return [{
            "page": 1,
            "text": f"Format {ext} handled by extensibility pipeline hook for {filename}."
        }]
