-- Hemingwix PostgreSQL Migration Script
-- Migrates content from SQLite preparation to PostgreSQL for production use

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector"; -- For pgvector if using PostgreSQL with vector support

-- Create database schema for Hemingwix Novel Creation Assistant
CREATE SCHEMA IF NOT EXISTS hemingwix;
SET search_path TO hemingwix;

-- Documents table - stores main document metadata and content
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    content_type VARCHAR(100),
    source VARCHAR(100),
    status VARCHAR(50) DEFAULT 'active',
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    word_count INTEGER DEFAULT 0,
    content_hash VARCHAR(64),
    full_content TEXT,
    metadata JSONB,
    
    -- Indexes
    CONSTRAINT valid_content_type CHECK (content_type IN (
        'character-development', 'chapter', 'reference-guide', 
        'research', 'literary-analysis', 'system-design', 
        'ai-analysis', 'unknown'
    )),
    CONSTRAINT valid_status CHECK (status IN ('active', 'archived', 'draft', 'published'))
);

-- Sections table - stores document sections for structured content
CREATE TABLE IF NOT EXISTS sections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content TEXT,
    section_level INTEGER DEFAULT 1,
    word_count INTEGER DEFAULT 0,
    section_order INTEGER DEFAULT 0,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_section_level CHECK (section_level BETWEEN 1 AND 6)
);

-- Chunks table - stores content chunks for RAG and vector search
CREATE TABLE IF NOT EXISTS chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    section_id UUID REFERENCES sections(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER DEFAULT 0,
    word_count INTEGER DEFAULT 0,
    start_word INTEGER DEFAULT 0,
    end_word INTEGER DEFAULT 0,
    embedding VECTOR(1536), -- OpenAI embedding dimension, adjust as needed
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Relationships table - tracks content relationships and cross-references
CREATE TABLE IF NOT EXISTS relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_doc_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    target_doc_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL,
    confidence_score REAL DEFAULT 0.0,
    metadata JSONB,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_relationship_type CHECK (relationship_type IN (
        'references', 'builds-on', 'contradicts', 'similar-theme', 
        'character-mention', 'plot-connection', 'research-supports'
    )),
    CONSTRAINT valid_confidence CHECK (confidence_score BETWEEN 0.0 AND 1.0),
    CONSTRAINT no_self_reference CHECK (source_doc_id != target_doc_id)
);

-- Characters table - specific to novel writing for character tracking
CREATE TABLE IF NOT EXISTS characters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    archetype VARCHAR(100),
    motivation TEXT,
    backstory TEXT,
    voice_notes TEXT,
    relationships JSONB,
    mentioned_in_docs UUID[] DEFAULT '{}',
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Plot points table - for story structure tracking
CREATE TABLE IF NOT EXISTS plot_points (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    act INTEGER,
    chapter INTEGER,
    scene INTEGER,
    plot_type VARCHAR(50), -- 'setup', 'conflict', 'climax', 'resolution'
    characters_involved UUID[] DEFAULT '{}',
    document_id UUID REFERENCES documents(id),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_plot_type CHECK (plot_type IN (
        'setup', 'inciting-incident', 'plot-point-1', 'midpoint', 
        'plot-point-2', 'climax', 'resolution', 'character-arc'
    ))
);

-- Research topics table - for research management
CREATE TABLE IF NOT EXISTS research_topics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic VARCHAR(255) NOT NULL,
    summary TEXT,
    sources JSONB,
    reliability_score REAL DEFAULT 0.5,
    related_scenes TEXT[],
    tags TEXT[],
    document_id UUID REFERENCES documents(id),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_reliability CHECK (reliability_score BETWEEN 0.0 AND 1.0)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_documents_content_type ON documents(content_type);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_created_date ON documents(created_date);
CREATE INDEX IF NOT EXISTS idx_documents_word_count ON documents(word_count);

CREATE INDEX IF NOT EXISTS idx_sections_document_id ON sections(document_id);
CREATE INDEX IF NOT EXISTS idx_sections_section_order ON sections(section_order);

CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_section_id ON chunks(section_id);
CREATE INDEX IF NOT EXISTS idx_chunks_word_count ON chunks(word_count);

CREATE INDEX IF NOT EXISTS idx_relationships_source_doc ON relationships(source_doc_id);
CREATE INDEX IF NOT EXISTS idx_relationships_target_doc ON relationships(target_doc_id);
CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships(relationship_type);

CREATE INDEX IF NOT EXISTS idx_characters_name ON characters(name);
CREATE INDEX IF NOT EXISTS idx_plot_points_act_chapter ON plot_points(act, chapter);
CREATE INDEX IF NOT EXISTS idx_research_topics_topic ON research_topics(topic);

