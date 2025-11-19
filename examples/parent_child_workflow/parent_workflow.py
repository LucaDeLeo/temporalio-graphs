"""Parent workflow example: Order processing with payment child workflow.

This workflow demonstrates parent-child workflow relationships with one decision
point in the parent workflow (high-value order check).
"""

from datetime import timedelta

from temporalio import workflow

from temporalio_graphs import to_decision

# Import child workflow
with workflow.unsafe.imports_passed_through():
    from examples.parent_child_workflow.child_workflow import PaymentWorkflow


@workflow.defn
class OrderWorkflow:
    """Order processing workflow that calls PaymentWorkflow as child.

    Decision points:
    - HighValue: If order value > $10,000, require manager approval

    This creates 2 execution paths in reference mode:
    - Path 1: Low value order (no manager approval)
    - Path 2: High value order (with manager approval)

    In inline mode with PaymentWorkflow (which has 1 decision), this creates
    2 × 2 = 4 total end-to-end paths.
    """

    @workflow.run
    async def run(self, order_amount: float, customer_id: str) -> str:
        """Execute order workflow.

        Args:
            order_amount: Order total in dollars
            customer_id: Customer identifier

        Returns:
            Order confirmation message
        """
        # Activity 1: Validate order
        order_id = await workflow.execute_activity(
            "validate_order",
            args=[order_amount, customer_id],
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Decision: High value order check
        is_high_value = await to_decision(
            order_amount > 10000,
            name="HighValue"
        )

        if is_high_value:
            # Activity 2: Require manager approval for high-value orders
            await workflow.execute_activity(
                "manager_approval",
                args=[order_id, order_amount],
                start_to_close_timeout=timedelta(seconds=300),
            )

        # Child workflow: Process payment
        payment_result = await workflow.execute_child_workflow(
            PaymentWorkflow,
            args=[order_amount, customer_id],
            id=f"payment-{order_id}",
        )

        # Activity 3: Send confirmation
        await workflow.execute_activity(
            "send_confirmation",
            args=[order_id, customer_id, payment_result],
            start_to_close_timeout=timedelta(seconds=30),
        )

        return f"Order {order_id} completed with payment {payment_result}"
