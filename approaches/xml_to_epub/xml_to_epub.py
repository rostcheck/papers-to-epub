#!/usr/bin/env python3
import argparse
import zipfile
import re
from pathlib import Path

try:
    import lxml.etree as ET
    LXML_AVAILABLE = True
except ImportError:
    import xml.etree.ElementTree as ET
    LXML_AVAILABLE = False
    print("⚠️ lxml not available, falling back to basic ElementTree")

class XmlToEpubConverter:
    def __init__(self):
        self.output_dir = Path("epub_books")
        self.output_dir.mkdir(exist_ok=True)
        
        # Load XSLT stylesheet
        self.xslt_file = Path(__file__).parent / "xml_to_epub.xsl"
        if not self.xslt_file.exists():
            raise FileNotFoundError(f"XSLT stylesheet not found: {self.xslt_file}")
        
        if LXML_AVAILABLE:
            self.xslt_doc = ET.parse(str(self.xslt_file))
            self.transform = ET.XSLT(self.xslt_doc)
        else:
            print("⚠️ XSLT transformation not available without lxml")
    
    def convert_xml_to_epub(self, xml_file):
        """Convert XML to ePub format using XSLT transformation"""
        
        xml_path = Path(xml_file)
        if not xml_path.exists():
            raise FileNotFoundError(f"XML file not found: {xml_file}")
        
        print(f"📚 Converting XML to ePub: {xml_file}")
        
        # Parse XML document
        if LXML_AVAILABLE:
            xml_doc = ET.parse(str(xml_path))
        else:
            xml_doc = ET.parse(xml_path)
        
        # Extract metadata for ePub files
        metadata = self._extract_metadata(xml_doc)
        
        # Generate ePub filename from title
        title = metadata['title']
        safe_title = re.sub(r'[^\w\s-]', '', title).strip()
        safe_title = re.sub(r'[-\s]+', '_', safe_title)[:50]
        epub_filename = f"{safe_title}.epub"
        epub_path = self.output_dir / epub_filename
        
        # Transform XML to XHTML using XSLT
        if LXML_AVAILABLE:
            content_html = self._transform_with_xslt(xml_doc)
        else:
            content_html = self._transform_fallback(xml_doc)
        
        # Generate other ePub components
        content_opf = self._generate_content_opf(metadata, epub_filename)
        toc_ncx = self._generate_toc_ncx(xml_doc, metadata)
        styles_css = self._generate_styles_css()
        
        # Create ePub
        with zipfile.ZipFile(epub_path, 'w', zipfile.ZIP_DEFLATED) as epub:
            epub.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
            epub.writestr('META-INF/container.xml', self._generate_container_xml())
            epub.writestr('content.html', content_html)
            epub.writestr('content.opf', content_opf)
            epub.writestr('toc.ncx', toc_ncx)
            epub.writestr('styles.css', styles_css)
            
            # Add image files if they exist
            image_files = ['efficient-models.png']
            for img_file in image_files:
                img_path = Path(__file__).parent / img_file
                if img_path.exists():
                    epub.write(img_path, img_file)
        
        print(f"✅ Generated ePub: {epub_path}")
        return epub_path
    
    def _transform_with_xslt(self, xml_doc):
        """Transform XML to XHTML using XSLT"""
        try:
            result = self.transform(xml_doc)
            return str(result)
        except Exception as e:
            print(f"⚠️ XSLT transformation failed: {e}")
            print("Falling back to basic transformation...")
            return self._transform_fallback(xml_doc)
    
    def _transform_fallback(self, xml_doc):
        """Fallback transformation without XSLT"""
        root = xml_doc.getroot()
        
        # Extract basic information
        ns = {'ap': 'http://example.com/academic-paper'}
        
        title_elem = root.find('.//ap:title', ns)
        title = title_elem.text if title_elem is not None else "Untitled"
        
        # Basic HTML structure
        html = f'''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
    <meta charset="utf-8"/>
    <title>{self._escape_html(title)}</title>
    <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>
    <div class="title-page">
        <h1 class="title">{self._escape_html(title)}</h1>
        <p><em>Converted without XSLT - install lxml for full transformation</em></p>
    </div>
    
    <div class="content">
        <p>This ePub was generated using fallback transformation.</p>
        <p>For full XML-to-XHTML transformation with proper formatting, please install lxml:</p>
        <p><code>pip install lxml</code></p>
    </div>
</body>
</html>'''
        return html
    
    def _extract_metadata(self, xml_doc):
        """Extract metadata from XML document"""
        root = xml_doc.getroot()
        ns = {'ap': 'http://example.com/academic-paper'}
        
        # Extract title
        title_elem = root.find('.//ap:title', ns)
        title = title_elem.text if title_elem is not None else "Untitled"
        
        # Extract authors
        authors = []
        for author_elem in root.findall('.//ap:author', ns):
            name_elem = author_elem.find('ap:name', ns)
            if name_elem is not None:
                authors.append({'name': name_elem.text})
        
        # Extract publication info
        pub_info = {}
        pub_elem = root.find('.//ap:publication_info', ns)
        if pub_elem is not None:
            for field in ['venue', 'date', 'arxiv_id']:
                elem = pub_elem.find(f'ap:{field}', ns)
                if elem is not None:
                    pub_info[field] = elem.text
        
        return {
            'title': title,
            'authors': authors,
            'publication_info': pub_info
        }
    
    def _generate_content_opf(self, metadata, filename):
        """Generate content.opf metadata file"""
        opf = f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:title>{self._escape_xml(metadata['title'])}</dc:title>'''
        
        for author in metadata['authors']:
            opf += f'\n    <dc:creator opf:role="aut">{self._escape_xml(author["name"])}</dc:creator>'
        
        if metadata.get('publication_info', {}).get('date'):
            opf += f'\n    <dc:date>{metadata["publication_info"]["date"]}</dc:date>'
        
        if metadata.get('publication_info', {}).get('arxiv_id'):
            opf += f'\n    <dc:identifier id="bookid">arxiv:{metadata["publication_info"]["arxiv_id"]}</dc:identifier>'
        else:
            opf += f'\n    <dc:identifier id="bookid">{filename}</dc:identifier>'
        
        opf += '''
    <dc:language>en</dc:language>
    <dc:rights>Academic use</dc:rights>
  </metadata>
  
  <manifest>
    <item id="content" href="content.html" media-type="application/xhtml+xml"/>
    <item id="toc" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    <item id="css" href="styles.css" media-type="text/css"/>
    <item id="img1" href="efficient-models.png" media-type="image/png"/>
  </manifest>
  
  <spine toc="toc">
    <itemref idref="content"/>
  </spine>
  
  <guide>
    <reference type="toc" title="Table of Contents" href="content.html#toc"/>
  </guide>
