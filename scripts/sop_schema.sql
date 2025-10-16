CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS sop_chunks (
  id           text PRIMARY KEY,
  section      text,
  title        text,
  text         text,
  tags         text[],
  updated_at   timestamptz,
  embedding    vector(384) -- adjust to your model dim
);

CREATE INDEX IF NOT EXISTS idx_sop_chunks_embedding ON sop_chunks USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_sop_chunks_tags ON sop_chunks USING GIN (tags);
