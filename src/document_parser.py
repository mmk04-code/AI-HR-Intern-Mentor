"""
Document parser module for Internship Task Review Assistant.
Extracts readable text from PDF, DOCX, TXT, and Markdown files with robust error handling.
"""

import io
import os
from typing import Dict, Any, Union, Optional
import pypdf
import docx


def parse_document(
    file_source: Union[str, bytes, io.BytesIO],
    filename: str
) -> Dict[str, Any]:
    """
    Parse a requirements or submission document and extract plain text.

    Args:
        file_source: File path (str), raw bytes (bytes), or BytesIO stream.
        filename: Original name of the file (to detect extension).

    Returns:
        dict: {
            "success": bool,
            "text": str,
            "error": Optional[str],
            "char_count": int,
            "filename": str
        }
    """
    if not filename:
        return {
            "success": False,
            "text": "",
            "error": "No filename provided.",
            "char_count": 0,
            "filename": ""
        }

    ext = os.path.splitext(filename)[1].lower()

    # Read bytes from source
    file_bytes: bytes = b""
    try:
        if isinstance(file_source, str):
            if not os.path.exists(file_source):
                return {
                    "success": False,
                    "text": "",
                    "error": f"File does not exist: {file_source}",
                    "char_count": 0,
                    "filename": filename
                }
            with open(file_source, "rb") as f:
                file_bytes = f.read()
        elif isinstance(file_source, bytes):
            file_bytes = file_source
        elif hasattr(file_source, "read"):
            # BytesIO or UploadedFile
            file_source.seek(0)
            file_bytes = file_source.read()
        else:
            return {
                "success": False,
                "text": "",
                "error": f"Unsupported file source type: {type(file_source)}",
                "char_count": 0,
                "filename": filename
            }
    except Exception as e:
        return {
            "success": False,
            "text": "",
            "error": f"Failed to read file data: {str(e)}",
            "char_count": 0,
            "filename": filename
        }

    if not file_bytes or len(file_bytes.strip()) == 0:
        return {
            "success": False,
            "text": "",
            "error": f"The file '{filename}' is empty (0 bytes).",
            "char_count": 0,
            "filename": filename
        }

    # Parse based on extension
    try:
        if ext in [".txt", ".md", ".markdown", ".rst"]:
            text = _parse_text(file_bytes)
        elif ext == ".pdf":
            text = _parse_pdf(file_bytes)
        elif ext in [".docx", ".doc"]:
            text = _parse_docx(file_bytes)
        elif ext in [".py", ".js", ".ts", ".html", ".css", ".json", ".yaml", ".yml", ".sql"]:
            text = _parse_text(file_bytes)
        else:
            return {
                "success": False,
                "text": "",
                "error": f"Unsupported file format '{ext}'. Please upload PDF, DOCX, TXT, or Markdown.",
                "char_count": 0,
                "filename": filename
            }

        cleaned_text = text.strip()
        if not cleaned_text:
            return {
                "success": False,
                "text": "",
                "error": f"No readable text could be extracted from '{filename}'.",
                "char_count": 0,
                "filename": filename
            }

        return {
            "success": True,
            "text": cleaned_text,
            "error": None,
            "char_count": len(cleaned_text),
            "filename": filename
        }

    except Exception as e:
        return {
            "success": False,
            "text": "",
            "error": f"Error parsing '{filename}': {str(e)}",
            "char_count": 0,
            "filename": filename
        }


def _parse_text(file_bytes: bytes) -> str:
    """Parse plain text with fallback encoding support."""
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            return file_bytes.decode(enc)
        except UnicodeDecodeError:
            continue
    return file_bytes.decode("utf-8", errors="replace")


def _parse_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF pages using pypdf."""
    stream = io.BytesIO(file_bytes)
    reader = pypdf.PdfReader(stream)
    pages_text = []
    for i, page in enumerate(reader.pages):
        page_content = page.extract_text()
        if page_content:
            pages_text.append(f"--- Page {i+1} ---\n" + page_content)
    return "\n\n".join(pages_text)


def _parse_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX paragraphs and tables using python-docx."""
    stream = io.BytesIO(file_bytes)
    doc = docx.Document(stream)
    full_text = []

    # Paragraphs
    for para in doc.paragraphs:
        if para.text.strip():
            full_text.append(para.text)

    # Tables
    for table in doc.tables:
        for row in table.rows:
            row_data = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if row_data:
                full_text.append(" | ".join(row_data))

    return "\n\n".join(full_text)
