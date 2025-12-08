try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

def extract_pdf_text(path_or_bytes) -> str:
    """Extract text from PDF. Returns empty string if PyMuPDF not available."""
    if not PYMUPDF_AVAILABLE:
        return ""
    
    try:
        doc = fitz.open(stream=path_or_bytes, filetype="pdf") if isinstance(path_or_bytes, (bytes, bytearray)) else fitz.open(path_or_bytes)
        parts = []
        for page in doc:
            t = page.get_text("text")
            if t:
                parts.append(t)
        return "\n\n".join(parts).strip()
    except Exception:
        return ""