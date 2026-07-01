CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repo TEXT NOT NULL,
    file_path TEXT NOT NULL,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    source TEXT NOT NULL,
    parent_class TEXT,
    docstring TEXT,
    embedding vector(384)
);