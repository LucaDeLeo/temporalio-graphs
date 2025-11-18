"""Tests for AST-based workflow analyzer.

This module tests the WorkflowAnalyzer class which extracts workflow metadata
from Python source files using static AST analysis.
"""

import time
from pathlib import Path

import pytest

from temporalio_graphs.analyzer import WorkflowAnalyzer
from temporalio_graphs.exceptions import WorkflowParseError


@pytest.fixture
def analyzer() -> WorkflowAnalyzer:
    """Create a WorkflowAnalyzer instance for testing."""
    return WorkflowAnalyzer()


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures" / "sample_workflows"


def test_analyzer_detects_workflow_defn_decorator(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that analyzer detects @workflow.defn decorator on class."""
    workflow_file = fixtures_dir / "valid_linear_workflow.py"
    metadata = analyzer.analyze(workflow_file)

    assert metadata.workflow_class == "MyWorkflow"
    assert metadata.source_file == workflow_file.resolve()


def test_analyzer_extracts_workflow_class_name(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that analyzer correctly extracts workflow class name."""
    workflow_file = fixtures_dir / "valid_linear_workflow.py"
    metadata = analyzer.analyze(workflow_file)

    assert metadata.workflow_class == "MyWorkflow"


def test_analyzer_detects_workflow_run_method(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that analyzer detects @workflow.run method."""
    workflow_file = fixtures_dir / "valid_linear_workflow.py"
    metadata = analyzer.analyze(workflow_file)

    assert metadata.workflow_run_method == "run"


def test_analyzer_detects_multiple_methods_in_class(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that analyzer only detects run method, ignoring other methods."""
    workflow_file = fixtures_dir / "multiple_methods_workflow.py"
    metadata = analyzer.analyze(workflow_file)

    assert metadata.workflow_class == "MyWorkflow"
    assert metadata.workflow_run_method == "run"
    # Only run method should be detected, not helper_method or another_helper


def test_analyzer_no_workflow_defn_raises_error(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that missing @workflow.defn raises WorkflowParseError."""
    workflow_file = fixtures_dir / "no_workflow_decorator.py"

    with pytest.raises(WorkflowParseError) as exc_info:
        analyzer.analyze(workflow_file)

    error_message = str(exc_info.value)
    assert "No @workflow.defn decorated class found" in error_message
    assert str(workflow_file.resolve()) in error_message
    assert "Ensure the workflow class has @workflow.defn decorator" in error_message


def test_analyzer_no_workflow_run_raises_error(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that missing @workflow.run raises WorkflowParseError."""
    workflow_file = fixtures_dir / "no_run_method.py"

    with pytest.raises(WorkflowParseError) as exc_info:
        analyzer.analyze(workflow_file)

    error_message = str(exc_info.value)
    assert "No @workflow.run decorated method found" in error_message
    assert "MyWorkflow" in error_message


def test_analyzer_invalid_python_syntax_raises_error(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that invalid Python syntax raises WorkflowParseError."""
    workflow_file = fixtures_dir / "invalid_syntax.py"

    with pytest.raises(WorkflowParseError) as exc_info:
        analyzer.analyze(workflow_file)

    error_message = str(exc_info.value)
    assert "Syntax error in workflow file" in error_message
    assert str(workflow_file.resolve()) in error_message


def test_analyzer_file_not_found_raises_error(analyzer: WorkflowAnalyzer) -> None:
    """Test that non-existent file raises FileNotFoundError."""
    workflow_file = Path("/nonexistent/path/to/workflow.py")

    with pytest.raises(FileNotFoundError) as exc_info:
        analyzer.analyze(workflow_file)

    error_message = str(exc_info.value)
    assert "Workflow file not found" in error_message
    assert str(workflow_file) in error_message


def test_analyzer_stores_source_line_numbers(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that analyzer stores source line numbers for detected elements."""
    workflow_file = fixtures_dir / "valid_linear_workflow.py"
    metadata = analyzer.analyze(workflow_file)

    # Line numbers should be tracked internally (verified by successful analysis)
    # The _line_numbers dict is private, but we can verify correct parsing
    assert metadata.workflow_class == "MyWorkflow"
    assert metadata.workflow_run_method == "run"

    # Verify line numbers are captured in internal state
    assert hasattr(analyzer, "_line_numbers")
    assert "workflow_class" in analyzer._line_numbers
    assert "workflow_run_method" in analyzer._line_numbers
    assert analyzer._line_numbers["workflow_class"] > 0
    assert analyzer._line_numbers["workflow_run_method"] > 0


def test_analyzer_empty_workflow_class(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that empty workflow class (no methods) raises WorkflowParseError."""
    workflow_file = fixtures_dir / "empty_workflow.py"

    with pytest.raises(WorkflowParseError) as exc_info:
        analyzer.analyze(workflow_file)

    error_message = str(exc_info.value)
    assert "No @workflow.run decorated method found" in error_message


def test_analyzer_returns_workflow_metadata(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that analyzer returns WorkflowMetadata with correct type."""
    from temporalio_graphs._internal.graph_models import WorkflowMetadata

    workflow_file = fixtures_dir / "valid_linear_workflow.py"
    metadata = analyzer.analyze(workflow_file)

    assert isinstance(metadata, WorkflowMetadata)


def test_metadata_fields_populated_correctly(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that all WorkflowMetadata fields are populated correctly."""
    workflow_file = fixtures_dir / "valid_linear_workflow.py"
    metadata = analyzer.analyze(workflow_file)

    # Required fields from Epic 2
    assert metadata.workflow_class == "MyWorkflow"
    assert metadata.workflow_run_method == "run"
    assert metadata.source_file == workflow_file.resolve()

    # Empty lists (populated in future stories)
    assert metadata.activities == []
    assert metadata.decision_points == []
    assert metadata.signal_points == []

    # Linear workflow path count
    assert metadata.total_paths == 1


def test_metadata_total_paths_equals_one(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that total_paths is 1 for linear workflows in Epic 2."""
    workflow_file = fixtures_dir / "valid_linear_workflow.py"
    metadata = analyzer.analyze(workflow_file)

    assert metadata.total_paths == 1


def test_analyzer_accepts_path_object(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that analyzer accepts Path object as input."""
    workflow_file = fixtures_dir / "valid_linear_workflow.py"
    metadata = analyzer.analyze(workflow_file)

    assert metadata.workflow_class == "MyWorkflow"


def test_analyzer_accepts_string_path(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that analyzer accepts string path as input."""
    workflow_file = str(fixtures_dir / "valid_linear_workflow.py")
    metadata = analyzer.analyze(workflow_file)

    assert metadata.workflow_class == "MyWorkflow"


def test_analyzer_detects_async_run_method(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that analyzer detects async run methods."""
    workflow_file = fixtures_dir / "async_run_workflow.py"
    metadata = analyzer.analyze(workflow_file)

    assert metadata.workflow_class == "AsyncWorkflow"
    assert metadata.workflow_run_method == "run"


def test_analyzer_performance_simple_workflow(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that analyzer completes in <1ms for simple workflows (NFR-PERF-1)."""
    workflow_file = fixtures_dir / "valid_linear_workflow.py"

    start_time = time.perf_counter()
    metadata = analyzer.analyze(workflow_file)
    elapsed_time = time.perf_counter() - start_time

    # Verify successful analysis
    assert metadata.workflow_class == "MyWorkflow"

    # Performance requirement: <1ms for simple workflows
    # Allow some slack for CI environments (5ms max)
    assert elapsed_time < 0.005, f"Analysis took {elapsed_time*1000:.2f}ms (>5ms threshold)"


def test_error_message_includes_file_path(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that error messages include file path for debugging."""
    workflow_file = fixtures_dir / "no_workflow_decorator.py"

    with pytest.raises(WorkflowParseError) as exc_info:
        analyzer.analyze(workflow_file)

    error_message = str(exc_info.value)
    assert str(workflow_file.resolve()) in error_message


def test_error_message_includes_helpful_suggestion(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that error messages include actionable suggestions."""
    workflow_file = fixtures_dir / "no_workflow_decorator.py"

    with pytest.raises(WorkflowParseError) as exc_info:
        analyzer.analyze(workflow_file)

    error_message = str(exc_info.value)
    assert "Ensure" in error_message or "Please" in error_message


def test_analyzer_imports_workflow_metadata() -> None:
    """Test that analyzer can import WorkflowMetadata."""
    from temporalio_graphs._internal.graph_models import WorkflowMetadata

    # Verify import succeeds
    assert WorkflowMetadata is not None


def test_analyzer_uses_workflow_parse_error() -> None:
    """Test that analyzer uses WorkflowParseError exception."""
    from temporalio_graphs.exceptions import WorkflowParseError

    # Verify import succeeds
    assert WorkflowParseError is not None


def test_public_methods_have_docstrings(analyzer: WorkflowAnalyzer) -> None:
    """Test that public methods have docstrings."""
    # analyze() method should have docstring
    assert analyzer.analyze.__doc__ is not None
    assert len(analyzer.analyze.__doc__) > 50

    # Class should have docstring
    assert WorkflowAnalyzer.__doc__ is not None
    assert len(WorkflowAnalyzer.__doc__) > 50


def test_docstrings_have_args_section(analyzer: WorkflowAnalyzer) -> None:
    """Test that docstrings include Args section (Google style)."""
    # analyze() method docstring should have Args section
    docstring = analyzer.analyze.__doc__
    assert docstring is not None
    assert "Args:" in docstring
    assert "Returns:" in docstring
    assert "Raises:" in docstring


def test_analyzer_class_extends_ast_node_visitor() -> None:
    """Test that WorkflowAnalyzer extends ast.NodeVisitor."""
    import ast

    assert issubclass(WorkflowAnalyzer, ast.NodeVisitor)


def test_analyzer_has_analyze_method() -> None:
    """Test that WorkflowAnalyzer has analyze method with correct signature."""
    analyzer = WorkflowAnalyzer()

    assert hasattr(analyzer, "analyze")
    assert callable(analyzer.analyze)


def test_analyzer_warns_non_py_extension(
    analyzer: WorkflowAnalyzer, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that analyzer warns when file doesn't have .py extension."""
    import logging

    # Create a temp file with non-.py extension but valid Python content
    workflow_file = tmp_path / "workflow.txt"
    workflow_file.write_text(
        """from temporalio import workflow

@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        return f"Hello {name}"
"""
    )

    # Capture log warnings
    with caplog.at_level(logging.WARNING, logger="temporalio_graphs.analyzer"):
        metadata = analyzer.analyze(workflow_file)

        # Analysis should succeed despite warning
        assert metadata.workflow_class == "MyWorkflow"

        # Check that warning was logged
        assert any(".py extension" in record.message for record in caplog.records)


def test_analyzer_direct_decorator_import(
    analyzer: WorkflowAnalyzer, tmp_path: Path
) -> None:
    """Test that analyzer handles direct decorator imports."""
    # Create workflow with direct import pattern
    workflow_file = tmp_path / "direct_import_workflow.py"
    workflow_file.write_text(
        """from temporalio.workflow import defn, run

@defn
class DirectImportWorkflow:
    @run
    async def run(self, name: str) -> str:
        return f"Hello {name}"
"""
    )

    metadata = analyzer.analyze(workflow_file)
    assert metadata.workflow_class == "DirectImportWorkflow"
    assert metadata.workflow_run_method == "run"


def test_analyzer_nested_class_doesnt_interfere(
    analyzer: WorkflowAnalyzer, tmp_path: Path
) -> None:
    """Test that nested classes or classes outside workflow are ignored."""
    workflow_file = tmp_path / "nested_workflow.py"
    workflow_file.write_text(
        """from temporalio import workflow

class NonWorkflowClass:
    def some_method(self):
        pass

@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        return f"Hello {name}"

    def helper(self):
        pass

class AnotherNonWorkflow:
    pass
"""
    )

    metadata = analyzer.analyze(workflow_file)
    assert metadata.workflow_class == "MyWorkflow"
    assert metadata.workflow_run_method == "run"


def test_analyzer_sync_run_method(analyzer: WorkflowAnalyzer, tmp_path: Path) -> None:
    """Test that analyzer handles non-async (sync) run methods."""
    workflow_file = tmp_path / "sync_workflow.py"
    workflow_file.write_text(
        """from temporalio import workflow

@workflow.defn
class SyncWorkflow:
    @workflow.run
    def run(self, name: str) -> str:
        return f"Hello {name}"
"""
    )

    metadata = analyzer.analyze(workflow_file)
    assert metadata.workflow_class == "SyncWorkflow"
    assert metadata.workflow_run_method == "run"


# ============================================================================
# Activity Detection Tests (Story 2.3)
# ============================================================================


def test_analyzer_detects_single_activity(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that analyzer detects single execute_activity() call."""
    workflow_file = fixtures_dir / "single_activity_workflow.py"
    metadata = analyzer.analyze(workflow_file)

    assert len(metadata.activities) == 1
    assert metadata.activities[0] == "my_activity"


def test_analyzer_detects_multiple_activities(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that analyzer detects multiple sequential activity calls."""
    workflow_file = fixtures_dir / "multi_activity_workflow.py"
    metadata = analyzer.analyze(workflow_file)

    assert len(metadata.activities) == 3
    assert metadata.activities[0] == "activity_one"
    assert metadata.activities[1] == "activity_two"
    assert metadata.activities[2] == "activity_three"


def test_analyzer_detects_duplicate_activities(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that analyzer detects duplicate activity calls (same activity twice)."""
    workflow_file = fixtures_dir / "duplicate_activity_workflow.py"
    metadata = analyzer.analyze(workflow_file)

    assert len(metadata.activities) == 2
    assert metadata.activities[0] == "my_activity"
    assert metadata.activities[1] == "my_activity"


def test_analyzer_no_activities_workflow(analyzer: WorkflowAnalyzer, tmp_path: Path) -> None:
    """Test that analyzer handles workflows with no activity calls."""
    workflow_file = tmp_path / "no_activities.py"
    workflow_file.write_text(
        """from temporalio import workflow

@workflow.defn
class NoActivityWorkflow:
    @workflow.run
    async def run(self) -> str:
        return "done"
"""
    )

    metadata = analyzer.analyze(workflow_file)
    assert len(metadata.activities) == 0
    assert metadata.activities == []


def test_analyzer_extracts_activity_names(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that analyzer correctly extracts activity names from function references."""
    workflow_file = fixtures_dir / "single_activity_workflow.py"
    metadata = analyzer.analyze(workflow_file)

    assert "my_activity" in metadata.activities


def test_analyzer_handles_string_activity_names(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that analyzer handles string literal activity names."""
    workflow_file = fixtures_dir / "string_activity_workflow.py"
    metadata = analyzer.analyze(workflow_file)

    assert len(metadata.activities) == 2
    assert metadata.activities[0] == "validate_input"
    assert metadata.activities[1] == "process_data"


def test_analyzer_handles_await_prefix(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that analyzer handles await prefixes on execute_activity calls."""
    workflow_file = fixtures_dir / "single_activity_workflow.py"
    metadata = analyzer.analyze(workflow_file)

    # The single_activity_workflow uses await, so this tests await handling
    assert len(metadata.activities) == 1
    assert metadata.activities[0] == "my_activity"


def test_analyzer_activity_line_numbers(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that analyzer tracks source line numbers for activity calls."""
    workflow_file = fixtures_dir / "single_activity_workflow.py"
    metadata = analyzer.analyze(workflow_file)

    # Verify activities are detected (internal line tracking)
    assert len(metadata.activities) >= 1

    # Verify that line numbers are stored internally
    assert hasattr(analyzer, "_activities")
    assert len(analyzer._activities) >= 1

    # Check that tuples contain (name, line_number)
    for activity_name, line_no in analyzer._activities:
        assert isinstance(activity_name, str)
        assert isinstance(line_no, int)
        assert line_no > 0


def test_analyzer_ignores_non_activity_calls(
    analyzer: WorkflowAnalyzer, tmp_path: Path
) -> None:
    """Test that analyzer ignores non-activity method calls."""
    workflow_file = tmp_path / "non_activity_calls.py"
    workflow_file.write_text(
        """from temporalio import workflow

@workflow.defn
class NonActivityWorkflow:
    @workflow.run
    async def run(self) -> str:
        workflow.execute_signal("my_signal")
        other_module.execute_activity("something")
        self.helper_method()
        return "done"
"""
    )

    metadata = analyzer.analyze(workflow_file)
    # Should have no activities since only non-activity calls are present
    assert len(metadata.activities) == 0


def test_analyzer_activities_in_correct_order(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that activities are returned in the order they appear in source."""
    workflow_file = fixtures_dir / "multi_activity_workflow.py"
    metadata = analyzer.analyze(workflow_file)

    assert metadata.activities == ["activity_one", "activity_two", "activity_three"]


def test_analyzer_performance_multi_activity(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that analyzer detects multiple activities in <0.5ms (NFR-PERF-1)."""
    workflow_file = fixtures_dir / "multi_activity_workflow.py"

    start_time = time.perf_counter()
    metadata = analyzer.analyze(workflow_file)
    elapsed_time = time.perf_counter() - start_time

    # Verify correct detection
    assert len(metadata.activities) == 3

    # Performance requirement: <0.5ms for multi-activity workflows
    # Allow some slack for CI environments (5ms max)
    assert elapsed_time < 0.005, f"Analysis took {elapsed_time*1000:.2f}ms (>5ms threshold)"


def test_analyzer_backward_compatibility_with_story_2_2(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that Story 2.3 maintains backward compatibility with Story 2.2."""
    workflow_file = fixtures_dir / "valid_linear_workflow.py"
    metadata = analyzer.analyze(workflow_file)

    # All Story 2.2 requirements still work
    assert metadata.workflow_class == "MyWorkflow"
    assert metadata.workflow_run_method == "run"
    assert metadata.source_file == workflow_file.resolve()
    assert metadata.total_paths == 1
    assert metadata.decision_points == []
    assert metadata.signal_points == []

    # New Story 2.3 field is present
    assert hasattr(metadata, "activities")
    assert isinstance(metadata.activities, list)


def test_analyzer_handles_malformed_activity_call(
    analyzer: WorkflowAnalyzer, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that analyzer logs warning for malformed activity calls."""
    import logging

    workflow_file = tmp_path / "malformed_activity.py"
    workflow_file.write_text(
        """from temporalio import workflow

@workflow.defn
class MalformedActivityWorkflow:
    @workflow.run
    async def run(self) -> str:
        # Malformed: numeric literal as activity (invalid but parseable)
        await workflow.execute_activity(123, start_to_close_timeout=None)
        return "done"
"""
    )

    # Capture warnings
    with caplog.at_level(logging.WARNING, logger="temporalio_graphs.analyzer"):
        metadata = analyzer.analyze(workflow_file)

        # Should detect the malformed activity with placeholder name
        assert len(metadata.activities) == 1
        assert "<unknown_activity_" in metadata.activities[0]

        # Check that warning was logged
        assert any("Could not extract activity name" in record.message for record in caplog.records)
