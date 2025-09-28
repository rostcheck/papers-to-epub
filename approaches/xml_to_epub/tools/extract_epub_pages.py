#!/usr/bin/env python3
"""
Extract and render ePub pages as images for review
"""

import os
import sys
import subprocess
from pathlib import Path

def extract_epub_pages(epub_path, output_dir="output/epub_pages"):
    """Extract ePub to PDF then to individual page images"""
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Get base name for files
    epub_name = Path(epub_path).stem
    pdf_path = output_path / f"{epub_name}.pdf"
    
    print(f"📚 Extracting ePub: {epub_path}")
    print(f"📁 Output directory: {output_path}")
    
    # Step 1: Convert ePub to PDF using Calibre
    print("🔄 Converting ePub to PDF...")
    try:
        subprocess.run([
            "ebook-convert", 
            epub_path, 
            str(pdf_path)
        ], check=True, capture_output=True)
        print(f"✅ PDF created: {pdf_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ ePub to PDF conversion failed: {e}")
        return None
    
    # Step 2: Convert PDF pages to images
    print("🔄 Converting PDF pages to images...")
    try:
        subprocess.run([
            "pdftoppm", 
            "-png", 
            "-r", "150",  # 150 DPI resolution
            str(pdf_path),
            str(output_path / f"{epub_name}_page")
        ], check=True, capture_output=True)
        
        # List generated pages
        page_files = sorted(output_path.glob(f"{epub_name}_page-*.png"))
        print(f"✅ Generated {len(page_files)} page images")
        
        for i, page_file in enumerate(page_files, 1):
            print(f"   Page {i}: {page_file.name}")
        
        return page_files
        
    except subprocess.CalledProcessError as e:
        print(f"❌ PDF to images conversion failed: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 extract_epub_pages.py <epub_file>")
        sys.exit(1)
    
    epub_file = sys.argv[1]
    if not os.path.exists(epub_file):
        print(f"❌ ePub file not found: {epub_file}")
        sys.exit(1)
    
    pages = extract_epub_pages(epub_file)
    if pages:
        print(f"\n🎉 Successfully extracted {len(pages)} pages!")
        print(f"📍 Pages saved in: output/epub_pages/")
    else:
        print("❌ Failed to extract pages")
        sys.exit(1)
