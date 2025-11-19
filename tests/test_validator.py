"""Unit tests for workflow validation module.

Tests cover:
- ValidationWarning and ValidationReport data models
- Unreachable activity detection algorithm
- Validation orchestration and suppression
- Report formatting and output
"""

from pathlib import Path

import pytest

from temporalio_graphs._internal.graph_models import Activity, WorkflowMetadata
from temporalio_graphs.context import GraphBuildingContext
from temporalio_graphs.path import GraphPath, PathStep
from temporalio_graphs.validator import (
    ValidationReport,
    ValidationWarning,
    WarningSeverity,
    detect_unreachable_activities,
    validate_workflow,
)


class TestValidationWarning:
    """Tests for ValidationWarning dataclass."""

    def test_warning_creation(self) -> None:
        """Test ValidationWarning can be instantiated with all fields."""
        warning = ValidationWarning(
            severity=WarningSeverity.WARNING,
            category="unreachable",
            message="Activity never called",
            file_path=Path("workflow.py"),
            line=42,
            activity_name="my_activity",
            suggestion="Remove this activity"
        )

        assert warning.severity == WarningSeverity.WARNING
        assert warning.category == "unreachable"
        assert warning.message == "Activity never called"
        assert warning.file_path == Path("workflow.py")
        assert warning.line == 42
        assert warning.activity_name == "my_activity"
        assert warning.suggestion == "Remove this activity"

    def test_warning_format_with_all_fields(self) -> None:
        """Test ValidationWarning.format() produces correct output."""
        warning = ValidationWarning(
            severity=WarningSeverity.WARNING,
            category="unreachable",
            message="Activity is defined but never called",
            file_path=Path("workflow.py"),
            line=42,
            activity_name="orphan_activity",
            suggestion="Remove unused activity"
        )

        formatted = warning.format()

        # Check for icon, category, message, location, suggestion
        assert "⚠️" in formatted
        assert "[UNREACHABLE]" in formatted
        assert "Activity is defined but never called" in formatted
        assert "'orphan_activity'" in formatted
        assert "workflow.py:42" in formatted
        assert "Suggestion: Remove unused activity" in formatted

    def test_warning_format_info_severity(self) -> None:
        """Test ValidationWarning.format() uses info icon for INFO severity."""
        warning = ValidationWarning(
            severity=WarningSeverity.INFO,
            category="optimization",
            message="Consider optimizing this pattern",
            file_path=Path("workflow.py"),
            line=10,
            activity_name=None,
            suggestion=None
        )

        formatted = warning.format()

        # INFO severity should use info icon
        assert "ℹ️" in formatted
        assert "[OPTIMIZATION]" in formatted

    def test_warning_format_without_suggestion(self) -> None:
        """Test ValidationWarning.format() handles missing suggestion."""
        warning = ValidationWarning(
            severity=WarningSeverity.WARNING,
            category="test",
            message="Test message",
            file_path=Path("workflow.py"),
            line=5,
            activity_name=None,
            suggestion=None
        )

        formatted = warning.format()

        # Should not contain "Suggestion:" when suggestion is None
        assert "Suggestion:" not in formatted
        assert "Test message" in formatted

    def test_warning_immutability(self) -> None:
        """Test ValidationWarning is immutable (frozen dataclass)."""
        warning = ValidationWarning(
            severity=WarningSeverity.WARNING,
            category="test",
            message="Test",
            file_path=Path("workflow.py"),
            line=1,
        )

        # Attempting to modify should raise FrozenInstanceError
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            warning.line = 99  # type: ignore


