"""Order workflow that sends external signals to shipping workflow.

This fixture workflow demonstrates external signal sending that can be
resolved to a target workflow's signal handler. Used for testing
Story 8-9: analyze_signal_graph() public API.
"""

from datetime import timedelta

from temporalio import workflow


@workflow.defn
class OrderWorkflow:
    """Workflow that processes orders and signals shipping.

    After processing, signals the shipping workflow to dispatch the order.
    """

    @workflow.run
    async def run(self, order_id: str) -> str:
        """Execute order workflow.

        Args:
            order_id: Unique order identifier

        Returns:
            Order completion status message
        """
        # Activity: Validate order
        await workflow.execute_activity(
            "validate_order",
            args=[order_id],
            start_to_close_timeout=timedelta(minutes=5),
        )

        # Activity: Process payment
        await workflow.execute_activity(
            "process_payment",
            args=[order_id],
            start_to_close_timeout=timedelta(minutes=10),
        )

        # External signal: Notify shipping workflow to ship the order
        shipping_handle = workflow.get_external_workflow_handle(
            "ShippingWorkflow",
            workflow_id=f"shipping-{order_id}",
        )
        await shipping_handle.signal("ship_order", order_id)

        return "completed"
