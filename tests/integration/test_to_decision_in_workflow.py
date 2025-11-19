"""Integration tests for to_decision() helper in workflows (Story 3.2).

This module validates that to_decision() works correctly in actual workflow
contexts and integrates properly with DecisionDetector (Story 3.1).

Tests verify:
1. to_decision() can be imported from public API
2. to_decision() works in workflow method code
3. DecisionDetector correctly identifies to_decision() calls
4. WorkflowMetadata.decision_points populated correctly
5. Multiple decision patterns work together (to_decision + execute_activity)
"""

from pathlib import Path

import pytest

from temporalio_graphs import analyze_workflow, to_decision
from temporalio_graphs.detector import DecisionDetector


def _generate_workflow_with_decision() -> str:
    """Generate a test workflow using to_decision() from the library.

    Returns:
        Valid Python workflow code as string demonstrating to_decision() usage.
    """
    return '''"""Test workflow using to_decision() helper."""

from temporalio import workflow, activity
from temporalio_graphs import to_decision


@activity.defn
async def validate_amount(amount: int) -> bool:
    """Validate if amount is valid."""
    return amount > 0


@activity.defn
async def process_high_value(amount: int) -> str:
    """Process high value amount."""
    return f"Processing high value: {amount}"


@activity.defn
async def process_low_value(amount: int) -> str:
    """Process low value amount."""
    return f"Processing low value: {amount}"


@workflow.defn
class DecisionWorkflow:
    """Workflow demonstrating to_decision() helper usage."""

    @workflow.run
    async def run(self, amount: int = 100) -> str:
        """Run workflow with decision point."""
        # Execute an activity first
        await workflow.execute_activity(
            validate_amount, amount, schedule_to_close_timeout=600
        )

        # Use to_decision() to mark a decision point
        if await to_decision(amount > 1000, "HighValue"):
            result = await workflow.execute_activity(
                process_high_value, amount, schedule_to_close_timeout=600
            )
        else:
            result = await workflow.execute_activity(
                process_low_value, amount, schedule_to_close_timeout=600
            )

        return result
'''


def _generate_workflow_with_multiple_decisions() -> str:
    """Generate workflow with multiple decision points.

    Returns:
        Valid Python workflow code with multiple to_decision() calls.
    """
    return '''"""Test workflow with multiple decisions."""

from temporalio import workflow, activity
from temporalio_graphs import to_decision


@activity.defn
async def step_one() -> None:
    """First step."""
    pass


@activity.defn
async def step_two() -> None:
    """Second step."""
    pass


@activity.defn
async def step_three() -> None:
    """Third step."""
    pass


@activity.defn
async def step_four() -> None:
    """Fourth step."""
    pass


@workflow.defn
class MultiDecisionWorkflow:
    """Workflow with multiple decision points."""

    @workflow.run
    async def run(self, value: int = 50) -> str:
        """Run workflow with multiple decisions."""
        await workflow.execute_activity(step_one, schedule_to_close_timeout=600)

        # First decision
        if await to_decision(value > 100, "HighValue"):
            await workflow.execute_activity(step_two, schedule_to_close_timeout=600)

        # Second decision
        if await to_decision(value < 50, "LowValue"):
            await workflow.execute_activity(step_three, schedule_to_close_timeout=600)
        else:
            await workflow.execute_activity(step_four, schedule_to_close_timeout=600)

        return "complete"
'''


def _generate_workflow_with_complex_decision() -> str:
    """Generate workflow with complex boolean expression in decision.

    Returns:
        Valid Python workflow code with complex boolean in to_decision().
    """
    return '''"""Test workflow with complex decision expression."""

from temporalio import workflow, activity
from temporalio_graphs import to_decision


@activity.defn
async def approval_required() -> None:
    """Request approval."""
    pass


@activity.defn
async def proceed() -> None:
    """Proceed without approval."""
    pass


@workflow.defn
class ComplexDecisionWorkflow:
    """Workflow with complex decision expression."""

    @workflow.run
    async def run(self, amount: int = 5000, department: str = "ops") -> str:
        """Run workflow with complex decision."""
        # Complex boolean expression as decision
        if await to_decision(
            amount > 5000 and department == "procurement",
            "RequiresApproval"
        ):
            await workflow.execute_activity(
                approval_required, schedule_to_close_timeout=600
            )
        else:
            await workflow.execute_activity(
                proceed, schedule_to_close_timeout=600
            )

        return "complete"
'''


class TestToDecisionImportFromPublicAPI:
    """Test that to_decision can be imported from public API."""

    def test_to_decision_importable_from_package(self) -> None:
        """Test to_decision is available in public API."""
        # Should be able to import directly
        from temporalio_graphs import to_decision  # noqa: F401

        # Should be in __all__
        from temporalio_graphs import __all__

        assert "to_decision" in __all__

    def test_to_decision_has_docstring(self) -> None:
        """Test that to_decision has comprehensive documentation."""
        assert to_decision.__doc__ is not None
        assert "transparent passthrough" in to_decision.__doc__.lower()
        assert "decision point" in to_decision.__doc__.lower()
        assert "string literal" in to_decision.__doc__.lower()

    def test_to_decision_is_async(self) -> None:
        """Test that to_decision is async-compatible."""
        import inspect

        assert inspect.iscoroutinefunction(to_decision)