</package>'''
        return opf
    
    def _generate_toc_ncx(self, xml_doc, metadata):
        """Generate toc.ncx navigation file"""
        root = xml_doc.getroot()
        ns = {'ap': 'http://example.com/academic-paper'}
        
        ncx = f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="{metadata.get('publication_info', {}).get('arxiv_id', 'generated')}"/>
    <meta name="dtb:depth" content="2"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  
  <docTitle>
    <text>{self._escape_xml(metadata['title'])}</text>
  </docTitle>
  
  <navMap>'''
        
        play_order = 1
        
        # Add sections to navigation
        for section in root.findall('.//ap:section', ns):
            section_id = section.get('id', f'section{play_order}')
            title_elem = section.find('ap:title', ns)
            title = title_elem.text if title_elem is not None else f'Section {play_order}'
            
            ncx += f'''
    <navPoint id="{section_id}" playOrder="{play_order}">
      <navLabel>
        <text>{self._escape_xml(title)}</text>
      </navLabel>
      <content src="content.html#{section_id}"/>
    </navPoint>'''
            play_order += 1
        
        ncx += '''
  </navMap>
</ncx>'''
        return ncx
    
    def _generate_container_xml(self):
        """Generate META-INF/container.xml"""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>'''
    
    def _generate_styles_css(self):
        """Generate CSS styles"""
        return '''/* Academic ePub Styles with Math Support */

body {
    font-family: "Times New Roman", serif;
    font-size: 1em;
    line-height: 1.6;
    margin: 1em;
    color: #333;
}

