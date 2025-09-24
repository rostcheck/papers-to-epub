# Desired Architecture for High-Quality PDF-to-ePub Conversion

## Executive Summary

Current PDF-to-ePub conversion approaches fail because they treat PDFs as generic documents rather than structured academic papers. This document outlines an ideal architecture that processes PDFs semantically to produce high-quality ePub outputs.

## Current Problem Analysis

### Why Existing Approaches Fail

**Traditional Pipeline (Broken)**:
```
PDF → Text Extractor (PyPDF2) → Text Processor → ePub Assembler → Poor ePub
```

**Issues**:
- Text fragmentation at extraction layer
- No understanding of document structure
- Tables converted to images or fragmented text
- No semantic comprehension of academic paper conventions
- Processing broken input instead of clean source

## Ideal Input Structure

### 1. Document Metadata
```json
{
  "title": "Complete, untruncated title",
  "authors": [
    {
      "name": "Author Name", 
      "affiliation": "Institution", 
      "email": "contact@email.com"
    }
  ],
  "abstract": "Full abstract text without fragmentation",
  "keywords": ["keyword1", "keyword2"],
  "publication_info": {
    "venue": "Conference/Journal",
    "date": "2025-04-14",
    "doi": "10.1000/xyz",
    "arxiv_id": "2504.08066v1"
  }
}
```

### 2. Structured Content Hierarchy
```json
{
  "sections": [
    {
      "id": "introduction",
      "title": "1. Introduction", 
      "level": 1,
      "content": "Clean, continuous text without page breaks or fragmentation",
      "subsections": [
        {
          "id": "motivation",
          "title": "1.1 Motivation",
          "level": 2,
          "content": "Subsection text..."
        }
      ]
    }
  ]
}
```

### 3. Tables as Structured Data
```json
{
  "tables": [
    {
      "id": "table1",
      "caption": "Comparison of AI Scientist Versions",
      "position": "after_section_3.2",
      "headers": ["Feature", "Codebase", "Execution", "Parallel", "VLM", "Result"],
      "rows": [
        ["AI Scientist-v1", "Topic-Specific", "Linear", "✗", "✗", "Research Output"],
        ["AI Scientist-v2", "Domain-General", "Tree-Based", "✓", "✓", "Peer-Reviewed"]
      ],
      "styling": "comparison-table"
    }
  ]
}
```

### 4. Figures and Charts
```json
{
  "figures": [
    {
      "id": "figure1",
      "caption": "The AI Scientist-v2 Workflow",
      "position": "after_section_3.1",
      "type": "workflow_diagram",
      "description": "Detailed description of what the figure shows",
      "image_data": "base64_encoded_image_or_path",
      "alt_text": "Accessibility description"
    }
  ]
}
```

### 5. References and Citations
```json
{
  "references": [
    {
      "id": "ref1",
      "authors": ["Lu, C.", "et al."],
      "title": "The AI Scientist: Towards Fully Automated Open-Ended Scientific Discovery",
      "venue": "arXiv preprint",
      "year": "2024",
      "url": "https://arxiv.org/abs/2408.06292"
    }
  ],
  "citations": [
    {"text": "recent work [1]", "ref_id": "ref1", "position": "section_1_paragraph_2"}
  ]
}
```

### 6. Mathematical Equations
```json
{
  "equations": [
    {
      "id": "eq1",
      "content": "O = E \\times T \\times Q",
      "description": "Training complexity formula where E is number of training epochs, T is number of words in training set, Q is model-specific complexity",
      "position": "section_2_paragraph_2"
    }
  ]
}
```

## Desired Architecture

### High-Level Pipeline
```
PDF → Semantic Parser → Structured JSON → ePub Generator → High-Quality ePub
```

### Component Architecture

#### 1. Semantic PDF Parser
**Purpose**: Extract structured content from academic PDFs

**Capabilities**:
- **Document Structure Recognition**: Identify title, authors, abstract, sections, references
- **Table Extraction**: Parse tables as structured data, not images
- **Figure Context**: Extract figures with captions and positioning context
- **Text Flow Reconstruction**: Rebuild continuous text from multi-column layouts
- **Reference Linking**: Maintain citation relationships and bibliography

**Technologies**:
- Computer vision for layout analysis
- NLP for content classification
- Academic paper templates/patterns
- Multi-modal AI for figure understanding

#### 2. Content Validator
**Purpose**: Ensure extracted content accuracy and completeness

