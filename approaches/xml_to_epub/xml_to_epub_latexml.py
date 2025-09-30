#!/usr/bin/env python3
"""
LaTeXML XML to ePub Converter
Transforms LaTeXML XML to ePub using XSLT
"""

import sys
import zipfile
from pathlib import Path
from lxml import etree

class LaTeXMLToEpubConverter:
    """Convert LaTeXML XML to ePub format"""
    
    def __init__(self, xml_file: str):
        self.xml_file = Path(xml_file)
        self.output_dir = Path("epub_books")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate ePub filename from XML filename
        base_name = self.xml_file.stem.replace('_latexml', '')
        self.epub_file = self.output_dir / f"{base_name}.epub"
        
        self.xslt_file = Path(__file__).parent / "xml_to_epub_latexml.xsl"
    
    def convert_to_epub(self) -> str:
        """Convert LaTeXML XML to ePub"""
        print("🚀 LaTeXML XML-to-ePub Converter")
        print("=" * 50)
        print(f"✨ Features: LaTeXML XSLT transformation, professional XHTML")
        
        print(f"\n📚 Converting XML to ePub: {self.xml_file}")
        
        # Transform XML to XHTML using XSLT
        html_content = self._transform_xml_to_html()
        
        if not html_content:
            raise RuntimeError("XSLT transformation failed")
        
        # Create ePub package
        self._create_epub_package(html_content)
        
        # Results
        file_size = self.epub_file.stat().st_size
        print(f"✅ Generated ePub: {self.epub_file}")
        print(f"📊 Generated ePub: {file_size:,} bytes")
        print(f"🎉 LaTeXML XSLT transformation complete!")
        
        return str(self.epub_file)
    
    def _transform_xml_to_html(self) -> str:
        """Transform LaTeXML XML to XHTML using XSLT"""
        try:
            # Load XML
            xml_doc = etree.parse(str(self.xml_file))
            
            # Load XSLT
            if not self.xslt_file.exists():
                raise FileNotFoundError(f"XSLT file not found: {self.xslt_file}")
            
            xslt_doc = etree.parse(str(self.xslt_file))
            transform = etree.XSLT(xslt_doc)
            
            # Apply transformation
            result = transform(xml_doc)
            
            if result is None:
                print("❌ XSLT transformation returned None")
                return None
            
            # Convert to string
            html_content = etree.tostring(result, encoding='unicode', method='xml')
            
            print(f"✅ XSLT transformation successful ({len(html_content)} chars)")
            return html_content
            
        except Exception as e:
            print(f"❌ XSLT transformation failed: {e}")
            return None
    
    def _create_epub_package(self, html_content: str):
        """Create ePub package with the transformed HTML"""
        
        # Extract title from HTML
        title = self._extract_title_from_html(html_content)
        
        # Create ePub structure
        with zipfile.ZipFile(self.epub_file, 'w', zipfile.ZIP_DEFLATED) as epub:
            
            # mimetype (must be first, uncompressed)
            epub.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
            
            # META-INF/container.xml
            container_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>'''
            epub.writestr('META-INF/container.xml', container_xml)
            
            # content.opf (package document)
            content_opf = f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:title>{title}</dc:title>
    <dc:creator>Academic Paper</dc:creator>
    <dc:identifier id="bookid">urn:uuid:academic-paper-{self.xml_file.stem}</dc:identifier>
    <dc:language>en</dc:language>
    <meta name="cover" content="cover"/>
  </metadata>
  <manifest>
    <item id="content" href="content.html" media-type="application/xhtml+xml"/>
    <item id="toc" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
  </manifest>
  <spine toc="toc">
    <itemref idref="content"/>
  </spine>
</package>'''
            epub.writestr('content.opf', content_opf)
            
            # toc.ncx (navigation)
            toc_ncx = f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="urn:uuid:academic-paper-{self.xml_file.stem}"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle>
    <text>{title}</text>
  </docTitle>
  <navMap>
    <navPoint id="content" playOrder="1">
      <navLabel>
        <text>{title}</text>
      </navLabel>
      <content src="content.html"/>
    </navPoint>
  </navMap>
</ncx>'''
            epub.writestr('toc.ncx', toc_ncx)
            
            # content.html (main content)
            epub.writestr('content.html', html_content)
    
    def _extract_title_from_html(self, html_content: str) -> str:
        """Extract title from HTML content"""
        try:
            # Parse HTML and extract title
            html_doc = etree.fromstring(html_content.encode('utf-8'))
            title_elem = html_doc.xpath('//title')[0] if html_doc.xpath('//title') else None
            
            if title_elem is not None and title_elem.text:
                return title_elem.text.strip()
            else:
                return "Academic Paper"
                
        except Exception:
            return "Academic Paper"

def main():
    """Command-line interface"""
    if len(sys.argv) != 2:
        print("Usage: python3 xml_to_epub_latexml.py <latexml_xml_file>")
        sys.exit(1)
    
    xml_file = sys.argv[1]
    
    if not Path(xml_file).exists():
        print(f"Error: XML file '{xml_file}' not found")
        sys.exit(1)
    
    try:
        converter = LaTeXMLToEpubConverter(xml_file)
        epub_file = converter.convert_to_epub()
        print(f"\n✅ Success! ePub output: {epub_file}")
    except Exception as e:
        print(f"\n❌ Conversion failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
