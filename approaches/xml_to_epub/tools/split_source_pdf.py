#!/usr/bin/env python3
"""
Split source PDF into individual page images
"""

import subprocess
import sys
from pathlib import Path

def split_pdf_to_pages(pdf_path, output_dir="Other Research/pages"):
    """Split PDF into individual page images"""
    
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return None
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Get base name for files
    pdf_name = pdf_file.stem
    
    print(f"📄 Splitting PDF: {pdf_file}")
    print(f"📁 Output directory: {output_path}")
    
    # Convert PDF pages to JPEG images
    try:
        subprocess.run([
            "pdftoppm", 
            "-jpeg",
            "-r", "150",  # 150 DPI resolution
            str(pdf_file),
            str(output_path / f"{pdf_name}_page")
        ], check=True, capture_output=True)
        
        # List generated pages
        page_files = sorted(output_path.glob(f"{pdf_name}_page-*.jpg"))
        print(f"✅ Generated {len(page_files)} page images")
        
        for i, page_file in enumerate(page_files, 1):
            print(f"   Page {i}: {page_file.name}")
        
        return page_files
        
    except subprocess.CalledProcessError as e:
        print(f"❌ PDF splitting failed: {e}")
        return None

if __name__ == "__main__":
    # Split the source PDF
    pdf_path = "/home/aiuser/workspace/Other Research/1301.3781v3.pdf"
    pages = split_pdf_to_pages(pdf_path)
    
    if pages:
        print(f"\n🎉 Successfully split PDF into {len(pages)} pages!")
        print(f"📍 Pages saved in: Other Research/pages/")
    else:
        print("❌ Failed to split PDF")
        sys.exit(1)
