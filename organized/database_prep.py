#!/usr/bin/env python3
"""
Database Preparation Script for Hemingwix Novel Creation Assistant
Prepares markdown files for PostgreSQL database and ChromaDB vectorization
"""

import os
import re
import json
import sqlite3
from datetime import datetime
from pathlib import Path
import hashlib
from typing import Dict, List, Optional, Tuple

class DatabasePrep:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.markdown_path = self.base_path / "organized" / "markdown_output"
        self.db_path = self.base_path / "hemingwix.db"
        
    def extract_frontmatter(self, content: str) -> Tuple[Dict, str]:
        """Extract YAML frontmatter from markdown content"""
        frontmatter = {}
        body = content
        
        if content.startswith('---\n'):
            try:
                end_marker = content.find('\n---\n', 4)
                if end_marker != -1:
                    frontmatter_text = content[4:end_marker]
                    body = content[end_marker + 5:]
                    
                    # Simple YAML parsing for our specific format
                    for line in frontmatter_text.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            frontmatter[key.strip()] = value.strip().strip('"')
            except Exception as e:
                print(f"Error parsing frontmatter: {e}")
        
        return frontmatter, body.strip()
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[Dict]:
        """Split text into overlapping chunks for vector storage"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            chunks.append({
                'text': chunk_text,
                'word_count': len(chunk_words),
                'start_word': i,
                'end_word': min(i + chunk_size, len(words))
            })
            
            if i + chunk_size >= len(words):
                break
                
        return chunks
    
    def extract_sections(self, content: str) -> List[Dict]:
        """Extract sections from markdown content based on headers"""
        sections = []
        lines = content.split('\n')
        current_section = {'title': 'Introduction', 'content': '', 'level': 1}
        
        for line in lines:
            if line.startswith('#'):
                # Save previous section if it has content
                if current_section['content'].strip():
                    sections.append(current_section.copy())
                
                # Start new section
                level = len(line) - len(line.lstrip('#'))
                title = line.lstrip('#').strip()
                current_section = {
                    'title': title,
                    'content': '',
                    'level': level
                }
            else:
                current_section['content'] += line + '\n'
        
        # Add the last section
        if current_section['content'].strip():
            sections.append(current_section)
            
        return sections
    
    def create_database_schema(self):
        """Create SQLite database schema for content management"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                content_type TEXT,
                source TEXT,
                status TEXT,
                created_date TEXT,
                processed_date TEXT,
                word_count INTEGER,
                content_hash TEXT,
                full_content TEXT,
                metadata JSON
            )
        ''')
        
        # Sections table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                title TEXT NOT NULL,
                content TEXT,
                section_level INTEGER,
                word_count INTEGER,
                section_order INTEGER,
                FOREIGN KEY (document_id) REFERENCES documents (id)
            )
        ''')
        
        # Chunks table for vector storage preparation
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                section_id INTEGER,
                chunk_text TEXT,
                chunk_index INTEGER,
                word_count INTEGER,
                start_word INTEGER,
                end_word INTEGER,
                FOREIGN KEY (document_id) REFERENCES documents (id),
                FOREIGN KEY (section_id) REFERENCES sections (id)
            )
        ''')
        
        # Relationships table for cross-references
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_doc_id INTEGER,
                target_doc_id INTEGER,
                relationship_type TEXT,
                confidence_score REAL,
                FOREIGN KEY (source_doc_id) REFERENCES documents (id),
                FOREIGN KEY (target_doc_id) REFERENCES documents (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def process_markdown_files(self):
        """Process all markdown files and prepare for database insertion"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        processed_files = []
        
        for md_file in self.markdown_path.glob("*.md"):
            print(f"Processing: {md_file.name}")
            
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract frontmatter and body
                frontmatter, body = self.extract_frontmatter(content)
                
                # Calculate content hash
                content_hash = hashlib.md5(content.encode()).hexdigest()
                
                # Calculate word count
                word_count = len(body.split())
                
                # Insert document
                cursor.execute('''
                    INSERT OR REPLACE INTO documents 
                    (filename, title, content_type, source, status, created_date, 
                     processed_date, word_count, content_hash, full_content, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    md_file.name,
                    frontmatter.get('title', md_file.stem),
                    frontmatter.get('content_type', 'unknown'),
                    frontmatter.get('source', 'unknown'),
                    frontmatter.get('status', 'processed'),
                    frontmatter.get('created_date', datetime.now().strftime('%Y-%m-%d')),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    word_count,
                    content_hash,
                    body,
                    json.dumps(frontmatter)
                ))
                
                doc_id = cursor.lastrowid
                
                # Extract and process sections
                sections = self.extract_sections(body)
                for i, section in enumerate(sections):
                    cursor.execute('''
                        INSERT INTO sections 
                        (document_id, title, content, section_level, word_count, section_order)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        doc_id,
                        section['title'],
                        section['content'],
                        section['level'],
                        len(section['content'].split()),
                        i
                    ))
                    
                    section_id = cursor.lastrowid
                    
                    # Create chunks for vector storage
                    chunks = self.chunk_text(section['content'])
                    for j, chunk in enumerate(chunks):
                        cursor.execute('''
                            INSERT INTO chunks 
                            (document_id, section_id, chunk_text, chunk_index, 
                             word_count, start_word, end_word)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            doc_id, section_id, chunk['text'], j,
                            chunk['word_count'], chunk['start_word'], chunk['end_word']
                        ))
                
                processed_files.append({
                    'filename': md_file.name,
                    'title': frontmatter.get('title', md_file.stem),
                    'content_type': frontmatter.get('content_type', 'unknown'),
                    'word_count': word_count,
                    'sections': len(sections),
                    'total_chunks': sum(len(self.chunk_text(s['content'])) for s in sections)
                })
                
            except Exception as e:
                print(f"Error processing {md_file.name}: {e}")
        
        conn.commit()
        conn.close()
        
        return processed_files
    
    def generate_chroma_export(self):
        """Generate JSON export for ChromaDB vectorization"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all chunks with metadata
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
        
        chunks_data = []
        for row in cursor.fetchall():
            chunks_data.append({
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
        
        # Export to JSON
        export_file = self.base_path / "chroma_export.json"
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, indent=2, ensure_ascii=False)
        
        conn.close()
        return export_file, len(chunks_data)
    
    def generate_summary_report(self):
        """Generate summary report of processed content"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get document statistics
        cursor.execute('''
            SELECT 
                content_type,
                COUNT(*) as document_count,
                SUM(word_count) as total_words,
                AVG(word_count) as avg_words
            FROM documents
            GROUP BY content_type
            ORDER BY document_count DESC
        ''')
        
        content_stats = cursor.fetchall()
        
        # Get chunk statistics
        cursor.execute('SELECT COUNT(*) FROM chunks')
        total_chunks = cursor.fetchone()[0]
        
        # Get total word count
        cursor.execute('SELECT SUM(word_count) FROM documents')
        total_words = cursor.fetchone()[0]
        
        report = {
            'processing_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_documents': len(content_stats),
            'total_words': total_words,
            'total_chunks': total_chunks,
            'avg_chunk_size': total_words / total_chunks if total_chunks > 0 else 0,
            'content_types': {
                stat[0]: {
                    'document_count': stat[1],
                    'total_words': stat[2],
                    'avg_words_per_doc': stat[3]
                } for stat in content_stats
            }
        }
        
        # Save report
        report_file = self.base_path / "processing_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        conn.close()
        return report
    
    def run_full_processing(self):
        """Run the complete processing pipeline"""
        print("🚀 Starting Hemingwix Database Preparation")
        print("=" * 50)
        
        # Step 1: Create database schema
        print("📊 Creating database schema...")
        self.create_database_schema()
        
        # Step 2: Process markdown files
        print("📝 Processing markdown files...")
        processed_files = self.process_markdown_files()
        
        # Step 3: Generate ChromaDB export
        print("🔍 Generating ChromaDB export...")
        export_file, chunk_count = self.generate_chroma_export()
        
        # Step 4: Generate summary report
        print("📋 Generating summary report...")
        report = self.generate_summary_report()
        
        # Print summary
        print("\n✅ Processing Complete!")
        print("=" * 50)
        print(f"📚 Documents processed: {len(processed_files)}")
        print(f"💬 Total chunks created: {chunk_count}")
        print(f"📖 Total words: {report['total_words']:,}")
        print(f"🗄️ Database: {self.db_path}")
        print(f"🔍 ChromaDB export: {export_file}")
        print(f"📊 Report: {self.base_path / 'processing_report.json'}")
        
        return {
            'database_path': self.db_path,
            'chroma_export': export_file,
            'processed_files': processed_files,
            'summary': report
        }

if __name__ == "__main__":
    # Initialize and run processing
    base_path = "/Users/benitosmac/Limerix_JBP-Local/Novelcrafter Experiment "
    
    processor = DatabasePrep(base_path)
    results = processor.run_full_processing()
    
    print(f"\n🎉 Hemingwix database preparation complete!")
    print(f"Ready for PostgreSQL migration and ChromaDB vectorization.")