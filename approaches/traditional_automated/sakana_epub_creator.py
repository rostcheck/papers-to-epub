#!/usr/bin/env python3

import PyPDF2
import re
import os
from pathlib import Path

def extract_pdf_content(pdf_path):
    """Extract and structure content from Sakana.ai PDF"""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        
        # Extract text from all pages
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() + "\n"
    
    return full_text

def clean_and_structure_text(text):
    """Clean text and create proper structure"""
    
    # Fix common spacing issues
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Add space between lowercase and uppercase
    text = re.sub(r'(\w)(\d)', r'\1 \2', text)  # Add space between word and number
    text = re.sub(r'(\d)([A-Za-z])', r'\1 \2', text)  # Add space between number and letter
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    
    # Extract title (first substantial line)
    lines = text.split('\n')
    title = ""
    for line in lines:
        line = line.strip()
        if len(line) > 20 and not line.startswith('arXiv:'):
            title = line
            break
    
    # Structure the content
    sections = []
    current_section = {"title": "Introduction", "content": ""}
    
    # Split into paragraphs and identify sections
    paragraphs = text.split('\n\n')
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # Check if this is a section header
        if (len(para) < 100 and 
            (para.isupper() or 
             re.match(r'^\d+\.?\s+[A-Z]', para) or
             para in ['Abstract', 'Introduction', 'Methods', 'Results', 'Discussion', 'Conclusion', 'References'])):
            
            if current_section["content"]:
                sections.append(current_section)
            current_section = {"title": para, "content": ""}
        else:
            current_section["content"] += para + "\n\n"
    
    # Add final section
    if current_section["content"]:
        sections.append(current_section)
    
    return title, sections

def convert_tables_to_html(text):
    """Convert table-like structures to HTML tables"""
    
    # Look for table patterns (multiple columns separated by spaces/tabs)
    table_pattern = r'(\n[^\n]*\|[^\n]*\n)+'
    
    def table_replacer(match):
        table_text = match.group(0)
        rows = [row.strip() for row in table_text.split('\n') if row.strip()]
        
        html = '<table border="1" style="border-collapse: collapse; margin: 10px 0;">\n'
        
        for i, row in enumerate(rows):
            cells = [cell.strip() for cell in row.split('|') if cell.strip()]
            if cells:
                tag = 'th' if i == 0 else 'td'
                html += '  <tr>\n'
                for cell in cells:
                    html += f'    <{tag}>{cell}</{tag}>\n'
                html += '  </tr>\n'
        
        html += '</table>\n'
        return html
    
    return re.sub(table_pattern, table_replacer, text)

def create_epub_html(title, sections):
    """Create HTML content for ePub"""
    
    html = f'''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{title}</title>
    <meta charset="utf-8"/>
    <style>
        body {{ font-family: Georgia, serif; line-height: 1.6; margin: 2em; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 2em; }}
        p {{ margin: 1em 0; text-align: justify; }}
        table {{ margin: 1em 0; width: 100%; }}
        th, td {{ padding: 8px; text-align: left; }}
        th {{ background-color: #f8f9fa; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
'''
    
    for section in sections:
        html += f'    <h2>{section["title"]}</h2>\n'
        
        # Process content
        content = section["content"]
        content = convert_tables_to_html(content)
        
        # Split into paragraphs
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            para = para.strip()
            if para and not para.startswith('<table'):
                html += f'    <p>{para}</p>\n'
            elif para.startswith('<table'):
                html += f'    {para}\n'
    
    html += '''</body>
</html>'''
    
    return html

def create_epub(pdf_path, output_path):
    """Create ePub from PDF"""
    
    print(f"Processing: {pdf_path}")
    
    # Extract content
    text = extract_pdf_content(pdf_path)
    title, sections = clean_and_structure_text(text)
    
    print(f"Extracted title: {title}")
    print(f"Found {len(sections)} sections")
    
    # Create HTML
    html_content = create_epub_html(title, sections)
    
    # Save temporary HTML file
    temp_html = "/tmp/sakana_temp.html"
    with open(temp_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Convert to ePub using Calibre
    cmd = f'ebook-convert "{temp_html}" "{output_path}" --title "{title}" --authors "Sakana.ai" --language en'
    
    print(f"Converting to ePub: {output_path}")
    result = os.system(cmd)
    
    # Clean up
    if os.path.exists(temp_html):
        os.remove(temp_html)
    
    if result == 0:
        print(f"✓ Successfully created: {output_path}")
        return True
    else:
        print(f"✗ Conversion failed")
        return False

if __name__ == "__main__":
    pdf_path = "/home/aiuser/workspace/Sakana.ai/2502.14297v2.pdf"
    output_path = "/home/aiuser/workspace/epub_books/Improved_Sakana_Evaluation.epub"
    
    create_epub(pdf_path, output_path)
