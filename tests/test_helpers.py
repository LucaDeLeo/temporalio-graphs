"""Unit tests for workflow helper functions.

Tests the passthrough behavior and async compatibility of helper functions
like to_decision() which serve as markers for static analysis.
"""

import asyncio
import inspect
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest

from temporalio_graphs.helpers import to_decision, wait_condition


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


class TestWaitConditionBehavior:
    """Test wait_condition() wrapper behavior and API."""

    @pytest.mark.asyncio
    async def test_wait_condition_returns_true_on_success(self) -> None:
        """Test that wait_condition() returns True when condition met before timeout."""
        # Mock workflow.wait_condition to return successfully (no exception)
        with patch("temporalio.workflow.wait_condition", new_callable=AsyncMock) as mock_wait:
            mock_wait.return_value = None  # Success case

            result = await wait_condition(
                lambda: True, timedelta(seconds=10), "TestSignal"
            )

            assert result is True
            # Verify workflow.wait_condition was called with correct args
            mock_wait.assert_called_once()
            call_args = mock_wait.call_args
            assert call_args.kwargs["timeout"] == timedelta(seconds=10)

    @pytest.mark.asyncio
    async def test_wait_condition_returns_false_on_timeout(self) -> None:
        """Test that wait_condition() returns False when timeout occurs."""
        # Mock workflow.wait_condition to raise TimeoutError
        with patch("temporalio.workflow.wait_condition", new_callable=AsyncMock) as mock_wait:
            mock_wait.side_effect = asyncio.TimeoutError()

            result = await wait_condition(
                lambda: False, timedelta(seconds=1), "TestSignal"
            )

            assert result is False
            mock_wait.assert_called_once()

    @pytest.mark.asyncio
    async def test_wait_condition_is_async_function(self) -> None:
        """Test that wait_condition() is an async function."""
        assert inspect.iscoroutinefunction(wait_condition)

    @pytest.mark.asyncio
    async def test_wait_condition_has_correct_signature(self) -> None:
        """Test that wait_condition() has expected 3 parameters with correct names."""
        sig = inspect.signature(wait_condition)
        params = list(sig.parameters.keys())

        assert len(params) == 3
        assert params[0] == "condition_check"
        assert params[1] == "timeout"
        assert params[2] == "name"

    @pytest.mark.asyncio
    async def test_wait_condition_has_docstring(self) -> None:
        """Test that wait_condition() has comprehensive docstring."""
        assert wait_condition.__doc__ is not None
        assert len(wait_condition.__doc__) > 100

        # Check for required docstring sections
        docstring = wait_condition.__doc__
        assert "Args:" in docstring
        assert "Returns:" in docstring
        assert "Raises:" in docstring
        assert "Example:" in docstring
        assert "Note:" in docstring

    @pytest.mark.asyncio
    async def test_wait_condition_has_correct_type_hints(self) -> None:
        """Test that wait_condition() has complete type hints."""
        sig = inspect.signature(wait_condition)

        # Check parameter type hints
        assert sig.parameters["condition_check"].annotation != inspect.Parameter.empty
        assert sig.parameters["timeout"].annotation is timedelta
        assert sig.parameters["name"].annotation is str

        # Check return type hint
        assert sig.return_annotation is bool

    @pytest.mark.asyncio
    async def test_wait_condition_calls_workflow_wait_condition(self) -> None:
        """Test that wait_condition() calls underlying workflow.wait_condition()."""

        def condition() -> bool:
            return True

        timeout_val = timedelta(seconds=30)

        with patch("temporalio.workflow.wait_condition", new_callable=AsyncMock) as mock_wait:
            mock_wait.return_value = None

            await wait_condition(condition, timeout_val, "TestName")

            # Verify called exactly once
            mock_wait.assert_called_once()

            # Verify arguments (condition_check is first arg, timeout is kwarg)
            call_args = mock_wait.call_args
            assert call_args.args[0] == condition
            assert call_args.kwargs["timeout"] == timeout_val

    @pytest.mark.asyncio
    async def test_wait_condition_no_side_effects(self) -> None:
        """Test that wait_condition() has no side effects - pure function."""

        def condition() -> bool:
            return True

        timeout_val = timedelta(seconds=5)
        name = "TestSignal"

        with patch("temporalio.workflow.wait_condition", new_callable=AsyncMock) as mock_wait:
            mock_wait.return_value = None

            # Call multiple times with same args
            result1 = await wait_condition(condition, timeout_val, name)
            result2 = await wait_condition(condition, timeout_val, name)
            result3 = await wait_condition(condition, timeout_val, name)

            assert result1 is True
            assert result2 is True
            assert result3 is True
            assert mock_wait.call_count == 3

    @pytest.mark.asyncio
    async def test_wait_condition_with_various_names(self) -> None:
        """Test that wait_condition() accepts various string names."""
        with patch("temporalio.workflow.wait_condition", new_callable=AsyncMock) as mock_wait:
            mock_wait.return_value = None

            # Valid string literal names should all work
            result1 = await wait_condition(
                lambda: True, timedelta(seconds=1), "WaitForApproval"
            )
            result2 = await wait_condition(
                lambda: True, timedelta(seconds=1), "PaymentReceived"
            )
            result3 = await wait_condition(
                lambda: True, timedelta(seconds=1), "Signal_With_Underscores"
            )

            assert result1 is True
            assert result2 is True
            assert result3 is True

    @pytest.mark.asyncio
    async def test_wait_condition_with_different_timeouts(self) -> None:
        """Test that wait_condition() handles different timeout values."""
        with patch("temporalio.workflow.wait_condition", new_callable=AsyncMock) as mock_wait:
            mock_wait.return_value = None

            # Test various timeout formats
            await wait_condition(lambda: True, timedelta(seconds=10), "Test1")
            await wait_condition(lambda: True, timedelta(minutes=5), "Test2")
            await wait_condition(lambda: True, timedelta(hours=24), "Test3")

            assert mock_wait.call_count == 3

    @pytest.mark.asyncio
    async def test_wait_condition_return_type_is_bool(self) -> None:
        """Test that wait_condition() always returns bool type."""
        with patch("temporalio.workflow.wait_condition", new_callable=AsyncMock) as mock_wait:
            # Test success case
            mock_wait.return_value = None
            result_true = await wait_condition(lambda: True, timedelta(seconds=1), "Test")
            assert isinstance(result_true, bool)
            assert result_true is True

            # Test timeout case
            mock_wait.side_effect = asyncio.TimeoutError()
            result_false = await wait_condition(lambda: False, timedelta(seconds=1), "Test")
            assert isinstance(result_false, bool)
            assert result_false is False


class TestWaitConditionPublicAPI:
    """Test wait_condition() public API export."""

    @pytest.mark.asyncio
    async def test_wait_condition_importable_from_public_api(self) -> None:
        """Test that wait_condition can be imported from temporalio_graphs."""
        from temporalio_graphs import wait_condition as imported_wait_condition

        assert imported_wait_condition.__name__ == "wait_condition"
        assert callable(imported_wait_condition)
        assert inspect.iscoroutinefunction(imported_wait_condition)