-- Create GIN indexes for JSONB and array columns
CREATE INDEX IF NOT EXISTS idx_documents_metadata ON documents USING GIN(metadata);
CREATE INDEX IF NOT EXISTS idx_relationships_metadata ON relationships USING GIN(metadata);
CREATE INDEX IF NOT EXISTS idx_characters_relationships ON characters USING GIN(relationships);
CREATE INDEX IF NOT EXISTS idx_research_topics_sources ON research_topics USING GIN(sources);

-- Create full-text search indexes
CREATE INDEX IF NOT EXISTS idx_documents_fulltext ON documents USING GIN(to_tsvector('english', title || ' ' || COALESCE(full_content, '')));
CREATE INDEX IF NOT EXISTS idx_sections_fulltext ON sections USING GIN(to_tsvector('english', title || ' ' || COALESCE(content, '')));
CREATE INDEX IF NOT EXISTS idx_chunks_fulltext ON chunks USING GIN(to_tsvector('english', chunk_text));

-- Vector similarity index (if using pgvector)
-- CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create views for common queries

-- Document summary view
CREATE OR REPLACE VIEW document_summary AS
SELECT 
    d.id,
    d.filename,
    d.title,
    d.content_type,
    d.status,
    d.word_count,
    d.created_date,
    COUNT(DISTINCT s.id) as section_count,
    COUNT(DISTINCT c.id) as chunk_count,
    ARRAY_AGG(DISTINCT s.title) FILTER (WHERE s.title IS NOT NULL) as section_titles
FROM documents d
LEFT JOIN sections s ON d.id = s.document_id
LEFT JOIN chunks c ON d.id = c.document_id
GROUP BY d.id, d.filename, d.title, d.content_type, d.status, d.word_count, d.created_date;

-- Content statistics view
CREATE OR REPLACE VIEW content_statistics AS
SELECT 
    content_type,
    COUNT(*) as document_count,
    SUM(word_count) as total_words,
    AVG(word_count)::INTEGER as avg_words_per_doc,
    MIN(word_count) as min_words,
    MAX(word_count) as max_words
FROM documents
WHERE status = 'active'
GROUP BY content_type
ORDER BY document_count DESC;

-- Character mention view
CREATE OR REPLACE VIEW character_mentions AS
SELECT 
    c.id as character_id,
    c.name,
    d.id as document_id,
    d.title as document_title,
    d.content_type
FROM characters c
CROSS JOIN documents d
WHERE d.id = ANY(c.mentioned_in_docs)
ORDER BY c.name, d.title;

-- Functions for common operations

-- Function to update document word count
CREATE OR REPLACE FUNCTION update_document_word_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE documents 
    SET word_count = LENGTH(TRIM(full_content)) - LENGTH(REPLACE(TRIM(full_content), ' ', '')) + 1,
        updated_date = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update word count
DROP TRIGGER IF EXISTS trigger_update_word_count ON documents;
CREATE TRIGGER trigger_update_word_count
    AFTER INSERT OR UPDATE OF full_content ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_document_word_count();

-- Function for full-text search
CREATE OR REPLACE FUNCTION search_content(search_term TEXT, content_type_filter TEXT DEFAULT NULL)
RETURNS TABLE(
    doc_id UUID,
    title TEXT,
    content_type TEXT,
    relevance REAL,
    snippet TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.id,
        d.title,
        d.content_type,
        ts_rank(to_tsvector('english', d.title || ' ' || COALESCE(d.full_content, '')), plainto_tsquery('english', search_term)) as relevance,
        ts_headline('english', COALESCE(d.full_content, ''), plainto_tsquery('english', search_term), 'MaxWords=50') as snippet
    FROM documents d
    WHERE to_tsvector('english', d.title || ' ' || COALESCE(d.full_content, '')) @@ plainto_tsquery('english', search_term)
    AND (content_type_filter IS NULL OR d.content_type = content_type_filter)
    AND d.status = 'active'
    ORDER BY relevance DESC;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON SCHEMA hemingwix TO hemingwix_user;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA hemingwix TO hemingwix_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA hemingwix TO hemingwix_user;

-- Sample data insertion (uncomment to populate with processed data)
-- You would run a script to import your SQLite data here

COMMENT ON SCHEMA hemingwix IS 'Schema for Hemingwix Novel Creation Assistant - stores documents, characters, plot points, and research data';
COMMENT ON TABLE documents IS 'Main documents table storing all content files with metadata';
COMMENT ON TABLE sections IS 'Document sections for structured content organization';
COMMENT ON TABLE chunks IS 'Content chunks for RAG and vector search capabilities';
COMMENT ON TABLE relationships IS 'Cross-references and relationships between documents';
COMMENT ON TABLE characters IS 'Character definitions and tracking for novel writing';
COMMENT ON TABLE plot_points IS 'Story structure and plot point tracking';
COMMENT ON TABLE research_topics IS 'Research management and source tracking';