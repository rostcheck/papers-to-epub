#!/usr/bin/env python3
import os
import subprocess
import re
import zipfile
import tempfile
from pathlib import Path
from epub_quality_analyzer import EpubQualityAnalyzer

# Import existing functions
from convert_to_epub import clean_filename, extract_title_from_pdf

def convert_pdf_to_epub_improved(pdf_path, output_dir="epub_books"):
    """Convert PDF to ePub with quality improvements"""
    pdf_file = Path(pdf_path)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Extract title
    title = extract_title_from_pdf(pdf_path)
    if title:
        epub_name = clean_filename(title) + ".epub"
    else:
        epub_name = pdf_file.stem + ".epub"
    
    epub_path = output_path / epub_name
    
    try:
        # Step 1: Convert with improved Calibre parameters
        cmd = [
            "ebook-convert", str(pdf_file), str(epub_path),
            "--no-default-epub-cover",
            "--linearize-tables",
        ]
        
        if title:
            cmd.extend(["--title", title])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"✗ Failed to convert {pdf_file.name}: {result.stderr}")
            return False
        
        # Step 2: Post-process the ePub to fix quality issues
        if post_process_epub(epub_path):
            print(f"✓ Converted and improved: {pdf_file.name} → {epub_name}")
            if title:
                print(f"  Title: {title}")
            return True
        else:
            print(f"⚠ Converted but post-processing failed: {pdf_file.name}")
            return True
            
    except Exception as e:
        print(f"✗ Error converting {pdf_file.name}: {e}")
        return False

def post_process_epub(epub_path):
    """Post-process ePub to fix quality issues"""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Extract ePub
            with zipfile.ZipFile(epub_path, 'r') as epub:
                epub.extractall(temp_path)
            
            # Fix main content
            html_file = temp_path / "index.html"
            if html_file.exists():
                content = html_file.read_text(encoding='utf-8')
                content = clean_html_content(content)
                html_file.write_text(content, encoding='utf-8')
            
            # Rebuild ePub
            with zipfile.ZipFile(epub_path, 'w', zipfile.ZIP_DEFLATED) as new_epub:
                for file_path in temp_path.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(temp_path)
                        new_epub.write(file_path, arcname)
        
        return True
    except Exception as e:
        print(f"Post-processing error: {e}")
        return False

def clean_html_content(content):
    """Clean HTML content to remove repeated footers and fix formatting"""
    
    # Remove repeated date/time footers (only if they're standalone)
    content = re.sub(r'<p[^>]*>\s*\d{1,2}/\d{1,2}/\d{2,4},?\s+\d{1,2}:\d{2}\s+[AP]M\s*</p>', '', content, flags=re.IGNORECASE)
    
    # Remove repeated URL footers - ONLY if they're standalone URLs, not mixed with content
    content = re.sub(r'<p[^>]*>\s*https?://[^\s<]+\s*</p>', '', content, flags=re.IGNORECASE)
    
    # Remove page number footers like "1/10" (only if standalone)
    content = re.sub(r'<p[^>]*>\s*\d+/\d+\s*</p>', '', content)
    
    # Remove excessive whitespace
    content = re.sub(r'(<p[^>]*>\s*</p>\s*){2,}', '', content)
    
    # Fix broken text flow (single characters on lines) - be more conservative
    content = re.sub(r'<p[^>]*>\s*[A-Za-z]\s*</p>\s*<p[^>]*>\s*[A-Za-z]\s*</p>', '', content)
    
    return content

