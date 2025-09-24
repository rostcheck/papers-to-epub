#!/usr/bin/env python3
import zipfile
import os
from pathlib import Path

def create_manual_epub():
    """Assemble the manually created ePub files into a proper ePub"""
    
    epub_path = Path("epub_books/Manual_Sakana_AI_Scientist_Evaluation.epub")
    epub_path.parent.mkdir(exist_ok=True)
    
    print("🔧 Assembling manual ePub...")
    
    with zipfile.ZipFile(epub_path, 'w', zipfile.ZIP_DEFLATED) as epub:
        # Add mimetype (must be first, uncompressed)
        epub.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
        
        # Add META-INF directory
        epub.writestr('META-INF/container.xml', '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>''')
        
        # Add content files
        epub.write('manual_content.opf', 'content.opf')
        epub.write('manual_epub_content.html', 'content.html')
        epub.write('manual_toc.ncx', 'toc.ncx')
        epub.write('manual_styles.css', 'styles.css')
    
    print(f"✅ Manual ePub created: {epub_path}")
    
    # Clean up temporary files
    for temp_file in ['manual_content.opf', 'manual_epub_content.html', 'manual_toc.ncx', 'manual_styles.css']:
        if Path(temp_file).exists():
            Path(temp_file).unlink()
    
    return epub_path

if __name__ == "__main__":
    epub_path = create_manual_epub()
    
    # Test the quality
    print("\n=== Testing Manual ePub Quality ===")
    from epub_quality_analyzer import EpubQualityAnalyzer
    
    analyzer = EpubQualityAnalyzer(epub_path)
    issues = analyzer.analyze()
    
    if not issues:
        print("🎉 Perfect quality - zero issues detected!")
    else:
        print(f"Found {len(issues)} issues:")
        for issue in issues:
            print(f"  - {issue}")
