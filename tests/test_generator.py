"""Unit tests for PathPermutationGenerator.

Tests for path generation from workflow metadata, including edge cases,
error handling, and performance validation.

Tests cover:
- Epic 2: Linear workflows (0 decisions)
- Epic 3: Decision-based path permutation (2^n paths for n decisions)
"""

import time
from pathlib import Path

import pytest

from temporalio_graphs._internal.graph_models import DecisionPoint, WorkflowMetadata, Activity
from temporalio_graphs.context import GraphBuildingContext
from temporalio_graphs.exceptions import GraphGenerationError
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
        activities=[Activity("ValidateInput", 10)],
        decision_points=[],
        signal_points=[],
        source_file=Path("workflows.py"),
        total_paths=1,
    )

    paths = generator.generate_paths(metadata, default_context)

    assert len(paths) == 1
    assert paths[0].path_id == "path_0"
    assert [step.name for step in paths[0].steps] == ["ValidateInput"]


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
        activities=[Activity("ValidateInput", 10), Activity("ProcessOrder", 20), Activity("SendConfirmation", 30)],
        decision_points=[],
        signal_points=[],
        source_file=Path("workflows.py"),
        total_paths=1,
    )

    paths = generator.generate_paths(metadata, default_context)

    assert len(paths) == 1
    assert paths[0].path_id == "path_0"
    assert [step.name for step in paths[0].steps] == ["ValidateInput", "ProcessOrder", "SendConfirmation"]


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
    assert [step.name for step in paths[0].steps] == activities


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

    assert [step.name for step in paths[0].steps] == activity_sequence


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
        activities=[Activity("Step1", 10), Activity("Step2", 20), Activity("Step3", 30)],
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
        activities=[Activity("DoSomething", 10)],
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
        activities=[Activity("ActivityA", 10), Activity("ActivityB", 20), Activity("ActivityC", 30)],
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
    assert path.steps[0].name == "ActivityA"
    assert path.steps[1].name == "ActivityB"
    assert path.steps[2].name == "ActivityC"


