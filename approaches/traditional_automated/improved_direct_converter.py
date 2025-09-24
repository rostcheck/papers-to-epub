#!/usr/bin/env python3
import PyPDF2
import re
import zipfile
import uuid
from pathlib import Path
from datetime import datetime

class ImprovedDirectConverter:
    def __init__(self):
        self.epub_dir = Path("epub_books")
        self.epub_dir.mkdir(exist_ok=True)
    
    def convert(self, pdf_path):
        """Convert PDF to high-quality ePub with proper TOC"""
        pdf_path = Path(pdf_path)
        print(f"Converting: {pdf_path.name}")
        
        # Extract all content
        pages_text, metadata = self._extract_pdf_content(pdf_path)
        full_text = "\n\n".join(pages_text)
        
        # Extract metadata
        title = self._extract_title(full_text, metadata)
        author = self._extract_author(full_text, metadata)
        
        # Create structured content with TOC
        toc_entries, chapters = self._create_structured_content(full_text)
        
        # Create ePub
        clean_title = self._clean_filename(title)
        epub_path = self.epub_dir / f"{clean_title}.epub"
        self._create_epub(epub_path, title, author, toc_entries, chapters)
        
        print(f"✓ Created: {epub_path.name}")
        print(f"  Chapters: {len(chapters)}")
        print(f"  TOC entries: {len(toc_entries)}")
        return epub_path
    
    def _extract_pdf_content(self, pdf_path):
        """Extract text from all pages"""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            metadata = reader.metadata or {}
            
            pages_text = []
            for page in reader.pages:
                text = page.extract_text()
                if text.strip():
                    pages_text.append(text)
        
        return pages_text, metadata
    
    def _extract_title(self, text, metadata):
        """Extract clean title"""
        if metadata.get('/Title'):
            title = str(metadata['/Title']).strip()
            # Clean arXiv format
            title = re.sub(r'^arXiv:\d+\.\d+v?\d*\s*\[.*?\]\s*\d+\s*\w+\s*\d+', '', title).strip()
            if title:
                return title
        
        # Look for title in first 1000 chars
        lines = text[:1000].split('\n')
        for line in lines[1:8]:  # Skip first line (often arXiv ID)
            line = line.strip()
            if 10 < len(line) < 200 and not re.match(r'^(abstract|introduction|page|\d+)', line.lower()):
                # Clean up
                line = re.sub(r'\s+', ' ', line)
                return line
        
        return "Academic Paper"
    
    def _extract_author(self, text, metadata):
        """Extract author information"""
        if metadata.get('/Author'):
            return str(metadata['/Author']).strip()
        
        # Look for author patterns after title
        lines = text[:2000].split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            # Look for author patterns
            if re.match(r'^[A-Z][A-Z\s,]+$', line) and 5 < len(line) < 100:
                return line
            # Look for name patterns
            if re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+', line) and len(line) < 50:
                return line
        
        return "Unknown Author"
    
    def _create_structured_content(self, text):
        """Create structured content with proper sections"""
        # Define section patterns for academic papers
        section_patterns = [
            (r'\n\s*(\d+\.?\s+[A-Z][^.\n]{5,80})\s*\n', 'numbered'),
            (r'\n\s*(Abstract)\s*\n', 'keyword'),
            (r'\n\s*(Introduction)\s*\n', 'keyword'),
            (r'\n\s*(Related Work|Literature Review)\s*\n', 'keyword'),
            (r'\n\s*(Methodology|Methods|Approach)\s*\n', 'keyword'),
            (r'\n\s*(Results|Findings|Evaluation)\s*\n', 'keyword'),
            (r'\n\s*(Discussion)\s*\n', 'keyword'),
            (r'\n\s*(Conclusion|Conclusions)\s*\n', 'keyword'),
            (r'\n\s*(References|Bibliography)\s*\n', 'keyword'),
            (r'\n\s*(Appendix|Appendices)\s*\n', 'keyword'),
        ]
        
        # Find all section matches
        all_matches = []
        for pattern, pattern_type in section_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                all_matches.append({
                    'start': match.start(),
                    'end': match.end(),
                    'title': match.group(1).strip(),
                    'type': pattern_type
                })
        
        # Sort by position
        all_matches.sort(key=lambda x: x['start'])
        
        # Create chapters
        chapters = []
        toc_entries = []
        
        if not all_matches:
            # No sections found - create single chapter
            chapters.append({
                'id': 'chapter1',
                'title': 'Full Document',
                'content': self._clean_content(text)
            })
            toc_entries.append({'title': 'Full Document', 'href': 'chapter1.html'})
        else:
            # Create chapters from sections
            for i, match in enumerate(all_matches):
                start_pos = match['end']
                end_pos = all_matches[i + 1]['start'] if i + 1 < len(all_matches) else len(text)
                
                content = text[start_pos:end_pos].strip()
                if len(content) > 50:  # Only include meaningful content
                    chapter_id = f'chapter{len(chapters) + 1}'
                    chapters.append({
                        'id': chapter_id,
                        'title': match['title'],
                        'content': self._clean_content(content)
                    })
                    toc_entries.append({
                        'title': match['title'],
                        'href': f'{chapter_id}.html'
                    })
        
        return toc_entries, chapters
    
    def _clean_content(self, content):
        """Clean and format content"""
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        content = re.sub(r' +', ' ', content)
        
        # Fix hyphenated words across lines
        content = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', content)
        
        # Remove standalone page numbers
        content = re.sub(r'\n\s*\d+\s*\n', '\n\n', content)
        
        # Clean up common artifacts
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        return content.strip()
    
    def _clean_filename(self, title):
        """Create clean filename"""
        clean = re.sub(r'[^\w\s-]', '', title)
        clean = re.sub(r'\s+', '_', clean)
        return clean[:50]
    
    def _create_epub(self, epub_path, title, author, toc_entries, chapters):
        """Create complete ePub with TOC"""
        with zipfile.ZipFile(epub_path, 'w', zipfile.ZIP_DEFLATED) as epub:
            # mimetype
            epub.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
            
            # META-INF
            epub.writestr('META-INF/container.xml', self._container_xml())
            
            # Create TOC HTML page
            toc_html = self._create_toc_html(title, toc_entries)
            epub.writestr('OEBPS/toc.html', toc_html)
            
            # OPF with TOC
            epub.writestr('OEBPS/content.opf', self._content_opf(title, author, chapters))
            
            # NCX
            epub.writestr('OEBPS/toc.ncx', self._toc_ncx(title, toc_entries))
            
            # CSS
            epub.writestr('OEBPS/styles.css', self._styles_css())
            
            # HTML chapters
            for chapter in chapters:
                epub.writestr(f'OEBPS/{chapter["id"]}.html', self._chapter_html(chapter))
    
    def _create_toc_html(self, title, toc_entries):
        """Create HTML table of contents page"""
        toc_links = '\n'.join([
            f'    <li><a href="{entry["href"]}">{entry["title"]}</a></li>'
            for entry in toc_entries
        ])
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <title>Table of Contents</title>
  <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>
  <h1>Table of Contents</h1>
  <h2>{title}</h2>
  <ul class="toc">
{toc_links}
  </ul>
