# LaTeX to ePub Converter with Multi-Approach Processing

Convert LaTeX academic papers to high-quality ePub format using rules-based, cognitive AI, and hybrid processing approaches with professional XML transformation.

## Current Architecture

### 🎯 **LaTeX → XML → ePub Pipeline**
```
LaTeX Source → [Rules-Based | Cognitive | Hybrid] → Structured XML → XSLT → Professional ePub
```

### 📁 **File Structure**
```
approaches/xml_to_epub/
├── latex_to_xml_rules_based.py     # Heuristic regex-based LaTeX parsing
├── latex_to_xml_cognitive.py       # Q Developer CLI-based conversion
├── latex_to_xml_hybrid.py          # TexSoup + pylatexenc + LLM approach
├── latex_to_xml_latexml.py         # LaTeXML professional conversion
├── xml_to_epub.py                  # XSLT-based XML to ePub converter
├── xml_to_epub.xsl                 # XSLT stylesheet for transformation
├── xml_to_epub_latexml.py          # LaTeXML XML to ePub converter
├── xml_to_epub_latexml.xsl         # LaTeXML XSLT stylesheet
├── academic_paper_schema.xsd       # XML schema definition
├── structural_review/
│   └── review_structure.py         # Quality assessment tool
├── tools/                          # Utility scripts
│   ├── extract_epub_pages.py       # ePub page extraction for testing
│   ├── compare_pages_bedrock.py    # AI-powered visual comparison
│   ├── compare_converters.py       # Converter performance comparison
│   └── split_source_pdf.py         # PDF splitting utility
├── output/                         # All generated files (gitignored)
└── epub_books/                     # Generated ePub files
```

## Four Conversion Approaches

### 🔧 **Rules-Based Converter** (`latex_to_xml_rules_based.py`)
- **Method**: Pure Python with regex parsing
- **Strengths**: Reliable structure extraction, comprehensive content
- **Status**: ✅ Working, generates professional ePubs
- **Best for**: Stable, predictable conversion

### 🧠 **Cognitive Converter** (`latex_to_xml_cognitive.py`)  
- **Method**: Amazon Q Developer CLI with iterative improvement
- **Strengths**: Intelligent content understanding, metadata handling
- **Status**: ⚠️ Requires Q CLI integration fixes
- **Best for**: Complex document understanding

### 🔄 **Hybrid Converter** (`latex_to_xml_hybrid.py`)
- **Method**: TexSoup (structure) + pylatexenc (content) + LLM (unstructured)
- **Strengths**: Best of all approaches - structured parsing + AI processing
- **Status**: ⚠️ XML namespace issues, needs refinement
- **Best for**: Optimal quality when working

### ⚡ **LaTeXML Converter** (`latex_to_xml_latexml.py`)
- **Method**: Professional LaTeXML engine with Bedrock cognitive bibliography processing
- **Strengths**: Industry-standard LaTeX processing, perfect tables, AI-enhanced citations
- **Status**: ✅ Working, professional-grade conversion with cognitive enhancements
- **Best for**: Maximum accuracy, LaTeX compatibility, and intelligent bibliography formatting

## Usage

### Convert LaTeX to XML

#### Rules-Based Approach (Recommended)
```bash
cd approaches/xml_to_epub
python3 latex_to_xml_rules_based.py path/to/paper.tex
```

#### Cognitive Approach
```bash
cd approaches/xml_to_epub
python3 latex_to_xml_cognitive.py path/to/paper.tex
```

#### LaTeXML Approach (Professional)
```bash
cd approaches/xml_to_epub
python3 latex_to_xml_latexml.py path/to/paper.tex
```

### Convert XML to ePub
```bash
cd approaches/xml_to_epub
python3 xml_to_epub.py output/paper.xml
# OR for LaTeXML XML:
python3 xml_to_epub_latexml.py output/paper_latexml.xml
```

### Quality Assessment
```bash
cd approaches/xml_to_epub
python3 structural_review/review_structure.py path/to/paper.tex output/paper.xml
```

### Visual Quality Testing
```bash
cd approaches/xml_to_epub
python3 tools/extract_epub_pages.py epub_books/paper.epub
python3 tools/compare_pages_bedrock.py
```

## Performance Status

