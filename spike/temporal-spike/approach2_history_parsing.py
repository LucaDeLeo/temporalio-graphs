"""Approach 2: History-Based Parsing for Graph Generation.

This approach runs the workflow, extracts execution history, and parses
events to build a graph. This is similar to the existing temporal-diagram-generator.
"""
import time
from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum


class EventType(Enum):
    """Temporal workflow event types."""
    WORKFLOW_STARTED = "WorkflowExecutionStarted"
    ACTIVITY_SCHEDULED = "ActivityTaskScheduled"
    ACTIVITY_STARTED = "ActivityTaskStarted"
    ACTIVITY_COMPLETED = "ActivityTaskCompleted"
    WORKFLOW_COMPLETED = "WorkflowExecutionCompleted"


@dataclass
class HistoryEvent:
    """Represents a workflow history event."""
    event_id: int
    event_type: EventType
    timestamp: str
    attributes: Dict[str, Any]


@dataclass
class ExecutionHistory:
    """Represents workflow execution history."""
    workflow_id: str
    events: List[HistoryEvent]


# Simulated execution histories for our test workflow
HISTORY_NO_APPROVAL = ExecutionHistory(
    workflow_id="spike-test-500",
    events=[
        HistoryEvent(1, EventType.WORKFLOW_STARTED, "2025-11-18T10:00:00Z", {"input": 500}),
        HistoryEvent(2, EventType.ACTIVITY_SCHEDULED, "2025-11-18T10:00:01Z", {"activityType": "withdraw"}),
        HistoryEvent(3, EventType.ACTIVITY_STARTED, "2025-11-18T10:00:02Z", {"activityType": "withdraw"}),
        HistoryEvent(4, EventType.ACTIVITY_COMPLETED, "2025-11-18T10:00:03Z", {"activityType": "withdraw", "result": "Withdrew $500"}),
        HistoryEvent(5, EventType.ACTIVITY_SCHEDULED, "2025-11-18T10:00:04Z", {"activityType": "deposit"}),
        HistoryEvent(6, EventType.ACTIVITY_STARTED, "2025-11-18T10:00:05Z", {"activityType": "deposit"}),
        HistoryEvent(7, EventType.ACTIVITY_COMPLETED, "2025-11-18T10:00:06Z", {"activityType": "deposit", "result": "Deposited $500"}),
        HistoryEvent(8, EventType.WORKFLOW_COMPLETED, "2025-11-18T10:00:07Z", {"result": "complete"}),
    ]
)

HISTORY_WITH_APPROVAL = ExecutionHistory(
    workflow_id="spike-test-2000",
    events=[
        HistoryEvent(1, EventType.WORKFLOW_STARTED, "2025-11-18T10:00:00Z", {"input": 2000}),
        HistoryEvent(2, EventType.ACTIVITY_SCHEDULED, "2025-11-18T10:00:01Z", {"activityType": "withdraw"}),
        HistoryEvent(3, EventType.ACTIVITY_STARTED, "2025-11-18T10:00:02Z", {"activityType": "withdraw"}),
        HistoryEvent(4, EventType.ACTIVITY_COMPLETED, "2025-11-18T10:00:03Z", {"activityType": "withdraw", "result": "Withdrew $2000"}),
        HistoryEvent(5, EventType.ACTIVITY_SCHEDULED, "2025-11-18T10:00:04Z", {"activityType": "approve"}),
        HistoryEvent(6, EventType.ACTIVITY_STARTED, "2025-11-18T10:00:05Z", {"activityType": "approve"}),
        HistoryEvent(7, EventType.ACTIVITY_COMPLETED, "2025-11-18T10:00:06Z", {"activityType": "approve", "result": "Approved $2000"}),
        HistoryEvent(8, EventType.ACTIVITY_SCHEDULED, "2025-11-18T10:00:07Z", {"activityType": "deposit"}),
        HistoryEvent(9, EventType.ACTIVITY_STARTED, "2025-11-18T10:00:08Z", {"activityType": "deposit"}),
        HistoryEvent(10, EventType.ACTIVITY_COMPLETED, "2025-11-18T10:00:09Z", {"activityType": "deposit", "result": "Deposited $2000"}),
        HistoryEvent(11, EventType.WORKFLOW_COMPLETED, "2025-11-18T10:00:10Z", {"result": "complete"}),
    ]
)


class HistoryParser:
    """Parses workflow execution history into a graph structure."""

    def parse_activities(self, history: ExecutionHistory) -> List[str]:
        """Extract activity sequence from history."""
        activities = []
        for event in history.events:
            if event.event_type == EventType.ACTIVITY_COMPLETED:
                activity_type = event.attributes.get("activityType")
                activities.append(activity_type)
        return activities

    def generate_mermaid(self, histories: List[ExecutionHistory]) -> str:
        """Generate Mermaid diagram from multiple execution histories."""
        mermaid = ["graph TD"]
        mermaid.append("    Start((Start))")

        for hist_idx, history in enumerate(histories):
            activities = self.parse_activities(history)
            prev_node = "Start"

            for act_idx, activity in enumerate(activities):
                node_id = f"H{hist_idx}A{act_idx}"
                mermaid.append(f"    {node_id}[{activity}]")
                mermaid.append(f"    {prev_node} --> {node_id}")
                prev_node = node_id

            # Connect to end
            mermaid.append(f"    {prev_node} --> End")

        mermaid.append("    End((End))")
        return "\n".join(mermaid)


async def run_approach2():
    """Run Approach 2: History-Based Parsing."""
    print("=" * 60)
    print("APPROACH 2: History-Based Parsing")
    print("=" * 60)

    start_time = time.time()

    # Simulate having execution histories
    histories = [HISTORY_NO_APPROVAL, HISTORY_WITH_APPROVAL]

    parser = HistoryParser()

    print("\nParsing execution histories...")
    for idx, history in enumerate(histories):
        activities = parser.parse_activities(history)
        print(f"\nWorkflow: {history.workflow_id}")
        print(f"  Total events: {len(history.events)}")
        print(f"  Activities: {' -> '.join(activities)}")

    # Generate diagram
    print("\n" + "=" * 60)
    print("MERMAID DIAGRAM:")
    print("=" * 60)
    mermaid = parser.generate_mermaid(histories)
    print(mermaid)

    elapsed = time.time() - start_time

    print("\n" + "=" * 60)
    print("EVALUATION - Approach 2: History-Based Parsing")
    print("=" * 60)
    print(f"✓ Can generate 2^n paths? NO - Only shows executed paths")
    print(f"✓ Deterministic execution? N/A - Analyzes post-execution")
    print(f"✓ Code complexity? MEDIUM - Requires event parsing logic")
    print(f"✓ Matches .NET model? NO - Only shows what happened, not all possibilities")
    print(f"✓ Performance? EXCELLENT - {elapsed:.4f} seconds (post-execution)")
    print(f"✓ Produces Mermaid output? YES")
    print()
    print("PROS:")
    print("  + Works with real execution data")
    print("  + Shows actual execution flow with real results")
    print("  + Can include timing information")
    print("  + No need to modify workflows or activities")
    print("  + This is how the existing temporal-diagram-generator works")
    print()
    print("CONS:")
    print("  - CANNOT generate all possible paths (only executed ones)")
    print("  - Requires workflows to actually run (possibly multiple times)")
    print("  - Need to execute workflow for each path you want to visualize")
    print("  - Does NOT match .NET's permutation-based approach")
    print("  - Cannot show branches that weren't taken")

    return histories, mermaid, elapsed


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_approach2())