class TestValidationReport:
    """Tests for ValidationReport dataclass."""

    def test_report_creation_empty(self) -> None:
        """Test ValidationReport can be instantiated with no warnings."""
        report = ValidationReport(
            warnings=[],
            total_activities=5,
            total_paths=4,
            unreachable_count=0,
            unused_count=0
        )

        assert report.warnings == []
        assert report.total_activities == 5
        assert report.total_paths == 4
        assert report.unreachable_count == 0
        assert report.unused_count == 0

    def test_report_has_warnings_false(self) -> None:
        """Test ValidationReport.has_warnings() returns False when empty."""
        report = ValidationReport(
            warnings=[],
            total_activities=5,
            total_paths=4,
            unreachable_count=0
        )

        assert report.has_warnings() is False

    def test_report_has_warnings_true(self) -> None:
        """Test ValidationReport.has_warnings() returns True when warnings exist."""
        warning = ValidationWarning(
            severity=WarningSeverity.WARNING,
            category="unreachable",
            message="Activity never called",
            file_path=Path("workflow.py"),
            line=42,
        )
        report = ValidationReport(
            warnings=[warning],
            total_activities=5,
            total_paths=4,
            unreachable_count=1
        )

        assert report.has_warnings() is True

    def test_report_format_empty(self) -> None:
        """Test ValidationReport.format() returns empty string when no warnings."""
        report = ValidationReport(
            warnings=[],
            total_activities=5,
            total_paths=4,
            unreachable_count=0
        )

        formatted = report.format()

        assert formatted == ""

    def test_report_format_with_warnings(self) -> None:
        """Test ValidationReport.format() produces complete report."""
        warning1 = ValidationWarning(
            severity=WarningSeverity.WARNING,
            category="unreachable",
            message="Activity never called",
            file_path=Path("workflow.py"),
            line=42,
            activity_name="activity_a",
        )
        warning2 = ValidationWarning(
            severity=WarningSeverity.WARNING,
            category="unreachable",
            message="Activity never called",
            file_path=Path("workflow.py"),
            line=55,
            activity_name="activity_b",
        )
        report = ValidationReport(
            warnings=[warning1, warning2],
            total_activities=5,
            total_paths=4,
            unreachable_count=2
        )

        formatted = report.format()

        # Check header
        assert "--- Validation Report ---" in formatted
        assert "Total Paths: 4" in formatted
        assert "Total Activities: 5" in formatted
        assert "Warnings: 2" in formatted

        # Check both warnings appear
        assert "activity_a" in formatted
        assert "activity_b" in formatted
        assert "workflow.py:42" in formatted
        assert "workflow.py:55" in formatted

    def test_report_immutability(self) -> None:
        """Test ValidationReport is immutable (frozen dataclass)."""
        report = ValidationReport(
            warnings=[],
            total_activities=5,
            total_paths=4,
            unreachable_count=0
        )

        # Attempting to modify should raise FrozenInstanceError
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            report.total_paths = 99  # type: ignore


