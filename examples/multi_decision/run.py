"""Multi-decision workflow analysis example.

This script demonstrates how to use the temporalio-graphs library to analyze
a complex Temporal workflow with multiple decision points and generate a
comprehensive visualization diagram.

Usage:
    python examples/multi_decision/run.py

Output:
    Prints a Mermaid flowchart diagram showing all 8 possible execution paths
    through the LoanApprovalWorkflow.

The diagram shows:
- Start node (s)
- Sequential activities (validate_application, approve_loan)
- Decision nodes as diamonds (HighValue, LowCredit, ExistingLoans)
- Conditional activities (manager_review, require_collateral, debt_ratio_check)
- End node (e)
- All possible paths (2^3 = 8 paths)

This example validates that:
1. The workflow file can be analyzed successfully
2. All 3 decision points are detected
3. All 5 activities are present in the output
4. The correct number of paths (8) are generated
5. Decision nodes are rendered as diamonds with yes/no branches
"""

from pathlib import Path

from temporalio_graphs import GraphBuildingContext, analyze_workflow


def main() -> None:
    """Analyze the multi-decision workflow and print the complete diagram.

    This function demonstrates advanced usage of the analyze_workflow API:
    - Import both analyze_workflow and GraphBuildingContext
    - Configure context with custom settings
    - Pass the workflow file path and context
    - Print the result (Mermaid diagram + path list)
    - Save the result to expected_output.md for validation
    """
    # Path to the example workflow
    workflow_file = Path(__file__).parent / "workflow.py"

    # Create context with default settings (shows full output with paths)
    # You can customize the context for different output formats:
    # - split_names_by_words=True converts snake_case to "Title Case"
    # - output_format="full" includes both Mermaid diagram and path list
    context = GraphBuildingContext(
        split_names_by_words=True,  # Convert activity names to readable format
        output_format="full",  # Include both diagram and path list
    )

    try:
        # Analyze the workflow using the public API
        # Returns a complete formatted string with Mermaid diagram and paths
        result = analyze_workflow(workflow_file, context)

        # Print the complete result
        print(result)

        # Save to expected_output.md for validation and regression testing
        output_file = Path(__file__).parent / "expected_output.md"
        output_file.write_text(result)
        print(f"\nOutput saved to: {output_file}")

    except Exception as e:
        # Demonstrate error handling for library exceptions
        print(f"Error analyzing workflow: {e}")
        raise


if __name__ == "__main__":
    main()
