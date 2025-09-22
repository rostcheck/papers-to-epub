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
            
        self._print_summary()
        return self.issues
    
    def _get_main_content(self, epub):
        """Extract main HTML content"""
        try:
            return epub.read('index.html').decode('utf-8')
        except:
            # Try other common names
            for name in ['content.html', 'text.html']:
                try:
                    return epub.read(name).decode('utf-8')
                except:
                    continue
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
        """Check for repeated footer/header content"""
        # Common footer patterns
        patterns = [
            r'\d{1,2}/\d{1,2}/\d{2,4},?\s+\d{1,2}:\d{2}\s+[AP]M',  # Date/time
            r'https?://[^\s]+',  # URLs
            r'\d+/\d+$',  # Page numbers like "1/10"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            if len(matches) > 3:  # If appears more than 3 times, likely repeated
                counter = Counter(matches)
                for match, count in counter.most_common(3):
                    if count > 2:
                        self.issues.append(f"MAJOR: Repeated footer content '{match}' appears {count} times")
    
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

if __name__ == "__main__":
    main()
