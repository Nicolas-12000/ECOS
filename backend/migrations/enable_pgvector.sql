-- 1. Enable the pgvector extension to work with embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Add the embedding column to the knowledge_base table
-- Using 384 dimensions for all-MiniLM-L6-v2
ALTER TABLE public.knowledge_base 
ADD COLUMN IF NOT EXISTS embedding vector(384);

-- 3. Create a function to search for documents using cosine similarity
-- This will be callable via RPC or raw SQL
CREATE OR REPLACE FUNCTION match_knowledge(
  query_embedding vector(384),
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  id bigint,
  title text,
  content text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    kb.id,
    kb.title,
    kb.content,
    1 - (kb.embedding <=> query_embedding) AS similarity
  FROM public.knowledge_base kb
  WHERE 1 - (kb.embedding <=> query_embedding) > match_threshold
  ORDER BY kb.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
