#!/usr/bin/env python3
"""
Simple comparison tool for rules-based vs cognitive converters
"""

import subprocess
import json
import sys
from pathlib import Path

def run_qa_assessment(latex_file, xml_file):
    """Run quality assessment and return parsed results"""
    try:
        result = subprocess.run([
            'python3', 'structural_review/review_structure.py', 
            latex_file, xml_file, '--json'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('{') and 'overall_score' in line:
                    return json.loads(line)
    except Exception as e:
        print(f"Error assessing {xml_file}: {e}")
    
    return None

def compare_converters(latex_file):
    """Compare both converter outputs"""
    latex_path = Path(latex_file)
    rules_xml = f"output/{latex_path.stem}_rules_based.xml"
    cognitive_xml = f"output/{latex_path.stem}_cognitive_iter2.xml"  # Use best iteration
    
    print("🔍 CONVERTER COMPARISON")
    print("=" * 50)
    
    # Check files exist
    if not Path(rules_xml).exists():
        print(f"❌ Rules-based output not found: {rules_xml}")
        return
    if not Path(cognitive_xml).exists():
        print(f"❌ Cognitive output not found: {cognitive_xml}")
        return
    
    # Run assessments
    rules_data = run_qa_assessment(latex_file, rules_xml)
    cognitive_data = run_qa_assessment(latex_file, cognitive_xml)
    
    if not rules_data or not cognitive_data:
        print("❌ Failed to assess one or both converters")
        return
    
    # Compare results
    print(f"📊 QUALITY SCORES")
    print(f"Rules-Based:  {rules_data['overall_score']:.1f}%")
    print(f"Cognitive:    {cognitive_data['overall_score']:.1f}%")
    print()
    
    print(f"📁 FILE SIZES")
    rules_size = Path(rules_xml).stat().st_size
    cognitive_size = Path(cognitive_xml).stat().st_size
    print(f"Rules-Based:  {rules_size:,} bytes")
    print(f"Cognitive:    {cognitive_size:,} bytes")
    print()
    
    print(f"📋 DETAILED COMPARISON")
    print(f"{'Component':<15} {'Rules-Based':<12} {'Cognitive':<12} {'Winner'}")
    print("-" * 50)
    
    # Extract analysis data
    r_analysis = rules_data['analysis']
    c_analysis = cognitive_data['analysis']
    
    # Compare components
    comparisons = [
        ("Title", "✅" if r_analysis['metadata']['title']['xml'] else "❌", 
                 "✅" if c_analysis['metadata']['title']['xml'] else "❌"),
        ("Authors", f"{r_analysis['metadata']['authors']['xml']}/3", 
                  f"{c_analysis['metadata']['authors']['xml']}/3"),
        ("Abstract", "✅" if r_analysis['metadata']['abstract']['xml_chars'] > 0 else "❌",
                   "✅" if c_analysis['metadata']['abstract']['xml_chars'] > 0 else "❌"),
        ("Sections", f"{r_analysis['structure']['sections']['xml']}/8",
                   f"{c_analysis['structure']['sections']['xml']}/8"),
        ("Equations", f"{r_analysis['mathematics']['equations']['xml']}/5",
                    f"{c_analysis['mathematics']['equations']['xml']}/5"),
        ("Citations", f"{r_analysis['references']['citations']['xml']}/51",
                    f"{c_analysis['references']['citations']['xml']}/51"),
        ("Bibliography", f"{r_analysis['references']['bibliography']['xml']}/32",
                       f"{c_analysis['references']['bibliography']['xml']}/32"),
        ("Tables", f"{r_analysis['tables_figures']['tables']['xml']}/8",
                 f"{c_analysis['tables_figures']['tables']['xml']}/8"),
        ("Figures", f"{r_analysis['tables_figures']['figures']['xml']}/1",
                  f"{c_analysis['tables_figures']['figures']['xml']}/1"),
    ]
    
    for comp, rules_val, cognitive_val in comparisons:
        winner = "Tie"
        if rules_val != cognitive_val:
            # Simple heuristic for winner
            if "✅" in rules_val and "❌" in cognitive_val:
                winner = "Rules"
            elif "❌" in rules_val and "✅" in cognitive_val:
                winner = "Cognitive"
            elif "/" in rules_val and "/" in cognitive_val:
                r_num = int(rules_val.split('/')[0])
                c_num = int(cognitive_val.split('/')[0])
                if r_num > c_num:
                    winner = "Rules"
                elif c_num > r_num:
                    winner = "Cognitive"
        
        print(f"{comp:<15} {rules_val:<12} {cognitive_val:<12} {winner}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 compare_converters.py <latex_file>")
        sys.exit(1)
    
    compare_converters(sys.argv[1])
