#!/usr/bin/env python3
import os
import zipfile
import re
from pathlib import Path
from collections import Counter
import xml.etree.ElementTree as ET

class EpubQualityAnalyzer:
    def __init__(self, epub_path):
        self.epub_path = Path(epub_path)
        self.issues = []
        
    def analyze(self):
        """Analyze ePub file for quality issues"""
        print(f"\n=== Analyzing: {self.epub_path.name} ===")
        
        with zipfile.ZipFile(self.epub_path, 'r') as epub:
            # Extract content
            content_html = self._get_main_content(epub)
            toc_content = self._get_toc_content(epub)
            
            # Run quality checks
            self._check_toc_issues(toc_content, content_html)
            self._check_repeated_footers(content_html)
            self._check_table_formatting(content_html)
            self._check_general_formatting(content_html)
            self._check_blank_pages(epub)
            self._check_toc_placement(content_html)
            self._check_excessive_line_breaks(content_html)
            
        self._print_summary()
        return self.issues
    
    def _get_main_content(self, epub):
        """Extract main HTML content from all HTML files"""
        content = ""
        try:
            # Try common main file names first
            for filename in ['index.html', 'content.html', 'text.html']:
                try:
                    content = epub.read(filename).decode('utf-8')
                    return content
                except KeyError:
                    continue
            
            # If no main file found, combine all HTML files
            html_files = [f for f in epub.namelist() if f.endswith('.html') or f.endswith('.xhtml')]
            html_files = [f for f in html_files if not f.startswith('META-INF/')]  # Skip metadata
            
            for html_file in sorted(html_files):  # Sort to get consistent order
                try:
                    file_content = epub.read(html_file).decode('utf-8')
                    content += file_content + "\n"
                except:
                    continue
                    
            return content
        except Exception as e:
            return ""
    
    def _get_toc_content(self, epub):
        """Extract table of contents"""
        try:
            return epub.read('toc.ncx').decode('utf-8')
        except:
            return ""
    
    def _check_toc_issues(self, toc_content, html_content):
        """Check for TOC placement and quality issues"""
        if not toc_content:
            self.issues.append("CRITICAL: No table of contents found")
            return
            
        # Parse TOC entries
        try:
            root = ET.fromstring(toc_content)
            nav_points = root.findall('.//{http://www.daisy.org/z3986/2005/ncx/}navLabel/{http://www.daisy.org/z3986/2005/ncx/}text')
            toc_entries = [point.text for point in nav_points if point.text]
            
            # Check for meaningless entries
            meaningless_patterns = [r'^\d+$', r'^\.\d+$', r'^↩$', r'^analysis section\)$']
            meaningless_count = 0
            for entry in toc_entries:
                if any(re.match(pattern, entry.strip()) for pattern in meaningless_patterns):
                    meaningless_count += 1
            
            if meaningless_count > len(toc_entries) * 0.5:
                self.issues.append(f"MAJOR: TOC has {meaningless_count}/{len(toc_entries)} meaningless entries")
            
            # Check TOC placement (should be near beginning)
            if 'toc' in html_content.lower():
                toc_position = html_content.lower().find('toc')
                content_length = len(html_content)
                if toc_position > content_length * 0.8:
                    self.issues.append("MAJOR: TOC appears at end of document instead of beginning")
                    
        except Exception as e:
            self.issues.append(f"ERROR: Could not parse TOC: {e}")
    
    def _check_repeated_footers(self, content):
        """Check for repeated footer/header content with enhanced detection"""
        # Extract all paragraph text
        paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', content, re.DOTALL | re.IGNORECASE)
        
        # Clean paragraphs and count occurrences
        cleaned_paragraphs = []
        for p in paragraphs:
            # Remove HTML tags and normalize whitespace
            clean_text = re.sub(r'<[^>]+>', '', p).strip()
            clean_text = re.sub(r'\s+', ' ', clean_text)
            if len(clean_text) > 5:  # Only consider substantial content
                cleaned_paragraphs.append(clean_text)
        
        # Count occurrences of each paragraph
        paragraph_counts = Counter(cleaned_paragraphs)
        
        # Check for repeated content (appears 3+ times)
        for text, count in paragraph_counts.items():
            if count >= 3:
                # Common footer patterns
                footer_patterns = [
                    r'manuscript submitted to',
                    r'arxiv:',
                    r'page \d+ of \d+',
                    r'©.*\d{4}',
                    r'proceedings of',
                    r'conference on',
                    r'https?://[^\s]+',
                    r'acm.*\d{4}',
                    r'ieee.*\d{4}'
                ]
                
                is_footer = any(re.search(pattern, text.lower()) for pattern in footer_patterns)
                if is_footer or len(text) < 80:  # Short repeated text likely footer
                    self.issues.append(f"MAJOR: Repeated footer content '{text[:60]}...' appears {count} times")
                    break
    
    def _check_table_formatting(self, content):
        """Check for table formatting issues"""
        # Count images vs actual tables
        img_count = len(re.findall(r'<img[^>]*>', content))
        table_count = len(re.findall(r'<table[^>]*>', content))
        
        if img_count > 5 and table_count == 0:
            self.issues.append("MINOR: Document has many images but no HTML tables - tables may be converted to images")
        
        # Check for table-like content in paragraphs
        lines = content.split('\n')
        table_like_lines = 0
        for line in lines:
            if re.search(r'<p[^>]*>.*\|.*\|.*</p>', line):  # Pipe-separated content
                table_like_lines += 1
        
        if table_like_lines > 3:
            self.issues.append("MINOR: Found table-like content in paragraphs instead of proper tables")
    
    def _check_general_formatting(self, content):
        """Check for general formatting issues"""
        # Excessive whitespace
        excessive_breaks = len(re.findall(r'(<br[^>]*>\s*){3,}', content))
        if excessive_breaks > 5:
            self.issues.append(f"MINOR: Found {excessive_breaks} instances of excessive line breaks")
        
        # Very short paragraphs (might indicate broken text flow)
        paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', content, re.DOTALL)
        short_paragraphs = [p for p in paragraphs if len(p.strip()) < 10 and p.strip()]
        if len(short_paragraphs) > len(paragraphs) * 0.3:
            self.issues.append(f"MINOR: {len(short_paragraphs)} very short paragraphs may indicate text flow issues")
    
    def _print_summary(self):
        """Print analysis summary"""
        if not self.issues:
            print("✓ No quality issues detected")
            return
        
        critical = [i for i in self.issues if i.startswith('CRITICAL')]
        major = [i for i in self.issues if i.startswith('MAJOR')]
        minor = [i for i in self.issues if i.startswith('MINOR')]
        errors = [i for i in self.issues if i.startswith('ERROR')]
        
        print(f"Found {len(self.issues)} issues:")
        for issue_type, issues in [('CRITICAL', critical), ('MAJOR', major), ('MINOR', minor), ('ERROR', errors)]:
            if issues:
                print(f"\n{issue_type} ({len(issues)}):")
                for issue in issues:
                    print(f"  - {issue}")

