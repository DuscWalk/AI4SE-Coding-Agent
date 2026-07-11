import pytest
import tempfile
from pathlib import Path
from coding_agent.infrastructure.file_system import FileSystemManager


def test_read_file():
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "test.txt"
        f.write_text("hello world", encoding="utf-8")
        mgr = FileSystemManager(allowed_dirs=[td])
        content = mgr.read_file(str(f))
        assert content == "hello world"


def test_write_file():
    with tempfile.TemporaryDirectory() as td:
        mgr = FileSystemManager(allowed_dirs=[td])
        f = Path(td) / "out.txt"
        mgr.write_file(str(f), "written content")
        assert f.read_text(encoding="utf-8") == "written content"


def test_write_file_outside_allowed_dirs_raises():
    mgr = FileSystemManager(allowed_dirs=["/tmp/allowed"])
    with pytest.raises(PermissionError):
        mgr.write_file("/etc/passwd", "evil")


def test_write_file_rejects_sibling_with_allowed_prefix(tmp_path: Path) -> None:
    allowed = tmp_path / "project"
    sibling = tmp_path / "project-copy" / "escape.txt"
    allowed.mkdir()
    mgr = FileSystemManager(allowed_dirs=[str(allowed)])

    with pytest.raises(PermissionError):
        mgr.write_file(str(sibling), "evil")


def test_list_dir():
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "a.py").touch()
        (Path(td) / "b.py").touch()
        mgr = FileSystemManager(allowed_dirs=[td])
        files = mgr.list_dir(td)
        assert "a.py" in files
        assert "b.py" in files