def analyze_and_convert(pdf_path, max_iterations=2):
    """Convert PDF and iteratively improve quality"""
    print(f"\n=== Processing: {Path(pdf_path).name} ===")
    
    # Pre-conversion quality check
    from pdf_quality_detector import analyze_pdf_quality
    pdf_analysis = analyze_pdf_quality(pdf_path)
    
    print(f"PDF Quality Check: {'✓ Suitable' if pdf_analysis['suitable'] else '⚠ Issues detected'}")
    print(f"Text: {pdf_analysis['text_length']} chars, Academic score: {pdf_analysis['academic_score']}/9")
    
    if pdf_analysis['issues']:
        print("Issues found:")
        for issue in pdf_analysis['issues']:
            print(f"  - {issue}")
    
    # Determine processing strategy based on PDF quality
    if not pdf_analysis['suitable']:
        print("\n⚠ PDF not suitable for standard conversion - applying enhanced processing")
        return convert_problematic_pdf(pdf_path, pdf_analysis)
    
    # Standard conversion for good PDFs
    if not convert_pdf_to_epub_improved(pdf_path):
        return False
    
    # Get the output file name
    title = extract_title_from_pdf(pdf_path)
    if title:
        epub_name = clean_filename(title) + ".epub"
    else:
        epub_name = Path(pdf_path).stem + ".epub"
    
    epub_path = Path("epub_books") / epub_name
    
    # Iterative quality improvement
    for iteration in range(max_iterations):
        print(f"\n--- Quality Check (Iteration {iteration + 1}) ---")
        analyzer = EpubQualityAnalyzer(epub_path)
        issues = analyzer.analyze()
        
        if not issues:
            print("✓ Quality check passed!")
            break
        
        # Apply additional fixes based on detected issues
        if iteration < max_iterations - 1:
            print("Applying additional fixes...")
            apply_targeted_fixes(epub_path, issues)
    
    # Apply TOC fixes if needed
    print("\n--- Applying TOC Improvements ---")
    from toc_fixer import TOCFixer
    toc_fixer = TOCFixer(epub_path)
    toc_fixer.fix_toc()
    
    # Final quality check
    print("\n--- Final Quality Check ---")
    analyzer = EpubQualityAnalyzer(epub_path)
    final_issues = analyzer.analyze()
    
    return True

def convert_problematic_pdf(pdf_path, pdf_analysis):
    """Enhanced conversion for problematic PDFs using Claude"""
    pdf_file = Path(pdf_path)
    output_path = Path("epub_books")
    output_path.mkdir(exist_ok=True)
    
    # Extract title
    title = extract_title_from_pdf(pdf_path)
    if title:
        epub_name = clean_filename(title) + ".epub"
    else:
        epub_name = pdf_file.stem + ".epub"
    
    epub_path = output_path / epub_name
    
    # Use Claude for content extraction and restructuring
    print("🤖 Using Claude to restructure PDF content...")
    from claude_pdf_extractor import extract_pdf_with_claude, create_epub_from_claude_content
    
    claude_content = extract_pdf_with_claude(pdf_path)
    
    if "error" not in claude_content:
        # Create ePub from Claude-structured content
        if create_epub_from_claude_content(claude_content, epub_path):
            print(f"✓ Claude-enhanced conversion completed: {epub_name}")
            return True
        else:
            print("✗ Failed to create ePub from Claude content")
            return False
    else:
        print(f"✗ Claude extraction failed: {claude_content['error']}")
        # Fallback to standard conversion
        print("Falling back to standard conversion...")
        return convert_pdf_to_epub_improved(pdf_path)

def clean_web_screenshot_epub(epub_path):
    """Clean up ePub converted from web screenshot"""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Extract ePub
            with zipfile.ZipFile(epub_path, 'r') as epub:
                epub.extractall(temp_path)
            
            # Clean HTML content
            html_file = temp_path / "index.html"
            if html_file.exists():
                content = html_file.read_text(encoding='utf-8')
                content = clean_web_screenshot_content(content)
                html_file.write_text(content, encoding='utf-8')
            
            # Rebuild ePub
            with zipfile.ZipFile(epub_path, 'w', zipfile.ZIP_DEFLATED) as new_epub:
                for file_path in temp_path.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(temp_path)
                        new_epub.write(file_path, arcname)
        
    except Exception as e:
        print(f"Web screenshot cleanup error: {e}")

