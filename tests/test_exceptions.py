"""Unit tests for exception classes in temporalio_graphs.exceptions module."""

from pathlib import Path

import pytest

from temporalio_graphs.exceptions import (
    GraphGenerationError,
    InvalidDecisionError,
    TemporalioGraphsError,
    UnsupportedPatternError,
    WorkflowParseError,
)


class TestTemporalioGraphsError:
    """Tests for TemporalioGraphsError base exception."""

    def test_base_exception_creation(self) -> None:
        """Test base exception can be created with message."""
        error = TemporalioGraphsError("test error message")
        assert str(error) == "test error message"

    def test_base_exception_inheritance(self) -> None:
        """Test base exception inherits from Exception."""
        error = TemporalioGraphsError("test")
        assert isinstance(error, Exception)


class TestWorkflowParseError:
    """Tests for WorkflowParseError exception."""

    def test_workflow_parse_error_format(self) -> None:
        """Test WorkflowParseError formatted message contains all components."""
        error = WorkflowParseError(
            file_path=Path("/path/to/workflow.py"),
            line=42,
            message="Missing @workflow.defn decorator",
            suggestion="Add @workflow.defn decorator to workflow class",
        )

        error_str = str(error)
        assert "Cannot parse workflow file: /path/to/workflow.py" in error_str
        assert "Line 42:" in error_str
        assert "Missing @workflow.defn decorator" in error_str
        assert "Suggestion: Add @workflow.defn decorator to workflow class" in error_str

    def test_workflow_parse_error_attributes(self) -> None:
        """Test WorkflowParseError attributes are accessible."""
        file_path = Path("/path/to/workflow.py")
        error = WorkflowParseError(
            file_path=file_path,
            line=42,
            message="Missing @workflow.defn decorator",
            suggestion="Add @workflow.defn decorator to workflow class",
        )

        assert error.file_path == file_path
        assert error.line == 42
        assert error.message == "Missing @workflow.defn decorator"
        assert error.suggestion == "Add @workflow.defn decorator to workflow class"

    def test_workflow_parse_error_inheritance(self) -> None:
        """Test WorkflowParseError inherits from TemporalioGraphsError."""
        error = WorkflowParseError(
            file_path=Path("test.py"),
            line=0,
            message="test",
            suggestion="test",
        )
        assert isinstance(error, TemporalioGraphsError)
        assert isinstance(error, Exception)

    def test_workflow_parse_error_line_zero(self) -> None:
        """Test WorkflowParseError with line 0 (file-level error)."""
        error = WorkflowParseError(
            file_path=Path("/path/to/workflow.py"),
            line=0,
            message="Workflow file not found",
            suggestion="Verify file path is correct",
        )

        error_str = str(error)
        assert "Line 0:" in error_str
        assert "Workflow file not found" in error_str


class TestUnsupportedPatternError:
    """Tests for UnsupportedPatternError exception."""

    def test_unsupported_pattern_error_with_line(self) -> None:
        """Test UnsupportedPatternError with line number includes line in message."""
        error = UnsupportedPatternError(
            pattern="while loop",
            suggestion="Refactor loop into linear activities",
            line=23,
        )

        error_str = str(error)
        assert "Unsupported pattern: while loop at line 23" in error_str
        assert "Suggestion: Refactor loop into linear activities" in error_str

    def test_unsupported_pattern_error_without_line(self) -> None:
        """Test UnsupportedPatternError without line number excludes line from message."""
        error = UnsupportedPatternError(
            pattern="dynamic activity name",
            suggestion="Use string literal for activity name",
        )

        error_str = str(error)
        assert "Unsupported pattern: dynamic activity name" in error_str
        assert "at line" not in error_str
        assert "Suggestion: Use string literal for activity name" in error_str

    def test_unsupported_pattern_error_attributes(self) -> None:
        """Test UnsupportedPatternError attributes are accessible."""
        error = UnsupportedPatternError(
            pattern="while loop",
            suggestion="Refactor loop into linear activities",
            line=23,
        )

        assert error.pattern == "while loop"
        assert error.suggestion == "Refactor loop into linear activities"
        assert error.line == 23

    def test_unsupported_pattern_error_attributes_no_line(self) -> None:
        """Test UnsupportedPatternError attributes when line is None."""
        error = UnsupportedPatternError(
            pattern="dynamic activity name",
            suggestion="Use string literal for activity name",
        )

        assert error.pattern == "dynamic activity name"
        assert error.suggestion == "Use string literal for activity name"
        assert error.line is None

    def test_unsupported_pattern_error_inheritance(self) -> None:
        """Test UnsupportedPatternError inherits from TemporalioGraphsError."""
        error = UnsupportedPatternError(
            pattern="test",
            suggestion="test",
        )
        assert isinstance(error, TemporalioGraphsError)
        assert isinstance(error, Exception)


