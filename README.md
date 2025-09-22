# PDF to ePub Converter

Convert PDF research papers to ePub format for better mobile reading experience.

## What it does

This tool converts PDF files to ePub format using Calibre's `ebook-convert` utility. ePub files are optimized for mobile devices with:
- Reflowable text that adapts to screen size
- Adjustable font size and style
- Better battery life than PDF viewing
- Bookmarks and search functionality

**Smart Title Extraction**: Uses AWS Bedrock's Nova Micro model to intelligently extract clean, readable titles from academic papers, even when PDF metadata is missing or contains cryptic codes like "arXiv:2502.14297v2".

## Requirements

- Python 3.x
- Calibre (for ebook-convert)
- AWS credentials with Bedrock access
- PyPDF2 and boto3 Python packages

## Installation

### Python packages
```bash
pip3 install -r requirements.txt
```

### Calibre

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y calibre
```

### macOS
```bash
brew install calibre
```

### Windows
Download and install Calibre from https://calibre-ebook.com/download

## Usage

1. Place your PDF files in the project directory (or subdirectories)
2. Run the conversion script:
```bash
python3 convert_to_epub.py
```

The script will:
- Find all PDF files recursively
- Convert each to ePub format
- Save results in the `epub_books/` directory

## Output

Converted ePub files can be transferred to mobile devices and opened in:
- Kindle app
- Apple Books
- Google Play Books
- Any ePub-compatible reader

### Uploading to Kindle

You can upload ePub files directly to your Kindle library at:
https://www.amazon.com/sendtokindle

This will sync the books to all your Kindle devices and apps.

## Example

```
Found 6 PDF files:
  - ./Deep Research/How are deep research models architected_.pdf
  - ./Sakana.ai/paper.pdf
  ...

Converting to ePub format...
✓ Converted: paper.pdf → paper.epub
✓ Converted: research.pdf → research.epub

Conversion complete: 6/6 files converted successfully
ePub files are saved in the 'epub_books' directory
```
