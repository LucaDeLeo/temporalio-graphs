r"""Runner script demonstrating peer-to-peer workflow signal visualization.

This script shows how to use analyze_workflow() to visualize workflows that
send external signals to other workflows (peer-to-peer pattern).

The example demonstrates:
- Order workflow sending external signal to Shipping workflow
- Trapezoid node rendering for external signals: [/Signal 'name' to target\]
- Dashed edge style for async signal flow: -.signal.->
- Orange/amber color styling distinguishing signals from activities

Run this script from the project root:
    python examples/peer_signal_workflow/run.py
"""

from pathlib import Path

from temporalio_graphs import GraphBuildingContext, analyze_workflow


def main() -> None:
    """Demonstrate peer-to-peer workflow signal visualization."""
    # Get absolute paths to workflow files
    order_workflow_path = Path(__file__).parent / "order_workflow.py"
    shipping_workflow_path = Path(__file__).parent / "shipping_workflow.py"

    print("=" * 80)
    print("Peer-to-Peer Workflow Signal Visualization Demo")
    print("=" * 80)
    print()

    # Analyze Order workflow (sender)
    print("ORDER WORKFLOW (Signal Sender)")
    print("-" * 80)
    print("This workflow sends external signal 'ship_order' to Shipping workflow")
    print()

    # Use target-pattern mode to show the target workflow pattern in the label
    context = GraphBuildingContext(
        external_signal_label_style="target-pattern"
    )

    order_result = analyze_workflow(
        order_workflow_path,
        context=context
    )
    print(order_result)
    print()

    # Analyze Shipping workflow (receiver)
    print("SHIPPING WORKFLOW (Signal Receiver)")
    print("-" * 80)
    print("This workflow receives 'ship_order' signal via @workflow.signal handler")
    print()

    shipping_result = analyze_workflow(
        shipping_workflow_path,
        context=context
    )
    print(shipping_result)
    print()

    print("=" * 80)
    print("Signal Pattern Visualization:")
    print("  - Trapezoid nodes: [/Signal 'name' to target\\]")
    print("  - Dashed edges: -.signal.-> (async communication)")
    print("  - Orange/amber color: Distinguishes signals from activities")
    print()
    print("Three Signal Types:")
    print("  1. Internal Signals: wait_condition() - workflow waits for own state")
    print("  2. Parent-Child: execute_child_workflow() - synchronous spawning")
    print("  3. Peer-to-Peer: get_external_workflow_handle().signal() - async")
    print("=" * 80)


if __name__ == "__main__":
    main()
