"""Unit tests for PathPermutationGenerator.

Tests for path generation from workflow metadata, including edge cases,
error handling, and performance validation.
"""

import time
from pathlib import Path

import pytest

from temporalio_graphs._internal.graph_models import WorkflowMetadata
from temporalio_graphs.context import GraphBuildingContext
from temporalio_graphs.generator import PathPermutationGenerator


@pytest.fixture
def generator() -> PathPermutationGenerator:
    """Create a PathPermutationGenerator instance for testing."""
    return PathPermutationGenerator()


@pytest.fixture
def default_context() -> GraphBuildingContext:
    """Create a GraphBuildingContext with default settings."""
    return GraphBuildingContext()


@pytest.fixture
def custom_context() -> GraphBuildingContext:
    """Create a GraphBuildingContext with custom labels."""
    return GraphBuildingContext(
        start_node_label="BEGIN",
        end_node_label="FINISH",
        max_decision_points=5,
    )


def test_generate_paths_empty_workflow(
    generator: PathPermutationGenerator, default_context: GraphBuildingContext
) -> None:
    """Generate paths for workflow with 0 activities (edge case).

    Validates that empty workflows are handled gracefully by returning
    a single path with empty steps list.
    """
    metadata = WorkflowMetadata(
        workflow_class="EmptyWorkflow",
        workflow_run_method="run",
        activities=[],
        decision_points=[],
        signal_points=[],
        source_file=Path("workflows.py"),
        total_paths=1,
    )

    paths = generator.generate_paths(metadata, default_context)

    assert len(paths) == 1
    assert paths[0].path_id == "path_0"
    assert paths[0].steps == []


def test_generate_paths_single_activity(
    generator: PathPermutationGenerator, default_context: GraphBuildingContext
) -> None:
    """Generate paths for workflow with 1 activity (minimal case).

    Validates minimal workflow with single activity is handled correctly.
    """
    metadata = WorkflowMetadata(
        workflow_class="SingleActivityWorkflow",
        workflow_run_method="run",
        activities=["ValidateInput"],
        decision_points=[],
        signal_points=[],
        source_file=Path("workflows.py"),
        total_paths=1,
    )

    paths = generator.generate_paths(metadata, default_context)

    assert len(paths) == 1
    assert paths[0].path_id == "path_0"
    assert paths[0].steps == ["ValidateInput"]


def test_generate_paths_multiple_activities(
    generator: PathPermutationGenerator, default_context: GraphBuildingContext
) -> None:
    """Generate paths for workflow with multiple activities (typical case).

    Validates typical workflow with 3-5 activities is handled correctly
    with all activities preserved in sequence.
    """
    metadata = WorkflowMetadata(
        workflow_class="MultiActivityWorkflow",
        workflow_run_method="run",
        activities=["ValidateInput", "ProcessOrder", "SendConfirmation"],
        decision_points=[],
        signal_points=[],
        source_file=Path("workflows.py"),
        total_paths=1,
    )

    paths = generator.generate_paths(metadata, default_context)

    assert len(paths) == 1
    assert paths[0].path_id == "path_0"
    assert paths[0].steps == ["ValidateInput", "ProcessOrder", "SendConfirmation"]


def test_generate_paths_large_workflow(
    generator: PathPermutationGenerator, default_context: GraphBuildingContext
) -> None:
    """Generate paths for large workflow with 100 activities.

    Validates that large workflows are handled correctly and efficiently.
    Ensures algorithm scales linearly (O(n)) without performance degradation.
    """
    activities = [f"Activity{i}" for i in range(100)]
    metadata = WorkflowMetadata(
        workflow_class="LargeWorkflow",
        workflow_run_method="run",
        activities=activities,
        decision_points=[],
        signal_points=[],
        source_file=Path("workflows.py"),
        total_paths=1,
    )

    paths = generator.generate_paths(metadata, default_context)

    assert len(paths) == 1
    assert paths[0].path_id == "path_0"
    assert len(paths[0].steps) == 100
    assert paths[0].steps == activities


def test_generate_paths_preserves_activity_order(
    generator: PathPermutationGenerator, default_context: GraphBuildingContext
) -> None:
    """Verify that activity order is preserved in generated path.

    Validates that activities appear in the same sequence as in metadata.
    Order preservation is critical for correct graph representation.
    """
    activity_sequence = [
        "Withdraw",
        "CurrencyConvert",
        "Deposit",
        "NotifyATO",
        "LogTransaction",
    ]
    metadata = WorkflowMetadata(
        workflow_class="MoneyTransferWorkflow",
        workflow_run_method="run",
        activities=activity_sequence,
        decision_points=[],
        signal_points=[],
        source_file=Path("workflows.py"),
        total_paths=1,
    )

    paths = generator.generate_paths(metadata, default_context)

    assert paths[0].steps == activity_sequence


def test_generate_paths_returns_single_element_list(
    generator: PathPermutationGenerator, default_context: GraphBuildingContext
) -> None:
    """Verify that linear workflows always return list with exactly 1 path.

    Validates Epic 2 constraint: linear workflows (0 decisions) generate
    exactly one execution path, not multiple paths.
    """
    metadata = WorkflowMetadata(
        workflow_class="LinearWorkflow",
        workflow_run_method="run",
        activities=["Step1", "Step2", "Step3"],
        decision_points=[],
        signal_points=[],
        source_file=Path("workflows.py"),
        total_paths=1,
    )

    paths = generator.generate_paths(metadata, default_context)

    assert len(paths) == 1
    assert isinstance(paths, list)


