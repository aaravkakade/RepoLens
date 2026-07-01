from dataclasses import dataclass

from pgvector import Vector
from pgvector.psycopg import register_vector

from app.db import get_connection
from app.embeddings import embed_text


@dataclass
class SearchResult:
    file_path: str
    name: str
    kind: str
    start_line: int
    end_line: int
    source: str
    parent_class: str | None
    docstring: str | None
    distance: float


def search_code(repo: str, query: str, limit: int = 10) -> list[SearchResult]:
    query_embedding = Vector(embed_text(query))

    with get_connection() as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT file_path, name, kind, start_line, end_line, source, parent_class, docstring,
                       embedding <=> %s AS distance
                FROM chunks
                WHERE repo = %s AND embedding IS NOT NULL
                ORDER BY embedding <=> %s
                LIMIT %s
                """,
                (query_embedding, repo, query_embedding, limit),
            )
            rows = cur.fetchall()

    return [
        SearchResult(
            file_path=row[0],
            name=row[1],
            kind=row[2],
            start_line=row[3],
            end_line=row[4],
            source=row[5],
            parent_class=row[6],
            docstring=row[7],
            distance=float(row[8]),
        )
        for row in rows
    ]