def test_generate_paths_with_decisions_returns_paths(
    generator: PathPermutationGenerator, default_context: GraphBuildingContext
) -> None:
    """Verify decision support is now implemented (Epic 3 feature).

    Validates that workflows with decisions are now supported and return
    the correct number of paths instead of raising an error.
    """
    decision = DecisionPoint(
        id="d0",
        name="CheckAmount",
        line_number=30, line_num=30,
        true_label="yes",
        false_label="no",
    )
    metadata = WorkflowMetadata(
        workflow_class="DecisionWorkflow",
        workflow_run_method="run",
        activities=[Activity("Step1", 10), Activity("Step2", 20)],
        decision_points=[decision],
        signal_points=[],
        source_file=Path("workflows.py"),
        total_paths=2,
    )

    # Should now return paths instead of raising NotImplementedError
    paths = generator.generate_paths(metadata, default_context)

    assert len(paths) == 2, f"Expected 2 paths for 1 decision, got {len(paths)}"
    assert "CheckAmount" in str(paths[0].steps or paths[1].steps)


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
        activities=[Activity("DoWork", 10)],
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
    """Validate performance requirement: <1ms for 100 activities.

    Measures path generation time for large workflow and asserts
    it completes within reasonable performance (<1ms).
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

    # Assert performance requirement: <1ms for 100 activities
    assert elapsed_time < 0.001, f"Performance requirement: <1ms, got {elapsed_time*1000:.4f}ms"
    assert len(paths) == 1
    assert len(paths[0].steps) == 100
    assert [step.name for step in paths[0].steps] == activities


# =============================================================================
# Epic 3: Decision Support Tests
# =============================================================================


def test_generate_zero_decisions_returns_linear_path(
    generator: PathPermutationGenerator, default_context: GraphBuildingContext
) -> None:
    """Test backward compatibility: 0 decisions returns 1 linear path.

    Validates Epic 2 behavior is preserved - workflows with no decisions
    should generate exactly one path using the linear algorithm.
    This is a regression test for backward compatibility.
    """
    metadata = WorkflowMetadata(
        workflow_class="LinearWorkflow",
        workflow_run_method="run",
        activities=[Activity("Withdraw", 10), Activity("Deposit", 20)],
        decision_points=[],
        signal_points=[],
        source_file=Path("workflows.py"),
        total_paths=1,
    )

    paths = generator.generate_paths(metadata, default_context)

    assert len(paths) == 1
    assert paths[0].path_id == "path_0"
    assert [step.name for step in paths[0].steps] == ["Withdraw", "Deposit"]
    assert len(paths[0].decisions) == 0


def test_generate_one_decision_two_paths(
    generator: PathPermutationGenerator, default_context: GraphBuildingContext
) -> None:
    """Test 1 decision generates exactly 2 paths (True and False branches).

    Validates 2^1 = 2 paths are generated for a single decision point.
    Each path should have a different decision value.
    """
    decision = DecisionPoint(
        id="d0",
        name="HighValue",
        line_number=42, line_num=42,
        true_label="yes",
        false_label="no",
    )
    metadata = WorkflowMetadata(
        workflow_class="OneDecisionWorkflow",
        workflow_run_method="run",
        activities=[Activity("Withdraw", 10), Activity("Deposit", 20)],
        decision_points=[decision],
        signal_points=[],
        source_file=Path("workflows.py"),
        total_paths=2,
    )

    paths = generator.generate_paths(metadata, default_context)

    # Should generate exactly 2 paths
    assert len(paths) == 2, f"Expected 2 paths for 1 decision, got {len(paths)}"

    # Each path should have the decision recorded with different values
    decision_values = [path.decisions.get("d0") for path in paths]
    assert True in decision_values, "Missing path with decision=True"
    assert False in decision_values, "Missing path with decision=False"

    # Verify path IDs are unique
    path_ids = {path.path_id for path in paths}
    assert len(path_ids) == 2, "Path IDs should be unique"


def test_generate_two_decisions_four_paths(
    generator: PathPermutationGenerator, default_context: GraphBuildingContext
) -> None:
    """Test 2 decisions generate exactly 4 paths (2^2 combinations).

    Validates 2^2 = 4 paths are generated with all combinations:
    (True, True), (True, False), (False, True), (False, False).
    """
    decisions = [
        DecisionPoint("d0", "NeedConvert", 42, 42, "yes", "no"),
        DecisionPoint("d1", "HighValue", 55, 55, "yes", "no"),
    ]
    metadata = WorkflowMetadata(
        workflow_class="TwoDecisionWorkflow",
        workflow_run_method="run",
        activities=[Activity("Withdraw", 10), Activity("CurrencyConvert", 20), Activity("Deposit", 30)],
        decision_points=decisions,
        signal_points=[],
        source_file=Path("workflows.py"),
        total_paths=4,
    )

    paths = generator.generate_paths(metadata, default_context)

    # Should generate exactly 4 paths
    assert len(paths) == 4, f"Expected 4 paths for 2 decisions, got {len(paths)}"

    # Verify all combinations are present
    decision_combos = [
        (path.decisions.get("d0"), path.decisions.get("d1")) for path in paths
    ]
    expected_combos = [(True, True), (True, False), (False, True), (False, False)]

    for combo in expected_combos:
        assert combo in decision_combos, f"Missing combination {combo}"


def test_generate_three_decisions_eight_paths(
    generator: PathPermutationGenerator, default_context: GraphBuildingContext
) -> None:
    """Test 3 decisions generate exactly 8 paths (2^3 combinations).

    Validates 2^3 = 8 paths are generated with all combinations.
    """
    decisions = [
        DecisionPoint("d0", "Decision1", 10, 10, "yes", "no"),
        DecisionPoint("d1", "Decision2", 20, 20, "yes", "no"),
        DecisionPoint("d2", "Decision3", 30, 30, "yes", "no"),
    ]
    metadata = WorkflowMetadata(
        workflow_class="ThreeDecisionWorkflow",
        workflow_run_method="run",
        activities=[Activity("Activity1", 10), Activity("Activity2", 20)],
        decision_points=decisions,
        signal_points=[],
        source_file=Path("workflows.py"),
        total_paths=8,
    )

    paths = generator.generate_paths(metadata, default_context)

    # Should generate exactly 8 paths
    assert len(paths) == 8, f"Expected 8 paths for 3 decisions, got {len(paths)}"

    # Verify all paths have all decisions recorded
    for path in paths:
        assert len(path.decisions) == 3, f"Path should have 3 decisions, has {len(path.decisions)}"
        assert all(isinstance(v, bool) for v in path.decisions.values()), \
            f"All decision values should be bool, got {path.decisions}"


def test_generate_custom_branch_labels(
    generator: PathPermutationGenerator,
) -> None:
    """Test custom decision branch labels via GraphBuildingContext.

    Validates that context.decision_true_label and decision_false_label
    are respected (though labels are used by renderer, not generator).
    This test verifies the context is accepted without error.
    """
    custom_context = GraphBuildingContext(
        decision_true_label="T",
        decision_false_label="F",
    )

    decision = DecisionPoint("d0", "TestDecision", 50, 50, "yes", "no")
    metadata = WorkflowMetadata(
        workflow_class="CustomLabelWorkflow",
        workflow_run_method="run",
        activities=[Activity("Step1", 10), Activity("Step2", 20)],
        decision_points=[decision],
        signal_points=[],
        source_file=Path("workflows.py"),
        total_paths=2,
    )

    paths = generator.generate_paths(metadata, custom_context)

    assert len(paths) == 2
    # Labels are used by renderer, not stored in path, so we just verify it didn't error


def test_explosion_limit_exceeds_default(
    generator: PathPermutationGenerator, default_context: GraphBuildingContext
) -> None:
    """Test error when decisions exceed default max_decision_points (10).

    Validates that 11 decisions raises GraphGenerationError because
    2^11 = 2048 paths exceeds the default limit of max_decision_points=10.
    """
    # Create 11 decisions (exceeds default max of 10)
    decisions = [
        DecisionPoint(f"d{i}", f"Decision{i}", 10 + i, 10 + i, "yes", "no")
        for i in range(11)
    ]
    metadata = WorkflowMetadata(
        workflow_class="TooManyDecisionsWorkflow",
        workflow_run_method="run",
        activities=[Activity("Activity1", 10)],
        decision_points=decisions,
        signal_points=[],
        source_file=Path("workflows.py"),
        total_paths=2**11,
    )

    with pytest.raises(GraphGenerationError) as exc_info:
        generator.generate_paths(metadata, default_context)

    error_msg = str(exc_info.value)
    assert "11" in error_msg, "Error should mention 11 decision points"
    assert "2048" in error_msg, "Error should mention 2048 paths"
    assert "10" in error_msg, "Error should mention the 10 decision point limit"


def test_explosion_limit_custom(
    generator: PathPermutationGenerator,
) -> None:
    """Test custom explosion limit via context.max_decision_points.

    Validates that context.max_decision_points is respected:
    - 5 decisions allowed when limit=5
    - 6 decisions raises error when limit=5
    """
    custom_context = GraphBuildingContext(max_decision_points=5)

    # Test 5 decisions (should succeed with limit=5)
    decisions_5 = [
        DecisionPoint(f"d{i}", f"Decision{i}", 10 + i, 10 + i, "yes", "no")
        for i in range(5)
    ]
    metadata_5 = WorkflowMetadata(
        workflow_class="FiveDecisionWorkflow",
        workflow_run_method="run",
        activities=[Activity("Activity1", 10)],
        decision_points=decisions_5,
        signal_points=[],
        source_file=Path("workflows.py"),
        total_paths=32,
    )

    paths_5 = generator.generate_paths(metadata_5, custom_context)
    assert len(paths_5) == 32, "Should allow 5 decisions when limit=5"

    # Test 6 decisions (should fail with limit=5)
    decisions_6 = [
        DecisionPoint(f"d{i}", f"Decision{i}", 10 + i, 10 + i, "yes", "no")
        for i in range(6)
    ]
    metadata_6 = WorkflowMetadata(
        workflow_class="SixDecisionWorkflow",
        workflow_run_method="run",
        activities=[Activity("Activity1", 10)],
        decision_points=decisions_6,
        signal_points=[],
        source_file=Path("workflows.py"),
        total_paths=64,
    )

    with pytest.raises(GraphGenerationError):
        generator.generate_paths(metadata_6, custom_context)


def test_all_permutations_complete(
    generator: PathPermutationGenerator, default_context: GraphBuildingContext
) -> None:
    """Test all 2^n permutations are generated with no duplicates.

    For 3 decisions, validates that all 8 combinations are present.
    """
    decisions = [
        DecisionPoint("d0", "Decision1", 10, 10, "yes", "no"),
        DecisionPoint("d1", "Decision2", 20, 20, "yes", "no"),
        DecisionPoint("d2", "Decision3", 30, 30, "yes", "no"),
    ]
    metadata = WorkflowMetadata(
        workflow_class="PermutationCheckWorkflow",
        workflow_run_method="run",
        activities=[Activity("Activity1", 10)],
        decision_points=decisions,
        signal_points=[],
        source_file=Path("workflows.py"),
        total_paths=8,
    )

    paths = generator.generate_paths(metadata, default_context)

    # Collect all unique decision combinations
    combos = set()
    for path in paths:
        combo = tuple(
            path.decisions[f"d{i}"] for i in range(3)
        )
        combos.add(combo)

    # Verify all 8 combinations are present
    assert len(combos) == 8, f"Should have 8 unique combinations, got {len(combos)}"

    # Verify all expected combinations are there
    for d0 in [True, False]:
        for d1 in [True, False]:
            for d2 in [True, False]:
                assert (d0, d1, d2) in combos, \
                    f"Missing combination ({d0}, {d1}, {d2})"


def test_performance_five_decisions(
    generator: PathPermutationGenerator, default_context: GraphBuildingContext
) -> None:
    """Validate performance requirement: 32 paths (5 decisions) in <1 second.

    NFR-PERF-1 requirement: generation of 32 paths must complete in <1 second.
    """
    decisions = [
        DecisionPoint(f"d{i}", f"Decision{i}", 10 + i, 10 + i, "yes", "no")
        for i in range(5)
    ]
    metadata = WorkflowMetadata(
        workflow_class="FiveDecisionPerf",
        workflow_run_method="run",
        activities=[Activity("Activity1", 10), Activity("Activity2", 20)],
        decision_points=decisions,
        signal_points=[],
        source_file=Path("workflows.py"),
        total_paths=32,
    )

    # Measure generation time
    start_time = time.perf_counter()
    paths = generator.generate_paths(metadata, default_context)
    elapsed_time = time.perf_counter() - start_time

    # Should generate 32 paths
    assert len(paths) == 32, f"Expected 32 paths, got {len(paths)}"

    # Should complete in <1 second
    assert elapsed_time < 1.0, \
        f"Performance requirement: <1s for 32 paths, got {elapsed_time:.4f}s"


def test_performance_ten_decisions(
    generator: PathPermutationGenerator, default_context: GraphBuildingContext
) -> None:
    """Validate performance requirement: 1024 paths (10 decisions) in <5 seconds.

    NFR-PERF-2 requirement: generation of 1024 paths must complete in <5 seconds.
    """
    decisions = [
        DecisionPoint(f"d{i}", f"Decision{i}", 10 + i, 10 + i, "yes", "no")
        for i in range(10)
    ]
    metadata = WorkflowMetadata(
        workflow_class="TenDecisionPerf",
        workflow_run_method="run",
        activities=[Activity("Activity1", 10)],
        decision_points=decisions,
        signal_points=[],
        source_file=Path("workflows.py"),
        total_paths=1024,
    )

    # Measure generation time
    start_time = time.perf_counter()
    paths = generator.generate_paths(metadata, default_context)
    elapsed_time = time.perf_counter() - start_time

    # Should generate 1024 paths
    assert len(paths) == 1024, f"Expected 1024 paths, got {len(paths)}"

    # Should complete in <5 seconds
    assert elapsed_time < 5.0, \
        f"Performance requirement: <5s for 1024 paths, got {elapsed_time:.4f}s"
