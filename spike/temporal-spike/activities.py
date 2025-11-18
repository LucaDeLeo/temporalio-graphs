"""Activity definitions for spike test workflow."""
from temporalio import activity


@activity.defn(name="withdraw")
async def withdraw(amount: int) -> str:
    """Withdraw money from account."""
    return f"Withdrew ${amount}"


@activity.defn(name="approve")
async def approve(amount: int) -> str:
    """Approve transaction."""
    return f"Approved ${amount}"


@activity.defn(name="deposit")
async def deposit(amount: int) -> str:
    """Deposit money to account."""
    return f"Deposited ${amount}"
