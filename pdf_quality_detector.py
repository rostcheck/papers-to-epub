#!/usr/bin/env python3
import PyPDF2
from pathlib import Path

def analyze_pdf_quality(pdf_path):
    """Analyze PDF to detect if it's suitable for ePub conversion"""
    issues = []
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            # Basic metrics
            num_pages = len(reader.pages)
            total_text = ""
            
            # Extract text from first few pages
            for i in range(min(3, num_pages)):
                page_text = reader.pages[i].extract_text()
                total_text += page_text
            
            # Quality checks
            text_length = len(total_text.strip())
            words = total_text.split()
            
            # Check 1: Very little text (likely image-based PDF)
            if text_length < 500:
                issues.append(f"CRITICAL: Very little text extracted ({text_length} chars) - likely image-based PDF")
            
            # Check 2: Web interface indicators
            web_indicators = ["New", "Answer", "Sources ·", "Steps", "Search", "Results"]
            web_count = sum(1 for indicator in web_indicators if indicator in total_text)
            if web_count >= 3:
                issues.append(f"CRITICAL: Contains web interface elements ({web_count} indicators) - web screenshot detected")
            elif web_count >= 2:
                issues.append(f"WARNING: Contains web interface elements ({web_count} indicators) - may be screenshot")
            
            # Check 3: Very short "paragraphs" (fragmented text)
            lines = [line.strip() for line in total_text.split('\n') if line.strip()]
            short_lines = [line for line in lines if len(line) < 10 and len(line) > 0]
            if len(short_lines) > len(lines) * 0.3:
                issues.append(f"WARNING: Many short text fragments ({len(short_lines)}/{len(lines)}) - poor text extraction")
            
            # Check 4: Academic paper indicators (positive signals)
            academic_indicators = ["Abstract", "Introduction", "Methodology", "Results", "Conclusion", "References", "et al.", "Figure", "Table"]
            academic_count = sum(1 for indicator in academic_indicators if indicator in total_text)
            
            if academic_count < 2:
                issues.append(f"WARNING: Few academic paper indicators ({academic_count}) - may not be research paper")
            
            return {
                "suitable": len([i for i in issues if i.startswith("CRITICAL")]) == 0,
                "issues": issues,
                "text_length": text_length,
                "num_pages": num_pages,
                "academic_score": academic_count
            }
            
    except Exception as e:
        return {
            "suitable": False,
            "issues": [f"ERROR: Could not analyze PDF - {e}"],
            "text_length": 0,
            "num_pages": 0,
            "academic_score": 0
        }

def main():
    """Test PDF quality detector"""
    pdf_file = Path("./Deep Research/How are deep research models architected_.pdf")
    
    if pdf_file.exists():
        result = analyze_pdf_quality(pdf_file)
        
        print(f"=== PDF Quality Analysis: {pdf_file.name} ===")
        print(f"Suitable for conversion: {'✓' if result['suitable'] else '✗'}")
        print(f"Text length: {result['text_length']} characters")
        print(f"Pages: {result['num_pages']}")
        print(f"Academic score: {result['academic_score']}/9")
        
        if result['issues']:
            print("\nIssues found:")
            for issue in result['issues']:
                print(f"  - {issue}")
    else:
        print("PDF file not found")

if __name__ == "__main__":
    main()
