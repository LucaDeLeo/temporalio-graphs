r"""Runner script demonstrating cross-workflow signal visualization.

This script shows how to use analyze_signal_graph() to visualize workflows that
are connected via signal sends and handlers (peer-to-peer signal flow).

The example demonstrates:
- Three-workflow signal chain: Order -> Shipping -> Notification
- Subgraph rendering for each workflow
- Signal handler hexagon nodes: {{signal_name}}
- Cross-subgraph dashed edges: -.signal_name.->
- Blue styling for signal handlers

Run this script from the project root:
    python examples/signal_flow/run.py
"""

from pathlib import Path

from temporalio_graphs import GraphBuildingContext, analyze_signal_graph


def main() -> None:
    """Demonstrate cross-workflow signal visualization."""
    # Get absolute paths to workflow files
    order_workflow_path = Path(__file__).parent / "order_workflow.py"
    search_paths = [Path(__file__).parent]

    print("=" * 80)
    print("Cross-Workflow Signal Flow Visualization Demo")
    print("=" * 80)
    print()

    print("SIGNAL CHAIN: Order -> Shipping -> Notification")
    print("-" * 80)
    print("This example shows three workflows connected by signals:")
    print("  1. OrderWorkflow sends 'ship_order' signal to ShippingWorkflow")
    print("  2. ShippingWorkflow handles 'ship_order' and sends 'notify_shipped'")
    print("  3. NotificationWorkflow handles 'notify_shipped'")
    print()

    # Create context for analysis
    context = GraphBuildingContext()

    # Analyze signal graph starting from OrderWorkflow
    result = analyze_signal_graph(
        order_workflow_path,
        search_paths=search_paths,
        context=context
    )

    print("GENERATED MERMAID DIAGRAM:")
    print("-" * 80)
    print(result)
    print()

    print("=" * 80)
    print("Visualization Features:")
    print("  - Each workflow is a subgraph: subgraph WorkflowName ... end")
    print("  - Signal handlers are hexagons: {{signal_name}}")
    print("  - Cross-workflow edges are dashed: -.signal_name.->")
    print("  - Signal handlers are styled blue: fill:#e6f3ff,stroke:#0066cc")
    print()
    print("See expected_output.md for the expected diagram structure.")
    print("=" * 80)


if __name__ == "__main__":
    main()
