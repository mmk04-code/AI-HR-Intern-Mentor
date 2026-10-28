"""
Submission reader module for Internship Task Review Assistant.
Safely processes candidate uploads (ZIP or individual files) and public GitHub repositories.
Never executes code; enforces strict size and file count limits.
"""

import io
import os
import re
import zipfile
from typing import Dict, List, Any, Union, Optional
import requests

from src.document_parser import parse_document

MAX_FILES_COUNT = 50
MAX_SINGLE_FILE_BYTES = 500 * 1024  # 500 KB
MAX_TOTAL_CHARS = 200_000           # ~50,000 tokens safe limit

IGNORED_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv", "env",
    "dist", "build", ".next", ".cache", ".idea", ".vscode"
}

IGNORED_EXTENSIONS = {
    ".exe", ".dll", ".so", ".dylib", ".bin", ".iso", ".zip", ".tar", ".gz",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp", ".svg",
    ".mp3", ".mp4", ".wav", ".avi", ".mov",
    ".pyc", ".pyo", ".pyd", ".class", ".o", ".obj"
}

TEXT_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".json",
    ".yaml", ".yml", ".sql", ".sh", ".bat", ".ps1", ".md", ".txt",
    ".csv", ".xml", ".env.example", ".toml", ".ini", ".cfg", ".java",
    ".c", ".cpp", ".h", ".cs", ".go", ".rs", ".php", ".rb"
}


def process_uploaded_submission(
    file_source: Union[str, bytes, io.BytesIO],
    filename: str
) -> Dict[str, Any]:
    """
    Process an uploaded submission (single file or ZIP archive).
    """
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".zip":
        return _process_zip_file(file_source, filename)
    else:
        # Single document or source file
        parsed = parse_document(file_source, filename)
        if not parsed["success"]:
            return {
                "success": False,
                "error": parsed["error"],
                "files_summary": [],
                "raw_content": "",
                "total_files": 0
            }

        return {
            "success": True,
            "error": None,
            "files_summary": [{
                "path": filename,
                "size": len(parsed["text"]),
                "type": ext.lstrip(".") or "txt"
            }],
            "raw_content": f"=== File: {filename} ===\n{parsed['text']}\n",
            "total_files": 1
        }


def _process_zip_file(
    file_source: Union[str, bytes, io.BytesIO],
    zip_filename: str
) -> Dict[str, Any]:
    """
    Safely inspect and extract text from a ZIP file in memory.
    """
    try:
        if isinstance(file_source, str):
            zf = zipfile.ZipFile(file_source, 'r')
        elif isinstance(file_source, bytes):
            zf = zipfile.ZipFile(io.BytesIO(file_source), 'r')
        else:
            file_source.seek(0)
            zf = zipfile.ZipFile(file_source, 'r')
    except Exception as e:
        return {
            "success": False,
            "error": f"Invalid or corrupted ZIP archive '{zip_filename}': {str(e)}",
            "files_summary": [],
            "raw_content": "",
            "total_files": 0
        }

    files_summary = []
    content_chunks = []
    total_chars = 0
    skipped_count = 0

    with zf:
        infolist = zf.infolist()
        # Sort to prioritize README and main files first
        def file_priority(info):
            fname = os.path.basename(info.filename).lower()
            if "readme" in fname:
                return 0
            if fname in ["app.py", "main.py", "index.js", "package.json", "requirements.txt"]:
                return 1
            return 2

        sorted_infos = sorted(infolist, key=file_priority)

        for info in sorted_infos:
            if info.is_dir():
                continue

            # Path check for ignored directories
            parts = info.filename.replace("\\", "/").split("/")
            if any(part in IGNORED_DIRS for part in parts):
                continue

            ext = os.path.splitext(info.filename)[1].lower()
            if ext in IGNORED_EXTENSIONS:
                skipped_count += 1
                continue

            # Check file size
            if info.file_size > MAX_SINGLE_FILE_BYTES:
                skipped_count += 1
                continue

            if len(files_summary) >= MAX_FILES_COUNT or total_chars >= MAX_TOTAL_CHARS:
                break

            try:
                raw_bytes = zf.read(info.filename)
                # Decode text
                parsed = parse_document(raw_bytes, os.path.basename(info.filename))
                if parsed["success"]:
                    text = parsed["text"]
                    clean_path = info.filename.replace("\\", "/")
                    files_summary.append({
                        "path": clean_path,
                        "size": len(text),
                        "type": ext.lstrip(".") or "text"
                    })
                    chunk = f"=== File: {clean_path} ===\n{text}\n"
                    content_chunks.append(chunk)
                    total_chars += len(chunk)
            except Exception:
                skipped_count += 1
                continue

    if not files_summary:
        return {
            "success": False,
            "error": f"No readable source or document files found in '{zip_filename}'.",
            "files_summary": [],
            "raw_content": "",
            "total_files": 0
        }

    raw_content = "\n".join(content_chunks)
    return {
        "success": True,
        "error": None,
        "files_summary": files_summary,
        "raw_content": raw_content,
        "total_files": len(files_summary),
        "skipped_files": skipped_count
    }


