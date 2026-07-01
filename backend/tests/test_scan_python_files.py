from pathlib import Path

from app.parser import scan_python_files


def test_scan_python_files_includes_expected_and_excludes_skipped_dirs(tmp_path: Path):
    root_py = tmp_path / "main.py"
    subdir = tmp_path / "pkg"
    subdir_py = subdir / "module.py"
    pycache_dir = tmp_path / "__pycache__"
    pycache_py = pycache_dir / "cached.py"
    git_dir = tmp_path / ".git"
    git_py = git_dir / "hooks.py"
    readme = tmp_path / "README.md"

    root_py.write_text("print('root')\n")
    subdir.mkdir()
    subdir_py.write_text("print('pkg')\n")
    pycache_dir.mkdir()
    pycache_py.write_text("print('cache')\n")
    git_dir.mkdir()
    git_py.write_text("print('git')\n")
    readme.write_text("# readme\n")

    result = scan_python_files(str(tmp_path))

    assert "main.py" in result
    assert "pkg/module.py" in result
    assert "__pycache__/cached.py" not in result
    assert ".git/hooks.py" not in result
    assert "README.md" not in result
    assert len(result) == 2


def test_scan_python_files_returns_relative_paths(tmp_path: Path):
    nested = tmp_path / "src"
    nested.mkdir()
    (nested / "app.py").write_text("x = 1\n")

    result = scan_python_files(str(tmp_path))

    assert result == ["src/app.py"]
    assert not any(path.startswith(str(tmp_path)) for path in result)
