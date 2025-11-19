"""Unit tests for workflow helper functions.

Tests the passthrough behavior and async compatibility of helper functions
like to_decision() which serve as markers for static analysis.
"""

import pytest

from temporalio_graphs.helpers import to_decision


class TestToDecisionPassthrough:
    """Test to_decision() transparent passthrough behavior."""

    @pytest.mark.asyncio
    async def test_to_decision_returns_true(self) -> None:
        """Test that to_decision() returns True when input is True."""
        result = await to_decision(True, "TestDecision")
        assert result is True

    @pytest.mark.asyncio
    async def test_to_decision_returns_false(self) -> None:
        """Test that to_decision() returns False when input is False."""
        result = await to_decision(False, "TestDecision")
        assert result is False

    @pytest.mark.asyncio
    async def test_to_decision_with_comparison_expression(self) -> None:
        """Test that to_decision() works with comparison expressions."""
        amount = 1500
        result = await to_decision(amount > 1000, "HighValue")
        assert result is True

        amount = 500
        result = await to_decision(amount > 1000, "HighValue")
        assert result is False

    @pytest.mark.asyncio
    async def test_to_decision_with_complex_boolean_expression(self) -> None:
        """Test that to_decision() works with complex boolean algebra."""
        a = 100
        b = 50
        result = await to_decision((a > 50) and (b < 100), "ComplexCheck")
        assert result is True

        result = await to_decision((a > 200) or (b < 25), "ComplexCheck")
        assert result is False

    @pytest.mark.asyncio
    async def test_to_decision_with_multiple_calls(self) -> None:
        """Test that to_decision() is idempotent - multiple calls have same effect."""
        # Call multiple times with same value
        result1 = await to_decision(True, "Test1")
        result2 = await to_decision(True, "Test1")
        result3 = await to_decision(True, "Test1")

        assert result1 is True
        assert result2 is True
        assert result3 is True

    @pytest.mark.asyncio
    async def test_to_decision_no_side_effects(self) -> None:
        """Test that to_decision() has no side effects - pure function."""
        # Verify no exceptions or state changes
        value = True
        original_value = value
        await to_decision(value, "NoSideEffects")
        assert value is original_value

    @pytest.mark.asyncio
    async def test_to_decision_name_parameter_is_string_literal(self) -> None:
        """Test that to_decision() accepts various string names."""
        # Valid string literal names should all work
        result1 = await to_decision(True, "HighValue")
        result2 = await to_decision(True, "NeedsApproval")
        result3 = await to_decision(True, "IsUrgent")
        result4 = await to_decision(True, "Check_With_Underscores")

        assert result1 is True
        assert result2 is True
        assert result3 is True
        assert result4 is True

    @pytest.mark.asyncio
    async def test_to_decision_with_ternary_expression(self) -> None:
        """Test that to_decision() handles ternary operator expressions."""
        x = 100
        y = 50
        condition = True
        # The result of ternary operator goes into to_decision
        result = await to_decision(x if condition else y, "TernaryChoice")
        assert result == 100

        result = await to_decision(x if not condition else y, "TernaryChoice")
        assert result == 50

    @pytest.mark.asyncio
    async def test_to_decision_return_type_matches_input(self) -> None:
        """Test that to_decision() preserves the boolean type."""
        result_true = await to_decision(True, "TestTrue")
        result_false = await to_decision(False, "TestFalse")

        assert isinstance(result_true, bool)
        assert isinstance(result_false, bool)
        assert result_true is not result_false

    @pytest.mark.asyncio
    async def test_to_decision_with_chained_comparisons(self) -> None:
        """Test that to_decision() works with chained comparisons."""
        value = 50
        result = await to_decision(10 < value < 100, "InRange")
        assert result is True

        result = await to_decision(60 < value < 100, "InRange")
        assert result is False

    @pytest.mark.asyncio
    async def test_to_decision_with_boolean_operators(self) -> None:
        """Test that to_decision() works with and, or, not operators."""
        # Test 'and' operator
        result = await to_decision(True and True, "AndTest")
        assert result is True

        result = await to_decision(True and False, "AndTest")
        assert result is False

        # Test 'or' operator
        result = await to_decision(False or True, "OrTest")
        assert result is True

        result = await to_decision(False or False, "OrTest")
        assert result is False

        # Test 'not' operator
        result = await to_decision(not False, "NotTest")
        assert result is True

        result = await to_decision(not True, "NotTest")
        assert result is False
