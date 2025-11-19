"""Child workflow example: Payment processing with 3D Secure check.

This workflow demonstrates a child workflow with one decision point
(3D Secure authentication requirement).
"""

from datetime import timedelta

from temporalio import workflow

from temporalio_graphs import to_decision


@workflow.defn
class PaymentWorkflow:
    """Payment processing workflow with 3DS authentication check.

    Decision points:
    - Requires3DS: If payment requires 3D Secure authentication

    This creates 2 execution paths:
    - Path 1: Standard payment (no 3DS)
    - Path 2: Secure payment (with 3DS verification)

    When called from OrderWorkflow (which has 1 decision), the combined
    inline mode visualization shows 2 × 2 = 4 total end-to-end paths.
    """

    @workflow.run
    async def run(self, amount: float, customer_id: str) -> str:
        """Execute payment workflow.

        Args:
            amount: Payment amount in dollars
            customer_id: Customer identifier

        Returns:
            Payment confirmation ID
        """
        # Activity 1: Process payment
        payment_id = await workflow.execute_activity(
            "process_payment",
            args=[amount, customer_id],
            start_to_close_timeout=timedelta(seconds=60),
        )

        # Decision: 3DS authentication required for international or high-value
        requires_3ds = await to_decision(
            amount > 5000,
            name="Requires3DS"
        )

        if requires_3ds:
            # Activity 2: Verify 3D Secure authentication
            await workflow.execute_activity(
                "verify_3ds",
                args=[payment_id, customer_id],
                start_to_close_timeout=timedelta(seconds=120),
            )

        return payment_id
