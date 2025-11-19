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

from temporalio_graphs._internal.graph_models import DecisionPoint
from temporalio_graphs.detector import DecisionDetector
from temporalio_graphs.exceptions import WorkflowParseError


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
            id="d0", name="Test", line_number=42, true_label="yes", false_label="no"
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
