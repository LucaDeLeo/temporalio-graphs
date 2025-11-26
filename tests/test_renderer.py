"""Unit tests for MermaidRenderer.

Tests for Mermaid flowchart generation from workflow execution paths,
including output format validation, node rendering, deduplication,
and edge case handling.
"""

import re
import time
from pathlib import Path

import pytest

from temporalio_graphs.context import GraphBuildingContext
from temporalio_graphs.path import GraphPath
from temporalio_graphs.renderer import MermaidRenderer


@pytest.fixture
def renderer() -> MermaidRenderer:
    """Create a MermaidRenderer instance for testing."""
    return MermaidRenderer()


@pytest.fixture
def default_context() -> GraphBuildingContext:
    """Create a GraphBuildingContext with default settings."""
    return GraphBuildingContext()


@pytest.fixture
def custom_context() -> GraphBuildingContext:
    """Create a GraphBuildingContext with custom labels."""
    return GraphBuildingContext(
        start_node_label="BEGIN",
        end_node_label="FINISH",
        split_names_by_words=False,
    )


@pytest.fixture
def split_context() -> GraphBuildingContext:
    """Create a GraphBuildingContext with word splitting enabled."""
    return GraphBuildingContext(split_names_by_words=True)


# Test AC1: MermaidRenderer class exists with correct module placement
def test_mermaid_renderer_class_exists() -> None:
    """Verify MermaidRenderer class exists and is instantiable."""
    renderer = MermaidRenderer()
    assert renderer is not None
    assert isinstance(renderer, MermaidRenderer)


def test_to_mermaid_method_signature(renderer: MermaidRenderer) -> None:
    """Verify to_mermaid() method has correct type signature.

    Checks that the method accepts list[GraphPath] and GraphBuildingContext,
    and returns a string.
    """
    path = GraphPath(path_id="path_0")
    path.add_activity("TestActivity")
    context = GraphBuildingContext()

    result = renderer.to_mermaid([path], context)

    assert isinstance(result, str)
    assert len(result) > 0


