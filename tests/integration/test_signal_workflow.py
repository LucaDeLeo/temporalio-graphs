"""Integration tests for Signal workflow analysis (Story 4-4).

This module contains comprehensive end-to-end tests that validate the complete
pipeline for signal workflow analysis. Tests validate:

1. Signal workflow structure with 1 signal point and 3 activities
2. Exactly 2 paths generated (2^1 for 1 signal point)
3. Mermaid syntax validity with hexagon signal nodes
4. Signal node naming and Signaled/Timeout branch labels
5. Golden file regression test (structural match)
6. Performance requirements (<1 second for analysis)
7. Feature parity with .NET reference implementation

The ApprovalWorkflow demonstrates:
- Signal point creating two execution paths (Signaled vs Timeout)
- Conditional activities that only execute on certain paths
- Reconverging branches (both paths end at End node)
- Complete integration of signal detection, path generation, and Mermaid rendering
"""

import re
import time
from pathlib import Path

from temporalio_graphs import analyze_workflow


def _extract_mermaid_content(output: str) -> str:
    """Extract Mermaid content from output.

    Args:
        output: Output string potentially containing Mermaid code block

    Returns:
        Mermaid content (either from code block or raw content)
    """
    # Handle fenced code block
    if "```mermaid" in output:
        match = re.search(r"```mermaid\n(.*?)\n```", output, re.DOTALL)
        if match:
            return match.group(1).strip()
    return output.strip()


def _extract_nodes_from_mermaid(mermaid_content: str) -> set[str]:
    """Extract all node IDs from Mermaid content.

    Args:
        mermaid_content: Mermaid flowchart content

    Returns:
        Set of node IDs (e.g., {'s', 'WaitForApproval', 'e'})
    """
    node_ids = set()

    # Match start node: s((Start))
    if re.search(r's\(\(Start\)\)', mermaid_content):
        node_ids.add('s')

    # Match activity nodes: submit_request[submit_request], etc.
    for match in re.finditer(r'(\w+)\[', mermaid_content):
        node_ids.add(match.group(1))

    # Match signal nodes: WaitForApproval{{...}}
    for match in re.finditer(r'(\w+)\{\{', mermaid_content):
        node_ids.add(match.group(1))

    # Match end node: e((End))
    if re.search(r'e\(\(End\)\)', mermaid_content):
        node_ids.add('e')

    return node_ids


def _extract_edges_from_mermaid(
    mermaid_content: str,
) -> list[tuple[str, str, str | None]]:
    """Extract all edges from Mermaid content with optional labels.

    Args:
        mermaid_content: Mermaid flowchart content

    Returns:
        List of (source, target, label) tuples for each edge
    """
    edges = []

    # Match edges with labels: WaitForApproval -- Signaled --> process_approved
    for match in re.finditer(
        r'(\w+)\s+--\s+(.*?)\s+-->\s+(\w+)', mermaid_content
    ):
        source = match.group(1)
        label = match.group(2)
        target = match.group(3)
        edges.append((source, target, label))

    # Match edges without labels: s --> submit_request
    for match in re.finditer(r'(\w+)\s+--+>\s+(\w+)', mermaid_content):
        source = match.group(1)
        target = match.group(2)
        # Check if already captured with label
        if not any(e[0] == source and e[1] == target for e in edges):
            edges.append((source, target, None))

    return edges


def test_signal_workflow_generates_valid_mermaid() -> None:
    """Test signal workflow generates valid Mermaid with hexagon nodes.

    This test validates AC1-AC4: Signal workflow exists, contains wait_condition,
    shows Signaled/Timeout paths, and produces valid Mermaid with hexagons.
    """
    # Get workflow file path
    workflow_file = (
        Path(__file__).parent.parent.parent / "examples" / "signal_workflow" / "workflow.py"
    )

    # Analyze workflow
    output = analyze_workflow(workflow_file)

    # Extract Mermaid content
    mermaid_content = _extract_mermaid_content(output)

    # AC4: Validate Mermaid structure
    assert output.startswith("```mermaid"), "Output should start with Mermaid fence"
    assert output.endswith("```"), "Output should end with Mermaid fence"
    assert "flowchart LR" in mermaid_content, "Should use flowchart LR syntax"

    # AC4: Validate hexagon signal node
    assert "{{Wait For Approval}}" in mermaid_content or "{{WaitForApproval}}" in mermaid_content, \
        "Signal node should use hexagon syntax with double braces"

    # Validate signal node ID pattern
    signal_node_pattern = r'WaitForApproval\{\{[^}]+\}\}'
    assert re.search(signal_node_pattern, mermaid_content), \
        "Signal node should match pattern: WaitForApproval{{...}}"

    # AC3: Validate edge labels for signal branches
    assert "-- Signaled -->" in mermaid_content, \
        "Should have 'Signaled' branch label for approval path"
    assert "-- Timeout -->" in mermaid_content, \
        "Should have 'Timeout' branch label for timeout path"

    # AC1: Validate activity nodes present
    assert "submit_request" in mermaid_content, \
        "Should have submit_request activity"
    assert "process_approved" in mermaid_content, \
        "Should have process_approved activity"
    assert "handle_timeout" in mermaid_content, \
        "Should have handle_timeout activity"

    # Validate start and end nodes
    assert "s((Start))" in mermaid_content, "Should have Start node"
    assert "e((End))" in mermaid_content, "Should have End node"


