"""
Script to analyze and visualize the OrderWorkflow using temporalio-graphs.
"""

from pathlib import Path
from temporalio_graphs import analyze_workflow, GraphBuildingContext


def main():
    """Analyze the order workflow and generate visualizations."""
    workflow_file = Path("order_workflow.py")

    print("=" * 80)
    print("TEMPORALIO-GRAPHS TEST - Order Processing Workflow")
    print("=" * 80)
    print()

    # Test 1: Basic analysis with default settings (Mermaid)
    print("Test 1: Basic Analysis (Mermaid Diagram)")
    print("-" * 80)
    result = analyze_workflow(str(workflow_file), output_format="mermaid")
    print(result)
    print()

    # Test 2: Path list format
    print("\n" + "=" * 80)
    print("Test 2: Execution Paths Format")
    print("-" * 80)
    result_paths = analyze_workflow(str(workflow_file), output_format="paths")
    print(result_paths)
    print()

    # Test 3: Custom configuration
    print("\n" + "=" * 80)
    print("Test 3: Custom Configuration (No Word Splitting)")
    print("-" * 80)
    custom_context = GraphBuildingContext(
        split_names_by_words=False,
        start_node_label="Order Start",
        end_node_label="Order Complete",
        decision_true_label="✓",
        decision_false_label="✗",
        signal_success_label="Paid",
        signal_timeout_label="Expired",
    )
    result_custom = analyze_workflow(
        str(workflow_file),
        context=custom_context,
        output_format="mermaid"
    )
    print(result_custom)
    print()

    # Test 4: Save to file
    print("\n" + "=" * 80)
    print("Test 4: Save to File")
    print("-" * 80)
    output_file = Path("workflow_diagram.md")
    file_context = GraphBuildingContext(
        graph_output_file=output_file
    )
    result_file = analyze_workflow(
        str(workflow_file),
        context=file_context,
        output_format="mermaid"
    )
    print(f"✓ Diagram saved to: {output_file}")
    print(f"✓ File size: {output_file.stat().st_size} bytes")
    print()

    print("=" * 80)
    print("All tests completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
