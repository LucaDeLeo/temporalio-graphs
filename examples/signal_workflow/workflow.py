"""Approval workflow example demonstrating signal/wait condition support.

This example demonstrates a Temporal workflow with a wait condition creating
2 possible execution paths. The workflow models an approval request that waits
for a signal or times out after 24 hours.

Signal Points:
1. WaitForApproval: True if approval signal received before timeout, False if timeout

This creates 2 execution paths:
- Path 1 (Signaled): Request submitted → Approval received → Process approved
- Path 2 (Timeout): Request submitted → Timeout after 24h → Handle timeout

Example usage (in actual Temporal client code):
    # Start workflow
    handle = await client.start_workflow(
        ApprovalWorkflow.run,
        args=["request-001"],
        id="approval-001",
        task_queue="default",
    )

    # Send approval signal within 24 hours
    await handle.signal(ApprovalWorkflow.approve)

    # Or let it timeout
    result = await handle.result()
"""

from datetime import timedelta

from temporalio import workflow

from temporalio_graphs import wait_condition


@workflow.defn
class ApprovalWorkflow:
    """Approval request workflow with signal wait condition.

    This workflow demonstrates signal/wait condition support in temporalio-graphs.
    It includes:
    - Sequential activities (SubmitRequest before signal)
    - Wait condition with 24-hour timeout (WaitForApproval signal node)
    - Conditional activities (ProcessApproved vs HandleTimeout)
    - Reconverging to end (both paths complete the workflow)
    """

    def __init__(self) -> None:
        """Initialize workflow state for approval tracking."""
        self.approved = False

    @workflow.run
    async def run(self, request_id: str) -> str:
        """Execute the approval workflow with signal wait condition.

        Args:
            request_id: Unique identifier for the approval request

        Returns:
            "approved" if signal received, "timeout" if no approval within 24h
        """
        # Activity 1: Always executed - submit approval request
        await workflow.execute_activity(
            submit_request,
            args=[request_id],
            start_to_close_timeout=None,
        )

        # Signal Point: Wait for approval signal or timeout after 24 hours
        # This creates a signal node in the graph with two branches:
        # - "Signaled" branch (approved=True): ProcessApproved activity
        # - "Timeout" branch (approved=False): HandleTimeout activity
        if await wait_condition(
            lambda: self.approved,
            timedelta(hours=24),
            "WaitForApproval",
        ):
            # Activity 2: Signaled branch - process approved request
            await workflow.execute_activity(
                process_approved,
                args=[request_id],
                start_to_close_timeout=None,
            )
            return "approved"
        else:
            # Activity 3: Timeout branch - handle timeout
            await workflow.execute_activity(
                handle_timeout,
                args=[request_id],
                start_to_close_timeout=None,
            )
            return "timeout"

    @workflow.signal
    async def approve(self) -> None:
        """Signal handler to approve the request.

        When this signal is received, self.approved becomes True, causing
        wait_condition to complete and take the "Signaled" branch.
        """
        self.approved = True


# Activity definitions (would normally be in a separate module)
# These are referenced in execute_activity() calls above


async def submit_request(request_id: str) -> bool:
    """Submit approval request for processing.

    This is a placeholder activity definition. In a real workflow, this would
    contain the actual business logic for submitting the approval request.

    Args:
        request_id: Unique identifier for the approval request

    Returns:
        True if submission succeeds, False otherwise.
    """
    return True


async def process_approved(request_id: str) -> bool:
    """Process the approved request.

    This activity only executes when approval signal is received before timeout.

    Args:
        request_id: Unique identifier for the approval request

    Returns:
        True if processing succeeds, False otherwise.
    """
    return True


async def handle_timeout(request_id: str) -> bool:
    """Handle timeout when no approval received.

    This activity only executes when wait_condition times out after 24 hours
    without receiving the approval signal.

    Args:
        request_id: Unique identifier for the approval request

    Returns:
        True if timeout handling succeeds, False otherwise.
    """
    return True
