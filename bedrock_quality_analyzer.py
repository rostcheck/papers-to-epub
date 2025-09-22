#!/usr/bin/env python3
import json
import subprocess
import re
import zipfile
from pathlib import Path
from bs4 import BeautifulSoup

class BedrockQualityAnalyzer:
    def __init__(self, epub_path):
        self.epub_path = Path(epub_path)
        
    def analyze_with_bedrock(self):
        """Use Bedrock to analyze ePub quality"""
        print(f"🤖 Running Bedrock quality analysis on {self.epub_path.name}")
        
        # Extract and sample content
        text_samples = self._extract_text_samples()
        if not text_samples:
            return {"error": "Could not extract text samples"}
        
        # Analyze each sample
        results = {}
        for section, text in text_samples.items():
            if len(text.strip()) > 50:  # Only analyze substantial content
                analysis = self._analyze_text_with_bedrock(text, section)
                results[section] = analysis
        
        return self._summarize_bedrock_results(results)
    
    def _extract_text_samples(self):
        """Extract text samples from key sections of the ePub"""
        try:
            with zipfile.ZipFile(self.epub_path, 'r') as epub:
                # Find the main HTML content file
                html_content = None
                for filename in ['index.html', 'content.html', 'text.html']:
                    try:
                        html_content = epub.read(filename).decode('utf-8')
                        break
                    except KeyError:
                        continue
                
                if not html_content:
                    # Try to find any HTML file
                    html_files = [f for f in epub.namelist() if f.endswith('.html') or f.endswith('.xhtml')]
                    if html_files:
                        html_content = epub.read(html_files[0]).decode('utf-8')
                
                if not html_content:
                    return {}
                
            # Parse HTML and extract clean text
            soup = BeautifulSoup(html_content, 'html.parser')
            paragraphs = [p.get_text().strip() for p in soup.find_all('p') if p.get_text().strip()]
            
            if len(paragraphs) < 3:
                return {}
            
            # Sample key sections
            total_paras = len(paragraphs)
            samples = {
                "beginning": " ".join(paragraphs[:min(5, total_paras//3)]),
                "middle": " ".join(paragraphs[total_paras//3:2*total_paras//3][:5]),
                "end": " ".join(paragraphs[-min(3, total_paras//4):])
            }
            
            return samples
            
        except Exception as e:
            print(f"Error extracting text: {e}")
            return {}
    
    def _analyze_text_with_bedrock(self, text, section):
        """Analyze text quality using Bedrock"""
        # Truncate if too long (cost control)
        if len(text) > 2000:
            text = text[:2000] + "..."
        
        prompt = f"""You are analyzing text from a PDF-to-ePub conversion to detect FORMATTING DEFECTS.

EXAMPLES of formatting issues to detect:
- Missing text: "We conducted experiments to validate our" (sentence cuts off)
- Footer intrusion: "The results show https://example.com/paper significant improvement" (URL inserted mid-paragraph)
- Broken citations: "As shown by Smith et al. the method works" (missing closing bracket)
- Word fragmentation: "The res ults show signif icant improve ment" (words split incorrectly)
- Repeated headers: "Introduction Introduction The main topic is..." (duplicate titles)

IGNORE content quality - only flag technical formatting defects.

Text from {section} section:
{text}

Respond with JSON:
{{
  "has_missing_text": true/false,
  "has_footer_intrusion": true/false,
  "has_broken_citations": true/false,
  "has_word_fragmentation": true/false,
  "formatting_issues": ["specific issues found"],
  "overall_score": 1-10,
  "severity": "LOW|MEDIUM|HIGH"
}}"""

        try:
            body = {
                "messages": [{
                    "role": "user", 
                    "content": [{"text": prompt}]
                }],
                "inferenceConfig": {
                    "maxTokens": 250,
                    "temperature": 0.1
                }
            }
            
            body_json = json.dumps(body)
            body_b64 = subprocess.check_output(['base64', '-w', '0'], input=body_json.encode()).decode()
            
            cmd = f"""
            bash -c 'source ~/workspace/.secure-agent/bin/aws-creds && 
            ~/workspace/.secure-agent/tools/aws-v2-bin/aws bedrock-runtime invoke-model \
                --model-id amazon.nova-micro-v1:0 \
                --region us-east-1 \
                --body "{body_b64}" \
                /tmp/bedrock_quality_response.json'
            """
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                with open('/tmp/bedrock_quality_response.json', 'r') as f:
                    response = json.load(f)
                    response_text = response['output']['message']['content'][0]['text'].strip()
                    
                    # Handle markdown code blocks
                    if "```json" in response_text:
                        json_start = response_text.find("```json") + 7
                        json_end = response_text.find("```", json_start)
                        if json_end > json_start:
                            response_text = response_text[json_start:json_end].strip()
                    
                    try:
                        return json.loads(response_text)
                    except json.JSONDecodeError:
                        return {"raw_response": response_text, "error": "Could not parse JSON"}
            else:
                return {"error": f"Bedrock call failed: {result.stderr}"}
                
        except Exception as e:
            return {"error": f"Analysis error: {e}"}
    
    def _summarize_bedrock_results(self, results):
        """Summarize Bedrock analysis results"""
        if not results:
            return {"error": "No analysis results"}
        
        # Count issues and calculate scores
        all_issues = []
        severities = []
        scores = []
        issue_counts = {
            "missing_text": 0,
            "footer_intrusion": 0, 
            "broken_citations": 0,
            "word_fragmentation": 0
        }
        
        for section, analysis in results.items():
            if "error" not in analysis:
                if "formatting_issues" in analysis:
                    all_issues.extend(analysis["formatting_issues"])
                
                if "severity" in analysis:
                    severities.append(analysis["severity"])
                
                if "overall_score" in analysis:
                    scores.append(analysis["overall_score"])
                
                # Count specific issue types
                for issue_type in issue_counts:
                    if f"has_{issue_type}" in analysis and analysis[f"has_{issue_type}"]:
                        issue_counts[issue_type] += 1
        
        # Calculate overall metrics
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Determine severity
        if "HIGH" in severities:
            overall_severity = "HIGH"
        elif "MEDIUM" in severities:
            overall_severity = "MEDIUM"
        else:
            overall_severity = "LOW"
        
        quality_level = "EXCELLENT" if avg_score >= 9 else \
                       "GOOD" if avg_score >= 7 else \
                       "FAIR" if avg_score >= 5 else "POOR"
        
        return {
            "overall_score": round(avg_score, 1),
            "quality_level": quality_level,
            "severity": overall_severity,
            "issue_counts": issue_counts,
            "formatting_issues": list(set(all_issues)),
            "section_details": results
        }

def main():
    """Test the Bedrock quality analyzer"""
    epub_dir = Path("epub_books")
    epub_files = list(epub_dir.glob("*.epub"))[:2]  # Test on first 2 files
    
    for epub_file in epub_files:
        analyzer = BedrockQualityAnalyzer(epub_file)
        result = analyzer.analyze_with_bedrock()
        
        print(f"\n=== Bedrock Formatting Analysis: {epub_file.name} ===")
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Formatting Quality: {result['quality_level']} ({result['overall_score']}/10)")
            print(f"Severity: {result['severity']}")
            print(f"Issue counts: {result['issue_counts']}")
            if result['formatting_issues']:
                print(f"Issues found: {result['formatting_issues'][:3]}...")  # Show first 3

if __name__ == "__main__":
    main()
