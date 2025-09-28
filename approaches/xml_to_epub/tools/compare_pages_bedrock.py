#!/usr/bin/env python3
"""
Compare ePub generated page with original paper page using Amazon Bedrock
"""

import boto3
import base64
import json
import sys
import tempfile
import re
from pathlib import Path
from PIL import Image
import io

def resize_image(image_path, max_size_mb=4):
    """Resize image to be under max_size_mb using PIL"""
    # Open and resize image
    with Image.open(image_path) as img:
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize to reasonable dimensions (use LANCZOS for older PIL versions)
        img.thumbnail((800, 1200), Image.LANCZOS)
        
        # Save to bytes with compression
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG', optimize=True)
        img_bytes.seek(0)
        
        return img_bytes.getvalue()

def encode_image(image_path):
    """Encode image to base64, resizing if needed"""
    # Check file size
    file_size = Path(image_path).stat().st_size
    if file_size > 4 * 1024 * 1024:  # 4MB threshold
        print(f"   Resizing large image ({file_size / 1024 / 1024:.1f}MB)...")
        resized_bytes = resize_image(image_path)
        return base64.b64encode(resized_bytes).decode('utf-8')
    else:
        with open(image_path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

def compare_pages_with_bedrock(original_page, epub_page, schema_file=None, xml_file=None):
    """Use Bedrock to compare two page images and analyze XML against schema"""
    
    # Initialize Bedrock client
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    # Encode both images
    print("📸 Encoding images...")
    original_b64 = encode_image(original_page)
    epub_b64 = encode_image(epub_page)
    
    # Read schema and XML content if provided
    schema_content = ""
    xml_content = ""
    
    if schema_file and Path(schema_file).exists():
        with open(schema_file, 'r') as f:
            schema_content = f.read()
        print("📋 Schema loaded")
    
    if xml_file and Path(xml_file).exists():
        with open(xml_file, 'r') as f:
            xml_content = f.read()
        print("📄 XML file loaded")
    
    # Prepare enhanced message
    prompt = """Please analyze these academic paper pages and XML conversion:

1. **Visual Comparison**: Compare the original paper page (first image) with the ePub-generated page (second image)
2. **XML Analysis**: Review the generated XML against the schema to identify structural issues
3. **Specific Recommendations**: Provide concrete XML changes to fix identified problems

Focus on:
- Missing bibliography entries and incomplete data
- Schema compliance issues  
- Formatting and structure problems
- Specific XML modifications needed

Please provide actionable XML corrections that can be implemented."""

    if schema_content:
        prompt += f"\n\n**SCHEMA:**\n```xml\n{schema_content[:2000]}...\n```"
    
    if xml_content:
        # Show relevant parts of XML (references section)
        refs_match = re.search(r'<references>.*?</references>', xml_content, re.DOTALL)
        if refs_match:
            prompt += f"\n\n**CURRENT XML REFERENCES:**\n```xml\n{refs_match.group(0)[:1500]}...\n```"
    
    message = {
        "role": "user",
        "content": [
            {"text": prompt},
            {
                "image": {
                    "format": "png" if original_page.suffix == '.png' else "jpeg",
                    "source": {"bytes": base64.b64decode(original_b64)}
                }
            },
            {
                "image": {
                    "format": "png",
                    "source": {"bytes": base64.b64decode(epub_b64)}
                }
            }
        ]
    }
    
    # Call Bedrock
    print("🤖 Calling Bedrock Claude for enhanced analysis...")
    try:
        response = bedrock.converse(
            modelId="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            messages=[message],
            inferenceConfig={
                "maxTokens": 3000,
                "temperature": 0.1
            }
        )
        
        analysis = response['output']['message']['content'][0]['text']
        return analysis
        
    except Exception as e:
        print(f"❌ Bedrock API error: {e}")
        return None

def main():
    # Define paths - compare hybrid approach
    original_page = Path("/home/aiuser/workspace/approaches/xml_to_epub/Other Research/pages/1301.3781v3_page-12.jpg")
    epub_page = Path("/home/aiuser/workspace/approaches/xml_to_epub/output/epub_pages/Untitled_page-10.png")
    schema_file = Path("/home/aiuser/workspace/approaches/xml_to_epub/academic_paper_schema.xsd")
    xml_file = Path("/home/aiuser/workspace/approaches/xml_to_epub/output/efficient-v22_hybrid.xml")
    
    # Check if files exist
    if not original_page.exists():
        print(f"❌ Original page not found: {original_page}")
        return
    
    if not epub_page.exists():
        print(f"❌ ePub page not found: {epub_page}")
        return
    
    print("🔍 Hybrid Approach Analysis:")
    print(f"   Original: {original_page.name}")
    print(f"   ePub:     {epub_page.name}")
    print(f"   Schema:   {schema_file.name}")
    print(f"   XML:      {xml_file.name}")
    
    # Enhanced comparison with schema and XML analysis
    analysis = compare_pages_with_bedrock(original_page, epub_page, schema_file, xml_file)
    
    if analysis:
        print("\n" + "="*60)
        print("📊 HYBRID APPROACH ANALYSIS RESULTS")
        print("="*60)
        print(analysis)
        print("="*60)
        
        # Save analysis to file
        output_file = Path("output/hybrid_analysis_results.txt")
        with open(output_file, 'w') as f:
            f.write("HYBRID APPROACH ANALYSIS - HEURISTICS + LLM\n")
            f.write("="*60 + "\n\n")
            f.write(f"Original: {original_page}\n")
            f.write(f"ePub:     {epub_page}\n")
            f.write(f"Schema:   {schema_file}\n")
            f.write(f"XML:      {xml_file}\n\n")
            f.write(analysis)
        
        print(f"\n💾 Hybrid analysis saved to: {output_file}")
    else:
        print("❌ Failed to get analysis from Bedrock")

if __name__ == "__main__":
    main()
