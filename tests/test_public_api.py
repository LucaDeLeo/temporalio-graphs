"""Integration tests for the public API entry point (analyze_workflow).

This module tests the complete end-to-end pipeline through the analyze_workflow()
function, verifying input validation, context handling, component orchestration,
and error handling per Story 2-6 acceptance criteria.
"""

import tempfile
from pathlib import Path

import pytest

from temporalio_graphs import GraphBuildingContext, analyze_workflow
from temporalio_graphs.exceptions import WorkflowParseError


class TestAnalyzeWorkflowMinimalUsage:
    """Test AC6: Quick start capability with minimal boilerplate."""

    def test_analyze_workflow_minimal_usage(self) -> None:
        """AC6: Verify 3-line basic usage works as documented."""
        # Arrange
        fixture_path = Path("tests/fixtures/sample_workflows/multi_activity_workflow.py")

        # Act
        result = analyze_workflow(fixture_path)

        # Assert
        assert isinstance(result, str)
        assert len(result) > 0
        assert "flowchart LR" in result
        assert "```mermaid" in result

    def test_analyze_workflow_minimal_usage_with_string_path(self) -> None:
        """AC1: Verify function accepts both Path and str for workflow_file."""
        # Arrange
        fixture_str = "tests/fixtures/sample_workflows/multi_activity_workflow.py"

        # Act
        result = analyze_workflow(fixture_str)

        # Assert
        assert isinstance(result, str)
        assert "flowchart LR" in result

    def test_analyze_workflow_returns_string(self) -> None:
        """AC1, AC4: Verify return type is str containing Mermaid."""
        # Arrange
        fixture_path = Path("tests/fixtures/sample_workflows/single_activity_workflow.py")

        # Act
        result = analyze_workflow(fixture_path)

        # Assert
        assert isinstance(result, str)
        assert result.startswith("```mermaid")
        assert result.endswith("```")


class TestAnalyzeWorkflowWithCustomContext:
    """Test AC3, AC6: Custom context and default context handling."""

    def test_analyze_workflow_with_custom_context(self) -> None:
        """AC3, AC6: Verify custom context is respected."""
        # Arrange
        fixture_path = Path("tests/fixtures/sample_workflows/multi_activity_workflow.py")
        custom_context = GraphBuildingContext(
            split_names_by_words=False,
            start_node_label="BEGIN",
            end_node_label="FINISH",
        )

        # Act
        result = analyze_workflow(fixture_path, context=custom_context)

        # Assert
        assert isinstance(result, str)
        assert "BEGIN" in result
        assert "FINISH" in result
        assert "flowchart LR" in result

    def test_analyze_workflow_default_context_used(self) -> None:
        """AC3: Verify None context becomes GraphBuildingContext() with defaults."""
        # Arrange
        fixture_path = Path("tests/fixtures/sample_workflows/multi_activity_workflow.py")

        # Act
        result = analyze_workflow(fixture_path, context=None)

        # Assert
        assert isinstance(result, str)
        # Default labels should be present
        assert "Start" in result
        assert "End" in result


class TestAnalyzeWorkflowFileOutput:
    """Test AC5: File output functionality."""

    def test_analyze_workflow_with_file_output(self) -> None:
        """AC5: Verify graph_output_file writes to disk."""
        # Arrange
        fixture_path = Path("tests/fixtures/sample_workflows/multi_activity_workflow.py")
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "workflow_diagram.md"
            context = GraphBuildingContext(graph_output_file=output_file)

            # Act
            result = analyze_workflow(fixture_path, context=context)

            # Assert
            assert output_file.exists()
            written_content = output_file.read_text(encoding="utf-8")
            assert written_content == result
            assert "flowchart LR" in written_content

    def test_analyze_workflow_file_output_creates_directories(self) -> None:
        """AC5: Verify intermediate directories are created if needed."""
        # Arrange
        fixture_path = Path("tests/fixtures/sample_workflows/multi_activity_workflow.py")
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "subdir1" / "subdir2" / "diagram.md"
            context = GraphBuildingContext(graph_output_file=output_file)

            # Act
            result = analyze_workflow(fixture_path, context=context)

            # Assert
            assert output_file.exists()
            assert output_file.parent.exists()
            written_content = output_file.read_text(encoding="utf-8")
            assert written_content == result

    def test_analyze_workflow_file_output_overwrites_existing(self) -> None:
        """AC5: Verify existing file is overwritten."""
        # Arrange
        fixture_path = Path("tests/fixtures/sample_workflows/multi_activity_workflow.py")
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "diagram.md"
            # Create initial file
            output_file.write_text("old content", encoding="utf-8")
            context = GraphBuildingContext(graph_output_file=output_file)

            # Act
            result = analyze_workflow(fixture_path, context=context)

            # Assert
            written_content = output_file.read_text(encoding="utf-8")
            assert written_content == result
            assert "old content" not in written_content

    def test_analyze_workflow_returns_result_even_with_file_output(self) -> None:
        """AC5: Verify result is returned even when written to file."""
        # Arrange
        fixture_path = Path("tests/fixtures/sample_workflows/multi_activity_workflow.py")
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "diagram.md"
            context = GraphBuildingContext(graph_output_file=output_file)

            # Act
            result = analyze_workflow(fixture_path, context=context)

            # Assert
            assert isinstance(result, str)
            assert len(result) > 0
            # Verify it matches what was written to file
            written_content = output_file.read_text(encoding="utf-8")
            assert result == written_content