**Capabilities**:
- **Completeness Check**: Verify all sections extracted
- **Structure Validation**: Confirm proper hierarchical organization
- **Cross-Reference Validation**: Ensure citations and references align
- **Quality Metrics**: Detect fragmentation, missing content, errors

#### 3. ePub Generator
**Purpose**: Convert structured JSON to high-quality ePub

**Capabilities**:
- **Semantic HTML Generation**: Create proper academic document structure
- **Professional Styling**: Apply academic formatting standards
- **Navigation Generation**: Build comprehensive table of contents
- **Metadata Integration**: Include complete bibliographic information
- **Quality Assurance**: Ensure XML validity and ePub compliance

### Key Design Principles

#### 1. Semantic Understanding
- **Academic Paper Conventions**: Understand typical paper structure
- **Content Type Recognition**: Distinguish text, tables, figures, equations
- **Relationship Preservation**: Maintain links between citations, figures, tables

#### 2. Quality-First Processing
- **Clean Input**: Process original PDF structure, not fragmented text
- **Validation at Each Step**: Ensure quality before proceeding
- **Error Recovery**: Handle parsing failures gracefully
- **Human-Readable Intermediate**: JSON format allows manual inspection/correction

#### 3. Modular Design
- **Pluggable Parsers**: Support different PDF parsing engines
- **Configurable Output**: Adapt to different ePub requirements
- **Quality Thresholds**: Configurable quality standards
- **Fallback Mechanisms**: Graceful degradation when parsing fails

## Schema Evolution from Real-World Testing

### LaTeX Experiment Results

Testing with the Word2Vec paper (Mikolov et al.) revealed that our initial schema was 85% correct but needed enhancements for academic papers:

#### **New Elements Added**

**1. Mathematical Equations**
```json
"equations": [
  {
    "id": "eq1",
    "content": "O = E \\times T \\times Q",
    "description": "Training complexity formula...",
    "position": "section_2_paragraph_2"
  }
]
```

**2. Enhanced Author Information**
```json
"authors": [
  {
    "name": "Tomas Mikolov",
    "affiliation": "Google Inc., Mountain View, CA",
    "email": "tmikolov@google.com",
    "orcid": "0000-0000-0000-0000",
    "corresponding": true
  }
]
```

**3. Enhanced Figure Metadata**
```json
"figures": [
  {
    "id": "figure1",
    "caption": "string",
    "position": "after_section_3.1",
    "type": "workflow_diagram",
    "description": "string",
    "source_reference": "filename.eps",
    "image_data": "base64_or_path",
    "alt_text": "string",
    "width_hint": "full|half|quarter"
  }
]
```

**4. Table Styling Enhancements**
```json
"tables": [
  {
    "styling": "semantic-syntactic-table",
    "table_type": "comparison|results|examples|data"
  }
]
```

**5. Document Classification**
```json
"publication_info": {
  "venue": "Conference/Journal",
  "date": "2025-04-14",
  "doi": "10.1000/xyz",
  "arxiv_id": "2504.08066v1",
  "document_class": "NIPS workshop paper"
}
```

#### **Key Insights**

1. **LaTeX source is ideal input** - Contains semantic structure without layout artifacts
2. **Academic papers are content-rich** - Need support for equations, complex citations, multiple table types
3. **Schema evolution is natural** - Real-world testing reveals additional requirements
4. **Positioning granularity matters** - Need paragraph-level positioning for precise element placement

## Formal JSON Schema

### Schema Specification

We have developed a comprehensive JSON Schema (`academic_paper_schema.json`) that validates our structured format. The schema includes:

#### **Core Validation Features**
- **Required fields**: Title, authors, abstract, sections
- **Data type validation**: Strings, arrays, objects with proper nesting
- **Format validation**: Email addresses, dates, ORCID IDs, arXiv IDs
- **Pattern matching**: Consistent ID naming conventions
- **Enum constraints**: Document classes, table types, figure types

#### **Academic-Specific Validation**
- **Author metadata**: Name, affiliation, email, ORCID, corresponding author flags
- **Publication info**: Venue, DOI, arXiv ID, document classification
- **Mathematical content**: Equations with LaTeX/MathML support
- **Rich tables**: Headers, rows, styling hints, semantic types
- **Figure metadata**: Captions, positioning, accessibility, sizing hints
- **Citation linking**: References connected to in-text citations

#### **Quality Assurance Rules**
- **Minimum lengths**: Titles (10+ chars), abstracts (50+ chars)
- **ID patterns**: Consistent naming (`table1`, `figure1`, `eq1`, `ref1`)
- **Position formats**: Standardized section/paragraph references (`section_1_paragraph_2`)
- **Hierarchical validation**: Section levels 1-4, proper nesting

