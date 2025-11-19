"""Unit tests for WorkflowCallGraphAnalyzer (Story 6.3)."""

import pytest
from pathlib import Path

from temporalio_graphs.call_graph_analyzer import WorkflowCallGraphAnalyzer
from temporalio_graphs.context import GraphBuildingContext
from temporalio_graphs.exceptions import (
    ChildWorkflowNotFoundError,
    CircularWorkflowError,
)


class TestWorkflowCallGraphAnalyzer:
    """Test WorkflowCallGraphAnalyzer functionality."""

    def test_simple_parent_child_analysis(self) -> None:
        """Test simple parent-child analysis (1 parent, 1 child) - AC1, AC6."""
        context = GraphBuildingContext(max_expansion_depth=2)
        analyzer = WorkflowCallGraphAnalyzer(context)

        parent_file = Path("tests/fixtures/parent_child_workflows/simple_parent.py")
        call_graph = analyzer.analyze(parent_file)

        # Verify root workflow
        assert call_graph.root_workflow.workflow_class == "SimpleParentWorkflow"
        assert call_graph.total_workflows == 2

        # Verify child workflows discovered (AC1)
        assert "SimpleChildWorkflow" in call_graph.child_workflows
        child_metadata = call_graph.child_workflows["SimpleChildWorkflow"]
        assert child_metadata.workflow_class == "SimpleChildWorkflow"

        # Verify call relationships (AC5)
        assert ("SimpleParentWorkflow", "SimpleChildWorkflow") in call_graph.call_relationships

        # Verify separate WorkflowMetadata created for each (AC6)
        assert call_graph.root_workflow is not child_metadata
        assert call_graph.root_workflow.source_file != child_metadata.source_file

    def test_multiple_children_analysis(self) -> None:
        """Test multiple children (1 parent, 2 different children) - AC1."""
        context = GraphBuildingContext(max_expansion_depth=2)
        analyzer = WorkflowCallGraphAnalyzer(context)

        parent_file = Path("tests/fixtures/parent_child_workflows/multi_child_parent.py")
        call_graph = analyzer.analyze(parent_file)

        # Verify both children discovered
        assert call_graph.total_workflows == 3
        assert "ChildWorkflowA" in call_graph.child_workflows
        assert "ChildWorkflowB" in call_graph.child_workflows

        # Verify call relationships
        assert ("MultiChildParentWorkflow", "ChildWorkflowA") in call_graph.call_relationships
        assert ("MultiChildParentWorkflow", "ChildWorkflowB") in call_graph.call_relationships

    def test_nested_children_analysis(self) -> None:
        """Test nested children (parent → child → grandchild, depth=2) - AC1, AC4."""
        context = GraphBuildingContext(max_expansion_depth=2)
        analyzer = WorkflowCallGraphAnalyzer(context)

        parent_file = Path("tests/fixtures/parent_child_workflows/nested_grandchild.py")
        call_graph = analyzer.analyze(parent_file)

        # Verify all three levels discovered (depth 2 = parent + child + grandchild)
        assert call_graph.total_workflows == 3
        assert "ChildWithGrandchildWorkflow" in call_graph.child_workflows
        assert "GrandchildWorkflow" in call_graph.child_workflows

        # Verify nested call relationships
        assert ("ParentWithGrandchildWorkflow", "ChildWithGrandchildWorkflow") in call_graph.call_relationships
        assert ("ChildWithGrandchildWorkflow", "GrandchildWorkflow") in call_graph.call_relationships

    def test_circular_reference_detection(self) -> None:
        """Test circular reference detection (parent → child → parent) - AC3."""
        # Use depth=3 to allow circular check to happen before depth limit
        context = GraphBuildingContext(max_expansion_depth=3)
        analyzer = WorkflowCallGraphAnalyzer(context)

        parent_file = Path("tests/fixtures/parent_child_workflows/circular_a.py")

        # Should raise CircularWorkflowError with workflow chain
        with pytest.raises(CircularWorkflowError) as exc_info:
            analyzer.analyze(parent_file)

        # Verify workflow chain is included in error
        error = exc_info.value
        assert "CircularWorkflowA" in error.workflow_chain
        assert "CircularWorkflowB" in error.workflow_chain
        # Last element should be the one creating the cycle
        assert error.workflow_chain[-1] == "CircularWorkflowA"

    def test_depth_limit_enforcement(self) -> None:
        """Test depth limit enforcement (reject workflows at depth 3) - AC4."""
        # Set max_expansion_depth to 1 (only root + direct children, no grandchildren)
        context = GraphBuildingContext(max_expansion_depth=1)
        analyzer = WorkflowCallGraphAnalyzer(context)

        parent_file = Path("tests/fixtures/parent_child_workflows/nested_grandchild.py")
        call_graph = analyzer.analyze(parent_file)

        # With depth=1, should only analyze parent + child (no grandchild)
        assert call_graph.total_workflows == 2  # Parent + ChildWithGrandchildWorkflow
        assert "ChildWithGrandchildWorkflow" in call_graph.child_workflows
        # Grandchild should NOT be discovered due to depth limit
        assert "GrandchildWorkflow" not in call_graph.child_workflows

    def test_child_workflow_not_found_error(self) -> None:
        """Test child workflow not found error with clear message - AC8."""
        context = GraphBuildingContext(max_expansion_depth=2)
        analyzer = WorkflowCallGraphAnalyzer(context)

        # Create a temporary parent workflow that references non-existent child
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
from temporalio import workflow

