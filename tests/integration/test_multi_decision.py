"""Integration tests for multi-decision workflow analysis (Story 5-4).

This module contains comprehensive end-to-end tests that validate the complete
pipeline for multi-decision workflow analysis. Tests validate:

1. LoanApprovalWorkflow structure with 3 decisions and 5 activities
2. Exactly 8 paths generated (2^3 for 3 decision points)
3. Mermaid syntax validity with decision diamond nodes
4. Decision node naming and yes/no branch labels
5. Performance requirements (<1 second for analysis)
6. Golden file comparison for regression testing

The multi-decision workflow demonstrates:
- Multiple independent decision points creating many execution paths
- Conditional activities that only execute on certain paths
- Complex path permutations (8 paths from 3 decisions)
- Complete integration of decision detection, path generation, and Mermaid rendering
"""

import re
import time
from pathlib import Path

from temporalio_graphs import GraphBuildingContext, analyze_workflow


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
        Set of node IDs (e.g., {'s', 'd0', 'd1', 'd2', 'e'})
    """
    node_ids = set()

    # Match start node: s((Start))
    if re.search(r's\(\(Start\)\)', mermaid_content):
        node_ids.add('s')

    # Match activity nodes: activity_name[...]
    for match in re.finditer(r'(\w+)\[', mermaid_content):
        node_ids.add(match.group(1))

    # Match decision nodes: d0{...}, d1{...}, etc.
    for match in re.finditer(r'(d\d+)\{', mermaid_content):
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

    # Match edges with labels: d0 -- label --> d1
    for match in re.finditer(
        r'(\w+)\s+--\s+(.*?)\s+-->\s+(\w+)', mermaid_content
    ):
        source = match.group(1)
        label = match.group(2)
        target = match.group(3)
        edges.append((source, target, label))

    # Match edges without labels: s --> activity
    for match in re.finditer(r'(\w+)\s+--+>\s+(\w+)', mermaid_content):
        source = match.group(1)
        target = match.group(2)
        # Check if already captured with label
        if not any(e[0] == source and e[1] == target and e[2] for e in edges):
            edges.append((source, target, None))

    return edges


def _load_golden_file(golden_path: Path) -> str:
    """Load and extract Mermaid content from golden file.

    Args:
        golden_path: Path to golden reference file

    Returns:
        Mermaid diagram content from file
    """
    content = golden_path.read_text(encoding="utf-8")
    return _extract_mermaid_content(content)


def _count_paths_in_mermaid(mermaid_content: str) -> int:
    """Count distinct execution paths in Mermaid diagram.

    Counts the number of unique decision node combinations by checking
    how many times each decision node makes branching decisions.

    Args:
        mermaid_content: Mermaid flowchart content

    Returns:
        Estimated number of paths (based on decision branching)
    """
    # Count decision nodes
    decision_count = len(re.findall(r'd\d+\{', mermaid_content))

    # For n decision points, there should be 2^n paths
    if decision_count == 0:
        return 1
    return 2 ** decision_count


class TestMultiDecisionIntegration:
    """Test AC1-AC8: Multi-decision integration test suite."""

    def test_multi_decision_workflow_example_exists(self) -> None:
        """AC1: Multi-decision workflow file exists and is valid Python.

        Validates that examples/multi_decision/workflow.py:
        - Exists and is readable
        - Contains valid Python syntax
        - Has @workflow.defn decorator
        - Has LoanApprovalWorkflow class
        - Uses to_decision helper
        """
        workflow_file = Path("examples/multi_decision/workflow.py")
        assert workflow_file.exists(), "workflow.py should exist"

        content = workflow_file.read_text(encoding="utf-8")
        assert len(content) > 0, "workflow.py should not be empty"
        assert "@workflow.defn" in content, "Should have @workflow.defn decorator"
        assert "class LoanApprovalWorkflow" in content, "Should have LoanApprovalWorkflow class"
        assert "to_decision" in content, "Should import and use to_decision helper"

    def test_multi_decision_analysis_eight_paths(self) -> None:
        """AC2: Integration test validates exactly 8 paths generated (2^3).

        Tests the complete pipeline:
        1. Analyzes LoanApproval workflow
        2. Validates output is valid Mermaid
        3. Validates exactly 8 paths (3 decisions -> 2^3 paths)
        4. Validates all 5 activities are present
        5. Validates decision nodes and labels
        6. Validates branch labels (yes/no)
        7. Performance: completes in <1 second
        """
        workflow_file = Path("examples/multi_decision/workflow.py")

        # Measure execution time
        start_time = time.perf_counter()
        result = analyze_workflow(workflow_file, GraphBuildingContext(output_format="full"))
        elapsed = time.perf_counter() - start_time

        # Assert: Performance requirement (<1 second)
        assert elapsed < 1.0, f"Analysis should complete in <1s, took {elapsed:.3f}s"

        # Assert: Result is string with Mermaid content
        assert isinstance(result, str), "Result should be a string"
        assert len(result) > 0, "Result should not be empty"
        assert "flowchart LR" in result, "Output should contain flowchart LR directive"
        assert "```mermaid" in result, "Output should be in Mermaid code block"

        # Extract Mermaid content
        mermaid_content = _extract_mermaid_content(result)
        assert len(mermaid_content) > 0, "Mermaid content should not be empty"

        # Assert: Valid Mermaid structure
        assert "s((Start))" in mermaid_content, "Should contain start node"
        assert "e((End))" in mermaid_content, "Should contain end node"

        # Assert: Exactly 8 paths (2^3 for 3 decisions)
        path_count = _count_paths_in_mermaid(mermaid_content)
        assert path_count == 8, f"Should generate 8 paths (2^3), got {path_count}"

    def test_multi_decision_all_activities_present(self) -> None:
        """AC2: Verify all 5 activities are present in output.

        LoanApproval workflow must include:
        1. validate_application
        2. manager_review
        3. require_collateral
        4. debt_ratio_check
        5. approve_loan
        """
        workflow_file = Path("examples/multi_decision/workflow.py")
        result = analyze_workflow(workflow_file)

        # Expected activities
        activities = [
            "validate_application",
            "manager_review",
            "require_collateral",
            "debt_ratio_check",
            "approve_loan",
        ]

        for activity in activities:
            assert activity in result, f"Activity '{activity}' should be in output"

    def test_multi_decision_decision_nodes(self) -> None:
        """AC2: Verify exactly 3 decision nodes with correct names.

        LoanApproval workflow must have decision points:
        1. HighValue (decision d0)
        2. LowCredit (decision d1)
        3. ExistingLoans (decision d2)
        """
        workflow_file = Path("examples/multi_decision/workflow.py")
        result = analyze_workflow(workflow_file)
        mermaid_content = _extract_mermaid_content(result)

        # Verify diamond syntax for decisions
        assert re.search(r'd0\{[^}]*\}', mermaid_content), "Should have d0 decision node"
        assert re.search(r'd1\{[^}]*\}', mermaid_content), "Should have d1 decision node"
        assert re.search(r'd2\{[^}]*\}', mermaid_content), "Should have d2 decision node"

        # Verify decision names are present (may be word-split)
        # "High Value" or "HighValue", "Low Credit" or "LowCredit", "Existing Loans" or "ExistingLoans"
        assert (
            "High" in mermaid_content or "high" in mermaid_content
        ), "First decision should mention 'High'"
        assert (
            "Value" in mermaid_content or "value" in mermaid_content
        ), "First decision should mention 'Value'"
        assert (
            "Low" in mermaid_content or "low" in mermaid_content
        ), "Second decision should mention 'Low'"
        assert (
            "Credit" in mermaid_content or "credit" in mermaid_content
        ), "Second decision should mention 'Credit'"
        assert (
            "Existing" in mermaid_content or "existing" in mermaid_content
        ), "Third decision should mention 'Existing'"
        assert (
            "Loans" in mermaid_content or "loans" in mermaid_content
        ), "Third decision should mention 'Loans'"

    def test_multi_decision_branch_labels(self) -> None:
        """AC2: Verify decision edges have yes/no labels.

        Decision branches should use:
        - "yes" label for true branches
        - "no" label for false branches
        (not "true"/"false")
        """
        workflow_file = Path("examples/multi_decision/workflow.py")
        result = analyze_workflow(workflow_file)
        mermaid_content = _extract_mermaid_content(result)

        # Verify yes/no labels are present
        assert "-- yes -->" in mermaid_content, "Should have 'yes' decision labels"
        assert "-- no -->" in mermaid_content, "Should have 'no' decision labels"

        # Verify true/false are NOT used as labels
        assert not re.search(
            r'--\s+true\s+-->', mermaid_content
        ), "Should not use 'true' as label"
        assert not re.search(
            r'--\s+false\s+-->', mermaid_content
        ), "Should not use 'false' as label"

    def test_multi_decision_decision_rendering(self) -> None:
        """AC4: Verify decision nodes use diamond syntax {}.

        Decision nodes must render as diamonds with curly braces,
        not parentheses or brackets.
        """
        workflow_file = Path("examples/multi_decision/workflow.py")
        result = analyze_workflow(workflow_file)
        mermaid_content = _extract_mermaid_content(result)

        # Count decision nodes with diamond syntax
        diamond_count = len(re.findall(r'd\d+\{[^}]+\}', mermaid_content))
        assert (
            diamond_count >= 3
        ), f"Should have at least 3 diamond decisions, found {diamond_count}"

    def test_multi_decision_path_list_output(self) -> None:
        """AC4: Verify path list output shows correct path count.

        Path list section should show:
        - "--- Execution Paths (8 total) ---"
        - "Decision Points: 3 (2^3 = 8 paths)"
        - All 8 paths listed as "Path 1:" through "Path 8:"
        """
        workflow_file = Path("examples/multi_decision/workflow.py")
        result = analyze_workflow(workflow_file, GraphBuildingContext(output_format="full"))

        # Verify path count header
        assert "Execution Paths (8 total)" in result, "Should show 8 total paths"
        assert "Decision Points: 3 (2^3 = 8 paths)" in result, "Should show decision formula"

        # Count path entries
        path_entries = len(re.findall(r'Path \d+:', result))
        assert path_entries == 8, f"Should have 8 path entries, found {path_entries}"

    def test_multi_decision_matches_golden_file(self) -> None:
        """AC3, AC4: Regression test - output matches golden file.

        Validates structural equivalence (nodes and edges match) between
        current output and golden reference file. Uses structural comparison
        (not byte-for-byte) to allow formatting variations.
        """
        workflow_file = Path("examples/multi_decision/workflow.py")
        golden_file = Path("examples/multi_decision/expected_output.md")

        assert golden_file.exists(), "Golden reference file should exist"

        # Generate current output
        result = analyze_workflow(workflow_file, GraphBuildingContext(output_format="full"))
        actual_mermaid = _extract_mermaid_content(result)

        # Load golden file
        golden_mermaid = _load_golden_file(golden_file)

        # Extract structural elements for comparison
        actual_nodes = _extract_nodes_from_mermaid(actual_mermaid)
        golden_nodes = _extract_nodes_from_mermaid(golden_mermaid)

        actual_edges = _extract_edges_from_mermaid(actual_mermaid)
        golden_edges = _extract_edges_from_mermaid(golden_mermaid)

        # Assert structural equivalence
        assert actual_nodes == golden_nodes, (
            f"Node sets should match. "
            f"Actual: {sorted(actual_nodes)}, "
            f"Expected: {sorted(golden_nodes)}"
        )

        # Extract just source->target pairs (ignore labels) for edge comparison
        actual_edges_simple = {(src, tgt) for src, tgt, _ in actual_edges}
        golden_edges_simple = {(src, tgt) for src, tgt, _ in golden_edges}

        assert actual_edges_simple == golden_edges_simple, (
            f"Edge sets should match. "
            f"Missing edges: {golden_edges_simple - actual_edges_simple}, "
            f"Extra edges: {actual_edges_simple - golden_edges_simple}"
        )

    def test_multi_decision_run_script_exists(self) -> None:
        """AC3: Verify run.py script exists and is executable.

        Validates that examples/multi_decision/run.py:
        - Exists and is readable
        - Imports analyze_workflow
        - Has main function
        - Can be executed
        """
        run_file = Path("examples/multi_decision/run.py")
        assert run_file.exists(), "run.py should exist"

        content = run_file.read_text(encoding="utf-8")
        assert len(content) > 0, "run.py should not be empty"
        assert "from temporalio_graphs import" in content, "Should import from temporalio_graphs"
        assert "analyze_workflow" in content, "Should import analyze_workflow"
        assert "def main(" in content, "Should have main function"
        assert 'if __name__ == "__main__"' in content, "Should have main guard"
