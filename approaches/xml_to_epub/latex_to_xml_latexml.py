#!/usr/bin/env python3
"""
LaTeX to XML Converter using LaTeXML with Cognitive Enhancement
Architecture: LaTeXML (professional conversion) + cognitive post-processing
"""

import json
import hashlib
import subprocess
import sys
from pathlib import Path
from lxml import etree
import boto3

# Add structural_review to path for quality assessment
sys.path.append(str(Path(__file__).parent / "structural_review"))
from review_structure import StructuralReviewer

class BedrockClient:
    """Clean Bedrock client with caching and Converse API"""
    
    def __init__(self):
        self.client = None
        
    def _get_client(self):
        if not self.client:
            self.client = boto3.client('bedrock-runtime', region_name='us-east-1')
        return self.client
    
    def call_llm(self, prompt: str, input_text: str, model_id: str = 'anthropic.claude-3-sonnet-20240229-v1:0') -> str:
        """Call Bedrock LLM with automatic caching"""
        # Create cache key from model + prompt + input
        cache_content = f"{model_id}:{prompt}:{input_text}"
        cache_key = hashlib.md5(cache_content.encode()).hexdigest()
        cache_file = Path("output") / f"bedrock_cache_{cache_key}.json"
        
        # Check cache first
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cached = json.load(f)
                    return cached['result']
            except Exception:
                pass
        
        try:
            client = self._get_client()
            
            # Use Converse API
            response = client.converse(
                modelId=model_id,
                messages=[{
                    'role': 'user',
                    'content': [{'text': f"{prompt}\n\nInput:\n{input_text}"}]
                }],
                inferenceConfig={
                    'maxTokens': 4000,
                    'temperature': 0.1
                }
            )
            
            result_text = response['output']['message']['content'][0]['text']
            
            # Cache the result
            try:
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                with open(cache_file, 'w') as f:
                    json.dump({'result': result_text}, f)
            except Exception as e:
                print(f"   ⚠️ Cache write failed: {e}")
            
            return result_text
            
        except Exception as e:
            print(f"   ❌ Bedrock call failed: {e}")
            return None

