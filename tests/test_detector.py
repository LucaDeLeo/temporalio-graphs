"""Unit tests for decision point detection in AST.

This test module verifies that the DecisionDetector correctly identifies to_decision()
calls in workflow code and extracts all decision metadata including names, line numbers,
and expressions.

Test coverage includes:
- Single and multiple decision detection
- Decision name extraction (positional and keyword arguments)
- Boolean expression extraction
- Line number tracking
- elif chain detection (multiple decisions)
- Ternary operator detection
- Non-matching function filtering
- Error handling for malformed calls
"""

import ast
from pathlib import Path

import pytest

from temporalio_graphs._internal.graph_models import (
    ChildWorkflowCall,
    DecisionPoint,
    ExternalSignalCall,
    SignalPoint,
)
from temporalio_graphs.detector import (
    ChildWorkflowDetector,
    DecisionDetector,
    ExternalSignalDetector,
    SignalDetector,
)
from temporalio_graphs.exceptions import InvalidSignalError, WorkflowParseError


class TestDecisionDetectorBasic:
    """Basic decision detection tests."""

    def test_single_decision_detection(self) -> None:
        """Test detection of a single to_decision() call."""
        source = """
if await to_decision(amount > 1000, "HighValue"):
    pass
"""
        tree = ast.parse(source)
        detector = DecisionDetector()
        detector.visit(tree)

        assert len(detector.decisions) == 1
        assert detector.decisions[0].name == "HighValue"

    def test_multiple_decisions_detection(self) -> None:
        """Test detection of multiple to_decision() calls."""
        source = """
if await to_decision(amount > 1000, "HighValue"):
    pass

if await to_decision(is_international, "InternationalOrder"):
    pass
"""
        tree = ast.parse(source)
        detector = DecisionDetector()
        detector.visit(tree)

        assert len(detector.decisions) == 2
        assert detector.decisions[0].name == "HighValue"
        assert detector.decisions[1].name == "InternationalOrder"

    def test_nested_decisions(self) -> None:
        """Test detection of decisions nested in if/else blocks."""
        source = """
if condition:
    if await to_decision(x > 10, "Nested"):
        pass
else:
    if await to_decision(y < 5, "NestedElse"):
        pass
"""
        tree = ast.parse(source)
        detector = DecisionDetector()
        detector.visit(tree)

        assert len(detector.decisions) == 2
        assert detector.decisions[0].name == "Nested"
        assert detector.decisions[1].name == "NestedElse"


class TestDecisionNameExtraction:
    """Tests for decision name extraction from arguments."""

    def test_positional_argument_name_extraction(self) -> None:
        """Test extraction of name from positional argument."""
        source = 'to_decision(condition, "MyDecision")'
        tree = ast.parse(source, mode="eval")
        detector = DecisionDetector()
        detector.visit(tree)

        assert len(detector.decisions) == 1
        assert detector.decisions[0].name == "MyDecision"

    def test_keyword_argument_name_extraction(self) -> None:
        """Test extraction of name from keyword argument."""
        source = 'to_decision(condition, name="KeywordDecision")'
        tree = ast.parse(source, mode="eval")
        detector = DecisionDetector()
        detector.visit(tree)

        assert len(detector.decisions) == 1
        assert detector.decisions[0].name == "KeywordDecision"

    def test_missing_name_argument_error(self) -> None:
        """Test error when name argument is missing."""
        source = "to_decision(amount > 1000)"
        tree = ast.parse(source, mode="eval")
        detector = DecisionDetector()

        with pytest.raises(WorkflowParseError) as exc_info:
            detector.visit(tree)

        assert "name argument" in str(exc_info.value).lower()
        assert "2 arguments" in str(exc_info.value)

    def test_non_string_name_error(self) -> None:
        """Test error when name is not a string."""
        source = "to_decision(amount > 1000, 123)"
        tree = ast.parse(source, mode="eval")
        detector = DecisionDetector()

        with pytest.raises(WorkflowParseError) as exc_info:
            detector.visit(tree)

        assert "string" in str(exc_info.value).lower()

    def test_no_arguments_error(self) -> None:
        """Test error when no arguments provided."""
        source = "to_decision()"
        tree = ast.parse(source, mode="eval")
        detector = DecisionDetector()

        with pytest.raises(WorkflowParseError) as exc_info:
            detector.visit(tree)

        error_msg = str(exc_info.value).lower()
        assert "argument" in error_msg


class TestExpressionExtraction:
    """Tests for boolean expression extraction."""

    def test_simple_expression_extraction(self) -> None:
        """Test extraction of simple boolean expression."""
        source = 'to_decision(amount > 1000, "Test")'
        tree = ast.parse(source, mode="eval")
        detector = DecisionDetector()
        detector.visit(tree)

        assert len(detector.decisions) == 1
        # Expression extracted and stored implicitly (validated during detection)

    def test_complex_expression_extraction(self) -> None:
        """Test extraction of complex boolean expression."""
        source = 'to_decision((a > 100) and (b < 50), "Complex")'
        tree = ast.parse(source, mode="eval")
        detector = DecisionDetector()
        detector.visit(tree)

        assert len(detector.decisions) == 1
        assert detector.decisions[0].name == "Complex"

    def test_ternary_expression_in_decision(self) -> None:
        """Test extraction of ternary operator in decision."""
        source = 'to_decision(x if condition else y, "Ternary")'
        tree = ast.parse(source, mode="eval")
        detector = DecisionDetector()
        detector.visit(tree)

        assert len(detector.decisions) == 1
        assert detector.decisions[0].name == "Ternary"


class TestLineNumberTracking:
    """Tests for source line number tracking."""

    def test_line_number_accuracy(self) -> None:
        """Test that line numbers match source locations."""
        source = """# Line 1
# Line 2
if await to_decision(condition, "Decision"):  # Line 3
    pass
"""
        tree = ast.parse(source)
        detector = DecisionDetector()
        detector.visit(tree)

        assert len(detector.decisions) == 1
        assert detector.decisions[0].line_number == 3

    def test_multiple_decisions_line_numbers(self) -> None:
        """Test line numbers for multiple decisions."""
        source = """if await to_decision(cond1, "D1"):  # Line 1
    pass

if await to_decision(cond2, "D2"):  # Line 4
    pass
"""
        lines = source.strip().split("\n")
        tree = ast.parse(source)
        detector = DecisionDetector()
        detector.visit(tree)

        assert len(detector.decisions) == 2
        assert detector.decisions[0].line_number == 1
        assert detector.decisions[1].line_number == 4


class TestElifChainDetection:
    """Tests for elif chain detection."""

    def test_two_elif_chain(self) -> None:
        """Test detection of two-branch elif chain."""
        source = """
if await to_decision(x < 100, "Low"):
    pass
elif await to_decision(x < 500, "Medium"):
    pass
else:
    pass
"""
        tree = ast.parse(source)
        detector = DecisionDetector()
        detector.visit(tree)

        assert len(detector.decisions) == 2
        assert detector.decisions[0].name == "Low"
        assert detector.decisions[1].name == "Medium"

    def test_three_elif_chain(self) -> None:
        """Test detection of three-branch elif chain."""
        source = """
if await to_decision(x < 100, "Low"):
    pass
elif await to_decision(x < 500, "Medium"):
    pass
elif await to_decision(x < 1000, "High"):
    pass
else:
    pass
"""
        tree = ast.parse(source)
        detector = DecisionDetector()
        detector.visit(tree)

        assert len(detector.decisions) == 3
        assert detector.decisions[0].name == "Low"
        assert detector.decisions[1].name == "Medium"
        assert detector.decisions[2].name == "High"

    def test_elif_chain_separate_entries(self) -> None:
        """Test that each elif creates separate DecisionPoint."""
        source = """
if await to_decision(cond1, "D1"):
    pass
elif await to_decision(cond2, "D2"):
    pass
"""
        tree = ast.parse(source)
        detector = DecisionDetector()
        detector.visit(tree)

        assert len(detector.decisions) == 2
        # Each should have unique ID
        assert detector.decisions[0].id != detector.decisions[1].id
        assert detector.decisions[0].name == "D1"
        assert detector.decisions[1].name == "D2"


