from pgvector.psycopg import register_vector

from app.db import get_connection


def main() -> None:
    with get_connection() as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            dummy = [0.0] * 384
            cur.execute(
                "INSERT INTO chunks (repo, file_path, name, kind, start_line, end_line, source, embedding) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                ("local/vectortest", "x.py", "x", "function", 1, 1, "pass", dummy),
            )
            conn.commit()

            cur.execute(
                "SELECT id, embedding FROM chunks WHERE repo = 'local/vectortest'"
            )
            row = cur.fetchone()
            print(row[0], type(row[1]), len(row[1]))


if __name__ == "__main__":
    main()