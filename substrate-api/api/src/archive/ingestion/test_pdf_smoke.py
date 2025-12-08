#!/usr/bin/env python3
"""Simple smoke test for PDF extraction - can be run manually."""

def test_pdf_extraction():
    try:
        from parsers.pdf_text import extract_pdf_text
        
        # Test with empty bytes (simulating a PDF)
        result = extract_pdf_text(b"")
        print(f"Empty bytes test: '{result}' (length: {len(result)})")
        
        # Note: In production, you'd test with real PDF files
        # Example: result = extract_pdf_text("sample.pdf")
        
        return True
    except ImportError as e:
        print(f"Import error (PyMuPDF may not be installed): {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    if test_pdf_extraction():
        print("✓ PDF extraction module loaded successfully")
    else:
        print("✗ PDF extraction module failed to load")