class TestTernaryOperatorDetection:
    """Tests for ternary operator detection."""

    def test_ternary_in_decision(self) -> None:
        """Test detection of ternary operator wrapped in to_decision()."""
        source = 'to_decision(a if cond else b, "TernaryChoice")'
        tree = ast.parse(source, mode="eval")
        detector = DecisionDetector()
        detector.visit(tree)

        assert len(detector.decisions) == 1
        assert detector.decisions[0].name == "TernaryChoice"

    def test_nested_ternary_in_decision(self) -> None:
        """Test detection of nested ternary in decision."""
        source = 'to_decision(x if (a if b else c) else y, "NestedTernary")'
        tree = ast.parse(source, mode="eval")
        detector = DecisionDetector()
        detector.visit(tree)

        assert len(detector.decisions) == 1
        assert detector.decisions[0].name == "NestedTernary"


class TestFunctionFiltering:
    """Tests for filtering non-decision function calls."""

    def test_ignore_other_functions(self) -> None:
        """Test that non-to_decision functions are ignored."""
        source = """
result = other_function(condition, "NotDecision")
result = to_warning(condition, "Warning")
result = to_decision(condition, "RealDecision")
"""
        tree = ast.parse(source)
        detector = DecisionDetector()
        detector.visit(tree)

        assert len(detector.decisions) == 1
        assert detector.decisions[0].name == "RealDecision"

    def test_to_decision_name_filtering(self) -> None:
        """Test that only exact to_decision matches are detected."""
        source = """
to_decision_something(cond, "NotMatch")
to_decision(cond, "Match")
something_to_decision(cond, "NotMatch2")
"""
        tree = ast.parse(source)
        detector = DecisionDetector()
        detector.visit(tree)

        assert len(detector.decisions) == 1
        assert detector.decisions[0].name == "Match"


class TestDecisionMetadata:
    """Tests for decision metadata storage."""

    def test_decision_metadata_fields(self) -> None:
        """Test that all decision metadata fields are populated."""
        source = 'if await to_decision(amount > 1000, "HighValue"): pass'
        tree = ast.parse(source)
        detector = DecisionDetector()
        detector.visit(tree)

        decision = detector.decisions[0]
        assert decision.id is not None
        assert decision.name == "HighValue"
        assert decision.line_number > 0
        assert decision.true_label == "yes"
        assert decision.false_label == "no"

    def test_decision_point_immutability(self) -> None:
        """Test that DecisionPoint is frozen (immutable)."""
        decision = DecisionPoint(
            id="d0", name="Test", line_number=42, line_num=42, true_label="yes", false_label="no"
        )

        # Attempting to modify should raise error
        with pytest.raises(AttributeError):
            decision.name = "Modified"  # type: ignore

    def test_unique_decision_ids(self) -> None:
        """Test that each decision gets a unique ID."""
        source = """
to_decision(cond1, "D1")
to_decision(cond2, "D2")
to_decision(cond3, "D3")
"""
        tree = ast.parse(source)
        detector = DecisionDetector()
        detector.visit(tree)

        assert len(detector.decisions) == 3
        ids = [d.id for d in detector.decisions]
        assert len(set(ids)) == 3  # All unique
        assert ids == ["d0", "d1", "d2"]


class TestErrorMessages:
    """Tests for error message quality."""

    def test_error_includes_line_number(self) -> None:
        """Test that error messages include line number."""
        source = """# Line 1
# Line 2
to_decision(condition)  # Line 3 - missing name arg
"""
        tree = ast.parse(source)
        detector = DecisionDetector()

        with pytest.raises(WorkflowParseError) as exc_info:
            detector.visit(tree)

        assert "Line 3" in str(exc_info.value)

    def test_error_includes_suggestion(self) -> None:
        """Test that error messages include helpful suggestions."""
        source = "to_decision(condition)"
        tree = ast.parse(source, mode="eval")
        detector = DecisionDetector()

        with pytest.raises(WorkflowParseError) as exc_info:
            detector.visit(tree)

        error_msg = str(exc_info.value).lower()
        assert "to_decision" in error_msg
        assert "2 arguments" in error_msg or "name" in error_msg

    def test_error_for_wrong_argument_type(self) -> None:
        """Test error message for wrong argument type."""
        source = "to_decision(condition, 123)"
        tree = ast.parse(source, mode="eval")
        detector = DecisionDetector()

        with pytest.raises(WorkflowParseError) as exc_info:
            detector.visit(tree)

        error_msg = str(exc_info.value)
        assert "string" in error_msg.lower() or "constant" in error_msg.lower()


class TestWorkflowFiles:
    """Integration tests using real workflow files."""

    def test_single_decision_workflow_file(self) -> None:
        """Test detection in single decision workflow file."""
        workflow_file = Path(__file__).parent / "fixtures" / "sample_workflows" / "single_decision_workflow.py"
        if workflow_file.exists():
            source = workflow_file.read_text()
            tree = ast.parse(source)
            detector = DecisionDetector()
            detector.visit(tree)

            assert len(detector.decisions) == 1
            assert detector.decisions[0].name == "HighValue"

    def test_multiple_decision_workflow_file(self) -> None:
        """Test detection in multiple decision workflow file."""
        workflow_file = Path(__file__).parent / "fixtures" / "sample_workflows" / "multiple_decision_workflow.py"
        if workflow_file.exists():
            source = workflow_file.read_text()
            tree = ast.parse(source)
            detector = DecisionDetector()
            detector.visit(tree)

            assert len(detector.decisions) == 2

    def test_elif_chain_workflow_file(self) -> None:
        """Test detection in elif chain workflow file."""
        workflow_file = Path(__file__).parent / "fixtures" / "sample_workflows" / "elif_chain_workflow.py"
        if workflow_file.exists():
            source = workflow_file.read_text()
            tree = ast.parse(source)
            detector = DecisionDetector()
            detector.visit(tree)

            assert len(detector.decisions) == 3


class TestDetectorProperty:
    """Tests for DecisionDetector property."""

    def test_decisions_property_returns_list(self) -> None:
        """Test that decisions property returns list."""
        detector = DecisionDetector()
        assert isinstance(detector.decisions, list)
        assert len(detector.decisions) == 0

    def test_decisions_property_read_only(self) -> None:
        """Test that decisions property cannot be reassigned."""
        detector = DecisionDetector()
        with pytest.raises(AttributeError):
            detector.decisions = []  # type: ignore


