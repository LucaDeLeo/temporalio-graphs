"""Integration tests for error handling in workflow analysis."""

import tempfile
from pathlib import Path

import pytest

from temporalio_graphs import analyze_workflow
from temporalio_graphs.context import GraphBuildingContext
from temporalio_graphs.exceptions import (
    GraphGenerationError,
    TemporalioGraphsError,
    WorkflowParseError,
)


class TestFileValidationErrors:
    """Tests for file validation error handling."""

    def test_file_not_found_error(self) -> None:
        """Test that non-existent file raises WorkflowParseError with helpful message."""
        non_existent_path = Path("/path/that/does/not/exist/workflow.py")

        with pytest.raises(WorkflowParseError) as exc_info:
            analyze_workflow(non_existent_path)

        error = exc_info.value
        assert error.file_path == non_existent_path
        assert error.line == 0
        assert "Workflow file not found" in error.message
        assert "Suggestion:" in str(error)
        assert "Verify file path is correct" in error.suggestion

    def test_file_not_found_can_be_caught_with_base(self) -> None:
        """Test that WorkflowParseError can be caught with TemporalioGraphsError."""
        non_existent_path = Path("/path/that/does/not/exist/workflow.py")

        try:
            analyze_workflow(non_existent_path)
        except TemporalioGraphsError as e:
            assert isinstance(e, WorkflowParseError)
            assert "Suggestion:" in str(e)
        else:
            pytest.fail("Expected TemporalioGraphsError to be raised")


class TestSyntaxErrors:
    """Tests for Python syntax error handling."""

    def test_syntax_error_raises_workflow_parse_error(self) -> None:
        """Test that invalid Python syntax raises WorkflowParseError with line number."""
        # Create a temporary file with syntax error
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""
from temporalio import workflow

@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self) -> str:
        if True  # Missing colon - syntax error
            return "test"
""")
            temp_path = Path(f.name)

        try:
            with pytest.raises(WorkflowParseError) as exc_info:
                analyze_workflow(temp_path)

            error = exc_info.value
            # Resolve both paths to handle macOS /private/var vs /var symlink
            assert error.file_path.resolve() == temp_path.resolve()
            assert error.line > 0  # Should have line number from SyntaxError
            assert "Invalid Python syntax" in error.message
            assert "Suggestion:" in str(error)
            assert "Check workflow file for syntax errors" in error.suggestion

            # Verify exception chaining
            assert error.__cause__ is not None
            assert isinstance(error.__cause__, SyntaxError)
        finally:
            temp_path.unlink()


class TestMissingDecoratorErrors:
    """Tests for missing decorator error handling."""

    def test_missing_workflow_defn_decorator(self) -> None:
        """Test that missing @workflow.defn raises WorkflowParseError."""
        # Create a temporary file without @workflow.defn
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""
from temporalio import workflow

class MyWorkflow:
    @workflow.run
    async def run(self) -> str:
        return "test"
""")
            temp_path = Path(f.name)

        try:
            with pytest.raises(WorkflowParseError) as exc_info:
                analyze_workflow(temp_path)

            error = exc_info.value
            # Resolve both paths to handle macOS /private/var vs /var symlink
            assert error.file_path.resolve() == temp_path.resolve()
            assert error.line == 0
            assert "Missing @workflow.defn decorator" in error.message
            assert "Suggestion:" in str(error)
            assert "Add @workflow.defn decorator to workflow class" in error.suggestion
        finally:
            temp_path.unlink()

    def test_missing_workflow_run_method(self) -> None:
        """Test that missing @workflow.run raises WorkflowParseError."""
        # Create a temporary file without @workflow.run
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""
from temporalio import workflow

@workflow.defn
class MyWorkflow:
    async def run(self) -> str:
        return "test"
""")
            temp_path = Path(f.name)

        try:
            with pytest.raises(WorkflowParseError) as exc_info:
                analyze_workflow(temp_path)

            error = exc_info.value
            # Resolve both paths to handle macOS /private/var vs /var symlink
            assert error.file_path.resolve() == temp_path.resolve()
            # Line may be 0 or the class line number
            assert "Missing @workflow.run method" in error.message
            assert "Suggestion:" in str(error)
            assert "Add @workflow.run method to workflow class" in error.suggestion
        finally:
            temp_path.unlink()


class TestPathExplosionError:
    """Tests for path explosion error handling."""

    def test_too_many_decision_points_error(self) -> None:
        """Test that exceeding max_decision_points raises GraphGenerationError."""
        # Create a workflow with many decision points (exceeds default limit of 10)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            # Generate 11 decision points (exceeds default limit of 10)
            decision_code = "\n".join(
                [
                    f"        d{i} = await to_decision(True, 'Decision{i}')"
                    for i in range(11)
                ]
            )
            f.write(f"""
