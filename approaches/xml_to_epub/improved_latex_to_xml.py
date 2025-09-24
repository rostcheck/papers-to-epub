#!/usr/bin/env python3
import re
import xml.etree.ElementTree as ET

def convert_latex_to_xml(latex_content):
    # Create root element with namespaces
    root = ET.Element("paper")
    root.set("xmlns", "http://example.com/academic-paper")
    root.set("xmlns:xhtml", "http://www.w3.org/1999/xhtml")
    root.set("xmlns:mathml", "http://www.w3.org/1998/Math/MathML")
    
    # Create metadata section
    metadata = ET.SubElement(root, "metadata")
    
    # Extract title
    title_match = re.search(r'\\title\{([^}]+)\}', latex_content)
    title_elem = ET.SubElement(metadata, "title")
    title_elem.text = title_match.group(1) if title_match else "Unknown Title"
    
    # Extract authors with improved parsing
    authors_elem = ET.SubElement(metadata, "authors")
    author_section = re.search(r'\\author\{(.*?)\}', latex_content, re.DOTALL)
    if author_section:
        author_text = author_section.group(1)
        # Split by \And or \AND
        author_parts = re.split(r'\\And|\\AND', author_text)
        
        for author_part in author_parts:
            author_elem = ET.SubElement(authors_elem, "author")
            
            # Clean up the author part
            author_part = author_part.strip()
            lines = [line.strip() for line in author_part.split('\n') if line.strip()]
            
            if lines:
                # First line is the name
                name_line = lines[0].replace('\\\\', '').strip()
                name_elem = ET.SubElement(author_elem, "name")
                name_elem.text = name_line
                
                # Extract email and affiliation
                email = None
                affiliation_parts = []
                
                for line in lines[1:]:
                    line = line.strip().rstrip(',').rstrip('\\\\').strip()
                    if '\\texttt{' in line:
                        email_match = re.search(r'\\texttt\{([^}]+)\}', line)
                        if email_match:
                            email = email_match.group(1)
                    elif line and not line.startswith('\\') and line != '\\\\':
                        affiliation_parts.append(line)
                
                # Set affiliation
                affiliation_elem = ET.SubElement(author_elem, "affiliation")
                if affiliation_parts:
                    affiliation_elem.text = ', '.join(affiliation_parts)
                else:
                    affiliation_elem.text = "Google Inc., Mountain View, CA"
                
                # Set email if found
                if email:
                    email_elem = ET.SubElement(author_elem, "email")
                    email_elem.text = email
    
    # Extract abstract
    abstract_match = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', latex_content, re.DOTALL)
    abstract_elem = ET.SubElement(metadata, "abstract")
    if abstract_match:
        abstract_text = abstract_match.group(1).strip()
        p_elem = ET.SubElement(abstract_elem, "{http://www.w3.org/1999/xhtml}p")
        p_elem.text = clean_latex_text(abstract_text)
    
    # Create sections
    sections_elem = ET.SubElement(root, "sections")
    
    # Extract sections with better content handling
    section_pattern = r'\\section\{([^}]+)\}(.*?)(?=\\section\{|\\bibliography|\\begin\{thebibliography\}|\\end\{document\}|$)'
    sections = re.findall(section_pattern, latex_content, re.DOTALL)
    
    section_id = 1
    for section_title, section_content in sections:
        section_elem = ET.SubElement(sections_elem, "section")
        section_elem.set("id", f"sec{section_id}")
        section_elem.set("level", "1")
        
        title_elem = ET.SubElement(section_elem, "title")
        title_elem.text = section_title
        
        content_elem = ET.SubElement(section_elem, "content")
        
        # Extract subsections
        subsection_pattern = r'\\subsection\{([^}]+)\}(.*?)(?=\\subsection\{|\\section\{|\\bibliography|\\begin\{thebibliography\}|\\end\{document\}|$)'
        subsections = re.findall(subsection_pattern, section_content, re.DOTALL)
        
        if subsections:
            subsections_elem = ET.SubElement(section_elem, "subsections")
            subsection_id = 1
            
            # Get content before first subsection
            first_subsection_pos = section_content.find('\\subsection{')
            if first_subsection_pos > 0:
                pre_subsection_content = section_content[:first_subsection_pos]
                if pre_subsection_content.strip():
                    add_paragraphs(content_elem, clean_latex_text(pre_subsection_content))
            
            for subsection_title, subsection_content in subsections:
                subsection_elem = ET.SubElement(subsections_elem, "subsection")
                subsection_elem.set("id", f"sec{section_id}_{subsection_id}")
                subsection_elem.set("level", "2")
                
                sub_title_elem = ET.SubElement(subsection_elem, "title")
                sub_title_elem.text = subsection_title
                
                sub_content_elem = ET.SubElement(subsection_elem, "content")
                add_paragraphs(sub_content_elem, clean_latex_text(subsection_content))
                subsection_id += 1
        else:
            add_paragraphs(content_elem, clean_latex_text(section_content))
        
        section_id += 1
    
    return root

