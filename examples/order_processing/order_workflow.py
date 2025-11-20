"""
Sample order processing workflow to test temporalio-graphs library.
Demonstrates decision nodes, signal handling, and activity execution.
"""

from datetime import timedelta
from temporalio import workflow
from temporalio_graphs import to_decision, wait_condition


# Activity stubs (these would be actual activities in a real workflow)
async def validate_order(order_id: str) -> bool:
    """Validate the order details."""
    pass


async def check_inventory(order_id: str) -> bool:
    """Check if items are in stock."""
    pass


async def reserve_inventory(order_id: str) -> None:
    """Reserve items from inventory."""
    pass


async def notify_backorder(order_id: str) -> None:
    """Notify customer about backorder."""
    pass


async def process_payment(order_id: str, amount: float) -> None:
    """Process payment for the order."""
    pass


async def require_manual_approval(order_id: str) -> None:
    """Require manual approval for high-value orders."""
    pass


async def ship_order(order_id: str) -> None:
    """Ship the order to customer."""
    pass


async def cancel_order(order_id: str) -> None:
    """Cancel the order."""
    pass


@workflow.defn
class OrderWorkflow:
    """
    Order processing workflow with decision points and signal handling.

    This workflow demonstrates:
    - Sequential activities
    - Decision nodes (inventory check, high-value approval)
    - Signal nodes (payment confirmation)
    """

    def __init__(self) -> None:
        self.payment_confirmed = False

    @workflow.run
    async def run(self, order_id: str, order_amount: float) -> str:
        """
        Process an order through validation, inventory, payment, and shipping.

        Args:
            order_id: Unique order identifier
            order_amount: Total order amount in dollars

        Returns:
            Order status: "shipped", "cancelled", or "pending_approval"
        """
        # Step 1: Validate order
        await workflow.execute_activity(
            validate_order,
            order_id,
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Step 2: Check inventory (decision point 1)
        if await to_decision(True, "InventoryAvailable"):
            # Items in stock - reserve them
            await workflow.execute_activity(
                reserve_inventory,
                order_id,
                start_to_close_timeout=timedelta(seconds=30),
            )
        else:
            # Items not in stock - notify and backorder
            await workflow.execute_activity(
                notify_backorder,
                order_id,
                start_to_close_timeout=timedelta(seconds=30),
            )
            return "backordered"

        # Step 3: Check if high-value order (decision point 2)
        if await to_decision(order_amount > 1000, "HighValueOrder"):
            # Require manual approval for high-value orders
            await workflow.execute_activity(
                require_manual_approval,
                order_id,
                start_to_close_timeout=timedelta(seconds=30),
            )

        # Step 4: Wait for payment confirmation (signal with timeout)
        if await wait_condition(
            lambda: self.payment_confirmed,
            timedelta(hours=24),
            "WaitForPayment"
        ):
            # Payment confirmed - process it
            await workflow.execute_activity(
                process_payment,
                order_id,
                order_amount,
                start_to_close_timeout=timedelta(seconds=30),
            )

            # Ship the order
            await workflow.execute_activity(
                ship_order,
                order_id,
                start_to_close_timeout=timedelta(seconds=30),
            )
            return "shipped"
        else:
            # Payment timeout - cancel order
            await workflow.execute_activity(
                cancel_order,
                order_id,
                start_to_close_timeout=timedelta(seconds=30),
            )
            return "cancelled"

    @workflow.signal
    async def confirm_payment(self) -> None:
        """Signal to confirm payment has been received."""
        self.payment_confirmed = True