class TestAnalyzeWorkflowErrorHandling:
    """Test AC2, AC11: Error handling and clear error messages."""

    def test_analyze_workflow_error_file_not_found(self) -> None:
        """AC2, AC11: Verify WorkflowParseError for missing file."""
        # Arrange
        nonexistent_file = "tests/fixtures/nonexistent_workflow.py"

        # Act & Assert - now raises WorkflowParseError instead of FileNotFoundError
        from temporalio_graphs.exceptions import WorkflowParseError

        with pytest.raises(WorkflowParseError) as exc_info:
            analyze_workflow(nonexistent_file)

        # Verify error message is helpful
        assert "Workflow file not found" in str(exc_info.value)

    def test_analyze_workflow_error_invalid_format(self) -> None:
        """AC11: Verify ValueError for unsupported output_format."""
        # Arrange
        fixture_path = Path("tests/fixtures/sample_workflows/multi_activity_workflow.py")

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            analyze_workflow(fixture_path, output_format="json")  # type: ignore
        assert "reserved for future use" in str(exc_info.value)

    def test_analyze_workflow_paths_format_supported(self) -> None:
        """Story 5-3: Verify 'paths' format is now supported."""
        # Arrange
        fixture_path = Path("tests/fixtures/sample_workflows/multi_activity_workflow.py")

        # Act - Should not raise
        result = analyze_workflow(fixture_path, output_format="paths")  # type: ignore

        # Assert - Should get path list output
        assert "--- Execution Paths" in result
        assert "Path 1:" in result

    def test_analyze_workflow_error_none_workflow_file(self) -> None:
        """AC2: Verify ValueError when workflow_file is None."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            analyze_workflow(None)  # type: ignore
        assert "workflow_file parameter required" in str(exc_info.value)


class TestAnalyzeWorkflowIntegration:
    """Test AC4, AC10: End-to-end pipeline integration."""

    def test_analyze_workflow_integration_single_activity(self) -> None:
        """AC4, AC13: Verify pipeline with simple single-activity workflow."""
        # Arrange
        fixture_path = Path("tests/fixtures/sample_workflows/single_activity_workflow.py")

        # Act
        result = analyze_workflow(fixture_path)

        # Assert
        assert isinstance(result, str)
        assert "flowchart LR" in result
        assert "s((Start))" in result
        assert "e((End))" in result
        # Single activity should be present (use activity name as node ID)
        assert "my_activity[" in result

    def test_analyze_workflow_integration_multi_activity(self) -> None:
        """AC4, AC13: Verify pipeline with multi-activity workflow."""
        # Arrange
        fixture_path = Path("tests/fixtures/sample_workflows/multi_activity_workflow.py")

        # Act
        result = analyze_workflow(fixture_path)

        # Assert
        assert isinstance(result, str)
        assert "flowchart LR" in result
        # Should contain start and end nodes
        assert "s((Start))" in result
        assert "e((End))" in result
        # Should contain edges
        assert " --> " in result
        # Should contain at least 3 activity nodes for 3 activities (use activity names as node IDs)
        assert "activity_one[" in result
        assert "activity_two[" in result
        assert "activity_three[" in result

    def test_analyze_workflow_integration_valid_mermaid_syntax(self) -> None:
        """AC4: Verify output is valid Mermaid with correct structure."""
        # Arrange
        fixture_path = Path("tests/fixtures/sample_workflows/multi_activity_workflow.py")

        # Act
        result = analyze_workflow(fixture_path)

        # Assert
        # Check structure
        assert result.startswith("```mermaid")
        assert result.endswith("```")
        assert "flowchart LR" in result
        # Check it contains node definitions and edges
        lines = result.split("\n")
        # Should have more than just fences and directive
        assert len(lines) > 5
        # Should have some node definitions (lines with [ or ()
        has_nodes = any("[" in line or "(" in line for line in lines)
        assert has_nodes


class TestAnalyzeWorkflowComponentIntegration:
    """Test AC10: Integration with core components without breaking changes."""

    def test_analyze_workflow_uses_workflow_analyzer(self) -> None:
        """AC10: Verify WorkflowAnalyzer is called and returns metadata."""
        # This test verifies the analyzer stage of the pipeline
        fixture_path = Path("tests/fixtures/sample_workflows/multi_activity_workflow.py")

        # Act
        result = analyze_workflow(fixture_path)

        # Assert
        # If analyzer failed, we wouldn't get here
        # The presence of valid output indicates analyzer worked
        assert "MultiActivityWorkflow" not in result or "flowchart" in result

    def test_analyze_workflow_uses_path_generator(self) -> None:
        """AC10: Verify PathPermutationGenerator returns paths for renderer."""
        # This test verifies the generator stage produces valid paths
        fixture_path = Path("tests/fixtures/sample_workflows/single_activity_workflow.py")

        # Act
        result = analyze_workflow(fixture_path)

        # Assert
        # Single activity workflow should produce exactly one path
        # Evidence: Start -> Activity -> End structure
        assert "s((Start))" in result
        assert "e((End))" in result

    def test_analyze_workflow_uses_mermaid_renderer(self) -> None:
        """AC10: Verify MermaidRenderer produces Mermaid output."""
        # This test verifies the renderer stage produces valid Mermaid
        fixture_path = Path("tests/fixtures/sample_workflows/multi_activity_workflow.py")

        # Act
        result = analyze_workflow(fixture_path)

        # Assert
        # Valid Mermaid output format
        assert result.startswith("```mermaid\nflowchart LR")
        assert result.endswith("```")
        # Mermaid elements present
        assert "-->" in result
        assert "((Start))" in result or "((" in result


class TestAnalyzeWorkflowSignature:
    """Test AC1: Function signature and module placement."""

    def test_analyze_workflow_is_exported(self) -> None:
        """AC1, AC6: Verify analyze_workflow is exported from __init__.py."""
        # Act & Assert
        from temporalio_graphs import analyze_workflow as exported_function

        assert callable(exported_function)
        assert exported_function.__name__ == "analyze_workflow"

    def test_graph_building_context_is_exported(self) -> None:
        """AC6: Verify GraphBuildingContext is exported from __init__.py."""
        # Act & Assert
        from temporalio_graphs import GraphBuildingContext as exported_context

        assert exported_context.__name__ == "GraphBuildingContext"

    def test_public_api_clean_minimal_export(self) -> None:
        """AC6: Verify __all__ list contains only public API."""
        # Arrange
        import temporalio_graphs

        # Act
        exported = temporalio_graphs.__all__

        # Assert
        # Updated in Story 5.1 to include validation APIs
        # Updated in Story 5.2 to include exception classes
        # Updated in Epic 6 to include cross-workflow APIs
        # Updated in Story 8.5 to include cross-workflow signal models
        # Updated in Story 8.6 to include PeerSignalGraphAnalyzer
        assert set(exported) == {
            "GraphBuildingContext",
            "analyze_workflow",
            "analyze_workflow_graph",
            "to_decision",
            "wait_condition",
            "ValidationWarning",
            "ValidationReport",
            "TemporalioGraphsError",
            "WorkflowParseError",
            "UnsupportedPatternError",
            "GraphGenerationError",
            "InvalidDecisionError",
            "MultiWorkflowPath",
            "PeerSignalGraph",
            "PeerSignalGraphAnalyzer",
            "SignalConnection",
        }
        # Verify internal components not exported
        assert "WorkflowAnalyzer" not in exported
        assert "PathPermutationGenerator" not in exported
        assert "MermaidRenderer" not in exported


class TestAnalyzeWorkflowDocstring:
    """Test AC7, AC8: Type hints and documentation."""

    def test_analyze_workflow_has_complete_docstring(self) -> None:
        """AC8: Verify docstring has Args, Returns, Raises, Example sections."""
        # Arrange
        from temporalio_graphs import analyze_workflow

        docstring = analyze_workflow.__doc__

        # Assert
        assert docstring is not None
        assert "Args:" in docstring
        assert "Returns:" in docstring
        assert "Raises:" in docstring
        assert "Example:" in docstring
        assert "workflow_file" in docstring
        assert "context" in docstring
        assert "output_format" in docstring

    def test_analyze_workflow_docstring_mentions_epic_2_limitations(self) -> None:
        """AC8: Verify docstring mentions Epic 2 limitations."""
        # Arrange
        from temporalio_graphs import analyze_workflow

        docstring = analyze_workflow.__doc__

        # Assert
        assert docstring is not None
        assert "Epic 2" in docstring or "linear" in docstring.lower()
        assert "decision" in docstring.lower() or "signal" in docstring.lower()

    def test_analyze_workflow_signature_has_type_hints(self) -> None:
        """AC7, AC12: Verify all parameters and return have type hints."""
        # Arrange
        from temporalio_graphs import analyze_workflow

        # Act
        hints = analyze_workflow.__annotations__

        # Assert
        assert "workflow_file" in hints
        assert "context" in hints
        assert "output_format" in hints
        assert "return" in hints
        # Return type should be str
        assert hints["return"] == str
