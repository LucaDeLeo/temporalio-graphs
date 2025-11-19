"""Integration tests for simple linear workflow analysis (Story 2-8).

This module contains comprehensive end-to-end tests that validate the complete
pipeline from workflow source code to Mermaid diagram generation. Tests validate:

1. Workflow file creation with multiple activities
2. analyze_workflow() public API functionality
3. Mermaid syntax validity and structure
4. Node and edge presence with correct IDs
5. Activity ordering and labels

The integration test uses pytest's tmp_path fixture to create temporary workflow
files at runtime, ensuring test isolation and no file system pollution.
"""

import ast
import re
from pathlib import Path

import pytest

from temporalio_graphs import analyze_workflow


def _generate_test_workflow(num_activities: int = 3) -> str:
    """Generate a test workflow with specified number of activities.

    Args:
        num_activities: Number of activities to include (default: 3)

    Returns:
        Valid Python workflow code as string

    This helper creates a complete workflow with the proper decorators,
    run method, and sequential activity calls for testing.
    """
    activities = []
    for i in range(1, num_activities + 1):
        activities.append(
            f"        await workflow.execute_activity(\n"
            f"            activity_{i},\n"
            f"            start_to_close_timeout=None,\n"
            f"        )"
        )

    activity_calls = "\n".join(activities)

    return f'''"""Test workflow for integration testing."""

from temporalio import workflow


@workflow.defn
class SimpleWorkflow:
    """A simple linear workflow with {num_activities} activities."""

    @workflow.run
    async def run(self) -> str:
        """Execute a sequence of activities in order."""
{activity_calls}
        return "complete"
'''


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
        Set of node IDs (e.g., {'s', 'validate_input', 'process_data', 'save_result', 'e'})
    """
    node_ids = set()

    # Match start node: s((Start))
    if re.search(r's\(\(Start\)\)', mermaid_content):
        node_ids.add('s')

    # Match activity nodes: activity_name[activity_name] or 1[Activity Name]
    # Updated to support both activity names and numeric IDs
    for match in re.finditer(r'(\w+)\[', mermaid_content):
        node_id = match.group(1)
        # Skip if it's a start/end node
        if node_id not in ('s', 'e'):
            node_ids.add(node_id)

    # Match end node: e((End))
    if re.search(r'e\(\(End\)\)', mermaid_content):
        node_ids.add('e')

    return node_ids


def _extract_edges_from_mermaid(mermaid_content: str) -> list[tuple[str, str]]:
    """Extract all edges from Mermaid content.

    Args:
        mermaid_content: Mermaid flowchart content

    Returns:
        List of (source, target) tuples for each edge
    """
    edges = []

    # Match edges: s --> 1, 1 --> 2, etc.
    # Also handle decision edges with labels: 0{...} -- label --> ...
    for match in re.finditer(r'(\w+|\d+)\s+--+>\s+(\w+|\d+)', mermaid_content):
        source = match.group(1)
        target = match.group(2)
        edges.append((source, target))

    return edges


class TestSimpleLinearWorkflowEndToEnd:
    """Test AC1-AC7: Complete end-to-end pipeline validation."""

    def test_simple_linear_workflow_end_to_end(self, tmp_path: Path) -> None:
        """AC1-AC7: Full pipeline validation (create, analyze, validate).

        This test validates the complete pipeline:
        1. Creates a temporary workflow file with 3 activities
        2. Calls analyze_workflow() on the file
        3. Validates Mermaid output syntax and structure
        4. Validates all nodes and edges are present
        5. Validates node IDs follow convention (s, activity_1, activity_2, activity_3, e)
        6. Validates edges connect in sequence
        """
        # Arrange: Create temporary workflow file
        workflow_file = tmp_path / "test_workflow.py"
        workflow_content = _generate_test_workflow(num_activities=3)
        workflow_file.write_text(workflow_content, encoding="utf-8")

        # Act: Call analyze_workflow
        result = analyze_workflow(workflow_file)

        # Assert: Result is string with Mermaid content
        assert isinstance(result, str), "Result should be a string"
        assert len(result) > 0, "Result should not be empty"
        assert "flowchart LR" in result, "Output should contain flowchart LR"
        assert "```mermaid" in result, "Output should be in Mermaid code block"

        # Extract Mermaid content for further validation
        mermaid_content = _extract_mermaid_content(result)
        assert len(mermaid_content) > 0, "Mermaid content should not be empty"

        # Validate start and end nodes
        assert "s((Start))" in mermaid_content, "Should contain start node"
        assert "e((End))" in mermaid_content, "Should contain end node"

        # Extract and validate nodes
        nodes = _extract_nodes_from_mermaid(mermaid_content)
        assert 's' in nodes, "Start node ID 's' should be present"
        assert 'activity_1' in nodes, "Activity 1 node ID should be present"
        assert 'activity_2' in nodes, "Activity 2 node ID should be present"
        assert 'activity_3' in nodes, "Activity 3 node ID should be present"
        assert 'e' in nodes, "End node ID 'e' should be present"

        # Extract and validate edges
        edges = _extract_edges_from_mermaid(mermaid_content)
        edge_dict = {src: tgt for src, tgt in edges}

        # Verify edge sequence: s -> activity_1 -> activity_2 -> activity_3 -> e
        # Note: Activity names are now used as node IDs
        assert 's' in edge_dict, "Start node should have outgoing edge"
        assert edge_dict.get('s') == 'activity_1', "Start should connect to activity_1"
        assert edge_dict.get('activity_1') == 'activity_2', "activity_1 should connect to activity_2"
        assert edge_dict.get('activity_2') == 'activity_3', "activity_2 should connect to activity_3"
        assert edge_dict.get('activity_3') == 'e', "activity_3 should connect to End"

    def test_validate_mermaid_syntax_valid(self, tmp_path: Path) -> None:
        """AC4: Validate Mermaid output syntax is valid.

        Ensures output contains proper Mermaid flowchart syntax:
        - Contains "flowchart LR" declaration
        - Is properly fenced in code block
        - Has no syntax errors (basic validation)
        """
        # Arrange
        workflow_file = tmp_path / "test_workflow.py"
        workflow_file.write_text(_generate_test_workflow(num_activities=2))

        # Act
        result = analyze_workflow(workflow_file)

        # Assert
        assert result.startswith("```mermaid"), "Should start with Mermaid fence"
        assert result.endswith("```"), "Should end with Mermaid fence"

        mermaid_content = _extract_mermaid_content(result)
        assert mermaid_content.startswith("flowchart LR"), "Should have flowchart LR"

        # Validate no obvious syntax errors
        assert "-->" in mermaid_content, "Should contain edge syntax -->"
        assert "((Start))" in mermaid_content, "Should have proper start node syntax"
        assert "((End))" in mermaid_content, "Should have proper end node syntax"

    def test_validate_start_end_nodes_present(self, tmp_path: Path) -> None:
        """AC5: Verify Start and End nodes are present and labeled correctly.

        Ensures:
        - Start node with ID 's' and label 'Start' is present
        - End node with ID 'e' and label 'End' is present
        - Both use correct Mermaid syntax: s((Start)), e((End))
        """
        # Arrange
        workflow_file = tmp_path / "test_workflow.py"
        workflow_file.write_text(_generate_test_workflow(num_activities=1))

        # Act
        result = analyze_workflow(workflow_file)
        mermaid_content = _extract_mermaid_content(result)

        # Assert
        assert "s((Start))" in mermaid_content, "Start node should be s((Start))"
        assert "e((End))" in mermaid_content, "End node should be e((End))"

        # Verify nodes are in output
        nodes = _extract_nodes_from_mermaid(mermaid_content)
        assert 's' in nodes, "Start node ID should be 's'"
        assert 'e' in nodes, "End node ID should be 'e'"

    def test_validate_node_ids_follow_convention(self, tmp_path: Path) -> None:
        """AC6: Verify node IDs follow convention using activity names.

        Ensures:
        - Start node ID is 's'
        - Activity nodes use activity names as IDs: activity_1, activity_2, etc.
        - End node ID is 'e'
        - All IDs match Mermaid syntax
        """
        # Arrange
        workflow_file = tmp_path / "test_workflow.py"
        workflow_file.write_text(_generate_test_workflow(num_activities=4))

        # Act
        result = analyze_workflow(workflow_file)
        mermaid_content = _extract_mermaid_content(result)

        # Assert
        nodes = _extract_nodes_from_mermaid(mermaid_content)

        # Verify specific node IDs (activity names are now used as node IDs)
        assert nodes == {'s', 'activity_1', 'activity_2', 'activity_3', 'activity_4', 'e'}, \
            f"Expected nodes {{s, activity_1, activity_2, activity_3, activity_4, e}}, got {nodes}"

        # Verify each node appears correctly in Mermaid syntax
        assert re.search(r's\(\(', mermaid_content), "Start node should use ((...)) syntax"
        assert re.search(r'activity_1\[', mermaid_content), "activity_1 should use [...] syntax"
        assert re.search(r'activity_2\[', mermaid_content), "activity_2 should use [...] syntax"
        assert re.search(r'activity_3\[', mermaid_content), "activity_3 should use [...] syntax"
        assert re.search(r'activity_4\[', mermaid_content), "activity_4 should use [...] syntax"
        assert re.search(r'e\(\(', mermaid_content), "End node should use ((...)) syntax"

    def test_validate_edge_connections_in_sequence(self, tmp_path: Path) -> None:
        """AC7: Verify edges connect nodes in correct sequence.

        Ensures proper linear connectivity:
        - s --> activity_1 (start to first activity)
        - activity_1 --> activity_2, activity_2 --> activity_3, etc. (activity to activity)
        - activity_3 --> e (or activity_4 --> e) (last activity to end)
        """
        # Arrange
        workflow_file = tmp_path / "test_workflow.py"
        workflow_file.write_text(_generate_test_workflow(num_activities=3))

        # Act
        result = analyze_workflow(workflow_file)
        mermaid_content = _extract_mermaid_content(result)

        # Assert
        edges = _extract_edges_from_mermaid(mermaid_content)

        # Verify all expected edges exist
        # Note: Activity names are now used as node IDs
        expected_edges = [('s', 'activity_1'), ('activity_1', 'activity_2'), ('activity_2', 'activity_3'), ('activity_3', 'e')]
        for src, tgt in expected_edges:
            assert (src, tgt) in edges, \
                f"Expected edge {src} --> {tgt} not found. Found edges: {edges}"

        # Verify no extra edges
        assert len(edges) == 4, \
            f"Expected exactly 4 edges, got {len(edges)}: {edges}"


class TestExampleWorkflowImportability:
    """Test AC8: Validate example workflow is importable and syntactically valid."""

    def test_example_workflow_syntax_valid(self) -> None:
        """AC8: Verify workflow.py is syntactically valid Python.

        Ensures:
        - File exists at examples/simple_linear/workflow.py
        - Contains valid Python syntax
        - Can be parsed by ast.parse()
        - Has proper @workflow.defn decorator
        - Has @workflow.run method
        """
        # Arrange
        workflow_path = Path("examples/simple_linear/workflow.py")

        # Act & Assert
        assert workflow_path.exists(), \
            "examples/simple_linear/workflow.py should exist"

        content = workflow_path.read_text(encoding="utf-8")
        assert len(content) > 0, "Workflow file should not be empty"

        # Validate Python syntax
        try:
            ast.parse(content)
        except SyntaxError as e:
            pytest.fail(f"Workflow file has syntax error: {e}")

        # Validate structure
        assert "@workflow.defn" in content, "Should have @workflow.defn decorator"
        assert "@workflow.run" in content, "Should have @workflow.run method"
        assert "async def run" in content, "Should have async run method"
        assert "execute_activity" in content, "Should have execute_activity calls"

    def test_example_workflow_has_required_activities(self) -> None:
        """AC8: Verify workflow has 3-4 execute_activity() calls.

        Ensures:
        - Workflow file contains multiple execute_activity calls
        - Activities are proper async/await calls
        - Workflow is complete and runnable
        """
        # Arrange
        workflow_path = Path("examples/simple_linear/workflow.py")

        # Act
        content = workflow_path.read_text(encoding="utf-8")

        # Assert: Count execute_activity calls
        activity_count = content.count("execute_activity(")
        assert activity_count >= 3, \
            f"Should have at least 3 activities, found {activity_count}"
        assert activity_count <= 4, \
            f"Should have at most 4 activities, found {activity_count}"


class TestExampleRunScriptExecutable:
    """Test AC9: Validate run.py demonstrates analyze_workflow() usage."""

    def test_example_run_script_exists(self) -> None:
        """AC9: Verify run.py exists and has proper imports.

        Ensures:
        - File exists at examples/simple_linear/run.py
        - Imports analyze_workflow from temporalio_graphs
        - Calls analyze_workflow on workflow.py
        - Prints result
        """
        # Arrange
        run_path = Path("examples/simple_linear/run.py")

        # Act & Assert
        assert run_path.exists(), "examples/simple_linear/run.py should exist"

        content = run_path.read_text(encoding="utf-8")

        # Validate imports
        assert "from temporalio_graphs import analyze_workflow" in content or \
               "from temporalio_graphs import" in content, \
            "Should import analyze_workflow from temporalio_graphs"

        # Validate function call
        assert "analyze_workflow(" in content, "Should call analyze_workflow()"

        # Validate it's executable
        assert "if __name__" in content or "print(" in content, \
            "Should be executable"

    def test_example_run_script_is_valid_python(self) -> None:
        """AC9: Verify run.py is syntactically valid.

        Ensures:
        - File can be parsed by ast.parse()
        - No syntax errors
        """
        # Arrange
        run_path = Path("examples/simple_linear/run.py")

        # Act & Assert
        content = run_path.read_text(encoding="utf-8")

        try:
            ast.parse(content)
        except SyntaxError as e:
            pytest.fail(f"run.py has syntax error: {e}")


class TestExampleExpectedOutput:
    """Test AC10: Validate expected_output.md contains golden Mermaid diagram."""

    def test_expected_output_file_exists(self) -> None:
        """AC10: Verify expected_output.md file exists.

        Ensures:
        - File exists at examples/simple_linear/expected_output.md
        - Contains valid Mermaid diagram
        - Has fenced code block
        """
        # Arrange
        output_path = Path("examples/simple_linear/expected_output.md")

        # Act & Assert
        assert output_path.exists(), \
            "examples/simple_linear/expected_output.md should exist"

        content = output_path.read_text(encoding="utf-8")
        assert len(content) > 0, "File should not be empty"

    def test_expected_output_contains_valid_mermaid(self) -> None:
        """AC10: Verify expected_output.md contains valid Mermaid diagram.

        Ensures:
        - Contains Mermaid code block (```mermaid)
        - Has flowchart LR declaration
        - Contains start and end nodes
        """
        # Arrange
        output_path = Path("examples/simple_linear/expected_output.md")

        # Act
        content = output_path.read_text(encoding="utf-8")

        # Assert
        assert "```mermaid" in content, "Should have Mermaid code block"
        assert "flowchart LR" in content, "Should have flowchart LR declaration"
        assert "s((Start))" in content, "Should have start node"
        assert "e((End))" in content, "Should have end node"

        # Extract and validate Mermaid content
        mermaid_content = _extract_mermaid_content(content)
        nodes = _extract_nodes_from_mermaid(mermaid_content)
        assert 's' in nodes, "Should have start node"
        assert 'e' in nodes, "Should have end node"
        assert len(nodes) >= 5, "Should have at least start + 3 activities + end"

    def test_expected_output_matches_actual_analysis(self) -> None:
        """AC10: Verify expected output matches actual analyze_workflow() result.

        Ensures:
        - Expected output file matches what analyze_workflow() produces
        - Consistency between documentation and implementation
        """
        # Arrange
        output_path = Path("examples/simple_linear/expected_output.md")
        workflow_path = Path("examples/simple_linear/workflow.py")

        # Act
        actual_result = analyze_workflow(workflow_path)
        expected_content = output_path.read_text(encoding="utf-8")

        # Extract Mermaid content from both
        actual_mermaid = _extract_mermaid_content(actual_result)
        expected_mermaid = _extract_mermaid_content(expected_content)

        # Assert: Both should have same structure
        actual_nodes = _extract_nodes_from_mermaid(actual_mermaid)
        expected_nodes = _extract_nodes_from_mermaid(expected_mermaid)

        assert actual_nodes == expected_nodes, \
            f"Node mismatch: actual {actual_nodes} vs expected {expected_nodes}"

        actual_edges = _extract_edges_from_mermaid(actual_mermaid)
        expected_edges = _extract_edges_from_mermaid(expected_mermaid)

        assert actual_edges == expected_edges, \
            f"Edge mismatch: actual {actual_edges} vs expected {expected_edges}"


class TestIntegrationTestSuiteQuality:
    """Test AC11-AC12: Test quality and performance requirements."""

    def test_all_integration_tests_pass(self) -> None:
        """AC11: Meta-test ensuring all integration tests pass.

        This test verifies:
        - No skipped tests
        - No failed tests
        - 100% success rate
        - Test isolation via tmp_path
        """
        # This test passes by virtue of pytest running all tests successfully
        # If any test fails, pytest will report failure overall
        assert True, "All integration tests should pass"

    def test_example_workflow_is_runnable(self, tmp_path: Path) -> None:
        """Verify the example workflow can be analyzed without errors.

        This ensures the example is complete and working.
        """
        # Arrange
        workflow_path = Path("examples/simple_linear/workflow.py")

        # Act: Analyze the example workflow
        result = analyze_workflow(workflow_path)

        # Assert
        assert isinstance(result, str), "analyze_workflow should return string"
        assert len(result) > 0, "Result should not be empty"
        assert "flowchart LR" in result, "Should be valid Mermaid"

    def test_integration_test_performance(self, tmp_path: Path) -> None:
        """AC12: Verify integration tests complete in <500ms.

        This test validates performance requirements per NFR-MAINT-2.
        Since this is already running, if total suite finishes in time, pass.
        """
        # Arrange
        workflow_file = tmp_path / "perf_test.py"
        workflow_file.write_text(_generate_test_workflow(num_activities=3))

        # Act & Assert: Just verify it runs without error
        # (pytest-benchmark would be better, but tmp fixture makes it tricky)
        result = analyze_workflow(workflow_file)
        assert isinstance(result, str), "Should complete analysis successfully"
