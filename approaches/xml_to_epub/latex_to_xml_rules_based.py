#!/usr/bin/env python3

import re
import xml.etree.ElementTree as ET
from xml.dom import minidom

def extract_title_authors(content):
    """Extract title and authors from LaTeX content"""
    title_match = re.search(r'\\title\{([^}]+)\}', content)
    title = title_match.group(1) if title_match else "Unknown Title"
    
    # Extract author block
    author_match = re.search(r'\\author\{(.*?)\}', content, re.DOTALL)
    authors = []
    
    if author_match:
        author_content = author_match.group(1)
        # Split by \And or \AND
        author_parts = re.split(r'\\And|\\AND', author_content)
        
        for part in author_parts:
            # Extract name and affiliation
            lines = [line.strip() for line in part.strip().split('\\\\') if line.strip()]
            if lines:
                name = lines[0].strip()
                affiliation = ""
                email = ""
                
                for line in lines[1:]:
                    if '\\texttt{' in line:
                        email_match = re.search(r'\\texttt\{([^}]+)\}', line)
                        if email_match:
                            email = email_match.group(1)
                    else:
                        if affiliation:
                            affiliation += ", "
                        affiliation += line.strip()
                
                authors.append({
                    'name': name,
                    'affiliation': affiliation,
                    'email': email
                })
    
    return title, authors

def extract_sections(content):
    """Extract sections and subsections with hierarchy"""
    sections = []
    
    # Find all sections and subsections
    section_pattern = r'\\(sub)?section\{([^}]+)\}'
    matches = list(re.finditer(section_pattern, content))
    
    for i, match in enumerate(matches):
        is_subsection = match.group(1) == 'sub'
        title = match.group(2)
        start_pos = match.end()
        
        # Find content until next section
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(content)
        
        section_content = content[start_pos:end_pos].strip()
        
        sections.append({
            'type': 'subsection' if is_subsection else 'section',
            'title': title,
            'content': section_content
        })
    
    return sections

def extract_bibliography(content):
    """Extract bibliography entries from \bibitem commands"""
    biblio = []
    
    # Find bibliography section
    bib_start = content.find('\\begin{thebibliography}')
    if bib_start == -1:
        return biblio
    
    bib_end = content.find('\\end{thebibliography}', bib_start)
    if bib_end == -1:
        bib_end = len(content)
    
    bib_content = content[bib_start:bib_end]
    
    # Extract bibitem entries
    bibitem_pattern = r'\\bibitem\{([^}]+)\}\s*([^\\]+?)(?=\\bibitem|\s*$)'
    matches = re.findall(bibitem_pattern, bib_content, re.DOTALL)
    
    for key, text in matches:
        biblio.append({
            'key': key,
            'text': text.strip()
        })
    
    return biblio

def extract_citations(content):
    """Extract all citations from \cite commands"""
    citations = []
    cite_pattern = r'\\cite\{([^}]+)\}'
    matches = re.findall(cite_pattern, content)
    
    for match in matches:
        # Handle multiple citations separated by commas
        keys = [key.strip() for key in match.split(',')]
        citations.extend(keys)
    
    return list(set(citations))  # Remove duplicates

def extract_tables(content):
    """Extract tables from \begin{table} environments"""
    tables = []
    
    table_pattern = r'\\begin\{table\}(.*?)\\end\{table\}'
    matches = re.findall(table_pattern, content, re.DOTALL)
    
    for i, match in enumerate(matches):
        # Extract caption
        caption_match = re.search(r'\\caption\{([^}]+)\}', match)
        caption = caption_match.group(1) if caption_match else f"Table {i+1}"
        
        # Extract label
        label_match = re.search(r'\\label\{([^}]+)\}', match)
        label = label_match.group(1) if label_match else f"tab{i+1}"
        
        tables.append({
            'id': label,
            'caption': caption,
            'content': match.strip()
        })
    
    return tables

def extract_figures(content):
    """Extract figures from \begin{figure} environments"""
    figures = []
    
    figure_pattern = r'\\begin\{figure\}(.*?)\\end\{figure\}'
    matches = re.findall(figure_pattern, content, re.DOTALL)
    
    for i, match in enumerate(matches):
        # Extract caption
        caption_match = re.search(r'\\caption\{([^}]+)\}', match)
        caption = caption_match.group(1) if caption_match else f"Figure {i+1}"
        
        # Extract label
        label_match = re.search(r'\\label\{([^}]+)\}', match)
        label = label_match.group(1) if label_match else f"fig{i+1}"
        
        figures.append({
            'id': label,
            'caption': caption,
            'content': match.strip()
        })
    
    return figures

def extract_equations(content):
    """Extract mathematical equations (both inline and display)"""
    equations = []
    
    # Display equations with \begin{equation}
    eq_pattern = r'\\begin\{equation\}(.*?)\\end\{equation\}'
    matches = re.findall(eq_pattern, content, re.DOTALL)
    
    for i, match in enumerate(matches):
        # Extract label if present
        label_match = re.search(r'\\label\{([^}]+)\}', match)
        label = label_match.group(1) if label_match else f"eq{i+1}"
        
        equations.append({
            'type': 'display',
            'id': label,
            'content': match.strip()
        })
    
    # Inline math with $ ... $
    inline_pattern = r'\$([^$]+)\$'
    inline_matches = re.findall(inline_pattern, content)
    
    for i, match in enumerate(inline_matches):
        equations.append({
            'type': 'inline',
            'id': f"inline{i+1}",
            'content': match.strip()
        })
    
    return equations

