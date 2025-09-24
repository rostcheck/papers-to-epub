#!/usr/bin/env python3
from pathlib import Path
from q_epub_pipeline import QEpubPipeline
import time

def batch_convert_pdfs():
    """Convert all PDFs using Q CLI pipeline"""
    pipeline = QEpubPipeline()
    
    # Find all PDFs
    pdf_files = []
    for pattern in ["*.pdf", "**/*.pdf"]:
        pdf_files.extend(Path(".").glob(pattern))
    
    print(f"🔍 Found {len(pdf_files)} PDF files")
    
    results = []
    for pdf_file in pdf_files:
        print(f"\n{'='*60}")
        print(f"Processing: {pdf_file}")
        
        start_time = time.time()
        result = pipeline.convert_pdf(pdf_file)
        duration = time.time() - start_time
        
        result['pdf_file'] = str(pdf_file)
        result['duration'] = duration
        results.append(result)
        
        # Print immediate results
        if result['success']:
            validation = result['validation']
            print(f"✅ Success in {duration:.1f}s")
            print(f"   Quality issues: {len(validation['quality_issues'])}")
            print(f"   XML valid: {validation['xml_valid']}")
        else:
            print(f"❌ Failed: {result['error']}")
    
    # Summary report
    print(f"\n{'='*60}")
    print("BATCH CONVERSION SUMMARY")
    print(f"{'='*60}")
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"Total files: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if successful:
        avg_duration = sum(r['duration'] for r in successful) / len(successful)
        total_issues = sum(len(r['validation']['quality_issues']) for r in successful)
        print(f"Average time: {avg_duration:.1f}s")
        print(f"Total quality issues: {total_issues}")
        
        # Best quality files
        zero_issue_files = [r for r in successful if len(r['validation']['quality_issues']) == 0]
        print(f"Perfect quality files: {len(zero_issue_files)}")
    
    if failed:
        print("\nFailed conversions:")
        for r in failed:
            print(f"  - {Path(r['pdf_file']).name}: {r['error']}")

if __name__ == "__main__":
    batch_convert_pdfs()
