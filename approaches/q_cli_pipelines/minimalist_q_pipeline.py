#!/usr/bin/env python3
import subprocess
import time
from pathlib import Path
from epub_quality_analyzer import EpubQualityAnalyzer

class MinimalistQPipeline:
    def __init__(self):
        self.epub_dir = Path("epub_books")
        self.epub_dir.mkdir(exist_ok=True)
    
    def convert_pdf(self, pdf_path):
        """Direct Q CLI conversion with minimal intervention"""
        pdf_path = Path(pdf_path)
        print(f"🎯 Direct Q CLI conversion: {pdf_path.name}")
        
        # Track existing ePubs
        existing_epubs = set(self.epub_dir.glob("*.epub"))
        
        # Create direct conversion prompt
        prompt = f"""
Please convert the PDF file '{pdf_path}' directly to a high-quality ePub format.

GOAL: Create a professional academic ePub that reads perfectly on mobile devices.

QUALITY STANDARDS:
- Clean, readable text with proper spacing
- Professional academic formatting
- Tables as HTML (not images)  
- Proper document structure with headings
- Table of contents at beginning
- Zero XML parsing errors
- Complete title and author information

APPROACH:
- Read the PDF directly using available tools
- Understand the document structure cognitively
- Create clean, semantic HTML content
- Generate proper ePub files (content.html, content.opf, toc.ncx, styles.css)
- Assemble into valid ePub format

OUTPUT: Save as epub_books/{{clean_filename}}.epub

Focus on quality over speed. Take whatever approach works best to achieve perfect results.
"""
        
        # Invoke Q CLI directly
        start_time = time.time()
        result = self._invoke_q_cli(prompt)
        duration = time.time() - start_time
        
        # Find new ePub
        new_epubs = set(self.epub_dir.glob("*.epub")) - existing_epubs
        
        if result['success'] and new_epubs:
            epub_path = list(new_epubs)[0]
            validation = self._validate_epub(epub_path)
            
            return {
                'success': True,
                'epub_path': epub_path,
                'duration': duration,
                'validation': validation
            }
        
        return {
            'success': False,
            'error': result.get('error', 'No ePub generated'),
            'duration': duration,
            'q_output': result.get('output', '')
        }
    
    def _invoke_q_cli(self, prompt):
        """Simple Q CLI invocation"""
        try:
            cmd = ["q", "chat", "-a", "--no-interactive", prompt]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes for quality work
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None
            }
            
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Timeout (10 minutes)'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _validate_epub(self, epub_path):
        """Quality validation"""
        try:
            # File size check
            file_size = epub_path.stat().st_size
            
            # Quality analysis
            analyzer = EpubQualityAnalyzer(epub_path)
            issues = analyzer.analyze()
            
            return {
                'file_size': file_size,
                'quality_issues': len(issues),
                'issues': issues,
                'valid': len(issues) == 0
            }
        except Exception as e:
            return {'error': str(e), 'valid': False}

def main():
    """Test minimalist pipeline"""
    pipeline = MinimalistQPipeline()
    
    test_pdf = "./Sakana.ai/2502.14297v2.pdf"
    
    if not Path(test_pdf).exists():
        print(f"❌ PDF not found: {test_pdf}")
        return
    
    print("🚀 MINIMALIST Q CLI PIPELINE")
    print("=" * 50)
    print("Giving Q CLI direct access to PDF...")
    print("No preprocessing, no fragmentation, pure cognitive processing.")
    print()
    
    result = pipeline.convert_pdf(test_pdf)
    
    print(f"\n📊 RESULTS:")
    print(f"Success: {result['success']}")
    print(f"Duration: {result.get('duration', 0):.1f}s")
    
    if result['success']:
        epub_path = result['epub_path']
        validation = result['validation']
        
        print(f"ePub: {epub_path.name}")
        print(f"Size: {validation['file_size']:,} bytes")
        print(f"Quality issues: {validation['quality_issues']}")
        
        if validation['valid']:
            print("🎉 PERFECT QUALITY - Zero issues!")
        else:
            print("Issues found:")
            for issue in validation['issues'][:3]:
                print(f"  - {issue}")
    else:
        print(f"❌ Failed: {result['error']}")
        if 'q_output' in result and result['q_output']:
            print("\nQ CLI output (last 300 chars):")
            output = result['q_output']
            print(output[-300:] if len(output) > 300 else output)

if __name__ == "__main__":
    main()
