# temporalio-graphs Quick Start Card

## Installation (Pick One)

```bash
pip install temporalio-graphs        # Most common
uv pip install temporalio-graphs     # Fastest
poetry add temporalio-graphs         # Poetry projects
```

## Basic Usage (3 Lines)

```python
from temporalio_graphs import analyze_workflow

result = analyze_workflow("my_workflow.py")
print(result)  # Prints Mermaid diagram
```

## Common Patterns

### Save to File
```python
from temporalio_graphs import analyze_workflow, GraphBuildingContext
from pathlib import Path

context = GraphBuildingContext(graph_output_file=Path("diagram.md"))
analyze_workflow("workflow.py", context)
```

### Custom Configuration
```python
context = GraphBuildingContext(
    split_names_by_words=False,      # Keep camelCase
    suppress_validation=True,        # No warnings
    max_decision_points=15           # Allow more paths
)
result = analyze_workflow("workflow.py", context)
```

### Error Handling
```python
from temporalio_graphs import analyze_workflow, WorkflowParseError

try:
    result = analyze_workflow("workflow.py")
except WorkflowParseError as e:
    print(f"Error at {e.file_path}:{e.line}")
    print(f"Suggestion: {e.suggestion}")
```

## Workflow Helpers

### Mark Decision Points
```python
from temporalio import workflow
from temporalio_graphs import to_decision

@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self, amount: float) -> str:
        if await to_decision(amount > 1000, "HighValue"):
            await workflow.execute_activity(special_handling, ...)
        return "complete"
```

### Mark Wait Conditions
```python
from temporalio_graphs import wait_condition
from datetime import timedelta

if await wait_condition(
    lambda: self.approved,
    timedelta(hours=24),
    "WaitForApproval"
):
    # Signaled path
    ...
else:
    # Timeout path
    ...
```

## Output Formats

```python
# Mermaid only (default)
analyze_workflow("workflow.py", output_format="mermaid")

# Path list only
analyze_workflow("workflow.py", output_format="paths")

# Both (full report)
analyze_workflow("workflow.py", output_format="full")
```

## Multi-Workflow Analysis

```python
from temporalio_graphs import analyze_workflow_graph, GraphBuildingContext

# Expand child workflows inline
context = GraphBuildingContext(child_workflow_expansion="inline")
result = analyze_workflow_graph("parent_workflow.py", context)
```

## Supported Patterns ✅

- `workflow.execute_activity(activity, ...)`
- `workflow.execute_activity_method(Class.method, ...)`
- `workflow.execute_child_workflow(ChildWorkflow.run, ...)`
- `workflow.wait_condition(lambda: ...)` - Ignored (Temporal's built-in)
- `to_decision(condition, name)` - Marks decision points
- `wait_condition(condition, timeout, name)` - Marks signals (3 args)

## Need Help?

- **Full Documentation**: See README.md
- **API Reference**: See docs/api-reference.md
- **Examples**: See examples/ directory
- **Packaging**: See PACKAGING_GUIDE.md
- **Issues**: https://github.com/yourusername/temporalio-graphs/issues

## Type Hints Included ✅

Package includes `py.typed` marker for full type checking support with mypy, pyright, and other type checkers.

---

**Version**: 0.1.0 | **License**: MIT | **Python**: 3.10+
