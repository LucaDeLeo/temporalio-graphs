"""Notification workflow that receives signals from shipping workflow.

This example demonstrates the end of a signal flow chain:
Order -> Shipping -> Notification

The NotificationWorkflow:
1. Has a signal handler for "notify_shipped" from ShippingWorkflow
2. Sends a notification (send_notification activity)
"""

from datetime import timedelta

from temporalio import workflow


@workflow.defn
class NotificationWorkflow:
    """Workflow that receives signals and sends notifications.

    Waits for notify_shipped signal from shipping workflow before sending.
    """

    def __init__(self) -> None:
        """Initialize workflow state."""
        self.should_notify = False
        self.order_id: str | None = None

    @workflow.run
    async def run(self, notification_id: str) -> str:
        """Execute notification workflow.

        Args:
            notification_id: Unique notification identifier

        Returns:
            Notification completion status message
        """
        # Wait for notify_shipped signal
        await workflow.wait_condition(
            lambda: self.should_notify,
            timeout=timedelta(hours=24),
        )

        # Activity: Send notification
        await workflow.execute_activity(
            "send_notification",
            args=[self.order_id],
            start_to_close_timeout=timedelta(minutes=5),
        )

        return "notified"

    @workflow.signal
    async def notify_shipped(self, order_id: str) -> None:
        """Receive notify_shipped signal from Shipping workflow.

        Args:
            order_id: Order identifier that was shipped
        """
        self.should_notify = True
        self.order_id = order_id
