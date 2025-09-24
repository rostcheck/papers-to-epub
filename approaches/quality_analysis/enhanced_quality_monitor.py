#!/usr/bin/env python3
import re
from pathlib import Path
import zipfile
from bs4 import BeautifulSoup

class EnhancedQualityMonitor:
    def __init__(self):
        self.quality_issues = []
        self.page_issues = {}
    
    def analyze_epub_detailed(self, epub_path):
        """Comprehensive page-by-page quality analysis"""
        print(f"🔍 Detailed Quality Analysis: {epub_path.name}")
        
        with zipfile.ZipFile(epub_path, 'r') as epub:
            content = epub.read('content.html').decode('utf-8')
            soup = BeautifulSoup(content, 'html.parser')
            
            # Analyze different aspects
            self._check_title_quality(soup)
            self._check_text_fragmentation(soup)
            self._check_table_presence(soup)
            self._check_content_completeness(soup)
            self._check_structure_quality(soup)
            
        return self._generate_report()
    
    def _check_title_quality(self, soup):
        """Check title extraction quality"""
        title = soup.find('title')
        h1 = soup.find('h1')
        
        issues = []
        if title:
            title_text = title.get_text()
            if len(title_text) < 20:
                issues.append("Title too short")
            if title_text.startswith(('or ', 'and ', 'the ')):
                issues.append("Title appears truncated")
            if not title_text[0].isupper():
                issues.append("Title doesn't start with capital")
        else:
            issues.append("No title found")
            
        if issues:
            self.quality_issues.extend([f"TITLE: {issue}" for issue in issues])
    
    def _check_text_fragmentation(self, soup):
        """Detect fragmented text (missing spaces)"""
        text_content = soup.get_text()
        
        # Common fragmentation patterns
        fragmentation_patterns = [
            r'[a-z][A-Z]',  # lowercase followed by uppercase (missing space)
            r'[a-z]\d',     # letter followed by number
            r'\d[A-Z]',     # number followed by uppercase letter
            r'[a-z]\(',     # letter followed by parenthesis
            r'\)[a-z]',     # parenthesis followed by letter
        ]
        
        fragmentation_count = 0
        for pattern in fragmentation_patterns:
            matches = re.findall(pattern, text_content)
            fragmentation_count += len(matches)
        
        if fragmentation_count > 20:  # Threshold for concern
            self.quality_issues.append(f"TEXT: High fragmentation detected ({fragmentation_count} instances)")
        elif fragmentation_count > 5:
            self.quality_issues.append(f"TEXT: Moderate fragmentation detected ({fragmentation_count} instances)")
    
    def _check_table_presence(self, soup):
        """Check for proper table formatting"""
        tables = soup.find_all('table')
        
        if not tables:
            # Check if there should be tables (look for table-like content)
            text = soup.get_text().lower()
            table_indicators = [
                'table 1', 'table 2', 'iteration', 'baseline',
                'results', 'experiment', 'comparison'
            ]
            
            if any(indicator in text for indicator in table_indicators):
                self.quality_issues.append("TABLE: Expected tables not found (may be missing or converted to text)")
        else:
            # Check table quality
            for i, table in enumerate(tables):
                rows = table.find_all('tr')
                if len(rows) < 2:
                    self.quality_issues.append(f"TABLE: Table {i+1} has insufficient rows")
    
    def _check_content_completeness(self, soup):
        """Check for missing or empty content sections"""
        # Check abstract
        abstract = soup.find(class_='abstract') or soup.find('div', string=re.compile('abstract', re.I))
        if abstract:
            abstract_text = abstract.get_text().strip()
            if len(abstract_text) < 100:
                self.quality_issues.append("CONTENT: Abstract too short or missing")
        
        # Check for empty paragraphs
        empty_paragraphs = soup.find_all('p', string=re.compile(r'^\s*$'))
        if len(empty_paragraphs) > 5:
            self.quality_issues.append(f"CONTENT: {len(empty_paragraphs)} empty paragraphs found")
    
    def _check_structure_quality(self, soup):
        """Check document structure quality"""
        # Check heading hierarchy
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
        if len(headings) < 3:
            self.quality_issues.append("STRUCTURE: Insufficient heading structure")
        
        # Check TOC quality
        toc = soup.find(class_='toc') or soup.find('div', string=re.compile('table of contents', re.I))
        if toc:
            links = toc.find_all('a')
            empty_links = [link for link in links if not link.get_text().strip()]
            if len(empty_links) > 2:
                self.quality_issues.append(f"TOC: {len(empty_links)} empty TOC entries")
    
    def _generate_report(self):
        """Generate comprehensive quality report"""
        report = {
            'total_issues': len(self.quality_issues),
            'issues_by_category': {},
            'severity_breakdown': {'CRITICAL': 0, 'MAJOR': 0, 'MINOR': 0},
            'detailed_issues': self.quality_issues
        }
        
        # Categorize issues
        for issue in self.quality_issues:
            category = issue.split(':')[0]
            if category not in report['issues_by_category']:
                report['issues_by_category'][category] = 0
            report['issues_by_category'][category] += 1
            
            # Assign severity
            if any(word in issue.upper() for word in ['MISSING', 'EMPTY', 'FRAGMENTATION']):
                report['severity_breakdown']['MAJOR'] += 1
            elif any(word in issue.upper() for word in ['TOO SHORT', 'INSUFFICIENT']):
                report['severity_breakdown']['MINOR'] += 1
            else:
                report['severity_breakdown']['CRITICAL'] += 1
        
        return report

def main():
    """Test enhanced quality monitoring"""
    monitor = EnhancedQualityMonitor()
    
    # Test on Q CLI generated ePub
    q_epub = Path("epub_books/or-an-EmergingReality-Towards-Artificial-ResearchIntell-igenceARI.epub")
    manual_epub = Path("epub_books/Manual_Sakana_AI_Scientist_Evaluation.epub")
    
    print("=" * 60)
    print("ENHANCED QUALITY COMPARISON")
    print("=" * 60)
    
    if q_epub.exists():
        print("\n🤖 Q CLI Generated ePub:")
        q_report = monitor.analyze_epub_detailed(q_epub)
        print(f"Total Issues: {q_report['total_issues']}")
        print(f"By Category: {q_report['issues_by_category']}")
        print("Issues:")
        for issue in q_report['detailed_issues'][:5]:
            print(f"  - {issue}")
    
    if manual_epub.exists():
        print("\n✋ Manual Generated ePub:")
        monitor.quality_issues = []  # Reset
        manual_report = monitor.analyze_epub_detailed(manual_epub)
        print(f"Total Issues: {manual_report['total_issues']}")
        print(f"By Category: {manual_report['issues_by_category']}")
        if manual_report['detailed_issues']:
            print("Issues:")
            for issue in manual_report['detailed_issues']:
                print(f"  - {issue}")
        else:
            print("🎉 No issues detected!")

if __name__ == "__main__":
    main()
