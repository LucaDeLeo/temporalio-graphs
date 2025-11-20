```mermaid
flowchart LR
s((Start))
WaitForPayment{{Wait For Payment}}
cancel_order[cancel_order]
d0{Inventory Available}
d1{High Value Order}
notify_backorder[notify_backorder]
process_payment[process_payment]
require_manual_approval[require_manual_approval]
reserve_inventory[reserve_inventory]
ship_order[ship_order]
validate_order[validate_order]
e((End))
s --> validate_order
validate_order --> d0
d0 -- no --> notify_backorder
notify_backorder --> d1
d1 -- no --> WaitForPayment
WaitForPayment -- Timeout --> cancel_order
cancel_order --> e
WaitForPayment -- Signaled --> process_payment
process_payment --> ship_order
ship_order --> e
d1 -- yes --> require_manual_approval
require_manual_approval --> WaitForPayment
d0 -- yes --> reserve_inventory
reserve_inventory --> d1
```

--- Execution Paths (8 total) ---
Decision Points: 2 (2^2 = 8 paths)

Path 1: Start → validate_order → notify_backorder → cancel_order → End
Path 2: Start → validate_order → notify_backorder → process_payment → ship_order → End
Path 3: Start → validate_order → notify_backorder → require_manual_approval → cancel_order → End
Path 4: Start → validate_order → notify_backorder → require_manual_approval → process_payment → ship_order → End
Path 5: Start → validate_order → reserve_inventory → cancel_order → End
Path 6: Start → validate_order → reserve_inventory → process_payment → ship_order → End
Path 7: Start → validate_order → reserve_inventory → require_manual_approval → cancel_order → End
Path 8: Start → validate_order → reserve_inventory → require_manual_approval → process_payment → ship_order → End