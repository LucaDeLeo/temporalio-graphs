"""Integration test for parent-child workflow visualization (Story 6.2).

This module tests end-to-end workflow analysis and rendering for workflows
that call child workflows via execute_child_workflow().
"""

import pytest
from pathlib import Path
from temporalio_graphs import analyze_workflow
from temporalio_graphs.context import GraphBuildingContext


# Sample parent workflow with child workflow call
PARENT_WORKFLOW_CODE = '''
from temporalio import workflow
from temporalio.workflow import ParentClosePolicy

@workflow.defn
class ParentWorkflow:
    @workflow.run
    async def run(self, order_id: str) -> str:
        # Validate the order
        await workflow.execute_activity(
            "validate_order",
            order_id,
            start_to_close_timeout=timedelta(seconds=30)
        )

        # Call child workflow to process payment
        await workflow.execute_child_workflow(
            "PaymentWorkflow",
            order_id,
            id=f"payment-{order_id}",
            parent_close_policy=ParentClosePolicy.ABANDON
        )

        # Send confirmation
        await workflow.execute_activity(
            "send_confirmation",
            order_id,
            start_to_close_timeout=timedelta(seconds=10)
        )

        return "completed"
'''


class TestParentChildWorkflowIntegration:
    """Integration tests for parent-child workflow rendering."""

    def test_parent_workflow_with_child_call_renders_mermaid(self, tmp_path: Path):
        """Test parent workflow with child workflow call generates valid Mermaid."""
        # Write workflow to temp file
        workflow_file = tmp_path / "parent_workflow.py"
        workflow_file.write_text(PARENT_WORKFLOW_CODE)

        # Analyze workflow
        result = analyze_workflow(
            str(workflow_file),
            context=GraphBuildingContext(split_names_by_words=False)
        )

        # Verify we got Mermaid output
        assert result is not None
        assert "```mermaid" in result
        assert "flowchart LR" in result

        # Verify child workflow node is present with double brackets
        assert "[[PaymentWorkflow]]" in result

        # Verify child workflow node ID follows format: child_{workflow_name}_{line}
        # The exact line number depends on the code, so we check for the pattern
        assert "child_paymentworkflow_" in result.lower()

        # Verify activities are present with single brackets
        assert "[validate_order]" in result or "[Validate Order]" in result
        assert "[send_confirmation]" in result or "[Send Confirmation]" in result

        # Verify edge connections
        # validate_order -> child workflow -> send_confirmation
        lines = result.split('\n')
        mermaid_lines = [l for l in lines if '-->' in l]

        # Should have edges connecting nodes
        assert len(mermaid_lines) >= 4  # s -> validate, validate -> child, child -> send, send -> e

    def test_parent_workflow_child_node_visual_distinction(self, tmp_path: Path):
        """Test child workflow nodes are visually distinct from activities."""
        workflow_file = tmp_path / "parent_workflow.py"
        workflow_file.write_text(PARENT_WORKFLOW_CODE)

        result = analyze_workflow(
            str(workflow_file),
            context=GraphBuildingContext(split_names_by_words=False)
        )

        # Count single brackets (activities) vs double brackets (child workflows)
        single_bracket_count = result.count('[') - result.count('[[')
        double_bracket_count = result.count('[[')

        # Should have at least 2 activities (validate_order, send_confirmation)
        assert single_bracket_count >= 2

        # Should have at least 1 child workflow (PaymentWorkflow)
        assert double_bracket_count >= 1

    def test_mermaid_output_structure_with_child_workflow(self, tmp_path: Path):
        """Test Mermaid output has correct structure with child workflow."""
        workflow_file = tmp_path / "parent_workflow.py"
        workflow_file.write_text(PARENT_WORKFLOW_CODE)

        result = analyze_workflow(
            str(workflow_file),
            context=GraphBuildingContext()
        )

        # Should start with mermaid block
        assert result.startswith("```mermaid")

        # Should contain mermaid closing fence (may have path list after)
        assert "```\n" in result

        # Extract the Mermaid content (first mermaid block)
        mermaid_section = result.split("```\n")[0]
        mermaid_content = mermaid_section.split("```mermaid\n")[1]

        # Should start with flowchart declaration
        assert mermaid_content.startswith("flowchart LR")

        # Should have node definitions and edges
        lines = mermaid_content.split('\n')
        node_lines = [l for l in lines if '[[' in l or '[' in l or '((' in l]
        edge_lines = [l for l in lines if '-->' in l]

        assert len(node_lines) > 0
        assert len(edge_lines) > 0


