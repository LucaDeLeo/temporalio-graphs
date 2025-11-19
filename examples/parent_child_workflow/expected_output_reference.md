# Expected Output: Reference Mode

Child workflow appears as [[PaymentWorkflow]] node (or PaymentWorkflow until rendering is fully implemented).
Generates 2 paths (parent decisions only).

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

- Child workflow (PaymentWorkflow) appears as atomic node
- Only parent workflow decisions are expanded
- No path explosion (safe mode)
- Future enhancement: Render as [[PaymentWorkflow]] with double brackets
