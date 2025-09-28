#!/usr/bin/env python3
"""
Hybrid LaTeX to XML Converter
- Uses heuristic parsing for structured elements (sections, equations, tables)
- Uses LLM (Bedrock) for unstructured elements (references, complex parsing)
"""

import re
import json
import boto3
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any
import sys

class HybridLatexToXmlConverter:
    def __init__(self, latex_file: str):
        self.latex_file = latex_file
        with open(latex_file, 'r', encoding='utf-8') as f:
            self.latex_content = f.read()
        
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        self.extraction_stats = {}
    
    def convert_to_xml(self, output_file: str = None) -> str:
        """Convert LaTeX to XML using hybrid approach"""
        
        if not output_file:
            output_file = f"output/{Path(self.latex_file).stem}_hybrid.xml"
        
        print("🔄 Hybrid LaTeX-to-XML Conversion")
        print("=" * 50)
        
        # Extract structured elements with heuristics
        print("📋 Extracting structured elements (heuristic)...")
        structured_data = self._extract_structured_elements()
        
        # Extract unstructured elements with LLM
        print("🤖 Processing unstructured elements (LLM)...")
        unstructured_data = self._extract_unstructured_elements()
        
        # Generate XML
        print("📄 Generating XML...")
        xml_content = self._generate_xml(structured_data, unstructured_data)
        
        # Save XML
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        print(f"✅ XML saved: {output_file}")
        self._print_stats()
        
        return output_file
    
    def _extract_structured_elements(self) -> Dict[str, Any]:
        """Extract well-structured elements using heuristic parsing"""
        
        data = {
            'metadata': self._extract_metadata(),
            'sections': self._extract_sections(),
            'equations': self._extract_equations(),
            'tables': self._extract_tables(),
            'figures': self._extract_figures(),
            'citations': self._extract_citations()
        }
        
        return data
    
    def _extract_metadata(self) -> Dict[str, str]:
        """Extract title, authors, abstract using heuristics"""
        metadata = {}
        
        # Title
        title_match = re.search(r'\\title\{([^}]+)\}', self.latex_content)
        if title_match:
            title = title_match.group(1).strip()
            # Clean LaTeX commands
            title = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', title)
            metadata['title'] = title
        
        # Authors (simplified - just get first author for now)
        author_match = re.search(r'\\author\{(.*?)\}', self.latex_content, re.DOTALL)
        if author_match:
            authors_raw = author_match.group(1).strip()
            # Extract just the first line (main author)
            first_line = authors_raw.split('\\\\')[0].strip()
            # Clean LaTeX commands
            first_line = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', first_line)
            metadata['authors'] = first_line
        
        # Abstract
        abstract_match = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', self.latex_content, re.DOTALL)
        if abstract_match:
            abstract = abstract_match.group(1).strip()
            # Clean LaTeX commands and normalize whitespace
            abstract = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', abstract)
            abstract = re.sub(r'\s+', ' ', abstract)
            metadata['abstract'] = abstract
        
        return metadata
    
    def _extract_sections(self) -> List[Dict[str, str]]:
        """Extract sections using LaTeX structure tags"""
        sections = []
        
        # Find all section commands
        section_pattern = r'\\(sub)*section\*?\{([^}]+)\}(.*?)(?=\\(?:sub)*section|\Z)'
        matches = re.finditer(section_pattern, self.latex_content, re.DOTALL)
        
        for i, match in enumerate(matches, 1):
            level = "subsection" if match.group(1) else "section"
            title = match.group(2).strip()
            content = match.group(3).strip()
            
            # Clean title and content
            title = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', title)
            content = self._clean_latex_content(content)
            
            sections.append({
                'id': f"section_{i}",
                'level': level,
                'title': title,
                'content': content[:500] + "..." if len(content) > 500 else content
            })
        
        self.extraction_stats['sections'] = len(sections)
        return sections
    
    def _clean_latex_content(self, content: str) -> str:
        """Clean LaTeX commands from content"""
        # Remove common LaTeX commands
        content = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', content)
        content = re.sub(r'\\[a-zA-Z]+\*?\s*', '', content)
        content = re.sub(r'\$([^$]+)\$', r'\1', content)  # Inline math
        content = re.sub(r'\\\\', ' ', content)  # Line breaks
        content = re.sub(r'\\&', '&', content)  # Escaped ampersands
        content = re.sub(r'\s+', ' ', content)  # Normalize whitespace
        return content.strip()
    
    def _extract_equations(self) -> List[Dict[str, str]]:
        """Extract equations using LaTeX math environments"""
        equations = []
        
        # Find equation environments
        eq_patterns = [
            r'\\begin\{equation\}(.*?)\\end\{equation\}',
            r'\\begin\{align\}(.*?)\\end\{align\}',
            r'\$\$(.*?)\$\$'
        ]
        
        for pattern in eq_patterns:
            matches = re.finditer(pattern, self.latex_content, re.DOTALL)
            for i, match in enumerate(matches):
                equations.append({
                    'id': f"eq_{len(equations) + 1}",
                    'content': match.group(1).strip()
                })
        
        self.extraction_stats['equations'] = len(equations)
        return equations
    
    def _extract_tables(self) -> List[Dict[str, str]]:
        """Extract tables using LaTeX table environments"""
        tables = []
        
        # Find table environments
        table_pattern = r'\\begin\{table\}(.*?)\\end\{table\}'
        matches = re.finditer(table_pattern, self.latex_content, re.DOTALL)
        
        for i, match in enumerate(matches, 1):
            tables.append({
                'id': f"table_{i}",
                'content': match.group(1).strip()
            })
        
        self.extraction_stats['tables'] = len(tables)
        return tables
    
    def _extract_figures(self) -> List[Dict[str, str]]:
        """Extract figures using LaTeX figure environments"""
        figures = []
        
        # Find figure environments
        figure_pattern = r'\\begin\{figure\}(.*?)\\end\{figure\}'
        matches = re.finditer(figure_pattern, self.latex_content, re.DOTALL)
        
        for i, match in enumerate(matches, 1):
            figures.append({
                'id': f"figure_{i}",
                'content': match.group(1).strip()
            })
        
        self.extraction_stats['figures'] = len(figures)
        return figures
    
    def _extract_citations(self) -> List[str]:
        """Extract citation references using heuristics"""
        citations = re.findall(r'\\cite\{([^}]+)\}', self.latex_content)
        self.extraction_stats['citations'] = len(set(citations))
        return list(set(citations))
    
    def _extract_unstructured_elements(self) -> Dict[str, Any]:
        """Extract unstructured elements using LLM"""
        
        # Extract raw bibliography section
        bib_match = re.search(r'\\begin\{thebibliography\}.*?\\end\{thebibliography\}', self.latex_content, re.DOTALL)
        raw_bibliography = bib_match.group(0) if bib_match else ""
        
        if raw_bibliography:
            print("   📚 Processing bibliography with LLM...")
            structured_refs = self._process_bibliography_with_llm(raw_bibliography)
            return {'references': structured_refs}
        
        return {'references': []}
    
    def _process_bibliography_with_llm(self, raw_bibliography: str) -> List[Dict[str, Any]]:
        """Use Bedrock to structure bibliography entries"""
        
        # Extract individual bibitem entries
        bibitem_pattern = r'\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}(.*?)(?=\\bibitem|\\end\{thebibliography\}|$)'
        matches = re.finditer(bibitem_pattern, raw_bibliography, re.DOTALL)
        
        all_references = []
        
        # Process in batches to handle token limits
        batch_size = 5
        current_batch = []
        
        for match in matches:
            ref_id = match.group(1)
            content = match.group(2).strip()
            current_batch.append((ref_id, content))
            
            if len(current_batch) >= batch_size:
                batch_refs = self._process_reference_batch(current_batch)
                all_references.extend(batch_refs)
                current_batch = []
        
        # Process remaining batch
        if current_batch:
            batch_refs = self._process_reference_batch(current_batch)
            all_references.extend(batch_refs)
        
        self.extraction_stats['bibliography'] = len(all_references)
        print(f"   ✅ Processed {len(all_references)} references")
        return all_references
    
    def _process_reference_batch(self, batch: List[tuple]) -> List[Dict[str, Any]]:
        """Process a batch of references with LLM"""
        
        batch_text = ""
        for ref_id, content in batch:
            batch_text += f"\\bibitem{{{ref_id}}} {content}\n\n"
        
        prompt = f"""Convert these LaTeX bibliography entries to structured JSON format.

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
                messages=[{
                    "role": "user",
                    "content": [{"text": prompt}]
                }],
                inferenceConfig={
                    "maxTokens": 2000,
                    "temperature": 0.1
                }
            )
            
            llm_response = response['output']['message']['content'][0]['text']
            
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            
        except Exception as e:
            print(f"   ⚠️ Batch processing failed: {e}")
        
        return []
    
    def _generate_xml(self, structured_data: Dict, unstructured_data: Dict) -> str:
        """Generate final XML from structured and unstructured data"""
        
        # Create root with proper namespace
        root = ET.Element('{http://example.com/academic-paper}paper')
        root.set('xmlns', 'http://example.com/academic-paper')
        
        # Add metadata
        if structured_data['metadata']:
            metadata = ET.SubElement(root, 'metadata')
            for key, value in structured_data['metadata'].items():
                if key == 'authors':
                    # Create proper authors structure
                    authors_elem = ET.SubElement(metadata, 'authors')
                    author_elem = ET.SubElement(authors_elem, 'author')
                    name_elem = ET.SubElement(author_elem, 'name')
                    name_elem.text = value
                else:
                    elem = ET.SubElement(metadata, key)
                    elem.text = value
        
        # Add sections
        if structured_data['sections']:
            sections = ET.SubElement(root, 'sections')
            for section in structured_data['sections']:
                sec_elem = ET.SubElement(sections, 'section')
                sec_elem.set('id', section['id'])
                
                title_elem = ET.SubElement(sec_elem, 'title')
                title_elem.text = section['title']
                
                content_elem = ET.SubElement(sec_elem, 'content')
                content_elem.text = section['content']
        
        # Add references (from LLM)
        if unstructured_data['references']:
            refs_elem = ET.SubElement(root, 'references')
            for ref in unstructured_data['references']:
                ref_elem = ET.SubElement(refs_elem, 'reference')
                ref_elem.set('id', ref.get('id', 'unknown'))
                
                if ref.get('authors'):
                    authors_elem = ET.SubElement(ref_elem, 'authors')
                    for author in ref['authors']:
                        author_elem = ET.SubElement(authors_elem, 'author')
                        author_elem.text = author
                
                for field in ['title', 'venue', 'year']:
                    if ref.get(field):
                        field_elem = ET.SubElement(ref_elem, field)
                        field_elem.text = ref[field]
        
        # Add other structured elements (simplified)
        for element_type in ['equations', 'tables', 'figures']:
            if structured_data[element_type]:
                container = ET.SubElement(root, element_type)
                for item in structured_data[element_type]:
                    item_elem = ET.SubElement(container, element_type[:-1])  # Remove 's'
                    item_elem.set('id', item['id'])
                    content_elem = ET.SubElement(item_elem, 'content')
                    content_elem.text = item['content']
        
        # Format XML with namespace declaration
        ET.register_namespace('', 'http://example.com/academic-paper')
        ET.indent(root, space="  ")
        xml_str = ET.tostring(root, encoding='unicode')
        
        # Add XML declaration
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
    
    def _print_stats(self):
        """Print extraction statistics"""
        print("\n📊 Extraction Summary:")
        for key, value in self.extraction_stats.items():
            print(f"✓ {key.title()}: {value}")

def main():
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
