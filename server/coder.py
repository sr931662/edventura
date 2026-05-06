#!/usr/bin/env python3
"""
Project Code Dumper
Recursively exports source code files into CODEDUMP.txt while excluding
sensitive, binary, and commonly ignored files/folders.
"""

from pathlib import Path
import fnmatch

OUTPUT_FILE = "SERVER CODEDUMP.txt"
ROOT_DIR = Path(".").resolve()
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB per file

# Directories to ignore
IGNORE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    "dist",
    "build",
    ".idea",
    ".vscode",
    ".mypy_cache",
    ".pytest_cache",
    "temp"
}

# File patterns to ignore
IGNORE_FILES = [
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "*.crt",
    "*.pfx",
    "*.p12",
    "*.pyc",
    "*.log",
    "*.sqlite3",
    "*.db",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "SERVER CODEDUMP.txt",
    "coder.py",
]

# Extensions considered binary/non-source
BINARY_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".ico",
    ".mp3", ".mp4", ".wav", ".avi", ".mov",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".exe", ".dll", ".so", ".bin",
    ".pdf", ".docx", ".xlsx", ".pptx",
}


def should_ignore(path: Path) -> bool:
    """Determine if file or directory should be ignored."""
    for part in path.parts:
        if part in IGNORE_DIRS:
            return True

    for pattern in IGNORE_FILES:
        if fnmatch.fnmatch(path.name, pattern):
            return True

    if path.suffix.lower() in BINARY_EXTENSIONS:
        return True

    return False


def is_text_file(file_path: Path) -> bool:
    """Check if file is likely text-readable."""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            if b"\x00" in chunk:
                return False
        return True
    except Exception:
        return False


def dump_codebase():
    files_dumped = 0

    with open(OUTPUT_FILE, "w", encoding="utf-8") as output:
        for file_path in sorted(ROOT_DIR.rglob("*")):
            if not file_path.is_file():
                continue

            if should_ignore(file_path):
                continue

            if file_path.stat().st_size > MAX_FILE_SIZE:
                continue

            if not is_text_file(file_path):
                continue

            rel_path = file_path.relative_to(ROOT_DIR)

            try:
                content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                try:
                    content = file_path.read_text(encoding="latin-1")
                except Exception:
                    continue
            except Exception:
                continue

            output.write("=" * 80 + "\n")
            output.write(f"FILE: {rel_path}\n")
            output.write("=" * 80 + "\n\n")
            output.write(content)
            output.write("\n\n")

            files_dumped += 1

    print(f"Done. Exported {files_dumped} files into {OUTPUT_FILE}")


if __name__ == "__main__":
    dump_codebase()
