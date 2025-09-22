#!/usr/bin/env python3
import json
import subprocess

def test_bedrock_formatting_detection():
    """Test Bedrock's ability to detect specific formatting issues"""
    
    # Test cases with known formatting problems
    test_cases = {
        "good_text": """
        The AI Scientist represents a significant advancement in automated research. 
        This paper describes our methodology and results. We conducted experiments 
        across multiple domains to validate our approach.
        """,
        
        "missing_text_end": """
        The AI Scientist represents a significant advancement in automated research.
        This paper describes our methodology and results. We conducted experiments
        across multiple domains to validate our
        """,
        
        "footer_in_text": """
        The AI Scientist represents a significant advancement in automated research.
        https://sakana.ai/ai-scientist-first-publication/
        This paper describes our methodology and results. We conducted experiments
        across multiple domains to validate our approach.
        """,
        
        "broken_citation": """
        The AI Scientist represents a significant advancement in automated research [1.
        This paper describes our methodology and results (Smith et al.. We conducted 
        experiments across multiple domains to validate our approach.
        """,
        
        "fragmented_words": """
        The AI Scien tist repres ents a signif icant advanc ement in autom ated research.
        This pa per descr ibes our method ology and res ults. We conduc ted experim ents
        across mult iple dom ains to valid ate our appr oach.
        """
    }
    
    print("Testing Bedrock formatting detection...")
    
    for test_name, text in test_cases.items():
        print(f"\n=== Testing: {test_name} ===")
        result = analyze_text_with_bedrock(text.strip(), test_name)
        
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Scores: {result}")
            if "formatting_issues" in result:
                print(f"Issues: {result['formatting_issues']}")

def analyze_text_with_bedrock(text, test_name):
    """Analyze text with improved Bedrock prompt"""
    
    prompt = f"""You are analyzing text from a PDF-to-ePub conversion to detect FORMATTING DEFECTS.

EXAMPLES of formatting issues to detect:
- Missing text: "We conducted experiments to validate our" (sentence cuts off)
- Footer intrusion: "The results show https://example.com/paper significant improvement" (URL inserted mid-paragraph)
- Broken citations: "As shown by Smith et al. the method works" (missing closing bracket)
- Word fragmentation: "The res ults show signif icant improve ment" (words split incorrectly)
- Repeated headers: "Introduction Introduction The main topic is..." (duplicate titles)

IGNORE content quality - only flag technical formatting defects.

Text to analyze:
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
            /tmp/bedrock_test_response.json'
        """
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            with open('/tmp/bedrock_test_response.json', 'r') as f:
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

if __name__ == "__main__":
    test_bedrock_formatting_detection()