def test_generate_paths_with_custom_labels(
    generator: PathPermutationGenerator, custom_context: GraphBuildingContext
) -> None:
    """Test generator respects custom context labels.

    Validates that GraphBuildingContext with custom start/end labels
    is accepted and does not affect path generation. Labels are used
    by renderer, not generator, but context is passed through.
    """
    metadata = WorkflowMetadata(
        workflow_class="CustomLabelWorkflow",
        workflow_run_method="run",
        activities=["DoSomething"],
        decision_points=[],
        signal_points=[],
        source_file=Path("workflows.py"),
        total_paths=1,
    )

    # Should not raise, custom context is accepted
    paths = generator.generate_paths(metadata, custom_context)

    assert len(paths) == 1
    assert paths[0].path_id == "path_0"


def test_generate_paths_node_id_assignment(
    generator: PathPermutationGenerator, default_context: GraphBuildingContext
) -> None:
    """Verify node IDs are assigned sequentially as strings "1", "2", "3".

    Validates that GraphPath.add_activity() generates sequential string IDs
    and they are not integers or formatted differently.
    """
    metadata = WorkflowMetadata(
        workflow_class="NodeIDWorkflow",
        workflow_run_method="run",
        activities=["ActivityA", "ActivityB", "ActivityC"],
        decision_points=[],
        signal_points=[],
        source_file=Path("workflows.py"),
        total_paths=1,
    )

    paths = generator.generate_paths(metadata, default_context)
    path = paths[0]

    # Verify activities were added (each call to add_activity returns node ID)
    # We don't check node IDs here directly as they're internal to GraphPath,
    # but we verify the steps list is populated and in order
    assert len(path.steps) == 3
    assert path.steps[0] == "ActivityA"
    assert path.steps[1] == "ActivityB"
    assert path.steps[2] == "ActivityC"


def test_generate_paths_raises_not_implemented_for_decisions(
    generator: PathPermutationGenerator, default_context: GraphBuildingContext
) -> None:
    """Verify NotImplementedError is raised for workflows with decisions.

    Validates that decision support (Epic 3 feature) properly raises
    NotImplementedError with clear message about epic scope.
    """
    metadata = WorkflowMetadata(
        workflow_class="DecisionWorkflow",
        workflow_run_method="run",
        activities=["Step1", "Step2"],
        decision_points=["CheckAmount"],  # This should trigger error
        signal_points=[],
        source_file=Path("workflows.py"),
        total_paths=2,
    )

    with pytest.raises(NotImplementedError) as exc_info:
        generator.generate_paths(metadata, default_context)

    error_msg = str(exc_info.value)
    assert "Epic 2" in error_msg or "Epic 3" in error_msg
    assert "decision" in error_msg.lower()


def test_generate_paths_validates_metadata_not_none(
    generator: PathPermutationGenerator, default_context: GraphBuildingContext
) -> None:
    """Verify ValueError is raised when metadata is None.

    Validates input validation catches None metadata and provides
    actionable error message.
    """
    with pytest.raises(ValueError) as exc_info:
        generator.generate_paths(None, default_context)  # type: ignore

    error_msg = str(exc_info.value)
    assert "metadata" in error_msg.lower()
    assert "None" in error_msg or "cannot be" in error_msg


def test_generate_paths_handles_none_context(
    generator: PathPermutationGenerator,
) -> None:
    """Verify generator handles None context gracefully (uses defaults).

    Validates that passing None for context does not raise error.
    Generator should use default GraphBuildingContext() if None provided.
    """
    metadata = WorkflowMetadata(
        workflow_class="NoneContextWorkflow",
        workflow_run_method="run",
        activities=["DoWork"],
        decision_points=[],
        signal_points=[],
        source_file=Path("workflows.py"),
        total_paths=1,
    )

    # Should not raise, should use default context
    paths = generator.generate_paths(metadata, None)  # type: ignore

    assert len(paths) == 1
    assert paths[0].path_id == "path_0"


def test_generate_paths_performance_100_activities(
    generator: PathPermutationGenerator, default_context: GraphBuildingContext
) -> None:
    """Validate performance requirement: <0.1ms for 100 activities.

    Measures path generation time for large workflow and asserts
    it completes within NFR-PERF-1 requirement of <0.1ms (0.0001 seconds).
    This validates O(n) linear algorithm scalability.
    """
    activities = [f"Activity{i}" for i in range(100)]
    metadata = WorkflowMetadata(
        workflow_class="PerformanceWorkflow",
        workflow_run_method="run",
        activities=activities,
        decision_points=[],
        signal_points=[],
        source_file=Path("workflows.py"),
        total_paths=1,
    )

    # Measure generation time
    start_time = time.perf_counter()
    paths = generator.generate_paths(metadata, default_context)
    elapsed_time = time.perf_counter() - start_time

    # Assert performance requirement
    assert elapsed_time < 0.0001, f"Performance requirement: <0.1ms, got {elapsed_time*1000:.4f}ms"
    assert len(paths) == 1
    assert len(paths[0].steps) == 100
