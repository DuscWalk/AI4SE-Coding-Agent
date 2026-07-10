from __future__ import annotations
from pathlib import Path


class FileSystemManager:
    def __init__(self, allowed_dirs: list[str] | None = None):
        self._allowed = [Path(d).resolve() for d in (allowed_dirs or ["."])]

    def _check_path(self, path: str) -> Path:
        resolved = Path(path).resolve()
        if not any(str(resolved).startswith(str(d)) for d in self._allowed):
            raise PermissionError(f"Access denied: {path} is outside allowed directories")
        return resolved

    def read_file(self, path: str) -> str:
        p = self._check_path(path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return p.read_text(encoding="utf-8")

    def write_file(self, path: str, content: str) -> None:
        p = self._check_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    def list_dir(self, path: str) -> list[str]:
        p = self._check_path(path)
        if not p.is_dir():
            raise NotADirectoryError(f"Not a directory: {path}")
        return [item.name for item in p.iterdir()]