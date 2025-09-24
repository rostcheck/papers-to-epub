#!/usr/bin/env python3
from pathlib import Path
from epub_fixer import EpubFixer
from epub_quality_analyzer import EpubQualityAnalyzer

def batch_fix_epubs():
    """Fix quality issues in all ePub files"""
    epub_dir = Path("epub_books")
    epub_files = list(epub_dir.glob("*.epub"))
    
    print(f"🔧 Batch fixing {len(epub_files)} ePub files...")
    
    for epub_file in epub_files:
        print(f"\n=== Processing: {epub_file.name} ===")
        
        # Analyze before fixing
        print("Before fixes:")
        analyzer = EpubQualityAnalyzer(epub_file)
        before_issues = analyzer.analyze()
        
        # Apply fixes
        fixer = EpubFixer(epub_file)
        fixer.fix_issues()
        
        # Analyze after fixing
        print("\nAfter fixes:")
        analyzer = EpubQualityAnalyzer(epub_file)
        after_issues = analyzer.analyze()
        
        # Show improvement
        improvement = len(before_issues) - len(after_issues)
        if improvement > 0:
            print(f"✅ Fixed {improvement} issues!")
        elif improvement == 0:
            print("⚠️ No improvement")
        else:
            print("❌ Issues increased (unexpected)")
    
    print(f"\n🎉 Batch fixing complete!")

if __name__ == "__main__":
    batch_fix_epubs()