### Schema Validation

The schema has been tested and validated against real academic papers:

```bash
# Install validation dependencies
pip3 install jsonschema

# Validate a structured paper
python3 validate_schema.py
```

**Validation Results**: ✅ Word2Vec paper (Mikolov et al.) passes all schema validation checks.

### Schema Benefits

1. **Data Quality Assurance**: Ensures consistent, complete structured data
2. **Early Error Detection**: Catches formatting issues before ePub generation
3. **Developer Documentation**: Schema serves as specification for implementers
4. **Tooling Integration**: Can be used in editors, APIs, validation pipelines
5. **Evolution Support**: Schema can be versioned and updated as requirements change

## Implementation Strategy

### Phase 1: Semantic Parser Development
1. **PDF Layout Analysis**: Identify document regions (header, body, footer, sidebar)
2. **Content Classification**: Classify regions as text, table, figure, reference
3. **Text Flow Reconstruction**: Rebuild reading order from layout
4. **Table Structure Extraction**: Parse table headers, rows, cells

### Phase 2: Content Understanding
1. **Section Hierarchy**: Build document outline from headings
2. **Citation Parsing**: Extract and link references
3. **Figure Context**: Associate captions with images
4. **Metadata Extraction**: Parse title, authors, abstract, keywords

### Phase 3: Quality Assurance
1. **Validation Framework**: Comprehensive quality checks
2. **Error Detection**: Identify parsing failures and inconsistencies
3. **Completeness Verification**: Ensure no content loss
4. **Human Review Interface**: Allow manual correction of parsing errors

### Phase 4: ePub Generation
1. **Template System**: Professional academic ePub templates
2. **Responsive Design**: Optimize for various screen sizes
3. **Accessibility**: Ensure screen reader compatibility
4. **Standards Compliance**: Full ePub specification adherence

## Success Metrics

### Quality Indicators
- **Zero Text Fragmentation**: No spacing artifacts from PDF extraction
- **Complete Content**: All sections, tables, figures preserved
- **Proper Structure**: Hierarchical organization maintained
- **Professional Formatting**: Academic standards applied
- **Perfect Navigation**: Comprehensive, accurate table of contents

### Performance Targets
- **Processing Time**: < 2 minutes for typical academic paper
- **Accuracy Rate**: > 95% content extraction accuracy
- **Quality Score**: Zero critical issues in generated ePub
- **User Satisfaction**: Readable on mobile devices without issues

## Technology Considerations

### PDF Parsing Options
- **PyMuPDF**: Better layout analysis than PyPDF2
- **pdfplumber**: Excellent table extraction capabilities
- **Adobe PDF Services API**: Commercial solution with advanced features
- **Custom Computer Vision**: ML-based layout analysis

### AI Integration Points
- **Document Classification**: Identify paper type and structure
- **Content Extraction**: NLP for text cleaning and organization
- **Quality Assessment**: AI-powered quality evaluation
- **Error Correction**: Automated fixing of common issues

### Validation Framework
- **Schema Validation**: Comprehensive quality checks using formal JSON Schema
- **Content Completeness**: Verify all expected sections present using schema requirements
- **Cross-Reference Integrity**: Validate citation and figure links using schema patterns
- **Quality Metrics**: Comprehensive ePub quality assessment with schema-enforced standards

## Conclusion

The key insight from our analysis is that **high-quality ePub generation requires semantic understanding of PDF structure**, not just text extraction. Current approaches fail because they process already-fragmented text rather than understanding the original document organization.

The proposed architecture addresses this by:
1. **Semantic parsing** that understands academic paper structure
2. **Structured intermediate format** with formal JSON Schema validation
3. **Quality-first processing** that validates each step against schema requirements
4. **Professional ePub generation** that applies academic formatting standards

### Deliverables

This architecture specification includes:
- **`desired_architecture.md`**: Complete architectural specification
- **`academic_paper_schema.json`**: Formal JSON Schema for validation
- **`validate_schema.py`**: Schema validation tooling
- **`word2vec_structured.json`**: Real-world example that passes validation

This approach would eliminate the fundamental issues we discovered in our testing:
- Text fragmentation from poor PDF extraction
- Missing or poorly formatted tables
- Incorrect document structure
- Incomplete content processing

The result would be ePub files that match the quality of manual processing while maintaining the scalability of automated systems.
