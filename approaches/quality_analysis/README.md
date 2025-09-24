# Quality Analysis Tools

## Overview
Comprehensive quality detection and monitoring tools for ePub files.

## Files
- `epub_quality_analyzer.py` - Core quality detection engine
- `enhanced_quality_monitor.py` - Advanced quality metrics and detailed analysis

## Quality Metrics Detected

### Core Issues (epub_quality_analyzer.py)
- Repeated footer content
- Table of contents placement
- Excessive line breaks
- Missing or meaningless TOC entries
- Blank pages
- Table formatting issues

### Enhanced Metrics (enhanced_quality_monitor.py)
- Title quality assessment
- Text fragmentation detection (spacing issues)
- Content completeness analysis
- Document structure validation
- Page-by-page quality breakdown

## Key Insights
- **Text Fragmentation**: Critical metric for PDF conversion quality
- **TOC Placement**: Major usability issue when at end of document
- **Content Completeness**: Abstract and section validation
- **XML Validation**: Essential for ePub reader compatibility

## Usage
```bash
# Basic quality analysis
python3 epub_quality_analyzer.py

# Detailed quality analysis with fragmentation detection
python3 enhanced_quality_monitor.py
```

## Quality Thresholds
- **Perfect**: 0 issues detected
- **Good**: 1-2 minor issues
- **Poor**: 3+ issues or major structural problems
- **Unacceptable**: XML parsing errors or severe fragmentation (200+ instances)