class TestEdgeCases:
    """Tests for edge cases and corner cases."""

    def test_attribute_access_function_not_matched(self) -> None:
        """Test that attribute access to non-to_decision functions not matched."""
        source = """
obj.some_method(condition, "Test")
obj.to_decision_v2(condition, "Test2")
"""
        tree = ast.parse(source)
        detector = DecisionDetector()
        detector.visit(tree)

        assert len(detector.decisions) == 0

    def test_error_missing_expression_argument(self) -> None:
        """Test error when expression argument is completely missing."""
        source = 'to_decision(name="OnlyName")'
        tree = ast.parse(source, mode="eval")
        detector = DecisionDetector()

        with pytest.raises(WorkflowParseError) as exc_info:
            detector.visit(tree)

        assert "at least 1 argument" in str(exc_info.value).lower()

    def test_keyword_argument_wrong_type_error(self) -> None:
        """Test error when keyword argument name has wrong type."""
        source = 'to_decision(condition, name=123)'
        tree = ast.parse(source, mode="eval")
        detector = DecisionDetector()

        with pytest.raises(WorkflowParseError) as exc_info:
            detector.visit(tree)

        error_msg = str(exc_info.value)
        assert "string" in error_msg.lower() or "name argument" in error_msg.lower()

    def test_multiple_decisions_with_errors(self) -> None:
        """Test that first valid decision is detected before error."""
        source = """
to_decision(cond1, "Valid")
to_decision(cond2)  # Missing name - error
"""
        tree = ast.parse(source)
        detector = DecisionDetector()

        # First to_decision should be detected successfully
        detector.visit(tree.body[0])
        assert len(detector.decisions) == 1
        assert detector.decisions[0].name == "Valid"

    def test_detector_reuse_after_clear(self) -> None:
        """Test detector can be reused with fresh state."""
        source1 = 'to_decision(cond1, "First")'
        source2 = 'to_decision(cond2, "Second")'

        tree1 = ast.parse(source1, mode="eval")
        tree2 = ast.parse(source2, mode="eval")

        detector = DecisionDetector()

        # First analysis
        detector.visit(tree1)
        assert len(detector.decisions) == 1
        assert detector.decisions[0].name == "First"

        # Create new detector for second analysis (fresh state)
        detector2 = DecisionDetector()
        detector2.visit(tree2)
        assert len(detector2.decisions) == 1
        assert detector2.decisions[0].name == "Second"

    def test_deeply_nested_decisions(self) -> None:
        """Test detection in deeply nested code structures."""
        source = """
if condition:
    if nested1:
        if nested2:
            if await to_decision(deep_cond, "DeepDecision"):
                pass
"""
        tree = ast.parse(source)
        detector = DecisionDetector()
        detector.visit(tree)

        assert len(detector.decisions) == 1
        assert detector.decisions[0].name == "DeepDecision"

    def test_decision_in_function_call_as_argument(self) -> None:
        """Test detection when to_decision is inside another function call."""
        source = 'some_function(to_decision(cond, "Nested"))'
        tree = ast.parse(source)
        detector = DecisionDetector()
        detector.visit(tree)

        # Should detect the nested to_decision call
        assert len(detector.decisions) == 1
        assert detector.decisions[0].name == "Nested"

    def test_non_name_non_attribute_callable(self) -> None:
        """Test that non-Name/Attribute callables are ignored."""
        source = """
(lambda x: x)(condition, "Test")
"""
        tree = ast.parse(source)
        detector = DecisionDetector()
        detector.visit(tree)

        # Lambda call should not match to_decision
        assert len(detector.decisions) == 0

    def test_keyword_argument_no_positional_name(self) -> None:
        """Test keyword argument name extraction without positional second arg."""
        source = 'to_decision(condition, name="KeywordOnly")'
        tree = ast.parse(source, mode="eval")
        detector = DecisionDetector()
        detector.visit(tree)

        assert len(detector.decisions) == 1
        assert detector.decisions[0].name == "KeywordOnly"


# ============================================================================
# Signal Detection Tests (Story 4.1)
# ============================================================================


class TestSignalDetectorBasic:
    """Basic signal detection tests."""

    def test_single_signal_detection(self) -> None:
        """Test detection of a single wait_condition() call."""
        source = """
result = await wait_condition(lambda: self.approved, timedelta(hours=24), "WaitForApproval")
"""
        tree = ast.parse(source)
        detector = SignalDetector()
        detector.visit(tree)

        assert len(detector.signals) == 1
        assert detector.signals[0].name == "WaitForApproval"

    def test_multiple_signals_detection(self) -> None:
        """Test detection of multiple wait_condition() calls."""
        source = """
first = await wait_condition(lambda: self.first, timedelta(hours=12), "FirstSignal")
second = await wait_condition(lambda: self.second, timedelta(hours=24), "SecondSignal")
"""
        tree = ast.parse(source)
        detector = SignalDetector()
        detector.visit(tree)

        assert len(detector.signals) == 2
        assert detector.signals[0].name == "FirstSignal"
        assert detector.signals[1].name == "SecondSignal"

    def test_ignore_non_wait_condition_calls(self) -> None:
        """Test that non-wait_condition function calls are ignored."""
        source = """
some_function(lambda: x, timedelta(hours=1), "NotASignal")
other_call(condition, timeout, "AlsoNotASignal")
"""
        tree = ast.parse(source)
        detector = SignalDetector()
        detector.visit(tree)

        assert len(detector.signals) == 0

    def test_attribute_access_wait_condition(self) -> None:
        """Test detection of workflow.wait_condition() attribute access."""
        source = """
result = await workflow.wait_condition(lambda: self.ready, timedelta(hours=1), "AttributeSignal")
"""
        tree = ast.parse(source)
        detector = SignalDetector()
        detector.visit(tree)

        assert len(detector.signals) == 1
        assert detector.signals[0].name == "AttributeSignal"


class TestSignalNameExtraction:
    """Tests for signal name extraction from arguments."""

    def test_extract_signal_name_from_literal(self) -> None:
        """Test extraction of signal name from string literal."""
        source = 'wait_condition(condition, timeout, "MySignal")'
        tree = ast.parse(source, mode="eval")
        detector = SignalDetector()
        detector.visit(tree)

        assert len(detector.signals) == 1
        assert detector.signals[0].name == "MySignal"

    def test_dynamic_signal_name_uses_unnamed(self) -> None:
        """Test that dynamic signal name (variable) uses 'UnnamedSignal'."""
        source = """
signal_name = "Dynamic"
wait_condition(condition, timeout, signal_name)
"""
        tree = ast.parse(source)
        detector = SignalDetector()

        # Should not raise error, but use fallback
        detector.visit(tree)

        assert len(detector.signals) == 1
        assert detector.signals[0].name == "UnnamedSignal"

    def test_missing_signal_name_raises_error(self) -> None:
        """Test that missing signal name argument raises InvalidSignalError."""
        source = 'wait_condition(condition, timeout)'
        tree = ast.parse(source, mode="eval")
        detector = SignalDetector()

        with pytest.raises(InvalidSignalError) as exc_info:
            detector.visit(tree)

        error_msg = str(exc_info.value)
        assert "3 arguments" in error_msg
        assert "got 2" in error_msg

    def test_completely_missing_arguments_raises_error(self) -> None:
        """Test that wait_condition with no arguments raises error."""
        source = 'wait_condition()'
        tree = ast.parse(source, mode="eval")
        detector = SignalDetector()

        with pytest.raises(InvalidSignalError) as exc_info:
            detector.visit(tree)

        error_msg = str(exc_info.value)
        assert "3 arguments" in error_msg
        assert "got 0" in error_msg


