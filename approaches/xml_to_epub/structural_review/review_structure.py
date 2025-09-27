#!/usr/bin/env python3
"""
Structural Quality Assurance Review
LaTeX to XML Conversion Analysis with unified scoring system
"""

import re
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from xml.etree import ElementTree as ET
from collections import defaultdict

class StructuralReviewer:
    """
    Unified structural quality assessment for LaTeX to XML conversion.
    Uses bottom-up component architecture with consistent scoring.
    """
    
    def __init__(self, latex_file: str, xml_file: str):
        self.latex_file = latex_file
        self.xml_file = xml_file
        self.latex_content = ""
        self.xml_root = None
        self.ns = {'ap': 'http://example.com/academic-paper'}
        self.issues = defaultdict(list)
        
        self._load_files()
    
    def _load_files(self) -> None:
        """Load and expand LaTeX files, then load XML"""
        try:
            self.latex_content = self._expand_latex(self.latex_file)
            self.xml_root = ET.parse(self.xml_file).getroot()
        except Exception as e:
            raise ValueError(f"Failed to load files: {e}")
    
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
                return match.group(0)
        
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
    
    # Low-level collection functions
    def collect_metadata_metrics(self) -> Dict[str, Any]:
        """Collect metadata comparison metrics"""
        # LaTeX metadata
        latex_title = self._extract_latex_title()
        latex_authors = self._extract_latex_authors()
        latex_abstract = self._extract_latex_abstract()
        
        # XML metadata
        xml_title = self._extract_xml_title()
        xml_authors = self._extract_xml_authors()
        xml_abstract = self._extract_xml_abstract()
        
        return {
            'title': {
                'latex': latex_title,
                'xml': xml_title,
                'match': latex_title == xml_title
            },
            'authors': {
                'latex': len(latex_authors),
                'xml': len(xml_authors),
                'match_ratio': len(xml_authors) / max(len(latex_authors), 1)
            },
            'abstract': {
                'latex_chars': len(latex_abstract),
                'xml_chars': len(xml_abstract),
                'match_ratio': min(len(xml_abstract), len(latex_abstract)) / max(len(latex_abstract), 1) if len(latex_abstract) > 0 else 0
            }
        }
    
    def collect_structure_metrics(self) -> Dict[str, Any]:
        """Collect document structure metrics"""
        # LaTeX structure
        latex_sections = self._extract_latex_sections()
        latex_subsections = self._extract_latex_subsections()
        
        # XML structure
        xml_sections = self._extract_xml_sections()
        
        return {
            'sections': {
                'latex': len(latex_sections),
                'xml': len(xml_sections),
                'match_ratio': min(len(xml_sections), len(latex_sections)) / max(len(latex_sections), 1)
            },
            'subsections': {
                'latex': len(latex_subsections)
            }
        }
    
    def collect_mathematics_metrics(self) -> Dict[str, Any]:
        """Collect mathematical content metrics"""
        # LaTeX math
        latex_equations = self._extract_latex_equations()
        latex_inline_math = self._extract_latex_inline_math()
        
        # XML math
        xml_equations = self._extract_xml_equations()
        
        return {
            'equations': {
                'latex': len(latex_equations),
                'xml': len(xml_equations),
                'match_ratio': min(len(xml_equations), len(latex_equations)) / max(len(latex_equations), 1)
            },
            'inline_math': {
                'latex': len(latex_inline_math)
            }
        }
    
    def collect_references_metrics(self) -> Dict[str, Any]:
        """Collect references and citations metrics"""
        # LaTeX references
        latex_citations = self._extract_latex_citations()
        latex_bibliography = self._extract_latex_bibliography()
        
        # XML references
        xml_citations = self._extract_xml_citations()
        xml_bibliography = self._extract_xml_bibliography()
        
        return {
            'citations': {
                'latex': len(latex_citations),
                'xml': len(xml_citations),
                'match_ratio': min(len(xml_citations), len(latex_citations)) / max(len(latex_citations), 1)
            },
            'bibliography': {
                'latex': len(latex_bibliography),
                'xml': len(xml_bibliography),
                'match_ratio': min(len(xml_bibliography), len(latex_bibliography)) / max(len(latex_bibliography), 1)
            }
        }
    
    def collect_tables_figures_metrics(self) -> Dict[str, Any]:
        """Collect tables and figures metrics"""
        # LaTeX tables/figures
        latex_tables = self._extract_latex_tables()
        latex_figures = self._extract_latex_figures()
        
        # XML tables/figures
        xml_tables = self._extract_xml_tables()
        xml_figures = self._extract_xml_figures()
        
        return {
            'tables': {
                'latex': len(latex_tables),
                'xml': len(xml_tables),
                'match_ratio': min(len(xml_tables), len(latex_tables)) / max(len(latex_tables), 1)
            },
            'figures': {
                'latex': len(latex_figures),
                'xml': len(xml_figures),
                'match_ratio': min(len(xml_figures), len(latex_figures)) / max(len(latex_figures), 1)
            }
        }
    
    # Unified scoring function
    def calculate_component_scores(self) -> Dict[str, float]:
        """Calculate standardized component scores (0.0 to 1.0)"""
        metadata = self.collect_metadata_metrics()
        structure = self.collect_structure_metrics()
        mathematics = self.collect_mathematics_metrics()
        references = self.collect_references_metrics()
        tables_figures = self.collect_tables_figures_metrics()
        
        # Calculate component scores with weighted sub-components
        scores = {
            'metadata': (
                (1.0 if metadata['title']['match'] else 0.0) * 0.3 +
                metadata['authors']['match_ratio'] * 0.4 +
                metadata['abstract']['match_ratio'] * 0.3
            ),
            'structure': structure['sections']['match_ratio'],
            'mathematics': mathematics['equations']['match_ratio'],
            'references': (
                references['citations']['match_ratio'] * 0.6 +
                references['bibliography']['match_ratio'] * 0.4
            ),
            'tables_figures': (
                tables_figures['tables']['match_ratio'] * 0.6 +
                tables_figures['figures']['match_ratio'] * 0.4
            )
        }
        
        return scores
    
    def calculate_overall_score(self, component_scores: Dict[str, float]) -> float:
        """Calculate overall quality score from component scores"""
        # Weighted average of components
        weights = {
            'metadata': 0.25,
            'structure': 0.20,
            'mathematics': 0.15,
            'references': 0.20,
            'tables_figures': 0.20
        }
        
        weighted_sum = sum(component_scores[component] * weights[component] 
                          for component in weights)
        
        return weighted_sum * 100  # Convert to percentage
    
    def assess_quality_level(self, overall_score: float) -> str:
        """Determine quality level from overall score"""
        if overall_score >= 85:
            return "EXCELLENT"
        elif overall_score >= 70:
            return "GOOD"
        elif overall_score >= 50:
            return "MODERATE"
        else:
            return "POOR"
    
    def generate_analysis_report(self) -> Dict[str, Any]:
        """Generate complete analysis report with unified scoring"""
        # Collect all metrics
        metadata = self.collect_metadata_metrics()
        structure = self.collect_structure_metrics()
        mathematics = self.collect_mathematics_metrics()
        references = self.collect_references_metrics()
        tables_figures = self.collect_tables_figures_metrics()
        
        # Calculate scores
        component_scores = self.calculate_component_scores()
        overall_score = self.calculate_overall_score(component_scores)
        quality_level = self.assess_quality_level(overall_score)
        
        # Build comprehensive report
        return {
            'overall_score': round(overall_score, 1),
            'quality_level': quality_level,
            'component_scores': {k: round(v, 2) for k, v in component_scores.items()},
            'detailed_metrics': {
                'metadata': metadata,
                'structure': structure,
                'mathematics': mathematics,
                'references': references,
                'tables_figures': tables_figures
            },
            'issues': list(self.issues.get('major', [])) + list(self.issues.get('minor', []))
        }
    
    def output_json(self) -> str:
        """Output analysis as JSON"""
        report = self.generate_analysis_report()
        
        # Format for compatibility with existing tools
        formatted_report = {
            'overall_score': report['overall_score'],
            'analysis': {
                'metadata': {
                    'title': {
                        'latex': report['detailed_metrics']['metadata']['title']['latex'],
                        'xml': report['detailed_metrics']['metadata']['title']['xml']
                    },
                    'authors': {
                        'latex': report['detailed_metrics']['metadata']['authors']['latex'],
                        'xml': report['detailed_metrics']['metadata']['authors']['xml']
                    },
                    'abstract': {
                        'latex_chars': report['detailed_metrics']['metadata']['abstract']['latex_chars'],
                        'xml_chars': report['detailed_metrics']['metadata']['abstract']['xml_chars']
                    }
                },
                'structure': {
                    'sections': {
                        'latex': report['detailed_metrics']['structure']['sections']['latex'],
                        'xml': report['detailed_metrics']['structure']['sections']['xml']
                    },
                    'subsections': {
                        'latex': report['detailed_metrics']['structure']['subsections']['latex']
                    }
                },
                'mathematics': {
                    'equations': {
                        'latex': report['detailed_metrics']['mathematics']['equations']['latex'],
                        'xml': report['detailed_metrics']['mathematics']['equations']['xml']
                    },
                    'inline_math': {
                        'latex': report['detailed_metrics']['mathematics']['inline_math']['latex']
                    }
                },
                'references': {
                    'citations': {
                        'latex': report['detailed_metrics']['references']['citations']['latex'],
                        'xml': report['detailed_metrics']['references']['citations']['xml']
                    },
                    'bibliography': {
                        'latex': report['detailed_metrics']['references']['bibliography']['latex'],
                        'xml': report['detailed_metrics']['references']['bibliography']['xml']
                    }
                },
                'tables_figures': {
                    'tables': {
                        'latex': report['detailed_metrics']['tables_figures']['tables']['latex'],
                        'xml': report['detailed_metrics']['tables_figures']['tables']['xml']
                    },
                    'figures': {
                        'latex': report['detailed_metrics']['tables_figures']['figures']['latex'],
                        'xml': report['detailed_metrics']['tables_figures']['figures']['xml']
                    }
                }
            },
            'issues': report['issues'],
            'summary': {
                'completion_percentage': report['overall_score'],
                'quality_level': report['quality_level'],
                'issue_counts': {
                    'critical': 0,
                    'major': len([i for i in report['issues'] if 'major' in str(i).lower()]),
                    'minor': len([i for i in report['issues'] if 'minor' in str(i).lower()])
                },
                'component_scores': report['component_scores']
            }
        }
        
        return json.dumps(formatted_report, indent=2, ensure_ascii=False)
    
    def output_text(self) -> str:
        """Output analysis as formatted text report"""
        report = self.generate_analysis_report()
        
        lines = []
        lines.append("=" * 80)
        lines.append("STRUCTURAL QUALITY ASSURANCE REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Metadata section
        metadata = report['detailed_metrics']['metadata']
        lines.append("=== METADATA ANALYSIS ===")
        lines.append(f"✓ Title: LaTeX='{metadata['title']['latex']}' | XML='{metadata['title']['xml']}'")
        lines.append(f"✓ Authors: LaTeX={metadata['authors']['latex']} | XML={metadata['authors']['xml']}")
        lines.append(f"✓ Abstract: LaTeX={metadata['abstract']['latex_chars']} chars | XML={metadata['abstract']['xml_chars']} chars")
        lines.append("")
        
        # Structure section
        structure = report['detailed_metrics']['structure']
        lines.append("=== DOCUMENT STRUCTURE ANALYSIS ===")
        lines.append(f"✓ Sections: LaTeX={structure['sections']['latex']} | XML={structure['sections']['xml']}")
        lines.append(f"✓ Subsections: LaTeX={structure['subsections']['latex']}")
        lines.append("")
        
        # Mathematics section
        mathematics = report['detailed_metrics']['mathematics']
        lines.append("=== MATHEMATICAL CONTENT ANALYSIS ===")
        lines.append(f"✓ Display equations: LaTeX={mathematics['equations']['latex']} | XML={mathematics['equations']['xml']}")
        lines.append(f"✓ Inline math: LaTeX={mathematics['inline_math']['latex']}")
        lines.append("")
        
        # References section
        references = report['detailed_metrics']['references']
        lines.append("=== REFERENCES AND CITATIONS ANALYSIS ===")
        lines.append(f"✓ Citations: LaTeX={references['citations']['latex']} | XML={references['citations']['xml']}")
        lines.append(f"✓ References: LaTeX={references['bibliography']['latex']} | XML={references['bibliography']['xml']}")
        lines.append("")
        
        # Tables/Figures section
        tables_figures = report['detailed_metrics']['tables_figures']
        lines.append("=== TABLES AND FIGURES ANALYSIS ===")
        lines.append(f"✓ Tables: LaTeX={tables_figures['tables']['latex']} | XML={tables_figures['tables']['xml']}")
        lines.append(f"✓ Figures: LaTeX={tables_figures['figures']['latex']} | XML={tables_figures['figures']['xml']}")
        lines.append("")
        
        # Summary
        lines.append("=" * 50)
        lines.append("EXECUTIVE SUMMARY")
        lines.append("=" * 50)
        lines.append(f"Overall Conversion Quality: {report['overall_score']}%")
        lines.append("Component Scores:")
        for component, score in report['component_scores'].items():
            lines.append(f"  📊 {component.title()}: {score:.2f}")
        lines.append(f"Quality Assessment: {report['quality_level']}")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    # Private extraction methods for LaTeX
    def _extract_latex_title(self) -> str:
        match = re.search(r'\\title\{([^}]+)\}', self.latex_content)
        return match.group(1) if match else ""
    
    def _extract_latex_authors(self) -> List[str]:
        author_match = re.search(r'\\author\{(.*?)\}', self.latex_content, re.DOTALL)
        if author_match:
            author_content = author_match.group(1)
            author_parts = re.split(r'\\And|\\AND', author_content)
            return [part.strip().split('\\\\')[0].strip() for part in author_parts if part.strip()]
        return []
    
    def _extract_latex_abstract(self) -> str:
        match = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', self.latex_content, re.DOTALL)
        return match.group(1).strip() if match else ""
    
    def _extract_latex_sections(self) -> List[str]:
        return re.findall(r'\\section\{([^}]+)\}', self.latex_content)
    
    def _extract_latex_subsections(self) -> List[str]:
        return re.findall(r'\\subsection\{([^}]+)\}', self.latex_content)
    
    def _extract_latex_equations(self) -> List[str]:
        patterns = [
            r'\\begin\{equation\}(.*?)\\end\{equation\}',
            r'\\begin\{align\}(.*?)\\end\{align\}',
            r'\\begin\{eqnarray\}(.*?)\\end\{eqnarray\}'
        ]
        equations = []
        for pattern in patterns:
            equations.extend(re.findall(pattern, self.latex_content, re.DOTALL))
        return equations
    
    def _extract_latex_inline_math(self) -> List[str]:
        return re.findall(r'\$([^$]+)\$', self.latex_content)
    
    def _extract_latex_citations(self) -> List[str]:
        citations = []
        matches = re.finditer(r'\\cite\{([^}]+)\}', self.latex_content)
        for match in matches:
            cite_keys = match.group(1).split(',')
            citations.extend([key.strip() for key in cite_keys])
        return list(set(citations))
    
    def _extract_latex_bibliography(self) -> List[str]:
        bibitem_pattern = r'\\bibitem\{([^}]+)\}'
        return re.findall(bibitem_pattern, self.latex_content)
    
    def _extract_latex_tables(self) -> List[str]:
        return re.findall(r'\\begin\{table\}(.*?)\\end\{table\}', self.latex_content, re.DOTALL)
    
    def _extract_latex_figures(self) -> List[str]:
        return re.findall(r'\\begin\{figure\}(.*?)\\end\{figure\}', self.latex_content, re.DOTALL)
    
    # Private extraction methods for XML
    def _extract_xml_title(self) -> str:
        title_elem = self.xml_root.find('.//ap:title', self.ns)
        return title_elem.text if title_elem is not None else ""
    
    def _extract_xml_authors(self) -> List[str]:
        authors = self.xml_root.findall('.//ap:author', self.ns)
        return [author.find('ap:name', self.ns).text for author in authors 
                if author.find('ap:name', self.ns) is not None]
    
    def _extract_xml_abstract(self) -> str:
        abstract_elem = self.xml_root.find('.//ap:abstract', self.ns)
        return ''.join(abstract_elem.itertext()).strip() if abstract_elem is not None else ""
    
    def _extract_xml_sections(self) -> List[str]:
        sections = self.xml_root.findall('.//ap:section', self.ns)
        return [section.find('ap:title', self.ns).text for section in sections 
                if section.find('ap:title', self.ns) is not None]
    
    def _extract_xml_equations(self) -> List[str]:
        equations = self.xml_root.findall('.//ap:equation', self.ns)
        return [eq.text for eq in equations if eq.text]
    
    def _extract_xml_citations(self) -> List[str]:
        citations = self.xml_root.findall('.//ap:citation', self.ns)
        return [cite.text for cite in citations if cite.text]
    
    def _extract_xml_bibliography(self) -> List[str]:
        refs = self.xml_root.findall('.//ap:reference', self.ns)
        return [ref.get('id', '') for ref in refs if ref.get('id')]
    
    def _extract_xml_tables(self) -> List[str]:
        tables = self.xml_root.findall('.//ap:table', self.ns)
        return [table.get('id', '') for table in tables]
    
    def _extract_xml_figures(self) -> List[str]:
        figures = self.xml_root.findall('.//ap:figure', self.ns)
        return [figure.get('id', '') for figure in figures]


def main():
    """Command-line interface"""
    if len(sys.argv) < 3:
        print("Usage: python3 review_structure.py <latex_file> <xml_file> [--json]")
        sys.exit(1)
    
    latex_file, xml_file = sys.argv[1], sys.argv[2]
    output_json = '--json' in sys.argv
    
    try:
        reviewer = StructuralReviewer(latex_file, xml_file)
        
        if output_json:
            print(reviewer.output_json())
        else:
            print(reviewer.output_text())
    
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
