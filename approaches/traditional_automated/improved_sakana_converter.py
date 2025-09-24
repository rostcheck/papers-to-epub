#!/usr/bin/env python3

import PyPDF2
import re
import os
from pathlib import Path

def extract_pdf_content(pdf_path):
    """Extract content from PDF with better text processing"""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        
        # Extract text from all pages
        pages_text = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            pages_text.append(text)
    
    return pages_text

def clean_text(text):
    """Clean and fix spacing issues in extracted text"""
    
    # Fix common spacing issues
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Add space between lowercase and uppercase
    text = re.sub(r'(\w)(\d)', r'\1 \2', text)  # Add space between word and number
    text = re.sub(r'(\d)([A-Za-z])', r'\1 \2', text)  # Add space between number and letter
    text = re.sub(r'([a-z])([A-Z][a-z])', r'\1 \2', text)  # Fix camelCase
    
    # Fix specific issues
    text = re.sub(r'ar Xiv:', 'arXiv:', text)
    text = re.sub(r'Sakana\.ai', 'Sakana.ai', text)
    text = re.sub(r'AI Scientist', 'AI Scientist', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text.strip()

def extract_title_and_abstract(pages_text):
    """Extract proper title and abstract from the paper"""
    
    # Combine first few pages to find title and abstract
    combined_text = ' '.join(pages_text[:3])
    combined_text = clean_text(combined_text)
    
    # Extract the proper title - look for the pattern after arXiv info
    title_match = re.search(r'arXiv:[^\s]+\s+(.+?)(?:Abstract|ABSTRACT)', combined_text, re.DOTALL)
    if title_match:
        title = title_match.group(1).strip()
        # Clean up the title
        title = re.sub(r'\s+', ' ', title)
        title = re.sub(r'^[^\w]*', '', title)  # Remove leading non-word chars
        title = title.split('\n')[0]  # Take first line only
    else:
        title = "Evaluating Sakana's AI Scientist for Autonomous Research"
    
    # Extract abstract
    abstract_match = re.search(r'Abstract\.?\s*(.+?)(?:\n\n|\d+\s+Introduction|1\s+Introduction)', combined_text, re.DOTALL)
    if abstract_match:
        abstract = abstract_match.group(1).strip()
        abstract = clean_text(abstract)
    else:
        abstract = "This paper evaluates Sakana.ai's AI Scientist system for autonomous research."
    
    return title, abstract

def structure_content(pages_text):
    """Structure the content into sections"""
    
    full_text = '\n'.join(pages_text)
    full_text = clean_text(full_text)
    
    # Define section patterns
    section_patterns = [
        r'\n\s*(\d+\.?\s*Introduction)\s*\n',
        r'\n\s*(\d+\.?\s*AI Scientist[:\s]*Functionality and Evaluation)\s*\n',
        r'\n\s*(\d+\.?\s*Future Work and Recommendations)\s*\n',
        r'\n\s*(\d+\.?\s*Discussion and Conclusion)\s*\n',
        r'\n\s*(\d+\.?\s*Acknowledgements)\s*\n',
        r'\n\s*(\d+\.?\s*References)\s*\n'
    ]
    
    sections = []
    current_pos = 0
    
    for i, pattern in enumerate(section_patterns):
        match = re.search(pattern, full_text[current_pos:], re.IGNORECASE)
        if match:
            # Add previous section content if exists
            if i > 0:
                prev_content = full_text[current_pos:current_pos + match.start()]
                if sections:
                    sections[-1]['content'] = prev_content.strip()
            
            # Start new section
            section_title = match.group(1).strip()
            sections.append({
                'title': section_title,
                'content': ''
            })
            current_pos += match.end()
    
    # Add final section content
    if sections:
        sections[-1]['content'] = full_text[current_pos:].strip()
    
    return sections

def convert_tables_to_html(text):
    """Convert table structures to HTML"""
    
    # Look for table-like patterns
    lines = text.split('\n')
    html_lines = []
    in_table = False
    table_rows = []
    
    for line in lines:
        # Detect table rows (lines with multiple columns separated by spaces)
        if re.search(r'\s+\w+\s+\w+\s+\w+', line) and not line.strip().startswith('Table'):
            if not in_table:
                in_table = True
                table_rows = []
            table_rows.append(line.strip())
        else:
            if in_table and table_rows:
                # Convert accumulated table rows to HTML
                html_table = '<table border="1" style="border-collapse: collapse; margin: 10px 0;">\n'
                for i, row in enumerate(table_rows):
                    cells = re.split(r'\s{2,}', row)  # Split on multiple spaces
                    if len(cells) > 1:
                        tag = 'th' if i == 0 else 'td'
                        html_table += '  <tr>\n'
                        for cell in cells:
                            if cell.strip():
                                html_table += f'    <{tag}>{cell.strip()}</{tag}>\n'
                        html_table += '  </tr>\n'
                html_table += '</table>\n'
                html_lines.append(html_table)
                table_rows = []
                in_table = False
            
            html_lines.append(line)
    
    return '\n'.join(html_lines)

def create_epub_html(title, abstract, sections):
    """Create HTML content for ePub"""
    
    html = f'''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{title}</title>
    <meta charset="utf-8"/>
    <style>
        body {{ 
            font-family: Georgia, serif; 
            line-height: 1.6; 
            margin: 2em; 
            max-width: 800px;
        }}
        h1 {{ 
            color: #2c3e50; 
            border-bottom: 2px solid #3498db; 
            padding-bottom: 10px; 
            font-size: 1.8em;
        }}
        h2 {{ 
            color: #34495e; 
            margin-top: 2em; 
            font-size: 1.4em;
        }}
        .abstract {{
            background-color: #f8f9fa;
            padding: 1em;
            border-left: 4px solid #3498db;
            margin: 1em 0;
            font-style: italic;
        }}
        p {{ 
            margin: 1em 0; 
            text-align: justify; 
        }}
        table {{ 
            margin: 1em 0; 
            width: 100%; 
            font-size: 0.9em;
        }}
        th, td {{ 
            padding: 8px; 
            text-align: left; 
            border: 1px solid #ddd;
        }}
        th {{ 
            background-color: #f8f9fa; 
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    
    <div class="abstract">
        <strong>Abstract:</strong> {abstract}
    </div>
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
                # Clean up paragraph
                para = re.sub(r'\n+', ' ', para)
                para = re.sub(r'\s+', ' ', para)
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
    pages_text = extract_pdf_content(pdf_path)
    title, abstract = extract_title_and_abstract(pages_text)
    sections = structure_content(pages_text)
    
    print(f"Extracted title: {title}")
    print(f"Found {len(sections)} sections")
    
    # Create HTML
    html_content = create_epub_html(title, abstract, sections)
    
    # Save temporary HTML file
    temp_html = "/tmp/sakana_improved.html"
    with open(temp_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Convert to ePub using Calibre
    cmd = f'ebook-convert "{temp_html}" "{output_path}" --title "{title}" --authors "Joeran Beel, Min-Yen Kan, Moritz Baumgart" --language en --chapter "//h:h2"'
    
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
