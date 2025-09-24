#!/usr/bin/env python3
import os
import subprocess
import re
from pathlib import Path
try:
    import PyPDF2
except ImportError:
    print("PyPDF2 not found. Install with: pip3 install PyPDF2")
    exit(1)

def clean_filename(title):
    """Clean title for use as filename"""
    # Remove invalid filename characters
    cleaned = re.sub(r'[<>:"/\\|?*]', '', title)
    # Replace multiple spaces with single space
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    # Limit length
    return cleaned[:100] if len(cleaned) > 100 else cleaned

def extract_title_from_pdf(pdf_path):
    """Extract title from PDF using AWS Bedrock Nova Micro"""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            # Check metadata first, but validate it's not cryptic
            if reader.metadata and reader.metadata.title:
                title = reader.metadata.title.strip()
                if title and len(title) > 10 and not re.match(r'^(arXiv:|arXiv\d+|\d+\.\d+)', title):
                    return title
            
            # Extract text from first page
            if len(reader.pages) > 0:
                text = reader.pages[0].extract_text()[:1500]  # First 1500 chars
                
                # Use Bedrock to extract clean title
                bedrock_title = get_title_from_bedrock(text)
                if bedrock_title and len(bedrock_title) > 5:
                    return bedrock_title
                    
    except Exception as e:
        print(f"Could not extract title from {pdf_path}: {e}")
    
    return None

def get_title_from_bedrock(text):
    """Use AWS Bedrock Nova Micro to extract clean title"""
    import subprocess
    import json
    import tempfile
    import os
    
    try:
        # Create request body
        body = {
            "messages": [{
                "role": "user", 
                "content": [{
                    "text": f"Extract the main title from this academic paper text. Return only the clean, readable title without any formatting or extra text.\n\nText:\n{text}\n\nTitle:"
                }]
            }],
            "inferenceConfig": {
                "maxTokens": 50,
                "temperature": 0.1
            }
        }
        
        # Encode to base64
        body_json = json.dumps(body)
        body_b64 = subprocess.check_output(['base64', '-w', '0'], input=body_json.encode()).decode()
        
        # Call Bedrock
        cmd = f"""
        bash -c 'source ~/workspace/.secure-agent/bin/aws-creds && 
        ~/workspace/.secure-agent/tools/aws-v2-bin/aws bedrock-runtime invoke-model \
            --model-id amazon.nova-micro-v1:0 \
            --region us-east-1 \
            --body "{body_b64}" \
            /tmp/bedrock_response.json'
        """
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            with open('/tmp/bedrock_response.json', 'r') as f:
                response = json.load(f)
                title = response['output']['message']['content'][0]['text'].strip()
                # Clean up the title
                title = re.sub(r'^(Title:|The title is:?)\s*', '', title, flags=re.IGNORECASE)
                return title
        else:
            print(f"Bedrock call failed: {result.stderr}")
            
    except Exception as e:
        print(f"Error calling Bedrock: {e}")
    
    return None

def convert_pdf_to_epub(pdf_path, output_dir="epub_books"):
    """Convert a PDF to ePub format using Calibre's ebook-convert"""
    pdf_file = Path(pdf_path)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Extract title
    title = extract_title_from_pdf(pdf_path)
    if title:
        epub_name = clean_filename(title) + ".epub"
    else:
        epub_name = pdf_file.stem + ".epub"
    
    epub_path = output_path / epub_name
    
    try:
        cmd = ["ebook-convert", str(pdf_file), str(epub_path)]
        
        # Add title metadata if we found one
        if title:
            cmd.extend(["--title", title])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            display_title = title if title else pdf_file.stem
            print(f"✓ Converted: {pdf_file.name} → {epub_name}")
            print(f"  Title: {display_title}")
            return True
        else:
            print(f"✗ Failed to convert {pdf_file.name}: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Error converting {pdf_file.name}: {e}")
        return False

def main():
    # Find all PDF files
    pdf_files = []
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    
    if not pdf_files:
        print("No PDF files found in the current directory.")
        return
    
    print(f"Found {len(pdf_files)} PDF files:")
    for pdf in pdf_files:
        print(f"  - {pdf}")
    
    print("\nConverting to ePub format...")
    successful = 0
    
    for pdf in pdf_files:
        if convert_pdf_to_epub(pdf):
            successful += 1
    
    print(f"\nConversion complete: {successful}/{len(pdf_files)} files converted successfully")
    print("ePub files are saved in the 'epub_books' directory")

if __name__ == "__main__":
    main()