class LaTeXMLConverter:
    """LaTeX to XML converter using LaTeXML with cognitive enhancement"""
    
    def __init__(self, latex_file: str):
        self.latex_file = Path(latex_file)
        self.output_dir = Path("output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate output filename
        base_name = self.latex_file.stem
        self.xml_file = self.output_dir / f"{base_name}_latexml.xml"
        
        self.stats = {}
        self.bedrock = BedrockClient()
    
    def convert_to_xml(self) -> str:
        """Convert LaTeX to XML using LaTeXML with cognitive enhancement"""
        print("🚀 LaTeXML-based LaTeX-to-XML Converter")
        print("=" * 50)
        print(f"📋 Architecture: LaTeXML + cognitive post-processing")
        
        # Phase 1: LaTeXML conversion
        print("🔍 Phase 1: LaTeXML conversion...")
        if not self._run_latexml():
            raise RuntimeError("LaTeXML conversion failed")
        
        # Phase 2: Cognitive enhancement
        print("🧠 Phase 2: Cognitive enhancement...")
        self._cognitive_enhancement()
        
        # Phase 3: Quality assessment
        print("🔍 Phase 3: Quality assessment...")
        quality_score = self._assess_quality()
        
        # Results
        self._print_results(quality_score)
        
        return str(self.xml_file)
    
    def _run_latexml(self) -> bool:
        """Run LaTeXML on the input file"""
        try:
            # Step 1: latexml
            cmd = ['latexml', '--dest', str(self.xml_file), str(self.latex_file)]
            print(f"   Running: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                print(f"   ❌ LaTeXML failed with return code {result.returncode}")
                print(f"   STDERR: {result.stderr}")
                return False
            
            # Step 2: latexmlpost for MathML
            print(f"   Converting math to MathML...")
            post_cmd = ['latexmlpost', '--pmml', '--dest', str(self.xml_file), str(self.xml_file)]
            post_result = subprocess.run(post_cmd, capture_output=True, text=True, timeout=60)
            
            if post_result.returncode != 0:
                print(f"   ❌ MathML conversion failed: {post_result.stderr}")
                return False
            
            print(f"   ✅ LaTeXML with MathML completed successfully")
            return True
            
        except subprocess.TimeoutExpired:
            print("   ❌ LaTeXML timed out")
            return False
        except Exception as e:
            print(f"   ❌ LaTeXML error: {e}")
            return False
    
    def _cognitive_enhancement(self):
        """Cognitive enhancement of LaTeXML output - fix references and citations only"""
        try:
            # Parse the XML
            tree = etree.parse(str(self.xml_file))
            root = tree.getroot()
            
            # Extract statistics first
            self._extract_stats(root)
            
            # Fix references (convert LABEL:xxx to proper text)
            self._fix_references_cognitively(root)
            
            # Fix citations (convert empty citations to proper format)
            self._fix_citations_cognitively(root)
            
            # Add any necessary IDs
            self._add_ids_if_needed(root)
            
            # Save enhanced XML
            tree.write(str(self.xml_file), encoding='utf-8', pretty_print=True, xml_declaration=True)
            
            print(f"   ✅ Cognitive enhancement complete")
            
        except Exception as e:
            print(f"   ⚠️ Cognitive enhancement failed: {e}")
    
    def _fix_references_cognitively(self, root):
        """Fix cross-references using LaTeXML's label system"""
        ns = {'ltx': 'http://dlmf.nist.gov/LaTeXML'}
        
        # Build label mapping from LaTeXML elements
        label_map = {}
        
        # Find tables with labels
        tables = root.xpath('//ltx:table[@labels]', namespaces=ns)
        for table in tables:
            label = table.get('labels')
            # Get table number from tags
            tag = table.xpath('.//ltx:tag[@role="refnum"]', namespaces=ns)
            if tag:
                num = tag[0].text
                label_map[label] = f"Table {num}"
        
        # Find equations with labels  
        equations = root.xpath('//ltx:equation[@labels]', namespaces=ns)
        for eq in equations:
            label = eq.get('labels')
            tag = eq.xpath('.//ltx:tag[@role="refnum"]', namespaces=ns)
            if tag:
                num = tag[0].text
                label_map[label] = f"Equation ({num})"
        
        # Find figures with labels
        figures = root.xpath('//ltx:figure[@labels]', namespaces=ns)
        for fig in figures:
            label = fig.get('labels')
            tag = fig.xpath('.//ltx:tag[@role="refnum"]', namespaces=ns)
            if tag:
                num = tag[0].text
                label_map[label] = f"Figure {num}"
        
        # Update all references
        refs = root.xpath('//ltx:ref', namespaces=ns)
        print(f"   🔗 Fixing {len(refs)} references...")
        
        for ref in refs:
            labelref = ref.get('labelref')
            if labelref in label_map:
                ref.text = label_map[labelref]
                print(f"     ✅ {labelref} → {label_map[labelref]}")
            else:
                ref.text = f"[{labelref}]"
                print(f"     ⚠️ Unresolved: {labelref}")
    
    def _fix_citations_cognitively(self, root):
        """Fix empty citations"""
        ns = {'ltx': 'http://dlmf.nist.gov/LaTeXML'}
        citations = root.xpath('//ltx:cite', namespaces=ns)
        
        print(f"   📚 Fixing {len(citations)} citations...")
        
        for i, cite in enumerate(citations):
            # For now, just number them sequentially
            # In a real implementation, you'd use Bedrock to resolve citation text
            if not cite.text or cite.text.strip() == '':
                cite.text = f"[{i+1}]"
    
    def _extract_stats(self, root):
        """Extract statistics from LaTeXML XML"""
        ns = {'ltx': 'http://dlmf.nist.gov/LaTeXML'}
        
        # Count elements
        sections = root.xpath('.//ltx:section | .//ltx:subsection', namespaces=ns)
        equations = root.xpath('.//ltx:equation', namespaces=ns)
        figures = root.xpath('.//ltx:figure', namespaces=ns)
        tables = root.xpath('.//ltx:table', namespaces=ns)
        
        # Count references (bibliography items)
        bibentries = root.xpath('.//ltx:bibentry', namespaces=ns)
        
        self.stats = {
            'sections': len(sections),
            'equations': len(equations),
            'figures': len(figures),
            'tables': len(tables),
            'references': len(bibentries)
        }
        
        print(f"   📊 Extracted: {len(sections)} sections, {len(equations)} equations, {len(figures)} figures, {len(tables)} tables, {len(bibentries)} references")
    
    def _add_ids_if_needed(self, root):
        """Add IDs to elements that need them for ePub generation"""
        ns = {'ltx': 'http://dlmf.nist.gov/LaTeXML'}
        
        # LaTeXML already provides good IDs, but we can enhance if needed
        # For now, just ensure we have the structure we need
        
        # Count elements that already have IDs
        elements_with_ids = root.xpath('.//*[@xml:id]', namespaces={'xml': 'http://www.w3.org/XML/1998/namespace'})
        print(f"   📋 Found {len(elements_with_ids)} elements with xml:id attributes")
    
    def _assess_quality(self) -> float:
        """Use existing StructuralReviewer for quality assessment"""
        try:
            reviewer = StructuralReviewer(str(self.latex_file), str(self.xml_file))
            report = reviewer.generate_analysis_report()
            return report['overall_score']
        except Exception as e:
            print(f"   ⚠️ Quality assessment failed: {e}")
            return 0.0
    
    def _print_results(self, quality_score: float):
        """Print conversion results"""
        print(f"✅ XML saved: {self.xml_file}")
        
        print("\n📊 Extraction Summary:")
        for key, value in self.stats.items():
            print(f"✓ {key.title()}: {value}")
        
        rating = "EXCELLENT" if quality_score >= 90 else "GOOD" if quality_score >= 80 else "FAIR" if quality_score >= 70 else "POOR"
        print(f"📊 Quality Score: {quality_score:.1f}% ({rating})")
        
        print(f"\n🎉 LaTeXML conversion complete: {self.xml_file}")

def main():
    """Command-line interface"""
    if len(sys.argv) != 2:
        print("Usage: python3 latex_to_xml_latexml.py <latex_file>")
        sys.exit(1)
    
    latex_file = sys.argv[1]
    
    if not Path(latex_file).exists():
        print(f"Error: LaTeX file '{latex_file}' not found")
        sys.exit(1)
    
    try:
        converter = LaTeXMLConverter(latex_file)
        output_file = converter.convert_to_xml()
        print(f"\n✅ Success! XML output: {output_file}")
    except Exception as e:
        print(f"\n❌ Conversion failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