class TestSignalMetadataExtraction:
    """Tests for signal metadata extraction (condition, timeout, line number)."""

    def test_condition_expression_extracted(self) -> None:
        """Test that condition expression is extracted correctly."""
        source = 'wait_condition(lambda: self.approved, timedelta(hours=24), "Test")'
        tree = ast.parse(source, mode="eval")
        detector = SignalDetector()
        detector.visit(tree)

        assert len(detector.signals) == 1
        assert "lambda" in detector.signals[0].condition_expr
        assert "approved" in detector.signals[0].condition_expr

    def test_timeout_expression_extracted(self) -> None:
        """Test that timeout expression is extracted correctly."""
        source = 'wait_condition(lambda: x, timedelta(hours=24), "Test")'
        tree = ast.parse(source, mode="eval")
        detector = SignalDetector()
        detector.visit(tree)

        assert len(detector.signals) == 1
        assert "timedelta" in detector.signals[0].timeout_expr
        assert "24" in detector.signals[0].timeout_expr

    def test_source_line_numbers_correct(self) -> None:
        """Test that source line numbers are recorded correctly."""
        source = """

result = await wait_condition(lambda: x, timedelta(hours=1), "Line3")


second = await wait_condition(lambda: y, timedelta(hours=2), "Line6")
"""
        tree = ast.parse(source)
        detector = SignalDetector()
        detector.visit(tree)

        assert len(detector.signals) == 2
        assert detector.signals[0].source_line == 3
        assert detector.signals[1].source_line == 6

    def test_node_id_generation_deterministic(self) -> None:
        """Test that node IDs are deterministic based on name and line."""
        source = """
await wait_condition(lambda: x, timedelta(hours=1), "MySignal")
"""
        tree = ast.parse(source)
        detector = SignalDetector()
        detector.visit(tree)

        assert len(detector.signals) == 1
        signal = detector.signals[0]
        assert signal.node_id == f"sig_mysignal_{signal.source_line}"

    def test_node_id_handles_spaces(self) -> None:
        """Test that node IDs handle signal names with spaces."""
        source = 'wait_condition(lambda: x, timedelta(hours=1), "Wait For Approval")'
        tree = ast.parse(source, mode="eval")
        detector = SignalDetector()
        detector.visit(tree)

        assert len(detector.signals) == 1
        assert "wait_for_approval" in detector.signals[0].node_id


class TestSignalWorkflowFiles:
    """Integration tests using signal workflow fixture files."""

    def test_signal_simple_workflow_file(self) -> None:
        """Test detection in simple signal workflow file."""
        workflow_file = Path(__file__).parent / "fixtures" / "sample_workflows" / "signal_simple.py"
        if workflow_file.exists():
            source = workflow_file.read_text()
            tree = ast.parse(source)
            detector = SignalDetector()
            detector.visit(tree)

            assert len(detector.signals) == 1
            assert detector.signals[0].name == "WaitForApproval"

    def test_signal_multiple_workflow_file(self) -> None:
        """Test detection in multiple signal workflow file."""
        workflow_file = Path(__file__).parent / "fixtures" / "sample_workflows" / "signal_multiple.py"
        if workflow_file.exists():
            source = workflow_file.read_text()
            tree = ast.parse(source)
            detector = SignalDetector()
            detector.visit(tree)

            assert len(detector.signals) == 2
            assert detector.signals[0].name == "WaitForFirstApproval"
            assert detector.signals[1].name == "WaitForSecondApproval"

    def test_signal_with_decision_workflow_file(self) -> None:
        """Test signal detection in workflow with both signals and decisions."""
        workflow_file = Path(__file__).parent / "fixtures" / "sample_workflows" / "signal_with_decision.py"
        if workflow_file.exists():
            source = workflow_file.read_text()
            tree = ast.parse(source)

            # Test signals
            signal_detector = SignalDetector()
            signal_detector.visit(tree)
            assert len(signal_detector.signals) == 1
            assert signal_detector.signals[0].name == "WaitForApproval"

            # Test decisions also detected
            decision_detector = DecisionDetector()
            decision_detector.visit(tree)
            assert len(decision_detector.decisions) == 1
            assert decision_detector.decisions[0].name == "HighValue"

    def test_signal_dynamic_name_workflow_file(self) -> None:
        """Test detection in workflow with dynamic signal name."""
        workflow_file = Path(__file__).parent / "fixtures" / "sample_workflows" / "signal_dynamic_name.py"
        if workflow_file.exists():
            source = workflow_file.read_text()
            tree = ast.parse(source)
            detector = SignalDetector()
            detector.visit(tree)

            # Should detect signal but use UnnamedSignal fallback
            assert len(detector.signals) == 1
            assert detector.signals[0].name == "UnnamedSignal"


class TestSignalDetectorProperty:
    """Tests for SignalDetector property."""

    def test_signals_property_returns_list(self) -> None:
        """Test that signals property returns list."""
        detector = SignalDetector()
        assert isinstance(detector.signals, list)
        assert len(detector.signals) == 0

    def test_signals_property_read_only(self) -> None:
        """Test that signals property cannot be reassigned."""
        detector = SignalDetector()
        with pytest.raises(AttributeError):
            detector.signals = []  # type: ignore


class TestSignalEdgeCases:
    """Tests for signal detection edge cases."""

    def test_nested_signal_calls(self) -> None:
        """Test detection of signals in nested code structures."""
        source = """
if condition:
    if nested:
        result = await wait_condition(lambda: x, timedelta(hours=1), "NestedSignal")
"""
        tree = ast.parse(source)
        detector = SignalDetector()
        detector.visit(tree)

        assert len(detector.signals) == 1
        assert detector.signals[0].name == "NestedSignal"

    def test_signal_in_function_call_as_argument(self) -> None:
        """Test detection when wait_condition is inside another function call."""
        source = 'some_function(wait_condition(cond, timeout, "Nested"))'
        tree = ast.parse(source)
        detector = SignalDetector()
        detector.visit(tree)

        assert len(detector.signals) == 1
        assert detector.signals[0].name == "Nested"

    def test_attribute_access_function_not_matched(self) -> None:
        """Test that attribute access to non-wait_condition functions not matched."""
        source = """
obj.some_method(condition, timeout, "Test")
obj.wait_condition_v2(condition, timeout, "Test2")
"""
        tree = ast.parse(source)
        detector = SignalDetector()
        detector.visit(tree)

        assert len(detector.signals) == 0

    def test_signal_point_dataclass_fields(self) -> None:
        """Test that SignalPoint has all required fields."""
        source = 'wait_condition(lambda: x, timedelta(hours=1), "TestSignal")'
        tree = ast.parse(source, mode="eval")
        detector = SignalDetector()
        detector.visit(tree)

        assert len(detector.signals) == 1
        signal = detector.signals[0]

        # Verify all fields exist and have correct types
        assert isinstance(signal.name, str)
        assert isinstance(signal.condition_expr, str)
        assert isinstance(signal.timeout_expr, str)
        assert isinstance(signal.source_line, int)
        assert isinstance(signal.node_id, str)

        # Verify field values are populated
        assert signal.name == "TestSignal"
        assert len(signal.condition_expr) > 0
        assert len(signal.timeout_expr) > 0
        assert signal.source_line > 0
        assert len(signal.node_id) > 0

    def test_detector_reuse_creates_fresh_state(self) -> None:
        """Test that each detector instance has independent state."""
        source1 = 'wait_condition(c1, t1, "First")'
        source2 = 'wait_condition(c2, t2, "Second")'

        tree1 = ast.parse(source1, mode="eval")
        tree2 = ast.parse(source2, mode="eval")

        detector1 = SignalDetector()
        detector1.visit(tree1)
        assert len(detector1.signals) == 1
        assert detector1.signals[0].name == "First"

        # Create new detector for independent state
        detector2 = SignalDetector()
        detector2.visit(tree2)
        assert len(detector2.signals) == 1
        assert detector2.signals[0].name == "Second"

        # Original detector unchanged
        assert len(detector1.signals) == 1
        assert detector1.signals[0].name == "First"