def main():
    epub_dir = Path("epub_books")
    if not epub_dir.exists():
        print("No epub_books directory found")
        return
    
    epub_files = list(epub_dir.glob("*.epub"))
    if not epub_files:
        print("No ePub files found")
        return
    
    print(f"Analyzing {len(epub_files)} ePub files...")
    
    all_issues = {}
    for epub_file in epub_files:
        analyzer = EpubQualityAnalyzer(epub_file)
        issues = analyzer.analyze()
        all_issues[epub_file.name] = issues
    
    # Summary
    print(f"\n=== OVERALL SUMMARY ===")
    total_issues = sum(len(issues) for issues in all_issues.values())
    print(f"Total issues found: {total_issues}")
    
    files_with_issues = [name for name, issues in all_issues.items() if issues]
    if files_with_issues:
        print(f"Files with issues: {len(files_with_issues)}/{len(epub_files)}")

# Enhanced heuristics methods - add to EpubQualityAnalyzer class
def _check_blank_pages(self, epub):
    """Check for blank or nearly empty pages"""
    try:
        # Check all HTML files in the ePub
        html_files = [f for f in epub.namelist() if f.endswith('.html') or f.endswith('.xhtml')]
        
        blank_pages = []
        for html_file in html_files:
            try:
                content = epub.read(html_file).decode('utf-8')
                # Remove HTML tags and whitespace
                text_content = re.sub(r'<[^>]+>', '', content).strip()
                text_content = re.sub(r'\s+', ' ', text_content)
                
                # Consider page blank if very little text content
                if len(text_content) < 50:  # Less than 50 characters of actual text
                    blank_pages.append(html_file)
            except:
                continue
        
        if len(blank_pages) >= 3:  # 3 or more blank pages is problematic
            self.issues.append(f"MAJOR: Found {len(blank_pages)} blank or nearly empty pages")
            
    except Exception as e:
        pass  # Don't fail if we can't check this

def _check_toc_placement(self, content_html):
    """Check if table of contents appears at the end instead of beginning"""
    # Look for common TOC indicators
    toc_patterns = [
        r'table of contents',
        r'contents',
        r'outline',
        r'<nav[^>]*>.*</nav>',
        r'class=["\']toc["\']'
    ]
    
    content_length = len(content_html)
    for pattern in toc_patterns:
        matches = list(re.finditer(pattern, content_html, re.IGNORECASE))
        for match in matches:
            position = match.start()
            # If TOC appears in last 20% of document
            if position > content_length * 0.8:
                self.issues.append("MAJOR: Table of contents appears at end of document instead of beginning")
                return

def _check_excessive_line_breaks(self, content_html):
    """Check for excessive line breaks in structured content like contact info"""
    # Look for patterns of many consecutive short paragraphs
    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', content_html, re.DOTALL)
    
    consecutive_short = 0
    max_consecutive = 0
    
    for p in paragraphs:
        clean_text = re.sub(r'<[^>]+>', '', p).strip()
        if len(clean_text) < 20 and len(clean_text) > 0:  # Very short but not empty
            consecutive_short += 1
            max_consecutive = max(max_consecutive, consecutive_short)
        else:
            consecutive_short = 0
    
    if max_consecutive >= 8:  # 8+ consecutive short paragraphs suggests formatting issue
        self.issues.append(f"MINOR: Found {max_consecutive} consecutive short paragraphs - may indicate excessive line breaks")

# Add methods to the class
EpubQualityAnalyzer._check_blank_pages = _check_blank_pages
EpubQualityAnalyzer._check_toc_placement = _check_toc_placement  
EpubQualityAnalyzer._check_excessive_line_breaks = _check_excessive_line_breaks

if __name__ == "__main__":
    main()
