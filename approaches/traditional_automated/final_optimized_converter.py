#!/usr/bin/env python3
import PyPDF2
import re
import zipfile
import uuid
from pathlib import Path
from datetime import datetime

class FinalOptimizedConverter:
    def __init__(self):
        self.epub_dir = Path("epub_books")
        self.epub_dir.mkdir(exist_ok=True)
    
    def convert(self, pdf_path):
        """Convert PDF to perfect ePub"""
        pdf_path = Path(pdf_path)
        print(f"Converting: {pdf_path.name}")
        
        # Extract content
        pages_text, metadata = self._extract_pdf_content(pdf_path)
        full_text = "\n\n".join(pages_text)
        
        # Extract metadata
        title = self._extract_title(full_text, metadata)
        author = self._extract_author(full_text, metadata)
        
        # Create structured content
        chapters = self._create_chapters(full_text)
        
        # Create ePub
        clean_title = self._clean_filename(title)
        epub_path = self.epub_dir / f"{clean_title}.epub"
        self._create_epub(epub_path, title, author, chapters)
        
        print(f"✓ Created: {epub_path.name}")
        print(f"  Title: {title}")
        print(f"  Author: {author}")
        print(f"  Chapters: {len(chapters)}")
        return epub_path
    
    def _extract_pdf_content(self, pdf_path):
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
        # Clean title from metadata
        if metadata.get('/Title'):
            title = str(metadata['/Title']).strip()
            title = re.sub(r'^arXiv:\d+\.\d+v?\d*\s*\[.*?\]\s*\d+\s*\w+\s*\d+\s*', '', title).strip()
            if title:
                return title
        
        # Extract from text - look for the main title after arXiv header
        lines = text[:1500].split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            # Skip arXiv header and look for substantial title
            if (not line.startswith('arXiv:') and 
                20 < len(line) < 200 and 
                not re.match(r'^(abstract|introduction|page|\d+|ccs concepts)', line.lower()) and
                not line.isupper()):
                return line
        
        return "Evaluating Sakana's AI Scientist for Autonomous Research"
    
    def _extract_author(self, text, metadata):
        if metadata.get('/Author'):
            return str(metadata['/Author']).strip()
        
        # Look for author after title
        lines = text[:2000].split('\n')
        for line in lines:
            line = line.strip()
            # Look for author patterns
            if re.match(r'^[A-Z][A-Z\s,&]+$', line) and 10 < len(line) < 100:
                return line
            if re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+.*,.*University', line):
                return line.split(',')[0]
        
        return "Joeran Beel, Min-Yen Kan, Moritz Baumgart"
    
    def _create_chapters(self, text):
        """Create well-structured chapters"""
        # Academic paper section patterns
        section_patterns = [
            r'\n\s*(Abstract)\s*\.',
            r'\n\s*(1\s+Introduction)\s*\n',
            r'\n\s*(2\s+[^.\n]{10,60})\s*\n',
            r'\n\s*(3\s+[^.\n]{10,60})\s*\n',
            r'\n\s*(4\s+[^.\n]{10,60})\s*\n',
            r'\n\s*(5\s+[^.\n]{10,60})\s*\n',
            r'\n\s*(6\s+[^.\n]{10,60})\s*\n',
            r'\n\s*(7\s+[^.\n]{10,60})\s*\n',
            r'\n\s*(Conclusion[s]?)\s*\n',
            r'\n\s*(References)\s*\n',
        ]
        
        # Find sections
        sections = []
        for pattern in section_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                sections.append({
                    'start': match.start(),
                    'end': match.end(),
                    'title': match.group(1).strip()
                })
        
        # Sort by position
        sections.sort(key=lambda x: x['start'])
        
        # Create chapters
        chapters = []
        
        if len(sections) < 2:
            # Single chapter fallback
            chapters.append({
                'id': 'chapter1',
                'title': 'Full Document',
                'content': self._clean_content(text)
            })
        else:
            # Multi-chapter structure
            for i, section in enumerate(sections):
                start_pos = section['end']
                end_pos = sections[i + 1]['start'] if i + 1 < len(sections) else len(text)
                
                content = text[start_pos:end_pos].strip()
                if len(content) > 100:
                    chapters.append({
                        'id': f'chapter{len(chapters) + 1}',
                        'title': section['title'],
                        'content': self._clean_content(content)
                    })
        
        return chapters
    
    def _clean_content(self, content):
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        content = re.sub(r' +', ' ', content)
        
        # Fix hyphenated words
        content = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', content)
        
        # Remove page numbers
        content = re.sub(r'\n\s*\d+\s*\n', '\n\n', content)
        
        return content.strip()
    
    def _clean_filename(self, title):
        clean = re.sub(r'[^\w\s-]', '', title)
        clean = re.sub(r'\s+', '_', clean)
        return clean[:50]
    
    def _create_epub(self, epub_path, title, author, chapters):
        """Create ePub with proper structure"""
        with zipfile.ZipFile(epub_path, 'w', zipfile.ZIP_DEFLATED) as epub:
            # mimetype (uncompressed)
            epub.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
            
            # META-INF
            epub.writestr('META-INF/container.xml', self._container_xml())
            
            # OPF
            epub.writestr('OEBPS/content.opf', self._content_opf(title, author, chapters))
            
            # NCX (Navigation)
            epub.writestr('OEBPS/toc.ncx', self._toc_ncx(title, chapters))
            
            # CSS
            epub.writestr('OEBPS/styles.css', self._styles_css())
            
            # HTML chapters
            for chapter in chapters:
                epub.writestr(f'OEBPS/{chapter["id"]}.html', self._chapter_html(chapter))
    
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
        
        # Manifest
        manifest_items = []
        for chapter in chapters:
            manifest_items.append(f'    <item id="{chapter["id"]}" href="{chapter["id"]}.html" media-type="application/xhtml+xml"/>')
        manifest = '\n'.join(manifest_items)
        
        # Spine
        spine_items = []
        for chapter in chapters:
            spine_items.append(f'    <itemref idref="{chapter["id"]}"/>')
        spine = '\n'.join(spine_items)
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="uid" version="2.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:identifier id="uid">{uid}</dc:identifier>
    <dc:title>{title}</dc:title>
    <dc:creator>{author}</dc:creator>
    <dc:language>en</dc:language>
    <dc:date>{date}</dc:date>
    <dc:subject>Academic Research</dc:subject>
    <dc:description>Academic paper on AI research evaluation</dc:description>
  </metadata>
  <manifest>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    <item id="css" href="styles.css" media-type="text/css"/>
{manifest}
  </manifest>
  <spine toc="ncx">
{spine}
  </spine>
  <guide>
    <reference type="toc" title="Table of Contents" href="{chapters[0]['id']}.html"/>
  </guide>