def parse_github_url(url: str) -> Optional[Dict[str, str]]:
    """
    Parse a GitHub URL into owner and repository name.
    Supported formats:
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - http://github.com/owner/repo
    - github.com/owner/repo
    """
    clean_url = url.strip()
    match = re.search(r"github\.com[/:]([\w.-]+)/([\w.-]+?)(?:\.git|/.*)?$", clean_url, re.IGNORECASE)
    if match:
        owner = match.group(1)
        repo = match.group(2)
        return {"owner": owner, "repo": repo}
    return None


def fetch_github_repository(url: str) -> Dict[str, Any]:
    """
    Fetch repository structure and file contents from a public GitHub repository.
    Enforces rate limits, size limits, and security boundaries.
    """
    parsed = parse_github_url(url)
    if not parsed:
        return {
            "success": False,
            "error": f"Invalid GitHub repository URL '{url}'. Expected format: https://github.com/owner/repository",
            "files_summary": [],
            "raw_content": "",
            "total_files": 0
        }

    owner = parsed["owner"]
    repo = parsed["repo"]

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Internship-Task-Review-Assistant/1.0"
    }

    # 1. Check if repo exists and is public
    repo_api_url = f"https://api.github.com/repos/{owner}/{repo}"
    try:
        resp = requests.get(repo_api_url, headers=headers, timeout=10)
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Network error connecting to GitHub: {str(e)}",
            "files_summary": [],
            "raw_content": "",
            "total_files": 0
        }

    if resp.status_code == 404:
        return {
            "success": False,
            "error": f"GitHub repository '{owner}/{repo}' not found or is private. Please verify the URL.",
            "files_summary": [],
            "raw_content": "",
            "total_files": 0
        }
    elif resp.status_code == 403:
        rate_reset = resp.headers.get("X-RateLimit-Reset", "soon")
        return {
            "success": False,
            "error": f"GitHub API rate limit exceeded for anonymous requests. Please try again later (Reset: {rate_reset}) or upload a ZIP archive of the repository.",
            "files_summary": [],
            "raw_content": "",
            "total_files": 0
        }
    elif resp.status_code != 200:
        return {
            "success": False,
            "error": f"GitHub API returned error {resp.status_code}: {resp.text[:200]}",
            "files_summary": [],
            "raw_content": "",
            "total_files": 0
        }

    repo_data = resp.json()
    if repo_data.get("private"):
        return {
            "success": False,
            "error": f"Repository '{owner}/{repo}' is private. Module 1 only supports public repositories.",
            "files_summary": [],
            "raw_content": "",
            "total_files": 0
        }

    default_branch = repo_data.get("default_branch", "main")

    # 2. Fetch Git tree
    tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
    try:
        tree_resp = requests.get(tree_url, headers=headers, timeout=10)
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Failed to retrieve repository tree: {str(e)}",
            "files_summary": [],
            "raw_content": "",
            "total_files": 0
        }

    if tree_resp.status_code != 200:
        # Fallback to contents API root
        return _fetch_github_contents_fallback(owner, repo, headers)

    tree_data = tree_resp.json()
    items = tree_data.get("tree", [])

    files_to_fetch = []
    for item in items:
        if item.get("type") != "blob":
            continue
        path = item.get("path", "")
        parts = path.split("/")
        if any(p in IGNORED_DIRS for p in parts):
            continue
        ext = os.path.splitext(path)[1].lower()
        if ext in IGNORED_EXTENSIONS:
            continue
        if ext in TEXT_EXTENSIONS or os.path.basename(path).lower() in ["dockerfile", "makefile", "license", "procfile"]:
            size = item.get("size", 0)
            if size <= MAX_SINGLE_FILE_BYTES:
                files_to_fetch.append({"path": path, "size": size})

    # Sort files prioritizing README and entry files
    def gh_priority(f):
        fname = os.path.basename(f["path"]).lower()
        if "readme" in fname:
            return 0
        if fname in ["app.py", "main.py", "index.js", "package.json", "requirements.txt"]:
            return 1
        return 2

    files_to_fetch = sorted(files_to_fetch, key=gh_priority)[:MAX_FILES_COUNT]

    files_summary = []
    content_chunks = []
    total_chars = 0

    for file_meta in files_to_fetch:
        if total_chars >= MAX_TOTAL_CHARS:
            break
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{default_branch}/{file_meta['path']}"
        try:
            raw_resp = requests.get(raw_url, timeout=8)
            if raw_resp.status_code == 200:
                file_text = raw_resp.text
                files_summary.append({
                    "path": file_meta["path"],
                    "size": len(file_text),
                    "type": os.path.splitext(file_meta["path"])[1].lstrip(".") or "text"
                })
                chunk = f"=== File: {file_meta['path']} ===\n{file_text}\n"
                content_chunks.append(chunk)
                total_chars += len(chunk)
        except Exception:
            continue

    if not files_summary:
        return {
            "success": False,
            "error": f"No readable code or text files could be fetched from '{owner}/{repo}'.",
            "files_summary": [],
            "raw_content": "",
            "total_files": 0
        }

    return {
        "success": True,
        "error": None,
        "files_summary": files_summary,
        "raw_content": "\n".join(content_chunks),
        "total_files": len(files_summary),
        "repo_name": f"{owner}/{repo}",
        "default_branch": default_branch
    }


