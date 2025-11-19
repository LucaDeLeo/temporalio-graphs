"""Runner script demonstrating all three expansion modes for parent-child workflows.

This script shows how to use analyze_workflow_graph() with different expansion modes:
- Reference mode (default): Child workflow as [[PaymentWorkflow]] node
- Inline mode: Complete end-to-end paths (4 paths = 2 parent × 2 child)
- Subgraph mode: Separate subgraph blocks for parent and child workflows

Run this script from the project root:
    python examples/parent_child_workflow/run.py
"""

from pathlib import Path

from temporalio_graphs import GraphBuildingContext, analyze_workflow_graph


def main() -> None:
    """Demonstrate all three expansion modes for parent-child workflow visualization."""
    # Get absolute path to parent workflow file
    parent_workflow_path = Path(__file__).parent / "parent_workflow.py"

    print("=" * 80)
    print("Parent-Child Workflow Visualization Demo")
    print("=" * 80)
    print()

    # Mode 1: Reference mode (default) - child as atomic node
    print("1. REFERENCE MODE (default)")
    print("-" * 80)
    print("Child workflow appears as [[PaymentWorkflow]] node")
    print("Generates 2 paths (parent decisions only)")
    print()

    context_reference = GraphBuildingContext(
        child_workflow_expansion="reference"
    )
    result_reference = analyze_workflow_graph(
        parent_workflow_path,
        context=context_reference
    )
    print(result_reference)
    print()

    # Mode 2: Inline mode - complete end-to-end paths
    print("2. INLINE MODE")
    print("-" * 80)
    print("Complete end-to-end paths spanning parent and child workflows")
    print("Generates 4 paths (2 parent × 2 child = 2² × 2¹ = 4)")
    print()

    context_inline = GraphBuildingContext(
        child_workflow_expansion="inline"
    )
    result_inline = analyze_workflow_graph(
        parent_workflow_path,
        context=context_inline
    )
    print(result_inline)
    print()

    # Mode 3: Subgraph mode - structural visualization
    print("3. SUBGRAPH MODE")
    print("-" * 80)
    print("Separate subgraph blocks showing workflow boundaries")
    print("Generates 2 paths per workflow (same as reference for path count)")
    print()

    context_subgraph = GraphBuildingContext(
        child_workflow_expansion="subgraph"
    )
    result_subgraph = analyze_workflow_graph(
        parent_workflow_path,
        context=context_subgraph
    )
    print(result_subgraph)
    print()

    print("=" * 80)
    print("Mode Selection Guide:")
    print("  - Reference: Best for overview, no path explosion risk")
    print("  - Inline: Best for understanding complete execution flow")
    print("  - Subgraph: Best for structural visualization with clear boundaries")
    print("=" * 80)


if __name__ == "__main__":
    main()
