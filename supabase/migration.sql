-- ================================================
-- Politikerapp — Supabase migration
-- Run this in the Supabase SQL Editor
-- ================================================

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- ------------------------------------------------
-- Documents
-- ------------------------------------------------
CREATE TABLE IF NOT EXISTS pol_documents (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title       TEXT NOT NULL,
    meeting_date TEXT,
    committee   TEXT,
    document_type TEXT CHECK(document_type IN ('innkalling','saksdokument','protokoll','vedlegg')),
    source      TEXT DEFAULT 'upload',
    raw_text    TEXT,
    storage_path TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE pol_documents ENABLE ROW LEVEL SECURITY;

-- ------------------------------------------------
-- Summaries
-- ------------------------------------------------
CREATE TABLE IF NOT EXISTS pol_summaries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES pol_documents(id) ON DELETE CASCADE,
    summary_text    TEXT NOT NULL,
    length_setting  INTEGER NOT NULL DEFAULT 50,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE pol_summaries ENABLE ROW LEVEL SECURITY;

-- ------------------------------------------------
-- Enrichments
-- ------------------------------------------------
CREATE TABLE IF NOT EXISTS pol_enrichments (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id      UUID NOT NULL REFERENCES pol_documents(id) ON DELETE CASCADE,
    enrichment_type  TEXT NOT NULL CHECK(enrichment_type IN ('law','news','research','municipal_comparison','budget')),
    source_url       TEXT,
    source_title     TEXT,
    content          TEXT,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE pol_enrichments ENABLE ROW LEVEL SECURITY;

-- ------------------------------------------------
-- Generated content (taler, leserinnlegg)
-- ------------------------------------------------
CREATE TABLE IF NOT EXISTS pol_generated_content (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id       UUID NOT NULL REFERENCES pol_documents(id) ON DELETE CASCADE,
    content_type      TEXT NOT NULL CHECK(content_type IN ('tale','leserinnlegg')),
    content_text      TEXT NOT NULL,
    length_setting    INTEGER NOT NULL DEFAULT 50,
    sentiment_setting INTEGER NOT NULL DEFAULT 50,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE pol_generated_content ENABLE ROW LEVEL SECURITY;

-- ------------------------------------------------
-- Style memory
-- ------------------------------------------------
CREATE TABLE IF NOT EXISTS pol_style_memory (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_type TEXT NOT NULL CHECK(content_type IN ('tale','leserinnlegg')),
    example_text TEXT NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE pol_style_memory ENABLE ROW LEVEL SECURITY;

-- ------------------------------------------------
-- Political context / stances
-- ------------------------------------------------
CREATE TABLE IF NOT EXISTS pol_political_context (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic      TEXT NOT NULL,
    stance     TEXT NOT NULL,
    notes      TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE pol_political_context ENABLE ROW LEVEL SECURITY;

-- ------------------------------------------------
-- Document chunks + embeddings
-- ------------------------------------------------
CREATE TABLE IF NOT EXISTS pol_document_chunks (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id  UUID NOT NULL REFERENCES pol_documents(id) ON DELETE CASCADE,
    chunk_index  INTEGER NOT NULL,
    chunk_text   TEXT NOT NULL,
    embedding    vector(1024),
    created_at   TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE pol_document_chunks ENABLE ROW LEVEL SECURITY;

-- HNSW index for fast approximate nearest-neighbour search
CREATE INDEX IF NOT EXISTS pol_chunks_embedding_hnsw_idx
    ON pol_document_chunks USING hnsw (embedding vector_cosine_ops);

-- ------------------------------------------------
-- App settings (name, party etc.)
-- ------------------------------------------------
CREATE TABLE IF NOT EXISTS pol_settings (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key        TEXT UNIQUE NOT NULL,
    value      TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE pol_settings ENABLE ROW LEVEL SECURITY;

-- Seed default settings
INSERT INTO pol_settings (key, value)
VALUES
    ('user_name', ''),
    ('party', 'Høyre'),
    ('portal_url', '')
ON CONFLICT (key) DO NOTHING;

-- ------------------------------------------------
-- RLS policies (service role bypasses RLS automatically)
-- These policies allow the backend (service role) full access.
-- Adjust if you add auth later.
-- ------------------------------------------------
DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOREACH tbl IN ARRAY ARRAY['pol_documents','pol_summaries','pol_enrichments',
        'pol_generated_content','pol_style_memory','pol_political_context',
        'pol_document_chunks','pol_settings']
    LOOP
        EXECUTE format('CREATE POLICY "service_all" ON %I FOR ALL USING (true) WITH CHECK (true)', tbl);
    END LOOP;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ------------------------------------------------
-- Vector similarity search function
-- ------------------------------------------------
CREATE OR REPLACE FUNCTION pol_search_documents(
    query_embedding vector(1024),
    match_count     int     DEFAULT 10,
    exclude_doc_id  uuid    DEFAULT NULL
)
RETURNS TABLE (
    document_id  uuid,
    title        text,
    chunk_text   text,
    score        float,
    meeting_date text,
    committee    text
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.document_id,
        d.title,
        c.chunk_text,
        (1 - (c.embedding <=> query_embedding))::float AS score,
        d.meeting_date,
        d.committee
    FROM pol_document_chunks c
    JOIN pol_documents d ON d.id = c.document_id
    WHERE (exclude_doc_id IS NULL OR c.document_id != exclude_doc_id)
      AND c.embedding IS NOT NULL
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ------------------------------------------------
-- Storage bucket (run separately if needed)
-- Execute: SELECT create_storage_bucket();
-- OR create via Supabase dashboard > Storage > New bucket "pol-documents"
-- ------------------------------------------------