def create_xml_document(title, authors, sections, bibliography, citations, tables, figures, equations):
    """Create XML document with all extracted components"""
    
    # Create root element with correct schema
    root = ET.Element('paper')
    root.set('xmlns', 'http://example.com/academic-paper')
    root.set('xmlns:xhtml', 'http://www.w3.org/1999/xhtml')
    root.set('xmlns:mathml', 'http://www.w3.org/1998/Math/MathML')
    
    # Metadata
    metadata = ET.SubElement(root, 'metadata')
    title_elem = ET.SubElement(metadata, 'title')
    title_elem.text = title
    
    authors_elem = ET.SubElement(metadata, 'authors')
    for author in authors:
        author_elem = ET.SubElement(authors_elem, 'author')
        name_elem = ET.SubElement(author_elem, 'name')
        name_elem.text = author['name']
        if author['affiliation']:
            affil_elem = ET.SubElement(author_elem, 'affiliation')
            affil_elem.text = author['affiliation']
        if author['email']:
            email_elem = ET.SubElement(author_elem, 'email')
            email_elem.text = author['email']
    
    # Content sections
    content_elem = ET.SubElement(root, 'content')
    
    for section in sections:
        if section['type'] == 'section':
            sect_elem = ET.SubElement(content_elem, 'section')
        else:
            sect_elem = ET.SubElement(content_elem, 'subsection')
        
        sect_title = ET.SubElement(sect_elem, 'title')
        sect_title.text = section['title']
        
        sect_content = ET.SubElement(sect_elem, 'text')
        sect_content.text = section['content']
    
    # Tables
    if tables:
        tables_elem = ET.SubElement(root, 'tables')
        for table in tables:
            table_elem = ET.SubElement(tables_elem, 'table')
            table_elem.set('id', table['id'])
            
            caption_elem = ET.SubElement(table_elem, 'caption')
            caption_elem.text = table['caption']
            
            content_elem = ET.SubElement(table_elem, 'content')
            content_elem.text = table['content']
    
    # Figures
    if figures:
        figures_elem = ET.SubElement(root, 'figures')
        for figure in figures:
            fig_elem = ET.SubElement(figures_elem, 'figure')
            fig_elem.set('id', figure['id'])
            
            caption_elem = ET.SubElement(fig_elem, 'caption')
            caption_elem.text = figure['caption']
            
            content_elem = ET.SubElement(fig_elem, 'content')
            content_elem.text = figure['content']
    
    # Equations
    if equations:
        equations_elem = ET.SubElement(root, 'equations')
        for equation in equations:
            eq_elem = ET.SubElement(equations_elem, 'equation')
            eq_elem.set('type', equation['type'])
            eq_elem.set('id', equation['id'])
            eq_elem.text = equation['content']
    
    # Citations
    if citations:
        citations_elem = ET.SubElement(root, 'citations')
        for citation in citations:
            cite_elem = ET.SubElement(citations_elem, 'citation')
            cite_elem.text = citation
    
    # Bibliography
    if bibliography:
        biblio_elem = ET.SubElement(root, 'bibliography')
        for bib_entry in bibliography:
            entry_elem = ET.SubElement(biblio_elem, 'entry')
            entry_elem.set('key', bib_entry['key'])
            entry_elem.text = bib_entry['text']
    
    return root

def convert_latex_to_xml(latex_file, output_file):
    """Main conversion function"""
    
    # Read LaTeX file
    with open(latex_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("Extracting components...")
    
    # Extract all components
    title, authors = extract_title_authors(content)
    sections = extract_sections(content)
    bibliography = extract_bibliography(content)
    citations = extract_citations(content)
    tables = extract_tables(content)
    figures = extract_figures(content)
    equations = extract_equations(content)
    
    print(f"Found: {len(sections)} sections, {len(bibliography)} bibliography entries")
    print(f"Found: {len(citations)} unique citations, {len(tables)} tables")
    print(f"Found: {len(figures)} figures, {len(equations)} equations")
    
    # Create XML document
    root = create_xml_document(title, authors, sections, bibliography, citations, tables, figures, equations)
    
    # Pretty print XML
    rough_string = ET.tostring(root, 'unicode')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    
    print(f"XML conversion complete: {output_file}")
    
    # Validation summary
    print("\nValidation Summary:")
    print(f"✓ Title: {title}")
    print(f"✓ Authors: {len(authors)}")
    print(f"✓ Sections: {len(sections)}")
    print(f"✓ Bibliography entries: {len(bibliography)}")
    print(f"✓ Citations: {len(citations)}")
    print(f"✓ Tables: {len(tables)}")
    print(f"✓ Figures: {len(figures)}")
    print(f"✓ Equations: {len(equations)}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 latex_to_xml_rules_based.py <latex_file> [output_file]")
        sys.exit(1)
    
    latex_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        # Default output to output directory
        from pathlib import Path
        latex_path = Path(latex_file)
        output_file = f"output/{latex_path.stem}_rules_based.xml"
    
    convert_latex_to_xml(latex_file, output_file)
