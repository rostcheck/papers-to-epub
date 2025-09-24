#!/usr/bin/env python3
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

class LatexToXmlConverter:
    def __init__(self):
        self.schema_file = Path(__file__).parent / "academic_paper_schema.xsd"
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
        
        # Read schema content
        schema_content = self._read_schema()
        
        # Validation loop
        for attempt in range(1, self.max_attempts + 1):
            print(f"🔄 Attempt {attempt}/{self.max_attempts}")
            
            if attempt == 1:
                success = self._initial_conversion(latex_path, output_path, schema_content)
            else:
                # Get validation error from previous attempt
                error_msg = self._validate_xml(output_path)
                success = self._fix_conversion(latex_path, output_path, schema_content, error_msg)
            
            if success:
                print(f"✅ Successfully converted: {output_xml}")
                return output_path
            
            print(f"❌ Attempt {attempt} failed")
        
        raise RuntimeError(f"Failed to convert LaTeX to valid XML after {self.max_attempts} attempts")
    
    def _initial_conversion(self, latex_path, output_path, schema_content):
        """Initial LaTeX-to-XML conversion using Q Developer CLI"""
        
        prompt = f"""Please read the LaTeX file '{latex_path}' and convert it to XML format that complies with the provided academic paper schema.

REQUIREMENTS:
1. Read and parse the entire LaTeX file
2. Extract title, authors (with affiliations and emails), abstract, all sections and subsections
3. Convert LaTeX math expressions to proper MathML format
4. Use XHTML formatting for text content (paragraphs, emphasis, etc.)
5. Create valid XML that validates against the schema
6. Write the complete XML to '{output_path}'

XML SCHEMA:
{schema_content}

EXAMPLE STRUCTURE:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<paper xmlns="http://example.com/academic-paper"
       xmlns:xhtml="http://www.w3.org/1999/xhtml"
       xmlns:mathml="http://www.w3.org/1998/Math/MathML">
  <metadata>
    <title>Paper Title</title>
    <authors>
      <author>
        <name>Author Name</name>
        <affiliation>Institution</affiliation>
        <email>email@example.com</email>
      </author>
    </authors>
    <abstract>
      <xhtml:p>Abstract content...</xhtml:p>
    </abstract>
  </metadata>
  <sections>
    <section id="intro" level="1">
      <title>Introduction</title>
      <content>
        <xhtml:p>Content with <xhtml:em>emphasis</xhtml:em> and math:
          <mathml:math display="inline">
            <mathml:mi>x</mathml:mi>
            <mathml:mo>=</mathml:mo>
            <mathml:mi>y</mathml:mi>
          </mathml:math>
        </xhtml:p>
      </content>
    </section>
  </sections>
</paper>
```

Please create the complete XML file with all content from the LaTeX paper."""
        
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
    
    def _read_schema(self):
        """Read the XML schema file"""
        try:
            with open(self.schema_file, 'r') as f:
                return f.read()
        except Exception as e:
            raise RuntimeError(f"Could not read schema file {self.schema_file}: {e}")

def main():
    """Test LaTeX-to-XML conversion with Q Developer CLI"""
    converter = LatexToXmlConverter()
    
    # Default to Word2Vec LaTeX file
    latex_file = "../../LaTeX/efficient-v22.tex"
    output_file = "word2vec_from_latex.xml"
    
    if not Path(latex_file).exists():
        print(f"❌ LaTeX file not found: {latex_file}")
        print("Please specify the path to a LaTeX file")
        return
    
    print("🚀 LaTeX-to-XML Converter using Q Developer CLI")
    print("=" * 60)
    print("✨ Features: Q Developer cognitive parsing, MathML conversion, schema validation loop")
    print()
    
    try:
        output_path = converter.convert_latex_to_xml(latex_file, output_file)
        
        file_size = output_path.stat().st_size
        print()
        print(f"📊 Generated XML: {file_size:,} bytes")
        print(f"📁 Output file: {output_path}")
        print("🎉 LaTeX-to-XML conversion complete!")
        
        # Test the XML-to-ePub pipeline
        print()
        print("🔄 Testing XML-to-ePub conversion...")
        try:
            from xml_to_epub import XmlToEpubConverter
            epub_converter = XmlToEpubConverter()
            epub_path = epub_converter.convert_xml_to_epub(output_path)
            print(f"📚 Generated ePub: {epub_path}")
            print("🎉 Complete LaTeX → XML → ePub pipeline successful!")
        except Exception as e:
            print(f"⚠️ ePub conversion failed: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
