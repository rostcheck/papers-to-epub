# PDF to ePub Converter with AI-Enhanced Quality Pipeline

Convert PDF research papers to high-quality ePub format with intelligent quality analysis and automated fixes.

## What it does

This advanced tool converts PDF files to ePub format with a sophisticated quality pipeline that automatically detects and fixes common formatting issues. Features include:

- **Dual Processing Paths**: Standard conversion for good PDFs, AI-enhanced processing for problematic ones
- **Quality Detection**: Automated analysis of PDF suitability and ePub formatting issues
- **AI-Powered Content Restructuring**: Uses Claude to reconstruct fragmented or screenshot-based PDFs
- **Smart Title Extraction**: AWS Bedrock intelligently extracts clean titles from academic papers
- **Automated Quality Fixes**: Removes repeated footers, fixes TOC placement, cleans formatting
- **Mobile-Optimized Output**: Reflowable text, adjustable fonts, better battery life

## Key Features

### 🔍 **PDF Quality Detection**
- Identifies web screenshots, image-based PDFs, and fragmented content
- Analyzes text extraction quality and academic paper indicators
- Routes to appropriate processing pipeline automatically

### 🤖 **AI-Enhanced Processing**
- **Claude Integration**: Restructures fragmented content into coherent documents
- **Bedrock Quality Analysis**: Detects formatting issues using specific examples
- **Smart Content Cleaning**: Preserves legitimate content while removing artifacts

### ✅ **Quality Assurance**
- **Automated Issue Detection**: TOC problems, repeated footers, broken formatting
- **Iterative Improvement**: Multiple quality check and fix cycles
- **Zero-Issue Goal**: Achieves professional-quality ePub output

## Requirements

- Python 3.x
- Calibre (for ebook-convert)
- AWS credentials with Bedrock access (Claude Sonnet, Nova Micro)
- Required Python packages: PyPDF2, boto3, beautifulsoup4

## Installation

### Python packages
```bash
pip3 install PyPDF2 boto3 beautifulsoup4
```

### Calibre

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y calibre
```

#### macOS
```bash
brew install calibre
```

#### Windows
Download and install Calibre from https://calibre-ebook.com/download

### AWS Setup
Configure AWS credentials with access to:
- `us.anthropic.claude-3-5-sonnet-20241022-v2:0` (for content restructuring)
- `amazon.nova-micro-v1:0` (for title extraction and quality analysis)

## Usage

### Standard Conversion
```bash
python3 improved_convert_to_epub.py
```

### Quality Analysis Only
```bash
python3 epub_quality_analyzer.py
```

### AI-Powered Quality Analysis
```bash
python3 bedrock_quality_analyzer.py
```

## Pipeline Flow

```
PDF Input → Quality Detection → Processing Route
    ↓                              ↓
📊 Analysis Report           🔀 Route Decision
    ↓                              ↓
Standard Path                 Enhanced Path
    ↓                              ↓
📚 Calibre Conversion        🤖 Claude Restructuring
    ↓                              ↓
🧹 Content Cleaning          📖 Structured ePub Creation
    ↓                              ↓
📑 TOC Reconstruction        ✅ Quality Validation
    ↓                              ↓
✅ Quality Validation ← ← ← ← ← Final ePub Output
```

## Output Quality

The enhanced pipeline achieves:
- **Zero formatting issues** for most conversions
- **Professional document structure** with meaningful sections
- **Clean, readable content** free from artifacts
- **Proper table of contents** placement and navigation

### Example Results

**Before Enhancement:**
```
Found 3 issues:
- MAJOR: TOC has meaningless entries ("1", ".2", "↩")
- MAJOR: Repeated footer content appears 10 times
- MINOR: Tables converted to images
```

**After Enhancement:**
```
✓ No quality issues detected
✓ Professional document structure
✓ Clean, coherent content
```

## File Structure

- `improved_convert_to_epub.py` - Main enhanced pipeline
- `pdf_quality_detector.py` - Pre-conversion PDF analysis
- `claude_pdf_extractor.py` - AI-powered content restructuring
- `epub_quality_analyzer.py` - Rule-based quality detection
- `bedrock_quality_analyzer.py` - AI-powered formatting analysis
- `toc_fixer.py` - Table of contents improvement
- `quality_instructions.md` - Quality evaluation criteria

## Supported Readers

Converted ePub files work with:
- Kindle app
- Apple Books
- Google Play Books
- Adobe Digital Editions
- Any ePub-compatible reader

### Uploading to Kindle

Upload ePub files directly to your Kindle library:
https://www.amazon.com/sendtokindle

## Example Output

```
=== Processing: research_paper.pdf ===
PDF Quality Check: ✓ Suitable
Text: 15,420 chars, Academic score: 8/9

✓ Converted and improved: research_paper.pdf → Clean Research Title.epub
  Title: Clean Research Title

--- Quality Check (Iteration 1) ---
✓ No quality issues detected

--- Applying TOC Improvements ---
✓ TOC fixed

--- Final Quality Check ---
✓ No quality issues detected

Conversion complete: High-quality ePub ready for mobile reading
```