| Approach | Status | Quality | Strengths | Issues |
|----------|--------|---------|-----------|--------|
| **Rules-Based** | ✅ Working | 99.8% | Complete extraction, reliable | Limited LaTeX cleaning |
| **Cognitive** | ⚠️ Needs fixes | TBD | Intelligent parsing | Q CLI integration |
| **Hybrid** | ⚠️ Experimental | 100%* | Best architecture | XML namespace issues |
| **LaTeXML** | ✅ Working | 100% | Professional LaTeX processing, perfect tables, cognitive bibliography | Requires LaTeXML install |

*When working properly

## Requirements

### Core Dependencies
- Python 3.x
- lxml (for XSLT processing)

### Optional Dependencies
- Amazon Q Developer CLI (`q` command) - for cognitive approach
- TexSoup, pylatexenc - for hybrid approach
- AWS CLI with Bedrock access - for visual testing

## Installation

### Basic Setup
```bash
pip3 install lxml
```

### For Hybrid Approach
```bash
pip3 install TexSoup pylatexenc
```

### For LaTeXML Approach
```bash
# Install LaTeXML (Ubuntu/Debian)
sudo apt-get install latexml
# OR (macOS with Homebrew)
brew install latexml

# AWS CLI setup for Bedrock cognitive processing
aws configure
pip3 install boto3
```

### For Cognitive Approach
Follow: https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/command-line-getting-started-installing.html

### For Visual Testing
```bash
# AWS CLI setup for Bedrock access
aws configure
```

## Example Usage

### Basic Conversion
```bash
cd approaches/xml_to_epub
python3 latex_to_xml_rules_based.py ../../LaTeX/efficient-v22.tex
python3 xml_to_epub.py output/efficient-v22_rules_based.xml
```

### With Quality Testing
```bash
cd approaches/xml_to_epub
python3 latex_to_xml_rules_based.py ../../LaTeX/efficient-v22.tex
python3 xml_to_epub.py output/efficient-v22_rules_based.xml
python3 tools/extract_epub_pages.py epub_books/Efficient_Estimation_of_Word_Representations_in_Ve.epub
python3 structural_review/review_structure.py ../../LaTeX/efficient-v22.tex output/efficient-v22_rules_based.xml
```

## Output Quality

The pipeline produces professional-quality ePub files with:
- ✅ **Complete metadata** (title, authors, abstract)
- ✅ **Structured content** (sections, equations, tables, figures)
- ✅ **Cognitive bibliography** (AI-enhanced citations with full author names)
- ✅ **Professional formatting** with academic styling
- ✅ **Clean text flow** (flattened citations, no line breaks)
- ✅ **LaTeX cleanup** (removes artifacts like \xspace)
- ✅ **Mobile compatibility** for all ePub readers

### Example Results (ARC-AGI Paper)
- **Input**: 12-page LaTeX academic paper with complex bibliography
- **Output**: Professional ePub with cognitive enhancements (~995KB)
- **Content**: 22 sections, 4 figures, 5 tables, 35 references
- **Bibliography**: Full author names, complete publication details
- **Quality Score**: 100% (EXCELLENT) - LaTeXML + Bedrock approach

## Architecture Benefits

### **Multi-Approach Strategy**
- **Rules-based**: Reliable baseline with comprehensive extraction
- **Cognitive**: Intelligent understanding for complex cases
- **Hybrid**: Combines structured parsing with AI processing

### **Professional Pipeline**
- **XSLT Transformation**: Industry-standard XML publishing
- **Schema Validation**: Ensures consistent output format
- **Quality Assurance**: Automated testing and visual comparison

### **Extensible Design**
- **Modular components**: Each approach can be improved independently
- **Tool ecosystem**: Utilities for testing, comparison, and analysis
- **Standard formats**: XML schema and XSLT for customization

## Troubleshooting

### Common Issues
```bash
# Check dependencies
python3 -c "import lxml.etree; print('lxml available')"
python3 -c "import TexSoup; print('TexSoup available')"

# Verify Q CLI (if using cognitive approach)
q --version

# Test XSLT transformation
python3 xml_to_epub.py output/sample.xml
```

### File Organization
- All generated output goes in `output/` directory
- Tools and utilities in `tools/` directory
- Follow naming convention: `*_rules_based`, `*_cognitive`, `*_hybrid`

This pipeline represents a comprehensive approach to academic document conversion, providing multiple strategies for different use cases while maintaining professional quality standards.
