#!/usr/bin/env python3
"""
WPF / .NET Desktop Project Code Dumper
Exports source code files into CODEDUMP.txt while excluding build artifacts,
sensitive files, binaries, and unnecessary generated folders.
"""

from pathlib import Path
import fnmatch

OUTPUT_FILE = "CODEDUMP.txt"
ROOT_DIR = Path(".").resolve()
MAX_FILE_SIZE = 3 * 1024 * 1024  # 3 MB per file

# Directories to ignore
IGNORE_DIRS = {
    ".git",
    ".vs",
    "bin",
    "obj",
    "Debug",
    "Release",
    ".idea",
    ".vscode",
    "packages",
    "TestResults",
    "temp",
    "__pycache__",
}

# Files to ignore
IGNORE_FILES = [
    ".env",
    ".env.*",
    "*.user",
    "*.suo",
    "*.cache",
    "*.pdb",
    "*.dll",
    "*.exe",
    "*.deps.json",
    "*.runtimeconfig.json",
    "*.nuget.*",
    "*.pem",
    "*.key",
    "*.crt",
    "*.log",
    "*.db",
    "*.sqlite",
    "CODEDUMP.txt",
    "coder.py",
]

# Binary/media extensions to skip
BINARY_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico", ".webp",
    ".mp3", ".mp4", ".wav", ".avi", ".mov",
    ".zip", ".rar", ".7z", ".tar", ".gz",
    ".dll", ".exe", ".bin", ".obj", ".class",
    ".pdf", ".docx", ".xlsx", ".pptx",
    ".baml",
}

# Preferred source code extensions for WPF/Desktop
ALLOWED_EXTENSIONS = {
    ".cs", ".xaml", ".csproj", ".sln", ".slnx",
    ".json", ".config", ".xml", ".resx", ".txt", ".md"
}


def should_ignore(path: Path) -> bool:
    for part in path.parts:
        if part in IGNORE_DIRS:
            return True

    for pattern in IGNORE_FILES:
        if fnmatch.fnmatch(path.name, pattern):
            return True

    if path.suffix.lower() in BINARY_EXTENSIONS:
        return True

    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        return True

    return False


def is_text_file(file_path: Path) -> bool:
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(2048)
            if b"\x00" in chunk:
                return False
        return True
    except Exception:
        return False


def read_file_safely(file_path: Path):
    encodings = ["utf-8", "utf-8-sig", "latin-1", "utf-16"]
    for encoding in encodings:
        try:
            return file_path.read_text(encoding=encoding)
        except Exception:
            continue
    return None


def dump_codebase():
    files_dumped = 0

    with open(OUTPUT_FILE, "w", encoding="utf-8") as output:
        for file_path in sorted(ROOT_DIR.rglob("*")):
            if not file_path.is_file():
                continue

            if should_ignore(file_path):
                continue

            try:
                if file_path.stat().st_size > MAX_FILE_SIZE:
                    continue
            except Exception:
                continue

            if not is_text_file(file_path):
                continue

            content = read_file_safely(file_path)
            if content is None:
                continue

            rel_path = file_path.relative_to(ROOT_DIR)

            output.write("=" * 100 + "\n")
            output.write(f"FILE: {rel_path}\n")
            output.write("=" * 100 + "\n\n")
            output.write(content)
            output.write("\n\n")

            files_dumped += 1

    print(f"Done. Exported {files_dumped} WPF project files into {OUTPUT_FILE}")


if __name__ == "__main__":
    dump_codebase()
