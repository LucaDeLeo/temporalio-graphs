"""Demonstration script for signal workflow visualization.

This script analyzes the ApprovalWorkflow example and prints the generated
Mermaid diagram showing signal node visualization with hexagon syntax and
branch labels for Signaled vs Timeout paths.

Usage:
    uv run python examples/signal_workflow/run.py
"""

from pathlib import Path

from temporalio_graphs import analyze_workflow


def main() -> None:
    """Run analysis on signal workflow and display Mermaid output."""
    # Get path to workflow file in same directory
    workflow_file = Path(__file__).parent / "workflow.py"

    print("=" * 70)
    print("Signal Workflow Visualization Example")
    print("=" * 70)
    print()
    print(f"Analyzing: {workflow_file}")
    print()
    print("This example demonstrates:")
    print("- Signal node rendering with hexagon syntax {{NodeName}}")
    print("- Two execution paths: Signaled (approval) and Timeout (no approval)")
    print("- Conditional activities based on signal outcome")
    print()
    print("=" * 70)
    print()

    # Analyze workflow and generate Mermaid diagram
    output = analyze_workflow(workflow_file)

    # Display the output
    print(output)
    print()
    print("=" * 70)
    print()
    print("Copy the Mermaid code above to https://mermaid.live to visualize!")
    print()


if __name__ == "__main__":
    main()
