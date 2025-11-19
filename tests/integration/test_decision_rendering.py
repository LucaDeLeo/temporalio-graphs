"""Integration tests for decision node rendering in Mermaid.

Tests the complete pipeline from workflow analysis through decision detection,
path generation, and Mermaid rendering. Validates that decision nodes render
correctly with branch labels and proper connectivity.
"""

from pathlib import Path

import pytest

from temporalio_graphs._internal.graph_models import DecisionPoint, WorkflowMetadata, Activity
from temporalio_graphs.context import GraphBuildingContext
from temporalio_graphs.generator import PathPermutationGenerator
from temporalio_graphs.renderer import MermaidRenderer


@pytest.fixture
def renderer() -> MermaidRenderer:
    """Create a MermaidRenderer instance."""
    return MermaidRenderer()


@pytest.fixture
def no_split_context() -> GraphBuildingContext:
    """Create context with word splitting disabled."""
    return GraphBuildingContext(split_names_by_words=False)


def test_decision_integration_single_decision(
    renderer: MermaidRenderer, no_split_context: GraphBuildingContext
) -> None:
    """Verify full pipeline with single decision.

    Tests complete flow: metadata -> path generation -> Mermaid rendering
    for a single decision point.
    """
    # Setup: Create workflow metadata with 1 decision
    d1 = DecisionPoint(
        id="d0", name="CheckLimit", line_number=42, line_num=42, true_label="yes", false_label="no"
    )
    metadata = WorkflowMetadata(
        workflow_class="TransferWorkflow",
        workflow_run_method="run",
        activities=[Activity("ValidateAccount", 10), Activity("Transfer", 20), Activity("NotifyUser", 30)],
        decision_points=[d1],
        signal_points=[],
        source_file=Path("workflows.py"),
        total_paths=2,
    )

    # Generate paths
    generator = PathPermutationGenerator()
    paths = generator.generate_paths(metadata, no_split_context)

    assert len(paths) == 2, "Should generate 2 paths for 1 decision"

    # Render to Mermaid
    result = renderer.to_mermaid(paths, no_split_context)

    # Verify structure
    assert "```mermaid" in result
    assert "flowchart LR" in result
    assert "s((Start))" in result
    assert "e((End))" in result

    # Verify all activities present (activity names are now used as node IDs)
    assert "ValidateAccount[ValidateAccount]" in result
    assert "Transfer[Transfer]" in result
    assert "NotifyUser[NotifyUser]" in result

    # Verify decision node
    assert "d0{CheckLimit}" in result

    # Verify branching
    assert "-- yes -->" in result
    assert "-- no -->" in result

    # Verify path count
    assert result.count("d0 --") == 2


def test_decision_integration_two_decisions(
    renderer: MermaidRenderer, no_split_context: GraphBuildingContext
) -> None:
    """Verify full pipeline with two sequential decisions (4 paths).

    Tests complete flow with 2 decisions generating 2^2 = 4 paths.
    """
    # Setup: Create workflow with 2 decisions
    d1 = DecisionPoint(
        id="d0", name="NeedConversion", line_number=42, line_num=42, true_label="yes", false_label="no"
    )
    d2 = DecisionPoint(
        id="d1", name="IsUrgent", line_number=55, line_num=55, true_label="yes", false_label="no"
    )

    metadata = WorkflowMetadata(
        workflow_class="PaymentWorkflow",
        workflow_run_method="run",
        activities=[Activity("Withdraw", 10), Activity("Convert", 20), Activity("Deposit", 30)],
        decision_points=[d1, d2],
        signal_points=[],
        source_file=Path("workflows.py"),
        total_paths=4,
    )

    # Generate paths
    generator = PathPermutationGenerator()
    paths = generator.generate_paths(metadata, no_split_context)

    assert len(paths) == 4, "Should generate 4 paths for 2 decisions (2^2)"

    # Verify each path has correct decisions
    path_decisions = [p.decisions for p in paths]
    assert {"d0": False, "d1": False} in path_decisions
    assert {"d0": False, "d1": True} in path_decisions
    assert {"d0": True, "d1": False} in path_decisions
    assert {"d0": True, "d1": True} in path_decisions

    # Render to Mermaid
    result = renderer.to_mermaid(paths, no_split_context)

    # Verify both decision nodes present
    assert "d0{NeedConversion}" in result
    assert "d1{IsUrgent}" in result

    # Verify deduplication (each decision appears once in definitions)
    assert result.count("d0{NeedConversion}") == 1
    assert result.count("d1{IsUrgent}") == 1

    # Verify all paths through both decisions
    assert "d0 -- yes --> d1" in result
    assert "d0 -- no --> d1" in result
    assert "d1 -- yes --> e" in result
    assert "d1 -- no --> e" in result


def test_decision_integration_with_custom_labels(
    renderer: MermaidRenderer,
) -> None:
    """Verify custom branch labels are applied throughout pipeline.

    Tests that custom decision labels from context are used in rendering.
    """
    # Create context with custom labels
    custom_context = GraphBuildingContext(
        decision_true_label="approved",
        decision_false_label="rejected",
        split_names_by_words=False,
    )

    d1 = DecisionPoint(
        id="d0", name="Approval", line_number=42, line_num=42, true_label="yes", false_label="no"
    )

    metadata = WorkflowMetadata(
        workflow_class="ApprovalWorkflow",
        workflow_run_method="run",
        activities=[Activity("SubmitRequest", 10), Activity("ProcessApproval", 20), Activity("NotifyUser", 30)],
        decision_points=[d1],
        signal_points=[],
        source_file=Path("workflows.py"),
        total_paths=2,
    )

    # Generate and render
    generator = PathPermutationGenerator()
    paths = generator.generate_paths(metadata, custom_context)
    result = renderer.to_mermaid(paths, custom_context)

    # Verify custom labels are used
    assert "-- approved -->" in result
    assert "-- rejected -->" in result

    # Verify default labels are NOT used
    assert "-- yes -->" not in result
    assert "-- no -->" not in result


