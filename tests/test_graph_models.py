"""Unit tests for internal graph models."""

from pathlib import Path

from temporalio_graphs._internal.graph_models import (
    GraphEdge,
    GraphNode,
    NodeType,
    SignalHandler,
    WorkflowMetadata,
)


def test_node_type_enum_values() -> None:
    """Verify NodeType enum has all 7 values with correct string representations."""
    assert NodeType.START.value == "start"
    assert NodeType.END.value == "end"
    assert NodeType.ACTIVITY.value == "activity"
    assert NodeType.DECISION.value == "decision"
    assert NodeType.SIGNAL.value == "signal"
    assert NodeType.CHILD_WORKFLOW.value == "child_workflow"
    assert NodeType.EXTERNAL_SIGNAL.value == "external_signal"

    # Verify all 7 members exist (Epic 7 adds EXTERNAL_SIGNAL)
    assert len(NodeType) == 7


def test_graph_node_to_mermaid_start() -> None:
    """GraphNode with START type renders with double parentheses."""
    node = GraphNode("s", NodeType.START, "Start", source_line=None)
    assert node.to_mermaid() == "s((Start))"


def test_graph_node_to_mermaid_end() -> None:
    """GraphNode with END type renders with double parentheses."""
    node = GraphNode("e", NodeType.END, "End", source_line=None)
    assert node.to_mermaid() == "e((End))"


def test_graph_node_to_mermaid_activity() -> None:
    """GraphNode with ACTIVITY type renders with square brackets."""
    node = GraphNode("1", NodeType.ACTIVITY, "ValidateInput", source_line=42)
    assert node.to_mermaid() == "1[ValidateInput]"


def test_graph_node_to_mermaid_decision() -> None:
    """GraphNode with DECISION type renders with curly braces."""
    node = GraphNode("0", NodeType.DECISION, "HighValue", source_line=55)
    assert node.to_mermaid() == "0{HighValue}"


def test_graph_node_to_mermaid_signal() -> None:
    """GraphNode with SIGNAL type renders with double curly braces."""
    node = GraphNode("2", NodeType.SIGNAL, "WaitApproval", source_line=67)
    assert node.to_mermaid() == "2{{WaitApproval}}"


def test_graph_node_to_mermaid_external_signal() -> None:
    """GraphNode with EXTERNAL_SIGNAL type renders with trapezoid syntax."""
    node = GraphNode("ext_sig_ship_order_50", NodeType.EXTERNAL_SIGNAL,
                     "Signal 'ship_order'", source_line=50)
    assert node.to_mermaid() == "ext_sig_ship_order_50[/Signal 'ship_order'\\]"


def test_graph_edge_to_mermaid_no_label() -> None:
    """GraphEdge without label renders as simple arrow."""
    edge = GraphEdge("s", "1", None)
    assert edge.to_mermaid() == "s --> 1"


def test_graph_edge_to_mermaid_with_label() -> None:
    """GraphEdge with label renders with labeled arrow."""
    edge = GraphEdge("0", "1", "yes")
    assert edge.to_mermaid() == "0 -- yes --> 1"


def test_graph_edge_hash_for_deduplication() -> None:
    """Create identical edges, verify hash equality and set deduplication."""
    edge1 = GraphEdge("s", "1", None)
    edge2 = GraphEdge("s", "1", None)
    edge3 = GraphEdge("s", "2", None)  # Different to_node
    edge4 = GraphEdge("s", "1", "label")  # Different label

    # Identical edges should have same hash
    assert hash(edge1) == hash(edge2)
    assert edge1 == edge2

    # Different edges should not be equal
    assert edge1 != edge3
    assert edge1 != edge4

    # Set deduplication should work
    edges = {edge1, edge2, edge3, edge4}
    assert len(edges) == 3  # edge1 and edge2 collapsed into one


