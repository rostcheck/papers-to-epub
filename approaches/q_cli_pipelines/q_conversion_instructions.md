# Q CLI PDF-to-ePub Conversion Instructions

## Task
Convert the PDF file `{pdf_path}` to a high-quality ePub format using cognitive processing.

## Process
1. **Extract and read** the PDF content using PyPDF2 or similar
2. **Cognitively process** the content to understand structure, sections, tables, figures
3. **Create clean HTML** with proper semantic markup:
   - Proper headings hierarchy (h1, h2, h3)
   - Table of contents at the beginning
   - Well-formatted tables (not images)
   - Clean paragraph structure
   - Proper citations and references
4. **Generate ePub files**:
   - `content.html` - Main content with proper structure
   - `content.opf` - Metadata and manifest
   - `toc.ncx` - Navigation structure
   - `styles.css` - Professional academic styling
5. **Assemble ePub** using zipfile with correct structure
6. **Output location**: `epub_books/{clean_title}.epub`

## Quality Requirements
- Zero XML parsing errors (escape &, <, > properly)
- Table of contents at beginning, not end
- No repeated footers or headers
- Tables as HTML, not images
- Professional academic styling
- Proper section hierarchy
- Clean, readable text flow

## Output
Create the ePub file and report:
- File location
- Title extracted
- Number of sections processed
- Any issues encountered

## Files to Create
Save the ePub as: `epub_books/{sanitized_title}.epub`
