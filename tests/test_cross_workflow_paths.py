"""Tests for cross-workflow path generation (Story 6.4).

Tests all three expansion modes: reference, inline, subgraph.
Tests path explosion safeguards, workflow transitions, and multiple children.
"""

from pathlib import Path

import pytest

from temporalio_graphs._internal.graph_models import (
    Activity,
    ChildWorkflowCall,
    DecisionPoint,
    MultiWorkflowPath,
    WorkflowCallGraph,
    WorkflowMetadata,
)
from temporalio_graphs.context import GraphBuildingContext
from temporalio_graphs.exceptions import GraphGenerationError
from temporalio_graphs.generator import PathPermutationGenerator


@pytest.fixture
def linear_parent_metadata():
    """Parent workflow with 2 activities, no decisions, calls 1 child."""
    return WorkflowMetadata(
        workflow_class="ParentWorkflow",
        workflow_run_method="run",
        activities=[
            Activity("ParentActivity1", 10),
            Activity("ParentActivity2", 30),
        ],
        decision_points=[],
        signal_points=[],
        source_file=Path("parent.py"),
        total_paths=1,
        child_workflow_calls=[
            ChildWorkflowCall("ChildWorkflow", 20, "child_childworkflow_20", "ParentWorkflow")
        ],
    )


@pytest.fixture
def linear_child_metadata():
    """Child workflow with 2 activities, no decisions."""
    return WorkflowMetadata(
        workflow_class="ChildWorkflow",
        workflow_run_method="run",
        activities=[
            Activity("ChildActivity1", 10),
            Activity("ChildActivity2", 20),
        ],
        decision_points=[],
        signal_points=[],
        source_file=Path("child.py"),
        total_paths=1,
        child_workflow_calls=[],
    )


@pytest.fixture
def parent_with_decision_metadata():
    """Parent workflow with 1 decision (2 paths), calls 1 child."""
    return WorkflowMetadata(
        workflow_class="ParentWorkflow",
        workflow_run_method="run",
        activities=[
            Activity("ParentActivity1", 10),
            Activity("ParentActivity2", 40),
        ],
        decision_points=[
            DecisionPoint("d0", "ParentDecision", 15, 15, "yes", "no"),
        ],
        signal_points=[],
        source_file=Path("parent.py"),
        total_paths=2,
        child_workflow_calls=[
            ChildWorkflowCall("ChildWorkflow", 30, "child_childworkflow_30", "ParentWorkflow")
        ],
    )


@pytest.fixture
def child_with_decision_metadata():
    """Child workflow with 1 decision (2 paths)."""
    return WorkflowMetadata(
        workflow_class="ChildWorkflow",
        workflow_run_method="run",
        activities=[
            Activity("ChildActivity1", 10),
            Activity("ChildActivity2", 30),
        ],
        decision_points=[
            DecisionPoint("d0", "ChildDecision", 20, 20, "yes", "no"),
        ],
        signal_points=[],
        source_file=Path("child.py"),
        total_paths=2,
        child_workflow_calls=[],
    )


@pytest.fixture
def parent_with_multiple_decisions():
    """Parent workflow with 5 decisions (32 paths) for explosion testing."""
    return WorkflowMetadata(
        workflow_class="ParentWorkflow",
        workflow_run_method="run",
        activities=[Activity("Activity1", 10)],
        decision_points=[
            DecisionPoint(f"d{i}", f"Decision{i}", 20 + i * 5, 20 + i * 5, "yes", "no")
            for i in range(5)
        ],
        signal_points=[],
        source_file=Path("parent.py"),
        total_paths=32,
        child_workflow_calls=[
            ChildWorkflowCall("ChildWorkflow", 50, "child_childworkflow_50", "ParentWorkflow")
        ],
    )


@pytest.fixture
def child_with_multiple_decisions():
    """Child workflow with 5 decisions (32 paths) for explosion testing."""
    return WorkflowMetadata(
        workflow_class="ChildWorkflow",
        workflow_run_method="run",
        activities=[Activity("ChildActivity1", 10)],
        decision_points=[
            DecisionPoint(f"d{i}", f"ChildDecision{i}", 20 + i * 5, 20 + i * 5, "yes", "no")
            for i in range(5)
        ],
        signal_points=[],
        source_file=Path("child.py"),
        total_paths=32,
        child_workflow_calls=[],
    )


