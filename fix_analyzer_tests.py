#!/usr/bin/env python3
"""Fix analyzer tests to work with Activity objects."""

import re
from pathlib import Path

def fix_activity_assertions(content: str) -> str:
    """Fix assertions that compare activities to strings."""
    # Pattern: assert metadata.activities[N] == "string"
    # Replace with: assert metadata.activities[N].name == "string"
    pattern = r'assert metadata\.activities\[(\d+)\] == "([^"]+)"'
    replacement = r'assert metadata.activities[\1].name == "\2"'
    content = re.sub(pattern, replacement, content)

    return content

def fix_activity_in_assertions(content: str) -> str:
    """Fix assertions that check if activity in list."""
    # Pattern: assert "activity" in metadata.activities
    # This is trickier - we need to check activity names
    # Replace with: assert any(a.name == "activity" for a in metadata.activities)
    pattern = r'assert "([^"]+)" in metadata\.activities'
    replacement = r'assert any(a.name == "\1" for a in metadata.activities)'
    content = re.sub(pattern, replacement, content)

    return content

def fix_file(file_path: Path):
    """Fix analyzer tests."""
    print(f"Fixing {file_path}")
    content = file_path.read_text()
    original_content = content

    # Apply fixes
    content = fix_activity_assertions(content)
    content = fix_activity_in_assertions(content)

    # Only write if changed
    if content != original_content:
        file_path.write_text(content)
        print(f"  ✓ Updated {file_path}")
    else:
        print(f"  - No changes needed for {file_path}")

def main():
    """Fix analyzer test file."""
    fix_file(Path("tests/test_analyzer.py"))

if __name__ == "__main__":
    main()
