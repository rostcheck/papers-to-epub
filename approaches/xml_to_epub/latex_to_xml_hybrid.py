#!/usr/bin/env python3
"""
Hybrid LaTeX to XML Converter
Architecture: TexSoup (structure) + pylatexenc (content) + LLM (unstructured) + MathML
"""

import re
import json
import boto3
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

from TexSoup import TexSoup
from pylatexenc.latex2text import LatexNodes2Text
import latex2mathml.converter

# Import existing quality assessment component
sys.path.append(str(Path(__file__).parent / "structural_review"))
from review_structure import StructuralReviewer

class StructuralExtractor:
    """Phase 1: Extract document structure using TexSoup"""
    
    def __init__(self, latex_content: str):
        self.soup = TexSoup(latex_content)
        self.latex_content = latex_content
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    def extract_metadata(self) -> Dict[str, str]:
        """Extract title, authors, abstract using LLM for complex parsing"""
        metadata = {}
        
        # Title - try TexSoup first
        title = self.soup.find('title')
        if title and title.string:
            metadata['title'] = str(title.string).strip()
        
        # Authors - use LLM for cognitive extraction
        metadata['authors'] = self._extract_authors_with_llm()
        
        # Abstract
        abstract = self.soup.find('abstract')
        if abstract:
            metadata['abstract'] = str(abstract).strip()
        
        return metadata
    
    def _extract_authors_with_llm(self) -> List[Dict[str, str]]:
        """Extract authors using pylatexenc + Bedrock LLM"""
        from pylatexenc.latexwalker import LatexWalker
        
        try:
            # Use pylatexenc to properly parse LaTeX and find \author commands
            walker = LatexWalker(self.latex_content)
            nodes = walker.get_latex_nodes()[0]
            
            # Find \author macro
            author_block = None
            for node in nodes:
                if hasattr(node, 'macroname') and node.macroname == 'author':
                    if node.nodeargd and node.nodeargd.argnlist:
                        # Get the argument content
                        author_block = node.nodeargd.argnlist[0].latex_verbatim()
                        break
            
            if not author_block:
                return []
            
            prompt = f"""Extract ALL author information from this LaTeX author block. Pay attention to LaTeX separators like \\And and \\AND which separate different authors.

AUTHOR BLOCK:
{author_block}

IMPORTANT: 
- \\And and \\AND separate different authors
- \\\\ separates lines within the same author's information
- Extract ALL authors, not just the first one
- Each author should be a separate object in the array

Return a JSON array with ALL author objects:
[
  {{
    "name": "Author Name",
    "affiliation": "Institution",
    "email": "email@domain.com"
  }},
  {{
    "name": "Second Author Name", 
    "affiliation": "Institution",
    "email": "email2@domain.com"
  }}
]

Return ONLY the JSON array. Make sure to extract ALL authors mentioned."""
            
            response = self.bedrock.converse(
                modelId="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                inferenceConfig={"maxTokens": 1500, "temperature": 0.1}
            )
            
            llm_response = response['output']['message']['content'][0]['text']
            json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
            if json_match:
                authors = json.loads(json_match.group(0))
                print(f"   ✅ Extracted {len(authors)} authors")
                return authors
                
        except Exception as e:
            print(f"   ⚠️ Author extraction failed: {e}")
        
        return []
    
    def extract_sections(self) -> List[Dict[str, str]]:
        """Extract sections and their complete content"""
        sections = []
        
        # Use regex to find section boundaries and extract content between them
        section_pattern = r'\\((?:sub)*section)\*?\{([^}]+)\}'
        matches = list(re.finditer(section_pattern, self.latex_content))
        
        for i, match in enumerate(matches):
            section_type = match.group(1)  # 'section' or 'subsection'
            section_title = match.group(2).strip()
            section_start = match.end()
            
            # Find the end of this section (next section or end of document)
            if i + 1 < len(matches):
                section_end = matches[i + 1].start()
            else:
                # Check for bibliography or end of document
                bib_match = re.search(r'\\begin\{thebibliography\}', self.latex_content[section_start:])
                if bib_match:
                    section_end = section_start + bib_match.start()
                else:
                    section_end = len(self.latex_content)
            
            # Extract content between section start and end
            content = self.latex_content[section_start:section_end].strip()
            
            sections.append({
                'id': f"section_{i+1}",
                'type': section_type,
                'title': section_title,
                'content': content
            })
        
        return sections
    
    def extract_bibliography_block(self) -> Optional[str]:
        """Extract raw bibliography block for LLM processing"""
        bib_match = re.search(r'\\begin\{thebibliography\}.*?\\end\{thebibliography\}', 
                             self.latex_content, re.DOTALL)
        return bib_match.group(0) if bib_match else None
    
    def extract_equations(self) -> List[Dict[str, str]]:
        """Extract equation environments and clean LaTeX content"""
        equations = []
        
        # Find equation environments
        equation_patterns = [
            r'\\begin\{equation\}(.*?)\\end\{equation\}',
            r'\\begin\{align\}(.*?)\\end\{align\}',
            r'\\begin\{eqnarray\}(.*?)\\end\{eqnarray\}',
            r'\$\$(.*?)\$\$'  # Display math
        ]
        
        equation_count = 0
        for pattern in equation_patterns:
            matches = re.finditer(pattern, self.latex_content, re.DOTALL)
            for match in matches:
                equation_count += 1
                latex_content = match.group(1).strip()
                
                # Clean LaTeX content - remove label commands and other non-math content
                clean_latex = re.sub(r'\\label\{[^}]*\}', '', latex_content)
                clean_latex = clean_latex.strip()
                
                equations.append({
                    'id': f"eq_{equation_count}",
                    'latex': clean_latex,
                    'full_match': match.group(0)  # For replacement in sections
                })
        
        return equations
    
    def extract_citations(self) -> List[Dict[str, str]]:
        """Extract citation commands using pylatexenc LatexWalker"""
        from pylatexenc.latexwalker import LatexWalker, LatexMacroNode
        
        citations = []
        citation_count = 0
        
        def traverse_nodes(nodes):
            nonlocal citation_count
            for node in nodes:
                if isinstance(node, LatexMacroNode) and node.macroname == 'cite':
                    citation_count += 1
                    
                    # Extract citation keys from arguments
                    keys = []
                    if node.nodeargs:
                        for arg in node.nodeargs:
                            if hasattr(arg, 'nodelist'):
                                key_text = ''.join(n.chars for n in arg.nodelist if hasattr(n, 'chars'))
                                keys.extend([k.strip() for k in key_text.split(',')])
                    
                    citations.append({
                        'id': f"cite_{citation_count}",
                        'keys': keys,
                        'full_match': node.latex_verbatim()
                    })
                
                # Recursively traverse child nodes
                if hasattr(node, 'nodelist') and node.nodelist:
                    traverse_nodes(node.nodelist)
                if hasattr(node, 'nodeargs') and node.nodeargs:
                    for arg in node.nodeargs:
                        if hasattr(arg, 'nodelist'):
                            traverse_nodes(arg.nodelist)
        
        try:
            walker = LatexWalker(self.latex_content)
            nodes, pos, len_ = walker.get_latex_nodes()
            traverse_nodes(nodes)
        except Exception as e:
            print(f"   ⚠️ Citation extraction failed: {e}")
        
        return citations
    
    def extract_structured_elements(self) -> Dict[str, List]:
        """Extract tables, figures, inline math, and citations"""
        return {
            'tables': self._parse_latex_tables(),
            'figures': [{'id': f"figure_{i+1}", 'content': str(fig)} 
                       for i, fig in enumerate(self.soup.find_all('figure'))],
            'inline_math': self._extract_inline_math(),
            'citations': self._extract_citations()
        }
    
    def _parse_latex_tables(self) -> List[Dict]:
        """Parse LaTeX tables using TexSoup API + string splitting"""
        from pylatexenc.latex2text import LatexNodes2Text
        
        tables = []
        
        for i, table in enumerate(self.soup.find_all('table')):
            table_content = str(table)
            
            # Extract caption using TexSoup API - clean with latex2text
            caption = f"Table {i+1}"
            if table.caption:
                raw_caption = table.caption.string
                if raw_caption:
                    # Clean LaTeX formatting but let XSLT handle italic styling
                    l2t = LatexNodes2Text()
                    caption = l2t.latex_to_text(raw_caption).strip()
            
            # Extract tabular content using TexSoup API
            headers = []
            rows = []
            tabular = table.find('tabular')
            
            if tabular and tabular.contents:
                current_row = []
                
                for item in tabular.contents:
                    item_str = str(item).strip()
                    
                    # Skip column specification (first item, contains |l|c| etc)
                    if '|' in item_str and all(c in 'lcrp|' for c in item_str.replace('|', '')):
                        continue
                    
                    # Skip hline commands
                    if item_str.startswith('\\hline'):
                        continue
                    
                    if item_str == r'\\':
                        # End of row
                        if current_row:
                            if not headers:
                                headers = current_row
                            else:
                                rows.append(current_row)
                            current_row = []
                    else:
                        # Skip commented rows
                        if item_str.startswith('%'):
                            continue
                            
                        # Handle multicolumn commands
                        if '\\multicolumn' in item_str:
                            # Extract: \multicolumn{span}{align}{content}
                            import re
                            match = re.search(r'\\multicolumn\{(\d+)\}\{[^}]*\}\{([^}]*)\}', item_str)
                            if match:
                                colspan = int(match.group(1))
                                content = match.group(2).strip()
                                # Clean content with latex2text
                                l2t = LatexNodes2Text()
                                clean_content = l2t.latex_to_text(content).strip()
                                current_row.append({'content': clean_content, 'colspan': colspan})
                            continue
                        
                        # Regular cell content - split by &
                        if item_str and not item_str.startswith('\\'):
                            cells = [cell.strip() for cell in item_str.split('&')]
                            for cell in cells:
                                if cell:
                                    # Clean each cell with latex2text
                                    l2t = LatexNodes2Text()
                                    clean_cell = l2t.latex_to_text(cell).strip()
                                    if clean_cell:
                                        current_row.append({'content': clean_cell, 'colspan': 1})
                
                # Add last row if any
                if current_row:
                    if not headers:
                        headers = current_row
                    else:
                        rows.append(current_row)
            
            tables.append({
                'id': f"table_{i+1}",
                'caption': caption,
                'headers': headers,
                'rows': rows,
                'content': table_content
            })
        
        return tables
    
    def _extract_inline_math(self) -> List[Dict[str, str]]:
        """Extract inline math expressions $...$"""
        inline_math = []
        # Find inline math patterns
        patterns = [r'\$([^$]+)\$', r'\\([^)]+\\)']
        
        math_count = 0
        for pattern in patterns:
            matches = re.finditer(pattern, self.latex_content)
            for match in matches:
                math_count += 1
                inline_math.append({
                    'id': f"math_{math_count}",
                    'content': match.group(1).strip()
                })
        
        return inline_math
    
    def _extract_citations(self) -> List[Dict[str, str]]:
        """Extract citation commands \\cite{...}"""
        citations = []
        cite_pattern = r'\\cite(?:\[[^\]]*\])?\{([^}]+)\}'
        matches = re.finditer(cite_pattern, self.latex_content)
        
        cite_count = 0
        for match in matches:
            cite_count += 1
            ref_keys = match.group(1).split(',')
            for key in ref_keys:
                citations.append({
                    'id': f"cite_{cite_count}",
                    'ref_key': key.strip()
                })
        
        return citations

