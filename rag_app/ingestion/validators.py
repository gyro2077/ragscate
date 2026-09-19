from pathlib import Path
import pymupdf as fitz  # PyMuPDF (fitz alias deprecated)

class UnsignedDocumentError(ValueError):
    """Lanzada cuando un documento de negocio no contiene firma electrónica."""
    pass

def is_pdf_signed(file_path: Path) -> bool:
    try:
        doc = fitz.open(file_path)
        for page in doc:
            for widget in page.widgets():
                if widget.field_type == fitz.PDF_WIDGET_TYPE_SIGNATURE:
                    return True
        return False
    except Exception as e:
        print(f"Error al analizar las firmas del PDF {file_path}: {e}")
        return False
