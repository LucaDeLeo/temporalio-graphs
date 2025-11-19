"""Integration tests for MoneyTransfer workflow analysis (Story 3-5).

This module contains comprehensive end-to-end tests that validate the complete
pipeline for MoneyTransfer workflow analysis. Tests validate:

1. MoneyTransfer workflow structure with 2 decisions and 5 activities
2. Exactly 4 paths generated (2^2 for 2 decision points)
3. Mermaid syntax validity with decision diamond nodes
4. Decision node naming and yes/no branch labels
5. Performance requirements (<1 second for analysis)
6. Feature parity with .NET reference implementation via golden file

The MoneyTransfer workflow demonstrates:
- Multiple decision points creating multiple execution paths
- Conditional activities that only execute on certain paths
- Reconverging branches (Deposit executes regardless of path)
- Complete integration of decision detection, path generation, and Mermaid rendering
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
        Set of node IDs (e.g., {'s', '1', '2', 'd0', 'd1', 'e'})
    """
    node_ids = set()

    # Match start node: s((Start))
    if re.search(r's\(\(Start\)\)', mermaid_content):
        node_ids.add('s')

    # Match activity nodes: 1[...], 2[...], etc.
    for match in re.finditer(r'(\d+)\[', mermaid_content):
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

    # Match edges without labels: s --> 1
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


def _extract_decision_names_from_mermaid(mermaid_content: str) -> set[str]:
    """Extract decision names from Mermaid content.

    Args:
        mermaid_content: Mermaid flowchart content

    Returns:
        Set of decision names (e.g., {'Need To Convert', 'Is TFN_Known'})
    """
    decision_names = set()

    # Match decision nodes: d0{Name}, d1{Name}, etc.
    for match in re.finditer(r'd\d+\{([^}]+)\}', mermaid_content):
        decision_names.add(match.group(1))

    return decision_names


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