def test_workflow_metadata_calculate_paths() -> None:
    """Verify calculate_total_paths uses 2^(decisions+signals) formula."""
    # Linear workflow: 2^0 = 1 path
    assert WorkflowMetadata.calculate_total_paths(0, 0) == 1

    # 2 decisions: 2^2 = 4 paths
    assert WorkflowMetadata.calculate_total_paths(2, 0) == 4

    # 2 decisions + 1 signal: 2^3 = 8 paths
    assert WorkflowMetadata.calculate_total_paths(2, 1) == 8

    # 3 decisions + 2 signals: 2^5 = 32 paths
    assert WorkflowMetadata.calculate_total_paths(3, 2) == 32

    # 10 decisions (max default): 2^10 = 1024 paths
    assert WorkflowMetadata.calculate_total_paths(10, 0) == 1024


def test_workflow_metadata_instantiation() -> None:
    """Create WorkflowMetadata instance and verify all fields."""
    metadata = WorkflowMetadata(
        workflow_class="MoneyTransferWorkflow",
        workflow_run_method="run",
        activities=["Withdraw", "CurrencyConvert", "Deposit"],
        decision_points=["NeedToConvert", "IsTFN_Known"],
        signal_points=[],
        source_file=Path("workflows.py"),
        total_paths=4,
    )

    assert metadata.workflow_class == "MoneyTransferWorkflow"
    assert metadata.workflow_run_method == "run"
    assert len(metadata.activities) == 3
    assert len(metadata.decision_points) == 2
    assert len(metadata.signal_points) == 0
    assert metadata.source_file == Path("workflows.py")
    assert metadata.total_paths == 4
    # Verify default value for signal_handlers
    assert metadata.signal_handlers == ()


def test_workflow_metadata_signal_handlers_default() -> None:
    """Verify signal_handlers defaults to empty tuple when not provided."""
    metadata = WorkflowMetadata(
        workflow_class="TestWorkflow",
        workflow_run_method="run",
        activities=[],
        decision_points=[],
        signal_points=[],
        source_file=Path("test.py"),
        total_paths=1,
    )

    assert metadata.signal_handlers == ()
    assert isinstance(metadata.signal_handlers, tuple)


def test_workflow_metadata_signal_handlers_populated() -> None:
    """Verify signal_handlers correctly stores SignalHandler tuple."""
    handler1 = SignalHandler(
        signal_name="ship_order",
        method_name="ship_order",
        workflow_class="ShippingWorkflow",
        source_line=67,
        node_id="sig_handler_ship_order_67",
    )
    handler2 = SignalHandler(
        signal_name="cancel_order",
        method_name="cancel",
        workflow_class="ShippingWorkflow",
        source_line=85,
        node_id="sig_handler_cancel_order_85",
    )

    metadata = WorkflowMetadata(
        workflow_class="ShippingWorkflow",
        workflow_run_method="run",
        activities=[],
        decision_points=[],
        signal_points=[],
        source_file=Path("shipping.py"),
        total_paths=1,
        signal_handlers=(handler1, handler2),
    )

    assert len(metadata.signal_handlers) == 2
    assert metadata.signal_handlers[0].signal_name == "ship_order"
    assert metadata.signal_handlers[1].signal_name == "cancel_order"
    assert metadata.signal_handlers[0].workflow_class == "ShippingWorkflow"


def test_workflow_metadata_signal_handlers_immutable() -> None:
    """Verify signal_handlers tuple is immutable (cannot be modified)."""
    handler = SignalHandler(
        signal_name="process",
        method_name="process",
        workflow_class="TestWorkflow",
        source_line=10,
        node_id="sig_handler_process_10",
    )

    metadata = WorkflowMetadata(
        workflow_class="TestWorkflow",
        workflow_run_method="run",
        activities=[],
        decision_points=[],
        signal_points=[],
        source_file=Path("test.py"),
        total_paths=1,
        signal_handlers=(handler,),
    )

    # Verify tuple is immutable - attempting assignment raises TypeError
    import pytest
    with pytest.raises(TypeError):
        metadata.signal_handlers[0] = handler  # type: ignore[index]

    # Verify tuple has no append method (unlike list)
    assert not hasattr(metadata.signal_handlers, "append")
