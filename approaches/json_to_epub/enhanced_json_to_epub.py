#!/usr/bin/env python3
import json
import zipfile
import re
from pathlib import Path

class EnhancedJsonToEpubGenerator:
    def __init__(self):
        self.output_dir = Path("epub_books")
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_epub(self, json_file):
        """Generate enhanced ePub with footnotes, linked references, and proper paragraphs"""
        
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        print(f"📚 Generating enhanced ePub from {json_file}")
        
        # Create ePub filename
        title = data['metadata']['title']
        safe_title = re.sub(r'[^\w\s-]', '', title).strip()
        safe_title = re.sub(r'[-\s]+', '_', safe_title)[:50]
        epub_filename = f"Enhanced_{safe_title}.epub"
        epub_path = self.output_dir / epub_filename
        
        # Generate ePub components
        content_html = self._generate_enhanced_content_html(data)
        content_opf = self._generate_content_opf(data, epub_filename)
        toc_ncx = self._generate_toc_ncx(data)
        styles_css = self._generate_enhanced_styles_css()
        
        # Assemble ePub
        with zipfile.ZipFile(epub_path, 'w', zipfile.ZIP_DEFLATED) as epub:
            epub.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
            epub.writestr('META-INF/container.xml', self._generate_container_xml())
            epub.writestr('content.html', content_html)
            epub.writestr('content.opf', content_opf)
            epub.writestr('toc.ncx', toc_ncx)
            epub.writestr('styles.css', styles_css)
        
        print(f"✅ Generated enhanced ePub: {epub_path}")
        return epub_path
    
    def _generate_enhanced_content_html(self, data):
        """Generate HTML with enhanced features"""
        metadata = data['metadata']
        sections = data['sections']
        tables = data.get('tables', [])
        figures = data.get('figures', [])
        references = data.get('references', [])
        
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
    {self._process_text_with_citations(metadata['abstract'], references)}
</div>

{self._generate_enhanced_sections_html(sections, tables, figures, references)}

{self._generate_enhanced_references_html(references)}

{self._generate_footnotes_html()}

