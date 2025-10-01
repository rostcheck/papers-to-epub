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
    
    def call_llm(self, prompt: str, input_text: str, model_id: str = 'us.anthropic.claude-sonnet-4-20250514-v1:0') -> str:
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
            
            # Process citations while bibref elements still exist
            self._process_citations_early()
            
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
    
    def _process_citations_early(self):
        """Process citations while bibref elements still exist"""
        try:
            # Register xml namespace before parsing to handle xml:id attributes
            etree.register_namespace('xml', 'http://www.w3.org/XML/1998/namespace')
            
            # Parse the XML
            tree = etree.parse(str(self.xml_file))
            root = tree.getroot()
            ns = {'ltx': 'http://dlmf.nist.gov/LaTeXML'}
            
            # Phase 1: Build author-year mapping from bibliography
            ref_key_to_citation = {}
            author_year_counts = {}
            
            bibitems = root.xpath('.//ltx:bibitem', namespaces=ns)
            for bibitem in bibitems:
                key = bibitem.get('key')
                if key:
                    bibblock = bibitem.find('.//ltx:bibblock', namespaces=ns)
                    if bibblock is not None and bibblock.text:
                        author_year = self._extract_author_year_regex(bibblock.text)
                        
                        # Track duplicates
                        if author_year in author_year_counts:
                            author_year_counts[author_year] += 1
                            suffix = chr(ord('a') + author_year_counts[author_year] - 1)
                            ref_key_to_citation[key] = f"{author_year}{suffix}"
                        else:
                            author_year_counts[author_year] = 1
                            ref_key_to_citation[key] = author_year
                    else:
                        ref_key_to_citation[key] = key
            
            # Phase 2: Apply citations using pre-computed mapping
            citations = root.xpath('//ltx:cite', namespaces=ns)
            
            for cite in citations:
                bibrefs = cite.xpath('.//ltx:bibref', namespaces=ns)
                
                if bibrefs:
                    citation_parts = []
                    for bibref in bibrefs:
                        ref_keys = bibref.get('bibrefs', '').split(',')
                        for ref_key in ref_keys:
                            ref_key = ref_key.strip()
                            if ref_key and ref_key not in citation_parts:
                                citation_format = ref_key_to_citation.get(ref_key, ref_key)
                                citation_parts.append(citation_format)
                    
                    if citation_parts:
                        # Preserve any trailing text after the citation
                        tail_text = cite.tail or ""
                        
                        # Replace citation content with meaningful keys
                        cite.clear()
                        cite.text = f"[{', '.join(citation_parts)}]"
                        cite.tail = tail_text
                    else:
                        # Remove empty citations completely
                        parent = cite.getparent()
                        if parent is not None:
                            parent.remove(cite)
                else:
                    # Remove citations with no bibrefs
                    parent = cite.getparent()
                    if parent is not None:
                        parent.remove(cite)
            
            # Remove the empty first bibliography, keep the populated second one
            first_bib = root.find('.//ltx:bibliography', namespaces=ns)
            if first_bib is not None and not first_bib.find('.//ltx:bibitem', namespaces=ns):
                parent = first_bib.getparent()
                if parent is not None:
                    parent.remove(first_bib)
            
            # Add author+year tags to bibliography entries for easy matching
            self._add_author_year_tags(root, ref_key_to_citation, ns)
            
            # Save the updated XML
            tree.write(str(self.xml_file), encoding='utf-8', pretty_print=True, xml_declaration=True)
            print(f"   ✅ Early citation processing complete (using LaTeXML bibliography)")
            
        except Exception as e:
            print(f"   ⚠️ Early citation processing failed: {e}")
    
    def _extract_author_year_regex(self, bibblock_text):
        """Extract author surname and year using regex"""
        import re
        
        # Extract year (very reliable)
        year_match = re.search(r'\b(19|20)\d{2}\b', bibblock_text)
        year = year_match.group(0) if year_match else ""
        
        # Extract first author surname - try common patterns
        author = None
        
        # Pattern 1: "Y. Bengio," -> "Bengio"
        author_match = re.search(r'^\s*[A-Z]\.\s*([A-Z][a-z]+),', bibblock_text.strip())
        if author_match:
            author = author_match.group(1)
        else:
            # Pattern 2: "Bengio, Y." -> "Bengio"  
            author_match = re.search(r'^\s*([A-Z][a-z]+),', bibblock_text.strip())
            if author_match:
                author = author_match.group(1)
            else:
                # Pattern 3: "R. Collobert and J. Weston" -> "Collobert"
                author_match = re.search(r'^\s*[A-Z]\.\s*([A-Z][a-z]+)\s+and', bibblock_text.strip())
                if author_match:
                    author = author_match.group(1)
        
        if author and year:
            return f"{author}{year}"
        else:
            # Fallback: use any capitalized word + year
            fallback_match = re.search(r'([A-Z][a-z]+)', bibblock_text)
            fallback_author = fallback_match.group(1) if fallback_match else "Unknown"
            return f"{fallback_author}{year}"
    
    def _add_author_year_tags(self, root, ref_key_to_citation, ns):
        """Add author+year tags to bibliography entries"""
        try:
            # Find all bibliography items
            bibitems = root.xpath('.//ltx:bibitem', namespaces=ns)
            
            for bibitem in bibitems:
                key = bibitem.get('key')
                if key and key in ref_key_to_citation:
                    # Get the author+year format for this entry
                    author_year = ref_key_to_citation[key]
                    
                    # Add author+year to the beginning of bibblock text
                    bibblock = bibitem.find('.//ltx:bibblock', namespaces=ns)
                    if bibblock is not None and bibblock.text:
                        if not bibblock.text.strip().startswith(author_year):
                            bibblock.text = f"{author_year}: {bibblock.text.strip()}"
                            
        except Exception as e:
            print(f"   ⚠️ Failed to add author+year tags: {e}")
    
    def _add_references_section(self, root, bibliography, ns):
        """Replace existing empty bibliography with populated entries"""
        if not bibliography:
            return
        
        # Find the first bibliography section (the empty one)
        first_bib = root.find('.//ltx:bibliography[@xml:id="bib"]', namespaces=ns)
        if first_bib is not None:
            biblist = first_bib.find('.//ltx:biblist', namespaces=ns)
            if biblist is not None:
                # Clear and populate the first bibliography
                biblist.clear()
                
                # Add each bibliography entry
                for i, (key, entry) in enumerate(bibliography.items(), 1):
                    bibitem = etree.SubElement(biblist, '{http://dlmf.nist.gov/LaTeXML}bibitem')
                    bibitem.set('key', key)
                    bibitem.set('xml:id', f'bib.{key}')
                    
                    # Add tags for numbering
                    tags = etree.SubElement(bibitem, '{http://dlmf.nist.gov/LaTeXML}tags')
                    tag = etree.SubElement(tags, '{http://dlmf.nist.gov/LaTeXML}tag')
                    tag.text = f'[{i}]'
                    
                    # Add bibliographic data
                    bibblock = etree.SubElement(bibitem, '{http://dlmf.nist.gov/LaTeXML}bibblock')
                    
                    # Format: Authors. Title. Year.
                    ref_parts = []
                    if entry.get('authors'):
                        authors = ', '.join(entry['authors'])
                        ref_parts.append(authors)
                    
                    if entry.get('title'):
                        ref_parts.append(f'"{entry["title"]}"')
                    
                    if entry.get('year'):
                        ref_parts.append(f'({entry["year"]})')
                    
                    bibblock.text = '. '.join(ref_parts) + '.'
        
        # Remove the second bibliography section (biba)
        second_bib = root.find('.//ltx:bibliography[@xml:id="biba"]', namespaces=ns)
        if second_bib is not None:
            parent = second_bib.getparent()
            if parent is not None:
                parent.remove(second_bib)
        
        print(f"   ✅ Replaced bibliography section with {len(bibliography)} entries")
    
    def _cognitive_enhancement(self):
        """Cognitive enhancement of LaTeXML output - fix references and citations only"""
        try:
            # Parse the XML
            tree = etree.parse(str(self.xml_file))
            root = tree.getroot()
            
            # Extract statistics first
            self._extract_stats(root)
            
            # Fix authors (clean up messy personname content)
            self._fix_authors_cognitively(root)
            
            # Skip reference fixing - LaTeXML already handles references correctly
            # self._fix_references_cognitively(root)
            
            # Fix citations (convert empty citations to proper format)
            self._fix_citations_cognitively(root)
            
            # Add any necessary IDs
            self._add_ids_if_needed(root)
            
            # Save enhanced XML
            tree.write(str(self.xml_file), encoding='utf-8', pretty_print=True, xml_declaration=True)
            
            print(f"   ✅ Cognitive enhancement complete")
            
        except Exception as e:
            print(f"   ⚠️ Cognitive enhancement failed: {e}")
    
    def _fix_authors_cognitively(self, root):
        """Clean up messy author information using Bedrock"""
        ns = {'ltx': 'http://dlmf.nist.gov/LaTeXML'}
        creators = root.xpath('//ltx:creator[@role="author"]', namespaces=ns)
        
        for creator in creators:
            personname = creator.find('.//ltx:personname', namespaces=ns)
            if personname is not None:
                # Get the messy content
                messy_content = etree.tostring(personname, encoding='unicode', method='xml')
                
                prompt = '''Parse this messy author information from LaTeX/XML and extract clean author names with their institutions and emails.
The ERROR elements with \\And and \\AND are author separators.
Return only clean XML with separate creator elements for each author.

Return format: <creators><creator><name>First Last</name><institution>Institution Name</institution><email>email@domain.com</email></creator></creators>'''
                
                try:
                    result = self.bedrock.call_llm(prompt, messy_content, 'us.anthropic.claude-sonnet-4-20250514-v1:0')
                    
                    # Parse the result and create separate creator elements
                    if '<creators>' in result and '</creators>' in result:
                        try:
                            from xml.etree import ElementTree as ET
                            # Extract the creators XML
                            creators_xml = result[result.find('<creators>'):result.find('</creators>') + 11]
                            creators_root = ET.fromstring(creators_xml)
                            
                            # Get the parent of the current creator element
                            parent = creator.getparent()
                            creator_index = list(parent).index(creator)
                            
                            # Remove the original creator
                            parent.remove(creator)
                            
                            # Add new creator elements for each author
                            for i, author_elem in enumerate(creators_root.findall('creator')):
                                new_creator = etree.Element('{http://dlmf.nist.gov/LaTeXML}creator')
                                new_creator.set('role', 'author')
                                
                                new_personname = etree.SubElement(new_creator, '{http://dlmf.nist.gov/LaTeXML}personname')
                                
                                # Add name
                                name = author_elem.find('name')
                                if name is not None:
                                    new_personname.text = name.text
                                
                                # Add institution
                                institution = author_elem.find('institution')
                                if institution is not None:
                                    br1 = etree.SubElement(new_personname, '{http://dlmf.nist.gov/LaTeXML}break')
                                    br1.tail = institution.text
                                
                                # Add email
                                email = author_elem.find('email')
                                if email is not None:
                                    br2 = etree.SubElement(new_personname, '{http://dlmf.nist.gov/LaTeXML}break')
                                    email_elem = etree.SubElement(new_personname, '{http://dlmf.nist.gov/LaTeXML}text')
                                    email_elem.set('font', 'typewriter')
                                    email_elem.text = email.text
                                
                                # Insert the new creator at the correct position
                                parent.insert(creator_index + i, new_creator)
                            
                            print(f"   ✅ Created separate creator elements for each author")
                            
                        except Exception as parse_error:
                            print(f"   ⚠️ XML parsing failed: {parse_error}")
                            # Keep original if parsing fails
                    
                    else:
                        print(f"   ⚠️ No valid XML structure in result")
                        
                except Exception as e:
                    print(f"   ⚠️ Author cleaning failed: {e}")
    
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
        """Fix empty citations using bibliography extraction"""
        ns = {'ltx': 'http://dlmf.nist.gov/LaTeXML'}
        citations = root.xpath('//ltx:cite', namespaces=ns)
        
        print(f"   📚 Fixing {len(citations)} citations...")
        
        # Extract bibliography from LaTeX source
        bibliography = self._extract_bibliography_from_latex()
        
        for cite in citations:
            # First try bibref elements (original LaTeXML format)
            bibrefs = cite.xpath('.//ltx:bibref', namespaces=ns)
            
            if bibrefs:
                # Use original bibref keys
                citation_parts = []
                for bibref in bibrefs:
                    ref_keys = bibref.get('bibrefs', '').split(',')
                    for ref_key in ref_keys:
                        ref_key = ref_key.strip()
                        if ref_key and ref_key in bibliography:
                            entry = bibliography[ref_key]
                            if entry.get('authors'):
                                first_author = entry['authors'][0].split()[-1]  # Last name
                                citation_parts.append(first_author)
                            else:
                                citation_parts.append(ref_key)
                        else:
                            citation_parts.append(ref_key or 'Unknown')
                
                if citation_parts:
                    cite.clear()
                    cite.text = f"[{', '.join(citation_parts)}]"
                    continue
            
            # Fallback to ref elements (processed format)
            refs = cite.xpath('.//ltx:ref', namespaces=ns)
            if refs:
                citation_parts = []
                for ref in refs:
                    ref_id = ref.get('idref', '')
                    ref_key = ref_id.split('.')[-1] if '.' in ref_id else ref_id
                    
                    # Try to match by looking for the key in bibliography keys
                    matched_key = None
                    for bib_key in bibliography.keys():
                        if ref_key in bib_key or bib_key in ref_key:
                            matched_key = bib_key
                            break
                    
                    if matched_key:
                        entry = bibliography[matched_key]
                        if entry.get('authors'):
                            first_author = entry['authors'][0].split()[-1]
                            citation_parts.append(first_author)
                        else:
                            citation_parts.append(matched_key)
                    else:
                        citation_parts.append(ref_key or 'Unknown')
                
                if citation_parts:
                    cite.clear()
                    cite.text = f"[{', '.join(citation_parts)}]"
    
    def _extract_bibliography_from_latex(self):
        """Extract bibliography entries from LaTeX source using Bedrock"""
        try:
            # Read the LaTeX source
            with open(self.latex_file, 'r', encoding='utf-8') as f:
                latex_content = f.read()
            
            # Find bibliography section
            bib_start = latex_content.find('\\begin{thebibliography}')
            bib_end = latex_content.find('\\end{thebibliography}')
            
            if bib_start == -1 or bib_end == -1:
                return {}
            
            bib_content = latex_content[bib_start:bib_end + len('\\end{thebibliography}')]
            
            prompt = '''Parse this LaTeX bibliography and extract citation information.
Return JSON with citation keys as keys and objects with authors (array), title, year fields.

Format: {"key1": {"authors": ["Author Name"], "title": "Title", "year": "2023"}}'''
            
            result = self.bedrock.call_llm(prompt, bib_content, 'us.anthropic.claude-sonnet-4-20250514-v1:0')
            
            # Parse JSON result
            import json
            if result.strip().startswith('{'):
                return json.loads(result)
            else:
                # Extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            
        except Exception as e:
            print(f"   ⚠️ Bibliography extraction failed: {e}")
        
        return {}
    
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
