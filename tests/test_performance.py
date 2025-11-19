"""Performance tests for workflow validation.

Tests ensure validation operations meet performance requirements:
- Unreachable activity detection: <10ms for 50 activities
"""

import time
from pathlib import Path

from temporalio_graphs._internal.graph_models import Activity, WorkflowMetadata
from temporalio_graphs.context import GraphBuildingContext
from temporalio_graphs.path import GraphPath, PathStep
from temporalio_graphs.validator import validate_workflow


def test_validation_performance() -> None:
    """Test validation completes in less than 10ms for 50 activities.

    AC 6: Performance validation (<10ms for 50 activities).
    """
    # Create metadata with 50 activities
    activities = [
        Activity(f"activity_{i}", i * 10)
        for i in range(50)
    ]

    metadata = WorkflowMetadata(
        workflow_class="PerformanceTestWorkflow",
        workflow_run_method="run",
        activities=activities,
        decision_points=[],
        signal_points=[],
        source_file=Path("test_perf.py"),
        total_paths=1
    )

    # Create path with only 25 activities called (50% unreachable)
    path_steps = [
        PathStep("activity", f"activity_{i}")
        for i in range(0, 50, 2)  # Every other activity (25 total)
    ]
    path = GraphPath("0", path_steps)

    context = GraphBuildingContext()

    # Measure validation time
    start = time.perf_counter()
    report = validate_workflow(metadata, [path], context)
    duration = time.perf_counter() - start

    # Validate results are correct
    assert report.has_warnings() is True
    assert report.unreachable_count == 25  # 25 activities unreachable
    assert report.total_activities == 50

    # Performance requirement: <10ms (0.01 seconds)
    assert duration < 0.01, (
        f"Validation took {duration*1000:.2f}ms, exceeds 10ms requirement"
    )
