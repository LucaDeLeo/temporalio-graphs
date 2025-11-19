"""Tests for child workflow node rendering (Story 6.2).

This module tests the rendering of child workflow nodes with Mermaid's
double-bracket subroutine syntax.
"""

import pytest

from temporalio_graphs._internal.graph_models import GraphNode, NodeType
from temporalio_graphs.context import GraphBuildingContext
from temporalio_graphs.path import GraphPath
from temporalio_graphs.renderer import MermaidRenderer


class TestGraphNodeChildWorkflowRendering:
    """Test GraphNode.to_mermaid() for child workflow nodes."""

    def test_child_workflow_node_double_bracket_syntax(self):
        """Test child workflow nodes render with double brackets [[]]."""
        node = GraphNode(
            node_id="child_paymentworkflow_45",
            node_type=NodeType.CHILD_WORKFLOW,
            display_name="PaymentWorkflow"
        )
        result = node.to_mermaid()
        assert result == "child_paymentworkflow_45[[PaymentWorkflow]]"

    def test_child_workflow_node_with_word_splitting(self):
        """Test child workflow node display name can be word-split."""
        node = GraphNode(
            node_id="child_processorderworkflow_100",
            node_type=NodeType.CHILD_WORKFLOW,
            display_name="Process Order Workflow"
        )
        result = node.to_mermaid()
        assert result == "child_processorderworkflow_100[[Process Order Workflow]]"

    def test_child_workflow_node_visual_distinction_from_activity(self):
        """Test child workflows use [[]] while activities use []."""
        activity_node = GraphNode(
            node_id="1",
            node_type=NodeType.ACTIVITY,
            display_name="ProcessOrder"
        )
        child_workflow_node = GraphNode(
            node_id="child_orderworkflow_50",
            node_type=NodeType.CHILD_WORKFLOW,
            display_name="OrderWorkflow"
        )

        activity_result = activity_node.to_mermaid()
        child_result = child_workflow_node.to_mermaid()

        # Activities use single brackets
        assert "[ProcessOrder]" in activity_result
        assert "[[" not in activity_result

        # Child workflows use double brackets
        assert "[[OrderWorkflow]]" in child_result
        assert child_result != activity_result

    def test_child_workflow_node_deterministic_id_format(self):
        """Test node IDs follow child_{workflow_name}_{line} format."""
        node = GraphNode(
            node_id="child_myworkflow_42",
            node_type=NodeType.CHILD_WORKFLOW,
            display_name="MyWorkflow"
        )
        result = node.to_mermaid()

        # Node ID should be in the format child_name_line
        assert result.startswith("child_myworkflow_42[[")
        assert "child_myworkflow_42[[MyWorkflow]]" == result


class TestGraphPathChildWorkflowIntegration:
    """Test GraphPath.add_child_workflow() method."""

    def test_add_child_workflow_returns_deterministic_id(self):
        """Test add_child_workflow returns deterministic node ID."""
        path = GraphPath(path_id="path_0")
        node_id = path.add_child_workflow("PaymentWorkflow", 45)

        assert node_id == "child_paymentworkflow_45"

    def test_add_child_workflow_stores_step_correctly(self):
        """Test add_child_workflow stores PathStep with correct data."""
        path = GraphPath(path_id="path_0")
        path.add_child_workflow("OrderWorkflow", 100)

        assert len(path.steps) == 1
        step = path.steps[0]

        assert step.node_type == 'child_workflow'
        assert step.name == "OrderWorkflow"
        assert step.line_number == 100

    def test_multiple_child_workflows_have_unique_ids(self):
        """Test multiple child workflow calls render with unique IDs."""
        path = GraphPath(path_id="path_0")
        id1 = path.add_child_workflow("WorkflowA", 10)
        id2 = path.add_child_workflow("WorkflowB", 20)
        id3 = path.add_child_workflow("WorkflowA", 30)  # Same workflow, different line

        assert id1 == "child_workflowa_10"
        assert id2 == "child_workflowb_20"
        assert id3 == "child_workflowa_30"
        assert id1 != id2
        assert id1 != id3
        assert id2 != id3

    def test_child_workflow_id_lowercase_for_consistency(self):
        """Test child workflow IDs use lowercase workflow names."""
        path = GraphPath(path_id="path_0")
        id1 = path.add_child_workflow("MyWorkflow", 50)
        id2 = path.add_child_workflow("ANOTHER", 60)

        assert id1 == "child_myworkflow_50"
        assert id2 == "child_another_60"