class TestGraphGenerationError:
    """Tests for GraphGenerationError exception."""

    def test_graph_generation_error_with_context(self) -> None:
        """Test GraphGenerationError with context dict includes context in message."""
        error = GraphGenerationError(
            reason="Too many decision points (12) would generate 4096 paths (limit: 1024)",
            context={"decision_count": 12, "limit": 10, "paths": 4096},
        )

        error_str = str(error)
        assert "Graph generation failed:" in error_str
        assert "Too many decision points (12) would generate 4096 paths" in error_str
        assert "Context:" in error_str
        assert "decision_count" in error_str

    def test_graph_generation_error_without_context(self) -> None:
        """Test GraphGenerationError without context dict excludes context from message."""
        error = GraphGenerationError(
            reason="Path count exceeds maximum",
        )

        error_str = str(error)
        assert "Graph generation failed: Path count exceeds maximum" in error_str
        assert "Context:" not in error_str

    def test_graph_generation_error_attributes(self) -> None:
        """Test GraphGenerationError attributes are accessible."""
        context_dict = {"decision_count": 12, "limit": 10, "paths": 4096}
        error = GraphGenerationError(
            reason="Too many decision points",
            context=context_dict,
        )

        assert error.reason == "Too many decision points"
        assert error.context == context_dict

    def test_graph_generation_error_attributes_no_context(self) -> None:
        """Test GraphGenerationError attributes when context is None."""
        error = GraphGenerationError(
            reason="Path count exceeds maximum",
        )

        assert error.reason == "Path count exceeds maximum"
        assert error.context is None

    def test_graph_generation_error_inheritance(self) -> None:
        """Test GraphGenerationError inherits from TemporalioGraphsError."""
        error = GraphGenerationError(
            reason="test",
        )
        assert isinstance(error, TemporalioGraphsError)
        assert isinstance(error, Exception)


class TestInvalidDecisionError:
    """Tests for InvalidDecisionError exception."""

    def test_invalid_decision_error_format(self) -> None:
        """Test InvalidDecisionError formatted message contains all components."""
        error = InvalidDecisionError(
            function="to_decision",
            issue="Missing decision name parameter",
            suggestion="Provide decision name as second argument: to_decision(condition, 'DecisionName')",
        )

        error_str = str(error)
        assert "Invalid to_decision usage:" in error_str
        assert "Missing decision name parameter" in error_str
        assert "Suggestion: Provide decision name as second argument" in error_str

    def test_invalid_decision_error_attributes(self) -> None:
        """Test InvalidDecisionError attributes are accessible."""
        error = InvalidDecisionError(
            function="to_decision",
            issue="Missing decision name parameter",
            suggestion="Provide decision name as second argument",
        )

        assert error.function == "to_decision"
        assert error.issue == "Missing decision name parameter"
        assert error.suggestion == "Provide decision name as second argument"

    def test_invalid_decision_error_wait_condition(self) -> None:
        """Test InvalidDecisionError for wait_condition function."""
        error = InvalidDecisionError(
            function="wait_condition",
            issue="Timeout must be positive timedelta",
            suggestion="Use timedelta with positive duration",
        )

        error_str = str(error)
        assert "Invalid wait_condition usage:" in error_str
        assert "Timeout must be positive timedelta" in error_str

    def test_invalid_decision_error_inheritance(self) -> None:
        """Test InvalidDecisionError inherits from TemporalioGraphsError."""
        error = InvalidDecisionError(
            function="test",
            issue="test",
            suggestion="test",
        )
        assert isinstance(error, TemporalioGraphsError)
        assert isinstance(error, Exception)


class TestExceptionChaining:
    """Tests for exception chaining with raise...from pattern."""

    def test_exception_chaining_preserves_original(self) -> None:
        """Test that raise...from preserves original exception in __cause__."""
        original = FileNotFoundError("File not found")

        try:
            raise WorkflowParseError(
                file_path=Path("/test/file.py"),
                line=0,
                message="Workflow file not found",
                suggestion="Verify file path is correct",
            ) from original
        except WorkflowParseError as e:
            assert e.__cause__ is original
            assert isinstance(e.__cause__, FileNotFoundError)


class TestExceptionInheritance:
    """Tests for exception inheritance hierarchy."""

    def test_all_exceptions_inherit_from_base(self) -> None:
        """Test all exceptions inherit from TemporalioGraphsError and Exception."""
        exceptions = [
            WorkflowParseError(Path("test.py"), 0, "test", "test"),
            UnsupportedPatternError("test", "test"),
            GraphGenerationError("test"),
            InvalidDecisionError("test", "test", "test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, TemporalioGraphsError)
            assert isinstance(exc, Exception)

    def test_base_exception_can_catch_all(self) -> None:
        """Test that TemporalioGraphsError can catch all library exceptions."""
        exceptions = [
            WorkflowParseError(Path("test.py"), 0, "test", "test"),
            UnsupportedPatternError("test", "test"),
            GraphGenerationError("test"),
            InvalidDecisionError("test", "test", "test"),
        ]

        for exc in exceptions:
            try:
                raise exc
            except TemporalioGraphsError:
                pass  # Successfully caught with base exception
            else:
                pytest.fail(f"Exception {type(exc).__name__} not caught by base class")