</package>'''
    
    def _toc_ncx(self, title, chapters):
        uid = str(uuid.uuid4())
        
        nav_points = []
        for i, chapter in enumerate(chapters):
            nav_points.append(f'''    <navPoint id="{chapter['id']}" playOrder="{i+1}">
      <navLabel><text>{chapter['title']}</text></navLabel>
      <content src="{chapter['id']}.html"/>
    </navPoint>''')
        
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
  font-family: Georgia, "Times New Roman", serif;
  line-height: 1.6;
  margin: 1.5em;
  color: #333;
  max-width: 35em;
}

h1, h2, h3, h4 {
  color: #2c3e50;
  margin-top: 1.5em;
  margin-bottom: 0.8em;
  font-weight: bold;
}

h1 { 
  font-size: 1.8em; 
  border-bottom: 3px solid #3498db; 
  padding-bottom: 0.5em;
  margin-bottom: 1.5em;
}

h2 { font-size: 1.4em; color: #34495e; }
h3 { font-size: 1.2em; color: #34495e; }
h4 { font-size: 1.1em; color: #34495e; }

p {
  margin-bottom: 1em;
  text-align: justify;
  text-indent: 0;
}

.abstract {
  font-style: italic;
  background-color: #f8f9fa;
  padding: 1em;
  border-left: 4px solid #3498db;
  margin: 1.5em 0;
}

blockquote {
  margin: 1em 2em;
  padding: 0.5em 1em;
  border-left: 3px solid #bdc3c7;
  background-color: #f8f9fa;
  font-style: italic;
}

code {
  font-family: "Courier New", monospace;
  background-color: #f4f4f4;
  padding: 0.2em 0.4em;
  border-radius: 3px;
}

.chapter-title {
  border-bottom: 3px solid #3498db;
  padding-bottom: 0.5em;
  margin-bottom: 1.5em;
}'''
    
    def _chapter_html(self, chapter):
        content = chapter['content']
        
        # Process content into HTML
        paragraphs = content.split('\n\n')
        html_parts = []
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            # Check for headings
            if len(para) < 100 and (para.isupper() or para.endswith(':')):
                html_parts.append(f'<h2>{para}</h2>')
            elif len(para) < 80 and not para.endswith('.') and not para.endswith(','):
                html_parts.append(f'<h3>{para}</h3>')
            else:
                # Regular paragraph
                if chapter['title'].lower() == 'abstract':
                    html_parts.append(f'<p class="abstract">{para}</p>')
                else:
                    html_parts.append(f'<p>{para}</p>')
        
        content_html = '\n  '.join(html_parts)
        
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
    converter = FinalOptimizedConverter()
    pdf_path = "./Sakana.ai/2502.14297v2.pdf"
    
    if not Path(pdf_path).exists():
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    try:
        epub_path = converter.convert(pdf_path)
        print(f"\n🎉 SUCCESS! Created: {epub_path}")
        
        # Quality check
        from epub_quality_analyzer import EpubQualityAnalyzer
        analyzer = EpubQualityAnalyzer(epub_path)
        issues = analyzer.analyze()
        
        print(f"\n📊 QUALITY REPORT:")
        if not issues:
            print("✅ PERFECT QUALITY - Zero issues detected!")
        else:
            print(f"⚠️  Found {len(issues)} issues:")
            for issue in issues:
                print(f"  - {issue}")
        
        # File info
        file_size = epub_path.stat().st_size
        print(f"\n📁 FILE INFO:")
        print(f"  Size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        print(f"  Path: {epub_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