class TestMermaidRendererChildWorkflowNodes:
    """Test MermaidRenderer handles child workflow nodes correctly."""

    def test_child_workflow_in_linear_path(self):
        """Test child workflow renders correctly in linear path."""
        renderer = MermaidRenderer()
        context = GraphBuildingContext()

        path = GraphPath(path_id="path_0")
        path.add_activity("ValidateInput")
        path.add_child_workflow("PaymentWorkflow", 45)
        path.add_activity("SendConfirmation")

        result = renderer.to_mermaid([path], context)

        # Check for child workflow node with double brackets (word splitting enabled by default)
        assert "child_paymentworkflow_45[[Payment Workflow]]" in result

        # Check for correct edge connections
        assert "ValidateInput --> child_paymentworkflow_45" in result or "Validate Input --> child_paymentworkflow_45" in result
        assert "child_paymentworkflow_45 --> SendConfirmation" in result or "child_paymentworkflow_45 --> Send Confirmation" in result

    def test_child_workflow_with_word_splitting(self):
        """Test child workflow names respect word splitting setting."""
        renderer = MermaidRenderer()
        context = GraphBuildingContext(split_names_by_words=True)

        path = GraphPath(path_id="path_0")
        path.add_child_workflow("ProcessOrderWorkflow", 50)

        result = renderer.to_mermaid([path], context)

        # Display name should be word-split
        assert "child_processorderworkflow_50[[Process Order Workflow]]" in result

    def test_child_workflow_without_word_splitting(self):
        """Test child workflow names with word splitting disabled."""
        renderer = MermaidRenderer()
        context = GraphBuildingContext(split_names_by_words=False)

        path = GraphPath(path_id="path_0")
        path.add_child_workflow("ProcessOrderWorkflow", 50)

        result = renderer.to_mermaid([path], context)

        # Display name should NOT be word-split
        assert "child_processorderworkflow_50[[ProcessOrderWorkflow]]" in result

    def test_multiple_child_workflows_in_same_path(self):
        """Test multiple child workflows render with unique IDs."""
        renderer = MermaidRenderer()
        context = GraphBuildingContext(split_names_by_words=False)

        path = GraphPath(path_id="path_0")
        path.add_child_workflow("WorkflowA", 10)
        path.add_child_workflow("WorkflowB", 20)
        path.add_child_workflow("WorkflowC", 30)

        result = renderer.to_mermaid([path], context)

        # All three child workflows should be present with unique IDs
        assert "child_workflowa_10[[WorkflowA]]" in result
        assert "child_workflowb_20[[WorkflowB]]" in result
        assert "child_workflowc_30[[WorkflowC]]" in result

        # Check sequential edges
        assert "child_workflowa_10 --> child_workflowb_20" in result
        assert "child_workflowb_20 --> child_workflowc_30" in result

    def test_child_workflow_mixed_with_activities(self):
        """Test child workflows and activities together in path."""
        renderer = MermaidRenderer()
        context = GraphBuildingContext(split_names_by_words=False)

        path = GraphPath(path_id="path_0")
        path.add_activity("Activity1")
        path.add_child_workflow("ChildWorkflow", 50)
        path.add_activity("Activity2")

        result = renderer.to_mermaid([path], context)

        # Activities use single brackets
        assert "Activity1[Activity1]" in result
        assert "Activity2[Activity2]" in result

        # Child workflow uses double brackets
        assert "child_childworkflow_50[[ChildWorkflow]]" in result

        # Check edge sequence
        assert "Activity1 --> child_childworkflow_50" in result
        assert "child_childworkflow_50 --> Activity2" in result

    def test_child_workflow_node_deduplication_across_paths(self):
        """Test same child workflow on different paths is deduplicated."""
        renderer = MermaidRenderer()
        context = GraphBuildingContext(split_names_by_words=False)

        # Two paths calling the same child workflow at the same line
        path1 = GraphPath(path_id="path_0b0")
        path1.add_activity("Activity1")
        path1.add_child_workflow("SharedWorkflow", 45)

        path2 = GraphPath(path_id="path_0b1")
        path2.add_activity("Activity2")
        path2.add_child_workflow("SharedWorkflow", 45)

        result = renderer.to_mermaid([path1, path2], context)

        # Child workflow node should appear only once
        count = result.count("child_sharedworkflow_45[[SharedWorkflow]]")
        assert count == 1

        # Both paths should reference it
        assert "Activity1 --> child_sharedworkflow_45" in result
        assert "Activity2 --> child_sharedworkflow_45" in result

    def test_child_workflow_valid_mermaid_syntax(self):
        """Test generated Mermaid with child workflow is syntactically valid."""
        renderer = MermaidRenderer()
        context = GraphBuildingContext()

        path = GraphPath(path_id="path_0")
        path.add_activity("StartActivity")
        path.add_child_workflow("MyChildWorkflow", 100)
        path.add_activity("EndActivity")

        result = renderer.to_mermaid([path], context)

        # Basic Mermaid structure checks
        assert "```mermaid" in result
        assert "flowchart LR" in result
        assert "```" in result.split("```mermaid")[1]

        # Child workflow syntax (with word splitting by default)
        assert "child_mychildworkflow_100[[My Child Workflow]]" in result

        # Should have start and end nodes
        assert "s((Start))" in result
        assert "e((End))" in result