class ContentCleaner:
    """Phase 2: Clean LaTeX content and replace equations with references"""
    
    def __init__(self):
        self.cleaner = LatexNodes2Text()
    
    def clean_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Clean LaTeX commands from metadata"""
        cleaned = {}
        for key, value in metadata.items():
            if key == 'authors':
                # Authors is already processed by LLM, keep as-is
                cleaned[key] = value
            elif value and isinstance(value, str):
                cleaned[key] = self.cleaner.latex_to_text(value)
            else:
                cleaned[key] = value
        return cleaned
    
    def clean_sections_with_inline_equations(self, sections: List[Dict[str, str]], equations: List[Dict[str, str]], citations: List[Dict[str, str]], references: List[Dict[str, str]], tables: List[Dict]) -> List[Dict[str, str]]:
        """Clean LaTeX commands from sections and embed MathML equations inline"""
        cleaned = []
        for section in sections:
            cleaned_section = section.copy()
            if section.get('title'):
                cleaned_section['title'] = self.cleaner.latex_to_text(section['title'])
            if section.get('content'):
                content = section['content']
                
                # First: Replace equation environments with placeholders
                equation_map = {}
                for i, eq in enumerate(equations):
                    if eq['full_match'] in content:
                        placeholder = f"__EQ_PLACEHOLDER_{i}__"
                        equation_map[placeholder] = eq
                        content = content.replace(eq['full_match'], placeholder)
                
                # Second: Replace citations with placeholders
                citation_map = {}
                for i, cite in enumerate(citations):
                    if cite['full_match'] in content:
                        placeholder = f"__CITE_PLACEHOLDER_{i}__"
                        citation_map[placeholder] = cite
                        content = content.replace(cite['full_match'], placeholder)
                
                # Third: Replace tables with placeholders
                table_map = {}
                for i, table in enumerate(tables):
                    if table.get('content') and table['content'] in content:
                        placeholder = f"__TABLE_PLACEHOLDER_{i}__"
                        table_map[placeholder] = table
                        content = content.replace(table['content'], placeholder)
                
                # Second: Clean all LaTeX commands (placeholders are safe)
                content = self.cleaner.latex_to_text(content)
                
                # Third: Replace citation placeholders with author names
                for placeholder, cite in citation_map.items():
                    author_names = []
                    for key in cite['keys']:
                        # Find reference by key and get first author
                        ref = next((r for r in references if r.get('id') == key), None)
                        if ref and ref.get('authors'):
                            author_names.append(ref['authors'][0])
                        else:
                            author_names.append(key)  # Fallback to key
                    citation_text = f"[{', '.join(author_names)}]"
                    content = content.replace(placeholder, citation_text)
                
                # Fourth: Replace table placeholders with XML table elements
                for placeholder, table in table_map.items():
                    table_xml = self._generate_table_xml(table)
                    content = content.replace(placeholder, table_xml)
                
                # Fifth: Convert equation LaTeX to MathML and replace placeholders
                for placeholder, eq in equation_map.items():
                    if eq.get('latex'):
                        try:
                            mathml = latex2mathml.converter.convert(eq['latex'])
                            content = content.replace(placeholder, mathml)
                        except Exception as e:
                            print(f"   ⚠️ Failed to convert equation to MathML: {e}")
                            content = content.replace(placeholder, f"({eq['latex']})")
                    else:
                        content = content.replace(placeholder, f"({eq.get('latex', 'equation')})")
                
                cleaned_section['content'] = content
            cleaned.append(cleaned_section)
        return cleaned
    
    def _generate_table_xml(self, table: Dict) -> str:
        """Generate XML table element from structured table data"""
        xml_lines = [f'<ap:table xmlns:ap="http://example.com/academic-paper" id="{table["id"]}">']
        
        if table.get('caption'):
            xml_lines.append(f'  <ap:caption>{self._escape_xml(table["caption"])}</ap:caption>')
        
        if table.get('headers'):
            xml_lines.append('  <ap:headers>')
            for header in table['headers']:
                if isinstance(header, dict):
                    colspan_attr = f' colspan="{header["colspan"]}"' if header.get('colspan', 1) > 1 else ''
                    xml_lines.append(f'    <ap:header{colspan_attr}>{self._escape_xml(header["content"])}</ap:header>')
                else:
                    xml_lines.append(f'    <ap:header>{self._escape_xml(header)}</ap:header>')
            xml_lines.append('  </ap:headers>')
        
        if table.get('rows'):
            xml_lines.append('  <ap:rows>')
            for row in table['rows']:
                xml_lines.append('    <ap:row>')
                for cell in row:
                    if isinstance(cell, dict):
                        colspan_attr = f' colspan="{cell["colspan"]}"' if cell.get('colspan', 1) > 1 else ''
                        xml_lines.append(f'      <ap:cell{colspan_attr}>{self._escape_xml(cell["content"])}</ap:cell>')
                    else:
                        xml_lines.append(f'      <ap:cell>{self._escape_xml(cell)}</ap:cell>')
                xml_lines.append('    </ap:row>')
            xml_lines.append('  </ap:rows>')
        
        xml_lines.append('</ap:table>')
        return '\n'.join(xml_lines)
    
    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters"""
        if not text:
            return ""
        return (str(text)
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))

