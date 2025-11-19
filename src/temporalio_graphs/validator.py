"""Validation logic for workflow graph quality checks.

This module provides validation functions to detect potential issues in workflow
definitions, such as unreachable activities (activities defined but never called
in any execution path). Validation produces warnings, not errors, and never
prevents graph generation.

Example:
    >>> from temporalio_graphs import analyze_workflow, GraphBuildingContext
    >>> context = GraphBuildingContext()
    >>> result = analyze_workflow("workflow.py", context)
    >>> # If unreachable activities exist, validation report appears in output
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from temporalio_graphs._internal.graph_models import WorkflowMetadata
from temporalio_graphs.context import GraphBuildingContext
from temporalio_graphs.path import GraphPath


class WarningSeverity(Enum):
    """Severity level for validation warnings.

    Attributes:
        INFO: Informational message that may help improve workflow quality.
        WARNING: Potential issue that should be reviewed but doesn't prevent execution.
        ERROR: Serious issue that may cause runtime failures (future use).
    """

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class ValidationWarning:
    """Represents a single validation warning for a workflow quality issue.

    A validation warning indicates a potential problem in the workflow definition,
    such as an unreachable activity or suspicious pattern. Warnings are informational
    and do not prevent graph generation.

    Args:
        severity: Severity level (INFO, WARNING, ERROR).
        category: Warning category identifier (e.g., "unreachable", "unused").
        message: Human-readable description of the issue.
        file_path: Path to source file where issue was detected.
        line: Line number where issue occurs (0 if unknown).
        activity_name: Name of activity involved in the issue (None if not activity-related).
        suggestion: Optional suggestion for how to fix the issue.

    Example:
        >>> warning = ValidationWarning(
        ...     severity=WarningSeverity.WARNING,
        ...     category="unreachable",
        ...     message="Activity is defined but never called in any execution path",
        ...     file_path=Path("workflow.py"),
        ...     line=42,
        ...     activity_name="special_handling",
        ...     suggestion="Remove unused activity or check workflow logic"
        ... )
        >>> print(warning.format())  # doctest: +ELLIPSIS
        ⚠️ [UNREACHABLE] Activity is defined but never called in any execution path...
           Suggestion: Remove unused activity or check workflow logic
    """

    severity: WarningSeverity
    category: str
    message: str
    file_path: Path
    line: int
    activity_name: str | None = None
    suggestion: str | None = None

    def format(self) -> str:
        """Format warning as human-readable string with icon and location.

        Returns:
            Formatted warning string with icon, category, message, location, and suggestion.

        Example:
            >>> warning = ValidationWarning(
            ...     severity=WarningSeverity.WARNING,
            ...     category="unreachable",
            ...     message="Activity is defined but never called",
            ...     file_path=Path("workflow.py"),
            ...     line=42,
            ...     activity_name="my_activity",
            ...     suggestion="Remove unused activity"
            ... )
            >>> print(warning.format())
            ⚠️ [UNREACHABLE] Activity is defined but never called: 'my_activity' at workflow.py:42
               Suggestion: Remove unused activity
        """
        # Choose icon based on severity
        icon = "⚠️" if self.severity == WarningSeverity.WARNING else "ℹ️"

        # Build message with activity name if provided
        message_parts = [self.message]
        if self.activity_name:
            message_parts.append(f": '{self.activity_name}'")

        # Add location
        if self.line > 0:
            location = f"{self.file_path.name}:{self.line}"
        else:
            location = str(self.file_path.name)
        message_parts.append(f" at {location}")

        formatted = f"{icon} [{self.category.upper()}] {''.join(message_parts)}"

        # Add suggestion on new line with indentation
        if self.suggestion:
            formatted += f"\n   Suggestion: {self.suggestion}"

        return formatted


@dataclass(frozen=True)
class ValidationReport:
    """Contains validation results for a workflow analysis.

    A validation report aggregates all warnings detected during workflow validation,
    along with summary statistics about the workflow structure.

    Args:
        warnings: List of ValidationWarning objects (empty if no issues).
        total_activities: Total number of activities defined in workflow.
        total_paths: Total number of execution paths generated.
        unreachable_count: Number of unreachable activities detected.
        unused_count: Number of unused activities detected (future use).

    Example:
        >>> warnings = [
        ...     ValidationWarning(
        ...         severity=WarningSeverity.WARNING,
        ...         category="unreachable",
        ...         message="Activity never called",
        ...         file_path=Path("workflow.py"),
        ...         line=42,
        ...         activity_name="orphan_activity",
        ...         suggestion="Remove or use this activity"
        ...     )
        ... ]
        >>> report = ValidationReport(
        ...     warnings=warnings,
        ...     total_activities=5,
        ...     total_paths=4,
        ...     unreachable_count=1,
        ...     unused_count=0
        ... )
        >>> assert report.has_warnings() is True
        >>> print(report.format())
        --- Validation Report ---
        Total Paths: 4
        Total Activities: 5
        Warnings: 1
        <BLANKLINE>
        ⚠️ [UNREACHABLE] Activity never called: 'orphan_activity' at workflow.py:42
           Suggestion: Remove or use this activity
    """

    warnings: list[ValidationWarning]
    total_activities: int
    total_paths: int
    unreachable_count: int
    unused_count: int = 0  # Future use

    def has_warnings(self) -> bool:
        """Check if report contains any warnings.

        Returns:
            True if warnings list is non-empty, False otherwise.

        Example:
            >>> report = ValidationReport([], 5, 4, 0, 0)
            >>> report.has_warnings()
            False
            >>> report_with_warnings = ValidationReport([ValidationWarning(...)], 5, 4, 1, 0)
            >>> report_with_warnings.has_warnings()
            True
        """
        return len(self.warnings) > 0

    def format(self) -> str:
        """Format validation report as human-readable string.

        Returns:
            Complete formatted report with header, counts, and warnings.
            Returns empty string if no warnings exist.

        Example:
            >>> report = ValidationReport([], 5, 4, 0, 0)
            >>> report.format()
            ''
            >>> # With warnings, produces formatted report
        """
        if not self.has_warnings():
            return ""

        lines = [
            "--- Validation Report ---",
            f"Total Paths: {self.total_paths}",
            f"Total Activities: {self.total_activities}",
            f"Warnings: {len(self.warnings)}",
            "",  # Blank line before warnings
        ]

        # Add each formatted warning
        for warning in self.warnings:
            lines.append(warning.format())

        return "\n".join(lines)


def detect_unreachable_activities(
    metadata: WorkflowMetadata,
    paths: list[GraphPath]
) -> list[ValidationWarning]:
    """Detect activities defined but never called in any execution path.

    Compares the set of activities defined in the workflow AST against the set
    of activities that appear in at least one execution path. Any activity that
    is defined but never appears in a path is considered unreachable.

    Algorithm is O(n) where n is the number of activities, using set operations
    for efficiency.

    Args:
        metadata: WorkflowMetadata with activities list from AST analysis.
        paths: List of GraphPath objects representing all execution paths.

    Returns:
        List of ValidationWarning objects, one per unreachable activity.
        Returns empty list if all activities are reachable.

    Example:
        >>> from temporalio_graphs._internal.graph_models import Activity, WorkflowMetadata
        >>> from temporalio_graphs.path import GraphPath, PathStep
        >>> from pathlib import Path
        >>> # Workflow with 3 activities defined
        >>> metadata = WorkflowMetadata(
        ...     workflow_class="TestWorkflow",
        ...     workflow_run_method="run",
        ...     activities=[
        ...         Activity("activity_a", 10),
        ...         Activity("activity_b", 20),
        ...         Activity("orphan", 30),
        ...     ],
        ...     decision_points=[],
        ...     signal_points=[],
        ...     source_file=Path("test.py"),
        ...     total_paths=1
        ... )
        >>> # Only 2 activities are called in execution paths
        >>> path = GraphPath("0", [
        ...     PathStep("activity", "activity_a"),
        ...     PathStep("activity", "activity_b")
        ... ])
        >>> warnings = detect_unreachable_activities(metadata, [path])
        >>> len(warnings)
        1
        >>> warnings[0].activity_name
        'orphan'
    """
    # Edge case: no activities defined
    if not metadata.activities:
        return []

    # Edge case: no paths generated (shouldn't happen, but handle gracefully)
    if not paths:
        # All activities are unreachable if no paths exist
        early_warnings: list[ValidationWarning] = []
        for activity in metadata.activities:
            warning = ValidationWarning(
                severity=WarningSeverity.WARNING,
                category="unreachable",
                message="Activity is defined but never called in any execution path",
                file_path=metadata.source_file,
                line=activity.line_num,
                activity_name=activity.name,
                suggestion="Remove unused activity or check workflow logic"
            )
            early_warnings.append(warning)
        return early_warnings

    # Build set of defined activities: {activity_name: line_num}
    defined_activities: dict[str, int] = {
        activity.name: activity.line_num
        for activity in metadata.activities
    }

    # Build set of called activities from all paths
    called_activities: set[str] = set()
    for path in paths:
        for step in path.steps:
            if step.node_type == "activity":
                called_activities.add(step.name)

    # Find unreachable activities: defined but not called
    unreachable_names = set(defined_activities.keys()) - called_activities

    # Create warnings for each unreachable activity
    result: list[ValidationWarning] = []
    for activity_name in sorted(unreachable_names):  # Sort for deterministic output
        line_num = defined_activities[activity_name]
        warning = ValidationWarning(
            severity=WarningSeverity.WARNING,
            category="unreachable",
            message="Activity is defined but never called in any execution path",
            file_path=metadata.source_file,
            line=line_num,
            activity_name=activity_name,
            suggestion="Remove unused activity or check workflow logic"
        )
        result.append(warning)

    return result


def validate_workflow(
    metadata: WorkflowMetadata,
    paths: list[GraphPath],
    context: GraphBuildingContext
) -> ValidationReport:
    """Validate workflow quality and return report with warnings.

    Orchestrates all validation checks (unreachable activities, unused activities, etc.)
    and aggregates results into a ValidationReport. Validation can be suppressed via
    context.suppress_validation flag.

    Validation never throws exceptions and never prevents graph generation. All issues
    are reported as warnings only.

    Args:
        metadata: WorkflowMetadata from AST analysis with activities and structure.
        paths: List of GraphPath objects representing all execution paths.
        context: GraphBuildingContext with validation control flags.

    Returns:
        ValidationReport with warnings list and workflow statistics.
        Returns empty report (no warnings) if context.suppress_validation is True.

    Example:
        >>> from temporalio_graphs import GraphBuildingContext
        >>> from temporalio_graphs._internal.graph_models import WorkflowMetadata, Activity
        >>> from temporalio_graphs.path import GraphPath
        >>> from pathlib import Path
        >>> metadata = WorkflowMetadata(
        ...     workflow_class="Test",
        ...     workflow_run_method="run",
        ...     activities=[Activity("activity_a", 10)],
        ...     decision_points=[],
        ...     signal_points=[],
        ...     source_file=Path("test.py"),
        ...     total_paths=1
        ... )
        >>> paths = [GraphPath("0", [])]  # No activities called
        >>> context = GraphBuildingContext()
        >>> report = validate_workflow(metadata, paths, context)
        >>> report.has_warnings()
        True
        >>> # Suppress validation
        >>> context_suppressed = GraphBuildingContext(suppress_validation=True)
        >>> report_suppressed = validate_workflow(metadata, paths, context_suppressed)
        >>> report_suppressed.has_warnings()
        False
    """
    # Early return if validation is suppressed
    if context.suppress_validation:
        return ValidationReport(
            warnings=[],
            total_activities=len(metadata.activities),
            total_paths=len(paths),
            unreachable_count=0,
            unused_count=0
        )

    # Collect all warnings from validation checks
    all_warnings: list[ValidationWarning] = []

    # Check for unreachable activities
    unreachable_warnings = detect_unreachable_activities(metadata, paths)
    all_warnings.extend(unreachable_warnings)

    # Future: Add detect_unused_activities() check here
    # unused_warnings = detect_unused_activities(metadata, paths)
    # all_warnings.extend(unused_warnings)

    # Calculate counts for report
    unreachable_count = len([w for w in all_warnings if w.category == "unreachable"])
    unused_count = len([w for w in all_warnings if w.category == "unused"])

    # Construct and return report
    report = ValidationReport(
        warnings=all_warnings,
        total_activities=len(metadata.activities),
        total_paths=len(paths),
        unreachable_count=unreachable_count,
        unused_count=unused_count
    )

    return report
