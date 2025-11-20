"""Shipping workflow example: Shipping processing that receives signal from order workflow.

This workflow demonstrates the receiving side of peer-to-peer workflow signaling
where a Shipping workflow waits for and receives an external signal from an
Order workflow.

The Shipping workflow:
1. Waits for ship_order signal from Order workflow via wait_condition
2. Receives signal via @workflow.signal decorated handler
3. Ships package via activity

This complements the Order workflow example showing both sides of the
peer-to-peer signaling pattern.
"""

from datetime import timedelta

from temporalio import workflow


@workflow.defn
class ShippingWorkflow:
    """Shipping workflow that receives signal from Order workflow.

    This workflow demonstrates the receiving side of the peer-to-peer
    signaling pattern where a Shipping workflow waits for an Order
    workflow to signal when shipment should begin.

    Signal Handler:
    - Signal name: "ship_order"
    - Sender workflow: Order workflow (any instance)
    - Pattern: Peer-to-peer async communication (receive and process)
    """

    def __init__(self) -> None:
        """Initialize shipping workflow state."""
        self.should_ship = False
        self.order_id: str | None = None

    @workflow.run
    async def run(self, shipping_id: str) -> str:
        """Execute shipping workflow.

        Args:
            shipping_id: Unique shipping identifier (typically shipping-{order_id})

        Returns:
            Shipment completion status message
        """
        # Wait for ship_order signal from Order workflow
        # This creates an internal signal/wait condition node
        await workflow.wait_condition(
            lambda: self.should_ship,
            timeout=timedelta(hours=24),
        )

        # Activity: Ship package
        await workflow.execute_activity(
            "ship_package",
            args=[self.order_id],
            start_to_close_timeout=timedelta(minutes=5),
        )

        return "shipped"

    @workflow.signal
    async def ship_order(self, order_id: str) -> None:
        """Receive ship_order signal from Order workflow.

        This signal handler is triggered when the Order workflow sends
        the ship_order signal. It sets the condition that wait_condition
        is waiting for.

        Args:
            order_id: Order identifier to ship
        """
        self.should_ship = True
        self.order_id = order_id
