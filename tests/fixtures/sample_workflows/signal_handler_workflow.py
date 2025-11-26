"""Workflow with @workflow.signal handlers for analyzer integration testing.

This fixture workflow demonstrates signal handlers that can receive external signals
from other workflows. Used for testing Story 8.2: WorkflowMetadata signal_handlers
field population.
"""

from datetime import timedelta

from temporalio import workflow


@workflow.defn
class ShippingWorkflow:
    """Workflow that receives signals from external workflows.

    This workflow has multiple @workflow.signal handlers to test
    signal handler detection and metadata extraction.
    """

    def __init__(self) -> None:
        """Initialize workflow state."""
        self.should_ship = False
        self.order_id: str | None = None
        self.cancelled = False

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
            lambda: self.should_ship or self.cancelled,
            timeout=timedelta(hours=24),
        )

        if self.cancelled:
            return "cancelled"

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

    @workflow.signal(name="cancel_shipment")
    async def cancel(self) -> None:
        """Receive cancel_shipment signal to cancel this shipment.

        This handler uses explicit name= argument to demonstrate
        that signal_name differs from method_name.
        """
        self.cancelled = True
