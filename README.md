# temporalio-graphs

Static analysis for Temporal Python workflows that outputs Mermaid diagrams covering every possible execution path.

## What it does
- Parses workflow source with Python's AST; no Temporal server or activity execution required.
- Detects activities, decision points (`to_decision`), signal/wait points (`wait_condition`), and child workflow calls.
- Generates every path permutation (2^n across decisions + signals) with configurable limits to prevent explosion.
- Emits validation warnings for unreachable activities and branch-limit overruns.
- Optional multi-workflow view for `execute_child_workflow()` using reference, inline, or subgraph rendering modes.

## Install
```bash
# Recommended for development
uv pip install temporalio-graphs

# Standard
pip install temporalio-graphs
```
Requires Python 3.10+ and `temporalio>=1.7.1`.

## Quick start
```python
from datetime import timedelta
from temporalio import workflow
from temporalio_graphs import analyze_workflow, to_decision, wait_condition

@workflow.defn
class PaymentWorkflow:
    def __init__(self) -> None:
        self.approved = False

    @workflow.run
    async def run(self, amount: int) -> str:
        await workflow.execute_activity(validate_payment, amount)

        if await to_decision(amount > 1_000, "HighValue"):
            await workflow.execute_activity(require_approval, amount)

        if await wait_condition(lambda: self.approved, timedelta(hours=24), "WaitForApproval"):
            await workflow.execute_activity(process_payment, amount)
            return "approved"

        await workflow.execute_activity(handle_timeout, amount)
        return "timeout"

print(analyze_workflow("payment_workflow.py"))  # Mermaid diagram string
```
String literal names are required for `to_decision(..., "Name")` and `wait_condition(..., "Name")` so they can be detected statically.

## Configuration (GraphBuildingContext)
Create a context and pass it to `analyze_workflow()` or `analyze_workflow_graph()`.
```python
from temporalio_graphs import GraphBuildingContext

context = GraphBuildingContext(
    max_decision_points=10,   # decisions + signals allowed before warning
    max_paths=1024,           # hard cap on generated paths
    split_names_by_words=True,
    include_path_list=True,   # included when output_format="full"
    output_format="full",    # "mermaid", "paths", or "full"
    child_workflow_expansion="reference",  # also "inline" or "subgraph"
    graph_output_file=None,   # write to file when set
)
```
Key defaults: start/end labels `"Start"`/`"End"`, decision edge labels `"yes"`/`"no"`, signal edges `"Signaled"`/`"Timeout"`.

## Multi-workflow graphs
Use `analyze_workflow_graph()` when a parent workflow spawns children via `execute_child_workflow()`.
```python
from temporalio_graphs import analyze_workflow_graph, GraphBuildingContext

context = GraphBuildingContext(child_workflow_expansion="inline")
diagram = analyze_workflow_graph(
    "parent_workflow.py",
    workflow_search_paths=["./workflows"],
    context=context,
)
```
`child_workflow_expansion` modes:
- `reference` (default): render children as `[[ChildWorkflow]]` nodes without multiplying paths.
- `inline`: full end-to-end paths across parent and children.
- `subgraph`: separate Mermaid subgraphs for each workflow.

## Examples
Run the curated examples (linear, branching, signals, multi-decision):
```bash
make run-examples
# or individually
python examples/simple_linear/run.py
python examples/money_transfer/run.py
python examples/signal_workflow/run.py
python examples/multi_decision/run.py
```

## Troubleshooting
- Too many branches: raise `max_decision_points` / `max_paths` in `GraphBuildingContext` or simplify the workflow; errors include the calculated path count.
- Names missing: decision/signal names must be string literals; variables and f-strings are ignored by static analysis.
- Unsupported flow: loops or dynamic activity names are not graphed; refactor to explicit steps or decisions.

## Development
```bash
uv venv && source .venv/bin/activate
uv sync
pytest -v --cov=src/temporalio_graphs
mypy src/
ruff check src/ tests/ examples/
ruff format src/ tests/ examples/
```

## Reference
- API: `docs/api-reference.md`
- Architecture rationale: `docs/architecture.md`, `spike/EXECUTIVE_SUMMARY.md`
- Examples: `examples/`
- License: MIT (`LICENSE`)