</body>
</html>'''
        return html
    
    def _process_text_with_citations(self, text, references):
        """Process text to add proper paragraphs and link citations"""
        if not text:
            return ''
        
        # Split into paragraphs (double newlines or sentence boundaries)
        paragraphs = self._split_into_paragraphs(text)
        
        html = ''
        for para in paragraphs:
            if para.strip():
                # Process citations in paragraph - but don't escape HTML tags that are already there
                processed_para = self._link_citations(para.strip(), references)
                html += f'<p>{processed_para}</p>\n'
        
        return html
    
    def _split_into_paragraphs(self, text):
        """Intelligently split text into paragraphs"""
        # First try explicit double newlines
        if '\n\n' in text:
            return text.split('\n\n')
        
        # Otherwise split on sentence boundaries followed by capital letters
        # This handles cases where paragraphs aren't explicitly marked
        sentences = re.split(r'(\. [A-Z])', text)
        
        paragraphs = []
        current_para = ''
        
        for i, part in enumerate(sentences):
            if part.startswith('. ') and i > 0:
                # End current paragraph and start new one
                current_para += '.'
                if current_para.strip():
                    paragraphs.append(current_para.strip())
                current_para = part[2:]  # Remove '. ' and start new paragraph
            else:
                current_para += part
        
        # Add final paragraph
        if current_para.strip():
            paragraphs.append(current_para.strip())
        
        return paragraphs
    
    def _link_citations(self, text, references):
        """Convert citation markers to clickable links"""
        # First escape HTML in the text, but preserve existing HTML tags from LaTeX conversion
        escaped_text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # But restore the HTML tags we want to keep
        escaped_text = escaped_text.replace('&lt;em&gt;', '<em>').replace('&lt;/em&gt;', '</em>')
        escaped_text = escaped_text.replace('&lt;strong&gt;', '<strong>').replace('&lt;/strong&gt;', '</strong>')
        escaped_text = escaped_text.replace('&lt;a href=', '<a href=').replace('"&gt;', '">')
        escaped_text = escaped_text.replace('&lt;/a&gt;', '</a>')
        
        # Pattern for citations like [1], [2], [Smith et al.]
        citation_pattern = r'\[([^\]]+)\]'
        
        def replace_citation(match):
            citation_text = match.group(1)
            
            # Skip if this looks like a reference marker we want to keep
            if citation_text in ['citation', 'ref']:
                return f'[{citation_text}]'
            
            # Try to find matching reference
            ref_id = self._find_reference_id(citation_text, references)
            
            if ref_id:
                return f'<a href="#{ref_id}" class="citation">[{citation_text}]</a>'
            else:
                # Keep as-is if no matching reference found
                return f'[{citation_text}]'
        
        return re.sub(citation_pattern, replace_citation, escaped_text)
    
    def _find_reference_id(self, citation_text, references):
        """Find reference ID for citation text"""
        # Simple numeric citations
        if citation_text.isdigit():
            ref_num = int(citation_text)
            if 1 <= ref_num <= len(references):
                return f"ref{ref_num}"
        
        # Author-based citations
        for i, ref in enumerate(references, 1):
            if any(author.split(',')[0].lower() in citation_text.lower() 
                   for author in ref.get('authors', [])):
                return f"ref{i}"
        
        return None
    
    def _generate_enhanced_sections_html(self, sections, tables, figures, references):
        """Generate sections with enhanced text processing"""
        sections_html = ''
        
        for section in sections:
            sections_html += f'\n<div class="section" id="{section["id"]}">'
            sections_html += f'\n    <h{section["level"]} class="section-title">{self._escape_html(section["title"])}</h{section["level"]}>'
            
            # Process section content with citations and paragraphs
            content_html = self._process_text_with_citations(section['content'], references)
            sections_html += f'\n    <div class="section-content">{content_html}</div>'
            
            # Add tables and figures for this section
            sections_html += self._embed_elements_for_section(section['id'], tables, figures)
            
            # Process subsections
            for subsection in section.get('subsections', []):
                sections_html += f'\n    <div class="subsection" id="{subsection["id"]}">'
                sections_html += f'\n        <h{subsection["level"]} class="subsection-title">{self._escape_html(subsection["title"])}</h{subsection["level"]}>'
                
                subcontent_html = self._process_text_with_citations(subsection['content'], references)
                sections_html += f'\n        <div class="subsection-content">{subcontent_html}</div>'
                
                # Add elements for subsection
                sections_html += self._embed_elements_for_section(subsection['id'], tables, figures)
                sections_html += '\n    </div>'
            
            sections_html += '\n</div>'
        
        return sections_html
    
    def _embed_elements_for_section(self, section_id, tables, figures):
        """Embed tables and figures for a specific section"""
        elements_html = ''
        
        # Add tables
        for table in tables:
            if table.get('position', '').endswith(f'_{section_id}'):
                elements_html += self._generate_table_html(table)
        
        # Add figures
        for figure in figures:
            if figure.get('position', '').endswith(f'_{section_id}'):
                elements_html += self._generate_figure_html(figure)
        
        return elements_html
    
    def _generate_enhanced_references_html(self, references):
        """Generate enhanced references with proper IDs"""
        if not references:
            return ''
        
        refs_html = '\n<div class="references">'
        refs_html += '\n    <h2 id="references">References</h2>'
        refs_html += '\n    <ol class="reference-list">'
        
        for i, ref in enumerate(references, 1):
            refs_html += f'\n        <li id="ref{i}" class="reference-item">'
            
            # Authors
            authors = ', '.join(ref['authors'])
            refs_html += f'<span class="ref-authors">{self._escape_html(authors)}</span>. '
            
            # Title
            refs_html += f'<span class="ref-title">"{self._escape_html(ref["title"])}"</span>. '
            
            # Venue and year
            if ref.get('venue'):
                refs_html += f'<span class="ref-venue">{self._escape_html(ref["venue"])}</span>, '
            refs_html += f'<span class="ref-year">{ref["year"]}</span>.'
            
            # URL if available
            if ref.get('url'):
                refs_html += f' <a href="{ref["url"]}" target="_blank" class="ref-link">Link</a>'
            
            refs_html += '</li>'
        
        refs_html += '\n    </ol>'
        refs_html += '\n</div>'
        return refs_html
    
    def _generate_footnotes_html(self):
        """Generate footnotes section (placeholder for future enhancement)"""
        # This would be populated if footnotes were extracted from source
        return '\n<!-- Footnotes would appear here if present in source -->'
    
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
        """Generate HTML figure with proper image handling"""
        figure_html = f'\n<div class="figure-container">'
        figure_html += f'\n<figure id="{figure["id"]}">'
        
        if figure.get('image_data'):
            # Handle different image formats
            image_path = figure['image_data']
            if isinstance(image_path, str) and Path(image_path).exists():
                # Read and encode image as base64 for embedding
                try:
                    import base64
                    with open(image_path, 'rb') as img_file:
                        img_data = base64.b64encode(img_file.read()).decode('utf-8')
                        
                    # Determine MIME type
                    if image_path.lower().endswith('.png'):
                        mime_type = 'image/png'
                    elif image_path.lower().endswith('.jpg') or image_path.lower().endswith('.jpeg'):
                        mime_type = 'image/jpeg'
                    elif image_path.lower().endswith('.pdf'):
                        # PDF not supported in ePub images, show placeholder
                        figure_html += f'\n    <div class="figure-placeholder">[PDF Figure: {self._escape_html(figure.get("description", "PDF image not displayable in ePub"))}]</div>'
                        mime_type = None
                    else:
                        mime_type = 'image/png'  # Default
                    
                    if mime_type:
                        figure_html += f'\n    <img src="data:{mime_type};base64,{img_data}" alt="{self._escape_html(figure.get("alt_text", ""))}" class="figure-image"/>'
                        
                except Exception as e:
                    print(f"⚠️ Error embedding image {image_path}: {e}")
                    figure_html += f'\n    <div class="figure-placeholder">[Image: {self._escape_html(figure.get("description", "Image not available"))}]</div>'
            else:
                figure_html += f'\n    <div class="figure-placeholder">[Image: {self._escape_html(figure.get("description", "Image file not found"))}]</div>'
        else:
            figure_html += f'\n    <div class="figure-placeholder">[Figure: {self._escape_html(figure.get("description", "Image not available"))}]</div>'
        
        if figure.get('caption'):
            figure_html += f'\n    <figcaption><strong>Figure {figure["id"][6:]}.</strong> {self._escape_html(figure["caption"])}</figcaption>'
        
        figure_html += '\n</figure>\n</div>\n'
        return figure_html
    
    def _generate_toc_html(self, sections):
        """Generate table of contents"""
        toc_html = '''<div class="toc">
    <h2>Table of Contents</h2>
    <ul>'''
        
        for section in sections:
            toc_html += f'\n        <li><a href="#{section["id"]}">{self._escape_html(section["title"])}</a></li>'
            
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
    
    def _generate_enhanced_styles_css(self):
        """Generate enhanced CSS with citation and reference styling"""
        return '''/* Enhanced Academic ePub Styles */

