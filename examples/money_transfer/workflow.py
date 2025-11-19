"""MoneyTransfer workflow example demonstrating decision point support.

This example demonstrates a Temporal workflow with 2 decision points creating
4 possible execution paths. The workflow models an international money transfer
with conditional currency conversion and tax handling based on known TFN status.

Decision Points:
1. NeedToConvert: True if source and destination currencies differ
2. IsTFN_Known: True if recipient's tax file number is known

This creates 4 execution paths:
- Path 1 (Convert=true, TFN=true): Convert funds and notify ATO
- Path 2 (Convert=true, TFN=false): Convert funds and apply non-resident tax
- Path 3 (Convert=false, TFN=true): Skip conversion, notify ATO
- Path 4 (Convert=false, TFN=false): Skip conversion, apply non-resident tax

Example usage (in actual Temporal client code):
    result = await client.execute_workflow(
        MoneyTransferWorkflow.run,
        source_currency="GBP",
        dest_currency="AUD",
        tfn_known=True,
        id="transfer-001",
        task_queue="default",
    )
"""

from temporalio import workflow

from temporalio_graphs import to_decision


@workflow.defn
class MoneyTransferWorkflow:
    """International money transfer workflow with decision points.

    This workflow demonstrates the complete decision support in temporalio-graphs.
    It includes:
    - Sequential activities (Withdraw, Deposit)
    - Conditional activities (CurrencyConvert, NotifyAto, TakeNonResidentTax)
    - Two decision points (NeedToConvert, IsTFN_Known)
    - Reconverging branches (Deposit occurs regardless of path)
    """

    @workflow.run
    async def run(
        self, source_currency: str, dest_currency: str, tfn_known: bool
    ) -> str:
        """Execute the money transfer workflow with conditional branches.

        Args:
            source_currency: Source currency code (e.g., "GBP")
            dest_currency: Destination currency code (e.g., "AUD")
            tfn_known: Whether recipient's tax file number is known

        Returns:
            Completion message "transfer_complete"
        """
        # Activity 1: Always executed - withdraw funds from source
        await workflow.execute_activity(
            withdraw_funds,
            args=[source_currency, dest_currency],
            start_to_close_timeout=None,
        )

        # Decision 1: Check if currency conversion is needed
        if await to_decision(
            source_currency != dest_currency, "NeedToConvert"
        ):
            # Activity 2: Conditional - convert currency if needed
            await workflow.execute_activity(
                currency_convert,
                args=[source_currency, dest_currency],
                start_to_close_timeout=None,
            )

        # Decision 2: Check if TFN is known for tax purposes
        if await to_decision(tfn_known, "IsTFN_Known"):
            # Activity 3: True branch - notify ATO if TFN is known
            await workflow.execute_activity(
                notify_ato,
                start_to_close_timeout=None,
            )
        else:
            # Activity 4: False branch - apply non-resident tax if TFN unknown
            await workflow.execute_activity(
                take_non_resident_tax,
                start_to_close_timeout=None,
            )

        # Activity 5: Always executed - deposit funds to destination
        await workflow.execute_activity(
            deposit_funds,
            args=[dest_currency],
            start_to_close_timeout=None,
        )

        return "transfer_complete"


# Activity definitions (would normally be in a separate module)
# These are referenced in execute_activity() calls above


async def withdraw_funds(source_currency: str, dest_currency: str) -> bool:
    """Withdraw funds from source account.

    This is a placeholder activity definition. In a real workflow, this would
    contain the actual business logic for withdrawing funds.

    Args:
        source_currency: Source currency code
        dest_currency: Destination currency code

    Returns:
        True if withdrawal succeeds, False otherwise.
    """
    return True


async def currency_convert(source_currency: str, dest_currency: str) -> bool:
    """Convert funds from source currency to destination currency.

    This activity only executes when source_currency != dest_currency.

    Args:
        source_currency: Source currency code
        dest_currency: Destination currency code

    Returns:
        True if conversion succeeds, False otherwise.
    """
    return True


async def notify_ato() -> bool:
    """Notify Australian Tax Office (ATO) of transfer.

    This activity only executes when TFN (Tax File Number) is known.

    Returns:
        True if notification succeeds, False otherwise.
    """
    return True


async def take_non_resident_tax() -> bool:
    """Apply non-resident tax withholding.

    This activity only executes when TFN is unknown. Represents withholding
    tax applied to non-resident recipients.

    Returns:
        True if tax withholding succeeds, False otherwise.
    """
    return True


async def deposit_funds(dest_currency: str) -> bool:
    """Deposit funds to destination account.

    This is a placeholder activity definition. Executes regardless of whether
    currency conversion or tax handling occurred.

    Args:
        dest_currency: Destination currency code

    Returns:
        True if deposit succeeds, False otherwise.
    """
    return True
