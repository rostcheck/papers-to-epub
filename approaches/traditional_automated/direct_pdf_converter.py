#!/usr/bin/env python3
import PyPDF2
import re
import zipfile
import uuid
from pathlib import Path
from datetime import datetime

class DirectPDFConverter:
    def __init__(self):
        self.epub_dir = Path("epub_books")
        self.epub_dir.mkdir(exist_ok=True)
    
    def convert(self, pdf_path):
        """Convert PDF directly to ePub"""
        pdf_path = Path(pdf_path)
        print(f"Converting: {pdf_path.name}")
        
        # Extract text and metadata
        text_content, metadata = self._extract_pdf_content(pdf_path)
        
        # Process content
        title, author, chapters = self._process_content(text_content, metadata)
        
        # Create ePub
        epub_path = self.epub_dir / f"{self._clean_filename(title)}.epub"
        self._create_epub(epub_path, title, author, chapters)
        
        print(f"✓ Created: {epub_path.name}")
        return epub_path
    
    def _extract_pdf_content(self, pdf_path):
        """Extract text and metadata from PDF"""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            # Extract metadata
            metadata = reader.metadata or {}
            
            # Extract text
            text_content = []
            for page in reader.pages:
                text = page.extract_text()
                if text.strip():
                    text_content.append(text)
        
        return text_content, metadata
    
    def _process_content(self, text_content, metadata):
        """Process extracted content into structured format"""
        full_text = "\n\n".join(text_content)
        
        # Extract title
        title = self._extract_title(full_text, metadata)
        
        # Extract author
        author = self._extract_author(full_text, metadata)
        
        # Create chapters
        chapters = self._create_chapters(full_text)
        
        return title, author, chapters
    
    def _extract_title(self, text, metadata):
        """Extract clean title"""
        # Try metadata first
        if metadata.get('/Title'):
            return str(metadata['/Title']).strip()
        
        # Extract from first lines
        lines = text.split('\n')[:10]
        for line in lines:
            line = line.strip()
            if len(line) > 10 and len(line) < 200:
                # Clean up common artifacts
                line = re.sub(r'^\d+\s*', '', line)  # Remove leading numbers
                line = re.sub(r'\s+', ' ', line)     # Normalize spaces
                if not re.match(r'^(abstract|introduction|page)', line.lower()):
                    return line
        
        return "Academic Paper"
    
    def _extract_author(self, text, metadata):
        """Extract author information"""
        if metadata.get('/Author'):
            return str(metadata['/Author']).strip()
        
        # Look for author patterns in first 500 chars
        first_part = text[:500]
        author_patterns = [
            r'(?:by|author[s]?:?)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*$'
        ]
        
        for pattern in author_patterns:
            match = re.search(pattern, first_part, re.MULTILINE | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Unknown Author"
    
    def _create_chapters(self, text):
        """Create structured chapters"""
        # Split by common section headers
        section_patterns = [
            r'\n\s*(\d+\.?\s+[A-Z][^.\n]{10,80})\s*\n',
            r'\n\s*(Abstract|Introduction|Methodology|Results|Discussion|Conclusion|References)\s*\n',
            r'\n\s*([A-Z][A-Z\s]{5,50})\s*\n'
        ]
        
        chapters = []
        current_text = text
        
        for pattern in section_patterns:
            matches = list(re.finditer(pattern, current_text, re.IGNORECASE))
            if len(matches) >= 2:  # Need at least 2 sections
                for i, match in enumerate(matches):
                    title = match.group(1).strip()
                    start = match.end()
                    end = matches[i + 1].start() if i + 1 < len(matches) else len(current_text)
                    content = current_text[start:end].strip()
                    
                    if content and len(content) > 100:  # Meaningful content
                        chapters.append({
                            'title': title,
                            'content': self._clean_content(content)
                        })
                break
        
        # Fallback: single chapter
        if not chapters:
            chapters = [{
                'title': 'Full Document',
                'content': self._clean_content(text)
            }]
        
        return chapters
    
    def _clean_content(self, content):
        """Clean and format content"""
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        content = re.sub(r' +', ' ', content)
        
        # Fix common PDF artifacts
        content = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', content)  # Hyphenated words
        content = re.sub(r'\n\s*(\d+)\s*\n', r'\n\n', content)    # Page numbers
        
        return content.strip()
    
    def _clean_filename(self, title):
        """Create clean filename"""
        clean = re.sub(r'[^\w\s-]', '', title)
        clean = re.sub(r'\s+', '_', clean)
        return clean[:50]
    
    def _create_epub(self, epub_path, title, author, chapters):
        """Create ePub file"""
        with zipfile.ZipFile(epub_path, 'w', zipfile.ZIP_DEFLATED) as epub:
            # mimetype
            epub.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
            
            # META-INF
            epub.writestr('META-INF/container.xml', self._container_xml())
            
            # OPF
            epub.writestr('OEBPS/content.opf', self._content_opf(title, author, chapters))
            
            # NCX
            epub.writestr('OEBPS/toc.ncx', self._toc_ncx(title, chapters))
            
            # CSS
            epub.writestr('OEBPS/styles.css', self._styles_css())
            
            # HTML chapters
            for i, chapter in enumerate(chapters):
                epub.writestr(f'OEBPS/chapter{i+1}.html', self._chapter_html(chapter))
    
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
        
        manifest = '\n'.join([
            f'    <item id="chapter{i+1}" href="chapter{i+1}.html" media-type="application/xhtml+xml"/>'
            for i in range(len(chapters))
        ])
        
        spine = '\n'.join([
            f'    <itemref idref="chapter{i+1}"/>'
            for i in range(len(chapters))
        ])
        
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
    
    def _toc_ncx(self, title, chapters):
        uid = str(uuid.uuid4())
        
        nav_points = '\n'.join([
            f'''    <navPoint id="chapter{i+1}" playOrder="{i+1}">
      <navLabel><text>{chapter['title']}</text></navLabel>
      <content src="chapter{i+1}.html"/>
    </navPoint>'''
            for i, chapter in enumerate(chapters)
        ])
        
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
{nav_points}
  </navMap>
</ncx>'''
    
    def _styles_css(self):
        return '''body {
  font-family: Georgia, serif;
  line-height: 1.6;
  margin: 1em;
  color: #333;
}

h1, h2, h3 {
  color: #2c3e50;
  margin-top: 1.5em;
  margin-bottom: 0.5em;
}

h1 { font-size: 1.8em; }
h2 { font-size: 1.4em; }
h3 { font-size: 1.2em; }

p {
  margin-bottom: 1em;
  text-align: justify;
}

.chapter-title {
  border-bottom: 2px solid #3498db;
  padding-bottom: 0.5em;
  margin-bottom: 1.5em;
}'''
    
    def _chapter_html(self, chapter):
        content = chapter['content'].replace('\n\n', '</p>\n<p>')
        content = f'<p>{content}</p>'
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <title>{chapter['title']}</title>
  <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>
  <h1 class="chapter-title">{chapter['title']}</h1>
  {content}
</body>
</html>'''

def main():
    converter = DirectPDFConverter()
    pdf_path = "./Sakana.ai/2502.14297v2.pdf"
    
    if not Path(pdf_path).exists():
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    try:
        epub_path = converter.convert(pdf_path)
        print(f"🎉 Success! Created: {epub_path}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
