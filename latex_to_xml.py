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

# Import quality assessment
from review_structure import StructuralReviewer

class BedrockClient:
    """Clean Bedrock client with caching and Converse API"""
    
    def __init__(self):
        self.client = None
        
    def _get_client(self):
        if not self.client:
            self.client = boto3.client('bedrock-runtime', region_name='us-east-1')
        return self.client
    
    def call_llm(self, prompt: str, input_text: str, model_id: str = 'us.anthropic.claude-sonnet-4-20250514-v1:0', max_tokens: int = 4000) -> str:
        """Call Bedrock LLM with automatic caching"""
        # Create cache key from model + prompt + input + max_tokens
        cache_content = f"{model_id}:{prompt}:{input_text}:{max_tokens}"
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
                    'maxTokens': max_tokens,
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
        self.xml_file = self.output_dir / f"{base_name}.xml"
        
        self.stats = {}
        self.bedrock = BedrockClient()
    
    def _ensure_expanded_latex(self, latex_path: str) -> str:
        """Expand LaTeX file if needed, return path to expanded version"""
        latex_path = Path(latex_path)
        
        # If directory, find main .tex file
        if latex_path.is_dir():
            main_files = list(latex_path.glob("*.tex"))
            if len(main_files) == 1:
                latex_path = main_files[0]
            else:
                # Look for common main file names
                for name in ["main.tex", "paper.tex", f"{latex_path.name}.tex"]:
                    if (latex_path / name).exists():
                        latex_path = latex_path / name
                        break
                else:
                    # Filter out expanded files and look for conference/paper patterns
                    candidates = [f for f in main_files if not f.name.endswith('_expanded.tex')]
                    conference_files = [f for f in candidates if 'conference' in f.name or 'paper' in f.name]
                    
                    if len(conference_files) == 1:
                        latex_path = conference_files[0]
                    elif len(candidates) == 1:
                        latex_path = candidates[0]
                    else:
                        raise ValueError(f"Multiple .tex files found in {latex_path}. Candidates: {[f.name for f in candidates]}")
        
        # Create expanded filename
        expanded_path = latex_path.parent / f"{latex_path.stem}_expanded.tex"
        
        # Check if expansion needed
        if expanded_path.exists():
            # Check if expanded file is newer than all source files
            expanded_time = expanded_path.stat().st_mtime
            if self._is_expansion_current(latex_path, expanded_time):
                print(f"   ✅ Using existing expanded file: {expanded_path}")
                return str(expanded_path)
        
        # Expand the file
        print(f"   📄 Expanding LaTeX includes: {latex_path}")
        expanded_content = self._expand_latex_recursive(latex_path)
        
        with open(expanded_path, 'w', encoding='utf-8') as f:
            f.write(expanded_content)
        
        return str(expanded_path)
    
    def _is_expansion_current(self, main_file: Path, expanded_time: float) -> bool:
        """Check if expanded file is newer than all source files"""
        def check_file_time(file_path: Path) -> bool:
            if not file_path.exists():
                return True  # Missing files don't invalidate
            return file_path.stat().st_mtime <= expanded_time
        
        # Check main file
        if not check_file_time(main_file):
            return False
        
        # Check all included files recursively
        try:
            with open(main_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all input/include commands
            import re
            includes = re.findall(r'\\(?:input|include)\{([^}]+)\}', content)
            
            for include in includes:
                include_path = main_file.parent / f"{include}.tex"
                if include_path.exists() and not check_file_time(include_path):
                    return False
                    
        except Exception:
            return False  # If we can't check, assume stale
        
        return True
    
    def _expand_latex_recursive(self, latex_file: Path) -> str:
        """Recursively expand all input/include commands"""
        try:
            with open(latex_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"   ⚠️ Could not read {latex_file}: {e}")
            return ""
        
        # Replace input/include commands
        import re
        
        def replace_include(match):
            include_file = match.group(1)
            # Handle both with and without .tex extension
            if include_file.endswith('.tex'):
                include_path = latex_file.parent / include_file
            else:
                include_path = latex_file.parent / f"{include_file}.tex"
            
            if include_path.exists():
                # Recursively expand the included file
                included_content = self._expand_latex_recursive(include_path)
                return f"% Expanded from {include_file}\n{included_content}\n% End of {include_file}\n"
            else:
                print(f"   ⚠️ Include file not found: {include_path}")
                return match.group(0)  # Keep original if file not found
        
        # Replace both \input{} and \include{} commands
        content = re.sub(r'\\(?:input|include)\{([^}]+)\}', replace_include, content)
        
        return content
    
    def convert_to_xml(self) -> str:
        """Convert LaTeX to XML using LaTeXML with cognitive enhancement"""
        print("🚀 LaTeXML-based LaTeX-to-XML Converter")
        print("=" * 50)
        print(f"📋 Architecture: LaTeXML + cognitive post-processing")
        
        # Phase 0: Ensure LaTeX is expanded
        print("📄 Phase 0: LaTeX expansion...")
        expanded_latex = self._ensure_expanded_latex(self.latex_file)
        self.latex_file = Path(expanded_latex)  # Use expanded version for processing
        
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
            # Run from the LaTeX source directory so LaTeXML can find .bbl files
            latex_dir = self.latex_file.parent
            latex_filename = self.latex_file.name
            xml_output_path = self.xml_file.resolve()
            
            # Step 1: latexml
            cmd = ['latexml', '--dest', str(xml_output_path), latex_filename]
            print(f"   Running: {' '.join(cmd)} (from {latex_dir})")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=latex_dir)
            
            if result.returncode != 0:
                print(f"   ❌ LaTeXML failed with return code {result.returncode}")
                print(f"   STDERR: {result.stderr}")
                return False
            
            # Process citations and figures while preserving LaTeXML bibliography
            # self._process_citations_early()  # Disabled to preserve LaTeXML bibliography
            
            # Step 2: latexmlpost for MathML
            print(f"   Converting math to MathML...")
            post_cmd = ['latexmlpost', '--pmml', '--dest', str(xml_output_path), str(xml_output_path)]
            post_result = subprocess.run(post_cmd, capture_output=True, text=True, timeout=60)
            
            if post_result.returncode != 0:
                print(f"   ❌ MathML conversion failed: {post_result.stderr}")
                return False
            
            # Process figures after LaTeXML is complete
            self._process_figures_only()
            
            print(f"   ✅ LaTeXML with MathML completed successfully")
            return True
            
        except subprocess.TimeoutExpired:
            print("   ❌ LaTeXML timed out")
            return False
        except Exception as e:
            print(f"   ❌ LaTeXML error: {e}")
            return False
    
    def _process_figures_only(self):
        """Process figures: copy existing PNGs from subdirectories"""
        try:
            root = etree.parse(str(self.xml_file)).getroot()
            ns = {'ltx': 'http://dlmf.nist.gov/LaTeXML'}
            graphics = root.xpath('.//ltx:graphics', namespaces=ns)
            
            for graphic in graphics:
                graphic_name = graphic.get('graphic')
                if graphic_name and graphic_name.endswith('.png'):
                    latex_dir = self.latex_file.parent
                    png_source = latex_dir / graphic_name
                    png_dest = self.output_dir / Path(graphic_name).name
                    
                    if png_source.exists():
                        print(f"   🖼️ Copying PNG: {png_source.name}")
                        import shutil
                        shutil.copy2(png_source, png_dest)
                        
                        # Update XML to point to flattened filename
                        graphic.set('candidates', Path(graphic_name).name)
                        graphic.set('graphic', Path(graphic_name).stem)
            
            # Save updated XML with figure paths
            etree.ElementTree(root).write(str(self.xml_file), encoding='utf-8', xml_declaration=True)
            
        except Exception as e:
            print(f"   ⚠️ Figure processing failed: {e}")
    
    
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
            
            # Save the updated XML only if no bibliography section exists
            existing_bib = root.find('.//ltx:bibliography', namespaces=ns)
            if existing_bib is None:
                tree.write(str(self.xml_file), encoding='utf-8', pretty_print=True, xml_declaration=True)
                print(f"   ✅ Early citation processing complete (using LaTeXML bibliography)")
            else:
                print(f"   ✅ Early citation processing skipped (LaTeXML bibliography preserved)")
            
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
            
            # Fix citations (convert to author-year format using cognitive bibliography processing)
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
        """Fix citations using cognitive bibliography processing"""
        ns = {'ltx': 'http://dlmf.nist.gov/LaTeXML'}
        
        # Find bibliography section
        bibliography = root.find('.//ltx:bibliography', namespaces=ns)
        if bibliography is None:
            print(f"   ⚠️ No bibliography found, skipping citation processing")
            return
        
        # Extract essential bibliography information for Bedrock
        biblist = bibliography.find('.//ltx:biblist', namespaces=ns)
        if biblist is None:
            print(f"   ⚠️ No biblist found in bibliography")
            return
        
        # Extract key information from each bibitem
        bib_entries = []
        for bibitem in biblist.xpath('.//ltx:bibitem', namespaces=ns):
            xml_id = bibitem.get('xml:id', '')
            key = bibitem.get('key', '')
            
            # Extract author, year, title from tags
            tags = bibitem.find('.//ltx:tags', namespaces=ns)
            author_tag = tags.find('.//ltx:tag[@role="authors"]', namespaces=ns) if tags is not None else None
            year_tag = tags.find('.//ltx:tag[@role="year"]', namespaces=ns) if tags is not None else None
            title_tag = tags.find('.//ltx:tag[@role="title"]', namespaces=ns) if tags is not None else None
            
            entry_info = {
                'xml_id': xml_id,
                'key': key,
                'author': author_tag.text if author_tag is not None else '',
                'year': year_tag.text if year_tag is not None else '',
                'title': title_tag.text if title_tag is not None else ''
            }
            bib_entries.append(entry_info)
        
        # Create compact text representation for Bedrock
        bib_text = "Bibliography entries:\n"
        for entry in bib_entries:
            bib_text += f"ID: {entry['xml_id']}, Author: {entry['author']}, Year: {entry['year']}, Title: {entry['title']}\n"
        
        # Extract bibliography content for Bedrock
        bib_content = etree.tostring(bibliography, encoding='unicode')
        
        prompt = '''Parse this LaTeX bibliography XML and create properly formatted bibliography entries.

Example input:
<bibitem key="chollet2019" xml:id="bib.bib8">
  <tags><tag role="authors">Chollet</tag><tag role="year">2019</tag><tag role="title">On the measure of intelligence</tag></tags>
  <bibblock>F. Chollet (2019). On the measure of intelligence. arXiv preprint arXiv:1911.01547.</bibblock>
</bibitem>

Example output:
{
  "Chollet2019": "F. Chollet (2019). On the measure of intelligence. arXiv preprint arXiv:1911.01547."
}

Requirements:
- JSON key format: FirstAuthorLastName + Year (e.g. "Zhang2019", "Smith2020")  
- Value: Full formatted citation with all authors, title, venue details
- Include ALL authors from the original citation, not just first author
- Preserve all publication details (journal, pages, DOI, etc.)
- Return only valid JSON, no other text.'''
        
        print(f"   📚 Processing bibliography with Bedrock...")
        result = self.bedrock.call_llm(prompt, bib_content, max_tokens=8000)
        
        # Parse JSON response - no fallbacks
        clean_result = result.strip()
        if clean_result.startswith('```'):
            lines = clean_result.split('\n')
            clean_result = '\n'.join(lines[1:-1])
        
        bib_data = json.loads(clean_result)
        
        # Build citation mapping (XML ID -> citation key) and reverse lookup
        citation_map = {}
        xml_to_citation = {}
        
        # Need to map XML IDs to citation keys - extract from original bibliography
        biblist = bibliography.find('.//ltx:biblist', namespaces=ns)
        for bibitem in biblist.xpath('.//ltx:bibitem', namespaces=ns):
            xml_id = bibitem.get('xml:id', '')
            # Find matching citation key in bib_data by checking if any key matches this entry
            tags = bibitem.find('.//ltx:tags', namespaces=ns)
            if tags is not None:
                author_tag = tags.find('.//ltx:tag[@role="authors"]', namespaces=ns)
                year_tag = tags.find('.//ltx:tag[@role="year"]', namespaces=ns)
                if author_tag is not None and year_tag is not None:
                    # Try to match with generated citation keys
                    author_name = author_tag.text.split()[0] if author_tag.text else ''
                    year = year_tag.text or ''
                    expected_key = f"{author_name}{year}"
                    
                    # Find best match in bib_data keys
                    for citation_key in bib_data.keys():
                        if citation_key.startswith(author_name) and year in citation_key:
                            xml_to_citation[xml_id] = citation_key
                            break
            
        # Update citations in text
        citations = root.xpath('//ltx:cite', namespaces=ns)
        updated_count = 0
        for cite in citations:
            # Look for references to bibliography items
            refs = cite.xpath('.//ltx:ref', namespaces=ns)
            if refs:
                new_citations = []
                for ref in refs:
                    ref_id = ref.get('idref', '')
                    if ref_id in xml_to_citation:
                        new_citations.append(xml_to_citation[ref_id])
                
                if new_citations:
                    # Flatten citation to plain text
                    parent = cite.getparent()
                    citation_text = f"[{', '.join(new_citations)}]"
                    
                    # Get text before cite
                    before_text = parent.text or ""
                    
                    # Get text after cite  
                    after_text = cite.tail or ""
                    
                    # Combine all text
                    new_text = before_text + citation_text + after_text
                    
                    # Replace parent text and remove cite
                    parent.text = new_text
                    parent.remove(cite)
                    updated_count += 1
            else:
                # Handle direct citation text
                cite_text = cite.text or ''
                for xml_id, citation_key in xml_to_citation.items():
                    bib_key = xml_id.split('.')[-1] if '.' in xml_id else xml_id
                    if bib_key in cite_text:
                        # Flatten citation to plain text
                        parent = cite.getparent()
                        citation_text = cite_text.replace(f'[{bib_key}]', f'[{citation_key}]')
                        
                        # Get text before cite
                        before_text = parent.text or ""
                        
                        # Get text after cite  
                        after_text = cite.tail or ""
                        
                        # Combine all text
                        new_text = before_text + citation_text + after_text
                        
                        # Replace parent text and remove cite
                        parent.text = new_text
                        parent.remove(cite)
                        updated_count += 1
        
        # Clean up LaTeX artifacts in text content
        for text_node in root.xpath('//text()', namespaces=ns):
            if '\\xspace' in text_node:
                parent = text_node.getparent()
                if parent is not None:
                    # Replace \xspace with a space
                    cleaned_text = text_node.replace('\\xspace', ' ')
                    # Update the text content
                    if parent.text == text_node:
                        parent.text = cleaned_text
                    elif parent.tail == text_node:
                        parent.tail = cleaned_text
        
        # Rebuild bibliography with normalized format
        self._rebuild_bibliography(root, bibliography, bib_data, ns)
        
        print(f"   ✅ Processed {len(bib_data)} bibliography entries, updated {updated_count} citations")
    
    def _rebuild_bibliography(self, root, old_bib, bib_data, ns):
        """Rebuild bibliography with normalized entries"""
        # Create new bibliography structure
        new_bib = etree.Element('{http://dlmf.nist.gov/LaTeXML}bibliography')
        new_bib.set('{http://www.w3.org/XML/1998/namespace}id', 'bib')
        
        # Add title
        title = etree.SubElement(new_bib, '{http://dlmf.nist.gov/LaTeXML}title')
        title.text = 'References'
        
        # Add biblist
        biblist = etree.SubElement(new_bib, '{http://dlmf.nist.gov/LaTeXML}biblist')
        
        # Add entries using Bedrock's formatted output
        for i, (citation_key, formatted_entry) in enumerate(bib_data.items(), 1):
            bibitem = etree.SubElement(biblist, '{http://dlmf.nist.gov/LaTeXML}bibitem')
            bibitem.set('key', citation_key.lower())
            bibitem.set('{http://www.w3.org/XML/1998/namespace}id', f'bib.bib{i}')
            
            # Add tags
            tags = etree.SubElement(bibitem, '{http://dlmf.nist.gov/LaTeXML}tags')
            
            number_tag = etree.SubElement(tags, '{http://dlmf.nist.gov/LaTeXML}tag')
            number_tag.set('role', 'number')
            number_tag.text = str(i)
            
            refnum_tag = etree.SubElement(tags, '{http://dlmf.nist.gov/LaTeXML}tag')
            refnum_tag.set('role', 'refnum')
            refnum_tag.text = citation_key
            
            # Add bibblock with Bedrock's formatted entry (no number, XSLT adds it)
            bibblock = etree.SubElement(bibitem, '{http://dlmf.nist.gov/LaTeXML}bibblock')
            bibblock.text = f"[{citation_key}]: {formatted_entry}"
        
        # Replace old bibliography with new one
        parent = old_bib.getparent()
        if parent is not None:
            parent.replace(old_bib, new_bib)
    
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
        """LaTeXML-adapted quality assessment using StructuralReviewer logic"""
        try:
            tree = etree.parse(str(self.xml_file))
            root = tree.getroot()
            ns = {'ltx': 'http://dlmf.nist.gov/LaTeXML'}
            
            # Collect LaTeX metrics (reuse StructuralReviewer's LaTeX parsing)
            import re
            latex_content = Path(self.latex_file).read_text(encoding='utf-8')
            
            # LaTeX metrics
            latex_title = bool(re.search(r'\\title\{', latex_content))
            latex_authors = len(re.findall(r'\\author\{', latex_content))
            latex_abstract = bool(re.search(r'\\begin\{abstract\}', latex_content))
            latex_sections = len(re.findall(r'\\section\{', latex_content))
            latex_figures = len(re.findall(r'\\begin\{figure\}', latex_content))
            latex_tables = len(re.findall(r'\\begin\{table\}', latex_content))
            latex_bibitems = len(re.findall(r'\\bibitem\{', latex_content))
            
            # LaTeXML XML metrics
            xml_title = root.find('.//ltx:title', namespaces=ns) is not None
            xml_authors = len(root.xpath('.//ltx:creator', namespaces=ns))
            xml_abstract = root.find('.//ltx:abstract', namespaces=ns) is not None
            xml_sections = len(root.xpath('.//ltx:section', namespaces=ns))
            xml_figures = len(root.xpath('.//ltx:figure', namespaces=ns))
            xml_tables = len(root.xpath('.//ltx:table', namespaces=ns))
            xml_bibitems = len(root.xpath('.//ltx:bibitem', namespaces=ns))
            
            # Calculate component scores using StructuralReviewer's logic
            def safe_ratio(xml_count, latex_count):
                return min(xml_count / max(latex_count, 1), 1.0)
            
            # Metadata score (25%)
            metadata_score = (
                (1.0 if xml_title and latex_title else 0.0) * 0.4 +
                safe_ratio(xml_authors, latex_authors) * 0.4 +
                (1.0 if xml_abstract and latex_abstract else 0.0) * 0.2
            )
            
            # Structure score (20%)
            structure_score = safe_ratio(xml_sections, latex_sections)
            
            # Mathematics score (15%) - LaTeXML handles this well
            math_score = 0.9  # LaTeXML excels at math conversion
            
            # References score (20%)
            references_score = safe_ratio(xml_bibitems, latex_bibitems)
            
            # Tables/Figures score (20%)
            tables_figures_score = (
                safe_ratio(xml_tables, latex_tables) * 0.6 +
                safe_ratio(xml_figures, latex_figures) * 0.4
            )
            
            # Weighted overall score
            weights = {
                'metadata': 0.25,
                'structure': 0.20,
                'mathematics': 0.15,
                'references': 0.20,
                'tables_figures': 0.20
            }
            
            overall_score = (
                metadata_score * weights['metadata'] +
                structure_score * weights['structure'] +
                math_score * weights['mathematics'] +
                references_score * weights['references'] +
                tables_figures_score * weights['tables_figures']
            ) * 100
            
            return round(overall_score, 1)
            
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
        print("Usage: python3 latex_to_xml.py <latex_file>")
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