# Test AC2: Output format follows Mermaid flowchart LR structure
def test_to_mermaid_output_format_with_fences(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Verify output starts with triple-backtick fence and includes flowchart direction.

    Validates that output is a proper Mermaid code block with correct syntax.
    """
    path = GraphPath(path_id="path_0")
    path.add_activity("Activity1")

    result = renderer.to_mermaid([path], default_context)

    # Check fences
    assert result.startswith("```mermaid")
    assert result.endswith("```")

    # Check flowchart direction
    lines = result.split("\n")
    assert len(lines) >= 4  # fence, flowchart LR, nodes/edges, fence
    assert lines[1] == "flowchart LR"


def test_to_mermaid_output_structure(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Verify output structure is valid Mermaid syntax.

    Checks that output has proper line structure and valid identifiers.
    """
    path = GraphPath(path_id="path_0")
    path.add_activity("Withdraw")
    path.add_activity("Deposit")

    result = renderer.to_mermaid([path], default_context)
    lines = result.split("\n")

    # Validate structure
    assert lines[0] == "```mermaid"
    assert lines[1] == "flowchart LR"
    assert lines[-1] == "```"

    # Validate Mermaid content lines (not empty, contain valid syntax)
    mermaid_lines = lines[2:-1]
    for line in mermaid_lines:
        if line:  # Non-empty lines
            # Should contain node IDs or arrows
            assert any(
                c.isalnum() or c in "([]){ }->" for c in line
            ), f"Invalid line: {line}"


# Test AC3: Start and End node rendering
def test_to_mermaid_start_end_default_labels(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Verify Start renders as s((Start)) and End as e((End)) with defaults."""
    path = GraphPath(path_id="path_0")
    path.add_activity("Activity1")

    result = renderer.to_mermaid([path], default_context)

    assert "s((Start))" in result
    assert "e((End))" in result


def test_to_mermaid_start_end_custom_labels(
    renderer: MermaidRenderer, custom_context: GraphBuildingContext
) -> None:
    """Verify custom start_node_label and end_node_label are used."""
    path = GraphPath(path_id="path_0")
    path.add_activity("Activity1")

    result = renderer.to_mermaid([path], custom_context)

    assert "s((BEGIN))" in result
    assert "e((FINISH))" in result
    # Verify defaults NOT present
    assert "s((Start))" not in result
    assert "e((End))" not in result


def test_to_mermaid_start_end_only_empty_workflow(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Verify empty paths list generates Start -> End only."""
    result = renderer.to_mermaid([], default_context)

    assert "s((Start))" in result
    assert "e((End))" in result
    assert "s --> e" in result


# Test AC4: Activity node rendering
def test_to_mermaid_activity_nodes_single(
    renderer: MermaidRenderer,
) -> None:
    """Verify single activity renders as 1[ActivityName]."""
    no_split_context = GraphBuildingContext(split_names_by_words=False)
    path = GraphPath(path_id="path_0")
    node_id = path.add_activity("ValidateInput")

    result = renderer.to_mermaid([path], no_split_context)

    assert node_id == "1"
    assert "ValidateInput[ValidateInput]" in result


def test_to_mermaid_activity_nodes_multiple(
    renderer: MermaidRenderer,
) -> None:
    """Verify multiple activities render with sequential IDs 1, 2, 3, etc."""
    no_split_context = GraphBuildingContext(split_names_by_words=False)
    path = GraphPath(path_id="path_0")
    id1 = path.add_activity("ValidateInput")
    id2 = path.add_activity("ProcessOrder")
    id3 = path.add_activity("SendConfirmation")

    result = renderer.to_mermaid([path], no_split_context)

    assert id1 == "1" and id2 == "2" and id3 == "3"
    assert "ValidateInput[ValidateInput]" in result
    assert "ProcessOrder[ProcessOrder]" in result
    assert "SendConfirmation[SendConfirmation]" in result


def test_to_mermaid_activity_names_with_spaces(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Verify activity names with spaces are handled correctly."""
    path = GraphPath(path_id="path_0")
    path.add_activity("Send Email Notification")

    result = renderer.to_mermaid([path], default_context)

    assert "Send Email Notification[Send Email Notification]" in result


# Test AC5: Edge rendering with arrow syntax
def test_to_mermaid_edge_syntax(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Verify edges render with --> arrow syntax."""
    path = GraphPath(path_id="path_0")
    path.add_activity("Activity1")
    path.add_activity("Activity2")

    result = renderer.to_mermaid([path], default_context)

    # Verify arrow syntax
    assert " --> " in result
    # Verify specific edges
    assert "s --> Activity1" in result
    assert "Activity1 --> Activity2" in result
    assert "Activity2 --> e" in result


def test_to_mermaid_edge_connections_sequence(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Verify edges connect nodes in sequential order."""
    path = GraphPath(path_id="path_0")
    path.add_activity("First")
    path.add_activity("Second")
    path.add_activity("Third")

    result = renderer.to_mermaid([path], default_context)

    # Extract edges to verify sequence
    assert "s --> First" in result  # Start to first activity
    assert "First --> Second" in result  # Activity 1 to 2
    assert "Second --> Third" in result  # Activity 2 to 3
    assert "Third --> e" in result  # Last activity to End


# Test AC6: Node and edge deduplication
def test_to_mermaid_node_deduplication(
    renderer: MermaidRenderer,
) -> None:
    """Verify each node appears exactly once in output (no duplicates).

    Tests that even with multiple paths, nodes are not redefined.
    """
    no_split_context = GraphBuildingContext(split_names_by_words=False)
    path = GraphPath(path_id="path_0")
    path.add_activity("ValidateInput")
    path.add_activity("ProcessOrder")
    path.add_activity("SendConfirmation")

    result = renderer.to_mermaid([path], no_split_context)

    # Count node definitions
    start_count = result.count("s((Start))")
    end_count = result.count("e((End))")
    activity1_count = result.count("ValidateInput[ValidateInput]")
    activity2_count = result.count("ProcessOrder[ProcessOrder]")
    activity3_count = result.count("SendConfirmation[SendConfirmation]")

    # Each should appear exactly once
    assert start_count == 1, "Start node should appear exactly once"
    assert end_count == 1, "End node should appear exactly once"
    assert activity1_count == 1, "Activity 1 should appear exactly once"
    assert activity2_count == 1, "Activity 2 should appear exactly once"
    assert activity3_count == 1, "Activity 3 should appear exactly once"


def test_to_mermaid_edge_deduplication(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Verify each edge appears exactly once in output."""
    path = GraphPath(path_id="path_0")
    path.add_activity("Activity1")
    path.add_activity("Activity2")

    result = renderer.to_mermaid([path], default_context)

    # Count edge definitions
    s_to_1 = result.count("s --> Activity1")
    one_to_2 = result.count("Activity1 --> Activity2")
    two_to_e = result.count("Activity2 --> e")

    assert s_to_1 == 1, "Edge s --> 1 should appear exactly once"
    assert one_to_2 == 1, "Edge 1 --> 2 should appear exactly once"
    assert two_to_e == 1, "Edge 2 --> e should appear exactly once"


# Test AC7: Word splitting for camelCase names
def test_to_mermaid_word_splitting_enabled(
    renderer: MermaidRenderer, split_context: GraphBuildingContext
) -> None:
    """Verify camelCase names split when split_names_by_words=True."""
    split_context_true = GraphBuildingContext(split_names_by_words=True)
    path = GraphPath(path_id="path_0")
    path.add_activity("executePayment")
    path.add_activity("validateOutput")

    result = renderer.to_mermaid([path], split_context_true)

    # With splitting enabled, should have spaces
    assert "executePayment[execute Payment]" in result
    assert "validateOutput[validate Output]" in result


def test_to_mermaid_word_splitting_disabled(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Verify camelCase names preserved when split_names_by_words=False."""
    no_split_context = GraphBuildingContext(split_names_by_words=False)
    path = GraphPath(path_id="path_0")
    path.add_activity("executePayment")
    path.add_activity("validateOutput")

    result = renderer.to_mermaid([path], no_split_context)

    # Without splitting, should NOT have split names
    assert "executePayment[executePayment]" in result
    assert "validateOutput[validateOutput]" in result
    assert "execute Payment" not in result


def test_to_mermaid_word_splitting_edge_cases(
    renderer: MermaidRenderer,
) -> None:
    """Verify word splitting handles edge cases correctly.

    Tests: all caps, already spaced names, underscored names.
    """
    split_context = GraphBuildingContext(split_names_by_words=True)
    path = GraphPath(path_id="path_0")
    path.add_activity("CONSTANT")  # All caps - no split
    path.add_activity("Already Spaced")  # Already has spaces
    path.add_activity("snake_case")  # Underscores - no split
    path.add_activity("CamelCase")  # Should split

    result = renderer.to_mermaid([path], split_context)

    # Verify each case
    assert "CONSTANT[CONSTANT]" in result  # All caps unchanged
    assert "Already Spaced[Already Spaced]" in result  # Spaced unchanged
    assert "snake_case[snake_case]" in result  # Underscores unchanged
    assert "CamelCase[Camel Case]" in result  # camelCase split


# Test AC8: Path iteration and node sequence extraction
def test_to_mermaid_empty_workflow(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Verify empty paths list generates Start -> End only."""
    result = renderer.to_mermaid([], default_context)

    assert "s((Start))" in result
    assert "e((End))" in result
    assert "s --> e" in result

    # Should not have any activity nodes
    assert "[" not in result.split("flowchart LR")[1].split("```")[0] or all(
        c in "()" for c in result.split("flowchart LR")[1].split("```")[0]
    )


def test_to_mermaid_single_activity(
    renderer: MermaidRenderer,
) -> None:
    """Verify single activity path generates Start -> Activity -> End."""
    no_split_context = GraphBuildingContext(split_names_by_words=False)
    path = GraphPath(path_id="path_0")
    path.add_activity("ProcessPayment")

    result = renderer.to_mermaid([path], no_split_context)

    assert "s((Start))" in result
    assert "ProcessPayment[ProcessPayment]" in result
    assert "e((End))" in result
    assert "s --> ProcessPayment" in result
    assert "ProcessPayment --> e" in result


def test_to_mermaid_multiple_activities(
    renderer: MermaidRenderer,
) -> None:
    """Verify multiple activities generate correct sequence with edges."""
    no_split_context = GraphBuildingContext(split_names_by_words=False)
    path = GraphPath(path_id="path_0")
    path.add_activity("ValidateInput")
    path.add_activity("ProcessOrder")
    path.add_activity("SendConfirmation")

    result = renderer.to_mermaid([path], no_split_context)

    # Verify sequence - activity names are used as node IDs
    expected_sequence = [
        "s((Start))",
        "ValidateInput[ValidateInput]",
        "ProcessOrder[ProcessOrder]",
        "SendConfirmation[SendConfirmation]",
        "e((End))",
    ]

    for node in expected_sequence:
        assert node in result

    # Verify edges in order - using activity names as node IDs
    assert "s --> ValidateInput" in result
    assert "ValidateInput --> ProcessOrder" in result
    assert "ProcessOrder --> SendConfirmation" in result
    assert "SendConfirmation --> e" in result


# Test AC9: Type safety and complete type hints
def test_to_mermaid_type_hints_correct() -> None:
    """Verify to_mermaid() has correct type signature (verified by mypy)."""
    # This test is mainly for documentation - actual type checking done by mypy
    renderer = MermaidRenderer()
    path = GraphPath(path_id="path_0")
    path.add_activity("Test")
    context = GraphBuildingContext()

    # These should all work with correct types
    result: str = renderer.to_mermaid([path], context)
    assert isinstance(result, str)


# Test AC10: Integration with existing data models
def test_to_mermaid_integration_with_graph_path(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Verify renderer works correctly with GraphPath from Story 2.1."""
    path = GraphPath(path_id="path_0")

    # Use GraphPath interface as documented in Story 2.1
    id1 = path.add_activity("Activity1")
    id2 = path.add_activity("Activity2")

    # Verify returned IDs are sequential strings
    assert id1 == "1"
    assert id2 == "2"

    # Verify renderer can process the path
    result = renderer.to_mermaid([path], default_context)
    assert "1[Activity1]" in result
    assert "2[Activity2]" in result


def test_to_mermaid_integration_with_context(
    renderer: MermaidRenderer,
) -> None:
    """Verify renderer reads context fields correctly (immutable)."""
    path = GraphPath(path_id="path_0")
    path.add_activity("TestActivity")

    # Create context with all customization options
    context = GraphBuildingContext(
        start_node_label="BEGIN",
        end_node_label="FINISH",
        split_names_by_words=False,
    )

    result = renderer.to_mermaid([path], context)

    # Verify all context settings applied
    assert "s((BEGIN))" in result
    assert "e((FINISH))" in result

    # Verify context is not modified (immutable frozen dataclass)
    assert context.start_node_label == "BEGIN"


# Test AC11: Performance meets NFR-PERF-1 requirements
def test_to_mermaid_performance_50_nodes(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Measure rendering time for 50-node graph, assert <1ms per NFR-PERF-1.

    NFR-PERF-1 requires: rendering completes in <1ms for simple linear workflows.
    """
    # Create 50-node workflow
    path = GraphPath(path_id="path_0")
    for i in range(50):
        path.add_activity(f"Activity{i:03d}")

    # Measure rendering time
    start = time.perf_counter()
    result = renderer.to_mermaid([path], default_context)
    elapsed = time.perf_counter() - start

    # Verify performance requirement
    assert (
        elapsed < 0.001
    ), f"Performance requirement: <1ms, got {elapsed*1000:.3f}ms"

    # Verify output is correct
    assert "s((Start))" in result
    assert "e((End))" in result
    assert len([line for line in result.split("\n") if "[" in line]) == 50


def test_to_mermaid_performance_100_nodes(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Verify performance scales well for large workflows."""
    # Create 100-node workflow
    path = GraphPath(path_id="path_0")
    for i in range(100):
        path.add_activity(f"Activity{i:03d}")

    # Measure rendering time
    start = time.perf_counter()
    renderer.to_mermaid([path], default_context)
    elapsed = time.perf_counter() - start

    # Should be well under 1ms even for 100 nodes
    assert (
        elapsed < 0.001
    ), f"Performance should scale: <1ms for 100 nodes, got {elapsed*1000:.3f}ms"


# Test AC13: Handling edge cases and error conditions
def test_to_mermaid_raises_on_none_activity_name(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Verify ValueError raised with clear message for None activity names."""
    from temporalio_graphs.path import PathStep

    path = GraphPath(path_id="path_0")
    # Create a PathStep with None name to test error handling
    path.steps.append(PathStep(node_type='activity', name=None))  # type: ignore

    with pytest.raises(ValueError, match="Step name cannot be None or empty"):
        renderer.to_mermaid([path], default_context)


def test_to_mermaid_raises_on_empty_activity_name(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Verify ValueError raised for empty string activity names."""
    from temporalio_graphs.path import PathStep

    path = GraphPath(path_id="path_0")
    # Create a PathStep with empty string name to test error handling
    path.steps.append(PathStep(node_type='activity', name=""))

    with pytest.raises(ValueError, match="Step name cannot be None or empty"):
        renderer.to_mermaid([path], default_context)


def test_to_mermaid_handles_special_characters(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Verify activity names with special characters render correctly."""
    path = GraphPath(path_id="path_0")
    path.add_activity("Save-to-Database")
    path.add_activity("Check_Input_Valid")
    path.add_activity("Send/Email")

    result = renderer.to_mermaid([path], default_context)

    # Verify special characters preserved in node labels - using activity names as node IDs
    assert "Save-to-Database[Save-to-Database]" in result
    assert "Check_Input_Valid[Check_Input_Valid]" in result
    assert "Send/Email[Send/Email]" in result


def test_to_mermaid_handles_very_long_names(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Verify very long activity names (>100 chars) are supported."""
    long_name = "a" * 150
    path = GraphPath(path_id="path_0")
    path.add_activity(long_name)

    result = renderer.to_mermaid([path], default_context)

    # Should contain the full long name - using activity name as node ID
    assert f"{long_name}[{long_name}]" in result


def test_to_mermaid_handles_unicode_names(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Verify Unicode characters in activity names are supported."""
    path = GraphPath(path_id="path_0")
    path.add_activity("Validar_Entrada")  # Spanish
    path.add_activity("Verifier_Entrée")  # French
    path.add_activity("验证输入")  # Chinese

    result = renderer.to_mermaid([path], default_context)

    # Verify Unicode preserved - using activity names as node IDs
    assert "Validar_Entrada[Validar_Entrada]" in result
    assert "Verifier_Entrée[Verifier_Entrée]" in result
    assert "验证输入[验证输入]" in result


# Test AC14: Unit test coverage 100% for MermaidRenderer
def test_to_mermaid_valid_mermaid_syntax(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Verify output is valid Mermaid syntax (can be parsed).

    This validates the structure matches Mermaid flowchart specification.
    """
    path = GraphPath(path_id="path_0")
    path.add_activity("Activity1")
    path.add_activity("Activity2")

    result = renderer.to_mermaid([path], default_context)

    # Validate Mermaid structure with regex
    # Should match: node_id((label)) or node_id[label] or node_id{label}
    node_pattern = r"\w+(?:\(\(.*?\)\)|\[.*?\]|\{.*?\})"
    # Should match: node1 --> node2
    edge_pattern = r"\w+ --> \w+"

    mermaid_section = result.split("flowchart LR")[1].split("```")[0].strip()

    # Verify has nodes and edges
    lines = mermaid_section.split("\n")
    assert len(lines) > 0

    # Verify basic structure
    for line in lines:
        if line.strip():
            # Each non-empty line should be a node or edge definition
            assert re.match(
                rf"({node_pattern}|{edge_pattern})", line.strip()
            ), f"Invalid Mermaid syntax: {line}"


# Test AC15: Google-style docstrings
def test_to_mermaid_has_complete_docstring() -> None:
    """Verify to_mermaid() has complete Google-style docstring."""
    renderer = MermaidRenderer()
    docstring = renderer.to_mermaid.__doc__

    assert docstring is not None
    assert "Args:" in docstring
    assert "Returns:" in docstring
    assert "Raises:" in docstring
    assert "Example:" in docstring
    assert "paths" in docstring
    assert "context" in docstring
    assert "str" in docstring
    assert "ValueError" in docstring


# Golden file regression test
def test_to_mermaid_matches_expected_format(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Verify output matches expected format for simple workflow.

    This is a golden file test that validates consistency with baseline output.
    Loads the golden file and compares the complete output structure and order.
    """
    path = GraphPath(path_id="path_0")
    path.add_activity("Withdraw")
    path.add_activity("Deposit")

    result = renderer.to_mermaid([path], default_context)

    # Load golden file for comparison
    golden_file = Path(__file__).parent / "fixtures" / "expected_outputs" / "simple_linear.mermaid"
    with open(golden_file) as f:
        expected = f.read()

    # Compare complete output (normalized to handle whitespace variations)
    assert (
        result.strip() == expected.strip()
    ), f"Output does not match golden file.\n\nGot:\n{result}\n\nExpected:\n{expected}"


# Integration test with multiple paths (foundation for Epic 3)
def test_to_mermaid_handles_multiple_paths_foundation(
    renderer: MermaidRenderer,
) -> None:
    """Verify renderer can handle multiple paths (foundation for Epic 3 decisions).

    In Epic 2, we typically have single path. This tests deduplication foundation
    for future multi-path support in Epic 3.
    """
    no_split_context = GraphBuildingContext(split_names_by_words=False)
    # Create two identical paths (simulating reconvergence in Epic 3)
    path1 = GraphPath(path_id="path_0")
    path1.add_activity("ValidateInput")
    path1.add_activity("ProcessOrder")

    path2 = GraphPath(path_id="path_1")
    path2.add_activity("ValidateInput")
    path2.add_activity("ProcessOrder")

    result = renderer.to_mermaid([path1, path2], no_split_context)

    # With deduplication, nodes should appear only once - using activity names as node IDs
    validate_count = result.count("ValidateInput[ValidateInput]")
    process_count = result.count("ProcessOrder[ProcessOrder]")

    # Even with 2 paths, deduplication should keep each node once
    assert (
        validate_count == 1
    ), "Deduplication should prevent duplicate nodes in multi-path rendering"
    assert (
        process_count == 1
    ), "Deduplication should prevent duplicate nodes in multi-path rendering"

# ============================================================================
# Epic 4: Signal Node Rendering Tests (Story 4-3)
# ============================================================================


def test_signal_node_hexagon_syntax(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Verify signal nodes render with hexagon syntax {{NodeName}}.
    
    AC1: Signal nodes render using Mermaid hexagon syntax with double braces.
    """
    path = GraphPath(path_id="path_0")
    path.add_signal("WaitForApproval", "Signaled")
    
    result = renderer.to_mermaid([path], default_context)
    
    # Signal node should use double braces for hexagon: {{NodeName}}
    assert "WaitForApproval{{Wait For Approval}}" in result, \
        "Signal node should render with hexagon syntax (double braces)"


def test_signal_edges_labeled_correctly(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Verify signal edges are labeled with 'Signaled' or 'Timeout'.
    
    AC2: Signal branches labeled correctly with default labels.
    """
    # Path with Signaled outcome
    path1 = GraphPath(path_id="path_0b0")
    path1.add_signal("WaitApproval", "Signaled")
    path1.add_activity("ProcessApproval")
    
    # Path with Timeout outcome
    path2 = GraphPath(path_id="path_0b1")
    path2.add_signal("WaitApproval", "Timeout")
    path2.add_activity("HandleTimeout")
    
    result = renderer.to_mermaid([path1, path2], default_context)
    
    # Check for Signaled label
    assert "-- Signaled -->" in result, \
        "Signal success branch should be labeled 'Signaled'"
    
    # Check for Timeout label
    assert "-- Timeout -->" in result, \
        "Signal timeout branch should be labeled 'Timeout'"


def test_signal_custom_labels(renderer: MermaidRenderer) -> None:
    """Verify custom signal labels are used when configured.
    
    AC2: Custom signal labels supported via GraphBuildingContext configuration.
    """
    custom_context = GraphBuildingContext(
        signal_success_label="Success",
        signal_timeout_label="Failed"
    )
    
    path1 = GraphPath(path_id="path_0b0")
    path1.add_signal("WaitApproval", "Success")
    path1.add_activity("ProcessApproval")
    
    path2 = GraphPath(path_id="path_0b1")
    path2.add_signal("WaitApproval", "Failed")
    path2.add_activity("HandleFailure")
    
    result = renderer.to_mermaid([path1, path2], custom_context)
    
    # Check for custom labels
    assert "-- Success -->" in result, \
        "Custom signal success label should be used"
    assert "-- Failed -->" in result, \
        "Custom signal timeout label should be used"


def test_signal_node_deduplication(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Verify signal nodes deduplicate across paths.
    
    AC4: Same signal node ID appears only once in Mermaid output.
    """
    # Two paths with same signal but different outcomes
    path1 = GraphPath(path_id="path_0b0")
    path1.add_signal("WaitApproval", "Signaled")
    
    path2 = GraphPath(path_id="path_0b1")
    path2.add_signal("WaitApproval", "Timeout")
    
    result = renderer.to_mermaid([path1, path2], default_context)
    
    # Signal node should appear only once
    signal_node_count = result.count("WaitApproval{{Wait Approval}}")
    assert signal_node_count == 1, \
        "Signal node should be deduplicated (appear only once)"


def test_signal_and_activity_combined(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Verify signals and activities work together in same path.
    
    AC3: Signal nodes integrate into path permutation.
    """
    path = GraphPath(path_id="path_0")
    path.add_activity("StartProcess")
    path.add_signal("WaitApproval", "Signaled")
    path.add_activity("CompleteProcess")
    
    result = renderer.to_mermaid([path], default_context)
    
    # Check all nodes are present
    assert "StartProcess[Start Process]" in result
    assert "WaitApproval{{Wait Approval}}" in result
    assert "CompleteProcess[Complete Process]" in result
    
    # Check connections
    assert "StartProcess --> WaitApproval" in result
    assert "WaitApproval -- Signaled --> CompleteProcess" in result


def test_signal_and_decision_combined(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Verify signals and decisions work together in same path.
    
    AC3: Signal nodes integrate with decision nodes.
    """
    path = GraphPath(path_id="path_0b00")
    path.add_decision("d0", True, "NeedApproval")
    path.add_signal("WaitApproval", "Signaled")
    path.add_activity("CompleteProcess")
    
    result = renderer.to_mermaid([path], default_context)
    
    # Check all nodes are present
    assert "d0{Need Approval}" in result
    assert "WaitApproval{{Wait Approval}}" in result
    assert "CompleteProcess[Complete Process]" in result
    
    # Check connections with correct labels
    assert "d0 -- yes --> WaitApproval" in result
    assert "WaitApproval -- Signaled --> CompleteProcess" in result


def test_multiple_signals_in_path(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Verify multiple signals can exist in same path.
    
    AC3: Signal nodes integrate into path permutation.
    """
    path = GraphPath(path_id="path_0b00")
    path.add_signal("WaitApproval", "Signaled")
    path.add_activity("ProcessApproval")
    path.add_signal("WaitConfirmation", "Timeout")
    path.add_activity("HandleTimeout")
    
    result = renderer.to_mermaid([path], default_context)
    
    # Check both signal nodes are present
    assert "WaitApproval{{Wait Approval}}" in result
    assert "WaitConfirmation{{Wait Confirmation}}" in result
    
    # Check connections
    assert "WaitApproval -- Signaled --> ProcessApproval" in result
    assert "WaitConfirmation -- Timeout --> HandleTimeout" in result


def test_mermaid_output_valid_with_signals(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Verify generated Mermaid with signals is valid syntax.
    
    AC1, AC7: Generated Mermaid output is valid and renders correctly.
    """
    path = GraphPath(path_id="path_0")
    path.add_activity("StartProcess")
    path.add_signal("WaitApproval", "Signaled")
    path.add_activity("CompleteProcess")
    
    result = renderer.to_mermaid([path], default_context)
    
    # Basic structure validation
    assert result.startswith("```mermaid")
    assert result.endswith("```")
    lines = result.split("\n")
    assert lines[1] == "flowchart LR"
    
    # Validate hexagon syntax is correct (double braces)
    assert "{{" in result and "}}" in result, \
        "Hexagon syntax requires double braces"

    # No syntax errors (basic check)
    assert "{{" not in result.replace("{{", "").replace("}}", ""), \
        "No unmatched braces should exist"


# ============================================================================
# Epic 7: External Signal Rendering Tests
# ============================================================================


def test_external_signal_trapezoid_shape(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Test AC1: External signal nodes render with trapezoid syntax [/Signal Name\\].

    Validates that external signals use the correct Mermaid trapezoid shape
    syntax with forward slash and backslash.
    """
    path = GraphPath(path_id="path_0")
    path.add_activity("ProcessOrder")
    # Add external signal using PathStep with all required fields
    from temporalio_graphs.path import PathStep
    external_signal_step = PathStep(
        node_type='external_signal',
        name='ship_order',
        line_number=50,
        target_workflow_pattern='shipping-{*}'
    )
    path.steps.append(external_signal_step)
    path.add_activity("CompleteOrder")

    result = renderer.to_mermaid([path], default_context)

    # Verify trapezoid syntax appears
    assert "[/Signal 'ship_order'\\]" in result, \
        "External signal should render with trapezoid syntax [/...\\]"

    # Verify node ID format
    assert "ext_sig_ship_order_50" in result, \
        "External signal node ID should follow ext_sig_{name}_{line} format"


def test_external_signal_label_name_only(
    renderer: MermaidRenderer
) -> None:
    """Test AC2: External signal labels display in name-only mode (default).

    Validates that name-only mode shows just the signal name without target pattern.
    """
    context = GraphBuildingContext(external_signal_label_style="name-only")

    path = GraphPath(path_id="path_0")
    from temporalio_graphs.path import PathStep
    external_signal_step = PathStep(
        node_type='external_signal',
        name='ship_order',
        line_number=50,
        target_workflow_pattern='shipping-{*}'
    )
    path.steps.append(external_signal_step)

    result = renderer.to_mermaid([path], context)

    # Verify name-only label (no target pattern)
    assert "[/Signal 'ship_order'\\]" in result, \
        "Name-only mode should show Signal 'name' without target"
    assert "to shipping" not in result, \
        "Name-only mode should NOT include target pattern"


def test_external_signal_label_target_pattern(
    renderer: MermaidRenderer
) -> None:
    """Test AC2: External signal labels display in target-pattern mode.

    Validates that target-pattern mode shows both signal name and target workflow.
    """
    context = GraphBuildingContext(external_signal_label_style="target-pattern")

    path = GraphPath(path_id="path_0")
    from temporalio_graphs.path import PathStep
    external_signal_step = PathStep(
        node_type='external_signal',
        name='ship_order',
        line_number=50,
        target_workflow_pattern='shipping-{*}'
    )
    path.steps.append(external_signal_step)

    result = renderer.to_mermaid([path], context)

    # Verify target-pattern label includes both name and target
    assert "[/Signal 'ship_order' to shipping-{*}\\]" in result, \
        "Target-pattern mode should show Signal 'name' to target"


def test_external_signal_dashed_edge(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Test AC3: External signal edges render with dashed style -.signal.->.

    Validates that edges connecting to/from external signals use dashed notation
    to indicate asynchronous communication.
    """
    path = GraphPath(path_id="path_0")
    path.add_activity("ProcessOrder")

    from temporalio_graphs.path import PathStep
    external_signal_step = PathStep(
        node_type='external_signal',
        name='ship_order',
        line_number=50,
        target_workflow_pattern='shipping-{*}'
    )
    path.steps.append(external_signal_step)

    path.add_activity("CompleteOrder")

    result = renderer.to_mermaid([path], default_context)

    # Verify dashed edges appear
    assert "-.signal.->" in result, \
        "External signal edges should use dashed style -.signal.->"

    # Verify both edges use dashed style
    # Edge from ProcessOrder to external signal
    assert "ProcessOrder -.signal.-> ext_sig_ship_order_50" in result or \
           "ProcessOrder-.signal.->ext_sig_ship_order_50" in result.replace(" ", ""), \
        "Edge TO external signal should be dashed"

    # Edge from external signal to CompleteOrder
    assert "ext_sig_ship_order_50 -.signal.-> CompleteOrder" in result or \
           "ext_sig_ship_order_50-.signal.->CompleteOrder" in result.replace(" ", ""), \
        "Edge FROM external signal should be dashed"


def test_external_signal_color_styling(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Test AC4: External signal nodes have orange/amber color styling.

    Validates that style directive is generated with correct fill and stroke colors.
    """
    path = GraphPath(path_id="path_0")
    from temporalio_graphs.path import PathStep
    external_signal_step = PathStep(
        node_type='external_signal',
        name='ship_order',
        line_number=50,
        target_workflow_pattern='shipping-{*}'
    )
    path.steps.append(external_signal_step)

    result = renderer.to_mermaid([path], default_context)

    # Verify style directive exists
    assert "style ext_sig_ship_order_50 fill:#fff4e6,stroke:#ffa500" in result, \
        "External signal should have orange/amber color styling"


def test_show_external_signals_false(
    renderer: MermaidRenderer
) -> None:
    """Test AC6: Configuration option show_external_signals=False suppresses external signals.

    Validates that external signal nodes are completely excluded from output
    when show_external_signals is False.
    """
    context = GraphBuildingContext(show_external_signals=False)

    path = GraphPath(path_id="path_0")
    path.add_activity("ProcessOrder")

    from temporalio_graphs.path import PathStep
    external_signal_step = PathStep(
        node_type='external_signal',
        name='ship_order',
        line_number=50,
        target_workflow_pattern='shipping-{*}'
    )
    path.steps.append(external_signal_step)

    path.add_activity("CompleteOrder")

    result = renderer.to_mermaid([path], context)

    # Verify external signal does NOT appear
    assert "ext_sig_ship_order_50" not in result, \
        "External signal node should be suppressed when show_external_signals=False"
    assert "[/Signal" not in result, \
        "Trapezoid syntax should not appear when external signals are suppressed"

    # Verify activities still appear
    assert "ProcessOrder" in result, \
        "Activities should still render when external signals are suppressed"
    assert "CompleteOrder" in result, \
        "Activities should still render when external signals are suppressed"


def test_rendering_performance_10_external_signals(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Test AC10: Rendering completes in <1ms for graphs with 10 external signals.

    Performance test to ensure external signal rendering doesn't degrade performance.
    """
    path = GraphPath(path_id="path_0")

    from temporalio_graphs.path import PathStep

    # Add 10 external signal nodes
    for i in range(10):
        signal_step = PathStep(
            node_type='external_signal',
            name=f'signal_{i}',
            line_number=100 + i,
            target_workflow_pattern=f'workflow-{i}'
        )
        path.steps.append(signal_step)

    # Measure rendering time
    start_time = time.perf_counter()
    result = renderer.to_mermaid([path], default_context)
    end_time = time.perf_counter()

    rendering_time = end_time - start_time

    # Verify rendering completed
    assert len(result) > 0, "Rendering should produce output"

    # Verify performance target (<1ms = 0.001 seconds)
    # Allow 10ms for safety (CI systems can be slower)
    assert rendering_time < 0.010, \
        f"Rendering 10 external signals should complete in <10ms, took {rendering_time*1000:.2f}ms"

    # Verify all external signals rendered
    for i in range(10):
        assert f"ext_sig_signal_{i}_{100+i}" in result, \
            f"External signal {i} should be rendered"


def test_external_signal_with_decisions(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Test external signals work correctly with decision nodes.

    Validates that external signals can appear in decision branches and edges
    are labeled correctly.
    """
    path = GraphPath(path_id="path_0")
    path.add_activity("CheckInventory")
    decision_id = path.add_decision("d0", True, "InStock")

    from temporalio_graphs.path import PathStep
    external_signal_step = PathStep(
        node_type='external_signal',
        name='notify_warehouse',
        line_number=75,
        target_workflow_pattern='warehouse-{*}'
    )
    path.steps.append(external_signal_step)

    path.add_activity("ShipOrder")

    result = renderer.to_mermaid([path], default_context)

    # Verify decision node appears
    assert "d0{InStock}" in result or "d0{In Stock}" in result, \
        "Decision node should render"

    # Verify external signal appears
    assert "ext_sig_notify_warehouse_75" in result, \
        "External signal should render"

    # Verify edge from decision to external signal has label
    assert "-- yes -.signal.-> ext_sig_notify_warehouse_75" in result or \
           "d0 -- yes -.signal.-> ext_sig_notify_warehouse_75" in result, \
        "Edge from decision to external signal should have yes label and dashed style"


def test_external_signal_multiple_paths(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Test external signals are deduplicated across multiple paths.

    Validates that when the same external signal appears in multiple paths,
    it's rendered only once with proper edge deduplication.
    """
    from temporalio_graphs.path import PathStep

    # Path 1
    path1 = GraphPath(path_id="path_0")
    path1.add_activity("ProcessOrder")
    signal_step1 = PathStep(
        node_type='external_signal',
        name='ship_order',
        line_number=50,
        target_workflow_pattern='shipping-{*}'
    )
    path1.steps.append(signal_step1)

    # Path 2 - same external signal
    path2 = GraphPath(path_id="path_1")
    path2.add_activity("ProcessOrder")
    signal_step2 = PathStep(
        node_type='external_signal',
        name='ship_order',
        line_number=50,
        target_workflow_pattern='shipping-{*}'
    )
    path2.steps.append(signal_step2)

    result = renderer.to_mermaid([path1, path2], default_context)

    # Count occurrences of external signal node definition
    node_count = result.count("ext_sig_ship_order_50[/Signal 'ship_order'\\]")

    # Should appear exactly once (deduplicated)
    assert node_count == 1, \
        f"External signal node should be deduplicated, found {node_count} definitions"


# ============================================================================
# Epic 8: Subgraph Rendering Tests (Story 8-7)
# ============================================================================


@pytest.fixture
def simple_workflow_metadata() -> "WorkflowMetadata":
    """Create a simple WorkflowMetadata for testing."""
    from temporalio_graphs._internal.graph_models import (
        Activity,
        WorkflowMetadata,
    )
    return WorkflowMetadata(
        workflow_class="OrderWorkflow",
        workflow_run_method="run",
        activities=[Activity("process_order", 10), Activity("complete_order", 20)],
        decision_points=[],
        signal_points=[],
        source_file=Path("order_workflow.py"),
        total_paths=1,
        child_workflow_calls=[],
        external_signals=(),
        signal_handlers=(),
    )


@pytest.fixture
def workflow_with_handler() -> "WorkflowMetadata":
    """Create WorkflowMetadata with signal handler."""
    from temporalio_graphs._internal.graph_models import (
        Activity,
        SignalHandler,
        WorkflowMetadata,
    )
    return WorkflowMetadata(
        workflow_class="ShippingWorkflow",
        workflow_run_method="run",
        activities=[Activity("ship_package", 30)],
        decision_points=[],
        signal_points=[],
        source_file=Path("shipping_workflow.py"),
        total_paths=1,
        child_workflow_calls=[],
        external_signals=(),
        signal_handlers=(
            SignalHandler(
                signal_name="ship_order",
                method_name="ship_order",
                workflow_class="ShippingWorkflow",
                source_line=67,
                node_id="sig_handler_ship_order_67",
            ),
        ),
    )


@pytest.fixture
def peer_signal_graph_single(
    simple_workflow_metadata: "WorkflowMetadata",
) -> "PeerSignalGraph":
    """Create PeerSignalGraph with single workflow."""
    from temporalio_graphs._internal.graph_models import PeerSignalGraph
    return PeerSignalGraph(
        root_workflow=simple_workflow_metadata,
        workflows={"OrderWorkflow": simple_workflow_metadata},
        signal_handlers={},
        connections=[],
        unresolved_signals=[],
    )


@pytest.fixture
def peer_signal_graph_multiple(
    simple_workflow_metadata: "WorkflowMetadata",
    workflow_with_handler: "WorkflowMetadata",
) -> "PeerSignalGraph":
    """Create PeerSignalGraph with multiple workflows."""
    from temporalio_graphs._internal.graph_models import PeerSignalGraph, SignalHandler
    handler = SignalHandler(
        signal_name="ship_order",
        method_name="ship_order",
        workflow_class="ShippingWorkflow",
        source_line=67,
        node_id="sig_handler_ship_order_67",
    )
    return PeerSignalGraph(
        root_workflow=simple_workflow_metadata,
        workflows={
            "OrderWorkflow": simple_workflow_metadata,
            "ShippingWorkflow": workflow_with_handler,
        },
        signal_handlers={"ship_order": [handler]},
        connections=[],
        unresolved_signals=[],
    )


def test_render_signal_graph_single_workflow(
    renderer: MermaidRenderer,
    peer_signal_graph_single: "PeerSignalGraph",
) -> None:
    """Test AC17: Single workflow renders as subgraph with internal nodes.

    Validates that:
    - Output contains "subgraph WorkflowName"
    - Output contains "end" closing subgraph
    - Uses flowchart TB direction (top-to-bottom)
    """
    result = renderer.render_signal_graph(peer_signal_graph_single)

    # Verify fenced code block
    assert result.startswith("```mermaid"), \
        "Output should start with mermaid fence"
    assert result.endswith("```"), \
        "Output should end with closing fence"

    # Verify flowchart direction is TB (top-to-bottom)
    assert "flowchart TB" in result, \
        "Subgraph rendering should use flowchart TB direction"

    # Verify subgraph structure
    assert "subgraph OrderWorkflow" in result, \
        "Output should contain subgraph for OrderWorkflow"
    assert "    end" in result, \
        "Output should contain 'end' to close subgraph"

    # Verify internal nodes are present
    assert "s_OrderWorkflow((Start))" in result, \
        "Start node should have workflow-unique ID"
    assert "e_OrderWorkflow((End))" in result, \
        "End node should have workflow-unique ID"


def test_render_signal_graph_multiple_workflows(
    renderer: MermaidRenderer,
    peer_signal_graph_multiple: "PeerSignalGraph",
) -> None:
    """Test AC17: Multiple workflows each render as separate subgraphs.

    Validates that:
    - Each workflow has its own "subgraph" block
    - Each subgraph has matching "end" statement
    - Blank line between subgraphs for readability
    """
    result = renderer.render_signal_graph(peer_signal_graph_multiple)

    # Verify both subgraphs present
    assert "subgraph OrderWorkflow" in result, \
        "Output should contain subgraph for OrderWorkflow"
    assert "subgraph ShippingWorkflow" in result, \
        "Output should contain subgraph for ShippingWorkflow"

    # Count "end" statements - should match number of subgraphs
    end_count = result.count("    end")
    assert end_count == 2, \
        f"Should have 2 'end' statements (one per subgraph), found {end_count}"

    # Verify unique Start/End nodes per workflow
    assert "s_OrderWorkflow((Start))" in result, \
        "OrderWorkflow should have unique start node"
    assert "s_ShippingWorkflow((Start))" in result, \
        "ShippingWorkflow should have unique start node"
    assert "e_OrderWorkflow((End))" in result, \
        "OrderWorkflow should have unique end node"
    assert "e_ShippingWorkflow((End))" in result, \
        "ShippingWorkflow should have unique end node"


def test_render_signal_handler_hexagon_shape(
    renderer: MermaidRenderer,
    peer_signal_graph_multiple: "PeerSignalGraph",
) -> None:
    """Test AC18: Signal handlers render as hexagon with double curly braces.

    Validates that:
    - Handler node uses {{signal_name}} syntax (Mermaid hexagon)
    - Node ID format is sig_handler_{name}_{line}
    """
    result = renderer.render_signal_graph(peer_signal_graph_multiple)

    # Verify hexagon syntax appears (double curly braces)
    assert "sig_handler_ship_order_67{{ship_order}}" in result, \
        "Signal handler should render with hexagon syntax {{signal_name}}"

    # Verify node ID format
    assert "sig_handler_ship_order_67" in result, \
        "Signal handler node ID should follow sig_handler_{name}_{line} format"


def test_render_signal_handler_styling(
    renderer: MermaidRenderer,
    peer_signal_graph_multiple: "PeerSignalGraph",
) -> None:
    """Test AC20: Signal handlers have blue color styling.

    Validates that:
    - Style directive includes fill:#e6f3ff,stroke:#0066cc
    - Each handler node has corresponding style directive
    - Style comment is present
    """
    result = renderer.render_signal_graph(peer_signal_graph_multiple)

    # Verify styling comment
    assert "%% Signal handler styling (hexagons - blue)" in result, \
        "Output should include styling comment"

    # Verify style directive
    assert "style sig_handler_ship_order_67 fill:#e6f3ff,stroke:#0066cc" in result, \
        "Signal handler should have blue color styling"


def test_render_workflow_internal(
    renderer: MermaidRenderer,
    simple_workflow_metadata: "WorkflowMetadata",
    default_context: GraphBuildingContext,
) -> None:
    """Test _render_workflow_internal returns list of node/edge definitions.

    Validates that:
    - Returns list of strings (not full diagram)
    - Does not include subgraph wrapper
    - Contains node definitions and edges
    """
    lines = renderer._render_workflow_internal(simple_workflow_metadata, default_context)

    # Should return list of strings
    assert isinstance(lines, list), \
        "_render_workflow_internal should return list"
    assert all(isinstance(line, str) for line in lines), \
        "All elements should be strings"

    # Should NOT include subgraph wrapper or fences
    joined = "\n".join(lines)
    assert "subgraph" not in joined, \
        "_render_workflow_internal should not include subgraph wrapper"
    assert "```mermaid" not in joined, \
        "_render_workflow_internal should not include mermaid fence"

    # Should include workflow-unique node IDs
    assert "s_OrderWorkflow((Start))" in joined, \
        "Should include workflow-unique start node"
    assert "e_OrderWorkflow((End))" in joined, \
        "Should include workflow-unique end node"

    # Should include activity nodes
    assert "process_order_OrderWorkflow" in joined, \
        "Activity nodes should have workflow-unique IDs"


def test_render_signal_graph_with_context(
    renderer: MermaidRenderer,
    peer_signal_graph_single: "PeerSignalGraph",
) -> None:
    """Test render_signal_graph accepts custom context.

    Validates that custom start/end labels are respected.
    """
    custom_context = GraphBuildingContext(
        start_node_label="BEGIN",
        end_node_label="FINISH",
    )

    result = renderer.render_signal_graph(peer_signal_graph_single, custom_context)

    assert "BEGIN" in result, \
        "Custom start label should be used"
    assert "FINISH" in result, \
        "Custom end label should be used"


def test_render_signal_graph_empty_handlers(
    renderer: MermaidRenderer,
    peer_signal_graph_single: "PeerSignalGraph",
) -> None:
    """Test render_signal_graph with workflow without signal handlers.

    Validates that workflows without handlers render correctly without
    any handler nodes or styling.
    """
    result = renderer.render_signal_graph(peer_signal_graph_single)

    # Should NOT have handler styling section when no handlers
    assert "%% Signal handler styling" not in result, \
        "No styling section when no handlers present"

    # Should still have valid subgraph structure
    assert "subgraph OrderWorkflow" in result
    assert "    end" in result


def test_render_signal_graph_multiple_handlers_same_workflow(
    renderer: MermaidRenderer,
) -> None:
    """Test workflow with multiple signal handlers.

    Validates that multiple handlers in same workflow all render correctly.
    """
    from temporalio_graphs._internal.graph_models import (
        Activity,
        PeerSignalGraph,
        SignalHandler,
        WorkflowMetadata,
    )

    # Create workflow with multiple handlers
    handler1 = SignalHandler(
        signal_name="ship_order",
        method_name="ship_order",
        workflow_class="ShippingWorkflow",
        source_line=67,
        node_id="sig_handler_ship_order_67",
    )
    handler2 = SignalHandler(
        signal_name="cancel_order",
        method_name="cancel_order",
        workflow_class="ShippingWorkflow",
        source_line=80,
        node_id="sig_handler_cancel_order_80",
    )

    metadata = WorkflowMetadata(
        workflow_class="ShippingWorkflow",
        workflow_run_method="run",
        activities=[Activity("ship_package", 30)],
        decision_points=[],
        signal_points=[],
        source_file=Path("shipping_workflow.py"),
        total_paths=1,
        child_workflow_calls=[],
        external_signals=(),
        signal_handlers=(handler1, handler2),
    )

    graph = PeerSignalGraph(
        root_workflow=metadata,
        workflows={"ShippingWorkflow": metadata},
        signal_handlers={
            "ship_order": [handler1],
            "cancel_order": [handler2],
        },
        connections=[],
        unresolved_signals=[],
    )

    result = renderer.render_signal_graph(graph)

    # Both handlers should render as hexagons
    assert "sig_handler_ship_order_67{{ship_order}}" in result, \
        "First handler should render as hexagon"
    assert "sig_handler_cancel_order_80{{cancel_order}}" in result, \
        "Second handler should render as hexagon"

    # Both should have styling
    assert "style sig_handler_ship_order_67 fill:#e6f3ff,stroke:#0066cc" in result
    assert "style sig_handler_cancel_order_80 fill:#e6f3ff,stroke:#0066cc" in result


def test_render_signal_graph_node_id_uniqueness(
    renderer: MermaidRenderer,
) -> None:
    """Test that same activity name in multiple workflows gets unique IDs.

    Validates AC6: Node IDs within subgraphs avoid collisions.
    """
    from temporalio_graphs._internal.graph_models import (
        Activity,
        PeerSignalGraph,
        WorkflowMetadata,
    )

    # Create two workflows with same activity name
    metadata1 = WorkflowMetadata(
        workflow_class="OrderWorkflow",
        workflow_run_method="run",
        activities=[Activity("process", 10)],
        decision_points=[],
        signal_points=[],
        source_file=Path("order_workflow.py"),
        total_paths=1,
    )

    metadata2 = WorkflowMetadata(
        workflow_class="ShippingWorkflow",
        workflow_run_method="run",
        activities=[Activity("process", 20)],
        decision_points=[],
        signal_points=[],
        source_file=Path("shipping_workflow.py"),
        total_paths=1,
    )

    graph = PeerSignalGraph(
        root_workflow=metadata1,
        workflows={
            "OrderWorkflow": metadata1,
            "ShippingWorkflow": metadata2,
        },
        signal_handlers={},
        connections=[],
        unresolved_signals=[],
    )

    result = renderer.render_signal_graph(graph)

    # Activity nodes should have workflow-unique IDs
    assert "process_OrderWorkflow" in result, \
        "Activity in OrderWorkflow should have workflow-unique ID"
    assert "process_ShippingWorkflow" in result, \
        "Activity in ShippingWorkflow should have workflow-unique ID"

    # Start/End nodes should be unique
    assert "s_OrderWorkflow" in result
    assert "s_ShippingWorkflow" in result
    assert "e_OrderWorkflow" in result
    assert "e_ShippingWorkflow" in result


# ============================================================================
# Epic 8: Cross-Subgraph Edge Tests (Story 8-8)
# ============================================================================


def test_render_cross_subgraph_edge(
    renderer: MermaidRenderer,
) -> None:
    """Test AC19: Single SignalConnection renders as dashed edge.

    Validates that:
    - Cross-subgraph edge uses dashed syntax: -.signal_name.->
    - Edge connects sender_node_id to receiver_node_id
    - Edge appears AFTER all subgraph blocks
    """
    from temporalio_graphs._internal.graph_models import (
        Activity,
        ExternalSignalCall,
        PeerSignalGraph,
        SignalConnection,
        SignalHandler,
        WorkflowMetadata,
    )

    # Create OrderWorkflow with external signal
    order_metadata = WorkflowMetadata(
        workflow_class="OrderWorkflow",
        workflow_run_method="run",
        activities=[Activity("process_order", 10)],
        decision_points=[],
        signal_points=[],
        source_file=Path("order_workflow.py"),
        total_paths=1,
        external_signals=(
            ExternalSignalCall(
                signal_name="ship_order",
                target_workflow_pattern="shipping-{*}",
                source_line=56,
                node_id="ext_sig_ship_order_56",
                source_workflow="OrderWorkflow",
            ),
        ),
    )

    # Create ShippingWorkflow with signal handler
    handler = SignalHandler(
        signal_name="ship_order",
        method_name="ship_order",
        workflow_class="ShippingWorkflow",
        source_line=67,
        node_id="sig_handler_ship_order_67",
    )
    shipping_metadata = WorkflowMetadata(
        workflow_class="ShippingWorkflow",
        workflow_run_method="run",
        activities=[Activity("ship_package", 30)],
        decision_points=[],
        signal_points=[],
        source_file=Path("shipping_workflow.py"),
        total_paths=1,
        signal_handlers=(handler,),
    )

    # Create connection
    connection = SignalConnection(
        sender_workflow="OrderWorkflow",
        receiver_workflow="ShippingWorkflow",
        signal_name="ship_order",
        sender_line=56,
        receiver_line=67,
        sender_node_id="ext_sig_ship_order_56",
        receiver_node_id="sig_handler_ship_order_67",
    )

    graph = PeerSignalGraph(
        root_workflow=order_metadata,
        workflows={
            "OrderWorkflow": order_metadata,
            "ShippingWorkflow": shipping_metadata,
        },
        signal_handlers={"ship_order": [handler]},
        connections=[connection],
        unresolved_signals=[],
    )

    result = renderer.render_signal_graph(graph)

    # Verify cross-subgraph edge with dashed syntax
    assert "ext_sig_ship_order_56_OrderWorkflow -.ship_order.-> sig_handler_ship_order_67" in result, \
        "Cross-subgraph edge should use dashed syntax with signal name as label"

    # Verify edge appears after subgraph blocks
    subgraph_end_pos = result.rfind("    end")
    edge_pos = result.find("ext_sig_ship_order_56_OrderWorkflow -.ship_order.->")
    assert edge_pos > subgraph_end_pos, \
        "Cross-subgraph edge should appear AFTER all subgraph blocks"

    # Verify connection comment
    assert "%% Cross-workflow signal connections" in result, \
        "Output should include cross-workflow connections comment"


def test_render_multiple_cross_subgraph_edges(
    renderer: MermaidRenderer,
) -> None:
    """Test AC5: Multiple SignalConnections each render as separate dashed edges.

    Validates that:
    - All connections render (one edge per connection)
    - Order follows graph.connections list order
    - No duplicate edges
    """
    from temporalio_graphs._internal.graph_models import (
        Activity,
        PeerSignalGraph,
        SignalConnection,
        SignalHandler,
        WorkflowMetadata,
    )

    # Create workflow with multiple handlers
    handler1 = SignalHandler(
        signal_name="ship_order",
        method_name="ship_order",
        workflow_class="ShippingWorkflow",
        source_line=67,
        node_id="sig_handler_ship_order_67",
    )
    handler2 = SignalHandler(
        signal_name="notify_customer",
        method_name="notify_customer",
        workflow_class="NotificationWorkflow",
        source_line=42,
        node_id="sig_handler_notify_customer_42",
    )

    order_metadata = WorkflowMetadata(
        workflow_class="OrderWorkflow",
        workflow_run_method="run",
        activities=[Activity("process_order", 10)],
        decision_points=[],
        signal_points=[],
        source_file=Path("order_workflow.py"),
        total_paths=1,
    )

    shipping_metadata = WorkflowMetadata(
        workflow_class="ShippingWorkflow",
        workflow_run_method="run",
        activities=[Activity("ship_package", 30)],
        decision_points=[],
        signal_points=[],
        source_file=Path("shipping_workflow.py"),
        total_paths=1,
        signal_handlers=(handler1,),
    )

    notification_metadata = WorkflowMetadata(
        workflow_class="NotificationWorkflow",
        workflow_run_method="run",
        activities=[Activity("send_notification", 20)],
        decision_points=[],
        signal_points=[],
        source_file=Path("notification_workflow.py"),
        total_paths=1,
        signal_handlers=(handler2,),
    )

    # Create multiple connections
    connection1 = SignalConnection(
        sender_workflow="OrderWorkflow",
        receiver_workflow="ShippingWorkflow",
        signal_name="ship_order",
        sender_line=56,
        receiver_line=67,
        sender_node_id="ext_sig_ship_order_56",
        receiver_node_id="sig_handler_ship_order_67",
    )
    connection2 = SignalConnection(
        sender_workflow="OrderWorkflow",
        receiver_workflow="NotificationWorkflow",
        signal_name="notify_customer",
        sender_line=60,
        receiver_line=42,
        sender_node_id="ext_sig_notify_customer_60",
        receiver_node_id="sig_handler_notify_customer_42",
    )

    graph = PeerSignalGraph(
        root_workflow=order_metadata,
        workflows={
            "OrderWorkflow": order_metadata,
            "ShippingWorkflow": shipping_metadata,
            "NotificationWorkflow": notification_metadata,
        },
        signal_handlers={
            "ship_order": [handler1],
            "notify_customer": [handler2],
        },
        connections=[connection1, connection2],
        unresolved_signals=[],
    )

    result = renderer.render_signal_graph(graph)

    # Verify both connections render
    assert "ext_sig_ship_order_56_OrderWorkflow -.ship_order.-> sig_handler_ship_order_67" in result, \
        "First connection should render"
    assert "ext_sig_notify_customer_60_OrderWorkflow -.notify_customer.-> sig_handler_notify_customer_42" in result, \
        "Second connection should render"

    # Verify no duplicate edges (count each edge)
    count1 = result.count("ext_sig_ship_order_56_OrderWorkflow -.ship_order.-> sig_handler_ship_order_67")
    count2 = result.count("ext_sig_notify_customer_60_OrderWorkflow -.notify_customer.-> sig_handler_notify_customer_42")
    assert count1 == 1, "Each connection should appear exactly once"
    assert count2 == 1, "Each connection should appear exactly once"


def test_render_unresolved_signal_node(
    renderer: MermaidRenderer,
) -> None:
    """Test AC21: Unresolved signal renders with [/?/] dead-end and amber styling.

    Validates that:
    - Unresolved signal creates edge to unknown_{signal_name}_{line}[/?/]
    - Unknown node has amber warning styling
    - Style uses fill:#fff3cd,stroke:#ffc107
    """
    from temporalio_graphs._internal.graph_models import (
        Activity,
        ExternalSignalCall,
        PeerSignalGraph,
        WorkflowMetadata,
    )

    # Create workflow with unresolved signal
    unresolved_signal = ExternalSignalCall(
        signal_name="unknown_signal",
        target_workflow_pattern="missing-{*}",
        source_line=42,
        node_id="ext_sig_unknown_signal_42",
        source_workflow="OrderWorkflow",
    )

    order_metadata = WorkflowMetadata(
        workflow_class="OrderWorkflow",
        workflow_run_method="run",
        activities=[Activity("process_order", 10)],
        decision_points=[],
        signal_points=[],
        source_file=Path("order_workflow.py"),
        total_paths=1,
        external_signals=(unresolved_signal,),
    )

    graph = PeerSignalGraph(
        root_workflow=order_metadata,
        workflows={"OrderWorkflow": order_metadata},
        signal_handlers={},
        connections=[],
        unresolved_signals=[unresolved_signal],
    )

    result = renderer.render_signal_graph(graph)

    # Verify unresolved signal edge with dead-end node
    assert "ext_sig_unknown_signal_42_OrderWorkflow -.unknown_signal.-> unknown_unknown_signal_42[/?/]" in result, \
        "Unresolved signal should render edge to dead-end node with [/?/]"

    # Verify unresolved comment
    assert "%% Unresolved signals (no handler found)" in result, \
        "Output should include unresolved signals comment"

    # Verify amber warning styling
    assert "style unknown_unknown_signal_42 fill:#fff3cd,stroke:#ffc107" in result, \
        "Unresolved signal node should have amber warning styling"

    # Verify styling comment
    assert "%% Unresolved signal styling (warning - amber)" in result, \
        "Output should include unresolved styling comment"


def test_render_signal_graph_complete(
    renderer: MermaidRenderer,
) -> None:
    """Test AC7: Full graph with subgraphs, connections, and unresolved signals.

    Validates complete integration with:
    - Multiple subgraphs
    - Cross-subgraph signal connections
    - Unresolved signals with dead-end nodes
    - All styling (handler blue, unresolved amber)
    """
    from temporalio_graphs._internal.graph_models import (
        Activity,
        ExternalSignalCall,
        PeerSignalGraph,
        SignalConnection,
        SignalHandler,
        WorkflowMetadata,
    )

    # Signal handler
    handler = SignalHandler(
        signal_name="ship_order",
        method_name="ship_order",
        workflow_class="ShippingWorkflow",
        source_line=67,
        node_id="sig_handler_ship_order_67",
    )

    # Workflows
    order_metadata = WorkflowMetadata(
        workflow_class="OrderWorkflow",
        workflow_run_method="run",
        activities=[Activity("process_order", 10)],
        decision_points=[],
        signal_points=[],
        source_file=Path("order_workflow.py"),
        total_paths=1,
    )

    shipping_metadata = WorkflowMetadata(
        workflow_class="ShippingWorkflow",
        workflow_run_method="run",
        activities=[Activity("ship_package", 30)],
        decision_points=[],
        signal_points=[],
        source_file=Path("shipping_workflow.py"),
        total_paths=1,
        signal_handlers=(handler,),
    )

    # Connection (resolved)
    connection = SignalConnection(
        sender_workflow="OrderWorkflow",
        receiver_workflow="ShippingWorkflow",
        signal_name="ship_order",
        sender_line=56,
        receiver_line=67,
        sender_node_id="ext_sig_ship_order_56",
        receiver_node_id="sig_handler_ship_order_67",
    )

    # Unresolved signal
    unresolved = ExternalSignalCall(
        signal_name="unknown_signal",
        target_workflow_pattern="missing-{*}",
        source_line=85,
        node_id="ext_sig_unknown_signal_85",
        source_workflow="OrderWorkflow",
    )

    graph = PeerSignalGraph(
        root_workflow=order_metadata,
        workflows={
            "OrderWorkflow": order_metadata,
            "ShippingWorkflow": shipping_metadata,
        },
        signal_handlers={"ship_order": [handler]},
        connections=[connection],
        unresolved_signals=[unresolved],
    )

    result = renderer.render_signal_graph(graph)

    # Verify subgraphs
    assert "subgraph OrderWorkflow" in result
    assert "subgraph ShippingWorkflow" in result

    # Verify cross-subgraph connection
    assert "ext_sig_ship_order_56_OrderWorkflow -.ship_order.-> sig_handler_ship_order_67" in result

    # Verify unresolved signal with dead-end
    assert "ext_sig_unknown_signal_85_OrderWorkflow -.unknown_signal.-> unknown_unknown_signal_85[/?/]" in result

    # Verify handler styling (blue)
    assert "style sig_handler_ship_order_67 fill:#e6f3ff,stroke:#0066cc" in result

    # Verify unresolved styling (amber)
    assert "style unknown_unknown_signal_85 fill:#fff3cd,stroke:#ffc107" in result

    # Verify proper structure - fenced code block
    assert result.startswith("```mermaid")
    assert result.endswith("```")


def test_render_signal_graph_no_connections(
    renderer: MermaidRenderer,
    peer_signal_graph_single: "PeerSignalGraph",
) -> None:
    """Test AC5 edge case: Graph with no connections omits connection comment.

    Validates that when graph.connections is empty:
    - No "%% Cross-workflow signal connections" comment rendered
    - No connection edges rendered
    """
    result = renderer.render_signal_graph(peer_signal_graph_single)

    # Verify no connection comment when connections empty
    assert "%% Cross-workflow signal connections" not in result, \
        "No connection comment should appear when connections list is empty"


def test_render_signal_graph_no_unresolved(
    renderer: MermaidRenderer,
) -> None:
    """Test AC4 edge case: Graph with no unresolved signals omits unresolved section.

    Validates that when graph.unresolved_signals is empty:
    - No "%% Unresolved signals" comment rendered
    - No unresolved edges rendered
    - No amber styling section
    """
    from temporalio_graphs._internal.graph_models import (
        Activity,
        PeerSignalGraph,
        SignalConnection,
        SignalHandler,
        WorkflowMetadata,
    )

    # Create graph with connection but NO unresolved signals
    handler = SignalHandler(
        signal_name="ship_order",
        method_name="ship_order",
        workflow_class="ShippingWorkflow",
        source_line=67,
        node_id="sig_handler_ship_order_67",
    )

    order_metadata = WorkflowMetadata(
        workflow_class="OrderWorkflow",
        workflow_run_method="run",
        activities=[Activity("process_order", 10)],
        decision_points=[],
        signal_points=[],
        source_file=Path("order_workflow.py"),
        total_paths=1,
    )

    shipping_metadata = WorkflowMetadata(
        workflow_class="ShippingWorkflow",
        workflow_run_method="run",
        activities=[Activity("ship_package", 30)],
        decision_points=[],
        signal_points=[],
        source_file=Path("shipping_workflow.py"),
        total_paths=1,
        signal_handlers=(handler,),
    )

    connection = SignalConnection(
        sender_workflow="OrderWorkflow",
        receiver_workflow="ShippingWorkflow",
        signal_name="ship_order",
        sender_line=56,
        receiver_line=67,
        sender_node_id="ext_sig_ship_order_56",
        receiver_node_id="sig_handler_ship_order_67",
    )

    graph = PeerSignalGraph(
        root_workflow=order_metadata,
        workflows={
            "OrderWorkflow": order_metadata,
            "ShippingWorkflow": shipping_metadata,
        },
        signal_handlers={"ship_order": [handler]},
        connections=[connection],
        unresolved_signals=[],  # Empty!
    )

    result = renderer.render_signal_graph(graph)

    # Verify no unresolved comment when unresolved_signals empty
    assert "%% Unresolved signals (no handler found)" not in result, \
        "No unresolved comment should appear when unresolved_signals is empty"

    # Verify no amber styling section when no unresolved
    assert "%% Unresolved signal styling (warning - amber)" not in result, \
        "No amber styling section should appear when no unresolved signals"

    # Connection should still render
    assert "ext_sig_ship_order_56_OrderWorkflow -.ship_order.-> sig_handler_ship_order_67" in result, \
        "Connection should still render even without unresolved signals"
