#!/usr/bin/env python3

import PyPDF2
import re
import os
import zipfile
import html
from datetime import datetime

def extract_pdf_content(pdf_path):
    """Extract text content from PDF using PyPDF2"""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

def cognitive_process_content(text):
    """Process content to understand structure and extract metadata"""
    lines = text.split('\n')
    
    # Extract title (usually first significant line)
    title = ""
    for line in lines[:10]:
        line = line.strip()
        if len(line) > 10 and not line.startswith('arXiv:'):
            title = line
            break
    
    # Extract authors (typically after title)
    authors = ""
    for i, line in enumerate(lines):
        if title in line:
            for j in range(i+1, min(i+5, len(lines))):
                candidate = lines[j].strip()
                if candidate and not candidate.startswith('arXiv:') and len(candidate) < 200:
                    authors = candidate
                    break
            break
    
    # Find abstract
    abstract = ""
    abstract_start = -1
    for i, line in enumerate(lines):
        if line.strip().lower() == 'abstract':
            abstract_start = i + 1
            break
    
    if abstract_start > 0:
        for i in range(abstract_start, min(abstract_start + 20, len(lines))):
            if lines[i].strip() and not lines[i].strip().lower().startswith('1 '):
                abstract += lines[i].strip() + " "
            else:
                break
    
    # Identify sections
    sections = []
    current_section = {"title": "", "content": "", "level": 1}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check for section headers (numbered or capitalized)
        if re.match(r'^\d+\.?\s+[A-Z][A-Za-z\s]+$', line) or re.match(r'^[A-Z][A-Z\s]+$', line):
            if current_section["content"]:
                sections.append(current_section)
            current_section = {"title": line, "content": "", "level": 1}
        elif re.match(r'^\d+\.\d+\.?\s+[A-Z][A-Za-z\s]+$', line):
            if current_section["content"]:
                sections.append(current_section)
            current_section = {"title": line, "content": "", "level": 2}
        else:
            current_section["content"] += line + " "
    
    if current_section["content"]:
        sections.append(current_section)
    
    return {
        'title': title,
        'authors': authors,
        'abstract': abstract.strip(),
        'sections': sections
    }

def create_html_content(processed_data):
    """Create well-structured HTML with proper hierarchy"""
    title = html.escape(processed_data['title'])
    authors = html.escape(processed_data['authors'])
    abstract = html.escape(processed_data['abstract'])
    
    html_content = f'''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{title}</title>
    <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>
    <div class="title-page">
        <h1 class="title">{title}</h1>
        <p class="authors">{authors}</p>
    </div>
    
    <div class="toc">
        <h2>Table of Contents</h2>
        <ul>'''
    
    # Generate TOC
    for i, section in enumerate(processed_data['sections']):
        section_title = html.escape(section['title'])
        html_content += f'\n            <li><a href="#section{i}">{section_title}</a></li>'
    
    html_content += '''
        </ul>
    </div>
    
    <div class="abstract">
        <h2>Abstract</h2>
        <p>''' + abstract + '''</p>
    </div>
    
    <div class="content">'''
    
    # Add sections
    for i, section in enumerate(processed_data['sections']):
        section_title = html.escape(section['title'])
        section_content = html.escape(section['content'])
        
        # Clean up content
        section_content = re.sub(r'\s+', ' ', section_content).strip()
        
        # Split into paragraphs
        paragraphs = [p.strip() for p in section_content.split('.') if len(p.strip()) > 20]
        
        level = section['level']
        heading_tag = f'h{min(level + 2, 6)}'
        
        html_content += f'''
        <div class="section" id="section{i}">
            <{heading_tag}>{section_title}</{heading_tag}>'''
        
        for paragraph in paragraphs:
            if paragraph:
                html_content += f'\n            <p>{paragraph}.</p>'
        
        html_content += '\n        </div>'
    
    html_content += '''
    </div>
</body>
</html>'''
    
    return html_content

def create_opf_file(title, authors):
    """Create OPF metadata file"""
    clean_title = html.escape(title)
    clean_authors = html.escape(authors)
    
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid" version="2.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
        <dc:title>{clean_title}</dc:title>
        <dc:creator>{clean_authors}</dc:creator>
        <dc:language>en</dc:language>
        <dc:date>{datetime.now().strftime('%Y-%m-%d')}</dc:date>
        <meta name="cover" content="cover"/>
    </metadata>
    <manifest>
        <item id="content" href="content.html" media-type="application/xhtml+xml"/>
        <item id="toc" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
        <item id="styles" href="styles.css" media-type="text/css"/>
    </manifest>
    <spine toc="toc">
        <itemref idref="content"/>
    </spine>