# ============================================================================
# Child Workflow Detection Tests (Story 6.1)
# ============================================================================


class TestChildWorkflowDetectorBasic:
    """Basic child workflow detection tests."""

    def test_single_child_workflow_class_reference(self) -> None:
        """Test detection of single execute_child_workflow with class reference."""
        source = """
result = await workflow.execute_child_workflow(ChildWorkflow, args={"param": value})
"""
        tree = ast.parse(source)
        detector = ChildWorkflowDetector()
        detector.set_parent_workflow("ParentWorkflow")
        detector.visit(tree)

        assert len(detector.child_calls) == 1
        assert detector.child_calls[0].workflow_name == "ChildWorkflow"
        assert detector.child_calls[0].parent_workflow == "ParentWorkflow"

    def test_single_child_workflow_string_literal(self) -> None:
        """Test detection of single execute_child_workflow with string literal."""
        source = """
result = await workflow.execute_child_workflow("ChildWorkflowName", args={"param": value})
"""
        tree = ast.parse(source)
        detector = ChildWorkflowDetector()
        detector.set_parent_workflow("ParentWorkflow")
        detector.visit(tree)

        assert len(detector.child_calls) == 1
        assert detector.child_calls[0].workflow_name == "ChildWorkflowName"
        assert detector.child_calls[0].parent_workflow == "ParentWorkflow"

    def test_multiple_child_workflow_calls(self) -> None:
        """Test detection of multiple child workflow calls."""
        source = """
result1 = await workflow.execute_child_workflow(FirstChild, args={})
result2 = await workflow.execute_child_workflow("SecondChild", args={})
result3 = await workflow.execute_child_workflow(ThirdChild, args={})
"""
        tree = ast.parse(source)
        detector = ChildWorkflowDetector()
        detector.set_parent_workflow("ParentWorkflow")
        detector.visit(tree)

        assert len(detector.child_calls) == 3
        assert detector.child_calls[0].workflow_name == "FirstChild"
        assert detector.child_calls[1].workflow_name == "SecondChild"
        assert detector.child_calls[2].workflow_name == "ThirdChild"

    def test_ignore_non_child_workflow_calls(self) -> None:
        """Test that non-execute_child_workflow calls are ignored."""
        source = """
result = await workflow.execute_activity(my_activity, args={})
result = await workflow.start_child_workflow(Child, args={})
result = await other.execute_child_workflow(Child, args={})
"""
        tree = ast.parse(source)
        detector = ChildWorkflowDetector()
        detector.set_parent_workflow("ParentWorkflow")
        detector.visit(tree)

        assert len(detector.child_calls) == 0


class TestChildWorkflowNameExtraction:
    """Tests for child workflow name extraction."""

    def test_class_reference_extraction(self) -> None:
        """Test extraction of workflow name from class reference."""
        source = "workflow.execute_child_workflow(MyChildWorkflow)"
        tree = ast.parse(source, mode="eval")
        detector = ChildWorkflowDetector()
        detector.set_parent_workflow("Parent")
        detector.visit(tree)

        assert len(detector.child_calls) == 1
        assert detector.child_calls[0].workflow_name == "MyChildWorkflow"

    def test_string_literal_extraction(self) -> None:
        """Test extraction of workflow name from string literal."""
        source = 'workflow.execute_child_workflow("MyChildWorkflow")'
        tree = ast.parse(source, mode="eval")
        detector = ChildWorkflowDetector()
        detector.set_parent_workflow("Parent")
        detector.visit(tree)

        assert len(detector.child_calls) == 1
        assert detector.child_calls[0].workflow_name == "MyChildWorkflow"

    def test_missing_workflow_argument_error(self) -> None:
        """Test error when workflow argument is missing."""
        source = "workflow.execute_child_workflow()"
        tree = ast.parse(source, mode="eval")
        detector = ChildWorkflowDetector()
        detector.set_parent_workflow("Parent")

        with pytest.raises(WorkflowParseError) as exc_info:
            detector.visit(tree)

        error_msg = str(exc_info.value)
        assert "at least 1 argument" in error_msg.lower()

    def test_invalid_workflow_argument_type_error(self) -> None:
        """Test error when workflow argument is not class or string."""
        source = "workflow.execute_child_workflow(123)"
        tree = ast.parse(source, mode="eval")
        detector = ChildWorkflowDetector()
        detector.set_parent_workflow("Parent")

        with pytest.raises(WorkflowParseError) as exc_info:
            detector.visit(tree)

        error_msg = str(exc_info.value)
        assert "class reference or string" in error_msg.lower()


class TestChildWorkflowMetadata:
    """Tests for child workflow call metadata."""

    def test_call_site_line_number(self) -> None:
        """Test that call site line numbers are recorded correctly."""
        source = """

result1 = await workflow.execute_child_workflow(Child1)


result2 = await workflow.execute_child_workflow(Child2)
"""
        tree = ast.parse(source)
        detector = ChildWorkflowDetector()
        detector.set_parent_workflow("Parent")
        detector.visit(tree)

        assert len(detector.child_calls) == 2
        assert detector.child_calls[0].call_site_line == 3
        assert detector.child_calls[1].call_site_line == 6

    def test_call_id_generation_deterministic(self) -> None:
        """Test that call IDs are deterministic based on name and line."""
        source = """
await workflow.execute_child_workflow(MyChild)
"""
        tree = ast.parse(source)
        detector = ChildWorkflowDetector()
        detector.set_parent_workflow("Parent")
        detector.visit(tree)

        assert len(detector.child_calls) == 1
        call = detector.child_calls[0]
        assert call.call_id == f"child_mychild_{call.call_site_line}"

    def test_call_id_handles_spaces(self) -> None:
        """Test that call IDs handle workflow names with spaces."""
        source = 'workflow.execute_child_workflow("My Child Workflow")'
        tree = ast.parse(source, mode="eval")
        detector = ChildWorkflowDetector()
        detector.set_parent_workflow("Parent")
        detector.visit(tree)

        assert len(detector.child_calls) == 1
        assert "my_child_workflow" in detector.child_calls[0].call_id

    def test_parent_workflow_recorded(self) -> None:
        """Test that parent workflow name is recorded in each call."""
        source = """
result1 = await workflow.execute_child_workflow(Child1)
result2 = await workflow.execute_child_workflow(Child2)
"""
        tree = ast.parse(source)
        detector = ChildWorkflowDetector()
        detector.set_parent_workflow("ParentWorkflowName")
        detector.visit(tree)

        assert len(detector.child_calls) == 2
        assert detector.child_calls[0].parent_workflow == "ParentWorkflowName"
        assert detector.child_calls[1].parent_workflow == "ParentWorkflowName"

    def test_child_workflow_call_dataclass_fields(self) -> None:
        """Test that ChildWorkflowCall has all required fields."""
        source = 'workflow.execute_child_workflow(TestChild)'
        tree = ast.parse(source, mode="eval")
        detector = ChildWorkflowDetector()
        detector.set_parent_workflow("Parent")
        detector.visit(tree)

        assert len(detector.child_calls) == 1
        call = detector.child_calls[0]

        # Verify all fields exist and have correct types
        assert isinstance(call.workflow_name, str)
        assert isinstance(call.call_site_line, int)
        assert isinstance(call.call_id, str)
        assert isinstance(call.parent_workflow, str)

        # Verify field values are populated
        assert call.workflow_name == "TestChild"
        assert call.call_site_line > 0
        assert len(call.call_id) > 0
        assert call.parent_workflow == "Parent"


