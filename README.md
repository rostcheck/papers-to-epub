# LaTeX to ePub Converter with AI-Enhanced Processing

Convert LaTeX academic papers to high-quality ePub format using cognitive AI processing and professional XML transformation.

## What it does

This advanced tool converts LaTeX academic papers to professional ePub format using a sophisticated pipeline that combines AI cognitive processing with industry-standard XML transformation. Features include:

- **Cognitive LaTeX Processing**: Uses Amazon Q Developer CLI to intelligently parse LaTeX structure
- **Schema-Validated XML**: Converts to structured XML format with automatic validation
- **Professional XSLT Transformation**: Industry-standard XML-to-XHTML conversion
- **MathML Support**: Proper mathematical expression rendering in ePub readers
- **Validation Loop**: Automatic error detection and correction
- **Mobile-Optimized Output**: Professional ePub format for all devices

## Pipeline Architecture

### 🎯 **LaTeX → XML → ePub Pipeline**
```
LaTeX Source → Q Developer CLI → Structured XML → Schema Validation → XSLT → Professional ePub
```

### 🤖 **Cognitive Processing**
- **Q Developer CLI**: Intelligently parses LaTeX structure and content
- **Schema Compliance**: Generates XML that validates against academic paper schema
- **Auto-Correction**: Validation loop fixes errors automatically

### 🎨 **Professional Output**
- **XSLT Transformation**: Industry-standard XML-to-XHTML conversion
- **MathML Rendering**: Proper mathematical expressions in ePub readers
- **Academic Formatting**: Professional layout with proper sections, TOC, references

## Requirements

- Python 3.x
- Amazon Q Developer CLI (`q` command)
- lxml (for XSLT processing)
- Required Python packages: xml, pathlib, subprocess

## Installation

### Amazon Q Developer CLI
Follow the installation guide at: https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/command-line-getting-started-installing.html

### Python packages
```bash
pip3 install lxml
```

### Verify Q CLI Installation
```bash
q --version
```

## Usage

### Convert LaTeX to ePub

#### Method 1: Convert Specific LaTeX File
```bash
cd approaches/xml_to_epub
python3 latex_to_xml.py path/to/your/paper.tex
```

#### Method 2: Convert with Custom Output Name
```bash
cd approaches/xml_to_epub
python3 latex_to_xml.py path/to/your/paper.tex -o custom_output.xml
```

#### Method 3: Convert Word2Vec Example
```bash
cd approaches/xml_to_epub
python3 latex_to_xml.py ../../LaTeX/efficient-v22.tex
```

This will:
1. Use Q Developer CLI to convert LaTeX to XML
2. Validate XML against schema (with auto-fix if needed)
3. Automatically generate ePub using XSLT transformation

#### Method 4: XML to ePub Only
If you already have XML:
```bash
cd approaches/xml_to_epub
python3 xml_to_epub.py your_file.xml
```

### Pipeline Components

#### 1. LaTeX-to-XML Converter (`latex_to_xml.py`)
- Uses Q Developer CLI for cognitive LaTeX parsing
- Generates schema-compliant XML
- Includes validation loop with auto-correction
- Handles complex LaTeX structures, math expressions, citations

**Command-line options:**
```bash
python3 latex_to_xml.py <latex_file> [-o OUTPUT_FILE]

Arguments:
  latex_file          Path to the LaTeX file to convert
  -o, --output        Output XML file path (default: input_name.xml)
```

#### 2. XML-to-ePub Converter (`xml_to_epub.py`)
- Professional XSLT-based transformation
- Generates valid ePub3 format
- Includes CSS styling for academic papers
- Supports MathML rendering

**Command-line options:**
```bash
python3 xml_to_epub.py <xml_file>

Arguments:
  xml_file            Path to the XML file to convert
```

#### 3. XML Schema (`academic_paper_schema.xsd`)
- Defines structure for academic papers
- Supports XHTML and MathML content
- Validates metadata, sections, equations, references

## Output Quality

