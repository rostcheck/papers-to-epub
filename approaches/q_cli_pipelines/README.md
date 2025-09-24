# Q CLI Pipelines Approach

## Overview
Leverages Q CLI (Amazon Q Developer) for cognitive PDF processing.

## Files
- `minimalist_q_pipeline.py` - Direct Q CLI approach (best results)
- `q_pdf_converter.py` - Complex multi-step pipeline
- `q_epub_pipeline.py` - Original pipeline attempt
- `test_q_invoke.py` - Q CLI invocation testing
- `test_q_auto.py` - Automated Q CLI interaction
- `q_conversion_instructions.md` - Template instructions
- `batch_q_conversion.py` - Batch processing
- `improved_q_strategy.py` - Iterative processing strategy

## Results

### Minimalist Pipeline (Best)
- **Speed**: 591 seconds (~10 minutes)
- **Quality Issues**: 1 (missing TOC only)
- **Text Fragmentation**: Moderate (35+ instances)
- **Content Accuracy**: Moderate but better structure

### Complex Pipeline
- **Speed**: 82 seconds
- **Quality Issues**: 5+ issues
- **Text Fragmentation**: Very high (485+ instances)
- **Content Accuracy**: Poor

## Key Insight
Direct Q CLI access produces better results than complex preprocessing pipelines.

## Usage
```bash
# Best approach
python3 minimalist_q_pipeline.py

# Test Q CLI invocation
python3 test_q_invoke.py
```
