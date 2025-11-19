"""
Remove emojis from Python scripts for Windows compatibility.

This script scans all Python files in the project and replaces emojis
with text-based alternatives that display correctly in Windows PowerShell.

UPDATED: Now properly handles BOM (Byte Order Mark) characters without breaking syntax.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple

# Emoji mapping to text alternatives
EMOJI_REPLACEMENTS: Dict[str, str] = {
    '✓': '[OK]',
    '✗': '[X]',
    '⚠️': '[WARNING]',
    '⚠': '[WARNING]',
    '❌': '[ERROR]',
    '🎯': '[TARGET]',
    '📊': '[CHART]',
    '💰': '[MONEY]',
    '📈': '[UP]',
    '📉': '[DOWN]',
    '🔍': '[SEARCH]',
    '⏰': '[TIME]',
    '🏈': '[NFL]',
    '⚡': '[FAST]',
    '🎰': '[BET]',
    '📋': '[LIST]',
    '💡': '[INFO]',
    '🚀': '[LAUNCH]',
    '⭐': '[STAR]',
    '🔥': '[HOT]',
    '❗': '[!]',
    '❓': '[?]',
    '💵': '[$]',
    '📝': '[NOTE]',
    '🎲': '[DICE]',
    '🏆': '[WIN]',
    '⬆️': '[UP]',
    '⬇️': '[DOWN]',
    '➡️': '[->]',
    '⬅️': '[<-]',
    '🔴': '[RED]',
    '🟢': '[GREEN]',
    '🟡': '[YELLOW]',
}

def remove_emojis_from_file(filepath: Path) -> Tuple[bool, List[str]]:
    """
    Remove emojis from a Python file and replace with text alternatives.
    
    Args:
        filepath: Path to the Python file
        
    Returns:
        Tuple of (was_modified, list_of_changes)
    """
    try:
        # Read with UTF-8 encoding and strip BOM if present
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        
        original_content = content
        changes = []
        
        # Replace known emojis
        for emoji, replacement in EMOJI_REPLACEMENTS.items():
            if emoji in content:
                count = content.count(emoji)
                content = content.replace(emoji, replacement)
                changes.append(f"Replaced {count}x '{emoji}' with '{replacement}'")
        
        # Remove any remaining emojis (Unicode ranges)
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"  # dingbats
            "\U000024C2-\U0001F251"
            "\U0001F900-\U0001F9FF"  # supplemental symbols
            "\U00002600-\U000026FF"  # miscellaneous symbols
            "]+",
            flags=re.UNICODE
        )
        
        remaining_emojis = emoji_pattern.findall(content)
        if remaining_emojis:
            content = emoji_pattern.sub('', content)  # Remove completely instead of [*]
            unique_emojis = set(remaining_emojis)
            changes.append(f"Removed {len(remaining_emojis)} other emojis ({len(unique_emojis)} unique)")
            if len(unique_emojis) <= 5:  # Show which ones if not too many
                changes.append(f"  Removed: {', '.join(repr(e) for e in unique_emojis)}")
        
        # Write back if modified (UTF-8 without BOM)
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
                f.write(content)
            return True, changes
        
        return False, []
        
    except Exception as e:
        print(f"[ERROR] Failed to process {filepath}: {e}")
        return False, []

def process_project(project_root: Path, dry_run: bool = False) -> None:
    """
    Process all Python files in the project.
    
    Args:
        project_root: Root directory of the project
        dry_run: If True, only report what would be changed without modifying files
    """
    # Find all Python files
    python_files = []
    for pattern in ['*.py']:
        python_files.extend(project_root.rglob(pattern))
    
    # Filter out unwanted directories
    skip_dirs = {'.venv', 'venv', '__pycache__', 'build', 'dist', '.git', 
                 'node_modules', '.pytest_cache', '.ruff_cache', '.uv-cache',
                 'archive', 'vendor'}
    
    python_files = [
        f for f in python_files 
        if not any(skip_dir in f.parts for skip_dir in skip_dirs)
    ]
    
    print(f"\n{'='*70}")
    print(f"  Emoji Removal Tool - Windows Compatibility (Fixed)")
    print(f"{'='*70}")
    print(f"\nMode: {'DRY RUN (no changes will be made)' if dry_run else 'ACTIVE (files will be modified)'}")
    print(f"Found {len(python_files)} Python files to check\n")
    
    modified_count = 0
    total_changes = 0
    
    for filepath in sorted(python_files):
        if dry_run:
            # In dry run, just check without modifying
            try:
                with open(filepath, 'r', encoding='utf-8-sig') as f:
                    content = f.read()
                
                has_emojis = any(emoji in content for emoji in EMOJI_REPLACEMENTS.keys())
                
                # Check for other emojis
                emoji_pattern = re.compile(
                    "["
                    "\U0001F600-\U0001F64F"
                    "\U0001F300-\U0001F5FF"
                    "\U0001F680-\U0001F6FF"
                    "\U0001F1E0-\U0001F1FF"
                    "\U00002702-\U000027B0"
                    "\U000024C2-\U0001F251"
                    "\U0001F900-\U0001F9FF"
                    "\U00002600-\U000026FF"
                    "]+",
                    flags=re.UNICODE
                )
                has_other_emojis = bool(emoji_pattern.search(content))
                
                if has_emojis or has_other_emojis:
                    print(f"\n[WOULD MODIFY] {filepath.relative_to(project_root)}")
                    for emoji, replacement in EMOJI_REPLACEMENTS.items():
                        count = content.count(emoji)
                        if count > 0:
                            print(f"  - Would replace {count}x '{emoji}' with '{replacement}'")
                    if has_other_emojis:
                        print(f"  - Would remove other Unicode emojis")
                    modified_count += 1
            except Exception as e:
                print(f"[ERROR] {filepath.relative_to(project_root)}: {e}")
        else:
            # Actually modify files
            was_modified, changes = remove_emojis_from_file(filepath)
            
            if was_modified:
                modified_count += 1
                total_changes += len(changes)
                print(f"\n[MODIFIED] {filepath.relative_to(project_root)}")
                for change in changes:
                    print(f"  - {change}")
    
    print(f"\n{'='*70}")
    if dry_run:
        print(f"[DRY RUN COMPLETE] Would modify {modified_count} files")
        print(f"\nTo actually make changes, run without --dry-run flag:")
        print(f"  python scripts/remove_emojis.py")
    else:
        print(f"[COMPLETE] Modified {modified_count} files ({total_changes} changes)")
        
        if modified_count > 0:
            print(f"\nNext steps:")
            print(f"1. Review changes: git diff")
            print(f"2. Test scripts: python check_status.py")
            print(f"3. Run a script to verify: python analyze_week12.py")
    print(f"{'='*70}\n")

if __name__ == '__main__':
    import sys
    
    project_root = Path(__file__).parent.parent
    
    # Check for dry-run flag
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv
    
    print(f"\nProject root: {project_root}")
    
    if dry_run:
        print("\n[INFO] Running in DRY RUN mode - no files will be modified")
        response = 'y'
    else:
        print("\n[WARNING] This will modify Python files in your project!")
        response = input("Continue? (y/n): ").lower().strip()
    
    if response == 'y':
        process_project(project_root, dry_run=dry_run)
    else:
        print("\nAborted.")