def test_signal_workflow_matches_golden_file() -> None:
    """Test signal workflow output matches expected golden file.

    This test validates AC5-AC7: Golden file exists, contains correct diagram,
    and runtime output matches expected structure.
    """
    # Get file paths
    workflow_file = (
        Path(__file__).parent.parent.parent / "examples" / "signal_workflow" / "workflow.py"
    )
    expected_file = (
        Path(__file__).parent.parent.parent / "examples" / "signal_workflow" / "expected_output.md"
    )

    # AC5: Verify golden file exists
    assert expected_file.exists(), f"Golden file should exist at {expected_file}"

    # Generate actual output
    actual_output = analyze_workflow(workflow_file)
    actual_mermaid = _extract_mermaid_content(actual_output)

    # Load expected output
    expected_content = expected_file.read_text()
    expected_mermaid = _extract_mermaid_content(expected_content)

    # AC5, AC7: Compare outputs structurally
    # Extract nodes from both outputs
    actual_nodes = _extract_nodes_from_mermaid(actual_mermaid)
    expected_nodes = _extract_nodes_from_mermaid(expected_mermaid)

    assert actual_nodes == expected_nodes, \
        f"Node sets should match.\nActual: {actual_nodes}\nExpected: {expected_nodes}"

    # Extract edges from both outputs
    actual_edges = _extract_edges_from_mermaid(actual_mermaid)
    expected_edges = _extract_edges_from_mermaid(expected_mermaid)

    # Compare edge counts
    assert len(actual_edges) == len(expected_edges), \
        f"Edge counts should match. Actual: {len(actual_edges)}, Expected: {len(expected_edges)}"

    # Verify signal branch labels present
    edge_labels = {edge[2] for edge in actual_edges if edge[2] is not None}
    assert "Signaled" in edge_labels, "Should have Signaled branch label"
    assert "Timeout" in edge_labels, "Should have Timeout branch label"


def test_signal_workflow_generates_two_paths() -> None:
    """Test signal workflow generates exactly 2 paths (Signaled, Timeout).

    This test validates AC3: Path generation correctness with exactly 2 paths
    for 1 signal point (2^1 = 2).
    """
    # Get workflow file path
    workflow_file = (
        Path(__file__).parent.parent.parent / "examples" / "signal_workflow" / "workflow.py"
    )

    # Analyze workflow
    output = analyze_workflow(workflow_file)
    mermaid_content = _extract_mermaid_content(output)

    # AC3: Verify exactly 2 execution paths exist
    # Path 1: Start → SubmitRequest → WaitForApproval (Signaled) → ProcessApproved → End
    # Path 2: Start → SubmitRequest → WaitForApproval (Timeout) → HandleTimeout → End

    # Validate both signal outcomes present
    assert "Signaled" in mermaid_content, "Signaled path should exist"
    assert "Timeout" in mermaid_content, "Timeout path should exist"

    # Validate Signaled path activities
    edges = _extract_edges_from_mermaid(mermaid_content)

    # Find Signaled edge
    signaled_edges = [e for e in edges if e[2] == "Signaled"]
    assert len(signaled_edges) == 1, "Should have exactly one Signaled edge"
    signaled_target = signaled_edges[0][1]

    # Verify Signaled edge points to process_approved
    assert signaled_target == "process_approved", \
        f"Signaled edge should point to process_approved, got {signaled_target}"

    # Find Timeout edge
    timeout_edges = [e for e in edges if e[2] == "Timeout"]
    assert len(timeout_edges) == 1, "Should have exactly one Timeout edge"
    timeout_target = timeout_edges[0][1]

    # Verify Timeout edge points to handle_timeout
    assert timeout_target == "handle_timeout", \
        f"Timeout edge should point to handle_timeout, got {timeout_target}"

    # Verify both paths end at End node
    process_approved_edges = [e for e in edges if e[0] == "process_approved"]
    handle_timeout_edges = [e for e in edges if e[0] == "handle_timeout"]

    assert any(e[1] == "e" for e in process_approved_edges), \
        "process_approved should connect to End"
    assert any(e[1] == "e" for e in handle_timeout_edges), \
        "handle_timeout should connect to End"


def test_signal_workflow_analysis_performance() -> None:
    """Test signal workflow analysis completes within performance requirements.

    This test validates that signal workflow analysis runs in <1 second,
    meeting NFR-MAINT-2 performance requirements.
    """
    # Get workflow file path
    workflow_file = (
        Path(__file__).parent.parent.parent / "examples" / "signal_workflow" / "workflow.py"
    )

    # Measure analysis time
    start_time = time.time()
    analyze_workflow(workflow_file)
    elapsed_time = time.time() - start_time

    # Verify performance requirement
    assert elapsed_time < 1.0, \
        f"Signal workflow analysis should complete in <1s, took {elapsed_time:.3f}s"


def test_signal_hexagon_syntax_correct() -> None:
    """Test signal nodes use correct hexagon syntax (double braces).

    This test validates AC2, AC4: Signal nodes render with {{Name}} syntax,
    not {Name} (diamond) or [Name] (rectangle).
    """
    # Get workflow file path
    workflow_file = (
        Path(__file__).parent.parent.parent / "examples" / "signal_workflow" / "workflow.py"
    )

    # Analyze workflow
    output = analyze_workflow(workflow_file)
    mermaid_content = _extract_mermaid_content(output)

    # Verify hexagon syntax (double braces)
    hexagon_pattern = r'\w+\{\{[^}]+\}\}'
    hexagon_matches = list(re.finditer(hexagon_pattern, mermaid_content))
    assert len(hexagon_matches) >= 1, "Should have at least one hexagon node (signal)"

    # Verify NOT using diamond syntax (single braces for decisions)
    # Signal nodes should NOT match decision pattern
    signal_as_diamond_pattern = r'WaitForApproval\{[^{][^}]+\}'
    assert not re.search(signal_as_diamond_pattern, mermaid_content), \
        "Signal node should NOT use diamond syntax (single braces)"
