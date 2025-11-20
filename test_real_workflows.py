#!/usr/bin/env python3
"""
Test script for temporalio-graphs on real-world Temporal workflows
"""
import sys
from pathlib import Path
from typing import List, Tuple
import traceback

from temporalio_graphs import analyze_workflow, GraphBuildingContext

# Test workflows from real repositories
TEST_WORKFLOWS = [
    # Simple linear workflow
    {
        "name": "Hello Activity (Simple Linear)",
        "path": "/Users/luca/dev/bounty/repo-examples/samples-python/hello/hello_activity.py",
        "description": "Basic workflow with single activity",
        "expected_complexity": "Simple - 1 activity, no decisions"
    },
    # Medium complexity with loops
    {
        "name": "Polling Periodic (Loops + Error Handling)",
        "path": "/Users/luca/dev/bounty/repo-examples/samples-python/polling/periodic_sequence/workflows.py",
        "description": "Child workflow with retry loop and continue-as-new",
        "expected_complexity": "Medium - loops, error handling, child workflows"
    },
    # Complex with signals
    {
        "name": "AI Agent Workflow (Complex + Signals)",
        "path": "/Users/luca/dev/bounty/repo-examples/temporal-ai-agent/workflows/agent_goal_workflow.py",
        "description": "Complex AI agent workflow with signals and wait conditions",
        "expected_complexity": "Complex - multiple signals, wait conditions, state management"
    },
]

def print_separator(char="=", length=80):
    print(char * length)

def test_workflow(workflow_info: dict) -> Tuple[bool, str, str]:
    """Test a single workflow and return results"""
    name = workflow_info["name"]
    path = Path(workflow_info["path"])

    print_separator()
    print(f"Testing: {name}")
    print(f"File: {path}")
    print(f"Description: {workflow_info['description']}")
    print(f"Expected: {workflow_info['expected_complexity']}")
    print_separator("-")

    try:
        # Analyze the workflow with default context
        result = analyze_workflow(path)

        print("\n✓ Analysis successful!")
        print(f"\nGraph length: {len(result)} characters")

        # Show first 500 chars of the graph
        preview = result[:500]
        print(f"\nGraph preview (first 500 chars):\n{preview}")
        if len(result) > 500:
            print("...(truncated)")

        # Try with custom context
        print("\n\nTesting with custom context (verbose labels)...")
        custom_context = GraphBuildingContext(
            split_names_by_words=False,
            include_validation_report=True
        )
        result_custom = analyze_workflow(path, custom_context)
        print(f"✓ Custom context analysis successful! ({len(result_custom)} chars)")

        return True, result, None

    except Exception as e:
        print(f"\n✗ Analysis failed!")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print(f"\nFull traceback:")
        traceback.print_exc()
        return False, "", str(e)

def main():
    print("\n")
    print_separator("=")
    print("TEMPORALIO-GRAPHS REAL-WORLD TESTING")
    print_separator("=")
    print(f"\nTesting {len(TEST_WORKFLOWS)} workflows from real repositories\n")

    results = []

    for workflow_info in TEST_WORKFLOWS:
        success, output, error = test_workflow(workflow_info)
        results.append({
            "name": workflow_info["name"],
            "success": success,
            "output_length": len(output) if output else 0,
            "error": error
        })
        print("\n")

    # Summary
    print_separator("=")
    print("TEST SUMMARY")
    print_separator("=")

    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful

    print(f"\nTotal tests: {len(results)}")
    print(f"✓ Successful: {successful}")
    print(f"✗ Failed: {failed}")

    print("\nDetailed Results:")
    for i, result in enumerate(results, 1):
        status = "✓" if result["success"] else "✗"
        print(f"\n{i}. {status} {result['name']}")
        if result["success"]:
            print(f"   Output length: {result['output_length']} characters")
        else:
            print(f"   Error: {result['error']}")

    print_separator("=")

    # Return exit code
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