/* Math styling */
.math {
    font-family: "Times New Roman", serif;
    font-size: 1em;
}

.math-display {
    display: block;
    text-align: center;
    margin: 1em 0;
}

/* Title Page */
.title-page {
    text-align: center;
    margin: 2em 0 3em 0;
    page-break-after: always;
}

.title {
    font-size: 1.8em;
    font-weight: bold;
    color: #2c3e50;
    margin: 1em 0;
    line-height: 1.3;
}

.authors {
    margin: 2em 0;
}

.author-names {
    font-size: 1.2em;
    font-weight: bold;
    margin: 1em 0;
}

.affiliation {
    font-size: 0.9em;
    color: #666;
    margin: 0.5em 0;
}

/* Table of Contents */
.toc {
    background: #f8f9fa;
    padding: 1.5em;
    margin: 2em 0;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    page-break-after: always;
}

.toc h2 {
    margin-top: 0;
    color: #2c3e50;
    border-bottom: 2px solid #3498db;
    padding-bottom: 0.5em;
}

.toc ul {
    list-style-type: none;
    padding-left: 0;
}

.toc li {
    margin: 0.5em 0;
    padding-left: 1em;
}

.toc li.subsection {
    padding-left: 2em;
    font-size: 0.9em;
}

/* Abstract */
.abstract {
    background: #f8f9fa;
    padding: 1.5em;
    border-left: 4px solid #3498db;
    margin: 2em 0;
}

/* Sections */
.section {
    margin: 2em 0;
}

.section-title {
    color: #2c3e50;
    border-bottom: 2px solid #3498db;
    padding-bottom: 0.5em;
    margin: 2em 0 1em 0;
}

.subsection-title {
    color: #34495e;
    border-bottom: 1px solid #bdc3c7;
    padding-bottom: 0.3em;
    margin: 1.5em 0 0.5em 0;
}

/* Equations */
.equations {
    margin: 3em 0;
    border-top: 2px solid #3498db;
    padding-top: 2em;
}

.equation {
    margin: 2em 0;
    text-align: center;
}

.equation-content {
    font-size: 1.1em;
    margin: 1em 0;
}

.equation-description {
    font-size: 0.9em;
    color: #666;
    font-style: italic;
}

/* References */
.references {
    margin: 3em 0 0 0;
    border-top: 2px solid #3498db;
    padding-top: 2em;
}

.reference-list {
    padding-left: 2em;
}

.reference-item {
    margin: 1em 0;
    text-align: justify;
    line-height: 1.5;
}

.ref-authors {
    font-weight: bold;
}

.ref-title {
    font-style: italic;
}

.ref-venue {
    color: #666;
}

.ref-year {
    font-weight: bold;
}'''
    
    def _escape_html(self, text):
        """Escape HTML special characters"""
        if not text:
            return ''
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#x27;'))
    
    def _escape_xml(self, text):
        """Escape XML special characters"""
        return self._escape_html(text)

def main():
    """XML to ePub conversion with XSLT"""
    parser = argparse.ArgumentParser(description='Convert XML file to ePub format')
    parser.add_argument('xml_file', help='Path to the XML file to convert')
    
    args = parser.parse_args()
    
    xml_file = args.xml_file
    
    if not Path(xml_file).exists():
        print(f"❌ XML file not found: {xml_file}")
        return
    
    converter = XmlToEpubConverter()
    
    print("🚀 XML-to-ePub Converter (XSLT)")
    print("=" * 50)
    if LXML_AVAILABLE:
        print("✨ Features: XSLT transformation, native MathML support, professional XHTML")
    else:
        print("⚠️ Limited features: lxml not available, using fallback transformation")
    print()
    
    try:
        epub_path = converter.convert_xml_to_epub(xml_file)
        
        file_size = epub_path.stat().st_size
        print(f"📊 Generated ePub: {file_size:,} bytes")
        
        if LXML_AVAILABLE:
            print("🎉 XSLT transformation complete!")
        else:
            print("⚠️ Fallback transformation complete - install lxml for full features")
        
    except Exception as e:
        print(f"❌ Error converting XML to ePub: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
