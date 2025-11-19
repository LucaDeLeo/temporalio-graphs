"""Unit tests for path list formatting module.

Tests cover FormattedPath, PathListOutput, and format_path_list function
with various workflow patterns including linear, branching, and edge cases.
"""

from temporalio_graphs.formatter import FormattedPath, PathListOutput, format_path_list
from temporalio_graphs.path import GraphPath, PathStep


class TestFormattedPath:
    """Tests for FormattedPath dataclass and format() method."""

    def test_formatted_path_single_activity(self):
        """Test path with single activity."""
        path = FormattedPath(
            path_number=1,
            activities=["Withdraw"],
            decisions={}
        )
        result = path.format()
        assert result == "Path 1: Start → Withdraw → End"

    def test_formatted_path_multiple_activities(self):
        """Test path with multiple activities."""
        path = FormattedPath(
            path_number=2,
            activities=["Withdraw", "CurrencyConvert", "Deposit"],
            decisions={"NeedToConvert": True}
        )
        result = path.format()
        assert result == "Path 2: Start → Withdraw → CurrencyConvert → Deposit → End"

    def test_formatted_path_no_activities(self):
        """Test path with no activities (edge case)."""
        path = FormattedPath(
            path_number=1,
            activities=[],
            decisions={}
        )
        result = path.format()
        assert result == "Path 1: Start → End"

    def test_formatted_path_many_activities(self):
        """Test path with many activities."""
        activities = [f"Activity{i}" for i in range(1, 6)]
        path = FormattedPath(
            path_number=3,
            activities=activities,
            decisions={}
        )
        result = path.format()
        expected = "Path 3: Start → Activity1 → Activity2 → Activity3 → Activity4 → Activity5 → End"
        assert result == expected


class TestPathListOutput:
    """Tests for PathListOutput dataclass and format() method."""

    def test_path_list_output_format_linear(self):
        """Test output format for linear workflow (no decisions)."""
        paths = [
            FormattedPath(1, ["Withdraw", "Deposit"], {})
        ]
        output = PathListOutput(paths, total_paths=1, total_decisions=0)
        result = output.format()

        # Verify header shows "1 total"
        assert "--- Execution Paths (1 total) ---" in result
        # No decision info line for linear workflow
        assert "Decision Points:" not in result
        # Path appears
        assert "Path 1: Start → Withdraw → Deposit → End" in result

    def test_path_list_output_format_decisions(self):
        """Test output format with 2 decisions (4 paths)."""
        paths = [
            FormattedPath(1, ["Withdraw", "CurrencyConvert", "NotifyAto", "Deposit"], {}),
            FormattedPath(2, ["Withdraw", "CurrencyConvert", "TakeNonResidentTax", "Deposit"], {}),
            FormattedPath(3, ["Withdraw", "NotifyAto", "Deposit"], {}),
            FormattedPath(4, ["Withdraw", "TakeNonResidentTax", "Deposit"], {}),
        ]
        output = PathListOutput(paths, total_paths=4, total_decisions=2)
        result = output.format()

        # Verify header
        assert "--- Execution Paths (4 total) ---" in result
        # Decision info line present
        assert "Decision Points: 2 (2^2 = 4 paths)" in result
        # All 4 paths present
        assert "Path 1:" in result
        assert "Path 2:" in result
        assert "Path 3:" in result
        assert "Path 4:" in result

    def test_path_list_output_format_structure(self):
        """Test output structure with empty line after header."""
        paths = [
            FormattedPath(1, ["Activity1"], {})
        ]
        output = PathListOutput(paths, total_paths=1, total_decisions=0)
        result = output.format()

        lines = result.split("\n")
        # First line is newline + header
        assert lines[0] == ""
        assert "--- Execution Paths (1 total) ---" in lines[1]
        # Empty line after header
        assert lines[2] == ""
        # Path on next line
        assert "Path 1:" in lines[3]

    def test_path_list_output_three_decisions(self):
        """Test output with 3 decisions (8 paths)."""
        paths = [FormattedPath(i, ["Activity"], {}) for i in range(1, 9)]
        output = PathListOutput(paths, total_paths=8, total_decisions=3)
        result = output.format()

        assert "--- Execution Paths (8 total) ---" in result
        assert "Decision Points: 3 (2^3 = 8 paths)" in result
        # Verify all 8 paths numbered correctly
        for i in range(1, 9):
            assert f"Path {i}:" in result


