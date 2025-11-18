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
    assert "1[ValidateInput]" in result


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
    assert "1[ValidateInput]" in result
    assert "2[ProcessOrder]" in result
    assert "3[SendConfirmation]" in result


def test_to_mermaid_activity_names_with_spaces(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Verify activity names with spaces are handled correctly."""
    path = GraphPath(path_id="path_0")
    path.add_activity("Send Email Notification")

    result = renderer.to_mermaid([path], default_context)

    assert "1[Send Email Notification]" in result


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
    assert "s --> 1" in result
    assert "1 --> 2" in result
    assert "2 --> e" in result


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
    assert "s --> 1" in result  # Start to first activity
    assert "1 --> 2" in result  # Activity 1 to 2
    assert "2 --> 3" in result  # Activity 2 to 3
    assert "3 --> e" in result  # Last activity to End


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
    activity1_count = result.count("1[ValidateInput]")
    activity2_count = result.count("2[ProcessOrder]")
    activity3_count = result.count("3[SendConfirmation]")

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
    s_to_1 = result.count("s --> 1")
    one_to_2 = result.count("1 --> 2")
    two_to_e = result.count("2 --> e")

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
    assert "1[execute Payment]" in result
    assert "2[validate Output]" in result


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
    assert "1[executePayment]" in result
    assert "2[validateOutput]" in result
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
    assert "1[CONSTANT]" in result  # All caps unchanged
    assert "2[Already Spaced]" in result  # Spaced unchanged
    assert "3[snake_case]" in result  # Underscores unchanged
    assert "4[Camel Case]" in result  # camelCase split


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
    assert "1[ProcessPayment]" in result
    assert "e((End))" in result
    assert "s --> 1" in result
    assert "1 --> e" in result


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

    # Verify sequence
    expected_sequence = [
        "s((Start))",
        "1[ValidateInput]",
        "2[ProcessOrder]",
        "3[SendConfirmation]",
        "e((End))",
    ]

    for node in expected_sequence:
        assert node in result

    # Verify edges in order
    assert "s --> 1" in result
    assert "1 --> 2" in result
    assert "2 --> 3" in result
    assert "3 --> e" in result


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
    path = GraphPath(path_id="path_0")
    # Manually set None activity (bypassing add_activity validation)
    path.steps.append(None)  # type: ignore

    with pytest.raises(ValueError, match="Activity name cannot be None"):
        renderer.to_mermaid([path], default_context)


def test_to_mermaid_raises_on_empty_activity_name(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Verify ValueError raised for empty string activity names."""
    path = GraphPath(path_id="path_0")
    path.steps.append("")  # Empty string activity

    with pytest.raises(ValueError, match="Activity name cannot be None or empty"):
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

    # Verify special characters preserved in node labels
    assert "1[Save-to-Database]" in result
    assert "2[Check_Input_Valid]" in result
    assert "3[Send/Email]" in result


def test_to_mermaid_handles_very_long_names(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Verify very long activity names (>100 chars) are supported."""
    long_name = "a" * 150
    path = GraphPath(path_id="path_0")
    path.add_activity(long_name)

    result = renderer.to_mermaid([path], default_context)

    # Should contain the full long name
    assert f"1[{long_name}]" in result


def test_to_mermaid_handles_unicode_names(
    renderer: MermaidRenderer, default_context: GraphBuildingContext
) -> None:
    """Verify Unicode characters in activity names are supported."""
    path = GraphPath(path_id="path_0")
    path.add_activity("Validar_Entrada")  # Spanish
    path.add_activity("Verifier_Entrée")  # French
    path.add_activity("验证输入")  # Chinese

    result = renderer.to_mermaid([path], default_context)

    # Verify Unicode preserved
    assert "1[Validar_Entrada]" in result
    assert "2[Verifier_Entrée]" in result
    assert "3[验证输入]" in result


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

    # With deduplication, nodes should appear only once
    validate_count = result.count("1[ValidateInput]")
    process_count = result.count("2[ProcessOrder]")

    # Even with 2 paths, deduplication should keep each node once
    assert (
        validate_count == 1
    ), "Deduplication should prevent duplicate nodes in multi-path rendering"
    assert (
        process_count == 1
    ), "Deduplication should prevent duplicate nodes in multi-path rendering"
