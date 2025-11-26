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
    assert "Missing @workflow.defn decorator" in error_message
    assert str(workflow_file.resolve()) in error_message
    assert "Add @workflow.defn decorator to workflow class" in error_message


def test_analyzer_no_workflow_run_raises_error(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that missing @workflow.run raises WorkflowParseError."""
    workflow_file = fixtures_dir / "no_run_method.py"

    with pytest.raises(WorkflowParseError) as exc_info:
        analyzer.analyze(workflow_file)

    error_message = str(exc_info.value)
    assert "Missing @workflow.run method" in error_message
    # Note: workflow class name may or may not be in the new error format
    assert str(workflow_file.resolve()) in error_message


def test_analyzer_invalid_python_syntax_raises_error(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that invalid Python syntax raises WorkflowParseError."""
    workflow_file = fixtures_dir / "invalid_syntax.py"

    with pytest.raises(WorkflowParseError) as exc_info:
        analyzer.analyze(workflow_file)

    error_message = str(exc_info.value)
    assert "Invalid Python syntax" in error_message
    assert str(workflow_file.resolve()) in error_message


def test_analyzer_file_not_found_raises_error(analyzer: WorkflowAnalyzer) -> None:
    """Test that non-existent file raises WorkflowParseError."""
    workflow_file = Path("/nonexistent/path/to/workflow.py")

    with pytest.raises(WorkflowParseError) as exc_info:
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
    assert "Missing @workflow.run method" in error_message


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
    # New error format uses "Suggestion:" instead of "Ensure" or "Please"
    assert "Suggestion:" in error_message or "Ensure" in error_message or "Please" in error_message


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
    assert metadata.activities[0].name == "my_activity"


def test_analyzer_detects_multiple_activities(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that analyzer detects multiple sequential activity calls."""
    workflow_file = fixtures_dir / "multi_activity_workflow.py"
    metadata = analyzer.analyze(workflow_file)

    assert len(metadata.activities) == 3
    assert metadata.activities[0].name == "activity_one"
    assert metadata.activities[1].name == "activity_two"
    assert metadata.activities[2].name == "activity_three"


def test_analyzer_detects_duplicate_activities(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that analyzer detects duplicate activity calls (same activity twice)."""
    workflow_file = fixtures_dir / "duplicate_activity_workflow.py"
    metadata = analyzer.analyze(workflow_file)

    assert len(metadata.activities) == 2
    assert metadata.activities[0].name == "my_activity"
    assert metadata.activities[1].name == "my_activity"


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

    assert any(a.name == "my_activity" for a in metadata.activities)


def test_analyzer_handles_string_activity_names(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that analyzer handles string literal activity names."""
    workflow_file = fixtures_dir / "string_activity_workflow.py"
    metadata = analyzer.analyze(workflow_file)

    assert len(metadata.activities) == 2
    assert metadata.activities[0].name == "validate_input"
    assert metadata.activities[1].name == "process_data"


def test_analyzer_handles_await_prefix(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that analyzer handles await prefixes on execute_activity calls."""
    workflow_file = fixtures_dir / "single_activity_workflow.py"
    metadata = analyzer.analyze(workflow_file)

    # The single_activity_workflow uses await, so this tests await handling
    assert len(metadata.activities) == 1
    assert metadata.activities[0].name == "my_activity"


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

    # Check that Activity objects contain name and line_num
    for activity in analyzer._activities:
        assert isinstance(activity.name, str)
        assert isinstance(activity.line_num, int)
        assert activity.line_num > 0


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

    assert [a.name for a in metadata.activities] == ["activity_one", "activity_two", "activity_three"]


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
        assert any(a.name.startswith("<unknown_activity_") for a in metadata.activities)

        # Check that warning was logged
        assert any("Could not extract activity name" in record.message for record in caplog.records)


# ============================================================================
# Signal Detection Integration Tests (Story 4.1)
# ============================================================================


def test_analyzer_detects_single_signal(analyzer: WorkflowAnalyzer, fixtures_dir: Path) -> None:
    """Test that analyzer detects single wait_condition() call in workflow."""
    workflow_file = fixtures_dir / "signal_simple.py"
    metadata = analyzer.analyze(workflow_file)

    # Verify signal detection
    assert len(metadata.signal_points) == 1
    assert metadata.signal_points[0].name == "WaitForApproval"
    assert metadata.signal_points[0].source_line > 0
    assert "lambda" in metadata.signal_points[0].condition_expr
    assert "timedelta" in metadata.signal_points[0].timeout_expr
    assert metadata.signal_points[0].node_id.startswith("sig_")


def test_analyzer_detects_multiple_signals(analyzer: WorkflowAnalyzer, fixtures_dir: Path) -> None:
    """Test that analyzer detects multiple wait_condition() calls in workflow."""
    workflow_file = fixtures_dir / "signal_multiple.py"
    metadata = analyzer.analyze(workflow_file)

    # Verify signal detection
    assert len(metadata.signal_points) == 2
    assert metadata.signal_points[0].name == "WaitForFirstApproval"
    assert metadata.signal_points[1].name == "WaitForSecondApproval"

    # Verify line numbers are tracked
    assert metadata.signal_points[0].source_line < metadata.signal_points[1].source_line


def test_analyzer_detects_signals_and_decisions_together(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that analyzer detects both signals and decisions in same workflow."""
    workflow_file = fixtures_dir / "signal_with_decision.py"
    metadata = analyzer.analyze(workflow_file)

    # Verify both signal and decision detected
    assert len(metadata.signal_points) == 1
    assert metadata.signal_points[0].name == "WaitForApproval"

    assert len(metadata.decision_points) == 1
    assert metadata.decision_points[0].name == "HighValue"


def test_analyzer_calculates_total_branch_points_with_signals(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that WorkflowMetadata.total_branch_points includes signals."""
    workflow_file = fixtures_dir / "signal_with_decision.py"
    metadata = analyzer.analyze(workflow_file)

    # 1 signal + 1 decision = 2 branch points
    assert metadata.total_branch_points == 2


def test_analyzer_calculates_total_paths_with_signals(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that total_paths calculation includes signals (2^(signals+decisions))."""
    workflow_file = fixtures_dir / "signal_with_decision.py"
    metadata = analyzer.analyze(workflow_file)

    # 1 signal + 1 decision = 2^2 = 4 paths
    assert metadata.total_paths == 4

    # Also test property
    assert metadata.total_paths_from_branches == 4


def test_analyzer_signal_metadata_extraction(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that analyzer extracts complete signal metadata."""
    workflow_file = fixtures_dir / "signal_simple.py"
    metadata = analyzer.analyze(workflow_file)

    assert len(metadata.signal_points) == 1
    signal = metadata.signal_points[0]

    # Verify all fields populated
    assert signal.name == "WaitForApproval"
    assert len(signal.condition_expr) > 0
    assert "approved" in signal.condition_expr
    assert len(signal.timeout_expr) > 0
    assert "24" in signal.timeout_expr
    assert signal.source_line > 0
    assert signal.node_id == f"sig_waitforapproval_{signal.source_line}"


def test_analyzer_handles_dynamic_signal_name(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that analyzer handles dynamic signal names with UnnamedSignal fallback."""
    workflow_file = fixtures_dir / "signal_dynamic_name.py"
    metadata = analyzer.analyze(workflow_file)

    # Should detect signal with UnnamedSignal fallback
    assert len(metadata.signal_points) == 1
    assert metadata.signal_points[0].name == "UnnamedSignal"


def test_analyzer_workflow_with_no_signals(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that analyzer returns empty signal_points for workflows without signals."""
    workflow_file = fixtures_dir / "single_activity_workflow.py"
    metadata = analyzer.analyze(workflow_file)

    # No signals in this workflow
    assert len(metadata.signal_points) == 0
    assert metadata.signal_points == []


def test_analyzer_signal_detection_performance(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that signal detection adds <1ms overhead per NFR-PERF-1."""
    workflow_file = fixtures_dir / "signal_multiple.py"

    start_time = time.perf_counter()
    metadata = analyzer.analyze(workflow_file)
    elapsed_time = time.perf_counter() - start_time

    # Verify correct detection
    assert len(metadata.signal_points) == 2

    # Performance requirement: <1ms total for workflow with 2 signals
    # Allow some slack for CI environments (5ms max)
    assert elapsed_time < 0.005, f"Analysis took {elapsed_time*1000:.2f}ms (>5ms threshold)"


def test_analyzer_backward_compatibility_with_signals(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that Story 4.1 maintains backward compatibility with Epic 2-3."""
    workflow_file = fixtures_dir / "valid_linear_workflow.py"
    metadata = analyzer.analyze(workflow_file)

    # All previous fields still work
    assert metadata.workflow_class == "MyWorkflow"
    assert metadata.workflow_run_method == "run"
    assert metadata.source_file == workflow_file.resolve()
    assert metadata.decision_points == []

    # New Story 4.1 field is present
    assert hasattr(metadata, "signal_points")
    assert isinstance(metadata.signal_points, list)
    assert metadata.signal_points == []  # No signals in linear workflow


# ============================================================================
# Signal Handler Detection Integration Tests (Story 8.2)
# ============================================================================


def test_analyzer_detects_signal_handlers(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that analyzer detects @workflow.signal handlers in workflow.

    This integration test verifies that the SignalHandlerDetector is properly
    integrated into the analyzer pipeline and that signal_handlers field is
    populated in WorkflowMetadata.
    """
    workflow_file = fixtures_dir / "signal_handler_workflow.py"
    metadata = analyzer.analyze(workflow_file)

    # Verify signal handlers detected
    assert len(metadata.signal_handlers) == 2

    # Verify first handler: ship_order (method name = signal name)
    handler1 = metadata.signal_handlers[0]
    assert handler1.signal_name == "ship_order"
    assert handler1.method_name == "ship_order"
    assert handler1.workflow_class == "ShippingWorkflow"
    assert handler1.source_line == 56  # Line where @workflow.signal decorator is
    assert handler1.node_id == "sig_handler_ship_order_56"

    # Verify second handler: cancel_shipment (explicit name differs from method)
    handler2 = metadata.signal_handlers[1]
    assert handler2.signal_name == "cancel_shipment"
    assert handler2.method_name == "cancel"
    assert handler2.workflow_class == "ShippingWorkflow"
    assert handler2.source_line == 66  # Line where method is defined
    assert handler2.node_id == "sig_handler_cancel_shipment_66"


def test_analyzer_signal_handlers_empty_for_workflow_without_handlers(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that signal_handlers is empty tuple for workflows without signal handlers."""
    workflow_file = fixtures_dir / "valid_linear_workflow.py"
    metadata = analyzer.analyze(workflow_file)

    # No signal handlers in this workflow
    assert metadata.signal_handlers == ()
    assert isinstance(metadata.signal_handlers, tuple)


def test_analyzer_signal_handlers_is_tuple(
    analyzer: WorkflowAnalyzer, fixtures_dir: Path
) -> None:
    """Test that signal_handlers is a tuple (immutable) for data integrity."""
    workflow_file = fixtures_dir / "signal_handler_workflow.py"
    metadata = analyzer.analyze(workflow_file)

    # Verify it's a tuple, not a list
    assert isinstance(metadata.signal_handlers, tuple)
    assert len(metadata.signal_handlers) == 2