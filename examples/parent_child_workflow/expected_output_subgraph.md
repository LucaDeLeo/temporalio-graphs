# Expected Output: Subgraph Mode

Separate subgraph blocks showing workflow boundaries.
Generates 2 paths per workflow (same as reference for path count).

```mermaid
flowchart LR
s((Start))
HighValue[High Value]
PaymentWorkflow[Payment Workflow]
manager_approval[manager_approval]
send_confirmation[send_confirmation]
validate_order[validate_order]
e((End))
s --> validate_order
validate_order --> HighValue
HighValue --> manager_approval
manager_approval --> PaymentWorkflow
PaymentWorkflow --> send_confirmation
send_confirmation --> e
```

## Path List

Path 0: validate_order → HighValue → manager_approval → PaymentWorkflow → send_confirmation
Path 1: validate_order → HighValue → manager_approval → PaymentWorkflow → send_confirmation

## Notes

- Same path generation as reference mode
- Future enhancement: Wrap parent and child workflows in separate `subgraph` blocks:
  ```
  subgraph OrderWorkflow
    [parent workflow nodes]
  end
  subgraph PaymentWorkflow
    [child workflow nodes]
  end
  ```
- Transition edges should connect between subgraphs
- Provides clear visual separation of workflow boundaries