class TestDetectUnreachableActivities:
    """Tests for detect_unreachable_activities function."""

    def test_no_unreachable_activities(self) -> None:
        """Test detect_unreachable_activities when all activities are called."""
        metadata = WorkflowMetadata(
            workflow_class="TestWorkflow",
            workflow_run_method="run",
            activities=[
                Activity("activity_a", 10),
                Activity("activity_b", 20),
            ],
            decision_points=[],
            signal_points=[],
            source_file=Path("test.py"),
            total_paths=1
        )

        path = GraphPath("0", [
            PathStep("activity", "activity_a"),
            PathStep("activity", "activity_b"),
        ])

        warnings = detect_unreachable_activities(metadata, [path])

        assert len(warnings) == 0

    def test_single_unreachable_activity(self) -> None:
        """Test detect_unreachable_activities with 1 unreachable activity."""
        metadata = WorkflowMetadata(
            workflow_class="TestWorkflow",
            workflow_run_method="run",
            activities=[
                Activity("activity_a", 10),
                Activity("activity_b", 20),
                Activity("orphan", 30),
            ],
            decision_points=[],
            signal_points=[],
            source_file=Path("test.py"),
            total_paths=1
        )

        path = GraphPath("0", [
            PathStep("activity", "activity_a"),
            PathStep("activity", "activity_b"),
        ])

        warnings = detect_unreachable_activities(metadata, [path])

        assert len(warnings) == 1
        assert warnings[0].category == "unreachable"
        assert warnings[0].activity_name == "orphan"
        assert warnings[0].line == 30
        assert warnings[0].severity == WarningSeverity.WARNING
        assert "never called" in warnings[0].message
        assert warnings[0].suggestion is not None

    def test_multiple_unreachable_activities(self) -> None:
        """Test detect_unreachable_activities with 3 unreachable activities."""
        metadata = WorkflowMetadata(
            workflow_class="TestWorkflow",
            workflow_run_method="run",
            activities=[
                Activity("used_activity", 10),
                Activity("orphan_a", 20),
                Activity("orphan_b", 30),
                Activity("orphan_c", 40),
            ],
            decision_points=[],
            signal_points=[],
            source_file=Path("test.py"),
            total_paths=1
        )

        path = GraphPath("0", [
            PathStep("activity", "used_activity"),
        ])

        warnings = detect_unreachable_activities(metadata, [path])

        assert len(warnings) == 3
        # Warnings should be sorted by activity name
        assert warnings[0].activity_name == "orphan_a"
        assert warnings[1].activity_name == "orphan_b"
        assert warnings[2].activity_name == "orphan_c"

    def test_unreachable_with_multiple_paths(self) -> None:
        """Test detect_unreachable_activities with multiple execution paths."""
        metadata = WorkflowMetadata(
            workflow_class="TestWorkflow",
            workflow_run_method="run",
            activities=[
                Activity("activity_a", 10),
                Activity("activity_b", 20),
                Activity("activity_c", 30),
                Activity("orphan", 40),
            ],
            decision_points=[],
            signal_points=[],
            source_file=Path("test.py"),
            total_paths=2
        )

        # Path 1 calls a and b
        path1 = GraphPath("0", [
            PathStep("activity", "activity_a"),
            PathStep("activity", "activity_b"),
        ])

        # Path 2 calls a and c
        path2 = GraphPath("1", [
            PathStep("activity", "activity_a"),
            PathStep("activity", "activity_c"),
        ])

        warnings = detect_unreachable_activities(metadata, [path1, path2])

        # Only orphan is unreachable (a, b, c are all called in at least one path)
        assert len(warnings) == 1
        assert warnings[0].activity_name == "orphan"

    def test_no_activities_defined(self) -> None:
        """Test detect_unreachable_activities when no activities exist."""
        metadata = WorkflowMetadata(
            workflow_class="EmptyWorkflow",
            workflow_run_method="run",
            activities=[],
            decision_points=[],
            signal_points=[],
            source_file=Path("test.py"),
            total_paths=1
        )

        path = GraphPath("0", [])

        warnings = detect_unreachable_activities(metadata, [path])

        assert len(warnings) == 0

    def test_no_paths_generated(self) -> None:
        """Test detect_unreachable_activities when no paths exist (edge case)."""
        metadata = WorkflowMetadata(
            workflow_class="TestWorkflow",
            workflow_run_method="run",
            activities=[
                Activity("activity_a", 10),
            ],
            decision_points=[],
            signal_points=[],
            source_file=Path("test.py"),
            total_paths=0
        )

        warnings = detect_unreachable_activities(metadata, [])

        # All activities are unreachable if no paths
        assert len(warnings) == 1
        assert warnings[0].activity_name == "activity_a"


