#!/usr/bin/env python3
import zipfile
import tempfile
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from bs4 import BeautifulSoup

class TOCFixer:
    def __init__(self, epub_path):
        self.epub_path = Path(epub_path)
    
    def fix_toc(self):
        """Fix TOC issues in ePub file"""
        print(f"Fixing TOC for {self.epub_path.name}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Extract ePub
            with zipfile.ZipFile(self.epub_path, 'r') as epub:
                epub.extractall(temp_path)
            
            # Analyze content and create better TOC
            html_file = temp_path / "index.html"
            if html_file.exists():
                content = html_file.read_text(encoding='utf-8')
                sections = self._extract_sections(content)
                
                if sections:
                    # Update TOC file
                    toc_file = temp_path / "toc.ncx"
                    if toc_file.exists():
                        self._update_toc_file(toc_file, sections)
                    
                    # Add TOC to beginning of HTML
                    updated_content = self._add_toc_to_html(content, sections)
                    html_file.write_text(updated_content, encoding='utf-8')
            
            # Rebuild ePub
            with zipfile.ZipFile(self.epub_path, 'w', zipfile.ZIP_DEFLATED) as new_epub:
                for file_path in temp_path.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(temp_path)
                        new_epub.write(file_path, arcname)
        
        print("✓ TOC fixed")
    
    def _extract_sections(self, html_content):
        """Extract meaningful sections from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        paragraphs = soup.find_all('p')
        
        sections = []
        section_patterns = [
            r'^(Abstract|Introduction|Summary|Background|Methodology|Results|Discussion|Conclusion|References|Acknowledgments)$',
            r'^[A-Z][a-z]+ [A-Z][a-z]+.*$',  # Title case phrases
            r'^[0-9]+\.\s+[A-Z].*$',  # Numbered sections
        ]
        
        for i, p in enumerate(paragraphs):
            text = p.get_text().strip()
            
            # Skip very short or very long text
            if len(text) < 5 or len(text) > 100:
                continue
            
            # Check if it matches section patterns
            for pattern in section_patterns:
                if re.match(pattern, text):
                    # Create anchor if doesn't exist
                    anchor_id = f"section_{len(sections) + 1}"
                    sections.append({
                        'title': text,
                        'anchor': anchor_id,
                        'position': i
                    })
                    break
        
        # Limit to reasonable number of sections
        return sections[:10]
    
    def _update_toc_file(self, toc_file, sections):
        """Update the TOC NCX file with better entries"""
        try:
            # Parse existing TOC
            tree = ET.parse(toc_file)
            root = tree.getroot()
            
            # Find navMap
            ns = {'ncx': 'http://www.daisy.org/z3986/2005/ncx/'}
            nav_map = root.find('.//ncx:navMap', ns)
            
            if nav_map is not None:
                # Clear existing nav points
                nav_map.clear()
                
                # Add new nav points
                for i, section in enumerate(sections):
                    nav_point = ET.SubElement(nav_map, 'navPoint')
                    nav_point.set('id', f'section_{i+1}')
                    nav_point.set('playOrder', str(i+1))
                    
                    nav_label = ET.SubElement(nav_point, 'navLabel')
                    text_elem = ET.SubElement(nav_label, 'text')
                    text_elem.text = section['title']
                    
                    content_elem = ET.SubElement(nav_point, 'content')
                    content_elem.set('src', f"index.html#{section['anchor']}")
                
                # Write updated TOC
                tree.write(toc_file, encoding='utf-8', xml_declaration=True)
                
        except Exception as e:
            print(f"Error updating TOC file: {e}")
    
    def _add_toc_to_html(self, html_content, sections):
        """Add TOC at the beginning of HTML content"""
        if not sections:
            return html_content
        
        # Create TOC HTML
        toc_html = '\n<div class="table-of-contents">\n<h2>Table of Contents</h2>\n<ul>\n'
        for section in sections:
            toc_html += f'<li><a href="#{section["anchor"]}">{section["title"]}</a></li>\n'
        toc_html += '</ul>\n</div>\n\n'
        
        # Insert TOC after body tag
        body_start = html_content.find('<body')
        if body_start != -1:
            body_end = html_content.find('>', body_start) + 1
            html_content = html_content[:body_end] + toc_html + html_content[body_end:]
        
        # Add anchors to sections
        soup = BeautifulSoup(html_content, 'html.parser')
        paragraphs = soup.find_all('p')
        
        for section in sections:
            if section['position'] < len(paragraphs):
                p = paragraphs[section['position']]
                # Add anchor before the paragraph
                anchor = soup.new_tag('a', id=section['anchor'])
                p.insert_before(anchor)
        
        return str(soup)

def main():
    """Test TOC fixer on problematic files"""
    epub_dir = Path("epub_books")
    
    # Test on the file we know has TOC issues
    test_file = epub_dir / "The AI Scientist Generates its First Peer-Reviewed Scientific Publication.epub"
    if test_file.exists():
        fixer = TOCFixer(test_file)
        fixer.fix_toc()
    else:
        print("Test file not found")

if __name__ == "__main__":
    main()
