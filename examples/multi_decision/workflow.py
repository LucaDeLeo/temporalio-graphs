"""Loan approval workflow demonstrating complex multi-decision support.

This example demonstrates a Temporal workflow with 3 independent decision points
creating 8 possible execution paths (2^3 = 8). The workflow models a loan approval
process with conditional checks for high-value loans, credit score requirements,
and existing loan verification.

Decision Points:
1. HighValue: True if loan amount exceeds $10,000 (requires manager review)
2. LowCredit: True if credit score is below 600 (requires collateral)
3. ExistingLoans: True if applicant has existing loans (requires debt ratio check)

This creates 8 execution paths:
- Path 1 (HV=yes, LC=yes, EL=yes): All checks (manager, collateral, debt ratio)
- Path 2 (HV=yes, LC=yes, EL=no): Manager review + collateral
- Path 3 (HV=yes, LC=no, EL=yes): Manager review + debt ratio check
- Path 4 (HV=yes, LC=no, EL=no): Manager review only
- Path 5 (HV=no, LC=yes, EL=yes): Collateral + debt ratio check
- Path 6 (HV=no, LC=yes, EL=no): Collateral only
- Path 7 (HV=no, LC=no, EL=yes): Debt ratio check only
- Path 8 (HV=no, LC=no, EL=no): Minimal checks (approve immediately)

Example usage (in actual Temporal client code):
    result = await client.execute_workflow(
        LoanApprovalWorkflow.run,
        amount=15000,
        credit_score=580,
        has_existing_loans=True,
        id="loan-application-001",
        task_queue="default",
    )
"""

from temporalio import workflow

from temporalio_graphs import to_decision


@workflow.defn
class LoanApprovalWorkflow:
    """Loan approval workflow with multiple independent decision points.

    This workflow demonstrates complex decision support in temporalio-graphs:
    - Sequential activities (validate_application, approve_loan)
    - Conditional activities (manager_review, require_collateral, debt_ratio_check)
    - Three independent decision points (HighValue, LowCredit, ExistingLoans)
    - Path permutations (8 total paths from 3 decisions)
    - Realistic business logic for loan approval process
    """

    @workflow.run
    async def run(
        self, amount: float, credit_score: int, has_existing_loans: bool
    ) -> str:
        """Execute the loan approval workflow with conditional branches.

        Args:
            amount: Loan amount in dollars (e.g., 15000.00)
            credit_score: Applicant's credit score (300-850)
            has_existing_loans: Whether applicant has existing loans

        Returns:
            Approval result message: "loan_approved" or "loan_denied"
        """
        # Activity 1: Always executed - validate the loan application
        await workflow.execute_activity(
            validate_application,
            args=[amount, credit_score],
            start_to_close_timeout=None,
        )

        # Decision 1: Check if loan amount is high value (>$10,000)
        if await to_decision(amount > 10000, "HighValue"):
            # Activity 2: Conditional - high-value loans require manager review
            await workflow.execute_activity(
                manager_review,
                args=[amount],
                start_to_close_timeout=None,
            )

        # Decision 2: Check if credit score is low (<600)
        if await to_decision(credit_score < 600, "LowCredit"):
            # Activity 3: Conditional - low credit requires collateral
            await workflow.execute_activity(
                require_collateral,
                args=[credit_score],
                start_to_close_timeout=None,
            )

        # Decision 3: Check if applicant has existing loans
        if await to_decision(has_existing_loans, "ExistingLoans"):
            # Activity 4: Conditional - existing loans require debt ratio check
            await workflow.execute_activity(
                debt_ratio_check,
                start_to_close_timeout=None,
            )

        # Activity 5: Always executed - final approval decision
        await workflow.execute_activity(
            approve_loan,
            args=[amount, credit_score, has_existing_loans],
            start_to_close_timeout=None,
        )

        return "loan_approved"


# Activity definitions (would normally be in a separate module)
# These are referenced in execute_activity() calls above


async def validate_application(amount: float, credit_score: int) -> bool:
    """Validate the loan application for completeness and basic criteria.

    This is a placeholder activity definition. In a real workflow, this would
    contain business logic for validating application data, checking format,
    and verifying basic eligibility requirements.

    Args:
        amount: Loan amount requested
        credit_score: Applicant's credit score

    Returns:
        True if application is valid, raises exception otherwise.
    """
    return True


async def manager_review(amount: float) -> bool:
    """Request manager approval for high-value loans.

    This activity only executes when loan amount exceeds $10,000. Represents
    manual review step for large loans requiring additional oversight.

    Args:
        amount: Loan amount requiring review

    Returns:
        True if manager approves, False otherwise.
    """
    return True


async def require_collateral(credit_score: int) -> bool:
    """Require collateral for applicants with low credit scores.

    This activity only executes when credit score is below 600. Represents
    process of documenting and verifying collateral to secure the loan.

    Args:
        credit_score: Applicant's credit score

    Returns:
        True if adequate collateral is provided, False otherwise.
    """
    return True


async def debt_ratio_check() -> bool:
    """Calculate and verify debt-to-income ratio for existing loan holders.

    This activity only executes when applicant has existing loans. Represents
    financial analysis to ensure new loan won't overburden the applicant.

    Returns:
        True if debt ratio is acceptable, False otherwise.
    """
    return True


async def approve_loan(
    amount: float, credit_score: int, has_existing_loans: bool
) -> str:
    """Make final approval decision based on all checks.

    This is a placeholder activity definition. Executes regardless of which
    conditional checks were performed. In a real workflow, this would finalize
    the loan approval and update systems.

    Args:
        amount: Loan amount
        credit_score: Applicant's credit score
        has_existing_loans: Whether applicant has existing loans

    Returns:
        Approval result with loan terms
    """
    return f"Approved loan for ${amount}"