</body>
</html>'''
    
    def _container_xml(self):
        return '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>'''
    
    def _content_opf(self, title, author, chapters):
        uid = str(uuid.uuid4())
        date = datetime.now().strftime('%Y-%m-%d')
        
        manifest_items = ['    <item id="toc-html" href="toc.html" media-type="application/xhtml+xml"/>']
        manifest_items.extend([
            f'    <item id="{chapter["id"]}" href="{chapter["id"]}.html" media-type="application/xhtml+xml"/>'
            for chapter in chapters
        ])
        manifest = '\n'.join(manifest_items)
        
        spine_items = ['    <itemref idref="toc-html"/>']
        spine_items.extend([
            f'    <itemref idref="{chapter["id"]}"/>'
            for chapter in chapters
        ])
        spine = '\n'.join(spine_items)
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="uid" version="2.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:identifier id="uid">{uid}</dc:identifier>
    <dc:title>{title}</dc:title>
    <dc:creator>{author}</dc:creator>
    <dc:language>en</dc:language>
    <dc:date>{date}</dc:date>
  </metadata>
  <manifest>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    <item id="css" href="styles.css" media-type="text/css"/>
{manifest}
  </manifest>
  <spine toc="ncx">
{spine}
  </spine>
</package>'''
    
    def _toc_ncx(self, title, toc_entries):
        uid = str(uuid.uuid4())
        
        nav_points = ['    <navPoint id="toc" playOrder="1">\n      <navLabel><text>Table of Contents</text></navLabel>\n      <content src="toc.html"/>\n    </navPoint>']
        nav_points.extend([
            f'''    <navPoint id="nav{i+2}" playOrder="{i+2}">
      <navLabel><text>{entry['title']}</text></navLabel>
      <content src="{entry['href']}"/>
    </navPoint>'''
            for i, entry in enumerate(toc_entries)
        ])
        nav_points_str = '\n'.join(nav_points)
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="{uid}"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle><text>{title}</text></docTitle>
  <navMap>
{nav_points_str}
  </navMap>
</ncx>'''
    
    def _styles_css(self):
        return '''body {
  font-family: Georgia, serif;
  line-height: 1.6;
  margin: 1em;
  color: #333;
  max-width: 40em;
}

h1, h2, h3 {
  color: #2c3e50;
  margin-top: 1.5em;
  margin-bottom: 0.5em;
}

h1 { font-size: 1.8em; border-bottom: 2px solid #3498db; padding-bottom: 0.5em; }
h2 { font-size: 1.4em; }
h3 { font-size: 1.2em; }

p {
  margin-bottom: 1em;
  text-align: justify;
}

.toc {
  list-style-type: none;
  padding-left: 0;
}

.toc li {
  margin-bottom: 0.5em;
  padding: 0.5em;
  border-left: 3px solid #3498db;
  background-color: #f8f9fa;
}

.toc a {
  text-decoration: none;
  color: #2c3e50;
  font-weight: bold;
}

.toc a:hover {
  color: #3498db;
}

.chapter-title {
  border-bottom: 2px solid #3498db;
  padding-bottom: 0.5em;
  margin-bottom: 1.5em;
}'''
    
    def _chapter_html(self, chapter):
        content = chapter['content']
        
        # Convert paragraphs
        paragraphs = content.split('\n\n')
        html_content = []
        
        for para in paragraphs:
            para = para.strip()
            if para:
                # Check if it's a heading
                if len(para) < 100 and para.isupper():
                    html_content.append(f'<h2>{para}</h2>')
                elif len(para) < 80 and not para.endswith('.'):
                    html_content.append(f'<h3>{para}</h3>')
                else:
                    html_content.append(f'<p>{para}</p>')
        
        content_html = '\n  '.join(html_content)
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <title>{chapter['title']}</title>
  <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>
  <h1 class="chapter-title">{chapter['title']}</h1>
  {content_html}
</body>
</html>'''

def main():
    converter = ImprovedDirectConverter()
    pdf_path = "./Sakana.ai/2502.14297v2.pdf"
    
    if not Path(pdf_path).exists():
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    try:
        epub_path = converter.convert(pdf_path)
        print(f"🎉 Success! Created: {epub_path}")
        
        # Validate quality
        from epub_quality_analyzer import EpubQualityAnalyzer
        analyzer = EpubQualityAnalyzer(epub_path)
        issues = analyzer.analyze()
        
        if not issues:
            print("✅ Perfect quality - No issues detected!")
        else:
            print(f"⚠️  Found {len(issues)} issues:")
            for issue in issues[:3]:
                print(f"  - {issue}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