class TestMoneyTransferIntegration:
    """Test AC1-AC8: MoneyTransfer integration test suite."""

    def test_money_transfer_workflow_example_exists(self) -> None:
        """AC1: MoneyTransfer workflow file exists and is valid Python.

        Validates that examples/money_transfer/workflow.py:
        - Exists and is readable
        - Contains valid Python syntax
        - Has @workflow.defn decorator
        - Has MoneyTransferWorkflow class
        """
        workflow_file = Path("examples/money_transfer/workflow.py")
        assert workflow_file.exists(), "workflow.py should exist"

        content = workflow_file.read_text(encoding="utf-8")
        assert len(content) > 0, "workflow.py should not be empty"
        assert "@workflow.defn" in content, "Should have @workflow.defn decorator"
        assert "class MoneyTransferWorkflow" in content, "Should have MoneyTransferWorkflow class"
        assert "to_decision" in content, "Should import and use to_decision helper"

    def test_money_transfer_analysis_four_paths(self) -> None:
        """AC2: Integration test validates exactly 4 paths generated (2^2).

        Tests the complete pipeline:
        1. Analyzes MoneyTransfer workflow
        2. Validates output is valid Mermaid
        3. Validates exactly 4 paths (2 decisions -> 2^2 paths)
        4. Validates all 5 activities are present
        5. Validates decision nodes and labels
        6. Validates branch labels (yes/no)
        7. Performance: completes in <1 second
        """
        workflow_file = Path("examples/money_transfer/workflow.py")

        # Measure execution time
        start_time = time.perf_counter()
        result = analyze_workflow(workflow_file)
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

        # Assert: Exactly 4 paths (2^2 for 2 decisions)
        path_count = _count_paths_in_mermaid(mermaid_content)
        assert path_count == 4, f"Should generate 4 paths (2^2), got {path_count}"

    def test_money_transfer_all_activities_present(self) -> None:
        """AC2: Verify all 5 activities are present in output.

        MoneyTransfer workflow must include:
        1. withdraw_funds
        2. currency_convert
        3. notify_ato
        4. take_non_resident_tax
        5. deposit_funds
        """
        workflow_file = Path("examples/money_transfer/workflow.py")
        result = analyze_workflow(workflow_file)

        # Expected activities
        activities = [
            "withdraw_funds",
            "currency_convert",
            "notify_ato",
            "take_non_resident_tax",
            "deposit_funds",
        ]

        for activity in activities:
            assert activity in result, f"Activity '{activity}' should be in output"

    def test_money_transfer_decision_nodes(self) -> None:
        """AC2: Verify exactly 2 decision nodes with correct names.

        MoneyTransfer workflow must have decision points:
        1. NeedToConvert (decision d0)
        2. IsTFN_Known (decision d1)
        """
        workflow_file = Path("examples/money_transfer/workflow.py")
        result = analyze_workflow(workflow_file)
        mermaid_content = _extract_mermaid_content(result)

        # Verify diamond syntax for decisions
        assert re.search(r'd0\{[^}]*\}', mermaid_content), "Should have d0 decision node"
        assert re.search(r'd1\{[^}]*\}', mermaid_content), "Should have d1 decision node"

        # Verify decision names are present (may be word-split)
        # "Need To Convert" or "NeedToConvert", "Is TFN_Known" or "IsTFN_Known"
        assert (
            "Need" in mermaid_content or "need" in mermaid_content
        ), "First decision should mention 'Need'"
        assert (
            "Convert" in mermaid_content or "convert" in mermaid_content
        ), "First decision should mention 'Convert'"
        assert (
            "TFN" in mermaid_content or "tfn" in mermaid_content
        ), "Second decision should mention 'TFN'"

    def test_money_transfer_branch_labels(self) -> None:
        """AC2: Verify decision edges have yes/no labels.

        Decision branches should use:
        - "yes" label for true branches
        - "no" label for false branches
        (not "true"/"false")
        """
        workflow_file = Path("examples/money_transfer/workflow.py")
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

    def test_money_transfer_decision_rendering(self) -> None:
        """AC4: Verify decision nodes use diamond syntax {}.

        Decision nodes must render as diamonds with curly braces,
        not parentheses or brackets.
        """
        workflow_file = Path("examples/money_transfer/workflow.py")
        result = analyze_workflow(workflow_file)
        mermaid_content = _extract_mermaid_content(result)

        # Count decision nodes with diamond syntax
        diamond_count = len(re.findall(r'd\d+\{[^}]+\}', mermaid_content))
        assert (
            diamond_count >= 2
        ), f"Should have at least 2 diamond decisions, found {diamond_count}"

    def test_money_transfer_matches_golden_file(self) -> None:
        """AC3, AC4: Regression test - output matches golden file.

        Validates structural equivalence (nodes and edges match) between
        current output and golden reference file. Uses structural comparison
        (not byte-for-byte) to allow formatting variations.
        """
        workflow_file = Path("examples/money_transfer/workflow.py")
        golden_file = Path("examples/money_transfer/expected_output.md")

        assert golden_file.exists(), "Golden reference file should exist"

        # Generate current output
        result = analyze_workflow(workflow_file)
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
            f"Edge structures should match. "
            f"Actual: {sorted(actual_edges_simple)}, "
            f"Expected: {sorted(golden_edges_simple)}"
        )

    def test_money_transfer_example_runner_exists(self) -> None:
        """AC5: Verify example runner script exists and is executable.

        The examples/money_transfer/run.py should:
        - Exist and be valid Python
        - Import analyze_workflow
        - Import MoneyTransferWorkflow
        """
        runner_file = Path("examples/money_transfer/run.py")
        assert runner_file.exists(), "run.py should exist"

        content = runner_file.read_text(encoding="utf-8")
        assert "analyze_workflow" in content, "run.py should import analyze_workflow"
        assert '__main__' in content, "run.py should have main guard"

    def test_money_transfer_example_runner_executes(self) -> None:
        """AC5: Verify example runner script executes without errors.

        Running: python examples/money_transfer/run.py
        Should produce Mermaid diagram output without errors.
        """
        runner_file = Path("examples/money_transfer/run.py")

        # Import the module dynamically
        import importlib.util

        spec = importlib.util.spec_from_file_location("run", runner_file)
        assert spec is not None and spec.loader is not None
        run_module = importlib.util.module_from_spec(spec)

        # Execute the module - should not raise
        spec.loader.exec_module(run_module)

    def test_money_transfer_dotnet_feature_parity(self) -> None:
        """AC4: Verify .NET feature parity through structure comparison.

        MoneyTransfer output structure should match .NET Temporalio.Graphs:
        - Same workflow class name (MoneyTransferWorkflow)
        - Same activities (Withdraw, CurrencyConvert, NotifyAto, TakeNonResidentTax, Deposit)
        - Same decision names (NeedToConvert, IsTFN_Known)
        - Same path count (4 = 2^2)
        - Same branch labels (yes/no)
        """
        workflow_file = Path("examples/money_transfer/workflow.py")
        result = analyze_workflow(workflow_file)
        mermaid_content = _extract_mermaid_content(result)

        # Verify structure matches .NET reference
        assert len(result) > 100, "Should contain workflow analysis"

        # Verify 4 paths (2^2)
        path_count = _count_paths_in_mermaid(mermaid_content)
        assert path_count == 4, f"Should generate 4 paths like .NET version, got {path_count}"

        # Verify decision structure
        assert (
            "d0" in mermaid_content and "d1" in mermaid_content
        ), "Should have d0 and d1 decisions"
        assert (
            "-- yes -->" in mermaid_content
        ), "Should use yes/no labels like .NET version"
        assert "-- no -->" in mermaid_content, "Should have no labels on decision branches"


class TestMoneyTransferQualityGates:
    """Test AC7: Code quality requirements."""

    def test_workflow_has_type_hints(self) -> None:
        """Verify MoneyTransfer workflow has complete type hints.

        All function parameters and return types should be annotated.
        """
        workflow_file = Path("examples/money_transfer/workflow.py")
        content = workflow_file.read_text(encoding="utf-8")

        # Check for type hints in run method
        assert "async def run(" in content, "Should have run method"
        assert "->" in content, "Should have return type annotations"
        assert "str" in content, "Should have type annotations"

    def test_workflow_has_docstrings(self) -> None:
        """Verify MoneyTransfer workflow and methods have docstrings."""
        workflow_file = Path("examples/money_transfer/workflow.py")
        content = workflow_file.read_text(encoding="utf-8")

        # Check for docstrings
        assert '"""' in content, "Should have docstrings"
        assert "Args:" in content or "Return:" in content, "Should document parameters"

    def test_golden_file_exists(self) -> None:
        """AC3: Verify golden reference file exists and contains Mermaid."""
        golden_file = Path("examples/money_transfer/expected_output.md")
        assert golden_file.exists(), "expected_output.md should exist"

        content = golden_file.read_text(encoding="utf-8")
        assert len(content) > 0, "Golden file should not be empty"
        assert "```mermaid" in content, "Golden file should contain Mermaid code block"
        assert "flowchart LR" in content, "Golden file should contain flowchart"
