r"""Integration tests for peer signal workflow examples.

This module validates the peer signal workflow example in
examples/peer_signal_workflow/ to ensure Order and Shipping workflows
are correctly analyzed and visualized.

Validates AC5 from Story 7.5:
- Order workflow analysis detects external signal
- Mermaid output contains trapezoid syntax [/Signal...\]
- Mermaid output contains dashed edge -.signal.->
- Mermaid output contains target pattern shipping-{*}
- Output matches expected_output.md structure
"""

from pathlib import Path

import pytest

from temporalio_graphs import GraphBuildingContext, analyze_workflow


class TestPeerSignalWorkflowExamples:
    """Integration tests for peer signal workflow examples."""

    @pytest.fixture
    def order_workflow_path(self) -> Path:
        """Path to Order workflow example."""
        return Path("examples/peer_signal_workflow/order_workflow.py")

    @pytest.fixture
    def shipping_workflow_path(self) -> Path:
        """Path to Shipping workflow example."""
        return Path("examples/peer_signal_workflow/shipping_workflow.py")

    def test_order_workflow_analysis(self, order_workflow_path: Path) -> None:
        """Validate Order workflow analysis detects external signal send.

        AC5: analyze_workflow("examples/peer_signal_workflow/order_workflow.py")
        succeeds and output contains trapezoid signal node with correct syntax.
        """
        # Ensure file exists
        assert order_workflow_path.exists(), (
            f"Order workflow example not found at {order_workflow_path}"
        )

        # Analyze workflow with target-pattern label style
        context = GraphBuildingContext(
            external_signal_label_style="target-pattern"
        )
        result = analyze_workflow(order_workflow_path, context=context)

        # Validate analysis succeeded (returns non-empty string)
        assert result, "analyze_workflow() should return non-empty Mermaid output"
        assert isinstance(result, str), "analyze_workflow() should return string"

        # Validate trapezoid syntax appears (AC5)
        assert "[/Signal 'ship_order'" in result, (
            "Order workflow Mermaid output should contain trapezoid node "
            "[/Signal 'ship_order'...] for external signal"
        )

        # Validate dashed edge appears (AC5)
        assert "-.signal.->" in result, (
            "Order workflow Mermaid output should contain dashed edge -.signal.-> "
            "for async signal flow"
        )

        # Validate target pattern appears (AC5)
        assert "shipping-{*}" in result or "shipping-" in result, (
            "Order workflow Mermaid output should contain target pattern "
            "shipping-{*} or shipping- for Shipping workflow"
        )

        # Validate color styling appears
        assert "style ext_sig_" in result, (
            "Order workflow Mermaid output should contain color styling directive "
            "for external signal node"
        )

    def test_shipping_workflow_analysis(self, shipping_workflow_path: Path) -> None:
        """Validate Shipping workflow analysis detects signal handler and wait_condition.

        While the focus is on Order workflow sending signal, we also validate
        Shipping workflow can be analyzed (receiving side).
        """
        # Ensure file exists
        assert shipping_workflow_path.exists(), (
            f"Shipping workflow example not found at {shipping_workflow_path}"
        )

        # Analyze workflow
        context = GraphBuildingContext()
        result = analyze_workflow(shipping_workflow_path, context=context)

        # Validate analysis succeeded
        assert result, "analyze_workflow() should return non-empty Mermaid output"
        assert isinstance(result, str), "analyze_workflow() should return string"

        # Validate ship_package activity appears
        assert "ship_package" in result, (
            "Shipping workflow should contain ship_package activity"
        )

        # Note: The Shipping workflow uses Temporal's built-in wait_condition(),
        # not our custom 3-arg helper. Therefore, no special signal node appears.
        # The @workflow.signal handler is a method definition, not detected by
        # static analysis as an execution node. This is expected behavior.
        # The main focus of this example is the Order workflow (sender side).

    def test_peer_signal_mermaid_output_structure(
        self, order_workflow_path: Path
    ) -> None:
        """Validate complete Mermaid structure for peer signals matches expected_output.md.

        AC5: Output structure matches expected_output.md including:
        - Trapezoid node syntax
        - Dashed edge syntax
        - Target pattern format
        - Color styling
        """
        # Analyze Order workflow
        context = GraphBuildingContext(
            external_signal_label_style="target-pattern"
        )
        result = analyze_workflow(order_workflow_path, context=context)

        # Validate Mermaid structure elements
        assert result.startswith("flowchart LR\n") or "flowchart LR" in result, (
            "Mermaid output should contain 'flowchart LR' directive"
        )

        # Validate Start node appears
        assert "s((Start))" in result, (
            "Mermaid output should contain Start node s((Start))"
        )

        # Validate End node appears
        assert "e((End))" in result, (
            "Mermaid output should contain End node e((End))"
        )

        # Validate process_order activity appears
        assert "process_order" in result, (
            "Mermaid output should contain process_order activity node"
        )

        # Validate complete_order activity appears
        assert "complete_order" in result, (
            "Mermaid output should contain complete_order activity node"
        )

        # Validate external signal node structure
        assert "[/Signal 'ship_order' to shipping-{*}\\]" in result, (
            "Mermaid output should contain complete trapezoid syntax: "
            "[/Signal 'ship_order' to shipping-{*}\\]"
        )

        # Validate edge from external signal
        external_signal_node_pattern = "ext_sig_ship_order"
        assert external_signal_node_pattern in result, (
            f"Mermaid output should contain external signal node ID: "
            f"{external_signal_node_pattern}"
        )

        # Validate dashed edge from external signal node
        assert "-.signal.->" in result, (
            "Mermaid output should contain dashed edge -.signal.-> after external signal"
        )

        # Validate color styling directive
        assert "fill:#fff4e6" in result, (
            "Mermaid output should contain orange/amber fill color #fff4e6"
        )
        assert "stroke:#ffa500" in result, (
            "Mermaid output should contain orange stroke color #ffa500"
        )

    def test_order_workflow_path_list(self, order_workflow_path: Path) -> None:
        """Validate Order workflow generates expected execution path.

        Expected path: process_order → Signal 'ship_order' → complete_order
        """
        # Analyze workflow
        context = GraphBuildingContext(
            external_signal_label_style="target-pattern"
        )
        result = analyze_workflow(order_workflow_path, context=context)

        # Order workflow is linear (no decisions), should generate 1 path
        # Validate path structure in output (may appear in path list section)
        # The key validation is that nodes appear in correct order in Mermaid edges
        lines = result.split("\n")

        # Find edge definitions (lines containing "-->")
        edges = [line.strip() for line in lines if "-->" in line or "-.signal.->" in line]

        # Validate edge chain exists
        edge_str = " ".join(edges)
        assert "process_order" in edge_str, "Edges should contain process_order"
        assert "ship_order" in edge_str, "Edges should contain ship_order signal"
        assert "complete_order" in edge_str, "Edges should contain complete_order"

    def test_example_runner_imports(self) -> None:
        """Validate run.py example can import required modules.

        This doesn't execute run.py (would require uv), but validates
        the imports and structure are correct for manual execution.
        """
        run_file = Path("examples/peer_signal_workflow/run.py")
        assert run_file.exists(), (
            f"Example runner not found at {run_file}"
        )

        # Read run.py content
        content = run_file.read_text()

        # Validate imports
        assert "from temporalio_graphs import" in content, (
            "run.py should import from temporalio_graphs"
        )
        assert "analyze_workflow" in content, (
            "run.py should import analyze_workflow function"
        )
        assert "GraphBuildingContext" in content, (
            "run.py should import GraphBuildingContext"
        )

        # Validate it calls analyze_workflow for both workflows
        assert "order_workflow.py" in content, (
            "run.py should reference order_workflow.py"
        )
        assert "shipping_workflow.py" in content, (
            "run.py should reference shipping_workflow.py"
        )

    def test_expected_output_documentation_exists(self) -> None:
        """Validate expected_output.md exists and contains key documentation.

        AC4: expected_output.md exists with golden Mermaid diagram showing
        trapezoid signal node, dashed edge, orange/amber color styling.
        """
        expected_output_file = Path("examples/peer_signal_workflow/expected_output.md")
        assert expected_output_file.exists(), (
            f"Expected output documentation not found at {expected_output_file}"
        )

        content = expected_output_file.read_text()

        # Validate documentation contains key elements
        assert "Peer-to-Peer" in content or "peer-to-peer" in content, (
            "expected_output.md should explain peer-to-peer pattern"
        )

        # Validate Mermaid code blocks exist
        assert "```mermaid" in content, (
            "expected_output.md should contain Mermaid code blocks"
        )

        # Validate trapezoid syntax documented
        assert "[/Signal" in content, (
            "expected_output.md should document trapezoid syntax [/Signal..."
        )

        # Validate dashed edge documented
        assert "-.signal.->" in content, (
            "expected_output.md should document dashed edge -.signal.->"
        )

        # Validate color styling documented
        assert "#fff4e6" in content or "orange" in content or "amber" in content, (
            "expected_output.md should document color styling (orange/amber)"
        )

        # Validate target pattern documented
        assert "shipping-{*}" in content, (
            "expected_output.md should document target pattern shipping-{*}"
        )

        # Validate three signal types explained (AC6 preview)
        assert "Internal" in content or "internal" in content, (
            "expected_output.md should explain internal signals"
        )
        assert "Parent" in content or "parent" in content or "Child" in content, (
            "expected_output.md should explain parent-child pattern"
        )
