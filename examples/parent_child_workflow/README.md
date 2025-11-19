# Parent-Child Workflow Example

This example demonstrates cross-workflow visualization with parent-child workflow relationships. It shows how to use `analyze_workflow_graph()` to visualize workflows that call child workflows via `execute_child_workflow()`.

## Workflow Structure

### OrderWorkflow (Parent)

Order processing workflow with one decision point:
- **Decision: HighValue** - Order amount > $10,000 requires manager approval
- **Activities:**
  - `validate_order` - Validate order details
  - `manager_approval` - Approve high-value orders (conditional)
  - `send_confirmation` - Send order confirmation
- **Child Workflow:** Calls `PaymentWorkflow` to process payment

### PaymentWorkflow (Child)

Payment processing workflow with one decision point:
- **Decision: Requires3DS** - Payment amount > $5,000 requires 3D Secure authentication
- **Activities:**
  - `process_payment` - Process payment transaction
  - `verify_3ds` - Verify 3D Secure authentication (conditional)

## Path Combinations

With 1 decision in parent and 1 decision in child, there are **4 total end-to-end execution paths**:

1. **Low value order + Standard payment**: Order ≤ $10k, Payment ≤ $5k
2. **Low value order + Secure payment**: Order ≤ $10k, Payment > $5k
3. **High value order + Standard payment**: Order > $10k, Payment ≤ $5k
4. **High value order + Secure payment**: Order > $10k, Payment > $5k

## Expansion Modes

### Reference Mode (Default)

Child workflow appears as atomic node in parent workflow diagram.

**Use when:**
- You want a high-level overview of workflow structure
- Path explosion is a concern (many decisions in child workflows)
- You need to focus on parent workflow logic only

**Path count:** 2 (only parent decisions)

```python
from temporalio_graphs import analyze_workflow_graph, GraphBuildingContext

context = GraphBuildingContext(child_workflow_expansion="reference")
result = analyze_workflow_graph("parent_workflow.py", context=context)
```

### Inline Mode

Complete end-to-end paths spanning parent and child workflows.

**Use when:**
- You need to understand complete execution flow from start to finish
- You want to see all activity sequences across workflow boundaries
- Total path count is manageable (< 1024 by default)

**Path count:** 4 (2 parent × 2 child)

```python
context = GraphBuildingContext(child_workflow_expansion="inline")
result = analyze_workflow_graph("parent_workflow.py", context=context)
```

**Warning:** Path explosion risk! If parent has 10 decisions and child has 10 decisions, inline mode generates 2^10 × 2^10 = 1,048,576 paths. Use `max_paths` limit to prevent this.

### Subgraph Mode

Separate subgraph blocks for each workflow showing structural boundaries.

**Use when:**
- You want to see workflow structure with clear boundaries
- You need to understand parent-child relationships
- You want structural visualization without path explosion

**Path count:** 2 per workflow (same as reference mode)

```python
context = GraphBuildingContext(child_workflow_expansion="subgraph")
result = analyze_workflow_graph("parent_workflow.py", context=context)
```

## Running the Example

From the project root:

```bash
python examples/parent_child_workflow/run.py
```

This will generate visualizations for all three expansion modes.

## Usage in Your Own Workflows

### 1. Import Child Workflow

```python
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from your_module import ChildWorkflow
```

### 2. Call Child Workflow

```python
@workflow.defn
class ParentWorkflow:
    @workflow.run
    async def run(self, arg: str) -> str:
        # Execute child workflow
        result = await workflow.execute_child_workflow(
            ChildWorkflow,
            args=[arg],
            id="child-workflow-id",
        )
        return result
```

### 3. Analyze with Cross-Workflow Support

```python
from temporalio_graphs import analyze_workflow_graph

# Analyze parent workflow (discovers child workflows automatically)
result = analyze_workflow_graph("parent_workflow.py")
print(result)
```

## File Organization

```
parent_child_workflow/
├── README.md                         # This file
├── parent_workflow.py                # Parent workflow (OrderWorkflow)
├── child_workflow.py                 # Child workflow (PaymentWorkflow)
├── run.py                            # Runner demonstrating all modes
├── expected_output_reference.md      # Golden file for reference mode
├── expected_output_inline.md         # Golden file for inline mode
└── expected_output_subgraph.md       # Golden file for subgraph mode
```

## Testing

This example is used in integration tests to validate cross-workflow visualization:

```bash
pytest tests/integration/test_parent_child_workflow.py -v
```

The integration tests verify:
- ✅ All three expansion modes work correctly
- ✅ Path counts match expected values (2 for reference, 4 for inline)
- ✅ Generated output matches golden files (regression testing)
- ✅ Mermaid syntax is valid and parseable

## Troubleshooting

### Child workflow not found

**Error:** `ChildWorkflowNotFoundError: Cannot find child workflow 'PaymentWorkflow'`

**Solution:** Ensure child workflow file is in the same directory as parent workflow, or provide `workflow_search_paths`:

```python
result = analyze_workflow_graph(
    "parent_workflow.py",
    workflow_search_paths=["./workflows", "./common"]
)
```

### Circular workflow reference

**Error:** `CircularWorkflowError: Circular workflow reference detected: A -> B -> A`

**Solution:** Remove circular dependencies. Temporal workflows should not have circular parent-child relationships.

### Path explosion in inline mode

**Error:** `GraphGenerationError: Inline mode path explosion: 1024 paths exceeds max_paths limit`

**Solution:** Either:
- Use reference or subgraph mode instead
- Increase `max_paths` limit (if you really need all paths)
- Reduce decision points in workflows

```python
context = GraphBuildingContext(
    child_workflow_expansion="inline",
    max_paths=2048  # Increase limit
)
```

## Related Examples

- `examples/simple_linear/` - Basic linear workflow without decisions
- `examples/money_transfer/` - Single workflow with 2 decision points
- `examples/signal_workflow/` - Workflow with signal/wait conditions

## References

- [Epic 6 Tech Spec](../../docs/sprint-artifacts/tech-spec-epic-6.md) - Cross-workflow visualization specification
- [Integration Tests](../../tests/integration/test_parent_child_workflow.py) - Comprehensive test coverage
- [API Documentation](../../README.md#cross-workflow-visualization) - analyze_workflow_graph() reference
