#!/usr/bin/env python3
import zipfile
import tempfile
import re
from pathlib import Path
from bs4 import BeautifulSoup

class EpubFixer:
    def __init__(self, epub_path):
        self.epub_path = Path(epub_path)
    
    def fix_issues(self):
        """Apply fixes for detected quality issues"""
        print(f"🔧 Fixing issues in {self.epub_path.name}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Extract ePub
            with zipfile.ZipFile(self.epub_path, 'r') as epub:
                epub.extractall(temp_path)
            
            # Apply fixes
            self._fix_repeated_footers(temp_path)
            self._fix_toc_placement(temp_path)
            self._fix_excessive_line_breaks(temp_path)
            self._remove_blank_pages(temp_path)
            
            # Rebuild ePub
            with zipfile.ZipFile(self.epub_path, 'w', zipfile.ZIP_DEFLATED) as new_epub:
                for file_path in temp_path.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(temp_path)
                        new_epub.write(file_path, arcname)
        
        print("✓ Fixes applied")
    
    def _fix_repeated_footers(self, temp_path):
        """Remove repeated footer content"""
        html_files = list(temp_path.glob('*.html')) + list(temp_path.glob('*.xhtml'))
        
        for html_file in html_files:
            try:
                content = html_file.read_text(encoding='utf-8')
                soup = BeautifulSoup(content, 'html.parser')
                
                # Find repeated paragraphs
                paragraphs = soup.find_all('p')
                paragraph_texts = {}
                
                for p in paragraphs:
                    text = p.get_text().strip()
                    if len(text) > 10:
                        if text not in paragraph_texts:
                            paragraph_texts[text] = []
                        paragraph_texts[text].append(p)
                
                # Remove repeated footers (keep first occurrence)
                for text, elements in paragraph_texts.items():
                    if len(elements) >= 3:  # Repeated 3+ times
                        # Check if it's a footer pattern
                        footer_patterns = [
                            r'manuscript submitted',
                            r'arxiv:',
                            r'©.*\d{4}',
                            r'proceedings of',
                            r'conference on'
                        ]
                        
                        is_footer = any(re.search(pattern, text.lower()) for pattern in footer_patterns)
                        if is_footer or len(text) < 80:
                            # Remove all but first occurrence
                            for element in elements[1:]:
                                element.decompose()
                
                # Save modified content
                html_file.write_text(str(soup), encoding='utf-8')
                
            except Exception as e:
                print(f"Error fixing footers in {html_file}: {e}")
    
    def _fix_toc_placement(self, temp_path):
        """Move TOC from end to beginning"""
        html_files = list(temp_path.glob('*.html')) + list(temp_path.glob('*.xhtml'))
        
        for html_file in html_files:
            try:
                content = html_file.read_text(encoding='utf-8')
                soup = BeautifulSoup(content, 'html.parser')
                
                # Find TOC elements at the end
                body = soup.find('body')
                if not body:
                    continue
                
                # Look for TOC patterns in last 20% of content
                all_elements = body.find_all(['div', 'nav', 'section'])
                total_elements = len(all_elements)
                
                toc_elements = []
                for i, element in enumerate(all_elements):
                    if i > total_elements * 0.8:  # In last 20%
                        text = element.get_text().lower()
                        if any(pattern in text for pattern in ['table of contents', 'contents', 'outline']):
                            toc_elements.append(element)
                
                # Move TOC elements to beginning
                if toc_elements:
                    for toc_element in toc_elements:
                        toc_element.extract()
                        # Insert after first element in body
                        if body.contents:
                            body.contents[0].insert_after(toc_element)
                        else:
                            body.append(toc_element)
                
                html_file.write_text(str(soup), encoding='utf-8')
                
            except Exception as e:
                print(f"Error fixing TOC in {html_file}: {e}")
    
    def _fix_excessive_line_breaks(self, temp_path):
        """Consolidate excessive line breaks"""
        html_files = list(temp_path.glob('*.html')) + list(temp_path.glob('*.xhtml'))
        
        for html_file in html_files:
            try:
                content = html_file.read_text(encoding='utf-8')
                soup = BeautifulSoup(content, 'html.parser')
                
                # Find sequences of short paragraphs
                paragraphs = soup.find_all('p')
                
                i = 0
                while i < len(paragraphs) - 1:
                    current_p = paragraphs[i]
                    current_text = current_p.get_text().strip()
                    
                    # If current paragraph is very short
                    if len(current_text) < 20 and len(current_text) > 0:
                        # Look ahead for more short paragraphs
                        consecutive_short = [current_p]
                        j = i + 1
                        
                        while j < len(paragraphs):
                            next_p = paragraphs[j]
                            next_text = next_p.get_text().strip()
                            
                            if len(next_text) < 20 and len(next_text) > 0:
                                consecutive_short.append(next_p)
                                j += 1
                            else:
                                break
                        
                        # If we found 5+ consecutive short paragraphs, consolidate them
                        if len(consecutive_short) >= 5:
                            # Combine text into first paragraph
                            combined_text = ' '.join(p.get_text().strip() for p in consecutive_short)
                            consecutive_short[0].string = combined_text
                            
                            # Remove the rest
                            for p in consecutive_short[1:]:
                                p.decompose()
                        
                        i = j
                    else:
                        i += 1
                
                html_file.write_text(str(soup), encoding='utf-8')
                
            except Exception as e:
                print(f"Error fixing line breaks in {html_file}: {e}")
    
    def _remove_blank_pages(self, temp_path):
        """Remove blank or nearly empty HTML files"""
        html_files = list(temp_path.glob('*.html')) + list(temp_path.glob('*.xhtml'))
        
        removed_files = []
        for html_file in html_files:
            try:
                content = html_file.read_text(encoding='utf-8')
                # Remove HTML tags and check text content
                text_content = re.sub(r'<[^>]+>', '', content).strip()
                text_content = re.sub(r'\s+', ' ', text_content)
                
                # If very little actual text content, remove the file
                if len(text_content) < 50:
                    html_file.unlink()
                    removed_files.append(html_file.name)
                    
            except Exception as e:
                print(f"Error checking blank page {html_file}: {e}")
        
        if removed_files:
            print(f"Removed {len(removed_files)} blank pages")

def main():
    """Test the ePub fixer"""
    epub_dir = Path("epub_books")
    
    # Test on the problematic file
    test_file = epub_dir / "Evaluating Sakana's AI Scientist for Autonomous Research Wishful Thinking or an Emerging Reality Tow.epub"
    if test_file.exists():
        fixer = EpubFixer(test_file)
        fixer.fix_issues()
    else:
        print("Test file not found")

if __name__ == "__main__":
    main()
