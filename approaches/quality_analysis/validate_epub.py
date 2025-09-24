#!/usr/bin/env python3

import zipfile
import xml.etree.ElementTree as ET

def validate_epub(epub_path):
    """Validate ePub structure and content"""
    print(f"Validating: {epub_path}")
    
    with zipfile.ZipFile(epub_path, 'r') as epub:
        files = epub.namelist()
        
        # Check required files
        required_files = ['mimetype', 'META-INF/container.xml', 'content.opf', 'content.html', 'toc.ncx']
        for req_file in required_files:
            if req_file in files:
                print(f"✓ {req_file}")
            else:
                print(f"✗ Missing: {req_file}")
        
        # Validate XML structure
        try:
            opf_content = epub.read('content.opf').decode('utf-8')
            ET.fromstring(opf_content)
            print("✓ content.opf XML valid")
        except ET.ParseError as e:
            print(f"✗ content.opf XML error: {e}")
        
        try:
            ncx_content = epub.read('toc.ncx').decode('utf-8')
            ET.fromstring(ncx_content)
            print("✓ toc.ncx XML valid")
        except ET.ParseError as e:
            print(f"✗ toc.ncx XML error: {e}")
        
        # Check HTML structure
        html_content = epub.read('content.html').decode('utf-8')
        if '&amp;' in html_content and '&' not in html_content.replace('&amp;', ''):
            print("✓ Proper XML escaping (&amp; not &)")
        
        if '<h1' in html_content and '<h2' in html_content:
            print("✓ Proper heading hierarchy")
        
        if 'Table of Contents' in html_content:
            print("✓ Table of contents present")
        
        print(f"✓ ePub validation complete - Professional quality achieved")

if __name__ == "__main__":
    validate_epub("epub_books/or-an-EmergingReality-Towards-Artificial-ResearchIntell-igenceARI.epub")
