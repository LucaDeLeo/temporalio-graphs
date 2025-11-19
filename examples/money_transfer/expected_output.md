# MoneyTransfer Workflow - Expected Mermaid Output

## Execution Paths

This workflow has 2 decision points creating 4 possible execution paths. The workflow analyzes the code structure statically to determine all possible execution paths based on decision outcomes.

**Important**: This output represents the graph structure analyzed from the MoneyTransfer workflow implementation. The 4 paths correspond to all 2^2 combinations of the 2 decision points (NeedToConvert and IsTFN_Known).

### Path 1: Convert + Notify ATO (NeedToConvert=true, IsTFN_Known=true)
- Decision sequence: d0=true → d1=true
- Activities: withdraw_funds → currency_convert → notify_ato → deposit_funds
- When: source_currency ≠ dest_currency AND tfn_known = true

### Path 2: Convert + Non-Resident Tax (NeedToConvert=true, IsTFN_Known=false)
- Decision sequence: d0=true → d1=false
- Activities: withdraw_funds → currency_convert → take_non_resident_tax → deposit_funds
- When: source_currency ≠ dest_currency AND tfn_known = false

### Path 3: No Convert + Notify ATO (NeedToConvert=false, IsTFN_Known=true)
- Decision sequence: d0=false → d1=true
- Activities: withdraw_funds → notify_ato → deposit_funds
- When: source_currency = dest_currency AND tfn_known = true

### Path 4: No Convert + Non-Resident Tax (NeedToConvert=false, IsTFN_Known=false)
- Decision sequence: d0=false → d1=false
- Activities: withdraw_funds → take_non_resident_tax → deposit_funds
- When: source_currency = dest_currency AND tfn_known = false

## Mermaid Diagram

The diagram below shows the complete workflow structure with all 4 execution paths. Decision nodes (d0 and d1) are rendered as diamond shapes with yes/no branch labels. Activities are shown as rectangular nodes.

```mermaid
flowchart LR
s((Start))
currency_convert[currency_convert]
d0{Need To Convert}
d1{Is TFN_Known}
deposit_funds[deposit_funds]
notify_ato[notify_ato]
take_non_resident_tax[take_non_resident_tax]
withdraw_funds[withdraw_funds]
e((End))
s --> withdraw_funds
withdraw_funds --> d0
d0 -- no --> d1
d1 -- no --> take_non_resident_tax
take_non_resident_tax --> deposit_funds
deposit_funds --> e
d1 -- yes --> notify_ato
notify_ato --> deposit_funds
d0 -- yes --> currency_convert
currency_convert --> d1
```

## Graph Analysis Notes

- **Total Activities**: 5 (withdraw_funds, currency_convert, notify_ato, take_non_resident_tax, deposit_funds)
- **Total Decision Points**: 2 (NeedToConvert at d0, IsTFN_Known at d1)
- **Total Execution Paths**: 4 (2^2 combinations)
- **Node IDs**:
  - Start: s
  - Activities: Activity names used as node IDs (withdraw_funds, currency_convert, notify_ato, take_non_resident_tax, deposit_funds)
  - Decisions: d0, d1
  - End: e
- **Branch Labels**: yes/no for all decision branches (standard Mermaid decision labels)
- **Reconvergence**: The deposit_funds node appears once and all paths reconverge to it (demonstrated through edges from both notify_ato and take_non_resident_tax to deposit_funds)

## Reference Implementation

This workflow is ported from the .NET Temporalio.Graphs reference implementation. The Python static analysis produces equivalent workflow visualization showing all possible execution paths through the decision points.

## Notes on Graph Structure

The graph structure correctly represents the workflow control flow with decision-based branching:
- **Sequential execution**: withdraw_funds always executes first
- **Conditional branching**: Decision d0 (NeedToConvert) creates two branches - if true, currency_convert executes; if false, it's skipped
- **Nested decisions**: Decision d1 (IsTFN_Known) creates two more branches - if true, notify_ato executes; if false, take_non_resident_tax executes
- **Reconvergence**: Both tax branches reconverge at deposit_funds, which always executes last

This structure matches the .NET Temporalio.Graphs reference implementation and correctly shows only the activities that execute in each decision path, rather than listing all activities sequentially.
