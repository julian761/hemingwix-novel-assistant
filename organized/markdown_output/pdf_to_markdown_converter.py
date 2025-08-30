#!/usr/bin/env python3
"""
PDF to Markdown Converter for Hemingwix Novel Assistant
Converts PDF files to clean markdown format for PostgreSQL and ChromaDB vectorization
"""

import os
import sys
from pathlib import Path
import subprocess
import re

def install_requirements():
    """Install required packages"""
    packages = ['pymupdf', 'markdown-pdf', 'python-docx']
    for package in packages:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                         check=True, capture_output=True)
            print(f"✓ Installed {package}")
        except subprocess.CalledProcessError:
            print(f"⚠️  Failed to install {package}")

def pdf_to_markdown(pdf_path, output_path):
    """Convert PDF to markdown using PyMuPDF"""
    try:
        import fitz  # PyMuPDF
        
        doc = fitz.open(pdf_path)
        text_content = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            
            # Clean up the text
            text = re.sub(r'\n+', '\n', text)  # Remove excessive newlines
            text = re.sub(r' +', ' ', text)    # Remove excessive spaces
            
            if text.strip():
                text_content.append(f"\n## Page {page_num + 1}\n\n{text}\n")
        
        doc.close()
        
        # Write to markdown file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# {Path(pdf_path).stem}\n\n")
            f.write("".join(text_content))
        
        return True
    except Exception as e:
        print(f"Error converting {pdf_path}: {e}")
        return False

def clean_for_vectorization(text):
    """Clean text for better vectorization"""
    # Remove excessive whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    # Remove page numbers and headers/footers
    text = re.sub(r'^Page \d+\n', '', text, flags=re.MULTILINE)
    # Clean up citations and references
    text = re.sub(r'\[\d+\]', '', text)
    return text.strip()

def main():
    references_dir = Path("organized/references")
    output_dir = Path("organized/markdown_output")
    
    # Install requirements
    print("Installing requirements...")
    install_requirements()
    
    # Process PDFs
    pdf_files = list(references_dir.glob("*.pdf"))
    print(f"\nFound {len(pdf_files)} PDF files to convert")
    
    for pdf_file in pdf_files:
        output_file = output_dir / f"{pdf_file.stem}.md"
        print(f"Converting {pdf_file.name}...")
        
        if pdf_to_markdown(pdf_file, output_file):
            print(f"✓ Converted to {output_file.name}")
            
            # Create vectorization-ready version
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            clean_content = clean_for_vectorization(content)
            clean_output = output_dir / f"{pdf_file.stem}_vectorized.md"
            
            with open(clean_output, 'w', encoding='utf-8') as f:
                f.write(clean_content)
            
            print(f"✓ Created vectorization-ready version: {clean_output.name}")
        else:
            print(f"✗ Failed to convert {pdf_file.name}")

if __name__ == "__main__":
    main()