class UnstructuredProcessor:
    """Phase 3: Process unstructured elements with LLM"""
    
    def __init__(self):
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    def process_bibliography(self, bibliography_block: str) -> List[Dict[str, Any]]:
        """Process bibliography using LLM in batches"""
        if not bibliography_block:
            return []
        
        # Extract individual bibitem entries
        bibitem_pattern = r'\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}(.*?)(?=\\bibitem|\\end\{thebibliography\}|$)'
        matches = list(re.finditer(bibitem_pattern, bibliography_block, re.DOTALL))
        
        all_references = []
        batch_size = 5
        
        for i in range(0, len(matches), batch_size):
            batch = matches[i:i + batch_size]
            batch_refs = self._process_reference_batch(batch)
            all_references.extend(batch_refs)
        
        return all_references
    
    def _process_reference_batch(self, batch) -> List[Dict[str, Any]]:
        """Process a batch of references with LLM"""
        batch_text = ""
        for match in batch:
            ref_id = match.group(1)
            content = match.group(2).strip()
            batch_text += f"ID: {ref_id}\nContent: {content}\n\n"
        
        prompt = f"""Convert these bibliography entries to structured JSON format.

REQUIRED JSON FORMAT:
[
  {{
    "id": "ref_id",
    "authors": ["Author 1", "Author 2"],
    "title": "Paper Title",
    "venue": "Journal/Conference Name",
    "year": "YYYY"
  }}
]

BIBLIOGRAPHY ENTRIES:
{batch_text}

Return ONLY the JSON array. Extract complete information for each entry."""
        
        try:
            response = self.bedrock.converse(
                modelId="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                inferenceConfig={"maxTokens": 2000, "temperature": 0.1}
            )
            
            llm_response = response['output']['message']['content'][0]['text']
            json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
        except Exception as e:
            print(f"   ⚠️ Batch processing failed: {e}")
        
        return []

