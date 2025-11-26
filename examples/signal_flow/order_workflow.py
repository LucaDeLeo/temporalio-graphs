"""Order workflow that sends external signals to shipping workflow.

This example demonstrates the entry point of a signal flow chain:
Order -> Shipping -> Notification

The OrderWorkflow:
1. Processes an order (process_order activity)
2. Sends "ship_order" signal to ShippingWorkflow
3. Completes the order (complete_order activity)
"""

from datetime import timedelta

from temporalio import workflow


@workflow.defn
class OrderWorkflow:
    """Workflow that processes orders and signals shipping.

    After processing, signals the shipping workflow to dispatch the order.
    This is the entry point for the three-workflow signal chain example.
    """

    @workflow.run
    async def run(self, order_id: str) -> str:
        """Execute order workflow.

        Args:
            order_id: Unique order identifier

        Returns:
            Order completion status message
        """
        # Activity: Process order
        await workflow.execute_activity(
            "process_order",
            args=[order_id],
            start_to_close_timeout=timedelta(minutes=5),
        )

        # External signal: Notify shipping workflow to ship the order
        shipping_handle = workflow.get_external_workflow_handle(
            "ShippingWorkflow",
            workflow_id=f"shipping-{order_id}",
        )
        await shipping_handle.signal("ship_order", order_id)

        # Activity: Complete order
        await workflow.execute_activity(
            "complete_order",
            args=[order_id],
            start_to_close_timeout=timedelta(minutes=5),
        )

        return "completed"