class TestReferenceMode:
    """Tests for reference mode (default, safest mode)."""

    def test_reference_mode_linear_workflows(self, linear_parent_metadata, linear_child_metadata):
        """Reference mode with linear parent and child generates 1 parent path."""
        call_graph = WorkflowCallGraph(
            root_workflow=linear_parent_metadata,
            child_workflows={"ChildWorkflow": linear_child_metadata},
            call_relationships=[("ParentWorkflow", "ChildWorkflow")],
            all_child_calls=linear_parent_metadata.child_workflow_calls,
            total_workflows=2,
        )

        context = GraphBuildingContext(child_workflow_expansion="reference")
        generator = PathPermutationGenerator()
        mw_paths = generator.generate_cross_workflow_paths(call_graph, context)

        # Reference mode should generate 1 path (linear parent, child not expanded)
        assert len(mw_paths) == 1
        assert mw_paths[0].path_id == "mwpath_0"
        assert mw_paths[0].workflows == ["ParentWorkflow"]
        assert mw_paths[0].steps == ["ParentActivity1", "ChildWorkflow", "ParentActivity2"]
        assert mw_paths[0].workflow_transitions == []  # No transitions in reference mode
        assert mw_paths[0].total_decisions == 0

    def test_reference_mode_parent_with_decisions(
        self,
        parent_with_decision_metadata,
        linear_child_metadata,
    ):
        """Reference mode with parent having 2 decisions generates 4 parent paths."""
        call_graph = WorkflowCallGraph(
            root_workflow=parent_with_decision_metadata,
            child_workflows={"ChildWorkflow": linear_child_metadata},
            call_relationships=[("ParentWorkflow", "ChildWorkflow")],
            all_child_calls=parent_with_decision_metadata.child_workflow_calls,
            total_workflows=2,
        )

        context = GraphBuildingContext(child_workflow_expansion="reference")
        generator = PathPermutationGenerator()
        mw_paths = generator.generate_cross_workflow_paths(call_graph, context)

        # Reference mode should generate 2 paths (parent has 1 decision = 2^1 = 2 paths)
        assert len(mw_paths) == 2
        for mw_path in mw_paths:
            assert mw_path.workflows == ["ParentWorkflow"]
            assert "ChildWorkflow" in mw_path.steps  # Child appears as atomic step
            assert mw_path.workflow_transitions == []  # No transitions in reference mode
            assert mw_path.total_decisions == 1  # Only parent decision counted

    def test_reference_mode_no_path_explosion(
        self, parent_with_multiple_decisions, child_with_multiple_decisions
    ):
        """Reference mode with high-decision workflows (32 × 32) has no path explosion."""
        call_graph = WorkflowCallGraph(
            root_workflow=parent_with_multiple_decisions,
            child_workflows={"ChildWorkflow": child_with_multiple_decisions},
            call_relationships=[("ParentWorkflow", "ChildWorkflow")],
            all_child_calls=parent_with_multiple_decisions.child_workflow_calls,
            total_workflows=2,
        )

        context = GraphBuildingContext(child_workflow_expansion="reference")
        generator = PathPermutationGenerator()
        mw_paths = generator.generate_cross_workflow_paths(call_graph, context)

        # Reference mode should generate 32 paths (only parent, 2^5 = 32)
        # Child's 32 paths are NOT expanded
        assert len(mw_paths) == 32
        for mw_path in mw_paths:
            assert mw_path.workflows == ["ParentWorkflow"]
            assert "ChildWorkflow" in mw_path.steps
            assert mw_path.total_decisions == 5  # Only parent decisions