class TestFormatPathList:
    """Tests for format_path_list() function."""

    def test_format_path_list_linear_workflow(self):
        """Test formatting linear workflow (no decisions)."""
        # Create path with activity steps only
        path = GraphPath(
            path_id="0",
            steps=[
                PathStep('activity', 'Withdraw'),
                PathStep('activity', 'Deposit')
            ],
            decisions={}
        )

        result = format_path_list([path])

        assert isinstance(result, PathListOutput)
        assert result.total_paths == 1
        assert result.total_decisions == 0
        assert len(result.paths) == 1
        assert result.paths[0].path_number == 1
        assert result.paths[0].activities == ["Withdraw", "Deposit"]

    def test_format_path_list_branching_workflow(self):
        """Test formatting workflow with decisions (4 paths)."""
        # Create 4 paths with different decision outcomes
        paths = [
            GraphPath(
                path_id="0b00",
                steps=[
                    PathStep('activity', 'Withdraw'),
                    PathStep('decision', 'NeedToConvert', decision_id='0', decision_value=True),
                    PathStep('activity', 'CurrencyConvert'),
                    PathStep('decision', 'IsTFN_Known', decision_id='1', decision_value=True),
                    PathStep('activity', 'NotifyAto'),
                    PathStep('activity', 'Deposit')
                ],
                decisions={'0': True, '1': True}
            ),
            GraphPath(
                path_id="0b01",
                steps=[
                    PathStep('activity', 'Withdraw'),
                    PathStep('decision', 'NeedToConvert', decision_id='0', decision_value=True),
                    PathStep('activity', 'CurrencyConvert'),
                    PathStep('decision', 'IsTFN_Known', decision_id='1', decision_value=False),
                    PathStep('activity', 'TakeNonResidentTax'),
                    PathStep('activity', 'Deposit')
                ],
                decisions={'0': True, '1': False}
            ),
            GraphPath(
                path_id="0b10",
                steps=[
                    PathStep('activity', 'Withdraw'),
                    PathStep('decision', 'NeedToConvert', decision_id='0', decision_value=False),
                    PathStep('decision', 'IsTFN_Known', decision_id='1', decision_value=True),
                    PathStep('activity', 'NotifyAto'),
                    PathStep('activity', 'Deposit')
                ],
                decisions={'0': False, '1': True}
            ),
            GraphPath(
                path_id="0b11",
                steps=[
                    PathStep('activity', 'Withdraw'),
                    PathStep('decision', 'NeedToConvert', decision_id='0', decision_value=False),
                    PathStep('decision', 'IsTFN_Known', decision_id='1', decision_value=False),
                    PathStep('activity', 'TakeNonResidentTax'),
                    PathStep('activity', 'Deposit')
                ],
                decisions={'0': False, '1': False}
            ),
        ]

        result = format_path_list(paths)

        assert result.total_paths == 4
        assert result.total_decisions == 2
        assert len(result.paths) == 4

        # Verify path numbering
        assert result.paths[0].path_number == 1
        assert result.paths[1].path_number == 2
        assert result.paths[2].path_number == 3
        assert result.paths[3].path_number == 4

        # Verify activities extracted correctly (no decision names in activities)
        assert "Withdraw" in result.paths[0].activities
        assert "Deposit" in result.paths[0].activities
        assert "CurrencyConvert" in result.paths[0].activities
        # Decision names should NOT be in activities
        assert "NeedToConvert" not in result.paths[0].activities
        assert "IsTFN_Known" not in result.paths[0].activities

    def test_format_path_list_empty(self):
        """Test format_path_list with empty paths list (edge case)."""
        result = format_path_list([])

        assert result.total_paths == 0
        assert result.total_decisions == 0
        assert len(result.paths) == 0

    def test_format_path_list_activity_extraction(self):
        """Test that only activities are extracted (not decisions or signals)."""
        path = GraphPath(
            path_id="0",
            steps=[
                PathStep('activity', 'Activity1'),
                PathStep('decision', 'Decision1', decision_id='0', decision_value=True),
                PathStep('activity', 'Activity2'),
                PathStep('signal', 'WaitForApproval', signal_outcome='Signaled'),
                PathStep('activity', 'Activity3')
            ],
            decisions={'0': True}
        )

        result = format_path_list([path])

        # Only activities should be extracted
        assert result.paths[0].activities == ["Activity1", "Activity2", "Activity3"]
        # Verify signal and decision names NOT in activities
        assert "Decision1" not in result.paths[0].activities
        assert "WaitForApproval" not in result.paths[0].activities

    def test_format_path_list_child_workflow_extraction(self):
        """Test that child workflows are extracted along with activities."""
        path = GraphPath(
            path_id="0",
            steps=[
                PathStep('activity', 'validate_order'),
                PathStep('child_workflow', 'PaymentWorkflow', line_number=15),
                PathStep('activity', 'send_confirmation')
            ],
            decisions={}
        )

        result = format_path_list([path])

        # Both activities and child workflows should be extracted
        assert result.paths[0].activities == ["validate_order", "PaymentWorkflow", "send_confirmation"]

    def test_format_path_list_multiple_child_workflows(self):
        """Test path list with multiple child workflows."""
        path = GraphPath(
            path_id="0",
            steps=[
                PathStep('activity', 'start_order'),
                PathStep('child_workflow', 'InventoryWorkflow', line_number=10),
                PathStep('activity', 'process_order'),
                PathStep('child_workflow', 'PaymentWorkflow', line_number=15),
                PathStep('activity', 'complete_order')
            ],
            decisions={}
        )

        result = format_path_list([path])

        # All activities and child workflows should be in order
        assert result.paths[0].activities == [
            "start_order",
            "InventoryWorkflow",
            "process_order",
            "PaymentWorkflow",
            "complete_order"
        ]

    def test_format_path_list_child_workflow_integration(self):
        """Test end-to-end integration with child workflows in output."""
        paths = [
            GraphPath(
                path_id="0",
                steps=[
                    PathStep('activity', 'validate_order'),
                    PathStep('child_workflow', 'PaymentWorkflow', line_number=15),
                    PathStep('activity', 'send_confirmation')
                ],
                decisions={}
            )
        ]

        path_list = format_path_list(paths)
        output = path_list.format()

        # Verify child workflow appears in path output
        assert "validate_order → PaymentWorkflow → send_confirmation" in output

    def test_format_path_list_decision_extraction(self):
        """Test that decisions are extracted correctly."""
        path = GraphPath(
            path_id="0b01",
            steps=[
                PathStep('activity', 'Activity1'),
                PathStep('decision', 'HighValue', decision_id='0', decision_value=True),
                PathStep('activity', 'Activity2'),
                PathStep('decision', 'NeedsApproval', decision_id='1', decision_value=False),
            ],
            decisions={'0': True, '1': False}
        )

        result = format_path_list([path])

        # Decisions should be extracted
        assert result.paths[0].decisions == {
            'HighValue': True,
            'NeedsApproval': False
        }

    def test_format_path_list_integration(self):
        """Test end-to-end integration: format_path_list -> format() -> string."""
        paths = [
            GraphPath(
                path_id="0",
                steps=[
                    PathStep('activity', 'Withdraw'),
                    PathStep('activity', 'Deposit')
                ],
                decisions={}
            )
        ]

        path_list = format_path_list(paths)
        output = path_list.format()

        # Verify complete output structure
        assert "--- Execution Paths (1 total) ---" in output
        assert "Path 1: Start → Withdraw → Deposit → End" in output
        # No decision info for linear workflow
        assert "Decision Points:" not in output


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_many_paths_formatting(self):
        """Test formatting with many paths (e.g., 100 paths)."""
        # Create 100 simple paths
        paths = [
            GraphPath(
                path_id=str(i),
                steps=[PathStep('activity', f'Activity{i}')],
                decisions={}
            )
            for i in range(100)
        ]

        result = format_path_list(paths)

        assert result.total_paths == 100
        assert len(result.paths) == 100
        # Verify last path numbered correctly
        assert result.paths[99].path_number == 100

    def test_path_with_many_activities(self):
        """Test path with many activities."""
        steps = [PathStep('activity', f'Activity{i}') for i in range(20)]
        path = GraphPath(path_id="0", steps=steps, decisions={})

        result = format_path_list([path])

        assert len(result.paths[0].activities) == 20
        # Verify all activities in correct order
        for i in range(20):
            assert result.paths[0].activities[i] == f"Activity{i}"

    def test_unicode_arrow_in_output(self):
        """Test that output uses Unicode arrow (→) character."""
        path = FormattedPath(1, ["Activity1", "Activity2"], {})
        result = path.format()

        # Verify Unicode arrow used
        assert "→" in result
        # Verify format
        assert "Start → Activity1 → Activity2 → End" in result