@workflow.defn
class TestParent:
    @workflow.run
    async def run(self):
        await workflow.execute_child_workflow("NonExistentWorkflow")
""")
            temp_file = Path(f.name)

        try:
            with pytest.raises(ChildWorkflowNotFoundError) as exc_info:
                analyzer.analyze(temp_file)

            # Verify error message includes workflow name and search paths
            error = exc_info.value
            assert error.workflow_name == "NonExistentWorkflow"
            assert len(error.search_paths) > 0
            assert "could not be found" in str(error).lower()
            assert "searched in:" in str(error).lower()
        finally:
            temp_file.unlink()

    def test_import_tracking_resolution(self) -> None:
        """Test import tracking resolution (child imported from another module) - AC2."""
        context = GraphBuildingContext(max_expansion_depth=2)
        analyzer = WorkflowCallGraphAnalyzer(context)

        parent_file = Path("tests/fixtures/parent_child_workflows/simple_parent.py")
        call_graph = analyzer.analyze(parent_file)

        # SimpleParentWorkflow imports SimpleChildWorkflow from another file
        # Verify child was resolved via import tracking
        assert "SimpleChildWorkflow" in call_graph.child_workflows
        child_metadata = call_graph.child_workflows["SimpleChildWorkflow"]

        # Verify child has correct source file (different from parent)
        assert child_metadata.source_file.name == "simple_child.py"
        assert call_graph.root_workflow.source_file.name == "simple_parent.py"

    def test_filesystem_search_resolution(self) -> None:
        """Test filesystem search resolution (child in different directory) - AC2."""
        context = GraphBuildingContext(max_expansion_depth=2)
        analyzer = WorkflowCallGraphAnalyzer(context)

        # Test with explicit search paths
        parent_file = Path("tests/fixtures/parent_child_workflows/simple_parent.py")
        search_paths = [
            Path("tests/fixtures/parent_child_workflows"),
            Path("tests/fixtures"),
        ]

        call_graph = analyzer.analyze(parent_file, search_paths=search_paths)

        # Should find child via filesystem search in search_paths
        assert "SimpleChildWorkflow" in call_graph.child_workflows

    def test_search_paths_default_to_parent_directory(self) -> None:
        """Test search paths defaulting to parent directory - AC7."""
        context = GraphBuildingContext(max_expansion_depth=2)
        analyzer = WorkflowCallGraphAnalyzer(context)

        parent_file = Path("tests/fixtures/parent_child_workflows/simple_parent.py")

        # Call analyze without search_paths parameter
        call_graph = analyzer.analyze(parent_file, search_paths=None)

        # Should still find child in same directory as parent (default search path)
        assert "SimpleChildWorkflow" in call_graph.child_workflows

    def test_same_file_parent_child(self) -> None:
        """Test parent and child in same file (Priority 1 resolution) - AC2."""
        context = GraphBuildingContext(max_expansion_depth=2)
        analyzer = WorkflowCallGraphAnalyzer(context)

        parent_file = Path("tests/fixtures/parent_child_workflows/same_file_parent_child.py")
        call_graph = analyzer.analyze(parent_file)

        # Verify child discovered in same file
        assert "SameFileChildWorkflow" in call_graph.child_workflows
        child_metadata = call_graph.child_workflows["SameFileChildWorkflow"]

        # Both should have same source file
        assert child_metadata.source_file == call_graph.root_workflow.source_file

    def test_workflow_call_graph_structure(self) -> None:
        """Test WorkflowCallGraph data model contains all required fields - AC5."""
        context = GraphBuildingContext(max_expansion_depth=2)
        analyzer = WorkflowCallGraphAnalyzer(context)

        parent_file = Path("tests/fixtures/parent_child_workflows/simple_parent.py")
        call_graph = analyzer.analyze(parent_file)

        # Verify all WorkflowCallGraph fields are populated
        assert call_graph.root_workflow is not None
        assert isinstance(call_graph.child_workflows, dict)
        assert isinstance(call_graph.call_relationships, list)
        assert isinstance(call_graph.all_child_calls, list)
        assert isinstance(call_graph.total_workflows, int)

        # Verify all_child_calls contains ChildWorkflowCall objects
        assert len(call_graph.all_child_calls) >= 1
        child_call = call_graph.all_child_calls[0]
        assert child_call.workflow_name == "SimpleChildWorkflow"
        assert child_call.parent_workflow == "SimpleParentWorkflow"

    def test_depth_0_only_analyzes_root(self) -> None:
        """Test depth=0 only analyzes root workflow (no children) - AC4."""
        context = GraphBuildingContext(max_expansion_depth=0)
        analyzer = WorkflowCallGraphAnalyzer(context)

        parent_file = Path("tests/fixtures/parent_child_workflows/simple_parent.py")
        call_graph = analyzer.analyze(parent_file)

        # With depth=0, should only analyze root workflow
        assert call_graph.total_workflows == 1
        assert len(call_graph.child_workflows) == 0
        # Root workflow should still have child_workflow_calls detected
        assert len(call_graph.root_workflow.child_workflow_calls) == 1

    def test_backtracking_allows_shared_children(self) -> None:
        """Test backtracking allows same child from different parents (DAG structure)."""
        # Create a scenario where two parents call the same child
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create shared child
            shared_child = tmpdir_path / "shared_child.py"
            shared_child.write_text("""