body {
    font-family: "Times New Roman", serif;
    font-size: 1em;
    line-height: 1.6;
    margin: 1em;
    color: #333;
}

/* Citations */
.citation {
    color: #2c3e50;
    text-decoration: none;
    font-weight: bold;
    border-bottom: 1px dotted #3498db;
}

.citation:hover {
    background-color: #f8f9fa;
    border-bottom: 1px solid #3498db;
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

.ref-link {
    color: #3498db;
    text-decoration: none;
    font-size: 0.9em;
}

.ref-link:hover {
    text-decoration: underline;
}

/* Improved paragraph spacing */
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

/* Section content paragraphs */
.section-content p,
.subsection-content p {
    margin: 1.2em 0;
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
    
    def _generate_content_opf(self, data, filename):
        """Generate content.opf metadata file"""
        metadata = data['metadata']
        
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
        
        ncx += f'''
    <navPoint id="abstract" playOrder="{play_order}">
      <navLabel>
        <text>Abstract</text>
      </navLabel>
      <content src="content.html#abstract"/>
    </navPoint>'''
        play_order += 1
        
        for section in sections:
            ncx += f'''
    <navPoint id="{section['id']}" playOrder="{play_order}">
      <navLabel>
        <text>{self._escape_xml(section['title'])}</text>
      </navLabel>
      <content src="content.html#{section['id']}"/>
    </navPoint>'''
            play_order += 1
            
            for subsection in section.get('subsections', []):
                ncx += f'''
    <navPoint id="{subsection['id']}" playOrder="{play_order}">
      <navLabel>
        <text>{self._escape_xml(subsection['title'])}</text>
      </navLabel>
      <content src="content.html#{subsection['id']}"/>
    </navPoint>'''
                play_order += 1
        
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
    """Test the enhanced JSON to ePub generator"""
    generator = EnhancedJsonToEpubGenerator()
    
    json_file = "../../word2vec_complete.json"
    
    if not Path(json_file).exists():
        print(f"❌ JSON file not found: {json_file}")
        return
    
    print("🚀 Enhanced JSON-to-ePub Generator")
    print("=" * 50)
    print("✨ Features: Linked citations, proper paragraphs, enhanced references")
    print()
    
    try:
        epub_path = generator.generate_epub(json_file)
        
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
