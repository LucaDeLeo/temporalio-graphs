#!/usr/bin/env python3
"""Fix DecisionPoint instantiations to include line_num parameter."""

import re
from pathlib import Path

def fix_positional_decision_points(content: str) -> str:
    """Fix DecisionPoint("id", "name", line_num, "yes", "no") pattern."""
    # Pattern: DecisionPoint("str", "str", number, "str", "str")
    pattern = r'DecisionPoint\("([^"]+)",\s*"([^"]+)",\s*(\d+),\s*"([^"]+)",\s*"([^"]+)"\)'
    replacement = r'DecisionPoint("\1", "\2", \3, \3, "\4", "\5")'
    return re.sub(pattern, replacement, content)

def fix_keyword_decision_points(content: str) -> str:
    """Fix keyword-style DecisionPoint instantiations."""
    # Pattern: line_number=NUMBER, (with or without trailing comma)
    # Replace with: line_number=NUMBER, line_num=NUMBER,
    pattern = r'line_number=(\d+),(\s*)(?!line_num)'
    replacement = r'line_number=\1, line_num=\1,\2'
    return re.sub(pattern, replacement, content)

def fix_file(file_path: Path):
    """Fix DecisionPoint instantiations in a file."""
    print(f"Fixing {file_path}")
    content = file_path.read_text()
    original_content = content

    # Apply fixes
    content = fix_positional_decision_points(content)
    content = fix_keyword_decision_points(content)

    # Only write if changed
    if content != original_content:
        file_path.write_text(content)
        print(f"  ✓ Updated {file_path}")
    else:
        print(f"  - No changes needed for {file_path}")

def main():
    """Fix all test files."""
    test_files = [
        "tests/test_detector.py",
        "tests/test_generator.py",
        "tests/test_renderer.py",
        "tests/integration/test_decision_rendering.py",
    ]

    for file_path in test_files:
        fix_file(Path(file_path))

if __name__ == "__main__":
    main()
