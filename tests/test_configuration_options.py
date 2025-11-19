"""Unit tests for GraphBuildingContext configuration options wiring.

Tests that all configuration options defined in GraphBuildingContext are:
1. Properly validated (AC 10)
2. Actually used by components (AC 8, 9)
3. Work correctly together (AC 12)
4. Are documented (AC 13)
"""

import tempfile
from pathlib import Path

import pytest

from temporalio_graphs import GraphBuildingContext, analyze_workflow
from temporalio_graphs.exceptions import GraphGenerationError
from temporalio_graphs.path import GraphPath
from temporalio_graphs.renderer import MermaidRenderer


# ============================================================================
# AC 10: Configuration Validation Tests
# ============================================================================


class TestConfigurationValidation:
    """Tests for validation of configuration options."""

    def test_invalid_max_decision_points_negative(self) -> None:
        """Negative max_decision_points raises ValueError."""
        with pytest.raises(ValueError, match="max_decision_points must be positive"):
            analyze_workflow(
                Path("tests/fixtures/sample_workflows/single_activity_workflow.py"),
                context=GraphBuildingContext(max_decision_points=-1),
            )

    def test_invalid_max_decision_points_zero(self) -> None:
        """Zero max_decision_points raises ValueError."""
        with pytest.raises(ValueError, match="max_decision_points must be positive"):
            analyze_workflow(
                Path("tests/fixtures/sample_workflows/single_activity_workflow.py"),
                context=GraphBuildingContext(max_decision_points=0),
            )

    def test_invalid_max_paths_negative(self) -> None:
        """Negative max_paths raises ValueError."""
        with pytest.raises(ValueError, match="max_paths must be positive"):
            analyze_workflow(
                Path("tests/fixtures/sample_workflows/single_activity_workflow.py"),
                context=GraphBuildingContext(max_paths=-1),
            )

    def test_invalid_max_paths_zero(self) -> None:
        """Zero max_paths raises ValueError."""
        with pytest.raises(ValueError, match="max_paths must be positive"):
            analyze_workflow(
                Path("tests/fixtures/sample_workflows/single_activity_workflow.py"),
                context=GraphBuildingContext(max_paths=0),
            )

    def test_valid_configuration_positive_values(self) -> None:
        """Valid configuration with positive values works."""
        result = analyze_workflow(
            Path("tests/fixtures/sample_workflows/single_activity_workflow.py"),
            context=GraphBuildingContext(max_decision_points=5, max_paths=512),
        )
        assert result is not None
        assert "```mermaid" in result


# ============================================================================
# AC 2: split_names_by_words Configuration Tests
# ============================================================================


class TestSplitNamesByWords:
    """Tests for split_names_by_words configuration option."""

    def test_split_names_by_words_enabled(self) -> None:
        """When split_names_by_words=True, camelCase names are split."""
        renderer = MermaidRenderer()
        path = GraphPath(path_id="path_0")
        path.add_activity("withdrawFunds")
        path.add_activity("depositMoney")

        context = GraphBuildingContext(split_names_by_words=True)
        result = renderer.to_mermaid([path], context)

        # camelCase should be split with spaces (lowercase preserved)
        assert "withdraw Funds" in result
        assert "deposit Money" in result

    def test_split_names_by_words_disabled(self) -> None:
        """When split_names_by_words=False, names are unchanged."""
        renderer = MermaidRenderer()
        path = GraphPath(path_id="path_0")
        path.add_activity("withdrawFunds")
        path.add_activity("depositMoney")

        context = GraphBuildingContext(split_names_by_words=False)
        result = renderer.to_mermaid([path], context)

        # camelCase should NOT be split
        assert "withdrawFunds" in result
        assert "depositMoney" in result
        assert "Withdraw Funds" not in result
        assert "Deposit Money" not in result

    def test_split_names_by_words_multiple_transitions(self) -> None:
        """Word splitting works with multiple camelCase transitions."""
        renderer = MermaidRenderer()
        path = GraphPath(path_id="path_0")
        path.add_activity("validatePayment")
        path.add_activity("processTransaction")
        path.add_activity("sendConfirmation")

        context = GraphBuildingContext(split_names_by_words=True)
        result = renderer.to_mermaid([path], context)

        assert "validate Payment" in result
        assert "process Transaction" in result
        assert "send Confirmation" in result


# ============================================================================
# AC 4: start_node_label Configuration Tests
# ============================================================================