class TestInlineMode:
    """Tests for inline mode (full path expansion)."""

    def test_inline_mode_linear_workflows(self, linear_parent_metadata, linear_child_metadata):
        """Inline mode with linear parent and child generates 1 end-to-end path."""
        call_graph = WorkflowCallGraph(
            root_workflow=linear_parent_metadata,
            child_workflows={"ChildWorkflow": linear_child_metadata},
            call_relationships=[("ParentWorkflow", "ChildWorkflow")],
            all_child_calls=linear_parent_metadata.child_workflow_calls,
            total_workflows=2,
        )

        context = GraphBuildingContext(child_workflow_expansion="inline")
        generator = PathPermutationGenerator()
        mw_paths = generator.generate_cross_workflow_paths(call_graph, context)

        # Inline mode should generate 1 end-to-end path (1 × 1 = 1)
        assert len(mw_paths) == 1
        mw_path = mw_paths[0]
        assert mw_path.path_id == "mwpath_0"
        assert mw_path.workflows == ["ParentWorkflow", "ChildWorkflow"]
        # Child workflow steps injected between parent steps
        assert "ChildActivity1" in mw_path.steps
        assert "ChildActivity2" in mw_path.steps
        assert "ParentActivity1" in mw_path.steps
        assert "ParentActivity2" in mw_path.steps
        # Workflow transitions recorded
        assert len(mw_path.workflow_transitions) == 2  # Parent→Child, Child→Parent
        assert mw_path.total_decisions == 0

    def test_inline_mode_path_expansion(
        self,
        parent_with_decision_metadata,
        child_with_decision_metadata,
    ):
        """Inline mode expands parent (2 paths) × child (2 paths) = 4 end-to-end paths."""
        call_graph = WorkflowCallGraph(
            root_workflow=parent_with_decision_metadata,
            child_workflows={"ChildWorkflow": child_with_decision_metadata},
            call_relationships=[("ParentWorkflow", "ChildWorkflow")],
            all_child_calls=parent_with_decision_metadata.child_workflow_calls,
            total_workflows=2,
        )

        context = GraphBuildingContext(child_workflow_expansion="inline")
        generator = PathPermutationGenerator()
        mw_paths = generator.generate_cross_workflow_paths(call_graph, context)

        # Inline mode should generate 4 paths (2 × 2 = 4)
        assert len(mw_paths) == 4
        for mw_path in mw_paths:
            assert mw_path.workflows == ["ParentWorkflow", "ChildWorkflow"]
            assert mw_path.total_decisions == 2  # 1 parent + 1 child
            assert len(mw_path.workflow_transitions) == 2  # Parent→Child, Child→Parent

    def test_inline_mode_workflow_transitions(self, linear_parent_metadata, linear_child_metadata):
        """Inline mode records workflow transitions at correct step indices."""
        call_graph = WorkflowCallGraph(
            root_workflow=linear_parent_metadata,
            child_workflows={"ChildWorkflow": linear_child_metadata},
            call_relationships=[("ParentWorkflow", "ChildWorkflow")],
            all_child_calls=linear_parent_metadata.child_workflow_calls,
            total_workflows=2,
        )

        context = GraphBuildingContext(child_workflow_expansion="inline")
        generator = PathPermutationGenerator()
        mw_paths = generator.generate_cross_workflow_paths(call_graph, context)

        mw_path = mw_paths[0]
        transitions = mw_path.workflow_transitions

        # Should have 2 transitions: Parent→Child, Child→Parent
        assert len(transitions) == 2
        assert transitions[0][1] == "ParentWorkflow"
        assert transitions[0][2] == "ChildWorkflow"
        assert transitions[1][1] == "ChildWorkflow"
        assert transitions[1][2] == "ParentWorkflow"

    def test_inline_mode_path_explosion_error(
        self, parent_with_multiple_decisions, child_with_multiple_decisions
    ):
        """Inline mode raises error when 32 × 32 = 1024 paths exceeds max_paths."""
        call_graph = WorkflowCallGraph(
            root_workflow=parent_with_multiple_decisions,
            child_workflows={"ChildWorkflow": child_with_multiple_decisions},
            call_relationships=[("ParentWorkflow", "ChildWorkflow")],
            all_child_calls=parent_with_multiple_decisions.child_workflow_calls,
            total_workflows=2,
        )

        # Set max_paths to 1023 so that 32 × 32 = 1024 exceeds the limit
        context = GraphBuildingContext(child_workflow_expansion="inline", max_paths=1023)
        generator = PathPermutationGenerator()

        # Should raise error because 32 × 32 = 1024 paths exceeds limit of 1023
        with pytest.raises(GraphGenerationError) as exc_info:
            generator.generate_cross_workflow_paths(call_graph, context)

        error_msg = str(exc_info.value)
        assert "Cross-workflow path explosion" in error_msg
        assert "1024" in error_msg  # Total paths
        assert "ParentWorkflow" in error_msg or "Parent" in error_msg

    def test_inline_mode_no_children(self, linear_parent_metadata):
        """Inline mode with no child workflows behaves like reference mode."""
        # Create call graph with no children
        parent_no_children = WorkflowMetadata(
            workflow_class="ParentWorkflow",
            workflow_run_method="run",
            activities=[Activity("Activity1", 10)],
            decision_points=[],
            signal_points=[],
            source_file=Path("parent.py"),
            total_paths=1,
            child_workflow_calls=[],  # No children
        )

        call_graph = WorkflowCallGraph(
            root_workflow=parent_no_children,
            child_workflows={},
            call_relationships=[],
            all_child_calls=[],
            total_workflows=1,
        )

        context = GraphBuildingContext(child_workflow_expansion="inline")
        generator = PathPermutationGenerator()
        mw_paths = generator.generate_cross_workflow_paths(call_graph, context)

        # Should generate 1 path, same as reference mode
        assert len(mw_paths) == 1
        assert mw_paths[0].workflows == ["ParentWorkflow"]
        assert mw_paths[0].workflow_transitions == []


