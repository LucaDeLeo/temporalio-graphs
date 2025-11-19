#!/usr/bin/env python3
"""Fix Activity lists in tests to use Activity objects."""

import re
from pathlib import Path

def fix_activity_lists(content: str) -> str:
    """Convert activities=["name1", "name2"] to activities=[Activity("name1", 1), Activity("name2", 2)]."""

    def replace_activity_list(match):
        """Replace a single activities=[...] list."""
        full_match = match.group(0)
        activities_str = match.group(1)

        # Empty list
        if not activities_str.strip():
            return full_match

        # Extract activity names from the list
        # Handle both single-line and multi-line lists
        activity_names = re.findall(r'"([^"]+)"', activities_str)

        if not activity_names:
            return full_match

        # Generate Activity objects with incrementing line numbers
        activity_objects = []
        for i, name in enumerate(activity_names, start=1):
            activity_objects.append(f'Activity("{name}", {i*10})')

        # Format the result
        if len(activity_objects) == 1:
            return f"activities=[{activity_objects[0]}]"
        else:
            # Multi-line format for readability
            activities_formatted = ", ".join(activity_objects)
            return f"activities=[{activities_formatted}]"

    # Match activities=[...] including multi-line lists
    # This pattern captures the content between square brackets
    pattern = r'activities=\[((?:[^][]|\[[^]]*\])*)\]'
    content = re.sub(pattern, replace_activity_list, content, flags=re.MULTILINE | re.DOTALL)

    return content

def add_activity_import(content: str) -> str:
    """Add Activity import if not present."""
    # Check if Activity is already imported
    if 'from temporalio_graphs._internal.graph_models import' in content:
        # Check if Activity is in the import
        import_pattern = r'from temporalio_graphs\._internal\.graph_models import ([^\n]+)'
        match = re.search(import_pattern, content)
        if match:
            imports = match.group(1)
            if 'Activity' not in imports:
                # Add Activity to existing import
                new_imports = imports.rstrip() + ', Activity'
                content = re.sub(import_pattern, f'from temporalio_graphs._internal.graph_models import {new_imports}', content)
    else:
        # Add new import after other graph_models imports if they exist
        if 'from temporalio_graphs._internal.graph_models import' not in content:
            # Add import after other temporalio_graphs imports
            pattern = r'(from temporalio_graphs[^\n]+\n)'
            if re.search(pattern, content):
                content = re.sub(pattern, r'\1from temporalio_graphs._internal.graph_models import Activity\n', content, count=1)

    return content

def fix_file(file_path: Path):
    """Fix Activity lists in a test file."""
    print(f"Fixing {file_path}")
    content = file_path.read_text()
    original_content = content

    # Add Activity import
    content = add_activity_import(content)

    # Fix activity lists
    content = fix_activity_lists(content)

    # Only write if changed
    if content != original_content:
        file_path.write_text(content)
        print(f"  ✓ Updated {file_path}")
    else:
        print(f"  - No changes needed for {file_path}")

def main():
    """Fix all test files."""
    test_files = [
        "tests/test_generator.py",
        "tests/test_renderer.py",
        "tests/integration/test_decision_rendering.py",
    ]

    for file_path in test_files:
        fix_file(Path(file_path))

if __name__ == "__main__":
    main()