</package>'''

def create_ncx_file(title, sections):
    """Create NCX navigation file"""
    clean_title = html.escape(title)
    
    ncx_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
    <head>
        <meta name="dtb:uid" content="bookid"/>
        <meta name="dtb:depth" content="2"/>
        <meta name="dtb:totalPageCount" content="0"/>
        <meta name="dtb:maxPageNumber" content="0"/>
    </head>
    <docTitle>
        <text>{clean_title}</text>
    </docTitle>
    <navMap>'''
    
    for i, section in enumerate(sections):
        section_title = html.escape(section['title'])
        ncx_content += f'''
        <navPoint id="section{i}" playOrder="{i+1}">
            <navLabel>
                <text>{section_title}</text>
            </navLabel>
            <content src="content.html#section{i}"/>
        </navPoint>'''
    
    ncx_content += '''
    </navMap>
</ncx>'''
    
    return ncx_content

def create_css_file():
    """Create academic styling CSS"""
    return '''body {
    font-family: "Times New Roman", serif;
    line-height: 1.6;
    margin: 0;
    padding: 20px;
    color: #333;
}

.title-page {
    text-align: center;
    margin-bottom: 40px;
    page-break-after: always;
}

.title {
    font-size: 24px;
    font-weight: bold;
    margin-bottom: 20px;
    color: #000;
}

.authors {
    font-size: 16px;
    font-style: italic;
    margin-bottom: 10px;
}

.toc {
    margin-bottom: 40px;
    page-break-after: always;
}

.toc h2 {
    border-bottom: 2px solid #333;
    padding-bottom: 10px;
}

.toc ul {
    list-style-type: none;
    padding-left: 0;
}

.toc li {
    margin: 8px 0;
    padding-left: 20px;
}

.abstract {
    margin-bottom: 30px;
    padding: 20px;
    background-color: #f9f9f9;
    border-left: 4px solid #333;
}

.section {
    margin-bottom: 30px;
}

h1, h2, h3, h4, h5, h6 {
    color: #000;
    margin-top: 30px;
    margin-bottom: 15px;
}

h2 {
    font-size: 20px;
    border-bottom: 1px solid #ccc;
    padding-bottom: 5px;
}

h3 {
    font-size: 18px;
}

p {
    margin-bottom: 15px;
    text-align: justify;
}

a {
    color: #0066cc;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}'''

def create_epub(pdf_path):
    """Main function to convert PDF to ePub"""
    print(f"=== Processing: {pdf_path} ===")
    
    # Extract PDF content
    print("Extracting PDF content...")
    text = extract_pdf_content(pdf_path)
    
    # Cognitive processing
    print("Processing content structure...")
    processed_data = cognitive_process_content(text)
    
    # Clean title for filename
    clean_title = re.sub(r'[^\w\s-]', '', processed_data['title'])
    clean_title = re.sub(r'[-\s]+', '-', clean_title).strip('-')
    
    print(f"Title: {processed_data['title']}")
    print(f"Authors: {processed_data['authors']}")
    print(f"Sections found: {len(processed_data['sections'])}")
    
    # Create output directory
    os.makedirs('epub_books', exist_ok=True)
    
    # Create HTML content
    print("Creating HTML structure...")
    html_content = create_html_content(processed_data)
    
    # Create ePub files
    opf_content = create_opf_file(processed_data['title'], processed_data['authors'])
    ncx_content = create_ncx_file(processed_data['title'], processed_data['sections'])
    css_content = create_css_file()
    
    # Create ePub
    epub_path = f"epub_books/{clean_title}.epub"
    print(f"Assembling ePub: {epub_path}")
    
    with zipfile.ZipFile(epub_path, 'w', zipfile.ZIP_DEFLATED) as epub:
        # Add mimetype (uncompressed)
        epub.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
        
        # Add META-INF
        epub.writestr('META-INF/container.xml', '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>''')
        
        # Add content files
        epub.writestr('content.html', html_content)
        epub.writestr('content.opf', opf_content)
        epub.writestr('toc.ncx', ncx_content)
        epub.writestr('styles.css', css_content)
    
    print(f"✓ Conversion complete: {epub_path}")
    print(f"  Title: {processed_data['title']}")
    print(f"  Sections: {len(processed_data['sections'])}")
    return epub_path

if __name__ == "__main__":
    pdf_path = "Sakana.ai/2502.14297v2.pdf"
    if os.path.exists(pdf_path):
        create_epub(pdf_path)
    else:
        print(f"Error: PDF file not found: {pdf_path}")