class TestValidateWorkflow:
    """Tests for validate_workflow orchestrator function."""

    def test_validate_workflow_no_warnings(self) -> None:
        """Test validate_workflow returns empty report when all activities called."""
        metadata = WorkflowMetadata(
            workflow_class="TestWorkflow",
            workflow_run_method="run",
            activities=[
                Activity("activity_a", 10),
                Activity("activity_b", 20),
            ],
            decision_points=[],
            signal_points=[],
            source_file=Path("test.py"),
            total_paths=1
        )

        path = GraphPath("0", [
            PathStep("activity", "activity_a"),
            PathStep("activity", "activity_b"),
        ])

        context = GraphBuildingContext()
        report = validate_workflow(metadata, [path], context)

        assert report.has_warnings() is False
        assert report.total_activities == 2
        assert report.total_paths == 1
        assert report.unreachable_count == 0

    def test_validate_workflow_with_warnings(self) -> None:
        """Test validate_workflow returns report with warnings."""
        metadata = WorkflowMetadata(
            workflow_class="TestWorkflow",
            workflow_run_method="run",
            activities=[
                Activity("used", 10),
                Activity("orphan", 20),
            ],
            decision_points=[],
            signal_points=[],
            source_file=Path("test.py"),
            total_paths=1
        )

        path = GraphPath("0", [
            PathStep("activity", "used"),
        ])

        context = GraphBuildingContext()
        report = validate_workflow(metadata, [path], context)

        assert report.has_warnings() is True
        assert len(report.warnings) == 1
        assert report.warnings[0].activity_name == "orphan"
        assert report.unreachable_count == 1

    def test_validate_workflow_suppressed(self) -> None:
        """Test validate_workflow returns empty report when validation suppressed."""
        metadata = WorkflowMetadata(
            workflow_class="TestWorkflow",
            workflow_run_method="run",
            activities=[
                Activity("used", 10),
                Activity("orphan", 20),
            ],
            decision_points=[],
            signal_points=[],
            source_file=Path("test.py"),
            total_paths=1
        )

        path = GraphPath("0", [
            PathStep("activity", "used"),
        ])

        # Suppress validation
        context = GraphBuildingContext(suppress_validation=True)
        report = validate_workflow(metadata, [path], context)

        # Even though orphan is unreachable, validation is suppressed
        assert report.has_warnings() is False
        assert len(report.warnings) == 0
        assert report.unreachable_count == 0

    def test_validate_workflow_statistics(self) -> None:
        """Test validate_workflow correctly calculates report statistics."""
        metadata = WorkflowMetadata(
            workflow_class="TestWorkflow",
            workflow_run_method="run",
            activities=[
                Activity("a", 10),
                Activity("b", 20),
                Activity("c", 30),
                Activity("d", 40),
                Activity("e", 50),
            ],
            decision_points=[],
            signal_points=[],
            source_file=Path("test.py"),
            total_paths=4
        )

        # Create 4 paths (matching metadata.total_paths)
        paths = [
            GraphPath("0", [PathStep("activity", "a"), PathStep("activity", "b")]),
            GraphPath("1", [PathStep("activity", "a"), PathStep("activity", "b")]),
            GraphPath("2", [PathStep("activity", "a"), PathStep("activity", "b")]),
            GraphPath("3", [PathStep("activity", "a"), PathStep("activity", "b")]),
        ]

        context = GraphBuildingContext()
        report = validate_workflow(metadata, paths, context)

        # 5 activities total, 2 called, 3 unreachable, 4 paths
        assert report.total_activities == 5
        assert report.total_paths == 4
        assert report.unreachable_count == 3
        assert len(report.warnings) == 3


class TestWarningSeverity:
    """Tests for WarningSeverity enum."""

    def test_severity_enum_values(self) -> None:
        """Test WarningSeverity enum has expected values."""
        assert WarningSeverity.INFO.value == "info"
        assert WarningSeverity.WARNING.value == "warning"
        assert WarningSeverity.ERROR.value == "error"

    def test_severity_enum_comparison(self) -> None:
        """Test WarningSeverity enum members are comparable."""
        assert WarningSeverity.INFO == WarningSeverity.INFO
        assert WarningSeverity.WARNING != WarningSeverity.ERROR
