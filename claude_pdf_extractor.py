#!/usr/bin/env python3
import json
import subprocess
import tempfile
import base64
from pathlib import Path
import PyPDF2

def extract_pdf_with_claude(pdf_path):
    """Use Claude to extract and restructure content from problematic PDFs"""
    print(f"🤖 Using Claude to extract content from {Path(pdf_path).name}")
    
    try:
        # Extract raw text from PDF
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            raw_text = ""
            for page in reader.pages:
                raw_text += page.extract_text() + "\n"
        
        # Use Claude to restructure the content
        structured_content = restructure_with_claude(raw_text)
        
        if structured_content:
            return structured_content
        else:
            return {"error": "Claude extraction failed"}
            
    except Exception as e:
        return {"error": f"PDF extraction error: {e}"}

def restructure_with_claude(raw_text):
    """Use Claude to restructure fragmented PDF text"""
    
    prompt = f"""You are helping convert a PDF document to ePub format. The PDF text extraction is fragmented and contains web interface elements. Please restructure this content into a clean, readable document.

Tasks:
1. Remove web interface elements (New, Answer, Sources, Steps, etc.)
2. Reconstruct fragmented text into coherent paragraphs
3. Identify and structure main sections with proper headings
4. Fix broken sentences and word fragments
5. Create a logical document flow

Raw extracted text:
{raw_text}

Please return a JSON object with:
{{
  "title": "document title",
  "sections": [
    {{"heading": "Section Name", "content": "paragraph content"}},
    {{"heading": "Another Section", "content": "more content"}}
  ],
  "summary": "brief description of what this document is about"
}}"""

    try:
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 8000,
            "temperature": 0.1,
            "messages": [{
                "role": "user", 
                "content": [{"type": "text", "text": prompt}]
            }]
        }
        
        body_json = json.dumps(body)
        body_b64 = base64.b64encode(body_json.encode()).decode()
        
        cmd = f"""
        bash -c 'source ~/workspace/.secure-agent/bin/aws-creds && 
        ~/workspace/.secure-agent/tools/aws-v2-bin/aws bedrock-runtime invoke-model \
            --model-id us.anthropic.claude-3-5-sonnet-20241022-v2:0 \
            --region us-east-1 \
            --body "{body_b64}" \
            /tmp/claude_pdf_response.json'
        """
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            with open('/tmp/claude_pdf_response.json', 'r') as f:
                response = json.load(f)
                response_text = response['content'][0]['text'].strip()
                
                # Handle JSON in markdown blocks
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    if json_end > json_start:
                        response_text = response_text[json_start:json_end].strip()
                
                try:
                    return json.loads(response_text)
                except json.JSONDecodeError:
                    return {"error": "Could not parse Claude response", "raw": response_text}
        else:
            return {"error": f"Claude call failed: {result.stderr}"}
            
    except Exception as e:
        return {"error": f"Claude processing error: {e}"}

def create_epub_from_claude_content(content, output_path):
    """Create ePub from Claude-structured content"""
    
    if "error" in content:
        print(f"Cannot create ePub: {content['error']}")
        return False
    
    try:
        # Create HTML content
        html_content = f"""<?xml version='1.0' encoding='utf-8'?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{content.get('title', 'Extracted Document')}</title>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
</head>
<body>
    <h1>{content.get('title', 'Extracted Document')}</h1>
    
    <div class="summary">
        <h2>Summary</h2>
        <p>{content.get('summary', 'Document extracted and restructured from PDF.')}</p>
    </div>
"""
        
        # Add sections
        for section in content.get('sections', []):
            html_content += f"""
    <div class="section">
        <h2>{section.get('heading', 'Section')}</h2>
        <p>{section.get('content', '')}</p>
    </div>
"""
        
        html_content += """
</body>
</html>"""
        
        # Create temporary HTML file and convert to ePub
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as temp_html:
            temp_html.write(html_content)
            temp_html_path = temp_html.name
        
        # Convert HTML to ePub
        cmd = ["ebook-convert", temp_html_path, str(output_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Clean up
        Path(temp_html_path).unlink()
        
        if result.returncode == 0:
            print(f"✓ Claude-enhanced ePub created: {output_path.name}")
            return True
        else:
            print(f"✗ ePub creation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Error creating ePub: {e}")
        return False

def main():
    """Test Claude PDF extraction"""
    pdf_path = "./Deep Research/How are deep research models architected_.pdf"
    
    if Path(pdf_path).exists():
        content = extract_pdf_with_claude(pdf_path)
        print("Claude extraction result:")
        print(json.dumps(content, indent=2))
    else:
        print("Test PDF not found")

if __name__ == "__main__":
    main()
