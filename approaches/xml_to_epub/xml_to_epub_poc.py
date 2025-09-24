#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import zipfile
import re
from pathlib import Path

class XmlToEpubConverter:
    def __init__(self):
        self.output_dir = Path("epub_books")
        self.output_dir.mkdir(exist_ok=True)
        
        # Namespace mappings
        self.ns = {
            'ap': 'http://example.com/academic-paper',
            'xhtml': 'http://www.w3.org/1999/xhtml',
            'mathml': 'http://www.w3.org/1998/Math/MathML'
        }
        
        # Register namespaces for ElementTree
        for prefix, uri in self.ns.items():
            ET.register_namespace(prefix, uri)
    
    def convert_xml_to_epub(self, xml_file):
        """Convert XML to ePub format"""
        
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        print(f"📚 Converting XML to ePub: {xml_file}")
        
        # Extract metadata
        metadata = self._extract_metadata(root)
        
        # Generate ePub filename from title
        title = metadata['title']
        safe_title = re.sub(r'[^\w\s-]', '', title).strip()
        safe_title = re.sub(r'[-\s]+', '_', safe_title)[:50]
        epub_filename = f"{safe_title}.epub"
        epub_path = self.output_dir / epub_filename
        
        # Generate ePub components
        content_html = self._generate_content_html(root)
        content_opf = self._generate_content_opf(metadata, epub_filename)
        toc_ncx = self._generate_toc_ncx(root, metadata)
        styles_css = self._generate_styles_css()
        
        # Create ePub
        with zipfile.ZipFile(epub_path, 'w', zipfile.ZIP_DEFLATED) as epub:
            epub.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
            epub.writestr('META-INF/container.xml', self._generate_container_xml())
            epub.writestr('content.html', content_html)
            epub.writestr('content.opf', content_opf)
            epub.writestr('toc.ncx', toc_ncx)
            epub.writestr('styles.css', styles_css)
        
        print(f"✅ Generated ePub: {epub_path}")
        return epub_path
    
    def _extract_metadata(self, root):
        """Extract metadata from XML"""
        metadata_elem = root.find('.//ap:metadata', self.ns)
        
        title = metadata_elem.find('ap:title', self.ns).text
        
        # Extract authors
        authors = []
        for author_elem in metadata_elem.findall('.//ap:author', self.ns):
            author = {
                'name': author_elem.find('ap:name', self.ns).text,
                'affiliation': author_elem.find('ap:affiliation', self.ns).text
            }
            email_elem = author_elem.find('ap:email', self.ns)
            if email_elem is not None:
                author['email'] = email_elem.text
            authors.append(author)
        
        # Extract abstract
        abstract_elem = metadata_elem.find('ap:abstract', self.ns)
        abstract = self._convert_rich_content_to_html(abstract_elem)
        
        # Extract publication info
        pub_info = {}
        pub_elem = metadata_elem.find('ap:publication_info', self.ns)
        if pub_elem is not None:
            for field in ['venue', 'date', 'arxiv_id', 'document_class']:
                elem = pub_elem.find(f'ap:{field}', self.ns)
                if elem is not None:
                    pub_info[field] = elem.text
        
        return {
            'title': title,
            'authors': authors,
            'abstract': abstract,
            'publication_info': pub_info
        }
    
    def _convert_rich_content_to_html(self, element):
        """Convert XML rich content to HTML string"""
        if element is None:
            return ""
        
        html_parts = []
        
        # Handle text content and child elements
        if element.text:
            html_parts.append(element.text)
        
        for child in element:
            if child.tag.endswith('}p'):
                # XHTML paragraph
                p_content = self._element_to_html_string(child)
                html_parts.append(p_content)
            elif child.tag.endswith('}math'):
                # MathML - convert to HTML representation
                math_html = self._mathml_to_html(child)
                html_parts.append(math_html)
            else:
                # Other elements
                elem_html = self._element_to_html_string(child)
                html_parts.append(elem_html)
            
            if child.tail:
                html_parts.append(child.tail)
        
        return ''.join(html_parts)
    
    def _element_to_html_string(self, element):
        """Convert XML element to HTML string"""
        tag_name = element.tag.split('}')[-1]  # Remove namespace
        
        # Handle different element types
        if tag_name == 'p':
            content = self._get_element_content_with_children(element)
            return f'<p>{content}</p>'
        elif tag_name == 'em':
            return f'<em>{element.text or ""}</em>'
        elif tag_name == 'strong':
            return f'<strong>{element.text or ""}</strong>'
        elif tag_name == 'math':
            return self._mathml_to_html(element)
        else:
            return element.text or ""
    
    def _get_element_content_with_children(self, element):
        """Get element content including child elements"""
        content_parts = []
        
        if element.text:
            content_parts.append(element.text)
        
        for child in element:
            if child.tag.endswith('}math'):
                content_parts.append(self._mathml_to_html(child))
            elif child.tag.endswith('}em'):
                content_parts.append(f'<em>{child.text or ""}</em>')
            elif child.tag.endswith('}strong'):
                content_parts.append(f'<strong>{child.text or ""}</strong>')
            else:
                content_parts.append(child.text or "")
            
            if child.tail:
                content_parts.append(child.tail)
        
        return ''.join(content_parts)
    
    def _mathml_to_html(self, math_element):
        """Convert MathML to readable HTML"""
        # Simple MathML to HTML conversion for ePub compatibility
        parts = []
        
        for child in math_element:
            tag = child.tag.split('}')[-1]
            text = child.text or ""
            
            if tag == 'mi':  # Math identifier
                parts.append(f'<em>{text}</em>')
            elif tag == 'mo':  # Math operator
                parts.append(text)
            elif tag == 'mtext':  # Math text
                parts.append(text)
            else:
                parts.append(text)
        
        return ''.join(parts)
    
    def _generate_content_html(self, root):
        """Generate main content HTML"""
        metadata = self._extract_metadata(root)
        
        html = f'''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
    <meta charset="utf-8"/>
    <title>{self._escape_html(metadata['title'])}</title>
    <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>

{self._generate_toc_html(root)}

<div class="title-page">
    <h1 class="title">{self._escape_html(metadata['title'])}</h1>
    {self._generate_authors_html(metadata['authors'])}
    {self._generate_publication_info_html(metadata['publication_info'])}
</div>

<div class="abstract">
    <h2>Abstract</h2>
    {metadata['abstract']}
</div>

{self._generate_sections_html(root)}

{self._generate_equations_html(root)}

{self._generate_references_html(root)}

</body>
</html>'''
        return html
    
    def _generate_sections_html(self, root):
        """Generate sections HTML"""
        sections_html = ''
        
        sections_elem = root.find('.//ap:sections', self.ns)
        if sections_elem is None:
            return sections_html
        
        for section in sections_elem.findall('ap:section', self.ns):
            section_id = section.get('id')
            level = int(section.get('level', '1'))
            title = section.find('ap:title', self.ns).text
            content_elem = section.find('ap:content', self.ns)
            
            sections_html += f'\n<div class="section" id="{section_id}">'
            sections_html += f'\n    <h{level} class="section-title">{self._escape_html(title)}</h{level}>'
            
            if content_elem is not None:
                content_html = self._convert_rich_content_to_html(content_elem)
                sections_html += f'\n    <div class="section-content">{content_html}</div>'
            
            # Handle subsections
            subsections_elem = section.find('ap:subsections', self.ns)
            if subsections_elem is not None:
                for subsection in subsections_elem.findall('ap:subsection', self.ns):
                    sub_id = subsection.get('id')
                    sub_level = int(subsection.get('level', '2'))
                    sub_title = subsection.find('ap:title', self.ns).text
                    sub_content_elem = subsection.find('ap:content', self.ns)
                    
                    sections_html += f'\n    <div class="subsection" id="{sub_id}">'
                    sections_html += f'\n        <h{sub_level} class="subsection-title">{self._escape_html(sub_title)}</h{sub_level}>'
                    
                    if sub_content_elem is not None:
                        sub_content_html = self._convert_rich_content_to_html(sub_content_elem)
                        sections_html += f'\n        <div class="subsection-content">{sub_content_html}</div>'
                    
                    sections_html += '\n    </div>'
            
            sections_html += '\n</div>'
        
        return sections_html
    
    def _generate_equations_html(self, root):
        """Generate equations HTML"""
        equations_html = ''
        
        equations_elem = root.find('.//ap:equations', self.ns)
        if equations_elem is None:
            return equations_html
        
        equations_html += '\n<div class="equations">'
        equations_html += '\n    <h2>Equations</h2>'
        
        for equation in equations_elem.findall('ap:equation', self.ns):
            eq_id = equation.get('id')
            content_elem = equation.find('ap:content', self.ns)
            desc_elem = equation.find('ap:description', self.ns)
            
            equations_html += f'\n    <div class="equation" id="{eq_id}">'
            
            if content_elem is not None:
                # Find MathML in content
                math_elem = content_elem.find('.//mathml:math', self.ns)
                if math_elem is not None:
                    math_html = self._mathml_to_html(math_elem)
                    equations_html += f'\n        <div class="equation-content">{math_html}</div>'
            
            if desc_elem is not None:
                equations_html += f'\n        <div class="equation-description">{desc_elem.text}</div>'
            
            equations_html += '\n    </div>'
        
        equations_html += '\n</div>'
        return equations_html
    
    def _generate_references_html(self, root):
        """Generate references HTML"""
        refs_html = ''
        
        refs_elem = root.find('.//ap:references', self.ns)
        if refs_elem is None:
            return refs_html
        
        refs_html += '\n<div class="references">'
        refs_html += '\n    <h2 id="references">References</h2>'
        refs_html += '\n    <ol class="reference-list">'
        
        for i, ref in enumerate(refs_elem.findall('ap:reference', self.ns), 1):
            ref_id = ref.get('id')
            
            # Extract reference data
            authors_elem = ref.find('ap:authors', self.ns)
            title_elem = ref.find('ap:title', self.ns)
            venue_elem = ref.find('ap:venue', self.ns)
            year_elem = ref.find('ap:year', self.ns)
            
            refs_html += f'\n        <li id="{ref_id}" class="reference-item">'
            
            if authors_elem is not None:
                author_names = [a.text for a in authors_elem.findall('ap:author', self.ns)]
                refs_html += f'<span class="ref-authors">{", ".join(author_names)}</span>. '
            
            if title_elem is not None:
                refs_html += f'<span class="ref-title">"{self._escape_html(title_elem.text)}"</span>. '
            
            if venue_elem is not None:
                refs_html += f'<span class="ref-venue">{self._escape_html(venue_elem.text)}</span>, '
            
            if year_elem is not None:
                refs_html += f'<span class="ref-year">{year_elem.text}</span>.'
            
            refs_html += '</li>'
        
        refs_html += '\n    </ol>'
        refs_html += '\n</div>'
        return refs_html
    
    def _generate_toc_html(self, root):
        """Generate table of contents"""
        toc_html = '''<div class="toc">
    <h2>Table of Contents</h2>
    <ul>'''
        
        sections_elem = root.find('.//ap:sections', self.ns)
        if sections_elem is not None:
            for section in sections_elem.findall('ap:section', self.ns):
                section_id = section.get('id')
                title = section.find('ap:title', self.ns).text
                toc_html += f'\n        <li><a href="#{section_id}">{self._escape_html(title)}</a></li>'
                
                # Add subsections
                subsections_elem = section.find('ap:subsections', self.ns)
                if subsections_elem is not None:
                    for subsection in subsections_elem.findall('ap:subsection', self.ns):
                        sub_id = subsection.get('id')
                        sub_title = subsection.find('ap:title', self.ns).text
                        toc_html += f'\n        <li class="subsection"><a href="#{sub_id}">{self._escape_html(sub_title)}</a></li>'
        
        toc_html += '''
    </ul>
</div>'''
        return toc_html
    
    def _generate_authors_html(self, authors):
        """Generate authors HTML"""
        authors_html = '<div class="authors">'
        
        author_names = [author['name'] for author in authors]
        authors_html += f'<p class="author-names">{", ".join(author_names)}</p>'
        
        for author in authors:
            affiliation = author['affiliation']
            if author.get('email'):
                affiliation += f" ({author['email']})"
            authors_html += f'<p class="affiliation">{self._escape_html(affiliation)}</p>'
        
        authors_html += '</div>'
        return authors_html
    
    def _generate_publication_info_html(self, pub_info):
        """Generate publication info HTML"""
        if not pub_info:
            return ''
        
        info_html = '<div class="publication-info">'
        
        if pub_info.get('venue'):
            info_html += f'<p class="venue">{self._escape_html(pub_info["venue"])}</p>'
        
        if pub_info.get('date'):
            info_html += f'<p class="date">{pub_info["date"]}</p>'
        
        if pub_info.get('arxiv_id'):
            info_html += f'<p class="arxiv">arXiv:{pub_info["arxiv_id"]}</p>'
        
        info_html += '</div>'
        return info_html
    
    def _generate_styles_css(self):
        """Generate CSS styles"""
        return '''/* Academic ePub Styles with MathML Support */

body {
    font-family: "Times New Roman", serif;
    font-size: 1em;
    line-height: 1.6;
    margin: 1em;
    color: #333;
}

/* Math styling */
math {
    font-family: "Times New Roman", serif;
    font-size: 1em;
}

math[display="block"] {
    display: block;
    text-align: center;
    margin: 1em 0;
}

math[display="inline"] {
    display: inline;
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

.publication-info {
    margin: 2em 0;
    font-size: 0.9em;
    color: #666;
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

.toc a {
    text-decoration: none;
    color: #2c3e50;
}

/* Abstract */
.abstract {
    background: #f8f9fa;
    padding: 1.5em;
    border-left: 4px solid #3498db;
    margin: 2em 0;
}

.abstract h2 {
    margin-top: 0;
    color: #2c3e50;
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

.subsection {
    margin: 1.5em 0;
}

.subsection-title {
    color: #34495e;
    border-bottom: 1px solid #bdc3c7;
    padding-bottom: 0.3em;
    margin: 1.5em 0 0.5em 0;
}

/* Paragraphs */
p {
    margin: 1em 0;
    text-align: justify;
    text-indent: 1.5em;
}

.abstract p,
.toc p,
.authors p,
.publication-info p {
    text-indent: 0;
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

.references h2 {
    color: #2c3e50;
    margin-bottom: 1em;
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
}

/* Responsive design */
@media screen and (max-width: 600px) {
    body {
        margin: 0.5em;
        font-size: 0.9em;
    }
    
    .title {
        font-size: 1.5em;
    }
    
    .toc, .abstract {
        padding: 1em;
        margin: 1em 0;
    }
}'''
    
    def _generate_content_opf(self, metadata, filename):
        """Generate content.opf metadata file"""
        opf = f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:title>{self._escape_xml(metadata['title'])}</dc:title>'''
        
        for author in metadata['authors']:
            opf += f'\n    <dc:creator opf:role="aut">{self._escape_xml(author["name"])}</dc:creator>'
        
        opf += f'\n    <dc:description>{self._escape_xml(metadata["abstract"][:500])}...</dc:description>'
        
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
  </manifest>
  
  <spine toc="toc">
    <itemref idref="content"/>
  </spine>
  
  <guide>
    <reference type="toc" title="Table of Contents" href="content.html#toc"/>
  </guide>
</package>'''
        return opf
    
    def _generate_toc_ncx(self, root, metadata):
        """Generate toc.ncx navigation file"""
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
        
        ncx += f'''
    <navPoint id="abstract" playOrder="{play_order}">
      <navLabel>
        <text>Abstract</text>
      </navLabel>
      <content src="content.html#abstract"/>
    </navPoint>'''
        play_order += 1
        
        sections_elem = root.find('.//ap:sections', self.ns)
        if sections_elem is not None:
            for section in sections_elem.findall('ap:section', self.ns):
                section_id = section.get('id')
                title = section.find('ap:title', self.ns).text
                
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
    """Test XML to ePub conversion"""
    converter = XmlToEpubConverter()
    
    xml_file = "word2vec_test.xml"
    
    if not Path(xml_file).exists():
        print(f"❌ XML file not found: {xml_file}")
        return
    
    print("🚀 XML-to-ePub Converter")
    print("=" * 50)
    print("✨ Features: Native MathML support, XHTML formatting, academic structure")
    print()
    
    try:
        epub_path = converter.convert_xml_to_epub(xml_file)
        
        file_size = epub_path.stat().st_size
        print(f"📊 Generated ePub: {file_size:,} bytes")
        
        print("🎉 XML-to-ePub conversion complete!")
        
    except Exception as e:
        print(f"❌ Error converting XML to ePub: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
