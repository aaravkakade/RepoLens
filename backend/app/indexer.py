import sys

from pgvector.psycopg import register_vector

from app.db import get_connection
from app.embeddings import embed_texts
from app.parser import chunk_repository


def index_repository(repo_path: str, repo: str) -> dict:
    result = chunk_repository(repo_path)

    embed_inputs = [
        f"{chunk.name}\n{chunk.docstring or ''}\n{chunk.source}"
        for chunk in result.chunks
    ]
    embeddings = embed_texts(embed_inputs)

    with get_connection() as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute("DELETE FROM chunks WHERE repo = %s", (repo,))

            rows = [
                (
                    repo,
                    chunk.file_path,
                    chunk.name,
                    chunk.kind,
                    chunk.start_line,
                    chunk.end_line,
                    chunk.source,
                    chunk.parent_class,
                    chunk.docstring,
                    embedding,
                )
                for chunk, embedding in zip(result.chunks, embeddings)
            ]

            if rows:
                cur.executemany(
                    """
                    INSERT INTO chunks (
                        repo, file_path, name, kind, start_line, end_line,
                        source, parent_class, docstring, embedding
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    rows,
                )

        conn.commit()

    return {
        "repo": repo,
        "files_scanned": result.files_scanned,
        "files_indexed": result.files_indexed,
        "chunks_indexed": len(result.chunks),
        "skipped": len(result.skipped),
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: python -m app.indexer <repo_path> <repo>")
        sys.exit(1)

    summary = index_repository(sys.argv[1], sys.argv[2])
    print(summary)