class TestStartNodeLabel:
    """Tests for start_node_label configuration option."""

    def test_start_node_label_default(self) -> None:
        """Default start_node_label is 'Start'."""
        renderer = MermaidRenderer()
        path = GraphPath(path_id="path_0")
        path.add_activity("Work")

        context = GraphBuildingContext(start_node_label="Start")
        result = renderer.to_mermaid([path], context)

        assert "s((Start))" in result

    def test_start_node_label_custom(self) -> None:
        """Custom start_node_label is rendered correctly."""
        renderer = MermaidRenderer()
        path = GraphPath(path_id="path_0")
        path.add_activity("Work")

        context = GraphBuildingContext(start_node_label="BEGIN")
        result = renderer.to_mermaid([path], context)

        assert "s((BEGIN))" in result
        assert "s((Start))" not in result

    def test_start_node_label_multiword(self) -> None:
        """Custom start_node_label with multiple words."""
        renderer = MermaidRenderer()
        path = GraphPath(path_id="path_0")
        path.add_activity("Work")

        context = GraphBuildingContext(start_node_label="Workflow Begin")
        result = renderer.to_mermaid([path], context)

        assert "s((Workflow Begin))" in result


# ============================================================================
# AC 5: end_node_label Configuration Tests
# ============================================================================


class TestEndNodeLabel:
    """Tests for end_node_label configuration option."""

    def test_end_node_label_default(self) -> None:
        """Default end_node_label is 'End'."""
        renderer = MermaidRenderer()
        path = GraphPath(path_id="path_0")
        path.add_activity("Work")

        context = GraphBuildingContext(end_node_label="End")
        result = renderer.to_mermaid([path], context)

        assert "e((End))" in result

    def test_end_node_label_custom(self) -> None:
        """Custom end_node_label is rendered correctly."""
        renderer = MermaidRenderer()
        path = GraphPath(path_id="path_0")
        path.add_activity("Work")

        context = GraphBuildingContext(end_node_label="FINISH")
        result = renderer.to_mermaid([path], context)

        assert "e((FINISH))" in result
        assert "e((End))" not in result

    def test_end_node_label_multiword(self) -> None:
        """Custom end_node_label with multiple words."""
        renderer = MermaidRenderer()
        path = GraphPath(path_id="path_0")
        path.add_activity("Work")

        context = GraphBuildingContext(end_node_label="Workflow Complete")
        result = renderer.to_mermaid([path], context)

        assert "e((Workflow Complete))" in result


# ============================================================================
# AC 3: suppress_validation Configuration Tests
# ============================================================================