class TestChildWorkflowNestedDetection:
    """Tests for child workflow detection in nested code structures."""

    def test_child_workflow_in_if_block(self) -> None:
        """Test detection of child workflow call inside if block."""
        source = """
if condition:
    result = await workflow.execute_child_workflow(ChildWorkflow)
"""
        tree = ast.parse(source)
        detector = ChildWorkflowDetector()
        detector.set_parent_workflow("Parent")
        detector.visit(tree)

        assert len(detector.child_calls) == 1
        assert detector.child_calls[0].workflow_name == "ChildWorkflow"

    def test_child_workflow_in_else_block(self) -> None:
        """Test detection of child workflow call inside else block."""
        source = """
if condition:
    pass
else:
    result = await workflow.execute_child_workflow(ChildWorkflow)
"""
        tree = ast.parse(source)
        detector = ChildWorkflowDetector()
        detector.set_parent_workflow("Parent")
        detector.visit(tree)

        assert len(detector.child_calls) == 1
        assert detector.child_calls[0].workflow_name == "ChildWorkflow"

    def test_child_workflow_in_for_loop(self) -> None:
        """Test detection of child workflow call inside for loop."""
        source = """
for item in items:
    result = await workflow.execute_child_workflow(ChildWorkflow)
"""
        tree = ast.parse(source)
        detector = ChildWorkflowDetector()
        detector.set_parent_workflow("Parent")
        detector.visit(tree)

        assert len(detector.child_calls) == 1
        assert detector.child_calls[0].workflow_name == "ChildWorkflow"

    def test_deeply_nested_child_workflow(self) -> None:
        """Test detection of child workflow in deeply nested structure."""
        source = """
if outer:
    if inner1:
        if inner2:
            result = await workflow.execute_child_workflow(DeepChild)
"""
        tree = ast.parse(source)
        detector = ChildWorkflowDetector()
        detector.set_parent_workflow("Parent")
        detector.visit(tree)

        assert len(detector.child_calls) == 1
        assert detector.child_calls[0].workflow_name == "DeepChild"

    def test_multiple_child_workflows_different_blocks(self) -> None:
        """Test detection of multiple child workflows in different blocks."""
        source = """
if condition1:
    result1 = await workflow.execute_child_workflow(Child1)
else:
    result2 = await workflow.execute_child_workflow(Child2)

for item in items:
    result3 = await workflow.execute_child_workflow(Child3)
"""
        tree = ast.parse(source)
        detector = ChildWorkflowDetector()
        detector.set_parent_workflow("Parent")
        detector.visit(tree)

        assert len(detector.child_calls) == 3
        assert detector.child_calls[0].workflow_name == "Child1"
        assert detector.child_calls[1].workflow_name == "Child2"
        assert detector.child_calls[2].workflow_name == "Child3"


class TestChildWorkflowDetectorProperty:
    """Tests for ChildWorkflowDetector property."""

    def test_child_calls_property_returns_list(self) -> None:
        """Test that child_calls property returns list."""
        detector = ChildWorkflowDetector()
        assert isinstance(detector.child_calls, list)
        assert len(detector.child_calls) == 0

    def test_child_calls_property_read_only(self) -> None:
        """Test that child_calls property cannot be reassigned."""
        detector = ChildWorkflowDetector()
        with pytest.raises(AttributeError):
            detector.child_calls = []  # type: ignore


class TestChildWorkflowEdgeCases:
    """Tests for child workflow detection edge cases."""

    def test_child_workflow_call_immutability(self) -> None:
        """Test that ChildWorkflowCall is frozen (immutable)."""
        call = ChildWorkflowCall(
            workflow_name="Test",
            call_site_line=10,
            call_id="child_test_10",
            parent_workflow="Parent",
        )

        # Attempting to modify should raise error
        with pytest.raises(AttributeError):
            call.workflow_name = "Modified"  # type: ignore

    def test_detector_reuse_creates_fresh_state(self) -> None:
        """Test that each detector instance has independent state."""
        source1 = "workflow.execute_child_workflow(Child1)"
        source2 = "workflow.execute_child_workflow(Child2)"

        tree1 = ast.parse(source1, mode="eval")
        tree2 = ast.parse(source2, mode="eval")

        detector1 = ChildWorkflowDetector()
        detector1.set_parent_workflow("Parent1")
        detector1.visit(tree1)
        assert len(detector1.child_calls) == 1
        assert detector1.child_calls[0].workflow_name == "Child1"

        # Create new detector for independent state
        detector2 = ChildWorkflowDetector()
        detector2.set_parent_workflow("Parent2")
        detector2.visit(tree2)
        assert len(detector2.child_calls) == 1
        assert detector2.child_calls[0].workflow_name == "Child2"

        # Original detector unchanged
        assert len(detector1.child_calls) == 1
        assert detector1.child_calls[0].workflow_name == "Child1"
        assert detector1.child_calls[0].parent_workflow == "Parent1"

    def test_set_parent_workflow_updates_context(self) -> None:
        """Test that set_parent_workflow updates parent context."""
        source = "workflow.execute_child_workflow(Child)"
        tree = ast.parse(source, mode="eval")

        detector = ChildWorkflowDetector()
        detector.set_parent_workflow("FirstParent")
        detector.visit(tree)

        assert detector.child_calls[0].parent_workflow == "FirstParent"

    def test_attribute_access_non_workflow_object(self) -> None:
        """Test that execute_child_workflow on non-workflow object is ignored."""
        source = """
other_object.execute_child_workflow(Child)
obj.execute_child_workflow(Child)
"""
        tree = ast.parse(source)
        detector = ChildWorkflowDetector()
        detector.set_parent_workflow("Parent")
        detector.visit(tree)

        # Should not detect any child workflow calls
        assert len(detector.child_calls) == 0

    def test_child_workflow_in_function_call_argument(self) -> None:
        """Test detection when execute_child_workflow is nested in another call."""
        source = """
some_function(await workflow.execute_child_workflow(Child))
"""
        tree = ast.parse(source)
        detector = ChildWorkflowDetector()
        detector.set_parent_workflow("Parent")
        detector.visit(tree)

        # Should detect the nested execute_child_workflow call
        assert len(detector.child_calls) == 1
        assert detector.child_calls[0].workflow_name == "Child"


