"""Approach 1: Mock Activity Registration (Simplified).

This approach demonstrates the core concept without requiring a running Temporal server.
It simulates the workflow execution with mock activities that record paths.
"""
import time
from typing import List, Callable, Any
from dataclasses import dataclass


@dataclass
class ActivityCall:
    """Represents an activity invocation."""
    name: str
    args: List[Any]


class ExecutionPath:
    """Records the execution path of a workflow."""

    def __init__(self):
        self.steps: List[ActivityCall] = []

    def record(self, name: str, args: List[Any]):
        """Record an activity execution."""
        self.steps.append(ActivityCall(name, args))

    def __str__(self):
        return " -> ".join([f"{step.name}({step.args[0]})" for step in self.steps])


class MockWorkflowExecutor:
    """Simulates workflow execution with path recording."""

    def __init__(self):
        self.current_path = None

    async def execute_activity(self, name: str, args: List[Any]):
        """Execute (record) an activity."""
        self.current_path.record(name, args)
        return f"Executed {name}"

    async def run_workflow(self, amount: int) -> ExecutionPath:
        """Execute the spike test workflow logic."""
        self.current_path = ExecutionPath()

        # Step 1: Withdraw
        await self.execute_activity("withdraw", [amount])

        # Step 2: Conditional approval
        needs_approval = amount > 1000
        if needs_approval:
            await self.execute_activity("approve", [amount])

        # Step 3: Deposit
        await self.execute_activity("deposit", [amount])

        return self.current_path


def generate_mermaid(paths: List[ExecutionPath]) -> str:
    """Generate Mermaid diagram from execution paths."""
    mermaid = ["graph TD"]
    mermaid.append("    Start((Start))")

    # For each path, create nodes
    for path_idx, path in enumerate(paths):
        prev_node = "Start"
        for step_idx, step in enumerate(path.steps):
            node_id = f"P{path_idx}S{step_idx}"
            label = f"{step.name}({step.args[0]})"
            mermaid.append(f"    {node_id}[{label}]")

            # Add edge from previous node
            mermaid.append(f"    {prev_node} --> {node_id}")
            prev_node = node_id

        # Connect to end
        mermaid.append(f"    {prev_node} --> End")

    mermaid.append("    End((End))")

    return "\n".join(mermaid)


async def run_approach1():
    """Run Approach 1: Mock Activity Registration."""
    print("=" * 60)
    print("APPROACH 1: Mock Activity Registration (Simplified)")
    print("=" * 60)

    start_time = time.time()

    # Test amounts: 500 (no approval), 2000 (needs approval)
    test_amounts = [500, 2000]
    executor = MockWorkflowExecutor()
    execution_paths: List[ExecutionPath] = []

    for amount in test_amounts:
        print(f"\nExecuting workflow with amount=${amount}...")
        path = await executor.run_workflow(amount)
        execution_paths.append(path)
        print(f"  Path: {path}")

    # Generate diagram
    print("\n" + "=" * 60)
    print("EXECUTION PATHS:")
    print("=" * 60)
    for idx, path in enumerate(execution_paths):
        print(f"Path {idx + 1}: {path}")

    print("\n" + "=" * 60)
    print("MERMAID DIAGRAM:")
    print("=" * 60)
    mermaid = generate_mermaid(execution_paths)
    print(mermaid)

    elapsed = time.time() - start_time

    print("\n" + "=" * 60)
    print("EVALUATION - Approach 1: Mock Activity Registration")
    print("=" * 60)
    print(f"✓ Can generate 2^n paths? YES - Generated {len(execution_paths)} paths for 1 decision point")
    print(f"✓ Deterministic execution? YES - Same input = same path")
    print(f"✓ Code complexity? LOW - Simple mock pattern")
    print(f"✓ Matches .NET model? PARTIALLY - Uses permutations but needs actual Temporal")
    print(f"✓ Performance? EXCELLENT - {elapsed:.4f} seconds")
    print(f"✓ Produces Mermaid output? YES")
    print()
    print("PROS:")
    print("  + Very fast execution (no Temporal server needed)")
    print("  + Simple to understand and implement")
    print("  + Easy to control which paths are generated")
    print("  + Can record any custom metadata during execution")
    print()
    print("CONS:")
    print("  - Requires running workflow multiple times (once per path)")
    print("  - Need to know decision points ahead of time to generate all paths")
    print("  - Not analyzing actual workflow code structure")
    print("  - Mock activities must be manually created")

    return execution_paths, mermaid, elapsed


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_approach1())
