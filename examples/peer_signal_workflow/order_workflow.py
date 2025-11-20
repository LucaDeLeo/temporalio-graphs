r"""Order workflow example: Order processing that signals shipping workflow.

This workflow demonstrates peer-to-peer workflow signaling where one workflow
sends an external signal to another independent workflow.

The Order workflow:
1. Processes the order via activity
2. Sends external signal to Shipping workflow via get_external_workflow_handle
3. Completes order processing

This is visualized as:
- Trapezoid node for external signal: [/Signal 'ship_order' to shipping-{*}\]
- Dashed edge showing async signal flow: -.signal.->
- Orange/amber color styling distinguishing from activities
"""

from datetime import timedelta

from temporalio import workflow


@workflow.defn
class OrderWorkflow:
    """Order processing workflow that signals Shipping workflow.

    This workflow demonstrates the peer-to-peer signaling pattern where
    an Order workflow signals an independent Shipping workflow to begin
    shipment processing.

    External Signal:
    - Signal name: "ship_order"
    - Target workflow: shipping-{order_id}
    - Pattern: Peer-to-peer async communication (fire-and-forget)
    """

    @workflow.run
    async def run(self, order_id: str) -> str:
        """Execute order workflow.

        Args:
            order_id: Unique order identifier

        Returns:
            Order completion status message
        """
        # Activity 1: Process order
        await workflow.execute_activity(
            "process_order",
            args=[order_id],
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Send external signal to Shipping workflow
        # This creates a peer-to-peer async communication
        shipping_handle = workflow.get_external_workflow_handle(f"shipping-{order_id}")
        await shipping_handle.signal("ship_order", order_id)

        # Activity 2: Complete order processing
        await workflow.execute_activity(
            "complete_order",
            args=[order_id],
            start_to_close_timeout=timedelta(seconds=30),
        )

        return "order_complete"