def test_decision_integration_path_count_formula(
    renderer: MermaidRenderer, no_split_context: GraphBuildingContext
) -> None:
    """Verify path count matches 2^n formula for n decisions.

    Tests that the number of generated paths equals 2^num_decisions.
    """
    test_cases = [
        (1, 2),   # 1 decision = 2^1 = 2 paths
        (2, 4),   # 2 decisions = 2^2 = 4 paths
        (3, 8),   # 3 decisions = 2^3 = 8 paths
    ]

    for num_decisions, expected_paths in test_cases:
        # Create decisions dynamically
        decisions = [
            DecisionPoint(
                id=f"d{i}",
                name=f"Decision{i}",
                line_number=40 + i * 5,
                line_num=40 + i * 5,
                true_label="yes",
                false_label="no",
            )
            for i in range(num_decisions)
        ]

        metadata = WorkflowMetadata(
            workflow_class="TestWorkflow",
            workflow_run_method="run",
            activities=[Activity("Init", 10), Activity("Process", 20), Activity("Finalize", 30)],
            decision_points=decisions,
            signal_points=[],
            source_file=Path("workflows.py"),
            total_paths=expected_paths,
        )

        generator = PathPermutationGenerator()
        paths = generator.generate_paths(metadata, no_split_context)

        assert len(paths) == expected_paths, (
            f"Expected {expected_paths} paths for {num_decisions} decisions, "
            f"but got {len(paths)}"
        )

        # Render and verify all decisions are present
        result = renderer.to_mermaid(paths, no_split_context)
        for i in range(num_decisions):
            assert (
                f"d{i}{{Decision{i}}}" in result
            ), f"Decision d{i} should be in output"


def test_decision_integration_mermaid_syntax_validation(
    renderer: MermaidRenderer, no_split_context: GraphBuildingContext
) -> None:
    """Verify generated Mermaid syntax is valid and complete.

    Tests that output is syntactically valid and can be used in Mermaid viewers.
    """
    d1 = DecisionPoint(
        id="d0", name="Validate", line_number=42, line_num=42, true_label="yes", false_label="no"
    )

    metadata = WorkflowMetadata(
        workflow_class="ValidationWorkflow",
        workflow_run_method="run",
        activities=[Activity("Check", 10), Activity("Process", 20)],
        decision_points=[d1],
        signal_points=[],
        source_file=Path("workflows.py"),
        total_paths=2,
    )

    generator = PathPermutationGenerator()
    paths = generator.generate_paths(metadata, no_split_context)
    result = renderer.to_mermaid(paths, no_split_context)

    # Split into lines for validation
    lines = result.split("\n")

    # Verify structure
    assert lines[0] == "```mermaid"
    assert lines[1] == "flowchart LR"
    assert lines[-1] == "```"

    # Verify nodes come before edges
    node_lines = []
    edge_lines = []
    in_nodes = True

    for line in lines[2:-1]:
        if line and "-->" in line:
            in_nodes = False
        if in_nodes and line and "-->" not in line:
            node_lines.append(line)
        elif not in_nodes and line and "-->" in line:
            edge_lines.append(line)

    assert len(node_lines) > 0, "Should have node definitions"
    assert len(edge_lines) > 0, "Should have edge definitions"

    # Verify all nodes and edges have proper syntax
    for node_line in node_lines:
        # Node should have brackets or braces or parentheses
        assert (
            "{" in node_line or "[" in node_line or "(" in node_line
        ), f"Invalid node syntax: {node_line}"

    for edge_line in edge_lines:
        # Edge should have arrow
        assert "-->" in edge_line, f"Invalid edge syntax: {edge_line}"


def test_decision_integration_deduplication_across_paths(
    renderer: MermaidRenderer, no_split_context: GraphBuildingContext
) -> None:
    """Verify decision nodes are deduplicated across all paths.

    Tests that the same decision node appears only once even though
    it exists in all 4 paths (for 2 decisions).
    """
    d1 = DecisionPoint(
        id="d0", name="Check1", line_number=42, line_num=42, true_label="yes", false_label="no"
    )
    d2 = DecisionPoint(
        id="d1", name="Check2", line_number=55, line_num=55, true_label="yes", false_label="no"
    )

    metadata = WorkflowMetadata(
        workflow_class="CheckWorkflow",
        workflow_run_method="run",
        activities=[Activity("Prep", 10), Activity("Execute", 20)],
        decision_points=[d1, d2],
        signal_points=[],
        source_file=Path("workflows.py"),
        total_paths=4,
    )

    generator = PathPermutationGenerator()
    paths = generator.generate_paths(metadata, no_split_context)

    # Verify all 4 paths contain the same decision nodes
    for path in paths:
        assert "d0" in path.decisions
        assert "d1" in path.decisions
        assert len(path.decisions) == 2

    # Render with all paths
    result = renderer.to_mermaid(paths, no_split_context)

    # Count decision node definitions
    d0_count = result.count("d0{Check1}")
    d1_count = result.count("d1{Check2}")

    assert (
        d0_count == 1
    ), f"Decision d0 should appear exactly once in node definitions, found {d0_count}"
    assert (
        d1_count == 1
    ), f"Decision d1 should appear exactly once in node definitions, found {d1_count}"

    # Verify both decision nodes are reachable
    assert "d0 -- yes -->" in result
    assert "d0 -- no -->" in result
    assert "d1 -- yes -->" in result
    assert "d1 -- no -->" in result