def clean_web_screenshot_content(content):
    """Clean HTML content from web screenshots"""
    # Remove web interface elements
    web_elements = [
        r'<p[^>]*>\s*New\s*</p>',
        r'<p[^>]*>\s*Answer\s*</p>',
        r'<p[^>]*>\s*Sources\s*·\s*\d+\s*</p>',
        r'<p[^>]*>\s*Steps\s*</p>',
        r'<p[^>]*>\s*Search\s*</p>',
    ]
    
    for pattern in web_elements:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)
    
    # Fix fragmented text by joining single characters/short fragments
    lines = content.split('\n')
    cleaned_lines = []
    buffer = ""
    
    for line in lines:
        # Extract text content from HTML line
        text_content = re.sub(r'<[^>]+>', '', line).strip()
        
        # If it's a very short fragment, add to buffer
        if len(text_content) <= 3 and text_content.isalpha():
            buffer += text_content + " "
        else:
            # If we have buffered content, combine it
            if buffer:
                # Find the last paragraph tag and insert buffered content
                if '<p' in line:
                    line = line.replace('>', f'>{buffer}', 1)
                buffer = ""
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def apply_targeted_fixes(epub_path, issues):
    """Apply targeted fixes based on detected issues"""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            with zipfile.ZipFile(epub_path, 'r') as epub:
                epub.extractall(temp_path)
            
            html_file = temp_path / "index.html"
            if html_file.exists():
                content = html_file.read_text(encoding='utf-8')
                
                # Apply fixes based on specific issues
                for issue in issues:
                    if "Repeated footer content" in issue:
                        # Extract the repeated content and remove it more aggressively
                        match = re.search(r"'([^']+)'", issue)
                        if match:
                            repeated_text = re.escape(match.group(1))
                            content = re.sub(f'<p[^>]*>.*?{repeated_text}.*?</p>', '', content, flags=re.IGNORECASE)
                
                html_file.write_text(content, encoding='utf-8')
            
            # Rebuild ePub
            with zipfile.ZipFile(epub_path, 'w', zipfile.ZIP_DEFLATED) as new_epub:
                for file_path in temp_path.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(temp_path)
                        new_epub.write(file_path, arcname)
        
    except Exception as e:
        print(f"Targeted fix error: {e}")
    """Apply targeted fixes based on detected issues"""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            with zipfile.ZipFile(epub_path, 'r') as epub:
                epub.extractall(temp_path)
            
            html_file = temp_path / "index.html"
            if html_file.exists():
                content = html_file.read_text(encoding='utf-8')
                
                # Apply fixes based on specific issues
                for issue in issues:
                    if "Repeated footer content" in issue:
                        # Extract the repeated content and remove it more aggressively
                        match = re.search(r"'([^']+)'", issue)
                        if match:
                            repeated_text = re.escape(match.group(1))
                            content = re.sub(f'<p[^>]*>.*?{repeated_text}.*?</p>', '', content, flags=re.IGNORECASE)
                
                html_file.write_text(content, encoding='utf-8')
            
            # Rebuild ePub
            with zipfile.ZipFile(epub_path, 'w', zipfile.ZIP_DEFLATED) as new_epub:
                for file_path in temp_path.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(temp_path)
                        new_epub.write(file_path, arcname)
        
    except Exception as e:
        print(f"Targeted fix error: {e}")

def main():
    # Find all PDF files
    pdf_files = []
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    
    if not pdf_files:
        print("No PDF files found in the current directory.")
        return
    
    print(f"Found {len(pdf_files)} PDF files:")
    for pdf in pdf_files:
        print(f"  - {pdf}")
    
    print("\nConverting to ePub format with quality improvements...")
    successful = 0
    
    for pdf in pdf_files:
        if analyze_and_convert(pdf):
            successful += 1
    
    print(f"\n=== FINAL SUMMARY ===")
    print(f"Conversion complete: {successful}/{len(pdf_files)} files converted successfully")
    print("ePub files are saved in the 'epub_books' directory")

if __name__ == "__main__":
    main()
