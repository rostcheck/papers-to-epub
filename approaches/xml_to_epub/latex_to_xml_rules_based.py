#!/usr/bin/env python3
"""
Rules-Based LaTeX to XML Converter
High-quality engineering component for academic paper conversion
"""

import re
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from xml.etree import ElementTree as ET
from xml.dom import minidom

class RulesBasedConverter:
    """
    Rules-based LaTeX to XML converter using regex parsing.
    Provides comprehensive content extraction with structured output.
    """
    
    def __init__(self):
        self.latex_content = ""
        self.extraction_stats = {}
        
    def load_latex(self, latex_file: str) -> None:
        """Load and expand LaTeX content from file with recursive input handling"""
        try:
            self.latex_content = self._expand_latex(latex_file)
        except Exception as e:
            raise ValueError(f"Failed to load LaTeX file {latex_file}: {e}")
    
    def _expand_latex(self, main_file: str, base_dir: Path = None) -> str:
        r"""Recursively expand \input{} commands in LaTeX files"""
        if base_dir is None:
            base_dir = Path(main_file).parent
        
        content = Path(main_file).read_text(encoding='utf-8')
        
        def replace_input(match):
            filename = match.group(1)
            if not filename.endswith('.tex'):
                filename += '.tex'
            
            input_path = base_dir / filename
            if input_path.exists():
                return self._expand_latex(str(input_path), base_dir)
            else:
                return match.group(0)  # Keep original if file not found
        
        # Expand input files
        expanded_content = re.sub(r'\\input\{([^}]+)\}', replace_input, content)
        
        # Filter LaTeX comments (but preserve escaped % characters)
        filtered_content = self._filter_latex_comments(expanded_content)
        
        return filtered_content
    
    def _filter_latex_comments(self, content: str) -> str:
        """Remove LaTeX comments while preserving escaped % characters"""
        lines = content.split('\n')
        filtered_lines = []
        
        for line in lines:
            # Find the first unescaped % character
            comment_pos = -1
            i = 0
            while i < len(line):
                if line[i] == '%':
                    # Check if it's escaped
                    if i == 0 or line[i-1] != '\\':
                        comment_pos = i
                        break
                elif line[i] == '\\' and i + 1 < len(line) and line[i+1] == '%':
                    # Skip escaped %
                    i += 1
                i += 1
            
            if comment_pos >= 0:
                # Remove comment part but keep the line break
                filtered_lines.append(line[:comment_pos].rstrip())
            else:
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def extract_metadata(self) -> Dict[str, Any]:
        """Extract title, authors, and abstract"""
        metadata = {
            'title': self._extract_title(),
            'authors': self._extract_authors(),
            'abstract': self._extract_abstract()
        }
        return metadata
    
    def extract_structure(self) -> Dict[str, Any]:
        """Extract document structure (sections, subsections)"""
        sections = self._extract_sections()
        self.extraction_stats['sections'] = len(sections)
        return {'sections': sections}
    
    def extract_mathematics(self) -> Dict[str, Any]:
        """Extract equations and mathematical content"""
        equations = self._extract_equations()
        self.extraction_stats['equations'] = len(equations)
        return {'equations': equations}
    
    def extract_references(self) -> Dict[str, Any]:
        """Extract bibliography and citations"""
        bibliography = self._extract_bibliography()
        citations = self._extract_citations()
        self.extraction_stats['bibliography'] = len(bibliography)
        self.extraction_stats['citations'] = len(citations)
        return {
            'bibliography': bibliography,
            'citations': citations
        }
    
    def extract_tables_figures(self) -> Dict[str, Any]:
        """Extract tables and figures"""
        tables = self._extract_tables()
        figures = self._extract_figures()
        self.extraction_stats['tables'] = len(tables)
        self.extraction_stats['figures'] = len(figures)
        return {
            'tables': tables,
            'figures': figures
        }
    
    def convert_to_json(self) -> Dict[str, Any]:
        """Convert LaTeX to structured JSON representation"""
        if not self.latex_content:
            raise ValueError("No LaTeX content loaded")
        
        return {
            'metadata': self.extract_metadata(),
            'structure': self.extract_structure(),
            'mathematics': self.extract_mathematics(),
            'references': self.extract_references(),
            'tables_figures': self.extract_tables_figures(),
            'extraction_stats': self.extraction_stats
        }
    
    def convert_to_xml(self, json_data: Dict[str, Any]) -> str:
        """Convert JSON representation to XML string"""
        root = ET.Element('paper')
        root.set('xmlns', 'http://example.com/academic-paper')
        root.set('xmlns:xhtml', 'http://www.w3.org/1999/xhtml')
        root.set('xmlns:mathml', 'http://www.w3.org/1998/Math/MathML')
        
        # Add metadata
        self._add_metadata_to_xml(root, json_data['metadata'])
        
        # Add sections
        self._add_sections_to_xml(root, json_data['structure']['sections'])
        
        # Add references
        self._add_references_to_xml(root, json_data['references'])
        
        # Add tables and figures
        self._add_tables_figures_to_xml(root, json_data['tables_figures'])
        
        # Add equations
        self._add_equations_to_xml(root, json_data['mathematics']['equations'])
        
        return self._prettify_xml(root)
    
    def get_extraction_summary(self) -> Dict[str, Any]:
        """Get summary of extraction statistics"""
        return {
            'total_sections': self.extraction_stats.get('sections', 0),
            'total_equations': self.extraction_stats.get('equations', 0),
            'total_citations': self.extraction_stats.get('citations', 0),
            'total_bibliography': self.extraction_stats.get('bibliography', 0),
            'total_tables': self.extraction_stats.get('tables', 0),
            'total_figures': self.extraction_stats.get('figures', 0)
        }
    
    # Private extraction methods
    def _extract_title(self) -> str:
        """Extract document title"""
        match = re.search(r'\\title\{([^}]+)\}', self.latex_content)
        return match.group(1) if match else ""
    
    def _extract_authors(self) -> List[Dict[str, str]]:
        """Extract author information"""
        authors = []
        author_match = re.search(r'\\author\{(.*?)\}', self.latex_content, re.DOTALL)
        
        if author_match:
            author_content = author_match.group(1)
            author_parts = re.split(r'\\And|\\AND', author_content)
            
            for part in author_parts:
                lines = [line.strip() for line in part.strip().split('\\\\') if line.strip()]
                if lines:
                    name = lines[0].strip()
                    affiliation = ""
                    email = ""
                    
                    for line in lines[1:]:
                        if '\\texttt{' in line:
                            email_match = re.search(r'\\texttt\{([^}]+)\}', line)
                            if email_match:
                                email = email_match.group(1)
                        else:
                            if affiliation:
                                affiliation += ", "
                            affiliation += line.strip()
                    
                    authors.append({
                        'name': name,
                        'affiliation': affiliation,
                        'email': email
                    })
        
        return authors
    
    def _extract_abstract(self) -> str:
        """Extract abstract content"""
        match = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', 
                         self.latex_content, re.DOTALL)
        return match.group(1).strip() if match else ""
    
    def _extract_sections(self) -> List[Dict[str, Any]]:
        """Extract sections and subsections"""
        sections = []
        
        # Find all section-level commands
        section_pattern = r'\\(section|subsection|subsubsection)\{([^}]+)\}(.*?)(?=\\(?:section|subsection|subsubsection)\{|\\end\{document\}|$)'
        matches = re.finditer(section_pattern, self.latex_content, re.DOTALL)
        
        for match in matches:
            level = match.group(1)
            title = match.group(2)
            content = match.group(3).strip()
            
            sections.append({
                'level': level,
                'title': title,
                'content': content
            })
        
        return sections
    
    def _extract_equations(self) -> List[Dict[str, str]]:
        """Extract mathematical equations"""
        equations = []
        
        # Extract equation environments
        eq_patterns = [
            r'\\begin\{equation\}(.*?)\\end\{equation\}',
            r'\\begin\{align\}(.*?)\\end\{align\}',
            r'\\begin\{eqnarray\}(.*?)\\end\{eqnarray\}',
            r'\$\$(.*?)\$\$'
        ]
        
        for pattern in eq_patterns:
            matches = re.finditer(pattern, self.latex_content, re.DOTALL)
            for match in matches:
                equations.append({
                    'content': match.group(1).strip(),
                    'type': 'display'
                })
        
        return equations
    
    def _extract_bibliography(self) -> List[Dict[str, str]]:
        """Extract bibliography entries"""
        bibliography = []
        
        # Extract bibitem entries
        bibitem_pattern = r'\\bibitem\{([^}]+)\}(.*?)(?=\\bibitem|\\end\{thebibliography\}|$)'
        matches = re.finditer(bibitem_pattern, self.latex_content, re.DOTALL)
        
        for match in matches:
            ref_id = match.group(1)
            content = match.group(2).strip()
            
            bibliography.append({
                'id': ref_id,
                'content': content
            })
        
        return bibliography
    
    def _extract_citations(self) -> List[str]:
        """Extract citation references"""
        citations = []
        
        # Find all \cite commands
        cite_pattern = r'\\cite\{([^}]+)\}'
        matches = re.finditer(cite_pattern, self.latex_content)
        
        for match in matches:
            cite_keys = match.group(1).split(',')
            citations.extend([key.strip() for key in cite_keys])
        
        return list(set(citations))  # Remove duplicates
    
    def _extract_tables(self) -> List[Dict[str, Any]]:
        """Extract table environments"""
        tables = []
        
        table_pattern = r'\\begin\{table\}(.*?)\\end\{table\}'
        matches = re.finditer(table_pattern, self.latex_content, re.DOTALL)
        
        for i, match in enumerate(matches):
            content = match.group(1)
            
            # Extract caption if present
            caption_match = re.search(r'\\caption\{([^}]+)\}', content)
            caption = caption_match.group(1) if caption_match else f"Table {i+1}"
            
            tables.append({
                'id': f"table_{i+1}",
                'caption': caption,
                'content': content.strip()
            })
        
        return tables
    
    def _extract_figures(self) -> List[Dict[str, Any]]:
        """Extract figure environments"""
        figures = []
        
        figure_pattern = r'\\begin\{figure\}(.*?)\\end\{figure\}'
        matches = re.finditer(figure_pattern, self.latex_content, re.DOTALL)
        
        for i, match in enumerate(matches):
            content = match.group(1)
            
            # Extract caption and includegraphics
            caption_match = re.search(r'\\caption\{([^}]+)\}', content)
            caption = caption_match.group(1) if caption_match else f"Figure {i+1}"
            
            graphics_match = re.search(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', content)
            source = graphics_match.group(1) if graphics_match else ""
            
            figures.append({
                'id': f"figure_{i+1}",
                'caption': caption,
                'source': source,
                'content': content.strip()
            })
        
        return figures
    
    # Private XML generation methods
    def _add_metadata_to_xml(self, root: ET.Element, metadata: Dict[str, Any]) -> None:
        """Add metadata section to XML"""
        metadata_elem = ET.SubElement(root, 'metadata')
        
        # Title
        title_elem = ET.SubElement(metadata_elem, 'title')
        title_elem.text = metadata['title']
        
        # Authors
        authors_elem = ET.SubElement(metadata_elem, 'authors')
        for author in metadata['authors']:
            author_elem = ET.SubElement(authors_elem, 'author')
            
            name_elem = ET.SubElement(author_elem, 'name')
            name_elem.text = author['name']
            
            if author['affiliation']:
                affil_elem = ET.SubElement(author_elem, 'affiliation')
                affil_elem.text = author['affiliation']
            
            if author['email']:
                email_elem = ET.SubElement(author_elem, 'email')
                email_elem.text = author['email']
        
        # Abstract
        if metadata['abstract']:
            abstract_elem = ET.SubElement(metadata_elem, 'abstract')
            # Convert citations in abstract too
            self._add_content_with_citations(abstract_elem, metadata['abstract'])
    
    def _add_sections_to_xml(self, root: ET.Element, sections: List[Dict[str, Any]]) -> None:
        """Add sections to XML"""
        sections_elem = ET.SubElement(root, 'sections')
        
        for i, section in enumerate(sections):
            section_elem = ET.SubElement(sections_elem, 'section')
            section_elem.set('id', f"section_{i+1}")
            section_elem.set('level', section['level'])
            
            title_elem = ET.SubElement(section_elem, 'title')
            title_elem.text = section['title']
            
            content_elem = ET.SubElement(section_elem, 'content')
            
            # Convert LaTeX citations to XML citation elements in content
            self._add_content_with_citations(content_elem, section['content'])
    
    def _add_content_with_citations(self, parent_elem: ET.Element, text: str) -> None:
        """Add content with embedded citation elements"""
        p_elem = ET.SubElement(parent_elem, 'p')
        p_elem.set('xmlns', 'http://www.w3.org/1999/xhtml')
        
        # Find all citation patterns and their positions
        citation_pattern = r'\\cite(?:p)?\{([^}]+)\}'
        matches = list(re.finditer(citation_pattern, text))
        
        if not matches:
            # No citations, just add text
            p_elem.text = text
            return
        
        # Build content with citations
        last_end = 0
        
        for match in matches:
            # Add text before citation
            before_text = text[last_end:match.start()]
            if before_text:
                if p_elem.text is None:
                    p_elem.text = before_text
                else:
                    # Add to tail of last element
                    if len(p_elem) > 0:
                        if p_elem[-1].tail is None:
                            p_elem[-1].tail = before_text
                        else:
                            p_elem[-1].tail += before_text
                    else:
                        p_elem.text += before_text
            
            # Add citation elements
            cite_keys = match.group(1).split(',')
            for key in cite_keys:
                key = key.strip()
                citation_elem = ET.SubElement(p_elem, 'citation')
                citation_elem.text = key
            
            last_end = match.end()
        
        # Add remaining text after last citation
        remaining_text = text[last_end:]
        if remaining_text:
            if len(p_elem) > 0:
                if p_elem[-1].tail is None:
                    p_elem[-1].tail = remaining_text
                else:
                    p_elem[-1].tail += remaining_text
            else:
                if p_elem.text is None:
                    p_elem.text = remaining_text
                else:
                    p_elem.text += remaining_text

    
    def _add_references_to_xml(self, root: ET.Element, references: Dict[str, Any]) -> None:
        """Add references section to XML"""
        if references['bibliography']:
            refs_elem = ET.SubElement(root, 'references')
            
            for ref in references['bibliography']:
                ref_elem = ET.SubElement(refs_elem, 'reference')
                ref_elem.set('id', ref['id'])
                
                content_elem = ET.SubElement(ref_elem, 'content')
                content_elem.text = ref['content']
    
    def _add_tables_figures_to_xml(self, root: ET.Element, tables_figures: Dict[str, Any]) -> None:
        """Add tables and figures to XML"""
        # Add tables
        for table in tables_figures['tables']:
            table_elem = ET.SubElement(root, 'table')
            table_elem.set('id', table['id'])
            
            caption_elem = ET.SubElement(table_elem, 'caption')
            caption_elem.text = table['caption']
            
            content_elem = ET.SubElement(table_elem, 'content')
            content_elem.text = table['content']
        
        # Add figures
        for figure in tables_figures['figures']:
            figure_elem = ET.SubElement(root, 'figure')
            figure_elem.set('id', figure['id'])
            
            caption_elem = ET.SubElement(figure_elem, 'caption')
            caption_elem.text = figure['caption']
            
            if figure['source']:
                source_elem = ET.SubElement(figure_elem, 'source_reference')
                source_elem.text = figure['source']
    
    def _add_equations_to_xml(self, root: ET.Element, equations: List[Dict[str, str]]) -> None:
        """Add equations to XML"""
        for i, equation in enumerate(equations):
            eq_elem = ET.SubElement(root, 'equation')
            eq_elem.set('id', f"eq_{i+1}")
            eq_elem.set('type', equation['type'])
            eq_elem.text = equation['content']
    
    def _prettify_xml(self, root: ET.Element) -> str:
        """Format XML with proper indentation"""
        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")


def main():
    """Command-line interface"""
    if len(sys.argv) < 2:
        print("Usage: python3 latex_to_xml_rules_based.py <latex_file> [output_file]")
        sys.exit(1)
    
    latex_file = sys.argv[1]
    
    # Determine output file
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        latex_path = Path(latex_file)
        output_file = f"output/{latex_path.stem}_rules_based.xml"
    
    try:
        # Initialize converter
        converter = RulesBasedConverter()
        converter.load_latex(latex_file)
        
        # Convert to JSON representation (internal processing)
        json_data = converter.convert_to_json()
        
        # Convert to XML and save
        xml_content = converter.convert_to_xml(json_data)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        print(f"XML conversion complete: {output_file}")
        
        # Display extraction summary
        summary = converter.get_extraction_summary()
        print("\nExtraction Summary:")
        for key, value in summary.items():
            print(f"✓ {key.replace('total_', '').title()}: {value}")
        
        # Import and use structural reviewer for quality assessment
        try:
            from structural_review.review_structure import StructuralReviewer
            
            reviewer = StructuralReviewer(latex_file, output_file)
            json_output = reviewer.output_json()
            analysis = json.loads(json_output)
            
            score = analysis.get('overall_score', 0)
            quality_level = analysis.get('summary', {}).get('quality_level', 'UNKNOWN')
            print(f"\n📊 Quality Score: {score}% ({quality_level})")
        except Exception as e:
            print(f"\n⚠️  Quality assessment unavailable: {e}")
    
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