from temporalio import workflow
from temporalio_graphs import to_decision

@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self) -> str:
{decision_code}
        return "test"
""")
            temp_path = Path(f.name)

        try:
            # Use default context (max_decision_points=10)
            with pytest.raises(GraphGenerationError) as exc_info:
                analyze_workflow(temp_path)

            error = exc_info.value
            assert "Too many branch points" in error.reason
            assert "Suggestion:" in str(error)
            assert error.context is not None
            assert "decision_count" in error.context or "paths" in error.context
        finally:
            temp_path.unlink()

    def test_path_explosion_error_can_be_caught_with_base(self) -> None:
        """Test that GraphGenerationError can be caught with TemporalioGraphsError."""
        # Create a workflow with many decision points
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            decision_code = "\n".join(
                [
                    f"        d{i} = await to_decision(True, 'Decision{i}')"
                    for i in range(11)
                ]
            )
            f.write(f"""
from temporalio import workflow
from temporalio_graphs import to_decision

@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self) -> str:
{decision_code}
        return "test"
""")
            temp_path = Path(f.name)

        try:
            try:
                analyze_workflow(temp_path)
            except TemporalioGraphsError as e:
                assert isinstance(e, GraphGenerationError)
                assert "Suggestion:" in str(e)
            else:
                pytest.fail("Expected TemporalioGraphsError to be raised")
        finally:
            temp_path.unlink()


class TestErrorMessageQuality:
    """Tests for error message quality and helpfulness."""

    def test_all_errors_contain_suggestion(self) -> None:
        """Test that all error messages contain 'Suggestion:' keyword."""
        # Test file not found
        with pytest.raises(WorkflowParseError) as exc_info:
            analyze_workflow("/nonexistent/file.py")
        assert "Suggestion:" in str(exc_info.value)

        # Test missing decorator
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""
class MyWorkflow:
    async def run(self) -> str:
        return "test"
""")
            temp_path = Path(f.name)

        try:
            with pytest.raises(WorkflowParseError) as exc_info:
                analyze_workflow(temp_path)
            assert "Suggestion:" in str(exc_info.value)
        finally:
            temp_path.unlink()

    def test_error_messages_are_multiline(self) -> None:
        """Test that error messages use multi-line format for clarity."""
        with pytest.raises(WorkflowParseError) as exc_info:
            analyze_workflow("/nonexistent/file.py")

        error_message = str(exc_info.value)
        # Should have multiple lines (file path line, error line, suggestion line)
        assert error_message.count("\n") >= 2


class TestExceptionTypeCatching:
    """Tests for exception type catching behavior."""

    def test_can_catch_specific_exception_type(self) -> None:
        """Test that specific exception types can be caught separately."""
        caught_parse_error = False
        caught_generation_error = False

        # Test catching WorkflowParseError
        try:
            analyze_workflow("/nonexistent/file.py")
        except WorkflowParseError:
            caught_parse_error = True
        except GraphGenerationError:
            pytest.fail("Should have caught WorkflowParseError, not GraphGenerationError")

        assert caught_parse_error

        # Test catching GraphGenerationError
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            decision_code = "\n".join(
                [
                    f"        d{i} = await to_decision(True, 'Decision{i}')"
                    for i in range(11)
                ]
            )
            f.write(f"""
from temporalio import workflow
from temporalio_graphs import to_decision

@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self) -> str:
{decision_code}
        return "test"
""")
            temp_path = Path(f.name)

        try:
            try:
                analyze_workflow(temp_path)
            except GraphGenerationError:
                caught_generation_error = True
            except WorkflowParseError:
                pytest.fail("Should have caught GraphGenerationError, not WorkflowParseError")

            assert caught_generation_error
        finally:
            temp_path.unlink()

    def test_base_exception_catches_all_library_errors(self) -> None:
        """Test that TemporalioGraphsError catches all library exception types."""
        # Test with file not found (WorkflowParseError)
        try:
            analyze_workflow("/nonexistent/file.py")
        except TemporalioGraphsError as e:
            assert isinstance(e, WorkflowParseError)
        else:
            pytest.fail("Expected TemporalioGraphsError")

        # Test with path explosion (GraphGenerationError)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            decision_code = "\n".join(
                [
                    f"        d{i} = await to_decision(True, 'Decision{i}')"
                    for i in range(11)
                ]
            )
            f.write(f"""
from temporalio import workflow
from temporalio_graphs import to_decision

@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self) -> str:
{decision_code}
        return "test"
""")
            temp_path = Path(f.name)

        try:
            try:
                analyze_workflow(temp_path)
            except TemporalioGraphsError as e:
                assert isinstance(e, GraphGenerationError)
            else:
                pytest.fail("Expected TemporalioGraphsError")
        finally:
            temp_path.unlink()
