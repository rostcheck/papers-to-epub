#!/usr/bin/env python3
import PyPDF2
import re

def clean_text(text):
    # Remove extra spaces and fix common PDF extraction issues
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Add space between camelCase
    return text.strip()

def extract_pdf_content(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        
        # Extract first few pages for title/author info
        first_pages = ""
        for i in range(min(3, len(reader.pages))):
            first_pages += reader.pages[i].extract_text() + "\n"
        
        # Extract all text for sections
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() + "\n"
        
        return clean_text(first_pages), clean_text(full_text), len(reader.pages)

def parse_content(first_pages, full_text):
    lines = [line.strip() for line in first_pages.split('\n') if line.strip()]
    
    # Find actual title (skip arXiv header)
    title = ""
    for line in lines:
        if 'arXiv:' not in line and len(line) > 20 and not line.startswith('Abstract'):
            title = line
            break
    
    # Extract authors and affiliations
    authors = []
    affiliations = []
    
    # Look for author patterns
    author_text = first_pages.lower()
    if 'joeran beel' in author_text:
        authors.append("Joeran Beel")
    if 'min-yen kan' in author_text:
        authors.append("Min-Yen Kan") 
    if 'moritz baumgart' in author_text:
        authors.append("Moritz Baumgart")
    
    # Extract affiliations
    if 'university of siegen' in author_text:
        affiliations.append("University of Siegen, Germany")
    if 'national university of singapore' in author_text:
        affiliations.append("National University of Singapore")
    
    # Find abstract
    abstract = ""
    abstract_match = re.search(r'Abstract\.?\s*(.*?)(?=\n\s*\n|\n\s*1\s+Introduction|\n\s*Keywords)', first_pages, re.DOTALL | re.IGNORECASE)
    if abstract_match:
        abstract = clean_text(abstract_match.group(1))
    
    # Find sections
    sections = []
    section_pattern = r'^\s*(\d+(?:\.\d+)*)\s+([A-Z][^.]*?)(?=\s*\n|\s*\d+\.\d+|\s*$)'
    for match in re.finditer(section_pattern, full_text, re.MULTILINE):
        sections.append(f"{match.group(1)} {match.group(2)}")
    
    # Find tables and figures
    tables_figures = []
    for match in re.finditer(r'(Table|Figure)\s+(\d+)[:\.]?\s*([^\n]*)', full_text, re.IGNORECASE):
        tables_figures.append(f"{match.group(1)} {match.group(2)}: {match.group(3)[:50]}...")
    
    return {
        'title': title,
        'authors': authors,
        'affiliations': affiliations,
        'abstract': abstract,
        'sections': sections,
        'tables_figures': tables_figures
    }

if __name__ == "__main__":
    first_pages, full_text, page_count = extract_pdf_content("/home/aiuser/workspace/Sakana.ai/2502.14297v2.pdf")
    result = parse_content(first_pages, full_text)
    
    print("=== PDF ANALYSIS: Sakana.ai/2502.14297v2.pdf ===\n")
    print(f"📄 Total Pages: {page_count}\n")
    
    print("1. COMPLETE TITLE:")
    print(f"   {result['title']}\n")
    
    print("2. AUTHORS & AFFILIATIONS:")
    for author in result['authors']:
        print(f"   • {author}")
    print("   Affiliations:")
    for affiliation in result['affiliations']:
        print(f"     - {affiliation}")
    print()
    
    print("3. SECTION STRUCTURE:")
    for section in result['sections'][:10]:
        print(f"   • {section}")
    if len(result['sections']) > 10:
        print(f"   ... and {len(result['sections']) - 10} more sections")
    print()
    
    print("4. TABLES & FIGURES:")
    for item in result['tables_figures'][:8]:
        print(f"   • {item}")
    if len(result['tables_figures']) > 8:
        print(f"   ... and {len(result['tables_figures']) - 8} more items")
    print()
    
    print("5. ABSTRACT:")
    print(f"   {result['abstract'][:600]}...")