def _fetch_github_contents_fallback(owner: str, repo: str, headers: dict) -> Dict[str, Any]:
    """Fallback fetch via root contents API when tree API is blocked or truncated."""
    contents_url = f"https://api.github.com/repos/{owner}/{repo}/contents"
    try:
        resp = requests.get(contents_url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return {
                "success": False,
                "error": f"Failed to fetch repository contents ({resp.status_code}).",
                "files_summary": [],
                "raw_content": "",
                "total_files": 0
            }
        items = resp.json()
        files_summary = []
        content_chunks = []
        for item in items:
            if item.get("type") == "file":
                path = item.get("name", "")
                download_url = item.get("download_url")
                if download_url and (os.path.splitext(path)[1].lower() in TEXT_EXTENSIONS or "readme" in path.lower()):
                    f_resp = requests.get(download_url, timeout=8)
                    if f_resp.status_code == 200:
                        files_summary.append({"path": path, "size": len(f_resp.text), "type": "code"})
                        content_chunks.append(f"=== File: {path} ===\n{f_resp.text}\n")
        return {
            "success": True,
            "error": None,
            "files_summary": files_summary,
            "raw_content": "\n".join(content_chunks),
            "total_files": len(files_summary)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error in contents fallback: {str(e)}",
            "files_summary": [],
            "raw_content": "",
            "total_files": 0
        }
