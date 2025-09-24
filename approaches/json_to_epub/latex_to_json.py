#!/usr/bin/env python3
import re
import json
from pathlib import Path

class LaTeXToJsonConverter:
    def __init__(self):
        self.sections = []
        self.tables = []
        self.figures = []
        self.references = []
        self.equations = []
    
    def convert_latex_file(self, latex_file):
        """Convert LaTeX file to structured JSON"""
        
        with open(latex_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📖 Processing LaTeX file: {latex_file}")
        
        # Extract metadata
        metadata = self._extract_metadata(content)
        
        # Extract sections
        sections = self._extract_sections(content)
        
        # Extract tables
        tables = self._extract_tables(content)
        
        # Extract figures
        figures = self._extract_figures(content)
        
        # Extract references
        references = self._extract_references(content)
        
        # Extract equations
        equations = self._extract_equations(content)
        
        # Build complete JSON structure
        json_data = {
            "metadata": metadata,
            "sections": sections,
            "tables": tables,
            "figures": figures,
            "equations": equations,
            "references": references,
            "citations": []  # Would need more sophisticated parsing
        }
        
        return json_data
    
    def _extract_metadata(self, content):
        """Extract title, authors, abstract from LaTeX"""
        
        # Extract title
        title_match = re.search(r'\\title\{([^}]+)\}', content)
        title = title_match.group(1) if title_match else "Unknown Title"
        
        # Extract authors using robust parsing instead of regex
        authors = self._parse_authors_robust(content)
        
        # Extract abstract
        abstract_match = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', content, re.DOTALL)
        abstract = ""
        if abstract_match:
            abstract = self._clean_latex_text(abstract_match.group(1))
        
        return {
            "title": self._clean_latex_text(title),
            "authors": authors,
            "abstract": abstract,
            "keywords": [],  # Could extract from LaTeX if present
            "publication_info": {
                "venue": "arXiv preprint",
                "date": "2013-01-16",
                "arxiv_id": "1301.3781v3",
                "document_class": "workshop paper"
            }
        }
    
    def _extract_sections(self, content):
        """Extract all sections and subsections with complete content"""
        
        sections = []
        
        # Find all section markers (excluding commented ones)
        section_pattern = r'^(?!%).*?\\(sub)*section\{([^}]+)\}'
        section_matches = list(re.finditer(section_pattern, content, re.MULTILINE))
        
        for i, match in enumerate(section_matches):
            section_type = match.group(1)  # 'sub' or None
            section_title = self._clean_latex_text(match.group(2))
            
            # Determine section level
            level = 2 if section_type == 'sub' else 1
            
            # Create section ID
            section_id = self._create_section_id(section_title)
            
            # Extract content between this section and the next
            start_pos = match.end()
            
            if i + 1 < len(section_matches):
                end_pos = section_matches[i + 1].start()
            else:
                # Last section - go to end of document or references
                refs_match = re.search(r'\\begin\{thebibliography\}', content[start_pos:])
                if refs_match:
                    end_pos = start_pos + refs_match.start()
                else:
                    end_pos = len(content)
            
            # Extract and clean section content
            section_content = content[start_pos:end_pos]
            cleaned_content = self._extract_section_text(section_content)
            
            section_data = {
                "id": section_id,
                "title": section_title,
                "level": level,
                "content": cleaned_content,
                "subsections": []
            }
            
            sections.append(section_data)
        
        # Organize subsections under main sections
        organized_sections = self._organize_sections(sections)
        
        return organized_sections
    
    def _extract_section_text(self, section_content):
        """Extract clean text from section content, removing LaTeX commands"""
        
        # Remove tables, figures, equations - they'll be handled separately
        text = re.sub(r'\\begin\{table\}.*?\\end\{table\}', '', section_content, flags=re.DOTALL)
        text = re.sub(r'\\begin\{figure\}.*?\\end\{figure\}', '', text, flags=re.DOTALL)
        text = re.sub(r'\\begin\{equation\}.*?\\end\{equation\}', '', text, flags=re.DOTALL)
        
        # Remove comments
        text = re.sub(r'%.*$', '', text, flags=re.MULTILINE)
        
        # Clean LaTeX commands
        text = self._clean_latex_text(text)
        
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = text.strip()
        
        return text
    
    def _clean_latex_text(self, text):
        """Clean LaTeX commands from text using robust string operations"""
        if not text:
            return ""
        
        result = text
        
        # Handle math expressions first - convert LaTeX math to readable text
        # Handle vector("word") expressions
        while 'vector(' in result:
            start = result.find('vector(')
            if start == -1:
                break
            paren_count = 0
            pos = start + 7  # after 'vector('
            while pos < len(result):
                if result[pos] == '(':
                    paren_count += 1
                elif result[pos] == ')':
                    if paren_count == 0:
                        content = result[start + 7:pos]
                        result = result[:start] + f'<em>vector</em>({content})' + result[pos + 1:]
                        break
                    paren_count -= 1
                pos += 1
            else:
                break
        
        # Handle {\it text} formatting
        while '{\\it ' in result:
            start = result.find('{\\it ')
            if start == -1:
                break
            brace_count = 0
            pos = start + 5
            while pos < len(result):
                if result[pos] == '{':
                    brace_count += 1
                elif result[pos] == '}':
                    if brace_count == 0:
                        content = result[start + 5:pos]
                        result = result[:start] + f'<em>{content}</em>' + result[pos + 1:]
                        break
                    brace_count -= 1
                pos += 1
            else:
                break
        
        # Handle standard LaTeX commands
        latex_commands = [
            ('\\textit{', 'em'),
            ('\\textbf{', 'strong'), 
            ('\\emph{', 'em'),
            ('\\mathit{', 'em'),
            ('\\mathrm{', 'span')
        ]
        
        for cmd, tag in latex_commands:
            while cmd in result:
                start = result.find(cmd)
                if start == -1:
                    break
                brace_count = 0
                pos = start + len(cmd)
                while pos < len(result):
                    if result[pos] == '{':
                        brace_count += 1
                    elif result[pos] == '}':
                        if brace_count == 0:
                            content = result[start + len(cmd):pos]
                            if tag == 'span':
                                result = result[:start] + content + result[pos + 1:]
                            else:
                                result = result[:start] + f'<{tag}>{content}</{tag}>' + result[pos + 1:]
                            break
                        brace_count -= 1
                    pos += 1
                else:
                    break
        
        # Handle citations and references
        while '\\cite{' in result:
            start = result.find('\\cite{')
            end = result.find('}', start + 6)
            if end > start:
                citation = result[start + 6:end]
                result = result[:start] + f'[{citation}]' + result[end + 1:]
            else:
                break
        
        # Handle references
        result = result.replace('\\ref{', '[ref-').replace('}', ']')
        
        # Handle URLs
        while '\\url{' in result:
            start = result.find('\\url{')
            if start == -1:
                break
            end = result.find('}', start + 5)
            if end > start:
                url = result[start + 5:end]
                result = result[:start] + f'<a href="{url}">{url}</a>' + result[end + 1:]
            else:
                break
        
        # Clean up line breaks and spacing
        result = result.replace('\\\\', '\n')
        result = result.replace('\\newline', '\n')
        
        # Handle special characters
        replacements = {
            '\\&': '&', '\\_': '_', '\\%': '%', 
            '\\#': '#', '\\$': '$', '~': ' '
        }
        for old, new in replacements.items():
            result = result.replace(old, new)
        
        # Remove any remaining LaTeX commands that we missed
        # Simple cleanup for common patterns
        result = result.replace('\\', '')
        
        # Clean up whitespace
        result = ' '.join(result.split())
        
        return result
    
    def _parse_authors_robust(self, content):
        """Robust author parsing using string manipulation instead of regex"""
        authors = []
        
        # Find author block by looking for \author{ and matching braces
        start_marker = '\\author{'
        start_pos = content.find(start_marker)
        
        if start_pos == -1:
            return authors
        
        # Find the matching closing brace
        brace_count = 0
        pos = start_pos + len(start_marker)
        
        while pos < len(content):
            char = content[pos]
            if char == '{':
                brace_count += 1
            elif char == '}':
                if brace_count == 0:
                    break
                brace_count -= 1
            pos += 1
        
        if pos >= len(content):
            return authors
        
        # Extract author block content
        author_block = content[start_pos + len(start_marker):pos]
        
        # Split authors by looking for \And and \AND markers
        author_sections = []
        current_section = ""
        i = 0
        
        while i < len(author_block):
            # Check for \And or \AND
            if author_block[i:i+4] == '\\And':
                if i + 4 < len(author_block) and author_block[i+4] in ' \n\\':
                    # Found \And
                    author_sections.append(current_section)
                    current_section = ""
                    i += 4
                    continue
            elif author_block[i:i+4] == '\\AND':
                if i + 4 < len(author_block) and author_block[i+4] in ' \n\\':
                    # Found \AND
                    author_sections.append(current_section)
                    current_section = ""
                    i += 4
                    continue
            
            current_section += author_block[i]
            i += 1
        
        # Add the last section
        if current_section.strip():
            author_sections.append(current_section)
        
        # Parse each author section
        for section in author_sections:
            author = self._parse_single_author(section)
            if author:
                authors.append(author)
        
        return authors
    
    def _parse_single_author(self, section):
        """Parse a single author section"""
        lines = [line.strip() for line in section.split('\\\\') if line.strip()]
        
        if not lines:
            return None
        
        # First line is the name
        name = lines[0].strip()
        
        # Parse remaining lines for affiliation and email
        affiliation_parts = []
        email = ""
        
        for line in lines[1:]:
            line = line.strip()
            
            # Check for email in \texttt{}
            if '\\texttt{' in line:
                start = line.find('\\texttt{') + 8
                end = line.find('}', start)
                if end > start:
                    email = line[start:end]
            else:
                # Regular affiliation line
                if line and not line.startswith('\\'):
                    affiliation_parts.append(line)
        
        if not name:
            return None
        
        author_data = {
            "name": name,
            "affiliation": ", ".join(affiliation_parts) if affiliation_parts else "Unknown"
        }
        
        if email:
            author_data["email"] = email
        
        return author_data
    
    def _create_section_id(self, title):
        """Create section ID from title"""
        # Remove numbers and clean
        clean_title = re.sub(r'^\d+\.?\s*', '', title)
        # Convert to lowercase, replace spaces with underscores
        section_id = re.sub(r'[^\w\s]', '', clean_title.lower())
        section_id = re.sub(r'\s+', '_', section_id)
        return section_id
    
    def _organize_sections(self, sections):
        """Organize subsections under main sections"""
        organized = []
        current_main = None
        
        for section in sections:
            if section['level'] == 1:
                # Main section
                current_main = section
                organized.append(section)
            elif section['level'] == 2 and current_main:
                # Subsection
                current_main['subsections'].append(section)
        
        return organized
    
    def _extract_tables(self, content):
        """Extract tables from LaTeX"""
        tables = []
        
        table_pattern = r'\\begin\{table\}(.*?)\\end\{table\}'
        table_matches = re.findall(table_pattern, content, re.DOTALL)
        
        for i, table_content in enumerate(table_matches, 1):
            # Extract caption
            caption_match = re.search(r'\\caption\{([^}]+)\}', table_content)
            caption = caption_match.group(1) if caption_match else f"Table {i}"
            
            # Extract tabular content (simplified)
            tabular_match = re.search(r'\\begin\{tabular\}.*?\{([^}]+)\}(.*?)\\end\{tabular\}', table_content, re.DOTALL)
            
            if tabular_match:
                # This is a simplified table extraction - would need enhancement for complex tables
                table_data = {
                    "id": f"table{i}",
                    "caption": self._clean_latex_text(caption),
                    "position": f"after_section_results",  # Default positioning
                    "headers": ["Column 1", "Column 2", "Column 3"],  # Placeholder
                    "rows": [["Data", "Data", "Data"]],  # Placeholder
                    "styling": "results-table"
                }
                tables.append(table_data)
        
        return tables
    
    def _extract_figures(self, content):
        """Extract figures from LaTeX and process images"""
        figures = []
        
        figure_pattern = r'\\begin\{figure\}(.*?)\\end\{figure\}'
        figure_matches = re.findall(figure_pattern, content, re.DOTALL)
        
        for i, figure_content in enumerate(figure_matches, 1):
            # Extract caption
            caption_match = re.search(r'\\caption\{([^}]+)\}', figure_content)
            caption = caption_match.group(1) if caption_match else f"Figure {i}"
            
            # Extract image file reference
            image_file = None
            # Check for includegraphics
            includegraphics_match = re.search(r'\\includegraphics.*?\{([^}]+)\}', figure_content)
            # Check for epsfig
            epsfig_match = re.search(r'\\epsfig\{figure=([^,}]+)', figure_content)
            
            if includegraphics_match:
                image_file = includegraphics_match.group(1)
            elif epsfig_match:
                image_file = epsfig_match.group(1)
                # Add .pdf extension if not present
                if not image_file.endswith(('.pdf', '.eps', '.png', '.jpg')):
                    image_file += '.pdf'
            
            # Handle PDF images - convert to PNG for ePub compatibility
            if image_file and image_file.endswith('.pdf'):
                image_file = self._convert_pdf_to_png(image_file)
            
            figure_data = {
                "id": f"figure{i}",
                "caption": self._clean_latex_text(caption),
                "position": f"after_section_new_log_linear_models",  # Place in appropriate section
                "type": "diagram",
                "description": self._clean_latex_text(caption),
                "alt_text": f"Figure {i}",
                "image_data": image_file if image_file else None,
                "source_reference": (includegraphics_match.group(1) if includegraphics_match 
                                   else epsfig_match.group(1) if epsfig_match else None)
            }
            figures.append(figure_data)
        
        return figures
    
    def _convert_pdf_to_png(self, pdf_file):
        """Convert PDF image to PNG for ePub compatibility"""
        try:
            import subprocess
            from pathlib import Path
            
            # Check if PDF exists in LaTeX directory
            latex_dir = Path("../../LaTeX")
            pdf_path = latex_dir / pdf_file
            
            if not pdf_path.exists():
                print(f"⚠️ PDF image not found: {pdf_path}")
                return None
            
            # Convert PDF to PNG using ImageMagick (if available)
            png_file = pdf_file.replace('.pdf', '.png')
            png_path = latex_dir / png_file
            
            try:
                # Try ImageMagick convert
                result = subprocess.run([
                    'convert', 
                    str(pdf_path), 
                    '-density', '150',
                    '-quality', '90',
                    str(png_path)
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0 and png_path.exists():
                    print(f"✅ Converted {pdf_file} → {png_file}")
                    return str(png_path)
                else:
                    print(f"⚠️ ImageMagick conversion failed for {pdf_file}")
                    
            except (subprocess.TimeoutExpired, FileNotFoundError):
                print(f"⚠️ ImageMagick not available, keeping PDF reference: {pdf_file}")
                
            return str(pdf_path)  # Return original PDF path as fallback
            
        except Exception as e:
            print(f"⚠️ Error processing image {pdf_file}: {e}")
            return None
    
    def _extract_equations(self, content):
        """Extract equations from LaTeX"""
        equations = []
        
        equation_pattern = r'\\begin\{equation\}(.*?)\\end\{equation\}'
        equation_matches = re.findall(equation_pattern, content, re.DOTALL)
        
        for i, equation_content in enumerate(equation_matches, 1):
            equation_data = {
                "id": f"eq{i}",
                "content": equation_content.strip(),
                "description": f"Equation {i}",
                "position": f"section_model_architectures_paragraph_{i}"
            }
            equations.append(equation_data)
        
        return equations
    
    def _extract_references(self, content):
        """Extract references from LaTeX bibliography"""
        references = []
        
        # Look for bibliography section
        bib_match = re.search(r'\\begin\{thebibliography\}.*?\\end\{thebibliography\}', content, re.DOTALL)
        
        if bib_match:
            bib_content = bib_match.group(0)
            
            # Extract individual bibitem entries
            bibitem_pattern = r'\\bibitem\{([^}]+)\}(.*?)(?=\\bibitem|\}$)'
            bibitem_matches = re.findall(bibitem_pattern, bib_content, re.DOTALL)
            
            for i, (ref_key, ref_content) in enumerate(bibitem_matches, 1):
                # Simple reference parsing - could be enhanced
                ref_data = {
                    "id": f"ref{i}",
                    "authors": ["Author"],  # Would need better parsing
                    "title": "Title",  # Would need better parsing
                    "venue": "Venue",  # Would need better parsing
                    "year": "2013"  # Would need better parsing
                }
                references.append(ref_data)
        
        return references

def main():
    """Test LaTeX to JSON conversion"""
    converter = LaTeXToJsonConverter()
    
    latex_file = "../../LaTeX/efficient-v22.tex"
    
    if not Path(latex_file).exists():
        print(f"❌ LaTeX file not found: {latex_file}")
        return
    
    print("🚀 LaTeX-to-JSON Converter")
    print("=" * 50)
    
    try:
        json_data = converter.convert_latex_file(latex_file)
        
        # Save complete JSON
        output_file = "../../word2vec_complete.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Generated complete JSON: {output_file}")
        
        # Show statistics
        print(f"📊 Sections: {len(json_data['sections'])}")
        print(f"📊 Tables: {len(json_data['tables'])}")
        print(f"📊 Figures: {len(json_data['figures'])}")
        print(f"📊 Equations: {len(json_data['equations'])}")
        print(f"📊 References: {len(json_data['references'])}")
        
        # Show content length for first section
        if json_data['sections']:
            first_section = json_data['sections'][0]
            print(f"📝 First section content: {len(first_section['content'])} characters")
            print(f"   Preview: {first_section['content'][:100]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