class XMLAssembler:
    """Phase 4: Assemble schema-compliant XML with MathML"""
    
    def assemble(self, metadata: Dict, sections: List, references: List, equations: List, elements: Dict) -> str:
        """Generate XML with proper namespaces for XSLT compatibility"""
        
        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<paper xmlns="http://example.com/academic-paper">',
            '  <metadata>'
        ]
        
        # Metadata
        if metadata.get('title'):
            xml_lines.append(f'    <title>{self._escape_xml(metadata["title"])}</title>')
        
        # Authors (from LLM extraction)
        if metadata.get('authors'):
            xml_lines.append('    <authors>')
            for author in metadata['authors']:
                xml_lines.append('      <author>')
                if author.get('name'):
                    xml_lines.append(f'        <name>{self._escape_xml(author["name"])}</name>')
                if author.get('affiliation'):
                    xml_lines.append(f'        <affiliation>{self._escape_xml(author["affiliation"])}</affiliation>')
                if author.get('email'):
                    xml_lines.append(f'        <email>{self._escape_xml(author["email"])}</email>')
                xml_lines.append('      </author>')
            xml_lines.append('    </authors>')
        
        if metadata.get('abstract'):
            xml_lines.append(f'    <abstract>{self._escape_xml(metadata["abstract"])}</abstract>')
        
        xml_lines.append('  </metadata>')
        
        # Sections with mixed content (text + MathML)
        if sections:
            xml_lines.append('  <sections>')
            for section in sections:
                xml_lines.extend([
                    f'    <section id="{section["id"]}">',
                    f'      <title>{self._escape_xml(section["title"])}</title>',
                    '      <content>'
                ])
                
                # Handle content with embedded MathML and XML table elements
                content = section.get('content', '')
                if '<math xmlns="http://www.w3.org/1998/Math/MathML"' in content or '<ap:table xmlns:ap="http://example.com/academic-paper"' in content:
                    # Split content around MathML and XML tables
                    import re
                    parts = re.split(r'(<math xmlns="http://www\.w3\.org/1998/Math/MathML".*?</math>|<ap:table xmlns:ap="http://example\.com/academic-paper".*?</ap:table>)', content, flags=re.DOTALL)
                    for part in parts:
                        if part.startswith('<math xmlns="http://www.w3.org/1998/Math/MathML"') or part.startswith('<ap:table xmlns:ap="http://example.com/academic-paper"'):
                            # This is MathML or XML table - don't escape it
                            xml_lines.append(f'        {part}')
                        elif part.strip():
                            # This is text - escape it
                            xml_lines.append(f'        {self._escape_xml(part)}')
                else:
                    # No MathML, just escape the text
                    xml_lines.append(f'        {self._escape_xml(content)}')
                
                xml_lines.extend([
                    '      </content>',
                    '    </section>'
                ])
            xml_lines.append('  </sections>')
        
        # Equations (separate elements for StructuralReviewer compatibility)
        if equations:
            xml_lines.append('  <equations>')
            for eq in equations:
                xml_lines.append(f'    <equation id="{eq["id"]}">')
                xml_lines.append(f'      <content>{self._escape_xml(eq["latex"])}</content>')
                xml_lines.append('    </equation>')
            xml_lines.append('  </equations>')
        
        # Inline math (for StructuralReviewer counting)
        if elements.get('inline_math'):
            xml_lines.append('  <inline_math>')
            for math in elements['inline_math']:
                xml_lines.append(f'    <math id="{math["id"]}">{self._escape_xml(math["content"])}</math>')
            xml_lines.append('  </inline_math>')
        
        # Citations (for StructuralReviewer counting)
        if elements.get('citations'):
            xml_lines.append('  <citations>')
            for cite in elements['citations']:
                xml_lines.append(f'    <citation id="{cite["id"]}" ref="{cite["ref_key"]}"/>')
            xml_lines.append('  </citations>')
        
        # References
        if references:
            xml_lines.append('  <references>')
            for ref in references:
                xml_lines.append(f'    <reference id="{ref.get("id", "unknown")}">')
                
                if ref.get('authors'):
                    xml_lines.append('      <authors>')
                    for author in ref['authors']:
                        xml_lines.append(f'        <author>{self._escape_xml(author)}</author>')
                    xml_lines.append('      </authors>')
                
                for field in ['title', 'venue', 'year']:
                    if ref.get(field):
                        xml_lines.append(f'      <{field}>{self._escape_xml(ref[field])}</{field}>')
                
                xml_lines.append('    </reference>')
            xml_lines.append('  </references>')
        
        # Tables are now inline in content, no separate section needed
        
        # Other elements
        for element_type, items in elements.items():
            if items and element_type not in ['inline_math', 'citations', 'tables']:
                xml_lines.append(f'  <{element_type}>')
                for item in items:
                    xml_lines.extend([
                        f'    <{element_type[:-1]} id="{item["id"]}">',
                        f'      <content>{self._escape_xml(item["content"])}</content>',
                        f'    </{element_type[:-1]}>'
                    ])
                xml_lines.append(f'  </{element_type}>')
        
        xml_lines.append('</paper>')
        return '\n'.join(xml_lines)
    
    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters"""
        if not text:
            return ""
        return (str(text)
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))

class HybridLatexToXmlConverter:
    """Main converter orchestrating all phases"""
    
    def __init__(self, latex_file: str):
        self.latex_file = latex_file
        with open(latex_file, 'r', encoding='utf-8') as f:
            self.latex_content = f.read()
        
        # Initialize components
        self.extractor = StructuralExtractor(self.latex_content)
        self.cleaner = ContentCleaner()
        self.processor = UnstructuredProcessor()
        self.assembler = XMLAssembler()
        
        self.stats = {}
    
    def convert_to_xml(self, output_file: str = None) -> str:
        """Convert LaTeX to XML using hybrid approach"""
        
        if not output_file:
            output_file = f"output/{Path(self.latex_file).stem}_hybrid.xml"
        
        print("🔄 Hybrid LaTeX-to-XML Converter")
        print("=" * 50)
        print("📋 Architecture: TexSoup + pylatexenc + LLM + MathML")
        
        # Phase 1: Structure extraction
        print("🔍 Phase 1: Extracting structure (TexSoup)...")
        metadata = self.extractor.extract_metadata()
        sections = self.extractor.extract_sections()
        bibliography_block = self.extractor.extract_bibliography_block()
        equations = self.extractor.extract_equations()
        citations = self.extractor.extract_citations()
        elements = self.extractor.extract_structured_elements()
        
        # Process bibliography (structural data extraction)
        references = self.processor.process_bibliography(bibliography_block)
        
        # Phase 2: Content cleaning with inline equations
        print("🧹 Phase 2: Cleaning content + inline equations (pylatexenc)...")
        clean_metadata = self.cleaner.clean_metadata(metadata)
        clean_sections = self.cleaner.clean_sections_with_inline_equations(sections, equations, citations, references, elements['tables'])
        
        # Phase 3: XML assembly
        print("📄 Phase 3: Assembling XML with inline MathML...")
        xml_content = self.assembler.assemble(clean_metadata, clean_sections, references, equations, elements)
        
        # Phase 5: Quality assessment
        print("🔍 Phase 5: Quality assessment...")
        quality_score = self._assess_quality(output_file)
        
        # Save output
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        # Update stats
        self.stats.update({
            'sections': len(clean_sections),
            'references': len(references),
            'equations': len(equations),
            'tables': len(elements['tables']),
            'figures': len(elements['figures'])
        })
        
        self._print_results(output_file, quality_score)
        return output_file
    
    def _assess_quality(self, xml_file_path: str) -> float:
        """Use existing StructuralReviewer for quality assessment"""
        try:
            reviewer = StructuralReviewer(self.latex_file, xml_file_path)
            report = reviewer.generate_analysis_report()
            return report['overall_score']
        except Exception as e:
            print(f"   ⚠️ Quality assessment failed: {e}")
            return 0.0
    
    def _print_results(self, output_file: str, quality_score: float):
        """Print conversion results"""
        print(f"✅ XML saved: {output_file}")
        print("\n📊 Extraction Summary:")
        for key, value in self.stats.items():
            print(f"✓ {key.title()}: {value}")
        
        rating = "EXCELLENT" if quality_score >= 90 else "GOOD" if quality_score >= 80 else "FAIR" if quality_score >= 70 else "POOR"
        print(f"📊 Quality Score: {quality_score:.1f}% ({rating})")

def main():
    """Command-line interface"""
    if len(sys.argv) != 2:
        print("Usage: python3 latex_to_xml_hybrid.py <latex_file>")
        sys.exit(1)
    
    latex_file = sys.argv[1]
    if not Path(latex_file).exists():
        print(f"❌ LaTeX file not found: {latex_file}")
        sys.exit(1)
    
    converter = HybridLatexToXmlConverter(latex_file)
    output_file = converter.convert_to_xml()
    
    print(f"\n🎉 Hybrid conversion complete: {output_file}")

if __name__ == "__main__":
    main()
