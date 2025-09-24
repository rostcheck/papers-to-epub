#!/usr/bin/env python3
import json
import zipfile
import re
from pathlib import Path
from datetime import datetime

class JsonToEpubGenerator:
    def __init__(self):
        self.output_dir = Path("epub_books")
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_epub(self, json_file):
        """Generate high-quality ePub from structured JSON"""
        
        # Load and validate JSON
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        print(f"📚 Generating ePub from {json_file}")
        
        # Create ePub filename
        title = data['metadata']['title']
        safe_title = re.sub(r'[^\w\s-]', '', title).strip()
        safe_title = re.sub(r'[-\s]+', '_', safe_title)[:50]
        epub_filename = f"Generated_{safe_title}.epub"
        epub_path = self.output_dir / epub_filename
        
        # Generate ePub components
        content_html = self._generate_content_html(data)
        content_opf = self._generate_content_opf(data, epub_filename)
        toc_ncx = self._generate_toc_ncx(data)
        styles_css = self._generate_styles_css()
        
        # Assemble ePub
        with zipfile.ZipFile(epub_path, 'w', zipfile.ZIP_DEFLATED) as epub:
            # Add mimetype (must be first, uncompressed)
            epub.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
            
            # Add META-INF
            epub.writestr('META-INF/container.xml', self._generate_container_xml())
            
            # Add content files
            epub.writestr('content.html', content_html)
            epub.writestr('content.opf', content_opf)
            epub.writestr('toc.ncx', toc_ncx)
            epub.writestr('styles.css', styles_css)
        
        print(f"✅ Generated: {epub_path}")
        return epub_path
    
    def _generate_content_html(self, data):
        """Generate main HTML content"""
        metadata = data['metadata']
        sections = data['sections']
        tables = data.get('tables', [])
        figures = data.get('figures', [])
        equations = data.get('equations', [])
        
        html = f'''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
    <meta charset="utf-8"/>
    <title>{self._escape_html(metadata['title'])}</title>
    <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>

{self._generate_toc_html(sections)}

<div class="title-page">
    <h1 class="title">{self._escape_html(metadata['title'])}</h1>
    {self._generate_authors_html(metadata['authors'])}
    {self._generate_publication_info_html(metadata.get('publication_info', {}))}
</div>

<div class="abstract">
    <h2>Abstract</h2>
    <p>{self._escape_html(metadata['abstract'])}</p>
</div>

{self._generate_sections_html(sections, tables, figures, equations)}

{self._generate_references_html(data.get('references', []))}

</body>
</html>'''
        return html
    
    def _generate_toc_html(self, sections):
        """Generate table of contents HTML"""
        toc_html = '''<div class="toc">
    <h2>Table of Contents</h2>
    <ul>'''
        
        for section in sections:
            toc_html += f'\n        <li><a href="#{section["id"]}">{self._escape_html(section["title"])}</a></li>'
            
            # Add subsections
            for subsection in section.get('subsections', []):
                toc_html += f'\n        <li class="subsection"><a href="#{subsection["id"]}">{self._escape_html(subsection["title"])}</a></li>'
        
        toc_html += '''
    </ul>
</div>'''
        return toc_html
    
    def _generate_authors_html(self, authors):
        """Generate authors section"""
        authors_html = '<div class="authors">'
        
        author_names = []
        affiliations = []
        
        for author in authors:
            name = author['name']
            if author.get('corresponding'):
                name += '*'
            author_names.append(name)
            
            affiliation = author['affiliation']
            if author.get('email'):
                affiliation += f" ({author['email']})"
            if affiliation not in affiliations:
                affiliations.append(affiliation)
        
        authors_html += f'<p class="author-names">{", ".join(author_names)}</p>'
        
        for affiliation in affiliations:
            authors_html += f'<p class="affiliation">{self._escape_html(affiliation)}</p>'
        
        authors_html += '</div>'
        return authors_html
    
    def _generate_publication_info_html(self, pub_info):
        """Generate publication information"""
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
    
    def _generate_sections_html(self, sections, tables, figures, equations):
        """Generate sections with embedded tables, figures, and equations"""
        sections_html = ''
        
        for section in sections:
            # Main section
            sections_html += f'\n<div class="section" id="{section["id"]}">'
            sections_html += f'\n    <h{section["level"]} class="section-title">{self._escape_html(section["title"])}</h{section["level"]}>'
            
            # Section content with embedded elements
            content = self._embed_elements_in_content(section['content'], section['id'], tables, figures, equations)
            sections_html += f'\n    <div class="section-content">{content}</div>'
            
            # Subsections
            for subsection in section.get('subsections', []):
                sections_html += f'\n    <div class="subsection" id="{subsection["id"]}">'
                sections_html += f'\n        <h{subsection["level"]} class="subsection-title">{self._escape_html(subsection["title"])}</h{subsection["level"]}>'
                
                subcontent = self._embed_elements_in_content(subsection['content'], subsection['id'], tables, figures, equations)
                sections_html += f'\n        <div class="subsection-content">{subcontent}</div>'
                sections_html += '\n    </div>'
            
            sections_html += '\n</div>'
        
        return sections_html
    
    def _embed_elements_in_content(self, content, section_id, tables, figures, equations):
        """Embed tables, figures, and equations in content"""
        # Convert content to paragraphs
        paragraphs = content.split('\n\n')
        result_html = ''
        
        for para in paragraphs:
            if para.strip():
                result_html += f'<p>{self._escape_html(para.strip())}</p>\n'
        
        # Add tables that belong after this section
        for table in tables:
            if table.get('position', '').startswith(f'after_section_{section_id}'):
                result_html += self._generate_table_html(table)
        
        # Add figures that belong after this section
        for figure in figures:
            if figure.get('position', '').startswith(f'after_section_{section_id}'):
                result_html += self._generate_figure_html(figure)
        
        return result_html
    
    def _generate_table_html(self, table):
        """Generate HTML table"""
        table_html = f'\n<div class="table-container">'
        table_html += f'\n<table id="{table["id"]}" class="{table.get("styling", "")}">'
        
        if table.get('caption'):
            table_html += f'\n    <caption><strong>Table {table["id"][5:]}.</strong> {self._escape_html(table["caption"])}</caption>'
        
        # Headers
        table_html += '\n    <thead>\n        <tr>'
        for header in table['headers']:
            table_html += f'\n            <th>{self._escape_html(header)}</th>'
        table_html += '\n        </tr>\n    </thead>'
        
        # Rows
        table_html += '\n    <tbody>'
        for row in table['rows']:
            table_html += '\n        <tr>'
            for cell in row:
                table_html += f'\n            <td>{self._escape_html(cell)}</td>'
            table_html += '\n        </tr>'
        table_html += '\n    </tbody>'
        
        table_html += '\n</table>\n</div>\n'
        return table_html
    
    def _generate_figure_html(self, figure):
        """Generate HTML figure placeholder"""
        figure_html = f'\n<div class="figure-container">'
        figure_html += f'\n<figure id="{figure["id"]}">'
        
        if figure.get('image_data'):
            figure_html += f'\n    <img src="{figure["image_data"]}" alt="{self._escape_html(figure.get("alt_text", ""))}" class="figure-image"/>'
        else:
            figure_html += f'\n    <div class="figure-placeholder">[Figure: {self._escape_html(figure.get("description", "Image not available"))}]</div>'
        
        if figure.get('caption'):
            figure_html += f'\n    <figcaption><strong>Figure {figure["id"][6:]}.</strong> {self._escape_html(figure["caption"])}</figcaption>'
        
        figure_html += '\n</figure>\n</div>\n'
        return figure_html
    
    def _generate_references_html(self, references):
        """Generate references section"""
        if not references:
            return ''
        
        refs_html = '\n<div class="references">'
        refs_html += '\n    <h2 id="references">References</h2>'
        refs_html += '\n    <ol class="reference-list">'
        
        for ref in references:
            refs_html += f'\n        <li id="{ref["id"]}">'
            
            # Authors
            authors = ', '.join(ref['authors'])
            refs_html += f'{self._escape_html(authors)}. '
            
            # Title
            refs_html += f'"{self._escape_html(ref["title"])}". '
            
            # Venue and year
            if ref.get('venue'):
                refs_html += f'{self._escape_html(ref["venue"])}, '
            refs_html += f'{ref["year"]}.'
            
            # URL if available
            if ref.get('url'):
                refs_html += f' <a href="{ref["url"]}" target="_blank">Link</a>'
            
            refs_html += '</li>'
        
        refs_html += '\n    </ol>'
        refs_html += '\n</div>'
        return refs_html
    
    def _generate_content_opf(self, data, filename):
        """Generate content.opf metadata file"""
        metadata = data['metadata']
        
        opf = f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:title>{self._escape_xml(metadata['title'])}</dc:title>'''
        
        # Authors
        for author in metadata['authors']:
            opf += f'\n    <dc:creator opf:role="aut">{self._escape_xml(author["name"])}</dc:creator>'
        
        # Other metadata
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
    
    def _generate_toc_ncx(self, data):
        """Generate toc.ncx navigation file"""
        metadata = data['metadata']
        sections = data['sections']
        
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
        
        # Add abstract
        ncx += f'''
    <navPoint id="abstract" playOrder="{play_order}">
      <navLabel>
        <text>Abstract</text>
      </navLabel>
      <content src="content.html#abstract"/>
    </navPoint>'''
        play_order += 1
        
        # Add sections
        for section in sections:
            ncx += f'''
    <navPoint id="{section['id']}" playOrder="{play_order}">
      <navLabel>
        <text>{self._escape_xml(section['title'])}</text>
      </navLabel>
      <content src="content.html#{section['id']}"/>
    </navPoint>'''
            play_order += 1
            
            # Add subsections
            for subsection in section.get('subsections', []):
                ncx += f'''
    <navPoint id="{subsection['id']}" playOrder="{play_order}">
      <navLabel>
        <text>{self._escape_xml(subsection['title'])}</text>
      </navLabel>
      <content src="content.html#{subsection['id']}"/>
    </navPoint>'''
                play_order += 1
        
        # Add references if they exist
        if data.get('references'):
            ncx += f'''
    <navPoint id="references" playOrder="{play_order}">
      <navLabel>
        <text>References</text>
      </navLabel>
      <content src="content.html#references"/>
    </navPoint>'''
        
        ncx += '''
  </navMap>