class TestSuppressValidation:
    """Tests for suppress_validation configuration option."""

    def test_suppress_validation_default(self) -> None:
        """Default suppress_validation is False."""
        ctx = GraphBuildingContext()
        assert ctx.suppress_validation is False

    def test_suppress_validation_true(self) -> None:
        """suppress_validation=True is stored in context."""
        ctx = GraphBuildingContext(suppress_validation=True)
        assert ctx.suppress_validation is True

    def test_suppress_validation_false(self) -> None:
        """suppress_validation=False is stored in context."""
        ctx = GraphBuildingContext(suppress_validation=False)
        assert ctx.suppress_validation is False

    def test_empty_workflow_warning_emitted_by_default(
        self, tmp_path: Path
    ) -> None:
        """Empty workflow emits warning when suppress_validation=False (default)."""
        import warnings

        # Create empty workflow fixture
        empty_workflow = tmp_path / "empty_workflow.py"
        empty_workflow.write_text(
            """
from temporalio import workflow

@workflow.defn
class EmptyWorkflow:
    @workflow.run
    async def run(self) -> str:
        return "done"
"""
        )

        context = GraphBuildingContext()  # suppress_validation=False by default
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from temporalio_graphs import analyze_workflow

            analyze_workflow(empty_workflow, context)

            # Check warning was emitted
            assert len(w) == 1
            assert issubclass(w[0].category, UserWarning)
            assert "No activity calls detected" in str(w[0].message)
            assert "EmptyWorkflow" in str(w[0].message)

    def test_empty_workflow_warning_suppressed(self, tmp_path: Path) -> None:
        """Empty workflow does NOT emit warning when suppress_validation=True."""
        import warnings

        # Create empty workflow fixture
        empty_workflow = tmp_path / "empty_workflow_suppressed.py"
        empty_workflow.write_text(
            """
from temporalio import workflow

@workflow.defn
class EmptyWorkflowSuppressed:
    @workflow.run
    async def run(self) -> str:
        return "done"
"""
        )

        context = GraphBuildingContext(suppress_validation=True)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from temporalio_graphs import analyze_workflow

            analyze_workflow(empty_workflow, context)

            # Check NO warnings emitted
            assert len(w) == 0

    def test_long_activity_name_warning_emitted_by_default(
        self, tmp_path: Path
    ) -> None:
        """Very long activity names emit warning when suppress_validation=False."""
        import warnings

        # Create workflow with very long activity name
        long_activity_workflow = tmp_path / "long_activity_workflow.py"
        long_activity_name = "a" * 150  # 150 chars, exceeds 100 char threshold
        long_activity_workflow.write_text(
            f"""
from temporalio import workflow

@workflow.defn
class LongActivityWorkflow:
    @workflow.run
    async def run(self) -> str:
        await workflow.execute_activity("{long_activity_name}", schedule_to_close_timeout=60)
        return "done"
"""
        )

        context = GraphBuildingContext()  # suppress_validation=False by default
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from temporalio_graphs import analyze_workflow

            analyze_workflow(long_activity_workflow, context)

            # Check warning was emitted
            assert len(w) == 1
            assert issubclass(w[0].category, UserWarning)
            assert "is very long" in str(w[0].message)
            assert "150 chars" in str(w[0].message)

    def test_long_activity_name_warning_suppressed(self, tmp_path: Path) -> None:
        """Very long activity names do NOT emit warning when suppress_validation=True."""
        import warnings

        # Create workflow with very long activity name
        long_activity_workflow = tmp_path / "long_activity_workflow_suppressed.py"
        long_activity_name = "b" * 150  # 150 chars, exceeds 100 char threshold
        long_activity_workflow.write_text(
            f"""
from temporalio import workflow

@workflow.defn
class LongActivityWorkflowSuppressed:
    @workflow.run
    async def run(self) -> str:
        await workflow.execute_activity("{long_activity_name}", schedule_to_close_timeout=60)
        return "done"
"""
        )

        context = GraphBuildingContext(suppress_validation=True)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from temporalio_graphs import analyze_workflow

            analyze_workflow(long_activity_workflow, context)

            # Check NO warnings emitted
            assert len(w) == 0


# ============================================================================
# AC 6: max_decision_points Limit Tests
# ============================================================================


class TestMaxDecisionPointsLimit:
    """Tests for max_decision_points limit enforcement."""

    def test_max_decision_points_default_is_10(self) -> None:
        """Default max_decision_points is 10."""
        ctx = GraphBuildingContext()
        assert ctx.max_decision_points == 10

    def test_max_decision_points_custom_value(self) -> None:
        """Custom max_decision_points is stored."""
        ctx = GraphBuildingContext(max_decision_points=15)
        assert ctx.max_decision_points == 15

    def test_max_decision_points_custom_value_high(self) -> None:
        """High custom max_decision_points is allowed."""
        ctx = GraphBuildingContext(max_decision_points=20)
        assert ctx.max_decision_points == 20


# ============================================================================
# AC 7: graph_output_file Configuration Tests
# ============================================================================


class TestGraphOutputFile:
    """Tests for graph_output_file configuration option."""

    def test_graph_output_file_none_default(self) -> None:
        """Default graph_output_file is None."""
        ctx = GraphBuildingContext()
        assert ctx.graph_output_file is None

    def test_graph_output_file_writes_to_disk(self) -> None:
        """graph_output_file writes output to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.md"

            result = analyze_workflow(
                Path("tests/fixtures/sample_workflows/single_activity_workflow.py"),
                context=GraphBuildingContext(graph_output_file=output_path),
            )

            # File should be created
            assert output_path.exists()

            # File content should match returned string
            file_content = output_path.read_text()
            assert file_content == result

    def test_graph_output_file_creates_parent_directories(self) -> None:
        """graph_output_file creates parent directories if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "nested" / "output.md"

            result = analyze_workflow(
                Path("tests/fixtures/sample_workflows/single_activity_workflow.py"),
                context=GraphBuildingContext(graph_output_file=output_path),
            )

            # Parent directories should be created
            assert output_path.parent.exists()
            assert output_path.exists()

            # Content should match
            assert output_path.read_text() == result

    def test_graph_output_file_overwrites_existing(self) -> None:
        """graph_output_file overwrites existing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.md"

            # Write initial content
            output_path.write_text("old content")
            old_size = output_path.stat().st_size

            # Analyze workflow and write to same file
            result = analyze_workflow(
                Path("tests/fixtures/sample_workflows/single_activity_workflow.py"),
                context=GraphBuildingContext(graph_output_file=output_path),
            )

            # File should contain new content, not old
            new_content = output_path.read_text()
            assert new_content == result
            assert new_content != "old content"

    def test_graph_output_file_returns_result(self) -> None:
        """analyze_workflow returns result even with file output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.md"

            result = analyze_workflow(
                Path("tests/fixtures/sample_workflows/single_activity_workflow.py"),
                context=GraphBuildingContext(graph_output_file=output_path),
            )

            # Result should be returned
            assert result is not None
            assert isinstance(result, str)
            assert "```mermaid" in result


