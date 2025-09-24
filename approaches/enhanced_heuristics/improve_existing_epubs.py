#!/usr/bin/env python3
from pathlib import Path
from epub_quality_analyzer import EpubQualityAnalyzer
from improved_convert_to_epub import post_process_epub, apply_targeted_fixes
import shutil

def improve_existing_epubs():
    """Improve quality of existing ePub files"""
    epub_dir = Path("epub_books")
    backup_dir = Path("epub_books_original")
    
    if not epub_dir.exists():
        print("No epub_books directory found")
        return
    
    # Create backup if it doesn't exist
    if not backup_dir.exists():
        print("Creating backup of original ePub files...")
        shutil.copytree(epub_dir, backup_dir)
    
    epub_files = list(epub_dir.glob("*.epub"))
    if not epub_files:
        print("No ePub files found")
        return
    
    print(f"Improving {len(epub_files)} existing ePub files...")
    
    for epub_file in epub_files:
        print(f"\n=== Improving: {epub_file.name} ===")
        
        # Initial quality check
        analyzer = EpubQualityAnalyzer(epub_file)
        initial_issues = analyzer.analyze()
        
        if not initial_issues:
            print("✓ No issues found, skipping")
            continue
        
        # Apply post-processing
        print("Applying improvements...")
        if post_process_epub(epub_file):
            # Check quality again
            print("\n--- After Improvement ---")
            analyzer = EpubQualityAnalyzer(epub_file)
            final_issues = analyzer.analyze()
            
            if len(final_issues) < len(initial_issues):
                print(f"✓ Improved: {len(initial_issues)} → {len(final_issues)} issues")
            elif not final_issues:
                print("✓ All issues resolved!")
            else:
                print("⚠ Some issues remain, applying targeted fixes...")
                apply_targeted_fixes(epub_file, final_issues)
        else:
            print("✗ Post-processing failed")

if __name__ == "__main__":
    improve_existing_epubs()
