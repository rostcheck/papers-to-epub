#!/usr/bin/env python3
import subprocess
import json
from pathlib import Path
from epub_quality_analyzer import EpubQualityAnalyzer
import time

class QPdfConverter:
    def __init__(self):
        self.epub_dir = Path("epub_books")
        self.epub_dir.mkdir(exist_ok=True)
    
    def convert_pdf(self, pdf_path):
        """Convert PDF using Q CLI cognitive processing"""
        pdf_path = Path(pdf_path)
        print(f"🤖 Converting {pdf_path.name} using Q CLI...")
        
        # Create conversion prompt
        prompt = self._create_conversion_prompt(pdf_path)
        
        # Track existing ePubs to identify new ones
        existing_epubs = set(self.epub_dir.glob("*.epub"))
        
        # Invoke Q CLI
        start_time = time.time()
        result = self._invoke_q_cli(prompt)
        duration = time.time() - start_time
        
        if result['success']:
            # Find newly created ePub
            new_epubs = set(self.epub_dir.glob("*.epub")) - existing_epubs
            
            if new_epubs:
                epub_path = list(new_epubs)[0]  # Get the new ePub
                validation = self._validate_epub(epub_path)
                
                return {
                    'success': True,
                    'epub_path': epub_path,
                    'duration': duration,
                    'validation': validation,
                    'q_output': result['output']
                }
            else:
                return {
                    'success': False, 
                    'error': 'No ePub file generated',
                    'q_output': result['output']
                }
        
        return {
            'success': False, 
            'error': result.get('error', 'Q CLI failed'),
            'duration': duration
        }
    
    def _create_conversion_prompt(self, pdf_path):
        """Create detailed conversion prompt for Q CLI"""
        return f"""Please convert the PDF file '{pdf_path}' to a high-quality ePub format using the following process:

1. Extract and read the PDF content using PyPDF2
2. Cognitively process the content to understand:
   - Document structure and sections
   - Tables and figures
   - Academic formatting
   - Author information and citations

3. Create a well-structured HTML document with:
   - Proper heading hierarchy (h1, h2, h3)
   - Table of contents at the beginning
   - Tables as HTML (not images)
   - Clean paragraph structure
   - Proper XML escaping (&amp; not &)

4. Generate these ePub files:
   - content.html (main content)
   - content.opf (metadata)
   - toc.ncx (navigation)
   - styles.css (academic styling)

5. Assemble into ePub format and save as: epub_books/{{clean_title}}.epub

Focus on creating professional academic formatting with zero XML parsing errors. Report completion when done."""

    def _invoke_q_cli(self, prompt):
        """Invoke Q CLI with no-interactive flag"""
        try:
            cmd = ["q", "chat", "-a", "--no-interactive", prompt]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                return {'success': True, 'output': result.stdout}
            else:
                return {'success': False, 'error': result.stderr, 'output': result.stdout}
                
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Q CLI timeout (5 minutes)'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _validate_epub(self, epub_path):
        """Validate the generated ePub"""
        validation = {
            'xml_valid': False,
            'quality_issues': [],
            'file_size': 0,
            'structure_valid': False
        }
        
        try:
            validation['file_size'] = epub_path.stat().st_size
            
            # XML structure validation
            validation['xml_valid'] = self._check_xml_structure(epub_path)
            
            # Quality analysis
            analyzer = EpubQualityAnalyzer(epub_path)
            issues = analyzer.analyze()
            validation['quality_issues'] = issues
            
            # Basic structure check
            validation['structure_valid'] = self._check_epub_structure(epub_path)
            
        except Exception as e:
            validation['error'] = str(e)
        
        return validation
    
    def _check_xml_structure(self, epub_path):
        """Quick XML validation check"""
        try:
            import zipfile
            with zipfile.ZipFile(epub_path, 'r') as epub:
                content = epub.read('content.html').decode('utf-8')
                # Check for common XML errors
                if '&' in content and '&amp;' not in content.replace('&amp;', ''):
                    return False
                return True
        except:
            return False
    
    def _check_epub_structure(self, epub_path):
        """Check basic ePub structure"""
        try:
            import zipfile
            with zipfile.ZipFile(epub_path, 'r') as epub:
                files = epub.namelist()
                required = ['mimetype', 'META-INF/container.xml', 'content.opf']
                return all(f in files for f in required)
        except:
            return False

def main():
    """Test the Q CLI PDF converter"""
    converter = QPdfConverter()
    
    # Test with Sakana paper
    test_pdf = "./Sakana.ai/2502.14297v2.pdf"
    
    if Path(test_pdf).exists():
        print("🚀 Testing Q CLI PDF Converter")
        print("=" * 50)
        
        result = converter.convert_pdf(test_pdf)
        
        print(f"\n📊 Results:")
        print(f"Success: {result['success']}")
        print(f"Duration: {result.get('duration', 0):.1f}s")
        
        if result['success']:
            epub_path = result['epub_path']
            validation = result['validation']
            
            print(f"ePub created: {epub_path.name}")
            print(f"File size: {validation['file_size']:,} bytes")
            print(f"XML valid: {validation['xml_valid']}")
            print(f"Structure valid: {validation['structure_valid']}")
            print(f"Quality issues: {len(validation['quality_issues'])}")
            
            if validation['quality_issues']:
                print("Issues found:")
                for issue in validation['quality_issues'][:3]:
                    print(f"  - {issue}")
            else:
                print("🎉 Perfect quality - zero issues!")
        else:
            print(f"❌ Error: {result['error']}")
            if 'q_output' in result:
                print("Q CLI output (last 500 chars):")
                output = result['q_output']
                print(output[-500:] if len(output) > 500 else output)
    else:
        print(f"Test PDF not found: {test_pdf}")

if __name__ == "__main__":
    main()