class TestChildWorkflowWithDecisions:
    """Test child workflow nodes in paths with decisions."""

    def test_child_workflow_after_decision(self):
        """Test child workflow called after a decision point."""
        renderer = MermaidRenderer()
        context = GraphBuildingContext()

        path1 = GraphPath(path_id="path_0b0")
        path1.add_decision("d0", True, "NeedProcessing")
        path1.add_child_workflow("ProcessingWorkflow", 50)

        path2 = GraphPath(path_id="path_0b1")
        path2.add_decision("d0", False, "NeedProcessing")
        path2.add_activity("SkipProcessing")

        result = renderer.to_mermaid([path1, path2], context)

        # Child workflow should appear on true branch
        assert "d0 -- yes --> child_processingworkflow_50" in result

        # Activity should appear on false branch
        assert "d0 -- no --> SkipProcessing" in result

    def test_child_workflow_in_conditional_branch(self):
        """Test child workflow only in specific decision branch."""
        renderer = MermaidRenderer()
        context = GraphBuildingContext()

        # Path with decision followed by child workflow
        path = GraphPath(path_id="path_0b1")
        path.add_activity("Initialize")
        path.add_decision("d0", True, "RequiresSubWorkflow")
        path.add_child_workflow("SubWorkflow", 60)
        path.add_activity("Finalize")

        result = renderer.to_mermaid([path], context)

        # Check decision edge to child workflow
        assert "d0{RequiresSubWorkflow}" in result or "d0{Requires Sub Workflow}" in result
        assert "child_subworkflow_60[[SubWorkflow]]" in result or "child_subworkflow_60[[Sub Workflow]]" in result


class TestChildWorkflowEdgeCases:
    """Test edge cases for child workflow rendering."""

    def test_child_workflow_missing_line_number_raises_error(self):
        """Test rendering fails gracefully if line_number is missing."""
        renderer = MermaidRenderer()
        context = GraphBuildingContext()

        path = GraphPath(path_id="path_0")
        # Manually create a malformed step without line_number
        from temporalio_graphs.path import PathStep
        bad_step = PathStep(node_type='child_workflow', name='BadWorkflow', line_number=None)
        path.steps.append(bad_step)

        with pytest.raises(ValueError, match="missing line_number"):
            renderer.to_mermaid([path], context)

    def test_child_workflow_with_special_characters_in_name(self):
        """Test child workflow names with special characters."""
        renderer = MermaidRenderer()
        context = GraphBuildingContext()

        path = GraphPath(path_id="path_0")
        path.add_child_workflow("Workflow_V2", 70)

        result = renderer.to_mermaid([path], context)

        # Should handle underscores in workflow name
        assert "child_workflow_v2_70[[Workflow_V2]]" in result or "child_workflow_v2_70[[Workflow V2]]" in result

    def test_child_workflow_same_name_different_lines(self):
        """Test same workflow called multiple times has unique IDs."""
        renderer = MermaidRenderer()
        context = GraphBuildingContext()

        path = GraphPath(path_id="path_0")
        path.add_child_workflow("ReusableWorkflow", 10)
        path.add_activity("Intermediate")
        path.add_child_workflow("ReusableWorkflow", 20)

        result = renderer.to_mermaid([path], context)

        # Both calls should be present with different IDs
        assert "child_reusableworkflow_10[[ReusableWorkflow]]" in result or "child_reusableworkflow_10[[Reusable Workflow]]" in result
        assert "child_reusableworkflow_20[[ReusableWorkflow]]" in result or "child_reusableworkflow_20[[Reusable Workflow]]" in result

        # Sequential edges
        assert "child_reusableworkflow_10 --> Intermediate" in result
        assert "Intermediate --> child_reusableworkflow_20" in result
