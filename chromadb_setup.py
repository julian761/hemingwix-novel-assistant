#!/usr/bin/env python3
"""
ChromaDB Setup Script for Hemingwix Novel Creation Assistant
Sets up vector database for semantic search and RAG capabilities
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional
import sqlite3

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("⚠️  ChromaDB not installed. Install with: pip install chromadb")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("⚠️  sentence-transformers not installed. Install with: pip install sentence-transformers")

class ChromaDBManager:
    def __init__(self, base_path: str, collection_name: str = "hemingwix_content"):
        self.base_path = Path(base_path)
        self.collection_name = collection_name
        self.chroma_path = self.base_path / "chroma_db"
        self.sqlite_path = self.base_path / "hemingwix.db"
        self.export_path = self.base_path / "chroma_export.json"
        
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB is required. Install with: pip install chromadb")
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.chroma_path),
            settings=Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=str(self.chroma_path)
            )
        )
        
        # Initialize embedding model
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("🔧 Using SentenceTransformers for embeddings")
        else:
            self.embedding_model = None
            print("🔧 Using ChromaDB default embeddings")
    
    def create_collection(self, reset: bool = False) -> chromadb.Collection:
        """Create or get ChromaDB collection"""
        try:
            if reset:
                try:
                    self.client.delete_collection(name=self.collection_name)
                    print(f"🗑️  Deleted existing collection: {self.collection_name}")
                except Exception:
                    pass
            
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata={
                    "description": "Hemingwix Novel Creation Assistant content collection",
                    "embedding_function": "all-MiniLM-L6-v2" if self.embedding_model else "default"
                }
            )
            print(f"✅ Created collection: {self.collection_name}")
            return collection
            
        except Exception as e:
            # Collection might already exist
            collection = self.client.get_collection(name=self.collection_name)
            print(f"📚 Using existing collection: {self.collection_name}")
            return collection
    
    def load_chunks_from_export(self) -> List[Dict]:
        """Load chunks from JSON export file"""
        if not self.export_path.exists():
            raise FileNotFoundError(f"Export file not found: {self.export_path}")
        
        with open(self.export_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        print(f"📖 Loaded {len(chunks)} chunks from export file")
        return chunks
    
    def load_chunks_from_sqlite(self) -> List[Dict]:
        """Load chunks directly from SQLite database"""
        if not self.sqlite_path.exists():
            raise FileNotFoundError(f"SQLite database not found: {self.sqlite_path}")
        
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                c.id,
                c.chunk_text,
                c.chunk_index,
                c.word_count,
                d.filename,
                d.title,
                d.content_type,
                s.title as section_title,
                s.section_level
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            JOIN sections s ON c.section_id = s.id
            ORDER BY d.filename, s.section_order, c.chunk_index
        ''')
        
        chunks = []
        for row in cursor.fetchall():
            chunks.append({
                'id': f"chunk_{row[0]}",
                'text': row[1],
                'metadata': {
                    'chunk_index': row[2],
                    'word_count': row[3],
                    'document_filename': row[4],
                    'document_title': row[5],
                    'content_type': row[6],
                    'section_title': row[7],
                    'section_level': row[8]
                }
            })
        
        conn.close()
        print(f"📖 Loaded {len(chunks)} chunks from SQLite database")
        return chunks
    
    def add_chunks_to_collection(self, collection: chromadb.Collection, chunks: List[Dict], batch_size: int = 100):
        """Add chunks to ChromaDB collection in batches"""
        total_chunks = len(chunks)
        
        for i in range(0, total_chunks, batch_size):
            batch = chunks[i:i + batch_size]
            
            # Prepare batch data
            ids = [chunk['id'] for chunk in batch]
            documents = [chunk['text'] for chunk in batch]
            metadatas = [chunk['metadata'] for chunk in batch]
            
            # Generate embeddings if we have a model
            embeddings = None
            if self.embedding_model:
                embeddings = self.embedding_model.encode(documents).tolist()
            
            # Add to collection
            if embeddings:
                collection.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas,
                    embeddings=embeddings
                )
            else:
                collection.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
            
            print(f"✅ Added batch {i//batch_size + 1}/{(total_chunks + batch_size - 1)//batch_size} ({len(batch)} chunks)")
        
        print(f"🎉 Successfully added {total_chunks} chunks to ChromaDB collection")
    
    def query_collection(self, collection: chromadb.Collection, query: str, n_results: int = 5, content_type: str = None) -> Dict:
        """Query the collection with semantic search"""
        where_filter = {}
        if content_type:
            where_filter["content_type"] = content_type
        
        # Generate query embedding if we have a model
        query_embedding = None
        if self.embedding_model:
            query_embedding = self.embedding_model.encode([query]).tolist()[0]
        
        if query_embedding:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter if where_filter else None,
                include=['documents', 'metadatas', 'distances']
            )
        else:
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter if where_filter else None,
                include=['documents', 'metadatas', 'distances']
            )
        
        return results
    
    def test_queries(self, collection: chromadb.Collection):
        """Test the collection with sample queries"""
        test_queries = [
            "character development and motivation",
            "writing dialogue effectively",
            "story structure and plot points",
            "literary criticism and analysis",
            "AI agents for storytelling"
        ]
        
        print("\n🔍 Testing semantic search capabilities:")
        print("=" * 50)
        
        for query in test_queries:
            print(f"\n📝 Query: '{query}'")
            results = self.query_collection(collection, query, n_results=3)
            
            if results['documents']:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0], 
                    results['distances'][0]
                )):
                    print(f"  {i+1}. [{metadata['content_type']}] {metadata['document_title']}")
                    print(f"     Section: {metadata['section_title']} (similarity: {1-distance:.3f})")
                    print(f"     Preview: {doc[:100]}...")
            else:
                print("  No results found")
    
    def get_collection_stats(self, collection: chromadb.Collection) -> Dict:
        """Get statistics about the collection"""
        count = collection.count()
        
        # Get sample of metadata to analyze content types
        sample_results = collection.get(limit=min(count, 100))
        content_types = {}
        
        if sample_results['metadatas']:
            for metadata in sample_results['metadatas']:
                content_type = metadata.get('content_type', 'unknown')
                content_types[content_type] = content_types.get(content_type, 0) + 1
        
        return {
            'total_chunks': count,
            'content_type_distribution': content_types,
            'collection_name': self.collection_name,
            'storage_path': str(self.chroma_path)
        }
    
    def setup_complete_vectordb(self, use_sqlite: bool = True, reset: bool = False) -> Dict:
        """Complete setup of ChromaDB for Hemingwix"""
        print("🚀 Setting up ChromaDB for Hemingwix")
        print("=" * 50)
        
        # Step 1: Create collection
        collection = self.create_collection(reset=reset)
        
        # Step 2: Load chunks
        if use_sqlite and self.sqlite_path.exists():
            chunks = self.load_chunks_from_sqlite()
        else:
            chunks = self.load_chunks_from_export()
        
        # Step 3: Add chunks to collection
        if chunks:
            self.add_chunks_to_collection(collection, chunks)
        
        # Step 4: Get statistics
        stats = self.get_collection_stats(collection)
        
        # Step 5: Test queries
        self.test_queries(collection)
        
        print("\n✅ ChromaDB setup complete!")
        print("=" * 50)
        print(f"📊 Collection: {stats['collection_name']}")
        print(f"📚 Total chunks: {stats['total_chunks']}")
        print(f"💾 Storage: {stats['storage_path']}")
        print(f"📝 Content types: {list(stats['content_type_distribution'].keys())}")
        
        return stats

def main():
    """Main execution function"""
    base_path = "/Users/benitosmac/Limerix_JBP-Local/Novelcrafter Experiment "
    
    if not CHROMADB_AVAILABLE:
        print("❌ ChromaDB not available. Please install with: pip install chromadb")
        return
    
    try:
        manager = ChromaDBManager(base_path)
        stats = manager.setup_complete_vectordb(use_sqlite=True, reset=True)
        
        print(f"\n🎯 Next steps:")
        print(f"1. Use the ChromaDB collection for semantic search in your application")
        print(f"2. Query with: manager.query_collection(collection, 'your query')")
        print(f"3. Collection is persisted at: {manager.chroma_path}")
        
        return stats
        
    except Exception as e:
        print(f"❌ Error setting up ChromaDB: {e}")
        return None

if __name__ == "__main__":
    main()