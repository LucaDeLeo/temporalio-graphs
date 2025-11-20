"""Integration tests for external signal detection and path generation.

This module validates the complete pipeline for Epic 7: workflow file with
external signal → WorkflowAnalyzer → WorkflowMetadata → PathPermutationGenerator
→ paths with external signal nodes in correct execution order.
"""

import ast
from pathlib import Path

import pytest

from temporalio_graphs.analyzer import WorkflowAnalyzer
from temporalio_graphs.context import GraphBuildingContext
from temporalio_graphs.generator import PathPermutationGenerator
from temporalio_graphs.renderer import MermaidRenderer


@pytest.fixture
def order_workflow_with_external_signal(tmp_path: Path) -> Path:
    """Workflow that sends external signal to Shipping workflow."""
    source = '''from datetime import timedelta
import temporalio.workflow as workflow
from temporalio.workflow import workflow_method

@workflow.defn
class OrderWorkflow:
    @workflow.run
    async def run(self, order_id: str) -> str:
        await workflow.execute_activity(
            process_order,
            order_id,
            start_to_close_timeout=timedelta(seconds=30)
        )

        # Send external signal to Shipping workflow
        handle = workflow.get_external_workflow_handle(f"shipping-{order_id}")
        await handle.signal("ship_order", order_id)

        await workflow.execute_activity(
            complete_order,
            order_id,
            start_to_close_timeout=timedelta(seconds=30)
        )
        return "complete"

def process_order(order_id: str) -> None:
    pass

def complete_order(order_id: str) -> None:
    pass
'''
    workflow_file = tmp_path / "order_workflow.py"
    workflow_file.write_text(source)
    return workflow_file


@pytest.fixture
def workflow_with_decision_and_external_signal(tmp_path: Path) -> Path:
    """Workflow with 1 decision and 1 external signal."""
    source = '''from datetime import timedelta
import temporalio.workflow as workflow
from temporalio_graphs.helpers import to_decision

@workflow.defn
class OrderWorkflow:
    @workflow.run
    async def run(self, order_id: str, is_priority: bool) -> str:
        await workflow.execute_activity(
            validate_order,
            order_id,
            start_to_close_timeout=timedelta(seconds=30)
        )

        # Decision point
        if await to_decision(is_priority, "IsPriority"):
            # Send priority notification to shipping
            handle = workflow.get_external_workflow_handle(f"shipping-{order_id}")
            await handle.signal("priority_ship", order_id)

        await workflow.execute_activity(
            process_order,
            order_id,
            start_to_close_timeout=timedelta(seconds=30)
        )
        return "complete"

def validate_order(order_id: str) -> None:
    pass

def process_order(order_id: str) -> None:
    pass
'''
    workflow_file = tmp_path / "order_with_decision.py"
    workflow_file.write_text(source)
    return workflow_file


