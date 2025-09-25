#!/usr/bin/env python3
import argparse
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

class LatexToXmlConverter:
    def __init__(self):
        self.schema_file = Path(__file__).parent / "academic_paper_schema.xsd"
        self.prompt_template_file = Path(__file__).parent / "prompt_template.txt"
        self.xml_sample_file = Path(__file__).parent / "xml_sample.xml"
        self.max_attempts = 3
    
    def convert_latex_to_xml(self, latex_file, output_xml=None):
        """Convert LaTeX file to XML using Q Developer CLI with validation loop"""
        
        latex_path = Path(latex_file)
        if not latex_path.exists():
            raise FileNotFoundError(f"LaTeX file not found: {latex_file}")
        
        if output_xml is None:
            output_xml = latex_path.stem + ".xml"
        
        output_path = Path(output_xml)
        
        print(f"🚀 Converting LaTeX to XML using Q Developer CLI")
        print(f"📄 Input: {latex_file}")
        print(f"📄 Output: {output_xml}")
        print()
        
        # Read template files
        schema_content = self._read_file(self.schema_file)
        prompt_template = self._read_file(self.prompt_template_file)
        xml_sample = self._read_file(self.xml_sample_file)
        
        # Validation loop
        for attempt in range(1, self.max_attempts + 1):
            print(f"🔄 Attempt {attempt}/{self.max_attempts}")
            
            if attempt == 1:
                success = self._initial_conversion(latex_path, output_path, prompt_template, schema_content, xml_sample)
            else:
                # Get validation error from previous attempt
                error_msg = self._validate_xml(output_path)
                success = self._fix_conversion(latex_path, output_path, schema_content, error_msg)
            
            if success:
                print(f"✅ Successfully converted: {output_xml}")
                return output_path
            
            print(f"❌ Attempt {attempt} failed")
        
        raise RuntimeError(f"Failed to convert LaTeX to valid XML after {self.max_attempts} attempts")
    
    def _initial_conversion(self, latex_path, output_path, prompt_template, schema_content, xml_sample):
        """Initial LaTeX-to-XML conversion using Q Developer CLI"""
        
        prompt = prompt_template.format(
            latex_file=latex_path,
            output_file=output_path,
            schema_content=schema_content,
            xml_sample=xml_sample
        )
        
        return self._run_q_developer(prompt)
    
    def _fix_conversion(self, latex_path, output_path, schema_content, error_msg):
        """Fix XML conversion based on validation error"""
        
        prompt = f"""The XML conversion of '{latex_path}' failed validation. Please fix the XML file '{output_path}' to resolve the following error:

VALIDATION ERROR:
{error_msg}

REQUIREMENTS:
1. Read the current XML file '{output_path}'
2. Fix the validation error while preserving all content
3. Ensure the XML complies with the academic paper schema
4. Write the corrected XML back to '{output_path}'

XML SCHEMA:
{schema_content}

Please fix the XML file to make it valid against the schema."""
        
        return self._run_q_developer(prompt)
    
    def _run_q_developer(self, prompt):
        """Run Q Developer CLI with the given prompt"""
        
        try:
            cmd = ['q', 'chat', '--no-interactive', '--trust-all-tools', prompt]
            
            print(f"🤖 Running Q Developer CLI...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                print(f"❌ Q Developer CLI failed: {result.stderr}")
                return False
            
            print(f"📝 Q Developer response received")
            return True
            
        except subprocess.TimeoutExpired:
            print("❌ Q Developer CLI timed out")
            return False
        except Exception as e:
            print(f"❌ Error running Q Developer CLI: {e}")
            return False
    
    def _validate_xml(self, xml_path):
        """Validate XML against schema, return error message or None if valid"""
        
        if not xml_path.exists():
            return f"XML file does not exist: {xml_path}"
        
        try:
            # Parse XML
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Basic validation checks
            ns = {'ap': 'http://example.com/academic-paper'}
            
            # Check root element
            if not root.tag.endswith('}paper'):
                return f"Root element should be 'paper', found: {root.tag}"
            
            # Check required elements
            metadata = root.find('.//ap:metadata', ns)
            if metadata is None:
                return "Missing required 'metadata' element"
            
            title = metadata.find('ap:title', ns)
            if title is None or not title.text:
                return "Missing or empty 'title' element in metadata"
            
            authors = metadata.find('ap:authors', ns)
            if authors is None:
                return "Missing required 'authors' element in metadata"
            
            author_list = authors.findall('ap:author', ns)
            if not author_list:
                return "At least one author is required"
            
            sections = root.find('.//ap:sections', ns)
            if sections is None:
                return "Missing required 'sections' element"
            
            section_list = sections.findall('ap:section', ns)
            if not section_list:
                return "At least one section is required"
            
            # Check section attributes
            for section in section_list:
                if not section.get('id'):
                    return "Section missing required 'id' attribute"
                if not section.get('level'):
                    return "Section missing required 'level' attribute"
            
            print(f"✅ XML validation passed: {xml_path}")
            
            # Show summary
            print(f"📋 Title: {title.text}")
            print(f"📋 Authors: {len(author_list)}")
            print(f"📋 Sections: {len(section_list)}")
            
            return None
            
        except ET.ParseError as e:
            return f"XML parse error: {e}"
        except Exception as e:
            return f"Validation error: {e}"
    
    def _read_file(self, file_path):
        """Read file content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise RuntimeError(f"Could not read file {file_path}: {e}")

def main():
    """LaTeX-to-XML conversion with Q Developer CLI"""
    parser = argparse.ArgumentParser(description='Convert LaTeX file to XML using Q Developer CLI')
    parser.add_argument('latex_file', help='Path to the LaTeX file to convert')
    parser.add_argument('-o', '--output', help='Output XML file path (default: input_name.xml)')
    
    args = parser.parse_args()
    
    latex_file = args.latex_file
    output_file = args.output
    
    if not Path(latex_file).exists():
        print(f"❌ LaTeX file not found: {latex_file}")
        return
    
    converter = LatexToXmlConverter()
    
    print("🚀 LaTeX-to-XML Converter using Q Developer CLI")
    print("=" * 60)
    print("✨ Features: Template-based prompts, comprehensive XML sample, schema validation loop")
    print()
    
    try:
        output_path = converter.convert_latex_to_xml(latex_file, output_file)
        
        file_size = output_path.stat().st_size
        print()
        print(f"📊 Generated XML: {file_size:,} bytes")
        print(f"📁 Output file: {output_path}")
        print("🎉 LaTeX-to-XML conversion complete!")
        
    except Exception as e:
        print(f"❌ Conversion failed: {e}")

if __name__ == '__main__':
    main()