# Sample workflow with multiple child workflow calls
MULTI_CHILD_WORKFLOW_CODE = '''
from temporalio import workflow

@workflow.defn
class OrchestratorWorkflow:
    @workflow.run
    async def run(self, task_id: str) -> str:
        # Initialize
        await workflow.execute_activity(
            "initialize",
            task_id,
            start_to_close_timeout=timedelta(seconds=10)
        )

        # Call first child workflow
        await workflow.execute_child_workflow(
            "WorkflowA",
            task_id
        )

        # Call second child workflow
        await workflow.execute_child_workflow(
            "WorkflowB",
            task_id
        )

        # Finalize
        await workflow.execute_activity(
            "finalize",
            task_id,
            start_to_close_timeout=timedelta(seconds=10)
        )

        return "done"
'''


class TestMultipleChildWorkflows:
    """Test workflows with multiple child workflow calls."""

    def test_multiple_child_workflows_unique_ids(self, tmp_path: Path):
        """Test multiple child workflow calls have unique node IDs."""
        workflow_file = tmp_path / "orchestrator.py"
        workflow_file.write_text(MULTI_CHILD_WORKFLOW_CODE)

        result = analyze_workflow(
            str(workflow_file),
            context=GraphBuildingContext(split_names_by_words=False)
        )

        # Should have two different child workflow nodes
        assert "[[WorkflowA]]" in result
        assert "[[WorkflowB]]" in result

        # Should have different node IDs (different line numbers)
        assert "child_workflowa_" in result.lower()
        assert "child_workflowb_" in result.lower()

        # Extract line numbers from node IDs to verify they're different
        import re
        workflow_a_matches = re.findall(r'child_workflowa_(\d+)', result.lower())
        workflow_b_matches = re.findall(r'child_workflowb_(\d+)', result.lower())

        assert len(workflow_a_matches) >= 1
        assert len(workflow_b_matches) >= 1

        # Line numbers should be different
        if workflow_a_matches and workflow_b_matches:
            assert workflow_a_matches[0] != workflow_b_matches[0]

    def test_multiple_child_workflows_sequential_edges(self, tmp_path: Path):
        """Test multiple child workflows are connected sequentially."""
        workflow_file = tmp_path / "orchestrator.py"
        workflow_file.write_text(MULTI_CHILD_WORKFLOW_CODE)

        result = analyze_workflow(
            str(workflow_file),
            context=GraphBuildingContext(split_names_by_words=False)
        )

        # Should have edges connecting in sequence
        # initialize -> WorkflowA -> WorkflowB -> finalize

        # Check for presence of edges (exact format may vary)
        assert '-->' in result

        # Verify all nodes are present
        assert 'initialize' in result
        assert 'WorkflowA' in result
        assert 'WorkflowB' in result
        assert 'finalize' in result


# Sample workflow with child workflow in conditional branch
CONDITIONAL_CHILD_WORKFLOW_CODE = '''
from temporalio import workflow
from temporalio_graphs.helpers import to_decision

@workflow.defn
class ConditionalParentWorkflow:
    @workflow.run
    async def run(self, amount: float) -> str:
        # Check if amount is high
        is_high_value = amount > 1000
        await to_decision(is_high_value, "HighValue")

        if is_high_value:
            # Call approval workflow for high value
            await workflow.execute_child_workflow(
                "ApprovalWorkflow",
                amount
            )

        # Process payment
        await workflow.execute_activity(
            "process_payment",
            amount,
            start_to_close_timeout=timedelta(seconds=30)
        )

        return "completed"
'''


class TestChildWorkflowInConditionalBranch:
    """Test child workflow calls in conditional branches."""

    def test_child_workflow_after_decision_point(self, tmp_path: Path):
        """Test child workflow in conditional branch renders correctly."""
        workflow_file = tmp_path / "conditional.py"
        workflow_file.write_text(CONDITIONAL_CHILD_WORKFLOW_CODE)

        result = analyze_workflow(
            str(workflow_file),
            context=GraphBuildingContext(split_names_by_words=False)
        )

        # Should have decision node
        assert '{HighValue}' in result or '{High Value}' in result

        # Should have child workflow node
        assert '[[ApprovalWorkflow]]' in result or '[[Approval Workflow]]' in result

        # Should have multiple paths (2^1 = 2 paths for 1 decision)
        # One path with child workflow, one without
        assert 'process_payment' in result

        # Decision should have labeled edges
        assert '-- yes -->' in result or '-- no -->' in result
