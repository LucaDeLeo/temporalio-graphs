"""Unit tests for GraphBuildingContext configuration dataclass."""

from pathlib import Path
from typing import get_type_hints

import pytest

from temporalio_graphs.context import GraphBuildingContext


def test_default_configuration() -> None:
    """Verify GraphBuildingContext creates instance with all default values."""
    ctx = GraphBuildingContext()

    # Verify all 13 fields have expected defaults
    assert ctx.is_building_graph is True
    assert ctx.exit_after_building_graph is False
    assert ctx.graph_output_file is None
    assert ctx.split_names_by_words is True
    assert ctx.suppress_validation is False
    assert ctx.start_node_label == "Start"
    assert ctx.end_node_label == "End"
    assert ctx.max_decision_points == 10
    assert ctx.max_paths == 1024
    assert ctx.decision_true_label == "yes"
    assert ctx.decision_false_label == "no"
    assert ctx.signal_success_label == "Signaled"
    assert ctx.signal_timeout_label == "Timeout"


def test_custom_configuration() -> None:
    """Create context with custom values and verify fields match."""
    output_path = Path("/tmp/workflow_diagram.md")
    ctx = GraphBuildingContext(
        is_building_graph=False,
        exit_after_building_graph=True,
        graph_output_file=output_path,
        split_names_by_words=False,
        suppress_validation=True,
        start_node_label="Begin",
        end_node_label="Finish",
        max_decision_points=15,
        max_paths=2048,
        decision_true_label="TRUE",
        decision_false_label="FALSE",
        signal_success_label="Success",
        signal_timeout_label="TimedOut",
    )

    assert ctx.is_building_graph is False
    assert ctx.exit_after_building_graph is True
    assert ctx.graph_output_file == output_path
    assert ctx.split_names_by_words is False
    assert ctx.suppress_validation is True
    assert ctx.start_node_label == "Begin"
    assert ctx.end_node_label == "Finish"
    assert ctx.max_decision_points == 15
    assert ctx.max_paths == 2048
    assert ctx.decision_true_label == "TRUE"
    assert ctx.decision_false_label == "FALSE"
    assert ctx.signal_success_label == "Success"
    assert ctx.signal_timeout_label == "TimedOut"


def test_immutability_frozen() -> None:
    """Attempt to modify field after creation, expect error."""
    ctx = GraphBuildingContext()

    # Frozen dataclass should prevent field assignment
    with pytest.raises((AttributeError, TypeError)):
        ctx.max_paths = 2048  # type: ignore[misc]

    with pytest.raises((AttributeError, TypeError)):
        ctx.is_building_graph = False  # type: ignore[misc]


def test_all_fields_have_defaults() -> None:
    """Instantiate with no arguments, verify no TypeError."""
    # This should not raise TypeError for missing required arguments
    ctx = GraphBuildingContext()
    assert ctx is not None


def test_type_hints_present() -> None:
    """Use typing.get_type_hints to verify all fields have type annotations."""
    hints = get_type_hints(GraphBuildingContext)

    # Verify all 13 fields have type hints
    expected_fields = {
        "is_building_graph",
        "exit_after_building_graph",
        "graph_output_file",
        "split_names_by_words",
        "suppress_validation",
        "start_node_label",
        "end_node_label",
        "max_decision_points",
        "max_paths",
        "decision_true_label",
        "decision_false_label",
        "signal_success_label",
        "signal_timeout_label",
    }

    actual_fields = set(hints.keys())
    assert expected_fields.issubset(actual_fields), f"Missing type hints: {expected_fields - actual_fields}"

    # Verify specific types
    assert hints["is_building_graph"] == bool
    assert hints["max_decision_points"] == int
    assert hints["start_node_label"] == str
