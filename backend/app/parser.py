import ast
import os
import sys
from dataclasses import dataclass
from pathlib import Path

SKIP_DIRS = {
    ".git",
    "venv",
    ".venv",
    "env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "build",
    "dist",
    ".eggs",
}


@dataclass
class CodeChunk:
    file_path: str
    name: str
    kind: str
    start_line: int
    end_line: int
    source: str
    parent_class: str | None = None
    docstring: str | None = None


@dataclass
class SkippedFile:
    file_path: str
    reason: str


@dataclass
class RepositoryChunks:
    chunks: list[CodeChunk]
    files_scanned: int
    files_indexed: int
    skipped: list[SkippedFile]


def scan_python_files(repo_path: str) -> list[str]:
    python_files: list[str] = []
    for dirpath, dirnames, filenames in os.walk(repo_path):
        # os.walk only prunes recursion when dirnames is mutated in place;
        # rebinding (dirnames = [...]) leaves the original list unchanged.
        kept_dirs: list[str] = []
        for d in dirnames:
            if d not in SKIP_DIRS:
                kept_dirs.append(d)
        dirnames[:] = kept_dirs
        for filename in filenames:
            if filename.endswith(".py"):
                full_path = os.path.join(dirpath, filename)
                python_files.append(os.path.relpath(full_path, repo_path))
    return python_files


def _extract_source(source: str, start_line: int, end_line: int) -> str:
    lines = source.splitlines()
    return "\n".join(lines[start_line - 1 : end_line])


def _first_method_lineno(class_node: ast.ClassDef) -> int | None:
    method_lines = [
        item.lineno
        for item in class_node.body
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    return min(method_lines) if method_lines else None


def _make_chunk(
    *,
    source: str,
    file_path: str,
    name: str,
    kind: str,
    node: ast.AST,
    start_line: int,
    end_line: int,
    parent_class: str | None = None,
) -> CodeChunk:
    return CodeChunk(
        file_path=file_path,
        name=name,
        kind=kind,
        start_line=start_line,
        end_line=end_line,
        source=_extract_source(source, start_line, end_line),
        parent_class=parent_class,
        docstring=ast.get_docstring(node),
    )


def chunk_python_source(source: str, file_path: str) -> list[CodeChunk]:
    tree = ast.parse(source)
    chunks: list[CodeChunk] = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end_line = node.end_lineno or node.lineno
            chunks.append(
                _make_chunk(
                    source=source,
                    file_path=file_path,
                    name=node.name,
                    kind="function",
                    node=node,
                    start_line=node.lineno,
                    end_line=end_line,
                )
            )
        elif isinstance(node, ast.ClassDef):
            first_method_line = _first_method_lineno(node)
            if first_method_line is not None:
                class_end_line = first_method_line - 1
            else:
                class_end_line = node.end_lineno or node.lineno

            chunks.append(
                _make_chunk(
                    source=source,
                    file_path=file_path,
                    name=node.name,
                    kind="class",
                    node=node,
                    start_line=node.lineno,
                    end_line=class_end_line,
                )
            )

            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    end_line = item.end_lineno or item.lineno
                    chunks.append(
                        _make_chunk(
                            source=source,
                            file_path=file_path,
                            name=item.name,
                            kind="method",
                            node=item,
                            start_line=item.lineno,
                            end_line=end_line,
                            parent_class=node.name,
                        )
                    )

    return chunks


def chunk_repository(repo_path: str) -> RepositoryChunks:
    relative_paths = scan_python_files(repo_path)
    files_scanned = len(relative_paths)
    chunks: list[CodeChunk] = []
    skipped: list[SkippedFile] = []

    for rel_path in relative_paths:
        abs_path = os.path.join(repo_path, rel_path)
        try:
            with open(abs_path, "r", encoding="utf-8") as handle:
                text = handle.read()
            file_chunks = chunk_python_source(text, rel_path)
        except SyntaxError:
            skipped.append(SkippedFile(rel_path, "syntax error"))
            continue
        except (OSError, UnicodeDecodeError) as exc:
            skipped.append(SkippedFile(rel_path, str(exc)))
            continue

        chunks.extend(file_chunks)

    files_indexed = files_scanned - len(skipped)
    return RepositoryChunks(
        chunks=chunks,
        files_scanned=files_scanned,
        files_indexed=files_indexed,
        skipped=skipped,
    )


def _format_chunk_summary(chunk: CodeChunk) -> str:
    parent = f" (in {chunk.parent_class})" if chunk.parent_class else ""
    return (
        f"{chunk.kind:8} {chunk.name}{parent}  "
        f"{chunk.file_path}  lines {chunk.start_line}-{chunk.end_line}"
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {Path(__file__).name} <repo_path>")
        sys.exit(1)

    result = chunk_repository(sys.argv[1])
    print(f"files_scanned: {result.files_scanned}")
    print(f"files_indexed: {result.files_indexed}")
    print(f"chunks: {len(result.chunks)}")

    if result.skipped:
        print(f"skipped ({len(result.skipped)}):")
        for item in result.skipped:
            print(f"  {item.file_path}: {item.reason}")
    else:
        print("skipped: none")

    print("sample chunks:")
    for chunk in result.chunks[:15]:
        print(f"  {_format_chunk_summary(chunk)}")
