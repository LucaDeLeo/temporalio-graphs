"""Workflow helper functions for marking decision points and wait conditions.

This module provides helper functions that workflow developers use to mark
important control flow points in their Temporal workflows. These helpers serve
as markers for static analysis while remaining transparent during workflow execution.

Key helper functions:
- to_decision(): Marks a boolean expression as a decision point for branching
- wait_condition(): Marks a wait condition for signal-based branching (Epic 4)

Example:
    >>> from temporalio_graphs import to_decision
    >>> if await to_decision(amount > 1000, "HighValue"):
    ...     # This path is marked as a decision node in generated graphs
    ...     pass
"""

from collections.abc import Callable
from datetime import timedelta


async def to_decision(result: bool, name: str) -> bool:
    """Mark a boolean expression as a decision point in workflow execution.

    This helper function is a transparent passthrough that serves as a marker
    for static analysis. At runtime, it returns the input boolean value unchanged,
    enabling the graph generation library to identify decision points in workflow
    code and generate complete execution path diagrams.

    The function is designed for use in conditional statements within Temporal
    workflows. It has zero runtime overhead and no side effects - it simply
    returns the input value unchanged.

    Args:
        result: Boolean expression value determining the decision outcome.
            This can be any boolean value or expression that evaluates to bool,
            such as: amount > 1000, status == "approved", (a and b), etc.
        name: String literal identifier for this decision point in the graph.
            This name appears as a decision node label in generated diagrams.
            IMPORTANT: The name MUST be a string literal (not a variable or
            f-string) for static analysis to extract it from the AST.
            Examples of valid names: "HighValue", "NeedsApproval", "IsUrgent"
            Examples of invalid patterns: f"Check_{item}", name_var, etc.

    Returns:
        The input boolean value unchanged (transparent passthrough).

    Example:
        Use in if statements to mark decision branches:

        >>> if await to_decision(amount > 1000, "HighValue"):
        ...     await workflow.execute_activity(special_handling, amount)
        ... else:
        ...     await workflow.execute_activity(normal_handling, amount)

        Use with assignment to make decision logic explicit:

        >>> needs_approval = await to_decision(
        ...     amount > 5000 and department == "procurement",
        ...     "RequiresApproval"
        ... )
        >>> if needs_approval:
        ...     await workflow.execute_activity(request_approval)

    Note:
        The "name" parameter must be a string literal for the static analysis
        to work correctly. Do not use variables or f-strings for the name.
        If you need dynamic names, see Epic 4 documentation for signal-based
        branching alternatives.

        At runtime, this function has negligible cost:
        - Execution time: < 1 microsecond (just a return statement)
        - No memory allocation or object creation
        - No garbage collection pressure
        - No impact on workflow performance

        The static analysis that uses this function is performed during
        graph generation (before workflow execution), not at runtime.
    """
    return result


async def wait_condition(
    condition_check: Callable[[], bool],
    timeout: timedelta,
    name: str,
) -> bool:
    """Mark a wait condition as a signal node in the workflow graph.

    This function wraps Temporal's workflow.wait_condition() to enable static
    analysis detection of signal points. At runtime, it behaves identically to
    workflow.wait_condition() - waiting for the condition or timeout - but
    returns a boolean instead of raising TimeoutError.

    The function is designed for use in Temporal workflows where you need to wait
    for a condition to become true (typically set by a signal). It serves as both
    a functional wrapper and a static analysis marker for graph generation.

    Args:
        condition_check: Callable that returns True when condition is met.
            Typically a lambda checking workflow state. Must be a no-argument
            callable returning bool. Example: lambda: self.approved
        timeout: Maximum duration to wait before timing out. Uses Python's
            timedelta for type safety and clarity. Example: timedelta(hours=24)
        name: Human-readable name for the signal node in the graph.
            IMPORTANT: The name MUST be a string literal (not a variable or
            f-string) for static analysis to extract it from the AST.
            Examples of valid names: "WaitForApproval", "PaymentReceived"
            Examples of invalid patterns: f"Wait_{item}", name_var, etc.

    Returns:
        True if condition was met before timeout, False if timeout occurred.

    Raises:
        TemporalError: If called outside workflow context.

    Example:
        Use in workflows to wait for signals with timeout:

        >>> @workflow.defn
        >>> class ApprovalWorkflow:
        ...     def __init__(self) -> None:
        ...         self.approved = False
        ...
        ...     @workflow.run
        ...     async def run(self) -> str:
        ...         # Wait up to 24 hours for approval signal
        ...         result = await wait_condition(
        ...             lambda: self.approved,
        ...             timedelta(hours=24),
        ...             "WaitForApproval"
        ...         )
        ...
        ...         if result:
        ...             return "approved"
        ...         else:
        ...             return "timeout"
        ...
        ...     @workflow.signal
        ...     async def approve(self) -> None:
        ...         self.approved = True

    Note:
        - Must be called with `await` in async workflows
        - Static analysis detects this call and creates signal node
        - Graph will show two branches: "Signaled" and "Timeout"
        - The "name" parameter must be a string literal for static analysis
        - At runtime, catches TimeoutError and returns False for timeout
        - Returns True when condition becomes true before timeout
        - No side effects or state changes beyond calling SDK function

        The static analysis that uses this function is performed during
        graph generation (before workflow execution), not at runtime.
    """
    import asyncio

    from temporalio import workflow

    try:
        await workflow.wait_condition(condition_check, timeout=timeout)
        return True
    except asyncio.TimeoutError:
        return False
