from epub_quality_analyzer import EpubQualityAnalyzer
from bedrock_quality_analyzer import BedrockQualityAnalyzer

filename = "Evaluating Sakana's AI Scientist for Autonomous Research Wishful Thinking or an Emerging Reality Tow.epub"
filepath = f"epub_books/{filename}"

print(f"=== Quality Assessment: {filename} ===")

# Rule-based analysis
print("\n--- Rule-Based Quality Analysis ---")
analyzer = EpubQualityAnalyzer(filepath)
issues = analyzer.analyze()

# Bedrock AI analysis
print("\n--- AI-Powered Formatting Analysis ---")
bedrock_analyzer = BedrockQualityAnalyzer(filepath)
bedrock_result = bedrock_analyzer.analyze_with_bedrock()

if 'error' in bedrock_result:
    print(f"Bedrock analysis error: {bedrock_result['error']}")
else:
    print(f"Formatting Quality: {bedrock_result['quality_level']} ({bedrock_result['overall_score']}/10)")
    print(f"Severity: {bedrock_result['severity']}")
    print(f"Issue counts: {bedrock_result['issue_counts']}")
    if bedrock_result['formatting_issues']:
        print(f"Sample issues: {bedrock_result['formatting_issues'][:2]}")

print(f"\n=== Summary ===")
print(f"Rule-based issues: {len(issues)}")
print(f"AI analysis: {bedrock_result.get('quality_level', 'Error')}")