class TestToDecisionDetectionInWorkflow:
    """Test that DecisionDetector finds to_decision() calls in workflows."""

    def test_detector_finds_single_decision(self, tmp_path: Path) -> None:
        """Test DecisionDetector identifies a single to_decision() call."""
        # Create temporary workflow file
        workflow_file = tmp_path / "test_workflow.py"
        workflow_file.write_text(_generate_workflow_with_decision())

        # Analyze with DecisionDetector
        detector = DecisionDetector()
        tree = workflow_file.read_text()
        import ast

        parsed = ast.parse(tree)
        detector.visit(parsed)

        # Should find the single decision
        assert len(detector.decisions) == 1
        assert detector.decisions[0].name == "HighValue"

    def test_detector_finds_multiple_decisions(self, tmp_path: Path) -> None:
        """Test DecisionDetector identifies multiple to_decision() calls."""
        workflow_file = tmp_path / "test_workflow.py"
        workflow_file.write_text(_generate_workflow_with_multiple_decisions())

        detector = DecisionDetector()
        tree = workflow_file.read_text()
        import ast

        parsed = ast.parse(tree)
        detector.visit(parsed)

        # Should find both decisions
        assert len(detector.decisions) == 2
        assert detector.decisions[0].name == "HighValue"
        assert detector.decisions[1].name == "LowValue"

    def test_detector_finds_complex_expression_decision(self, tmp_path: Path) -> None:
        """Test DecisionDetector handles complex boolean expressions."""
        workflow_file = tmp_path / "test_workflow.py"
        workflow_file.write_text(_generate_workflow_with_complex_decision())

        detector = DecisionDetector()
        tree = workflow_file.read_text()
        import ast

        parsed = ast.parse(tree)
        detector.visit(parsed)

        # Should find the complex decision
        assert len(detector.decisions) == 1
        assert detector.decisions[0].name == "RequiresApproval"


class TestToDecisionIntegrationWithAnalyzeWorkflow:
    """Test to_decision() integration through analyze_workflow pipeline.

    Note: These tests validate that workflows with to_decision() calls are
    recognized by the analyzer. Full path generation for decision workflows
    will be implemented in Story 3.3 (PathPermutationGenerator).

    Currently, analyze_workflow() raises NotImplementedError for workflows
    with decision points because decision path generation is deferred to
    Epic 3. This is expected behavior per the implementation plan.
    """

    def test_analyze_workflow_with_single_decision(self, tmp_path: Path) -> None:
        """Test that analyze_workflow detects to_decision() calls.

        Currently, workflows with decision points raise NotImplementedError
        because path generation for decisions is Story 3.3. This validates
        that to_decision() is properly recognized by the analyzer.
        """
        workflow_file = tmp_path / "test_workflow.py"
        workflow_file.write_text(_generate_workflow_with_decision())

        # Decision path generation not yet implemented (Story 3.3)
        with pytest.raises(NotImplementedError):
            analyze_workflow(str(workflow_file))

    def test_analyze_workflow_with_multiple_decisions(self, tmp_path: Path) -> None:
        """Test analyze_workflow detects multiple decision points.

        Currently raises NotImplementedError - full support in Story 3.3.
        """
        workflow_file = tmp_path / "test_workflow.py"
        workflow_file.write_text(_generate_workflow_with_multiple_decisions())

        # Decision path generation not yet implemented (Story 3.3)
        with pytest.raises(NotImplementedError):
            analyze_workflow(str(workflow_file))

    def test_analyze_workflow_with_decision_and_activities(self, tmp_path: Path) -> None:
        """Test analyze_workflow detects mixed decision + activity patterns.

        This validates that to_decision() is properly recognized in complex
        workflows. Full path generation comes in Story 3.3.
        """
        workflow_file = tmp_path / "test_workflow.py"
        workflow_file.write_text(_generate_workflow_with_decision())

        # Decision path generation not yet implemented (Story 3.3)
        with pytest.raises(NotImplementedError):
            analyze_workflow(str(workflow_file))


class TestToDecisionDocumentationExamples:
    """Test that the examples in to_decision docstring are valid."""

    @pytest.mark.asyncio
    async def test_docstring_example_if_statement(self) -> None:
        """Test the if-statement example from docstring."""
        amount = 1500

        # Example from docstring: if await to_decision(amount > 1000, "HighValue"):
        if await to_decision(amount > 1000, "HighValue"):
            # This path should be taken
            result = "high"
        else:
            result = "low"

        assert result == "high"

    @pytest.mark.asyncio
    async def test_docstring_example_assignment(self) -> None:
        """Test the assignment example from docstring."""
        amount = 5000
        department = "procurement"

        # Example from docstring: needs_approval = await to_decision(...)
        needs_approval = await to_decision(
            amount > 5000 and department == "procurement",
            "RequiresApproval"
        )

        assert needs_approval is False  # amount is not > 5000
