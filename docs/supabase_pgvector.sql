-- SQL DDL for storing embeddings in Supabase (requires pgvector extension)

-- Enable extension (requires DB superuser or managed Supabase with pgvector enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Table to store document embeddings and small excerpts
CREATE TABLE IF NOT EXISTS public.document_embeddings (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_text text,
    excerpt text,
    embedding vector(384), -- model-dependent dimension (e.g., 384 for all-MiniLM-L6-v2)
    created_at timestamptz DEFAULT now()
);

-- Index for fast similarity search (cosine via ivfflat or approximate methods)
-- Example: create an ivfflat index (requires adjusting lists and params)
-- SELECT vector_fill_parameters('document_embeddings', 'embedding');
CREATE INDEX IF NOT EXISTS idx_document_embeddings_embedding ON public.document_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