class TestExternalSignalDetectionIntegration:
    """Integration tests for external signal detection in analysis pipeline."""

    def test_external_signal_detected_in_metadata(
        self, order_workflow_with_external_signal: Path
    ) -> None:
        """Validate WorkflowMetadata.external_signals contains ExternalSignalCall."""
        # Analyze workflow file
        context = GraphBuildingContext()
        analyzer = WorkflowAnalyzer()
        metadata = analyzer.analyze(order_workflow_with_external_signal, context)

        # Validate external signal was detected
        assert len(metadata.external_signals) == 1, (
            f"Expected 1 external signal, found {len(metadata.external_signals)}"
        )

        external_signal = metadata.external_signals[0]
        assert external_signal.signal_name == "ship_order"
        assert external_signal.target_workflow_pattern == "shipping-{*}"
        assert external_signal.source_workflow == "OrderWorkflow"
        assert external_signal.source_line > 0
        assert external_signal.node_id == f"ext_sig_ship_order_{external_signal.source_line}"

    def test_external_signal_appears_in_paths(
        self, order_workflow_with_external_signal: Path
    ) -> None:
        """Validate PathPermutationGenerator includes external signal node in paths.

        Also validates AC7, AC9: Mermaid rendering of external signals with
        trapezoid syntax, dashed edges, and color styling.
        """
        # Analyze workflow file
        context = GraphBuildingContext()
        analyzer = WorkflowAnalyzer()
        metadata = analyzer.analyze(order_workflow_with_external_signal, context)

        # Generate paths
        generator = PathPermutationGenerator()
        paths = generator.generate_paths(metadata, context)

        # Validate 1 path generated (linear workflow)
        assert len(paths) == 1, f"Expected 1 path, found {len(paths)}"

        path = paths[0]
        # Validate path contains: ProcessOrder -> ExternalSignal -> CompleteOrder
        assert len(path.steps) == 3, f"Expected 3 steps, found {len(path.steps)}"

        # Validate step types and order
        assert path.steps[0].node_type == "activity"
        assert path.steps[0].name == "process_order"

        assert path.steps[1].node_type == "external_signal"
        assert path.steps[1].name == "ship_order"
        assert path.steps[1].target_workflow_pattern == "shipping-{*}"

        assert path.steps[2].node_type == "activity"
        assert path.steps[2].name == "complete_order"

        # AC7, AC9: Validate Mermaid rendering
        renderer = MermaidRenderer()
        mermaid_output = renderer.to_mermaid(paths, context)

        # Validate trapezoid shape appears (AC7)
        assert "[/Signal 'ship_order'\\]" in mermaid_output, (
            "External signal should render with trapezoid syntax in Mermaid output"
        )

        # Validate dashed edge appears (AC7)
        assert "-.signal.->" in mermaid_output, (
            "External signal edges should use dashed style in Mermaid output"
        )

        # Validate color styling appears (AC7)
        assert "style ext_sig_" in mermaid_output, (
            "External signal color styling directive should appear in Mermaid output"
        )
        assert "fill:#fff4e6" in mermaid_output, (
            "External signal should have orange/amber fill color"
        )
        assert "stroke:#ffa500" in mermaid_output, (
            "External signal should have orange stroke color"
        )

    def test_external_signal_node_ordering(
        self, order_workflow_with_external_signal: Path
    ) -> None:
        """Validate external signal appears at correct source line position."""
        # Analyze workflow file
        context = GraphBuildingContext()
        analyzer = WorkflowAnalyzer()
        metadata = analyzer.analyze(order_workflow_with_external_signal, context)

        # Generate paths
        generator = PathPermutationGenerator()
        paths = generator.generate_paths(metadata, context)
        path = paths[0]

        # Get line numbers from metadata
        process_order_line = metadata.activities[0].line_num
        complete_order_line = metadata.activities[1].line_num
        external_signal_line = metadata.external_signals[0].source_line

        # Validate line number ordering: ProcessOrder < ExternalSignal < CompleteOrder
        assert process_order_line < external_signal_line, (
            f"ProcessOrder (line {process_order_line}) should come before "
            f"ExternalSignal (line {external_signal_line})"
        )
        assert external_signal_line < complete_order_line, (
            f"ExternalSignal (line {external_signal_line}) should come before "
            f"CompleteOrder (line {complete_order_line})"
        )

        # Validate path steps are in correct order
        assert path.steps[0].name == "process_order"
        assert path.steps[1].name == "ship_order"
        assert path.steps[2].name == "complete_order"

    def test_external_signal_no_path_explosion(
        self, order_workflow_with_external_signal: Path
    ) -> None:
        """Validate external signals don't create additional path permutations."""
        # Analyze workflow file (0 decisions, 1 external signal)
        context = GraphBuildingContext()
        analyzer = WorkflowAnalyzer()
        metadata = analyzer.analyze(order_workflow_with_external_signal, context)

        # Generate paths
        generator = PathPermutationGenerator()
        paths = generator.generate_paths(metadata, context)

        # Validate path count is 1 (2^0 = 1 path, external signal doesn't branch)
        assert len(paths) == 1, (
            f"Expected 1 path for linear workflow with external signal, "
            f"found {len(paths)} paths"
        )

        # Validate metadata.total_paths reflects no branching
        assert metadata.total_paths == 1

    def test_external_signal_with_decision(
        self, workflow_with_decision_and_external_signal: Path
    ) -> None:
        """Validate workflow with 1 decision and 1 external signal generates 2 paths.

        NOTE: External signals are currently treated as unconditional nodes (like
        activities before Epic 3). Conditional external signals (inside if blocks)
        appear in all paths. Full decision-aware filtering would require extending
        DecisionDetector to track external signal line numbers in branches, which
        is out of scope for Story 7.3.
        """
        # Analyze workflow file (1 decision, 1 external signal in true branch)
        context = GraphBuildingContext()
        analyzer = WorkflowAnalyzer()
        metadata = analyzer.analyze(workflow_with_decision_and_external_signal, context)

        # Generate paths
        generator = PathPermutationGenerator()
        paths = generator.generate_paths(metadata, context)

        # Validate path count is 2 (2^1 from decision only)
        assert len(paths) == 2, (
            f"Expected 2 paths for workflow with 1 decision, found {len(paths)}"
        )

        # Both paths contain: ValidateOrder -> Decision -> ExternalSignal -> ProcessOrder
        # (External signal appears unconditionally in current implementation)
        for i, path in enumerate(paths):
            assert path.steps[0].name == "validate_order"
            assert path.steps[1].node_type == "decision"
            assert path.steps[1].name == "IsPriority"
            assert path.steps[2].node_type == "external_signal"
            assert path.steps[2].name == "priority_ship"
            assert path.steps[3].name == "process_order"

    def test_external_signal_with_multiple_signals(self, tmp_path: Path) -> None:
        """Validate workflow with multiple external signals maintains correct order."""
        source = '''from datetime import timedelta
import temporalio.workflow as workflow

@workflow.defn
class OrderWorkflow:
    @workflow.run
    async def run(self, order_id: str) -> str:
        # First external signal
        handle1 = workflow.get_external_workflow_handle(f"warehouse-{order_id}")
        await handle1.signal("reserve_inventory", order_id)

        await workflow.execute_activity(
            process_payment,
            order_id,
            start_to_close_timeout=timedelta(seconds=30)
        )

        # Second external signal
        handle2 = workflow.get_external_workflow_handle(f"shipping-{order_id}")
        await handle2.signal("ship_order", order_id)

        return "complete"

def process_payment(order_id: str) -> None:
    pass
'''
        workflow_file = tmp_path / "multi_signal.py"
        workflow_file.write_text(source)

        # Analyze workflow file
        context = GraphBuildingContext()
        analyzer = WorkflowAnalyzer()
        metadata = analyzer.analyze(workflow_file, context)

        # Generate paths
        generator = PathPermutationGenerator()
        paths = generator.generate_paths(metadata, context)

        # Validate 2 external signals detected
        assert len(metadata.external_signals) == 2

        # Validate path contains nodes in correct order
        path = paths[0]
        assert len(path.steps) == 3

        assert path.steps[0].node_type == "external_signal"
        assert path.steps[0].name == "reserve_inventory"

        assert path.steps[1].node_type == "activity"
        assert path.steps[1].name == "process_payment"

        assert path.steps[2].node_type == "external_signal"
        assert path.steps[2].name == "ship_order"
