import sqlite3
import os
from pathlib import Path

DB_PATH = Path.home() / "politikerapp" / "data" / "documents.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        conn.enable_load_extension(True)
        import sqlite_vec
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
    except Exception:
        pass
    return conn


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            meeting_date TEXT,
            committee TEXT,
            document_type TEXT CHECK(document_type IN ('innkalling','saksdokument','protokoll','vedlegg')),
            source TEXT CHECK(source IN ('upload','scrape')),
            raw_text TEXT,
            file_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            summary_text TEXT NOT NULL,
            length_setting INTEGER NOT NULL DEFAULT 50,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS enrichments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            enrichment_type TEXT NOT NULL CHECK(enrichment_type IN ('law','news','research','municipal_comparison','budget')),
            source_url TEXT,
            source_title TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS generated_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            content_type TEXT NOT NULL CHECK(content_type IN ('tale','leserinnlegg')),
            content_text TEXT NOT NULL,
            length_setting INTEGER NOT NULL DEFAULT 50,
            sentiment_setting INTEGER NOT NULL DEFAULT 50,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS style_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_type TEXT NOT NULL CHECK(content_type IN ('tale','leserinnlegg')),
            example_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS political_context (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            stance TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS document_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            chunk_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_documents_meeting_date ON documents(meeting_date);
        CREATE INDEX IF NOT EXISTS idx_documents_committee ON documents(committee);
        CREATE INDEX IF NOT EXISTS idx_summaries_document_id ON summaries(document_id);
        CREATE INDEX IF NOT EXISTS idx_enrichments_document_id ON enrichments(document_id);
        CREATE INDEX IF NOT EXISTS idx_generated_content_document_id ON generated_content(document_id);
        CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON document_chunks(document_id);
    """)

    # sqlite-vec virtual table for embeddings (1024-dim for multilingual-e5-large)
    try:
        cur.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS document_embeddings USING vec0(
                chunk_id INTEGER PRIMARY KEY,
                embedding FLOAT[1024]
            )
        """)
    except Exception:
        # sqlite-vec may not be available at DB init time on all systems
        pass

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