class TestSubgraphMode:
    """Tests for subgraph mode (Mermaid subgraph rendering)."""

    def test_subgraph_mode_generates_reference_paths(
        self,
        linear_parent_metadata,
        linear_child_metadata,
    ):
        """Subgraph mode generates same paths as reference mode."""
        call_graph = WorkflowCallGraph(
            root_workflow=linear_parent_metadata,
            child_workflows={"ChildWorkflow": linear_child_metadata},
            call_relationships=[("ParentWorkflow", "ChildWorkflow")],
            all_child_calls=linear_parent_metadata.child_workflow_calls,
            total_workflows=2,
        )

        context_reference = GraphBuildingContext(child_workflow_expansion="reference")
        context_subgraph = GraphBuildingContext(child_workflow_expansion="subgraph")
        generator = PathPermutationGenerator()

        mw_paths_reference = generator.generate_cross_workflow_paths(call_graph, context_reference)
        mw_paths_subgraph = generator.generate_cross_workflow_paths(call_graph, context_subgraph)

        # Subgraph mode should generate same paths as reference mode
        assert len(mw_paths_subgraph) == len(mw_paths_reference)
        assert mw_paths_subgraph[0].steps == mw_paths_reference[0].steps
        assert mw_paths_subgraph[0].workflows == mw_paths_reference[0].workflows


class TestContextFieldValidation:
    """Tests for GraphBuildingContext.child_workflow_expansion field."""

    def test_default_child_workflow_expansion_is_reference(self):
        """Default child_workflow_expansion should be 'reference'."""
        context = GraphBuildingContext()
        assert context.child_workflow_expansion == "reference"

    def test_child_workflow_expansion_accepts_valid_modes(self):
        """child_workflow_expansion should accept 'reference', 'inline', 'subgraph'."""
        context_ref = GraphBuildingContext(child_workflow_expansion="reference")
        context_inline = GraphBuildingContext(child_workflow_expansion="inline")
        context_subgraph = GraphBuildingContext(child_workflow_expansion="subgraph")

        assert context_ref.child_workflow_expansion == "reference"
        assert context_inline.child_workflow_expansion == "inline"
        assert context_subgraph.child_workflow_expansion == "subgraph"

    def test_invalid_child_workflow_expansion_raises_error(self):
        """Invalid child_workflow_expansion mode should raise error during path generation."""
        # Create metadata with invalid mode (mypy won't catch this at runtime)
        linear_parent = WorkflowMetadata(
            workflow_class="ParentWorkflow",
            workflow_run_method="run",
            activities=[Activity("Activity1", 10)],
            decision_points=[],
            signal_points=[],
            source_file=Path("parent.py"),
            total_paths=1,
            child_workflow_calls=[],
        )

        call_graph = WorkflowCallGraph(
            root_workflow=linear_parent,
            child_workflows={},
            call_relationships=[],
            all_child_calls=[],
            total_workflows=1,
        )

        # Use object.__setattr__ to bypass frozen dataclass for testing
        context = GraphBuildingContext()
        object.__setattr__(context, "child_workflow_expansion", "invalid_mode")

        generator = PathPermutationGenerator()
        with pytest.raises(ValueError) as exc_info:
            generator.generate_cross_workflow_paths(call_graph, context)

        assert "Invalid child_workflow_expansion mode" in str(exc_info.value)


class TestMultiWorkflowPathDataModel:
    """Tests for MultiWorkflowPath data model."""

    def test_multiworkflow_path_creation(self):
        """MultiWorkflowPath should be created with all required fields."""
        mw_path = MultiWorkflowPath(
            path_id="mwpath_0",
            workflows=["ParentWorkflow", "ChildWorkflow"],
            steps=["Activity1", "ChildActivity", "Activity2"],
            workflow_transitions=[(1, "ParentWorkflow", "ChildWorkflow")],
            total_decisions=2,
        )

        assert mw_path.path_id == "mwpath_0"
        assert mw_path.workflows == ["ParentWorkflow", "ChildWorkflow"]
        assert len(mw_path.steps) == 3
        assert len(mw_path.workflow_transitions) == 1
        assert mw_path.total_decisions == 2

    def test_multiworkflow_path_is_frozen(self):
        """MultiWorkflowPath should be immutable (frozen dataclass)."""
        mw_path = MultiWorkflowPath(
            path_id="mwpath_0",
            workflows=["ParentWorkflow"],
            steps=["Activity1"],
            workflow_transitions=[],
            total_decisions=0,
        )

        with pytest.raises(AttributeError):
            mw_path.path_id = "mwpath_1"  # Should raise error