class TestChildWorkflowErrorMessages:
    """Tests for child workflow detection error messages."""

    def test_error_includes_line_number(self) -> None:
        """Test that error messages include line number."""
        source = """# Line 1
# Line 2
workflow.execute_child_workflow()  # Line 3 - missing workflow arg
"""
        tree = ast.parse(source)
        detector = ChildWorkflowDetector()
        detector.set_parent_workflow("Parent")

        with pytest.raises(WorkflowParseError) as exc_info:
            detector.visit(tree)

        assert "Line 3" in str(exc_info.value)

    def test_error_includes_suggestion(self) -> None:
        """Test that error messages include helpful suggestions."""
        source = "workflow.execute_child_workflow()"
        tree = ast.parse(source, mode="eval")
        detector = ChildWorkflowDetector()
        detector.set_parent_workflow("Parent")

        with pytest.raises(WorkflowParseError) as exc_info:
            detector.visit(tree)

        error_msg = str(exc_info.value).lower()
        assert "execute_child_workflow" in error_msg
        assert "at least 1 argument" in error_msg

    def test_error_for_wrong_argument_type(self) -> None:
        """Test error message for wrong argument type."""
        source = "workflow.execute_child_workflow(123)"
        tree = ast.parse(source, mode="eval")
        detector = ChildWorkflowDetector()
        detector.set_parent_workflow("Parent")

        with pytest.raises(WorkflowParseError) as exc_info:
            detector.visit(tree)

        error_msg = str(exc_info.value).lower()
        assert "class reference or string" in error_msg


# =====================================================================
# External Signal Detector Tests (Epic 7)
# =====================================================================


class TestExternalSignalDetectorBasic:
    """Basic external signal detection tests."""

    def test_single_external_signal_two_step_pattern(self) -> None:
        """Test basic two-step pattern: handle = get_external_workflow_handle(...); await handle.signal(...)."""
        source = """
import temporalio.workflow as workflow

@workflow.defn
class OrderWorkflow:
    @workflow.run
    async def run(self):
        handle = workflow.get_external_workflow_handle("shipping-123")
        await handle.signal("ship_order", order_data)
"""
        tree = ast.parse(source)
        detector = ExternalSignalDetector()
        detector.set_source_workflow("OrderWorkflow")
        detector.set_file_path(Path("workflow.py"))
        detector.visit(tree)

        signals = detector.external_signals
        assert len(signals) == 1
        assert signals[0].signal_name == "ship_order"
        assert signals[0].target_workflow_pattern == "shipping-123"
        assert signals[0].source_workflow == "OrderWorkflow"
        assert signals[0].source_line == 9
        assert signals[0].node_id == "ext_sig_ship_order_9"

    def test_single_external_signal_inline_pattern(self) -> None:
        """Test inline pattern: await get_external_workflow_handle(...).signal(...)."""
        source = """
handle = await workflow.get_external_workflow_handle("inventory-456").signal("check_stock", product_id)
"""
        tree = ast.parse(source)
        detector = ExternalSignalDetector()
        detector.set_source_workflow("CheckoutWorkflow")
        detector.set_file_path(Path("workflow.py"))
        detector.visit(tree)

        signals = detector.external_signals
        assert len(signals) == 1
        assert signals[0].signal_name == "check_stock"
        assert signals[0].target_workflow_pattern == "inventory-456"
        assert signals[0].source_workflow == "CheckoutWorkflow"
        assert signals[0].node_id == "ext_sig_check_stock_2"

    def test_multiple_external_signals_to_different_targets(self) -> None:
        """Test workflow with multiple external signals to different workflows."""
        source = """
handle1 = workflow.get_external_workflow_handle("shipping-123")
await handle1.signal("ship_order", order_data)

handle2 = workflow.get_external_workflow_handle("payment-456")
await handle2.signal("process_payment", payment_data)
"""
        tree = ast.parse(source)
        detector = ExternalSignalDetector()
        detector.set_source_workflow("OrderWorkflow")
        detector.set_file_path(Path("workflow.py"))
        detector.visit(tree)

        signals = detector.external_signals
        assert len(signals) == 2
        assert signals[0].signal_name == "ship_order"
        assert signals[0].target_workflow_pattern == "shipping-123"
        assert signals[1].signal_name == "process_payment"
        assert signals[1].target_workflow_pattern == "payment-456"

    def test_multiple_external_signals_to_same_target(self) -> None:
        """Test multiple signals sent to same workflow (unique node IDs)."""
        source = """
handle = workflow.get_external_workflow_handle("shipping-123")
await handle.signal("ship_order", order_data)
await handle.signal("update_tracking", tracking_data)
"""
        tree = ast.parse(source)
        detector = ExternalSignalDetector()
        detector.set_source_workflow("OrderWorkflow")
        detector.set_file_path(Path("workflow.py"))
        detector.visit(tree)

        signals = detector.external_signals
        assert len(signals) == 2
        assert signals[0].signal_name == "ship_order"
        assert signals[0].node_id == "ext_sig_ship_order_3"
        assert signals[1].signal_name == "update_tracking"
        assert signals[1].node_id == "ext_sig_update_tracking_4"


class TestExternalSignalDetectorPatternExtraction:
    """Test target workflow pattern extraction."""

    def test_format_string_target_pattern_extraction(self) -> None:
        """Test f-string workflow ID converted to wildcard pattern."""
        source = """
handle = workflow.get_external_workflow_handle(f"shipping-{order_id}")
await handle.signal("ship_order", data)
"""
        tree = ast.parse(source)
        detector = ExternalSignalDetector()
        detector.set_source_workflow("OrderWorkflow")
        detector.set_file_path(Path("workflow.py"))
        detector.visit(tree)

        signals = detector.external_signals
        assert len(signals) == 1
        assert signals[0].target_workflow_pattern == "shipping-{*}"

    def test_format_string_multiple_placeholders(self) -> None:
        """Test f-string with multiple placeholders."""
        source = """
handle = workflow.get_external_workflow_handle(f"ship-{region}-{order_id}")
await handle.signal("ship", data)
"""
        tree = ast.parse(source)
        detector = ExternalSignalDetector()
        detector.set_source_workflow("OrderWorkflow")
        detector.set_file_path(Path("workflow.py"))
        detector.visit(tree)

        signals = detector.external_signals
        assert len(signals) == 1
        assert signals[0].target_workflow_pattern == "ship-{*}-{*}"

    def test_dynamic_target_fallback_variable(self) -> None:
        """Test variable workflow ID falls back to <dynamic>."""
        source = """
handle = workflow.get_external_workflow_handle(workflow_id)
await handle.signal("notify", data)
"""
        tree = ast.parse(source)
        detector = ExternalSignalDetector()
        detector.set_source_workflow("OrderWorkflow")
        detector.set_file_path(Path("workflow.py"))
        detector.visit(tree)

        signals = detector.external_signals
        assert len(signals) == 1
        assert signals[0].target_workflow_pattern == "<dynamic>"

    def test_dynamic_target_fallback_function_call(self) -> None:
        """Test function call workflow ID falls back to <dynamic>."""
        source = """
handle = workflow.get_external_workflow_handle(compute_workflow_id())
await handle.signal("notify", data)
"""
        tree = ast.parse(source)
        detector = ExternalSignalDetector()
        detector.set_source_workflow("OrderWorkflow")
        detector.set_file_path(Path("workflow.py"))
        detector.visit(tree)

        signals = detector.external_signals
        assert len(signals) == 1
        assert signals[0].target_workflow_pattern == "<dynamic>"

    def test_unknown_target_pattern_fallback(self) -> None:
        """Test unknown AST node type falls back to <unknown>."""
        # Create an AST tree with a complex expression that doesn't match known patterns
        # Use a binary operation as workflow ID (not typical but tests edge case)
        source = """
handle = workflow.get_external_workflow_handle(prefix + suffix)
await handle.signal("notify", data)
"""
        tree = ast.parse(source)
        detector = ExternalSignalDetector()
        detector.set_source_workflow("OrderWorkflow")
        detector.set_file_path(Path("workflow.py"))
        detector.visit(tree)

        signals = detector.external_signals
        assert len(signals) == 1
        # Binary operation (BinOp) is not Name or Call, so falls back to <unknown>
        assert signals[0].target_workflow_pattern == "<unknown>"


