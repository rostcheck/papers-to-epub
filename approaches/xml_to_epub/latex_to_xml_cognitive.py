#!/usr/bin/env python3
"""
Optimized Cognitive LaTeX-to-XML Converter
Based on Q Developer CLI behavior analysis with proper timeouts and monitoring
"""

import subprocess
import sys
import json
import time
import threading
from pathlib import Path

class OptimizedCognitiveConverter:
    def __init__(self):
        self.max_iterations = 2  # Reduced from 3
        self.target_quality = 85.0  # Reduced from 90.0 
        self.timeout = 300  # 5 minutes based on analysis
        
    def convert_with_monitoring(self, latex_file, output_file=None):
        """Convert LaTeX to XML with real-time monitoring"""
        print("🧠 Optimized Cognitive LaTeX-to-XML Converter")
        print("=" * 55)
        
        latex_path = Path(latex_file)
        if not latex_path.exists():
            print(f"❌ LaTeX file not found: {latex_file}")
            return False
            
        if output_file is None:
            output_file = f"output/{latex_path.stem}_cognitive.xml"
            
        print(f"📄 Input: {latex_file}")
        print(f"📄 Output: {output_file}")
        print(f"🎯 Target quality: {self.target_quality}%")
        print(f"⏱️  Timeout per iteration: {self.timeout}s")
        print()
        
        best_score = 0
        best_file = None
        
        for iteration in range(1, self.max_iterations + 1):
            print(f"🔄 Iteration {iteration}/{self.max_iterations}")
            print("-" * 40)
            
            iter_file = f"output/{latex_path.stem}_cognitive_iter{iteration}.xml"
            
            # Create focused prompt
            prompt = self._create_focused_prompt(latex_file, iter_file, iteration)
            
            # Run with monitoring
            success, duration = self._run_with_monitoring(prompt)
            
            if not success:
                print(f"❌ Iteration {iteration} failed")
                continue
                
            # Check file creation
            if not Path(iter_file).exists():
                print(f"❌ Output file not created: {iter_file}")
                continue
                
            file_size = Path(iter_file).stat().st_size
            print(f"✅ Created: {iter_file} ({file_size:,} bytes)")
            
            # Quick quality assessment
            score = self._assess_quality(latex_file, iter_file)
            print(f"📊 Quality Score: {score:.1f}% (duration: {duration:.1f}s)")
            
            if score > best_score:
                best_score = score
                best_file = iter_file
                print(f"✨ New best score!")
                
            if score >= self.target_quality:
                print(f"🎉 Target quality achieved!")
                break
                
            print()
            
        # Copy best result
        if best_file and Path(best_file).exists():
            import shutil
            shutil.copy2(best_file, output_file)
            print(f"🏆 Best result: {output_file} (Quality: {best_score:.1f}%)")
            return True
        else:
            print("❌ No successful conversion")
            return False
            
    def _create_focused_prompt(self, latex_file, output_file, iteration):
        """Create focused, shorter prompts based on iteration"""
        
        if iteration == 1:
            return f"""Convert {latex_file} to XML format as {output_file}.

REQUIRED XML STRUCTURE (use exact namespaces):
<paper xmlns="http://example.com/academic-paper" xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <metadata>
    <title>Title</title>
    <authors><author><name>Name</name></author></authors>
    <abstract><p xmlns="http://www.w3.org/1999/xhtml">Text</p></abstract>
  </metadata>
  <sections>
    <section id="section1" level="1">
      <title>Title</title>
      <content><p xmlns="http://www.w3.org/1999/xhtml">Content</p></content>
    </section>
  </sections>
  <references>
    <reference id="ref1"><title>Title</title><year>Year</year></reference>
  </references>
</paper>

Extract: title, authors, abstract, ALL sections, ALL bibliography entries."""
        
        else:
            return f"""Improve the XML conversion of {latex_file} to {output_file}.

Focus on missing elements:
- Complete bibliography from \\bibitem entries
- All citations from \\cite commands  
- Tables from \\begin{{table}} environments
- Mathematical equations

Use the same XML structure with proper namespaces."""
            
    def _run_with_monitoring(self, prompt):
        """Run Q Developer CLI with real-time monitoring"""
        start_time = time.time()
        
        try:
            print("🤖 Starting Q Developer CLI...")
            
            process = subprocess.Popen([
                'q', 'chat', '--no-interactive', '--trust-all-tools', prompt
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Monitor with timeout
            try:
                return_code = process.wait(timeout=self.timeout)
                duration = time.time() - start_time
                
                if return_code == 0:
                    print(f"✅ Completed successfully ({duration:.1f}s)")
                    return True, duration
                else:
                    print(f"❌ Failed with return code {return_code}")
                    return False, duration
                    
            except subprocess.TimeoutExpired:
                duration = time.time() - start_time
                print(f"⏰ Timed out after {self.timeout}s")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                return False, duration
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ Error: {e}")
            return False, duration
            
    def _assess_quality(self, latex_file, xml_file):
        """Quick quality assessment"""
        try:
            result = subprocess.run([
                'python3', 'structural_review/review_structure.py', 
                latex_file, xml_file, '--json'
            ], capture_output=True, text=True, cwd=Path.cwd(), timeout=30)
            
            if result.returncode == 0:
                # Find JSON in output (skip stderr messages)
                output_lines = result.stdout.strip().split('\n')
                for line in output_lines:
                    line = line.strip()
                    if line.startswith('{') and 'overall_score' in line:
                        data = json.loads(line)
                        return data.get('overall_score', 0)
                        
        except Exception as e:
            print(f"⚠️  Quality assessment error: {e}")
            
        return 0

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 optimized_cognitive_converter.py <latex_file> [output_file]")
        sys.exit(1)
        
    latex_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    converter = OptimizedCognitiveConverter()
    success = converter.convert_with_monitoring(latex_file, output_file)
    
    if success:
        print("\n🎉 Optimized cognitive conversion complete!")
    else:
        print("\n❌ Conversion failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