from temporalio import workflow

@workflow.defn
class SharedChildWorkflow:
    @workflow.run
    async def run(self):
        return "shared"
""")

            # Create two parent workflows that both call SharedChildWorkflow
            parent = tmpdir_path / "multi_parent.py"
            parent.write_text("""
from temporalio import workflow

@workflow.defn
class ChildA:
    @workflow.run
    async def run(self):
        from shared_child import SharedChildWorkflow
        await workflow.execute_child_workflow(SharedChildWorkflow)
        return "a"

@workflow.defn
class ChildB:
    @workflow.run
    async def run(self):
        from shared_child import SharedChildWorkflow
        await workflow.execute_child_workflow(SharedChildWorkflow)
        return "b"

@workflow.defn
class MultiParent:
    @workflow.run
    async def run(self):
        await workflow.execute_child_workflow(ChildA)
        await workflow.execute_child_workflow(ChildB)
        return "parent"
""")

            context = GraphBuildingContext(max_expansion_depth=2)
            analyzer = WorkflowCallGraphAnalyzer(context)

            call_graph = analyzer.analyze(parent, search_paths=[tmpdir_path])

            # Should discover all workflows without circular error
            assert call_graph.total_workflows >= 3  # MultiParent + ChildA + ChildB

    def test_context_configuration_respected(self) -> None:
        """Test that GraphBuildingContext configuration is passed through."""
        context = GraphBuildingContext(
            max_expansion_depth=1,
            suppress_validation=True,
        )
        analyzer = WorkflowCallGraphAnalyzer(context)

        parent_file = Path("tests/fixtures/parent_child_workflows/nested_grandchild.py")
        call_graph = analyzer.analyze(parent_file)

        # Verify max_expansion_depth=1 is enforced
        assert call_graph.total_workflows == 2  # Parent + child only

    def test_absolute_path_resolution(self) -> None:
        """Test that file paths are resolved to absolute paths (NFR-SEC-Epic6-1)."""
        context = GraphBuildingContext(max_expansion_depth=2)
        analyzer = WorkflowCallGraphAnalyzer(context)

        # Use relative path
        parent_file = Path("tests/fixtures/parent_child_workflows/simple_parent.py")
        call_graph = analyzer.analyze(parent_file)

        # Verify all source files are absolute paths
        assert call_graph.root_workflow.source_file.is_absolute()
        for child_metadata in call_graph.child_workflows.values():
            assert child_metadata.source_file.is_absolute()

    def test_empty_workflow_hierarchy(self) -> None:
        """Test workflow with no child calls returns single workflow."""
        context = GraphBuildingContext(max_expansion_depth=2)
        analyzer = WorkflowCallGraphAnalyzer(context)

        # SimpleChildWorkflow has no child calls
        child_file = Path("tests/fixtures/parent_child_workflows/simple_child.py")
        call_graph = analyzer.analyze(child_file)

        # Should only contain root workflow
        assert call_graph.total_workflows == 1
        assert len(call_graph.child_workflows) == 0
        assert len(call_graph.call_relationships) == 0


class TestWorkflowCallGraphAnalyzerEdgeCases:
    """Test edge cases and error conditions."""

    def test_nonexistent_entry_workflow(self) -> None:
        """Test error when entry workflow file does not exist."""
        context = GraphBuildingContext(max_expansion_depth=2)
        analyzer = WorkflowCallGraphAnalyzer(context)

        nonexistent_file = Path("nonexistent_workflow.py")

        with pytest.raises(Exception):  # Should raise FileNotFoundError or WorkflowParseError
            analyzer.analyze(nonexistent_file)

    def test_malformed_workflow_file(self) -> None:
        """Test error when workflow file has syntax errors."""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("this is not valid python syntax {{{")
            temp_file = Path(f.name)

        try:
            context = GraphBuildingContext(max_expansion_depth=2)
            analyzer = WorkflowCallGraphAnalyzer(context)

            with pytest.raises(Exception):  # Should raise WorkflowParseError
                analyzer.analyze(temp_file)
        finally:
            temp_file.unlink()

    def test_deep_nesting_respects_limit(self) -> None:
        """Test that very deep nesting respects max_expansion_depth limit."""
        context = GraphBuildingContext(max_expansion_depth=1)
        analyzer = WorkflowCallGraphAnalyzer(context)

        parent_file = Path("tests/fixtures/parent_child_workflows/nested_grandchild.py")
        call_graph = analyzer.analyze(parent_file)

        # With depth=1, grandchild should not be analyzed
        assert "GrandchildWorkflow" not in call_graph.child_workflows
        # But child should be analyzed
        assert "ChildWithGrandchildWorkflow" in call_graph.child_workflows


class TestImportResolution:
    """Test import tracking and module resolution."""

    def test_import_map_building(self) -> None:
        """Test that import map correctly extracts imports from parent file."""
        context = GraphBuildingContext(max_expansion_depth=2)
        analyzer = WorkflowCallGraphAnalyzer(context)

        parent_file = Path("tests/fixtures/parent_child_workflows/simple_parent.py")

        # Build import map
        import_map = analyzer._build_import_map(parent_file)

        # Should contain SimpleChildWorkflow import
        assert "SimpleChildWorkflow" in import_map
        assert "parent_child_workflows.simple_child" in import_map["SimpleChildWorkflow"]

    def test_same_file_resolution_priority(self) -> None:
        """Test that same-file resolution has priority over imports."""
        context = GraphBuildingContext(max_expansion_depth=2)
        analyzer = WorkflowCallGraphAnalyzer(context)

        # SameFileParentWorkflow and SameFileChildWorkflow in same file
        parent_file = Path("tests/fixtures/parent_child_workflows/same_file_parent_child.py")

        # Should resolve to same file (Priority 1)
        resolved = analyzer._resolve_child_workflow_file(
            workflow_name="SameFileChildWorkflow",
            parent_file=parent_file,
            search_paths=[parent_file.parent],
        )

        assert resolved == parent_file.resolve()