class TestExternalSignalDetectorEdgeCases:
    """Edge case tests for external signal detection."""

    def test_signal_inside_conditional_if_block(self) -> None:
        """Test signal call inside if statement."""
        source = """
if condition:
    handle = workflow.get_external_workflow_handle("shipping-123")
    await handle.signal("ship_order", data)
"""
        tree = ast.parse(source)
        detector = ExternalSignalDetector()
        detector.set_source_workflow("OrderWorkflow")
        detector.set_file_path(Path("workflow.py"))
        detector.visit(tree)

        signals = detector.external_signals
        assert len(signals) == 1
        assert signals[0].signal_name == "ship_order"

    def test_signal_inside_loop_for_block(self) -> None:
        """Test signal call inside for loop."""
        source = """
for item in items:
    handle = workflow.get_external_workflow_handle(f"process-{item}")
    await handle.signal("process", item)
"""
        tree = ast.parse(source)
        detector = ExternalSignalDetector()
        detector.set_source_workflow("BatchWorkflow")
        detector.set_file_path(Path("workflow.py"))
        detector.visit(tree)

        signals = detector.external_signals
        assert len(signals) == 1
        assert signals[0].signal_name == "process"
        assert signals[0].target_workflow_pattern == "process-{*}"

    def test_external_signals_property_returns_list(self) -> None:
        """Test external_signals property returns list."""
        source = """
handle = workflow.get_external_workflow_handle("test-123")
await handle.signal("test_signal", data)
"""
        tree = ast.parse(source)
        detector = ExternalSignalDetector()
        detector.set_source_workflow("TestWorkflow")
        detector.set_file_path(Path("workflow.py"))
        detector.visit(tree)

        signals = detector.external_signals
        assert isinstance(signals, list)
        assert len(signals) == 1

    def test_external_signals_property_immutable(self) -> None:
        """Test modifying returned list doesn't affect detector internal state."""
        source = """
handle = workflow.get_external_workflow_handle("test-123")
await handle.signal("test_signal", data)
"""
        tree = ast.parse(source)
        detector = ExternalSignalDetector()
        detector.set_source_workflow("TestWorkflow")
        detector.set_file_path(Path("workflow.py"))
        detector.visit(tree)

        signals1 = detector.external_signals
        signals1.clear()
        signals2 = detector.external_signals
        assert len(signals2) == 1

    def test_detector_reuse_creates_fresh_state(self) -> None:
        """Test creating two detector instances have independent state."""
        source = """
handle = workflow.get_external_workflow_handle("test-123")
await handle.signal("test_signal", data)
"""
        tree = ast.parse(source)

        detector1 = ExternalSignalDetector()
        detector1.set_source_workflow("Workflow1")
        detector1.set_file_path(Path("workflow1.py"))
        detector1.visit(tree)

        detector2 = ExternalSignalDetector()
        detector2.set_source_workflow("Workflow2")
        detector2.set_file_path(Path("workflow2.py"))
        detector2.visit(tree)

        assert len(detector1.external_signals) == 1
        assert len(detector2.external_signals) == 1
        assert detector1.external_signals[0].source_workflow == "Workflow1"
        assert detector2.external_signals[0].source_workflow == "Workflow2"


class TestExternalSignalDetectorNodeIdFormat:
    """Test node ID format generation."""

    def test_external_signal_node_id_format_deterministic(self) -> None:
        """Test node ID format is ext_sig_{signal_name}_{line}."""
        source = """
handle = workflow.get_external_workflow_handle("test-123")
await handle.signal("ship_order", data)
"""
        tree = ast.parse(source)
        detector = ExternalSignalDetector()
        detector.set_source_workflow("OrderWorkflow")
        detector.set_file_path(Path("workflow.py"))
        detector.visit(tree)

        signals = detector.external_signals
        assert len(signals) == 1
        assert signals[0].node_id == "ext_sig_ship_order_3"

    def test_node_id_spaces_replaced_with_underscores(self) -> None:
        """Test node ID replaces spaces with underscores."""
        source = """
handle = workflow.get_external_workflow_handle("test-123")
await handle.signal("Ship Order Now", data)
"""
        tree = ast.parse(source)
        detector = ExternalSignalDetector()
        detector.set_source_workflow("OrderWorkflow")
        detector.set_file_path(Path("workflow.py"))
        detector.visit(tree)

        signals = detector.external_signals
        assert len(signals) == 1
        assert signals[0].node_id == "ext_sig_ship_order_now_3"

    def test_node_id_lowercase(self) -> None:
        """Test node ID is lowercase."""
        source = """
handle = workflow.get_external_workflow_handle("test-123")
await handle.signal("ShipOrder", data)
"""
        tree = ast.parse(source)
        detector = ExternalSignalDetector()
        detector.set_source_workflow("OrderWorkflow")
        detector.set_file_path(Path("workflow.py"))
        detector.visit(tree)

        signals = detector.external_signals
        assert len(signals) == 1
        assert signals[0].node_id == "ext_sig_shiporder_3"


class TestExternalSignalDetectorSourceWorkflowContext:
    """Test source workflow context tracking."""

    def test_source_workflow_context_stored(self) -> None:
        """Test source workflow is stored in ExternalSignalCall."""
        source = """
handle = workflow.get_external_workflow_handle("test-123")
await handle.signal("test_signal", data)
"""
        tree = ast.parse(source)
        detector = ExternalSignalDetector()
        detector.set_source_workflow("WorkflowA")
        detector.set_file_path(Path("workflow.py"))
        detector.visit(tree)

        signals = detector.external_signals
        assert len(signals) == 1
        assert signals[0].source_workflow == "WorkflowA"


class TestExternalSignalDetectorErrorHandling:
    """Test error handling for invalid signal patterns."""

    def test_invalid_signal_call_no_arguments(self) -> None:
        """Test error handling for .signal() with no arguments."""
        source = """
handle = workflow.get_external_workflow_handle("test-123")
await handle.signal()
"""
        tree = ast.parse(source)
        detector = ExternalSignalDetector()
        detector.set_source_workflow("OrderWorkflow")
        detector.set_file_path(Path("workflow.py"))

        with pytest.raises(WorkflowParseError) as exc_info:
            detector.visit(tree)

        error = exc_info.value
        assert error.line == 3
        assert "at least 1 argument" in error.message
        assert "signal_name" in error.suggestion

    def test_invalid_signal_call_non_string_signal_name(self) -> None:
        """Test error handling for .signal() with non-string signal name."""
        source = """
handle = workflow.get_external_workflow_handle("test-123")
await handle.signal(123, data)
"""
        tree = ast.parse(source)
        detector = ExternalSignalDetector()
        detector.set_source_workflow("OrderWorkflow")
        detector.set_file_path(Path("workflow.py"))

        with pytest.raises(WorkflowParseError) as exc_info:
            detector.visit(tree)

        error = exc_info.value
        assert error.line == 3
        assert "string literal" in error.message

    def test_signal_not_on_handle_ignored(self) -> None:
        """Test .signal() called on non-handle variable is ignored."""
        source = """
other_var = some_object()
await other_var.signal("test", data)
"""
        tree = ast.parse(source)
        detector = ExternalSignalDetector()
        detector.set_source_workflow("OrderWorkflow")
        detector.set_file_path(Path("workflow.py"))
        detector.visit(tree)

        signals = detector.external_signals
        assert len(signals) == 0
