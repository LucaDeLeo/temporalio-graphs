"""Workflow with multiple signal handlers for the same signal.

Test fixture for integration tests - demonstrates multiple handler detection.
"""

from datetime import timedelta

from temporalio import workflow


@workflow.defn
class MultiHandlerWorkflowA:
    """First workflow that handles the shared_signal."""

    def __init__(self) -> None:
        """Initialize workflow state."""
        self.received = False

    @workflow.run
    async def run(self, handler_id: str) -> str:
        """Execute handler A workflow.

        Args:
            handler_id: Unique handler identifier

        Returns:
            Processing completion status message
        """
        # Wait for shared_signal
        await workflow.wait_condition(
            lambda: self.received,
            timeout=timedelta(hours=24),
        )

        # Activity: Process in A
        await workflow.execute_activity(
            "process_in_a",
            args=[handler_id],
            start_to_close_timeout=timedelta(minutes=5),
        )

        return "processed_a"

    @workflow.signal
    async def shared_signal(self, data: str) -> None:
        """Receive shared_signal.

        Args:
            data: Signal data
        """
        self.received = True


@workflow.defn
class MultiHandlerWorkflowB:
    """Second workflow that handles the same shared_signal."""

    def __init__(self) -> None:
        """Initialize workflow state."""
        self.received = False

    @workflow.run
    async def run(self, handler_id: str) -> str:
        """Execute handler B workflow.

        Args:
            handler_id: Unique handler identifier

        Returns:
            Processing completion status message
        """
        # Wait for shared_signal
        await workflow.wait_condition(
            lambda: self.received,
            timeout=timedelta(hours=24),
        )

        # Activity: Process in B
        await workflow.execute_activity(
            "process_in_b",
            args=[handler_id],
            start_to_close_timeout=timedelta(minutes=5),
        )

        return "processed_b"

    @workflow.signal
    async def shared_signal(self, data: str) -> None:
        """Receive shared_signal (same name as in WorkflowA).

        Args:
            data: Signal data
        """
        self.received = True