</ncx>'''
        return ncx
    
    def _generate_styles_css(self):
        """Generate professional academic CSS"""
        return '''/* Professional Academic ePub Styles */

body {
    font-family: "Times New Roman", serif;
    font-size: 1em;
    line-height: 1.6;
    margin: 1em;
    color: #333;
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
    font-style: italic;
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

/* Tables */
.table-container {
    margin: 2em 0;
    overflow-x: auto;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 1em 0;
    font-size: 0.9em;
    border: 1px solid #ddd;
}

table caption {
    text-align: left;
    margin-bottom: 1em;
    font-weight: bold;
    color: #2c3e50;
}

th, td {
    padding: 0.75em 0.5em;
    text-align: left;
    border: 1px solid #ddd;
    vertical-align: top;
}

th {
    background-color: #f8f9fa;
    font-weight: bold;
    color: #2c3e50;
    text-align: center;
}

tbody tr:nth-child(even) {
    background-color: #f8f9fa;
}

/* Table styling variants */
.comparison-table th:first-child,
.comparison-table td:first-child {
    font-weight: bold;
}

.results-table td:nth-child(n+2) {
    text-align: center;
    font-family: monospace;
}

/* Figures */
.figure-container {
    margin: 2em 0;
    text-align: center;
}

.figure-placeholder {
    background: #f8f9fa;
    border: 2px dashed #dee2e6;
    padding: 2em;
    margin: 1em 0;
    color: #666;
    font-style: italic;
}

figcaption {
    margin-top: 1em;
    font-size: 0.9em;
    color: #666;
    text-align: left;
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

.reference-list li {
    margin: 1em 0;
    text-align: justify;
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
    
    table {
        font-size: 0.8em;
    }
    
    th, td {
        padding: 0.5em 0.25em;
    }
}'''
    
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
    """Test the JSON to ePub generator"""
    generator = JsonToEpubGenerator()
    
    json_file = "word2vec_structured.json"
    
    if not Path(json_file).exists():
        print(f"❌ JSON file not found: {json_file}")
        return
    
    print("🚀 JSON-to-ePub Generator")
    print("=" * 50)
    
    try:
        epub_path = generator.generate_epub(json_file)
        
        # Quick quality check
        file_size = epub_path.stat().st_size
        print(f"📊 Generated ePub: {file_size:,} bytes")
        
        # Test with quality analyzer if available
        try:
            from approaches.quality_analysis.epub_quality_analyzer import EpubQualityAnalyzer
            analyzer = EpubQualityAnalyzer(epub_path)
            issues = analyzer.analyze()
            print(f"🔍 Quality check: {len(issues)} issues")
            if issues:
                for issue in issues[:3]:
                    print(f"  - {issue}")
            else:
                print("🎉 Perfect quality!")
        except ImportError:
            print("📝 Quality analyzer not available")
        
    except Exception as e:
        print(f"❌ Error generating ePub: {e}")

if __name__ == "__main__":
    main()
