#!/usr/bin/env python3
"""
Structural Quality Assurance Review
LaTeX to XML Conversion Analysis with LaTeX Expansion
"""

import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
import json
import sys

class StructuralReviewer:
    def __init__(self, latex_file: str, xml_file: str):
        self.latex_file = latex_file
        self.xml_file = xml_file
        self.latex_content = ""
        self.xml_root = None
        self.issues = defaultdict(list)
        self.ns = {'ap': 'http://example.com/academic-paper'}
        self.load_files()
    
    def expand_latex(self, main_file, base_dir=None):
        """Recursively expand \input{} commands in LaTeX files"""
        if base_dir is None:
            base_dir = Path(main_file).parent
        
        content = Path(main_file).read_text(encoding='utf-8')
        
        def replace_input(match):
            filename = match.group(1)
            if not filename.endswith('.tex'):
                filename += '.tex'
            
            input_path = base_dir / filename
            if input_path.exists():
                return self.expand_latex(input_path, base_dir)
            else:
                return match.group(0)  # Keep original if file not found
        
        # Replace \input{filename} with file contents
        content = re.sub(r'\\input\{([^}]+)\}', replace_input, content)
        
        return content
    
    def load_files(self):
        """Load and expand LaTeX files, then load XML"""
        print(f"📄 Expanding LaTeX file: {self.latex_file}", file=sys.stderr)
        self.latex_content = self.expand_latex(self.latex_file)
        print(f"📄 Expanded content: {len(self.latex_content):,} characters", file=sys.stderr)
        
        self.xml_root = ET.parse(self.xml_file).getroot()
    
    def analyze_all(self, output_format='text'):
        """Run all analyses and generate report"""
        
        # Collect analysis data
        analysis_data = {
            'metadata': {},
            'structure': {},
            'mathematics': {},
            'references': {},
            'tables_figures': {},
            'summary': {}
        }
        
        if output_format == 'text':
            print("="*80)
            print("COMPREHENSIVE STRUCTURAL QUALITY ASSURANCE REPORT")
            print("LaTeX to XML Conversion Analysis")
            print("="*80)
        
    def parse_latex_title(self):
        """Extract title from LaTeX, skipping commented lines"""
        # Find all title commands, filter out commented ones
        title_matches = re.findall(r'^(?!%).*\\title\{([^}]+)\}', self.latex_content, re.MULTILINE)
        return title_matches[-1] if title_matches else ""
    
    def parse_latex_authors(self):
        """Extract author count from LaTeX, handling various formats"""
        # Find all author commands, filter out commented ones
        author_matches = re.findall(r'^(?!%).*\\author\{(.*?)\}', self.latex_content, re.MULTILINE | re.DOTALL)
        
        if not author_matches:
            return 0
        
        # Take the last (actual) author definition
        author_text = author_matches[-1]
        
        # Method 1: Count \And and \AND separators
        and_separators = len(re.findall(r'\\And|\\AND', author_text))
        if and_separators > 0:
            return and_separators + 1
        
        # Method 2: Count comma-separated names (heuristic)
        # Remove LaTeX formatting and count names
        clean_text = re.sub(r'\$[^$]*\$', '', author_text)  # Remove math
        clean_text = re.sub(r'\\textbf\{([^}]+)\}', r'\1', clean_text)  # Remove \textbf{}
        clean_text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', clean_text)  # Remove other commands
        clean_text = re.sub(r'\$[^$]*\$', '', clean_text)  # Remove remaining math
        clean_text = re.sub(r'\\\\', ' ', clean_text)  # Replace line breaks
        
        # Split by commas and count names (simple heuristic)
        names = [name.strip() for name in clean_text.split(',') if name.strip()]
        # Filter out affiliation lines (contain "University", "Institute", etc.)
        actual_names = [name for name in names if not re.search(r'University|Institute|College|Department', name, re.IGNORECASE)]
        
        return max(len(actual_names), 1)  # At least 1 author
    
    def analyze_all(self, output_format='text'):
        """Run all analyses and generate report"""
        
        # Collect analysis data
        analysis_data = {
            'metadata': {},
            'structure': {},
            'mathematics': {},
            'references': {},
            'tables_figures': {},
            'summary': {}
        }
        
        if output_format == 'text':
            print("="*80)
            print("COMPREHENSIVE STRUCTURAL QUALITY ASSURANCE REPORT")
            print("LaTeX to XML Conversion Analysis")
            print("="*80)
        
        # 1. Metadata Analysis
        if output_format == 'text':
            print("\n=== METADATA ANALYSIS ===")
            
        latex_title = self.parse_latex_title()
        
        # Use namespace-aware search
        xml_title_elem = self.xml_root.find('.//ap:title', self.ns)
        xml_title = xml_title_elem.text if xml_title_elem is not None else ""
        
        # Authors
        latex_authors = self.parse_latex_authors()
        xml_authors = len(self.xml_root.findall('.//ap:author', self.ns))
        
        # Abstract
        latex_abstract = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', self.latex_content, re.DOTALL)
        latex_abstract_len = len(latex_abstract.group(1).strip()) if latex_abstract else 0
        
        xml_abstract_elem = self.xml_root.find('.//ap:abstract', self.ns)
        xml_abstract_len = len(''.join(xml_abstract_elem.itertext()).strip()) if xml_abstract_elem is not None else 0
        
        # Store metadata analysis
        analysis_data['metadata'] = {
            'title': {'latex': latex_title, 'xml': xml_title},
            'authors': {'latex': latex_authors, 'xml': xml_authors},
            'abstract': {'latex_chars': latex_abstract_len, 'xml_chars': xml_abstract_len}
        }
        
        if output_format == 'text':
            print(f"✓ Title: LaTeX='{latex_title}' | XML='{xml_title}'")
            print(f"✓ Authors: LaTeX={latex_authors} | XML={xml_authors}")
            print(f"✓ Abstract: LaTeX={latex_abstract_len} chars | XML={xml_abstract_len} chars")
        
        # Check metadata completeness
        metadata_score = 0
        if xml_title and xml_title.strip() == latex_title.strip():
            metadata_score += 1
        elif xml_title:
            metadata_score += 0.5
            self.issues['Minor'].append("Title formatting differences")
        else:
            self.issues['Critical'].append("Title missing in XML")
        
        if xml_authors >= latex_authors and latex_authors > 0:
            metadata_score += 1
        elif xml_authors > 0:
            metadata_score += 0.8  # XML has authors, even if count differs
            if xml_authors < latex_authors:
                self.issues['Major'].append(f"Author count mismatch: LaTeX={latex_authors}, XML={xml_authors}")
        else:
            self.issues['Critical'].append("Authors missing in XML")
        
        if xml_abstract_len > 0:
            if abs(xml_abstract_len - latex_abstract_len) / max(latex_abstract_len, 1) < 0.1:
                metadata_score += 1
            else:
                metadata_score += 0.7
                self.issues['Minor'].append("Abstract length differs significantly")
        else:
            self.issues['Critical'].append("Abstract missing in XML")
        
        # 2. Document Structure
        if output_format == 'text':
            print("\n=== DOCUMENT STRUCTURE ANALYSIS ===")
            
        latex_sections = re.findall(r'\\section\{([^}]+)\}', self.latex_content)
        latex_subsections = re.findall(r'\\subsection\{([^}]+)\}', self.latex_content)
        
        xml_sections = self.xml_root.findall('.//ap:section', self.ns)
        xml_section_titles = []
        for section in xml_sections:
            title_elem = section.find('ap:title', self.ns)
            if title_elem is not None and title_elem.text:
                xml_section_titles.append(title_elem.text)
        
        # Store structure analysis
        analysis_data['structure'] = {
            'sections': {'latex': len(latex_sections), 'xml': len(xml_sections)},
            'subsections': {'latex': len(latex_subsections)},
            'section_titles': {'latex': latex_sections, 'xml': xml_section_titles}
        }
        
        if output_format == 'text':
            print(f"✓ Sections: LaTeX={len(latex_sections)} | XML={len(xml_sections)}")
            print(f"✓ Subsections: LaTeX={len(latex_subsections)}")
            print(f"✓ XML section titles found: {len(xml_section_titles)}")
        
        # Check section completeness
        structure_score = 0
        if len(xml_sections) == len(latex_sections) + len(latex_subsections):
            structure_score += 1
        elif len(xml_sections) > 0:
            structure_score += 0.5
            self.issues['Major'].append(f"Section count mismatch: LaTeX={len(latex_sections)+len(latex_subsections)}, XML={len(xml_sections)}")
        else:
            self.issues['Critical'].append("No sections found in XML")
        
        # Check if section titles match
        latex_all_titles = set(latex_sections + latex_subsections)
        xml_title_set = set(xml_section_titles)
        missing_titles = latex_all_titles - xml_title_set
        
        if missing_titles:
            self.issues['Major'].extend([f"Missing section: '{title}'" for title in list(missing_titles)[:5]])
            if len(missing_titles) > 5:
                self.issues['Major'].append(f"... and {len(missing_titles)-5} more missing sections")
        
        # 3. Mathematical Content
        print("\n=== MATHEMATICAL CONTENT ANALYSIS ===")
        latex_equations = len(re.findall(r'\\begin\{equation\}', self.latex_content))
        latex_inline_math = len(re.findall(r'\$[^$]+\$', self.latex_content))
        
        xml_equations = len(self.xml_root.findall('.//ap:equation', self.ns))
        xml_text = ET.tostring(self.xml_root, encoding='unicode')
        equation_placeholders = len(re.findall(r'\[EQUATION\]', xml_text))
        
        print(f"✓ Display equations: LaTeX={latex_equations} | XML={xml_equations}")
        print(f"✓ Inline math: LaTeX={latex_inline_math}")
        print(f"✓ Equation placeholders in XML: {equation_placeholders}")
        
        # Check mathematical content
        math_score = 0
        if latex_equations > 0:
            if xml_equations == latex_equations:
                math_score += 1
            elif equation_placeholders == latex_equations:
                math_score += 0.3
                self.issues['Major'].append(f"Equations converted to placeholders instead of MathML: {equation_placeholders}")
            else:
                self.issues['Critical'].append(f"Equation conversion failed: LaTeX={latex_equations}, XML={xml_equations}")
        else:
            math_score += 1  # No equations to convert
        
        if latex_inline_math > 0:
            # Check for inline math conversion (simplified check)
            if equation_placeholders > latex_equations:
                math_score += 0.3
                self.issues['Major'].append(f"Inline math may be converted to placeholders")
            else:
                self.issues['Major'].append(f"Inline math conversion unclear: {latex_inline_math} expressions")
        
        # 4. References and Citations
        print("\n=== REFERENCES AND CITATIONS ANALYSIS ===")
        latex_citations = len(re.findall(r'\\cite\{[^}]+\}', self.latex_content))
        latex_references = len(re.findall(r'\\bibitem\{[^}]+\}', self.latex_content))
        
        xml_citations = len(self.xml_root.findall('.//ap:citation', self.ns))
        xml_references = len(self.xml_root.findall('.//ap:reference', self.ns))
        
        unconverted_citations = len(re.findall(r'\\cite\{[^}]+\}', xml_text))
        
        print(f"✓ Citations: LaTeX={latex_citations} | XML={xml_citations}")
        print(f"✓ References: LaTeX={latex_references} | XML={xml_references}")
        print(f"✓ Unconverted citations in XML: {unconverted_citations}")
        
        # Check references and citations
        ref_score = 0
        if latex_references > 0:
            if xml_references == latex_references:
                ref_score += 0.5
            else:
                self.issues['Critical'].append(f"Bibliography missing: LaTeX={latex_references}, XML={xml_references}")
        else:
            ref_score += 0.5
        
        if latex_citations > 0:
            if xml_citations == latex_citations:
                ref_score += 0.5
            elif unconverted_citations > 0:
                self.issues['Major'].append(f"Citations not converted: {unconverted_citations} remain as LaTeX")
            else:
                self.issues['Critical'].append(f"All {latex_citations} citations missing")
        else:
            ref_score += 0.5
        
        # 5. Tables and Figures
        print("\n=== TABLES AND FIGURES ANALYSIS ===")
        latex_tables = len(re.findall(r'\\begin\{table\}', self.latex_content))
        latex_figures = len(re.findall(r'\\begin\{figure\}', self.latex_content))
        
        xml_tables = len(self.xml_root.findall('.//ap:table', self.ns))
        xml_figures = len(self.xml_root.findall('.//ap:figure', self.ns))
        
        print(f"✓ Tables: LaTeX={latex_tables} | XML={xml_tables}")
        print(f"✓ Figures: LaTeX={latex_figures} | XML={xml_figures}")
        
        # Check tables and figures
        table_fig_score = 0
        if latex_tables > 0:
            if xml_tables == latex_tables:
                table_fig_score += 0.5
            else:
                self.issues['Critical'].append(f"Tables missing: LaTeX={latex_tables}, XML={xml_tables}")
        else:
            table_fig_score += 0.5
        
        if latex_figures > 0:
            if xml_figures == latex_figures:
                table_fig_score += 0.5
            else:
                self.issues['Critical'].append(f"Figures missing: LaTeX={latex_figures}, XML={xml_figures}")
        else:
            table_fig_score += 0.5
        
        # Always check XML figures for image files
        if xml_figures > 0:
            self._check_figure_images()
        
        # Calculate overall completion percentage
        total_score = metadata_score + structure_score + math_score + ref_score + table_fig_score
        max_score = 6.0  # Maximum possible score
        completion = (total_score / max_score) * 100
        
        critical_count = len(self.issues['Critical'])
        major_count = len(self.issues['Major'])
        minor_count = len(self.issues['Minor'])
        
        # Generate summary
        print(f"\n{'='*50}")
        print("EXECUTIVE SUMMARY")
        print(f"{'='*50}")
        print(f"Overall Conversion Quality: {completion:.1f}%")
        print(f"Component Scores:")
        print(f"  📄 Metadata: {metadata_score:.1f}/3.0")
        print(f"  📑 Structure: {structure_score:.1f}/1.0")
        print(f"  🔢 Mathematics: {math_score:.1f}/1.0")
        print(f"  📚 References: {ref_score:.1f}/1.0")
        print(f"  📊 Tables/Figures: {table_fig_score:.1f}/1.0")
        print(f"Issues Found:")
        print(f"  🚨 Critical: {critical_count}")
        print(f"  ⚠️  Major: {major_count}")
        print(f"  💡 Minor: {minor_count}")
        
        if completion >= 85:
            quality = "🟢 EXCELLENT - High quality conversion"
        elif completion >= 70:
            quality = "🟡 GOOD - Acceptable with improvements needed"
        elif completion >= 50:
            quality = "🟠 MODERATE - Significant issues require attention"
        else:
            quality = "🔴 POOR - Major rework required"
        
        print(f"Quality Assessment: {quality}")
        
        # Show critical issues
        if self.issues['Critical']:
            print(f"\n🚨 CRITICAL ISSUES:")
            for i, issue in enumerate(self.issues['Critical'], 1):
                print(f"   {i}. {issue}")
        
        # Show major issues (limited)
        if self.issues['Major']:
            print(f"\n⚠️  MAJOR ISSUES:")
            for i, issue in enumerate(self.issues['Major'][:10], 1):
                print(f"   {i}. {issue}")
            if len(self.issues['Major']) > 10:
                print(f"   ... and {len(self.issues['Major'])-10} more")
        
        # Show minor issues (limited)
        if self.issues['Minor']:
            print(f"\n💡 MINOR ISSUES:")
            for i, issue in enumerate(self.issues['Minor'][:5], 1):
                print(f"   {i}. {issue}")
            if len(self.issues['Minor']) > 5:
                print(f"   ... and {len(self.issues['Minor'])-5} more")
        
        # Recommendations
        print(f"\n{'='*50}")
        print("PRIORITY RECOMMENDATIONS")
        print(f"{'='*50}")
        
        if critical_count > 0:
            print("1. 🚨 IMMEDIATE: Fix critical structural issues")
            print("   - Focus on missing core elements (tables, figures, references)")
        if major_count > 0:
            print("2. ⚠️  HIGH: Address major content conversion problems")
            print("   - Improve mathematical content handling")
            print("   - Fix section structure issues")
        if minor_count > 0:
            print("3. 💡 MEDIUM: Polish minor formatting issues")
        
        if critical_count == 0 and major_count <= 2:
            print("✅ Overall conversion quality is acceptable!")
        
        print(f"\n{'='*80}")
        
    def _check_figure_images(self):
        """Check if figures have image references and if image files exist"""
        figures = self.xml_root.findall('.//ap:figure', self.ns)
        
        for figure in figures:
            figure_id = figure.get('id', 'unknown')
            source_ref = figure.find('ap:source_reference', self.ns)
            
            if source_ref is None or not source_ref.text:
                self.issues['Major'].append(f"Figure {figure_id} missing source_reference")
                continue
            
            # Check if image file exists (assuming PNG format as per our implementation)
            image_filename = f"{source_ref.text}.png"
            image_path = Path(self.xml_file).parent / image_filename
            
            if not image_path.exists():
                self.issues['Major'].append(f"Figure {figure_id} image file not found: {image_filename}")
            else:
                print(f"✓ Figure {figure_id} image file exists: {image_filename}")
        
    def analyze_all_data(self):
        """Collect analysis data without printing"""
        # Run the same analysis but collect data
        
        # Metadata
        latex_title = self.parse_latex_title()
        xml_title_elem = self.xml_root.find('.//ap:title', self.ns)
        xml_title = xml_title_elem.text if xml_title_elem is not None else ""
        
        latex_authors = self.parse_latex_authors()
        xml_authors = len(self.xml_root.findall('.//ap:author', self.ns))
        
        latex_abstract = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', self.latex_content, re.DOTALL)
        latex_abstract_len = len(latex_abstract.group(1).strip()) if latex_abstract else 0
        xml_abstract_elem = self.xml_root.find('.//ap:abstract', self.ns)
        xml_abstract_len = len(''.join(xml_abstract_elem.itertext()).strip()) if xml_abstract_elem is not None else 0
        
        # Structure
        latex_sections = re.findall(r'\\section\{([^}]+)\}', self.latex_content)
        latex_subsections = re.findall(r'\\subsection\{([^}]+)\}', self.latex_content)
        xml_sections = self.xml_root.findall('.//ap:section', self.ns)
        
        # Math
        latex_equations = len(re.findall(r'\\begin\{equation\}', self.latex_content))
        latex_inline_math = len(re.findall(r'\$[^$]+\$', self.latex_content))
        xml_equations = len(self.xml_root.findall('.//ap:equation', self.ns))
        
        # References
        latex_citations = len(re.findall(r'\\cite\{[^}]+\}', self.latex_content))
        latex_references = len(re.findall(r'\\bibitem\{[^}]+\}', self.latex_content))
        xml_citations = len(self.xml_root.findall('.//ap:citation', self.ns))
        xml_references = len(self.xml_root.findall('.//ap:reference', self.ns))
        
        # Tables and Figures
        latex_tables = len(re.findall(r'\\begin\{table\}', self.latex_content))
        latex_figures = len(re.findall(r'\\begin\{figure\}', self.latex_content))
        xml_tables = len(self.xml_root.findall('.//ap:table', self.ns))
        xml_figures = len(self.xml_root.findall('.//ap:figure', self.ns))
        
        return {
            'metadata': {
                'title': {'latex': latex_title, 'xml': xml_title},
                'authors': {'latex': latex_authors, 'xml': xml_authors},
                'abstract': {'latex_chars': latex_abstract_len, 'xml_chars': xml_abstract_len}
            },
            'structure': {
                'sections': {'latex': len(latex_sections), 'xml': len(xml_sections)},
                'subsections': {'latex': len(latex_subsections)}
            },
            'mathematics': {
                'equations': {'latex': latex_equations, 'xml': xml_equations},
                'inline_math': {'latex': latex_inline_math}
            },
            'references': {
                'citations': {'latex': latex_citations, 'xml': xml_citations},
                'bibliography': {'latex': latex_references, 'xml': xml_references}
            },
            'tables_figures': {
                'tables': {'latex': latex_tables, 'xml': xml_tables},
                'figures': {'latex': latex_figures, 'xml': xml_figures}
            }
        }
    
    def output_json(self, analysis_data):
        """Output analysis results as JSON"""
        
        # Calculate final scores and summary
        critical_count = len(self.issues['Critical'])
        major_count = len(self.issues['Major'])
        minor_count = len(self.issues['Minor'])
        
        # Calculate component scores (simplified for JSON)
        metadata_score = 2.5 if analysis_data['metadata']['title']['xml'] else 0
        structure_score = 0.5 if analysis_data['structure']['sections']['xml'] > 0 else 0
        math_score = 1.0 if analysis_data['mathematics']['equations']['latex'] == 0 else 0.3
        ref_score = 0.0 if analysis_data['references']['citations']['latex'] > 0 else 0.5
        table_fig_score = 0.0 if (analysis_data['tables_figures']['tables']['latex'] > 0 or 
                                 analysis_data['tables_figures']['figures']['latex'] > 0) else 1.0
        
        total_score = metadata_score + structure_score + math_score + ref_score + table_fig_score
        completion = (total_score / 6.0) * 100
        
        # Determine quality level
        if completion >= 85:
            quality = "EXCELLENT"
        elif completion >= 70:
            quality = "GOOD"
        elif completion >= 50:
            quality = "MODERATE"
        else:
            quality = "POOR"
        
        # Build JSON structure
        result = {
            "overall_score": round(completion, 1),
            "analysis": analysis_data,
            "issues": self.issues['Critical'] + self.issues['Major'] + self.issues['Minor'],
            "summary": {
                "completion_percentage": round(completion, 1),
                "quality_level": quality,
                "issue_counts": {
                    "critical": critical_count,
                    "major": major_count,
                    "minor": minor_count
                },
                "component_scores": {
                    "metadata": round(metadata_score, 1),
                    "structure": round(structure_score, 1),
                    "mathematics": round(math_score, 1),
                    "references": round(ref_score, 1),
                    "tables_figures": round(table_fig_score, 1)
                }
            }
        }
        
        return json.dumps(result, indent=2)

if __name__ == "__main__":
    
    if len(sys.argv) < 3:
        print("Usage: python3 review_structure.py <latex_file> <xml_file> [--json]")
        sys.exit(1)
    
    latex_file, xml_file = sys.argv[1], sys.argv[2]
    output_json = '--json' in sys.argv
    
    reviewer = StructuralReviewer(latex_file, xml_file)
    
    if output_json:
        # Collect data without printing
        analysis_data = reviewer.analyze_all_data()
        print(reviewer.output_json(analysis_data))
    else:
        # Standard text output
        results = reviewer.analyze_all('text')
