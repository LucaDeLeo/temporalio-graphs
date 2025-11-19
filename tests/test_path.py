"""Unit tests for GraphPath execution path tracking."""

import pytest

from temporalio_graphs.path import GraphPath


def test_add_activity() -> None:
    """Create GraphPath, call add_activity, verify node ID and steps."""
    path = GraphPath(path_id="0")

    node_id = path.add_activity("MyActivity")

    assert node_id == "1"
    assert "MyActivity" in path.steps


def test_activity_node_id_generation() -> None:
    """Add 3 activities, verify IDs are sequential."""
    path = GraphPath(path_id="0")

    id1 = path.add_activity("ValidateInput")
    id2 = path.add_activity("ProcessOrder")
    id3 = path.add_activity("SendConfirmation")

    assert id1 == "1"
    assert id2 == "2"
    assert id3 == "3"


def test_add_decision_implementation() -> None:
    """Call add_decision, verify it records decision and returns node ID."""
    path = GraphPath(path_id="0b00")

    # add_decision should now work (Epic 3 implementation)
    node_id = path.add_decision("0", True, "HighValue")

    # Should return a node ID
    assert node_id == "1"

    # Decision should be recorded
    assert path.decisions["0"] is True

    # Decision name should be added to steps
    assert "HighValue" in path.steps


def test_add_signal_placeholder() -> None:
    """Call add_signal, verify it's a stub (NotImplementedError)."""
    path = GraphPath(path_id="0b10")

    with pytest.raises(NotImplementedError) as exc_info:
        path.add_signal("WaitForApproval", "Signaled")

    assert "Epic 2" in str(exc_info.value)
    assert "Epic 4" in str(exc_info.value)


def test_empty_path_initialization() -> None:
    """Create GraphPath, verify steps and decisions are empty."""
    path = GraphPath(path_id="test_path")

    assert path.path_id == "test_path"
    assert path.steps == []
    assert path.decisions == {}


def test_path_steps_tracking() -> None:
    """Add multiple activities, verify steps list preserves order."""
    path = GraphPath(path_id="linear")

    path.add_activity("Withdraw")
    path.add_activity("CurrencyConvert")
    path.add_activity("Deposit")

    assert path.steps == ["Withdraw", "CurrencyConvert", "Deposit"]
    assert len(path.steps) == 3
