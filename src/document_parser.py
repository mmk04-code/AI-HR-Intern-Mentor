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


def parse_spreadsheet(
    file_source: Union[str, bytes, io.BytesIO],
    filename: str
) -> Dict[str, Any]:
    """
    Parse an Excel (.xlsx, .xls) or CSV file containing intern/employee rosters.

    Returns:
        dict: {
            "success": bool,
            "records": List[Dict[str, str]],
            "count": int,
            "error": Optional[str],
            "filename": str
        }
    """
    import pandas as pd

    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".xlsx", ".xls", ".csv"]:
        return {
            "success": False,
            "records": [],
            "count": 0,
            "error": f"Unsupported spreadsheet format '{ext}'. Expected .xlsx, .xls, or .csv.",
            "filename": filename
        }

    try:
        # Load dataframe
        if isinstance(file_source, (bytes, io.BytesIO)) or hasattr(file_source, "read"):
            if isinstance(file_source, bytes):
                stream = io.BytesIO(file_source)
            elif hasattr(file_source, "read") and not isinstance(file_source, io.BytesIO):
                file_source.seek(0)
                stream = io.BytesIO(file_source.read())
            else:
                stream = file_source
                stream.seek(0)

            if ext in [".xlsx", ".xls"]:
                df = pd.read_excel(stream)
            else:
                df = pd.read_csv(stream)
        else:
            if ext in [".xlsx", ".xls"]:
                df = pd.read_excel(file_source)
            else:
                df = pd.read_csv(file_source)

        if df.empty:
            return {
                "success": False,
                "records": [],
                "count": 0,
                "error": f"The spreadsheet '{filename}' contains no rows.",
                "filename": filename
            }

        # Normalize column names
        col_map = {}
        for col in df.columns:
            clean = str(col).strip().lower().replace("_", " ")
            if any(k in clean for k in ["candidate name", "intern name", "full name", "employee name", "name"]):
                if "name" not in col_map:
                    col_map["name"] = col
            elif any(k in clean for k in ["email address", "mail", "email"]):
                if "email" not in col_map:
                    col_map["email"] = col
            elif any(k in clean for k in ["role", "designation", "position", "title"]):
                if "role" not in col_map:
                    col_map["role"] = col
            elif any(k in clean for k in ["batch", "cohort", "group"]):
                if "batch" not in col_map:
                    col_map["batch"] = col

        if "name" not in col_map and "email" not in col_map:
            return {
                "success": False,
                "records": [],
                "count": 0,
                "error": f"Could not detect 'Name' or 'Email' columns in '{filename}'. Found columns: {list(df.columns)}",
                "filename": filename
            }

        records = []
        for _, row in df.iterrows():
            name_val = str(row[col_map["name"]]).strip() if "name" in col_map and pd.notna(row[col_map["name"]]) else ""
            email_val = str(row[col_map["email"]]).strip() if "email" in col_map and pd.notna(row[col_map["email"]]) else ""
            role_val = str(row[col_map["role"]]).strip() if "role" in col_map and pd.notna(row[col_map["role"]]) else "Software Engineering Intern"
            batch_val = str(row[col_map["batch"]]).strip() if "batch" in col_map and pd.notna(row[col_map["batch"]]) else "Batch-2026-A"

            if name_val or email_val:
                if not name_val:
                    name_val = email_val.split("@")[0].capitalize()
                if not email_val:
                    email_val = f"{name_val.lower().replace(' ', '.')}@example.com"

                records.append({
                    "name": name_val,
                    "email": email_val,
                    "role": role_val,
                    "batch": batch_val
                })

        return {
            "success": True,
            "records": records,
            "count": len(records),
            "error": None,
            "filename": filename
        }

    except Exception as e:
        return {
            "success": False,
            "records": [],
            "count": 0,
            "error": f"Failed to parse spreadsheet '{filename}': {str(e)}",
            "filename": filename
        }

