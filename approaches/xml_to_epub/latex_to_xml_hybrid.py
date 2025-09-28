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
    
    def extract_metadata(self) -> Dict[str, str]:
        """Extract title, authors, abstract"""
        metadata = {}
        
        # Title
        title = self.soup.find('title')
        if title and title.string:
            metadata['title'] = str(title.string).strip()
        
        # Author (simplified - first author only)
        author = self.soup.find('author')
        if author:
            # Extract first line before \\
            author_text = str(author).split('\\\\')[0]
            metadata['author'] = author_text.strip()
        
        # Abstract
        abstract = self.soup.find('abstract')
        if abstract:
            metadata['abstract'] = str(abstract).strip()
        
        return metadata
    
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
    
    def extract_structured_elements(self) -> Dict[str, List]:
        """Extract tables and figures (equations handled separately)"""
        return {
            'tables': [{'id': f"table_{i+1}", 'content': str(table)} 
                      for i, table in enumerate(self.soup.find_all('table'))],
            'figures': [{'id': f"figure_{i+1}", 'content': str(fig)} 
                       for i, fig in enumerate(self.soup.find_all('figure'))]
        }

class ContentCleaner:
    """Phase 2: Clean LaTeX content and replace equations with references"""
    
    def __init__(self):
        self.cleaner = LatexNodes2Text()
    
    def clean_metadata(self, metadata: Dict[str, str]) -> Dict[str, str]:
        """Clean LaTeX commands from metadata"""
        cleaned = {}
        for key, value in metadata.items():
            if value:
                cleaned[key] = self.cleaner.latex_to_text(value)
        return cleaned
    
    def clean_sections_with_inline_equations(self, sections: List[Dict[str, str]], equations: List[Dict[str, str]]) -> List[Dict[str, str]]:
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
                
                # Second: Clean all LaTeX commands (placeholders are safe)
                content = self.cleaner.latex_to_text(content)
                
                # Third: Convert equation LaTeX to MathML and replace placeholders
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
    
    def assemble(self, metadata: Dict, sections: List, references: List, elements: Dict) -> str:
        """Generate XML with proper namespaces for XSLT compatibility"""
        
        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<paper xmlns="http://example.com/academic-paper">',
            '  <metadata>'
        ]
        
        # Metadata
        if metadata.get('title'):
            xml_lines.append(f'    <title>{self._escape_xml(metadata["title"])}</title>')
        
        if metadata.get('author'):
            xml_lines.extend([
                '    <authors>',
                '      <author>',
                f'        <name>{self._escape_xml(metadata["author"])}</name>',
                '      </author>',
                '    </authors>'
            ])
        
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
                
                # Handle content with embedded MathML
                content = section.get('content', '')
                if '<math xmlns="http://www.w3.org/1998/Math/MathML"' in content:
                    # Split content around MathML and handle each part
                    import re
                    parts = re.split(r'(<math xmlns="http://www\.w3\.org/1998/Math/MathML".*?</math>)', content)
                    for part in parts:
                        if part.startswith('<math xmlns="http://www.w3.org/1998/Math/MathML"'):
                            # This is MathML - don't escape it
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
        
        # Other elements
        for element_type, items in elements.items():
            if items:
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
        elements = self.extractor.extract_structured_elements()
        
        # Phase 2: Content cleaning with inline equations
        print("🧹 Phase 2: Cleaning content + inline equations (pylatexenc)...")
        clean_metadata = self.cleaner.clean_metadata(metadata)
        clean_sections = self.cleaner.clean_sections_with_inline_equations(sections, equations)
        
        # Phase 3: Unstructured processing
        print("🤖 Phase 3: Processing bibliography (LLM)...")
        references = self.processor.process_bibliography(bibliography_block)
        
        # Phase 4: XML assembly
        print("📄 Phase 4: Assembling XML with inline MathML...")
        xml_content = self.assembler.assemble(clean_metadata, clean_sections, references, elements)
        
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
