#!/usr/bin/env python3

import PyPDF2
import re
import os
from pathlib import Path

def extract_pdf_content(pdf_path):
    """Extract content from PDF"""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() + "\n"
    
    return full_text

def clean_and_structure_text(text):
    """Clean text and create proper structure with manual title"""
    
    # Set the proper title manually
    title = "Evaluating Sakana's AI Scientist for Autonomous Research: Wishful Thinking or an Emerging Reality Towards 'Artificial Research Intelligence' (ARI)?"
    
    # Clean text
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    text = re.sub(r'(\w)(\d)', r'\1 \2', text)
    text = re.sub(r'(\d)([A-Za-z])', r'\1 \2', text)
    text = re.sub(r'\s+', ' ', text)
    
    # Extract abstract
    abstract_match = re.search(r'Abstract\.?\s*(.+?)(?:CCS Concepts|Additional Key Words|1\s+Introduction)', text, re.DOTALL)
    if abstract_match:
        abstract = abstract_match.group(1).strip()
        abstract = re.sub(r'\s+', ' ', abstract)
    else:
        abstract = "This paper provides an independent evaluation of Sakana.ai's AI Scientist system, examining its capabilities and limitations in autonomous research generation."
    
    # Create structured sections
    sections = [
        {
            "title": "1. Introduction",
            "content": extract_section(text, r'1\s+Introduction', r'2\s+AI Scientist')
        },
        {
            "title": "2. AI Scientist: Functionality and Evaluation", 
            "content": extract_section(text, r'2\s+AI Scientist', r'3\s+Future Work')
        },
        {
            "title": "3. Future Work and Recommendations",
            "content": extract_section(text, r'3\s+Future Work', r'4\s+Discussion')
        },
        {
            "title": "4. Discussion and Conclusion",
            "content": extract_section(text, r'4\s+Discussion', r'5\s+Acknowledgements')
        },
        {
            "title": "5. Acknowledgements",
            "content": extract_section(text, r'5\s+Acknowledgements', r'References')
        }
    ]
    
    return title, abstract, sections

def extract_section(text, start_pattern, end_pattern):
    """Extract content between two section markers"""
    start_match = re.search(start_pattern, text, re.IGNORECASE)
    if not start_match:
        return ""
    
    start_pos = start_match.end()
    
    end_match = re.search(end_pattern, text[start_pos:], re.IGNORECASE)
    if end_match:
        end_pos = start_pos + end_match.start()
        content = text[start_pos:end_pos]
    else:
        content = text[start_pos:start_pos + 5000]  # Take next 5000 chars if no end found
    
    # Clean the content
    content = re.sub(r'\s+', ' ', content)
    content = re.sub(r'Manuscript submitted to ACM', '', content)
    content = content.strip()
    
    return content

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
            margin-bottom: 1em;
        }}
        h2 {{ 
            color: #34495e; 
            margin-top: 2em; 
            margin-bottom: 1em;
            font-size: 1.4em;
        }}
        .abstract {{
            background-color: #f8f9fa;
            padding: 1.5em;
            border-left: 4px solid #3498db;
            margin: 2em 0;
            font-style: italic;
            border-radius: 4px;
        }}
        p {{ 
            margin: 1em 0; 
            text-align: justify; 
            text-indent: 1em;
        }}
        .section-content {{
            margin-bottom: 2em;
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
        if section["content"]:
            html += f'    <h2>{section["title"]}</h2>\n'
            html += f'    <div class="section-content">\n'
            
            # Split content into paragraphs
            paragraphs = section["content"].split('. ')
            current_para = ""
            
            for sentence in paragraphs:
                sentence = sentence.strip()
                if sentence:
                    current_para += sentence + ". "
                    
                    # Create paragraph every 3-4 sentences or when reaching reasonable length
                    if len(current_para) > 400 or sentence.endswith(('?', '!', ':')):
                        html += f'        <p>{current_para.strip()}</p>\n'
                        current_para = ""
            
            # Add any remaining content
            if current_para.strip():
                html += f'        <p>{current_para.strip()}</p>\n'
            
            html += f'    </div>\n'
    
    html += '''</body>
</html>'''
    
    return html

def create_epub(pdf_path, output_path):
    """Create ePub from PDF"""
    
    print(f"Processing: {pdf_path}")
    
    # Extract content
    text = extract_pdf_content(pdf_path)
    title, abstract, sections = clean_and_structure_text(text)
    
    print(f"Title: {title}")
    print(f"Abstract length: {len(abstract)} characters")
    print(f"Found {len([s for s in sections if s['content']])} sections with content")
    
    # Create HTML
    html_content = create_epub_html(title, abstract, sections)
    
    # Save temporary HTML file
    temp_html = "/tmp/sakana_final.html"
    with open(temp_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Convert to ePub using Calibre with proper title
    clean_title = "Evaluating Sakana's AI Scientist for Autonomous Research"
    cmd = f'ebook-convert "{temp_html}" "{output_path}" --title "{clean_title}" --authors "Joeran Beel, Min-Yen Kan, Moritz Baumgart" --language en --chapter "//h:h2" --margin-top 16 --margin-bottom 16 --margin-left 20 --margin-right 20'
    
    print(f"Converting to ePub: {output_path}")
    result = os.system(cmd)
    
    # Clean up
    if os.path.exists(temp_html):
        os.remove(temp_html)
    
    if result == 0:
        print(f"✓ Successfully created: {output_path}")
        print(f"✓ Title: {clean_title}")
        print(f"✓ Authors: Joeran Beel, Min-Yen Kan, Moritz Baumgart")
        return True
    else:
        print(f"✗ Conversion failed")
        return False

if __name__ == "__main__":
    pdf_path = "/home/aiuser/workspace/Sakana.ai/2502.14297v2.pdf"
    output_path = "/home/aiuser/workspace/epub_books/Improved_Sakana_Evaluation.epub"
    
    create_epub(pdf_path, output_path)
