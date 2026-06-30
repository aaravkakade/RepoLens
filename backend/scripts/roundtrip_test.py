from pathlib import Path

from app.db import get_connection
from app.parser import chunk_repository

APP_DIR = Path(__file__).resolve().parent.parent / "app"


def main() -> None:
    result = chunk_repository(str(APP_DIR))
    if not result.chunks:
        raise SystemExit("No chunks found to insert")

    chunk = result.chunks[0]

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chunks (
                    repo, file_path, name, kind, start_line, end_line,
                    source, parent_class, docstring
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    "local/test",
                    chunk.file_path,
                    chunk.name,
                    chunk.kind,
                    chunk.start_line,
                    chunk.end_line,
                    chunk.source,
                    chunk.parent_class,
                    chunk.docstring,
                ),
            )
            conn.commit()

            cur.execute(
                """
                SELECT id, repo, file_path, name, kind, start_line, end_line, parent_class
                FROM chunks
                ORDER BY id DESC
                LIMIT 1
                """
            )
            row = cur.fetchone()
            print(row)


if __name__ == "__main__":
    main()