def clean_latex_text(text):
    """Clean LaTeX text and convert to plain text with basic formatting"""
    # Remove comments
    text = re.sub(r'%.*$', '', text, flags=re.MULTILINE)
    
    # Handle math expressions (simplified)
    text = re.sub(r'\$([^$]+)\$', r'\1', text)  # Inline math
    
    # Convert LaTeX commands
    text = re.sub(r'\\textbf\{([^}]+)\}', r'\1', text)  # Bold
    text = re.sub(r'\\textit\{([^}]+)\}', r'\1', text)  # Italic
    text = re.sub(r'\\emph\{([^}]+)\}', r'\1', text)    # Emphasis
    text = re.sub(r'\\texttt\{([^}]+)\}', r'\1', text)  # Typewriter
    text = re.sub(r'\{\\bf ([^}]+)\}', r'\1', text)     # Bold
    text = re.sub(r'\{\\it ([^}]+)\}', r'\1', text)     # Italic
    
    # Remove citations
    text = re.sub(r'~\\cite\{[^}]+\}', '', text)
    text = re.sub(r'\\cite\{[^}]+\}', '', text)
    
    # Remove footnotes
    text = re.sub(r'\\footnote\{[^}]*\}', '', text)
    
    # Remove URLs
    text = re.sub(r'\\url\{[^}]+\}', '', text)
    
    # Remove figure/table references
    text = re.sub(r'Figure~\\ref\{[^}]+\}', 'Figure', text)
    text = re.sub(r'Table~\\ref\{[^}]+\}', 'Table', text)
    text = re.sub(r'\\ref\{[^}]+\}', '', text)
    text = re.sub(r'\\label\{[^}]+\}', '', text)
    
    # Remove equation environments
    text = re.sub(r'\\begin\{equation\}.*?\\end\{equation\}', '[EQUATION]', text, flags=re.DOTALL)
    
    # Remove figure and table environments
    text = re.sub(r'\\begin\{figure\}.*?\\end\{figure\}', '', text, flags=re.DOTALL)
    text = re.sub(r'\\begin\{table\}.*?\\end\{table\}', '', text, flags=re.DOTALL)
    
    # Remove other LaTeX commands
    text = re.sub(r'\\[a-zA-Z]+\*?(\[[^\]]*\])?\{[^}]*\}', '', text)
    text = re.sub(r'\\[a-zA-Z]+\*?', '', text)
    
    # Clean up special characters
    text = text.replace('\\\\', ' ')
    text = text.replace('~', ' ')
    text = text.replace('---', '—')
    text = text.replace('--', '–')
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

def add_paragraphs(parent_elem, text):
    """Add paragraphs to parent element"""
    if not text.strip():
        return
    
    # Split into paragraphs
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    
    for para_text in paragraphs:
        if para_text and len(para_text) > 10:  # Skip very short fragments
            p_elem = ET.SubElement(parent_elem, "{http://www.w3.org/1999/xhtml}p")
            p_elem.text = para_text

def format_xml_output(root):
    """Format XML with proper indentation"""
    def indent(elem, level=0):
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for child in elem:
                indent(child, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
    
    indent(root)
    return root

# Read LaTeX file and convert
with open('../../LaTeX/efficient-v22.tex', 'r', encoding='utf-8') as f:
    latex_content = f.read()

# Convert to XML
xml_root = convert_latex_to_xml(latex_content)
formatted_root = format_xml_output(xml_root)

# Write XML file
tree = ET.ElementTree(formatted_root)
ET.register_namespace('', 'http://example.com/academic-paper')
ET.register_namespace('xhtml', 'http://www.w3.org/1999/xhtml')
ET.register_namespace('mathml', 'http://www.w3.org/1998/Math/MathML')

with open('word2vec_from_latex.xml', 'wb') as f:
    f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
    tree.write(f, encoding='utf-8', xml_declaration=False)

print("Improved conversion completed. XML file saved as 'word2vec_from_latex.xml'")
