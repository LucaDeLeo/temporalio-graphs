"""Shipping workflow that receives signals from order workflow.

This fixture workflow demonstrates signal handlers that receive signals
from the order workflow. Used for testing Story 8-9: analyze_signal_graph()
public API for cross-workflow signal visualization.
"""

from datetime import timedelta

from temporalio import workflow


@workflow.defn
class ShippingWorkflow:
    """Workflow that receives signals and dispatches shipments.

    Waits for ship_order signal from order workflow before processing.
    """

    def __init__(self) -> None:
        """Initialize workflow state."""
        self.should_ship = False
        self.order_id: str | None = None

    @workflow.run
    async def run(self, shipping_id: str) -> str:
        """Execute shipping workflow.

        Args:
            shipping_id: Unique shipping identifier

        Returns:
            Shipment completion status message
        """
        # Wait for ship_order signal
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

        Args:
            order_id: Order identifier to ship
        """
        self.should_ship = True
        self.order_id = order_id
