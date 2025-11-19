"""Simple linear workflow analysis example.

This script demonstrates how to use the temporalio-graphs library to analyze
a Temporal workflow and generate a visualization diagram.

Usage:
    python examples/simple_linear/run.py

Output:
    Prints a Mermaid flowchart diagram representing the workflow structure.

The diagram shows:
- Start node (s)
- All activities in sequence (1, 2, 3, ...)
- End node (e)
- Connections between activities

This example validates that:
1. The workflow file can be analyzed
2. All activities are detected
3. The correct Mermaid diagram is generated
"""

from pathlib import Path

from temporalio_graphs import analyze_workflow


def main() -> None:
    """Analyze the simple linear workflow and print the diagram.

    This function demonstrates the minimal usage of the analyze_workflow API:
    - Import the function from temporalio_graphs
    - Pass the workflow file path
    - Print the result
    """
    # Path to the example workflow
    workflow_file = Path(__file__).parent / "workflow.py"

    # Analyze the workflow using the public API
    # Returns a Mermaid diagram as a string
    diagram = analyze_workflow(workflow_file)

    # Print the diagram
    print(diagram)


if __name__ == "__main__":
    main()
