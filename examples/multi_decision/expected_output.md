```mermaid
flowchart LR
s((Start))
approve_loan[approve_loan]
d0{High Value}
d1{Low Credit}
d2{Existing Loans}
debt_ratio_check[debt_ratio_check]
manager_review[manager_review]
require_collateral[require_collateral]
validate_application[validate_application]
e((End))
s --> validate_application
validate_application --> d0
d0 -- no --> d1
d1 -- no --> d2
d2 -- no --> approve_loan
approve_loan --> e
d2 -- yes --> debt_ratio_check
debt_ratio_check --> approve_loan
d1 -- yes --> require_collateral
require_collateral --> d2
d0 -- yes --> manager_review
manager_review --> d1
```

--- Execution Paths (8 total) ---
Decision Points: 3 (2^3 = 8 paths)

Path 1: Start → validate_application → approve_loan → End
Path 2: Start → validate_application → debt_ratio_check → approve_loan → End
Path 3: Start → validate_application → require_collateral → approve_loan → End
Path 4: Start → validate_application → require_collateral → debt_ratio_check → approve_loan → End
Path 5: Start → validate_application → manager_review → approve_loan → End
Path 6: Start → validate_application → manager_review → debt_ratio_check → approve_loan → End
Path 7: Start → validate_application → manager_review → require_collateral → approve_loan → End
Path 8: Start → validate_application → manager_review → require_collateral → debt_ratio_check → approve_loan → End