#!/usr/bin/env python3
import subprocess
from pathlib import Path

class ImprovedQStrategy:
    def __init__(self):
        self.epub_dir = Path("epub_books")
    
    def convert_pdf_iteratively(self, pdf_path):
        """Convert PDF using iterative Q CLI approach"""
        pdf_path = Path(pdf_path)
        
        # Step 1: Extract and analyze PDF structure first
        structure_prompt = f"""
Please analyze the PDF '{pdf_path}' and provide:
1. The complete, proper title
2. Author names and affiliations  
3. Section structure (headings hierarchy)
4. Location of any tables or figures
5. Abstract content

Just analyze and report - don't convert yet.
"""
        
        print("📋 Step 1: Analyzing PDF structure...")
        structure_result = self._invoke_q_cli(structure_prompt)
        
        if not structure_result['success']:
            return structure_result
        
        # Step 2: Convert with specific instructions based on analysis
        conversion_prompt = f"""
Based on your analysis of '{pdf_path}', now create a high-quality ePub with these requirements:

1. TITLE: Use the complete proper title you identified
2. CONTENT: Process each section individually to avoid text fragmentation
3. TABLES: Convert any tables to proper HTML table format
4. STRUCTURE: Create proper heading hierarchy
5. QUALITY: Ensure proper spacing between words

Pay special attention to:
- Preserving spaces between words
- Converting tables from page 7 to HTML format
- Using complete title, not truncated version
- Including full abstract content

Save as: epub_books/Improved_Sakana_Evaluation.epub
"""
        
        print("🔧 Step 2: Converting with enhanced instructions...")
        return self._invoke_q_cli(conversion_prompt)
    
    def _invoke_q_cli(self, prompt):
        """Invoke Q CLI with enhanced error handling"""
        try:
            cmd = ["q", "chat", "-a", "--no-interactive", prompt]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                return {'success': True, 'output': result.stdout}
            else:
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

def main():
    """Test improved Q CLI strategy"""
    strategy = ImprovedQStrategy()
    
    test_pdf = "./Sakana.ai/2502.14297v2.pdf"
    
    if Path(test_pdf).exists():
        print("🚀 Testing Improved Q CLI Strategy")
        print("=" * 50)
        
        result = strategy.convert_pdf_iteratively(test_pdf)
        
        if result['success']:
            print("✅ Improved conversion completed")
            
            # Test the result
            improved_epub = Path("epub_books/Improved_Sakana_Evaluation.epub")
            if improved_epub.exists():
                from enhanced_quality_monitor import EnhancedQualityMonitor
                monitor = EnhancedQualityMonitor()
                report = monitor.analyze_epub_detailed(improved_epub)
                
                print(f"\n📊 Quality Results:")
                print(f"Total Issues: {report['total_issues']}")
                print(f"Categories: {report['issues_by_category']}")
            else:
                print("⚠️ ePub file not found")
        else:
            print(f"❌ Conversion failed: {result['error']}")

if __name__ == "__main__":
    main()