The pipeline produces professional-quality ePub files with:
- ✅ **Complete metadata** (title, authors, affiliations, emails)
- ✅ **Proper document structure** (sections, subsections, TOC)
- ✅ **Mathematical expressions** rendered as MathML
- ✅ **Professional formatting** with academic styling
- ✅ **Mobile compatibility** for all ePub readers

### Example Results

**Input**: LaTeX academic paper (e.g., Word2Vec paper)
**Output**: Professional ePub with:
- Complete author information (4 authors with affiliations)
- Structured content (8+ sections with proper hierarchy)
- Mathematical expressions properly rendered
- Professional academic formatting
- File size: ~12-15KB (highly optimized)

## File Structure

```
approaches/xml_to_epub/
├── latex_to_xml.py              # Q Developer CLI LaTeX converter
├── xml_to_epub.py               # XSLT-based ePub generator
├── xml_to_epub.xsl              # XSLT stylesheet for transformation
├── academic_paper_schema.xsd    # XML schema definition
├── word2vec_test.xml            # Example XML structure
└── epub_books/                  # Generated ePub files
```

## Supported Readers

Generated ePub files work with:
- Kindle app
- Apple Books
- Google Play Books
- Adobe Digital Editions
- Any ePub3-compatible reader

### Uploading to Kindle

Upload ePub files directly to your Kindle library:
https://www.amazon.com/sendtokindle

## Example Usage

```bash
# Convert Word2Vec LaTeX paper to ePub
cd approaches/xml_to_epub
python3 latex_to_xml.py ../../LaTeX/efficient-v22.tex

# Output files:
# - word2vec_from_latex.xml (structured XML)
# - epub_books/Efficient_Estimation_of_Word_Representations_in_Ve.epub
```

## Pipeline Features

### 🔍 **Cognitive Processing**
- Q Developer CLI understands LaTeX structure semantically
- Extracts titles, authors, sections, equations, references
- Converts LaTeX math to proper MathML
- Handles complex document hierarchies

### ✅ **Quality Assurance**
- XML schema validation ensures consistent structure
- Validation loop automatically fixes errors
- XSLT transformation guarantees valid XHTML output
- Professional academic formatting

### 🎨 **Professional Output**
- Industry-standard XSLT transformation
- Proper MathML for mathematical expressions
- Academic paper styling with CSS
- Mobile-optimized ePub3 format

## Troubleshooting

### Q Developer CLI Issues
```bash
# Verify Q CLI is installed and working
q --version

# Test basic functionality
q chat --no-interactive --trust-all-tools "Hello, please create a test file"
```

### XML Validation Errors
The pipeline includes automatic error correction, but if issues persist:
1. Check the XML schema file exists
2. Verify LaTeX file is properly formatted
3. Review Q Developer CLI output for errors

### XSLT Transformation Issues
```bash
# Verify lxml is installed
python3 -c "import lxml.etree; print('lxml available')"

# Test XSLT transformation manually
python3 xml_to_epub.py
```

## Advanced Usage

### Custom XML Schema
Modify `academic_paper_schema.xsd` to support additional document types or structures.

### Custom XSLT Styling
Edit `xml_to_epub.xsl` to customize the ePub appearance and formatting.

### Batch Processing
```python
from latex_to_xml import LatexToXmlConverter
converter = LatexToXmlConverter()

papers = ['paper1.tex', 'paper2.tex', 'paper3.tex']
for paper in papers:
    converter.convert_latex_to_xml(paper)
```

## Architecture Benefits

### **Structured Pipeline**
- **LaTeX → XML**: Preserves semantic meaning from source
- **XML → ePub**: Professional transformation using industry standards
- **Validation**: Ensures quality at each stage

### **Cognitive Processing**
- **Q Developer CLI**: Understands document structure intelligently
- **Schema Validation**: Guarantees consistent output format
- **Auto-Correction**: Fixes errors automatically

### **Professional Quality**
- **XSLT Transformation**: Industry-standard XML publishing
- **MathML Support**: Proper mathematical expression rendering
- **Academic Formatting**: Professional layout and styling

This pipeline represents the state-of-the-art in academic document conversion, combining AI cognitive processing with professional publishing standards.
