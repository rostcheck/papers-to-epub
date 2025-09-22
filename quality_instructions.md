# ePub Quality Evaluation Instructions

You are evaluating the quality of PDF-to-ePub conversions. Analyze the ePub content and identify formatting issues that impact readability on mobile devices.

## Known Quality Issues to Detect:

### 1. Table of Contents Problems
- TOC appears at the end of document instead of beginning
- TOC entries are meaningless (e.g., "1", ".2", "↩", "analysis section)")
- TOC should have proper section headings and page references

### 2. Repeated Footer Content
- Date/time stamps appearing repeatedly in body text (e.g., "9/12/25, 9:35 AM")
- URL footers repeated throughout (e.g., "https://sakana.ai/ai-scientist-first-publication/")
- Page numbers from original PDF (e.g., "1/10", "2/10") scattered in text
- These should be removed or consolidated

### 3. Poor Table Formatting
- Tables converted to images instead of proper HTML tables
- Table content split across multiple lines inappropriately
- Missing table structure and alignment

### 4. Additional Issues to Watch For:
- Excessive whitespace or line breaks
- Images not properly positioned relative to text
- Citation formatting issues
- Broken internal links
- Text flow problems around figures
- Font inconsistencies

## Quality Assessment Criteria:

**GOOD**: Content flows naturally, TOC is at beginning with meaningful entries, no repeated footers, tables are readable
**FAIR**: Minor formatting issues that don't significantly impact readability
**POOR**: Major structural problems, repeated content, unreadable tables, TOC issues

## Evaluation Process:
1. Check TOC placement and quality
2. Scan for repeated footer/header content
3. Examine table formatting
4. Assess overall text flow and readability
5. Note any other formatting anomalies
