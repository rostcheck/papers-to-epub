#!/usr/bin/env python3
import PyPDF2
import re

def analyze_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        
        # Extract all text
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() + "\n"
        
        # Find title (usually first large text block)
        lines = [line.strip() for line in full_text.split('\n') if line.strip()]
        
        # Extract title (first substantial line)
        title = lines[0] if lines else "Title not found"
        
        # Find authors (look for patterns after title)
        authors = []
        author_section = ""
        for i, line in enumerate(lines[1:10]):  # Check first 10 lines after title
            if any(word in line.lower() for word in ['university', 'institute', 'lab', '@']):
                author_section += line + " "
            elif line and not any(char.isdigit() for char in line) and len(line) > 10:
                authors.append(line)
        
        # Find abstract
        abstract = ""
        abstract_start = -1
        for i, line in enumerate(lines):
            if line.lower().strip() == "abstract":
                abstract_start = i
                break
        
        if abstract_start != -1:
            for line in lines[abstract_start+1:abstract_start+20]:
                if line.lower().strip() in ['introduction', '1 introduction', 'keywords']:
                    break
                abstract += line + " "
        
        # Find section headings
        sections = []
        for line in lines:
            # Look for numbered sections or common headings
            if re.match(r'^\d+\.?\s+[A-Z]', line) or line.isupper() and len(line) > 3:
                sections.append(line)
        
        # Find tables and figures
        tables_figures = []
        for i, line in enumerate(lines):
            if re.match(r'(Table|Figure)\s+\d+', line, re.IGNORECASE):
                tables_figures.append(f"Page ~{i//50 + 1}: {line}")
        
        return {
            'title': title,
            'authors': authors[:3],  # First 3 author lines
            'author_section': author_section.strip(),
            'abstract': abstract.strip()[:500],  # First 500 chars
            'sections': sections[:15],  # First 15 sections
            'tables_figures': tables_figures[:10],  # First 10 items
            'total_pages': len(reader.pages)
        }

if __name__ == "__main__":
    result = analyze_pdf("/home/aiuser/workspace/Sakana.ai/2502.14297v2.pdf")
    
    print("=== PDF ANALYSIS REPORT ===\n")
    print(f"📄 Total Pages: {result['total_pages']}\n")
    
    print("1. TITLE:")
    print(f"   {result['title']}\n")
    
    print("2. AUTHORS & AFFILIATIONS:")
    if result['authors']:
        for author in result['authors']:
            print(f"   • {author}")
    if result['author_section']:
        print(f"   Affiliations: {result['author_section']}")
    print()
    
    print("3. SECTION STRUCTURE:")
    for section in result['sections']:
        print(f"   • {section}")
    print()
    
    print("4. TABLES & FIGURES:")
    for item in result['tables_figures']:
        print(f"   • {item}")
    print()
    
    print("5. ABSTRACT:")
    print(f"   {result['abstract']}")
    if len(result['abstract']) >= 500:
        print("   [truncated...]")
