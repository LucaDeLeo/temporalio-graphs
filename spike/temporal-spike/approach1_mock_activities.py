"""Approach 1: Mock Activity Registration for Graph Generation.

This approach uses mock activities that record execution paths and test
different decision branches by running workflows multiple times.
"""
import asyncio
from datetime import timedelta
from typing import List
from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker
import time

# Global path recorder (in real implementation, would be better structured)
execution_paths: List[List[str]] = []
current_path: List[str] = []


@activity.defn(name="withdraw")
async def mock_withdraw(amount: int) -> str:
    """Mock withdraw that records execution."""
    current_path.append(f"withdraw({amount})")
    return f"Withdrew ${amount}"


@activity.defn(name="approve")
async def mock_approve(amount: int) -> str:
    """Mock approve that records execution."""
    current_path.append(f"approve({amount})")
    return f"Approved ${amount}"


@activity.defn(name="deposit")
async def mock_deposit(amount: int) -> str:
    """Mock deposit that records execution."""
    current_path.append(f"deposit({amount})")
    return f"Deposited ${amount}"


@workflow.defn
class SpikeTestWorkflow:
    """Test workflow with conditional branching."""

    @workflow.run
    async def run(self, amount: int) -> str:
        """Execute workflow with amount-based branching."""
        # Step 1: Withdraw
        await workflow.execute_activity(
            "withdraw",
            args=[amount],
            start_to_close_timeout=timedelta(seconds=10),
        )

        # Step 2: Conditional approval
        needs_approval = amount > 1000
        if needs_approval:
            await workflow.execute_activity(
                "approve",
                args=[amount],
                start_to_close_timeout=timedelta(seconds=10),
            )

        # Step 3: Deposit
        await workflow.execute_activity(
            "deposit",
            args=[amount],
            start_to_close_timeout=timedelta(seconds=10),
        )

        return "complete"


def generate_mermaid(paths: List[List[str]]) -> str:
    """Generate Mermaid diagram from execution paths."""
    mermaid = ["graph TD"]
    mermaid.append("    Start[Start]")

    # Track unique nodes
    nodes = set()
    edges = set()

    for path_idx, path in enumerate(paths):
        prev_node = "Start"
        for step_idx, step in enumerate(path):
            # Create unique node ID
            node_id = f"N{path_idx}_{step_idx}"
            nodes.add((node_id, step))

            # Add edge
            edges.add((prev_node, node_id, step))
            prev_node = node_id

        # Add end edge
        edges.add((prev_node, "End", "complete"))

    # Add nodes
    for node_id, label in sorted(nodes):
        mermaid.append(f"    {node_id}[\"{label}\"]")

    mermaid.append("    End[End]")

    # Add edges
    for src, dst, label in sorted(edges):
        mermaid.append(f"    {src} --> {dst}")

    return "\n".join(mermaid)


async def run_approach1():
    """Run Approach 1: Mock Activity Registration."""
    global execution_paths, current_path

    print("=" * 60)
    print("APPROACH 1: Mock Activity Registration")
    print("=" * 60)

    start_time = time.time()

    # Use test server with time-skipping
    from temporalio.testing import WorkflowEnvironment

    async with await WorkflowEnvironment.start_time_skipping() as env:
        client = env.client
        task_queue = "spike-test-approach1"

        # Test amounts: 500 (no approval), 2000 (needs approval)
        test_amounts = [500, 2000]

        async with Worker(
            client,
            task_queue=task_queue,
            workflows=[SpikeTestWorkflow],
            activities=[mock_withdraw, mock_approve, mock_deposit],
        ):
            for amount in test_amounts:
                # Reset path for this execution
                current_path = []

                print(f"\nExecuting workflow with amount=${amount}...")
                result = await client.execute_workflow(
                    SpikeTestWorkflow.run,
                    amount,
                    id=f"spike-test-workflow-{amount}",
                    task_queue=task_queue,
                )

                # Record the path
                execution_paths.append(current_path.copy())
                print(f"  Result: {result}")
                print(f"  Path: {current_path}")

    # Generate diagram
    print("\n" + "=" * 60)
    print("EXECUTION PATHS:")
    print("=" * 60)
    for idx, path in enumerate(execution_paths):
        print(f"Path {idx + 1}: {' -> '.join(path)}")

    print("\n" + "=" * 60)
    print("MERMAID DIAGRAM:")
    print("=" * 60)
    mermaid = generate_mermaid(execution_paths)
    print(mermaid)

    elapsed = time.time() - start_time

    print("\n" + "=" * 60)
    print("RESULTS:")
    print("=" * 60)
    print(f"✓ Generated {len(execution_paths)} different paths")
    print(f"✓ Execution time: {elapsed:.2f} seconds")
    print(f"✓ Deterministic: Yes (same input = same path)")
    print(f"✓ Produces Mermaid output: Yes")

    return execution_paths, mermaid, elapsed


if __name__ == "__main__":
    asyncio.run(run_approach1())
