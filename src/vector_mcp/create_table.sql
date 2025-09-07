-- SQL script to create the documents table in Supabase
-- Run this in your Supabase SQL Editor if automatic table creation fails

-- Enable the vector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the documents table
CREATE TABLE IF NOT EXISTS public.documents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    filename VARCHAR NOT NULL,
    content TEXT NOT NULL,
    file_path VARCHAR NOT NULL,
    file_hash VARCHAR NOT NULL,
    chunk_index INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    embedding VECTOR(1536)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS documents_embedding_idx ON public.documents 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS documents_filename_idx ON public.documents (filename);

CREATE INDEX IF NOT EXISTS documents_file_hash_idx ON public.documents (file_hash);

-- Enable Row Level Security (RLS) - optional but recommended
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;

-- Create a policy to allow all operations (adjust as needed for your security requirements)
CREATE POLICY "Allow all operations on documents" ON public.documents
FOR ALL USING (true);

-- Grant permissions to the authenticated role
GRANT ALL ON public.documents TO authenticated;
GRANT ALL ON public.documents TO anon;

-- Verify the table was created
SELECT 
    table_name, 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'documents' 
ORDER BY ordinal_position;