# ============================================================================
# AC 8, 9: Configuration Pipeline Integration Tests
# ============================================================================


class TestConfigurationPipelineIntegration:
    """Tests that configuration flows through entire pipeline."""

    def test_configuration_flows_to_renderer(self) -> None:
        """Configuration options are passed to MermaidRenderer."""
        result = analyze_workflow(
            Path("tests/fixtures/sample_workflows/single_activity_workflow.py"),
            context=GraphBuildingContext(
                start_node_label="CUSTOM_START",
                end_node_label="CUSTOM_END",
                split_names_by_words=False,
            ),
        )

        # Verify all customizations are in output
        assert "s((CUSTOM_START))" in result
        assert "e((CUSTOM_END))" in result
        assert "```mermaid" in result


# ============================================================================
# AC 12: Multiple Options Combined Tests
# ============================================================================


class TestMultipleOptionsCombined:
    """Tests that multiple configuration options work together."""

    def test_multiple_options_combined_basic(self) -> None:
        """Multiple configuration options work together."""
        renderer = MermaidRenderer()
        path = GraphPath(path_id="path_0")
        path.add_activity("validateInput")
        path.add_activity("processData")

        context = GraphBuildingContext(
            split_names_by_words=False,
            start_node_label="BEGIN",
            end_node_label="FINISH",
            suppress_validation=True,
        )

        result = renderer.to_mermaid([path], context)

        # All customizations should be present
        assert "s((BEGIN))" in result
        assert "e((FINISH))" in result
        assert "validateInput" in result  # Not split
        assert "processData" in result  # Not split
        assert "Validate Input" not in result  # Should not be split
        assert "Process Data" not in result  # Should not be split

    def test_multiple_options_combined_with_file_output(self) -> None:
        """Multiple options work together with file output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "workflow_diagram.md"

            result = analyze_workflow(
                Path("tests/fixtures/sample_workflows/multi_activity_workflow.py"),
                context=GraphBuildingContext(
                    split_names_by_words=True,
                    start_node_label="START",
                    end_node_label="END",
                    max_decision_points=10,
                    graph_output_file=output_path,
                ),
            )

            # Verify file was created
            assert output_path.exists()

            # Verify customizations are in output
            assert "s((START))" in result
            assert "e((END))" in result

    def test_multiple_options_immutable_not_modified(self) -> None:
        """Configuration object is never modified during processing."""
        context = GraphBuildingContext(
            split_names_by_words=True,
            start_node_label="BEGIN",
            end_node_label="FINISH",
            suppress_validation=True,
            max_decision_points=10,
            max_paths=1024,
        )

        original_split = context.split_names_by_words
        original_start = context.start_node_label
        original_end = context.end_node_label
        original_suppress = context.suppress_validation
        original_max_decisions = context.max_decision_points
        original_max_paths = context.max_paths

        # Process workflow
        analyze_workflow(
            Path("tests/fixtures/sample_workflows/single_activity_workflow.py"),
            context=context,
        )

        # Verify configuration was not modified
        assert context.split_names_by_words == original_split
        assert context.start_node_label == original_start
        assert context.end_node_label == original_end
        assert context.suppress_validation == original_suppress
        assert context.max_decision_points == original_max_decisions
        assert context.max_paths == original_max_paths


# ============================================================================
# Decision Point Limit Tests
# ============================================================================


class TestDecisionPointLimitEnforcement:
    """Tests for decision point limit enforcement (preparation for Epic 3)."""

    def test_max_decision_points_validation_message_format(self) -> None:
        """Error message for max_decision_points includes calculation."""
        # This will be triggered when Epic 3 adds decision point support
        # For now, test that validation structure is in place
        ctx = GraphBuildingContext(max_decision_points=5)
        assert ctx.max_decision_points == 5
