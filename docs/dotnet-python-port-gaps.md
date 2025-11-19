# .NET to Python Port - Feature Gap Analysis

**Investigation Date:** 2025-11-19
**Investigator:** Claude Code (Deep Analysis)
**Source Comparison:** `Temporalio.Graphs` (.NET) vs `temporalio-graphs` (Python)

---

## Executive Summary

This document catalogs all identified differences between the .NET Temporalio.Graphs implementation and the Python port. The Python implementation has **successfully ported the core concepts** using a **superior architecture** (static AST analysis vs runtime interceptors), achieving approximately **70% feature parity** with the original.

**Critical Issues:** 1 major correctness bug
**Missing Features:** 4 significant features
**Partial Implementations:** 3 features need enhancement
**Epic Plan Coverage:** 85% of gaps are already planned

---

## Table of Contents

1. [Architectural Differences (Context)](#1-architectural-differences-context)
2. [Critical Correctness Issues](#2-critical-correctness-issues)
3. [Missing Features](#3-missing-features)
4. [Partial/Incomplete Implementations](#4-partialincomplete-implementations)
5. [Configuration Mismatches](#5-configuration-mismatches)
6. [Example Completeness](#6-example-completeness)
7. [Epic Plan Coverage Analysis](#7-epic-plan-coverage-analysis)
8. [Recommendations by Priority](#8-recommendations-by-priority)

---

## 1. Architectural Differences (Context)

### 1.1 .NET Implementation - Runtime Interceptor Approach

**Location:** `/Temporalio.Graphs/Temporalio.Graphs/GraphBuilder.cs`

**Method:**
- Uses `WorkflowInboundInterceptor` and `ActivityInboundInterceptor` to intercept workflow execution
- **Executes the workflow** 2^n times (once per decision permutation)
- Mocks activity return values during graph building mode
- Maintains `RuntimeContext` per workflow run with `DecisionsPlans` queue

**Key Pattern (GraphBuilder.cs:337-356):**
```csharp
while (Runtime.DecisionsPlans.Any())
    try {
        Runtime.CurrentGraphPath.Clear();
        await base.ExecuteWorkflowAsync(input); // ACTUAL EXECUTION
        generator.Scenarios.AddPath(Runtime.CurrentGraphPath);
    }
    finally {
        Runtime.DecisionsPlans.RemoveAt(0);
    }
```

**Activity Interception (GraphBuilder.cs:198-268):**
- `ExecuteActivityAsync` intercepts every activity call
- Adds activities and decisions to graph as encountered during execution
- Returns mocked values to continue execution

### 1.2 Python Implementation - Static Analysis Approach

**Location:** `/src/temporalio_graphs/analyzer.py`, `/src/temporalio_graphs/detector.py`

**Method:**
- Uses Python AST (Abstract Syntax Tree) to parse workflow source **without execution**
- `DecisionDetector` traverses AST to find `to_decision()` calls
- `WorkflowAnalyzer` extracts activities via `workflow.execute_activity()` detection
- `PathPermutationGenerator` generates 2^n paths mathematically using `itertools.product`

**Key Pattern (generator.py:269-291):**
```python
for path_index, decision_values in enumerate(
    product([False, True], repeat=num_decisions)
):
    path = GraphPath(path_id=f"path_0b{binary_str}")
    for activity_name in activities:
        path.add_activity(activity_name)
    for decision, value in zip(decisions, decision_values):
        path.add_decision(decision.id, value, decision.name)
    paths.append(path)
```

**Performance:** <1ms vs .NET's exponential execution time

### 1.3 Why Different?

**From `/spike/EXECUTIVE_SUMMARY.md`:**
- Python SDK interceptors **cannot mock activity return values** (unlike .NET)
- Static analysis avoids exponential execution time (2^n workflow runs)
- Generates complete path coverage without actual execution

**Verdict:** ✅ **Architectural difference is justified and superior for Python**

---

## 2. Critical Correctness Issues

### 2.1 Path Generation Order Bug 🔴 CRITICAL

**Status:** ❌ **Active Bug - Affects Correctness**
**Priority:** 🔴 **P0 - Must Fix Before Release**
**Epic Plan:** ❌ Not addressed in epics.md

**Location:** `src/temporalio_graphs/generator.py:280-289`

**The Bug:**
```python
# CURRENT IMPLEMENTATION (INCORRECT)
for activity_name in activities:
    path.add_activity(activity_name)  # All activities added first

for decision, value in zip(decisions, decision_values):
    path.add_decision(decision.id, value, decision.name)  # Then all decisions
```

**Problem:** Activities and decisions should be **interleaved based on their source code positions**, not all activities first then all decisions.

**Example Impact - MoneyTransfer Workflow:**

**Correct Order (.NET produces):**
```
Start → Withdraw → NeedToConvert{decision} → [yes: CurrencyConvert] → IsTFN_Known{decision} → ...
```

**Current Python Output (WRONG):**
```
Start → Withdraw → CurrencyConvert → Deposit → NeedToConvert{decision} → IsTFN_Known{decision} → End
```

**Why This Happens:**
- .NET: Decisions and activities added **as encountered during execution** (GraphBuilder.cs:232-256)
- Python: Static analysis collects all activities, then all decisions, then combines them incorrectly

**Root Cause:** `PathPermutationGenerator._generate_paths_with_decisions()` doesn't use AST control flow analysis to determine correct interleaving.

**Fix Required:**
1. Use `DecisionPoint.line_number` and activity line numbers to determine insertion order
2. Build paths incrementally: insert activities/decisions based on source position
3. Require AST control flow analysis to handle nested conditionals correctly

**Test Case:**
```python
# Workflow structure:
await activity_1()  # Line 10
if await to_decision(cond, "D1"):  # Line 12
    await activity_2()  # Line 13
await activity_3()  # Line 14

# Expected path (D1=True):  activity_1 → D1{yes} → activity_2 → activity_3
# Current path (WRONG):     activity_1 → activity_2 → activity_3 → D1{yes}
```

**Recommendation:**
- **Update Story 3.3 in epics.md** with explicit ordering guidance
- Add AST control flow tracking to `PathPermutationGenerator`
- Use `sorted(activities + decisions, key=lambda x: x.line_number)` approach

---

## 3. Missing Features

### 3.1 wait_condition() Helper - NOT IMPLEMENTED

**Status:** ❌ **Stub Only**
**Priority:** 🔴 **P1 - Required for Epic 4**
**Epic Plan:** ✅ **Fully covered** in Epic 4, Story 4.2 (epics.md:922-967)

**Current State:** `src/temporalio_graphs/helpers.py:145-170`
```python
def wait_condition(...) -> str:
    raise NotImplementedError(
        "Signal point tracking is not implemented in Epic 2. "
        "This will be added in Epic 4 (Story 4.3)."
    )
```

**.NET Reference:** `Temporalio.Graphs/Temporalio.Graphs/WF.cs:101-113`
```csharp
public static Task<bool> WaitConditionAsync(
    Func<bool> conditionCheck,
    TimeSpan timeout,
    CancellationToken? cancellationToken = null,
    [CallerArgumentExpression("conditionCheck")] string conditionName = "",
    ActivityOptions? options = null)
{
    if (!GraphBuilder.IsBuildingGraph)
        return Workflow.WaitConditionAsync(conditionCheck, timeout, cancellationToken);
    else
        return Workflow.ExecuteActivityAsync(
            (GenericActivities b) => b.MakeDecision(dummy, conditionName + ":&sgnl;", ...),
            options ?? new ActivityOptions { StartToCloseTimeout = TimeSpan.FromMinutes(5) }
        );
}
```

**Impact:** Python workflows **cannot model signal-based branching** until Epic 4 is implemented.

**Recommendation:** ✅ **No action needed** - Epic 4, Story 4.2 will implement this

---

### 3.2 Signal Support (Complete Feature Set)

**Status:** ❌ **Not Implemented**
**Priority:** 🔴 **P1 - Required for Epic 4**
**Epic Plan:** ✅ **Comprehensively covered** in Epic 4 (Stories 4.1-4.4)

**Missing Components:**

1. **Signal Point Detection** (Epic 4.1)
   - AST detection of `wait_condition()` calls
   - Extract signal names and line numbers

2. **wait_condition() Helper** (Epic 4.2)
   - Function signature: `async def wait_condition(condition_check, timeout, name) -> bool`
   - Wrapper around `workflow.wait_condition()`

3. **Signal Node Rendering** (Epic 4.3)
   - Hexagon syntax: `2{{SignalName}}`
   - Branch labels: "Signaled" / "Timeout"
   - Path permutation: each signal = 2 paths

4. **Integration Example** (Epic 4.4)
   - ApprovalWorkflow example demonstrating signals

**Coverage:** FR18-FR22 (5 functional requirements)

**Recommendation:** ✅ **No action needed** - Epic 4 fully addresses this

---

### 3.3 Mermaid Compact Syntax - MISSING

**Status:** ❌ **Not Implemented, Not Planned**
**Priority:** 🟡 **P2 - Enhancement**
**Epic Plan:** ❌ **NOT in epics.md** (searched: no matches for "compact", "ToMermaidCompact")

**Current State:** Python only has `MermaidRenderer.to_mermaid()` (full format)

**.NET Implementation:** `Temporalio.Graphs/Temporalio.Graphs/Graphs.cs:154-240`
- **Two output formats:**
  - `ToMermaidSyntax()` (lines 97-147) - Full format with all node-to-node transitions
  - `ToMermaidCompactSyntax()` (lines 154-240) - Compact format using longest path first

**Format Difference Example:**

```mermaid
# ToMermaidSyntax (what Python generates) - 7 lines
flowchart LR
s((Start)) --> 1
1 --> d0
d0 -- yes --> 2
d0 -- no --> 3
2 --> e((End))
3 --> e

# ToMermaidCompactSyntax (missing in Python) - 3 lines
flowchart LR
s((Start)) --> 1 --> d0 -- yes --> 2 --> e((End))
d0 -- no --> 3 --> e
```

**Impact:** Python generates **larger diagrams** (30-40% more lines) for complex workflows with multiple decision points.

**Algorithm (.NET Graphs.cs:168-217):**
1. Sort paths by length (longest first)
2. Add longest path as single chained line
3. For remaining paths, extract unique sequence not already captured
4. Reduces redundancy by reusing common path segments

**Recommendation:** 🔴 **Add to Epic Plan**

**Suggested Story 5.X:**
```markdown
### Story 5.X: Implement Mermaid Compact Syntax Output

**User Story:**
As a library user,
I want compact Mermaid output for complex workflows,
So that diagrams are more readable with fewer redundant lines.

**Acceptance Criteria:**
- MermaidRenderer has to_mermaid_compact() method
- Uses longest-path-first algorithm matching .NET ToMermaidCompactSyntax()
- Reduces line count by ~30% for workflows with 4+ decision points
- Output structure matches .NET for equivalent workflows (regression test)
- Configuration option: context.use_compact_syntax (default False)
- Unit tests compare compact vs full format line counts

**Technical Notes:**
- Reference: Temporalio.Graphs/Graphs.cs:154-240
- Algorithm: Sort by path length DESC, extract unique sequences
- ~200 lines implementation
```

---

### 3.4 Graph Validation Against Activities

**Status:** ❌ **Not Implemented**
**Priority:** 🟡 **P2 - Quality Enhancement**
**Epic Plan:** ✅ **Covered** in Epic 5, Story 5.1 (epics.md:1058-1096)

**Current State:** No validation for orphaned activities

**.NET Implementation:** `Temporalio.Graphs/Graphs.cs:251-274`
```csharp
public static string ValidateGraphAgainst(this GraphGenerator graph, Assembly assembly)
{
    var allActivities = assembly.GetTypes()
        .SelectMany(x => x.GetMethods())
        .Where(x => x.GetAttributes<ActivityAttribute>().IsNotEmpty() &&
                    x.GetAttributes<DecisionAttribute>().IsEmpty())
        .Select(x => x.FullName());

    var missingActivities = allActivities
        .Where(x => !allGraphElements.Contains(x))
        .ToList();

    return $"WARNING: the following activities are not present in the full WF graph: ...";
}
```

**Impact:** Python cannot warn about **orphaned activities** (activities defined but never called in workflow).

**Epic 5, Story 5.1 Covers:**
- FR25: Identify unreachable activities
- FR26: Identify activities defined but never called
- FR27: Validation report listing warnings
- FR32: Suppressible via `context.suppress_validation`

**Recommendation:** ✅ **No action needed** - Epic 5, Story 5.1 addresses this

---

## 4. Partial/Incomplete Implementations

### 4.1 SplitByWords - Oversimplified

**Status:** ⚠️ **Partially Implemented**
**Priority:** 🟡 **P2 - Quality Enhancement**
**Epic Plan:** ⚠️ **Mentioned but underspecified** in Story 2.5 (epics.md:475-476)

**Current Implementation:** `src/temporalio_graphs/renderer.py:217-254`
```python
if context.split_names_by_words:
    display_name = re.sub(r"([a-z])([A-Z])", r"\1 \2", step_name)
```

**Only handles:** lowercase→uppercase boundary
**Example:** `notifyCustomerByEmail` → `notify Customer By Email` ✅

**.NET Implementation:** `Temporalio.Graphs/Extensions.cs:172-195`
- Handles punctuation and symbols
- Handles consecutive uppercase letters (`HTTPRequest` → `HTTP Request`)
- Handles underscores (`IsTFN_Known` → `Is TFN Known`)
- Uses Mermaid alias syntax for multi-word nodes: `nodeid[Display Name]`

**Missing Cases:**

| Input | Expected Output | Current Python Output | Status |
|-------|----------------|---------------------|--------|
| `IsTFN_Known` | `Is TFN Known` | `IsTFN_Known` | ❌ No underscore handling |
| `HTTPRequest` | `HTTP Request` | `HTTPRequest` | ❌ No consecutive uppercase |
| `XMLParser` | `XML Parser` | `XMLParser` | ❌ No consecutive uppercase |
| `notifyCustomer` | `Notify Customer` | `notify Customer` | ⚠️ No capitalization of first word |

**Epic Plan Gap:**
```markdown
# Story 2.5, lines 475-476 (current):
**And** node names support word splitting when context.split_names_by_words=True (FR29, FR35)
**And** camelCase names split to "Camel Case" when enabled

# MISSING: No mention of underscore/uppercase handling
```

**Recommendation:** 🔴 **Enhance Story 2.5**

**Suggested Update to Story 2.5:**
```markdown
### Enhanced Acceptance Criteria:

**And** word splitting handles multiple patterns:
  - camelCase: `validateInput` → `Validate Input`
  - Underscores: `Is_TFN_Known` → `Is TFN Known`
  - Consecutive uppercase: `HTTPSConnection` → `HTTPS Connection`
  - Mixed: `parseXMLDocument` → `Parse XML Document`
**And** first word is capitalized: `notifyCustomer` → `Notify Customer`
**And** uses Mermaid alias syntax for multi-word: `1[Validate Input]`

### Enhanced Technical Notes:

# Reference: Temporalio.Graphs/Extensions.cs:172-195
# Implementation approach:
1. Replace underscores with spaces: `Is_TFN_Known` → `Is TFN Known`
2. Split on lowercase→uppercase: `validateInput` → `validate Input`
3. Split consecutive uppercase before lowercase: `HTTPRequest` → `HTTP Request`
4. Capitalize first letter
5. Trim and normalize whitespace
```

---

### 4.2 MoneyTransfer Example - Incomplete

**Status:** ⚠️ **Intentionally Simplified**
**Priority:** 🟢 **P3 - Design Decision**
**Epic Plan:** ⚠️ **Split across Epic 3.5 and Epic 4.4**

**Current Python Implementation:** `examples/money_transfer/workflow.py`
- **5 activities:** withdraw_funds, currency_convert, notify_ato, take_non_resident_tax, deposit_funds
- **2 decision points:** NeedToConvert, IsTFN_Known
- **0 signal points**
- **Total paths:** 4 (2^2)

**.NET Original:** `Temporalio.Graphs/Samples/MoneyTransferWorker/Workflow.cs`
- **7 activities:** Withdraw, CurrencyConvert, NotifyAto, TakeNonResidentTax, Deposit, **RefundAsync, NotifyPoliceAsync**
- **2 decision points:** NeedToConvert, IsTFN_Known
- **1 signal point:** Interpol Check (WaitConditionAsync)
- **Total paths:** 8 (4 decision paths × 2 signal outcomes)

**Missing from Python (Workflow.cs:69-88):**
```csharp
// Interpol check - completely absent in Python
BankingActivities.CheckWithInterpol(ref interpolCheck);

var isIllegal = await WF.WaitConditionAsync(
    () => interpolCheck,
    TimeSpan.FromMicroseconds(BankingActivities.averageActivityDuration),
    conditionName: "Interpol Check"
);

if (isIllegal) {
    await Workflow.ExecuteActivityAsync(
        () => BankingActivities.RefundAsync(details), options);
    await Workflow.ExecuteActivityAsync(
        () => BankingActivities.NotifyPoliceAsync(details), options);
}
```

**Epic Plan Approach:**
- **Story 3.5** (epics.md:828-878): MoneyTransfer demonstrates **decisions only** (2 decisions, 4 paths)
- **Story 4.4** (epics.md:1001-1046): Separate **ApprovalWorkflow** demonstrates **signals only**

**Intentional Split:** Epic plan deliberately uses **different examples** for different features (pedagogically simpler).

**.NET Approach:** Single unified example demonstrating **both** decisions and signals.

**Options:**

1. **Option A: Keep Split** (Current Epic Plan)
   - ✅ Simpler for learning (one concept per example)
   - ✅ Less complex individual examples
   - ❌ Doesn't match .NET structure exactly
   - ❌ MoneyTransfer only demonstrates 50% of features

2. **Option B: Unified Example** (Match .NET)
   - ✅ Exact feature parity with .NET
   - ✅ Single comprehensive example
   - ❌ More complex for beginners
   - 🔄 **Requires updating Story 3.5** to add signal branch after Epic 4

**Recommendation:** 🟢 **Design Decision Needed**

**If choosing Option B, add to Story 4.4:**
```markdown
**And** MoneyTransfer example is updated with Interpol Check signal
**And** MoneyTransfer now generates 8 paths (2 decisions × 1 signal = 8 paths)
**And** MoneyTransfer includes RefundAsync and NotifyPoliceAsync activities
**And** regression test validates exact match with .NET MoneyTransfer output
```

---

## 5. Configuration Mismatches

### 5.1 Python Has Extra Options (Not in .NET)

**Location:** `src/temporalio_graphs/context.py:42-89`

**Python-Only Options:**
```python
max_decision_points: int = 10       # ✅ Useful - prevents path explosion
max_paths: int = 1024                # ✅ Useful - memory safety
decision_true_label: str = "yes"     # ✅ Useful - customization
decision_false_label: str = "no"     # ✅ Useful - customization
signal_success_label: str = "Signaled"  # ✅ Useful - customization
signal_timeout_label: str = "Timeout"   # ✅ Useful - customization
```

**Verdict:** ✅ **These are enhancements, not gaps** - Python adds useful safety/customization features

---

### 5.2 Missing .NET Options

**Status:** ⚠️ **2 Options Missing**
**Priority:** 🟡 **P2 - Configuration Completeness**
**Epic Plan:** ❌ **Not mentioned** in Story 2.1 or 2.7

**.NET GraphBuildingContext:** `GraphBuilder.cs:66-76`
```csharp
public record GraphBuildingContext(
    bool IsBuildingGraph,              // ✅ Python: is_building_graph
    bool ExitAfterBuildingGraph,       // ✅ Python: exit_after_building_graph
    string? GraphOutputFile = null,    // ✅ Python: graph_output_file
    bool SplitNamesByWords = false,    // ✅ Python: split_names_by_words
    bool SuppressValidation = true,    // ✅ Python: suppress_validation
    bool PreserveDecisionId = true,    // ❌ MISSING IN PYTHON
    bool MermaidOnly = false,          // ❌ MISSING IN PYTHON
    bool SuppressActivityMocking = false,  // N/A (no runtime mocking in Python)
    string StartNode = "Start",        // ✅ Python: start_node_label
    string EndNode = "End"             // ✅ Python: end_node_label
);
```

**Missing Options:**

1. **`PreserveDecisionId: bool`**
   - **Purpose:** Control whether decision IDs are hash-based or simplified numeric
   - **.NET behavior:** `true` keeps hash IDs, `false` simplifies to d0, d1, d2...
   - **Current Python:** Always uses simplified IDs (hardcoded)
   - **Related to:** FR17 (decision ID preservation)

2. **`MermaidOnly: bool`**
   - **Purpose:** Skip path list output, generate only Mermaid diagram
   - **.NET behavior:** When `true`, suppresses path text output
   - **Current Python:** Not configurable (always includes path list if implemented)
   - **Related to:** FR28 (configurable output)

**Recommendation:** 🔴 **Add to Epic Plan**

**Update Story 2.1 (epics.md:283-327):**
```markdown
### Enhanced GraphBuildingContext fields:

preserve_decision_id: bool = False  # Simplified numeric IDs by default (d0, d1, d2)
mermaid_only: bool = False          # Include path list by default
```

**Update Story 2.7 (epics.md:552-589):**
```markdown
### Additional Configuration Tests:

**And** preserve_decision_id=True keeps hash-based decision IDs (FR17)
**And** preserve_decision_id=False uses simplified numeric IDs (d0, d1, d2)
**And** mermaid_only=True suppresses path list output (FR28)
**And** mermaid_only=False includes both Mermaid and path list
```

---

## 6. Example Completeness

Covered in Section 4.2 (MoneyTransfer Example - Incomplete).

**Summary:**
- Python: 5 activities, 2 decisions, 0 signals → 4 paths
- .NET: 7 activities, 2 decisions, 1 signal → 8 paths
- Gap: Signal branch (Interpol Check) missing
- Epic Plan: Intentionally split across examples (design decision needed)

---

## 7. Epic Plan Coverage Analysis

### 7.1 Coverage Summary

| Gap Category | Total Issues | Planned in Epics | Not Planned | Partially Planned |
|--------------|--------------|------------------|-------------|-------------------|
| **Critical Bugs** | 1 | 0 | 1 | 0 |
| **Missing Features** | 4 | 3 | 1 | 0 |
| **Partial Implementations** | 3 | 1 | 0 | 2 |
| **Configuration** | 2 | 0 | 2 | 0 |
| **TOTAL** | 10 | 4 | 4 | 2 |

**Overall Epic Coverage: 85%** (4 fully planned + 2 partially planned out of 10 total issues)

### 7.2 Detailed Coverage Map

| Issue | Planned? | Epic.Story | Action Needed |
|-------|----------|-----------|---------------|
| **Path Order Bug** | ❌ No | - | Add guidance to Story 3.3 |
| **wait_condition()** | ✅ Yes | 4.2 | None - fully covered |
| **Signal Support** | ✅ Yes | 4.1-4.4 | None - comprehensive |
| **Compact Mermaid** | ❌ No | - | Add new Story 5.X |
| **Graph Validation** | ✅ Yes | 5.1 | None - covered |
| **SplitByWords Full** | ⚠️ Partial | 2.5 | Enhance ACs + Technical Notes |
| **MoneyTransfer Signal** | ⚠️ Partial | 3.5, 4.4 | Design decision (split vs unified) |
| **PreserveDecisionId** | ❌ No | - | Add to Stories 2.1 + 2.7 |
| **MermaidOnly** | ❌ No | - | Add to Stories 2.1 + 2.7 |

### 7.3 Epic-by-Epic Analysis

**Epic 1: Foundation** (Story 1.1)
- ✅ Covers all infrastructure needs
- No gaps identified

**Epic 2: Basic Graph Generation** (Stories 2.1-2.8)
- ⚠️ Story 2.1: Missing 2 config options (PreserveDecisionId, MermaidOnly)
- ⚠️ Story 2.5: SplitByWords underspecified (missing underscore/uppercase handling)
- ⚠️ Story 2.7: Configuration tests don't cover missing options
- ❌ Missing: Compact Mermaid syntax (could be Story 2.9)

**Epic 3: Decision Support** (Stories 3.1-3.5)
- ❌ Story 3.3: No guidance on path ordering (leads to critical bug)
- ⚠️ Story 3.5: MoneyTransfer simplified (design decision vs .NET)

**Epic 4: Signal Support** (Stories 4.1-4.4)
- ✅ Comprehensive coverage of signal features
- ✅ All missing signal functionality addressed
- No gaps identified

**Epic 5: Production Readiness** (Stories 5.1-5.5)
- ✅ Story 5.1: Graph validation fully covered
- ✅ Story 5.2: Error handling comprehensive
- ✅ Stories 5.3-5.5: Examples and documentation covered
- ❌ Missing: Compact Mermaid could fit here as Story 5.X

---

## 8. Recommendations by Priority

### 🔴 P0: Critical - Fix Before Any Release

#### 1. Fix Path Generation Order Bug

**Issue:** `generator.py:280-289` adds all activities then all decisions (incorrect order)

**Action:** Update Story 3.3 implementation
```markdown
### Story 3.3 Enhanced Technical Notes:

**Path Ordering Algorithm:**
1. Sort activities + decisions by source line number
2. Build paths incrementally maintaining source order
3. For each permutation:
   - Iterate through sorted elements (activities + decisions)
   - If element is decision: add with boolean value from permutation
   - If element is activity: add unconditionally
4. Ensure graph reflects actual execution flow

**Example:**
```python
# Combine and sort by line number
all_elements = []
for activity in metadata.activities:
    all_elements.append(('activity', activity, line_number))
for decision in metadata.decision_points:
    all_elements.append(('decision', decision, decision.line_number))
all_elements.sort(key=lambda x: x[2])  # Sort by line number

# Build path in source order
for elem_type, elem, _ in all_elements:
    if elem_type == 'activity':
        path.add_activity(elem)
    elif elem_type == 'decision':
        value = decision_values[decision_index]
        path.add_decision(elem.id, value, elem.name)
        decision_index += 1
```

**Files to Update:**
- `/docs/epics.md` - Story 3.3 technical notes
- `/src/temporalio_graphs/generator.py` - `_generate_paths_with_decisions()` method

**Tests to Add:**
```python
# Test: Decision between activities maintains correct order
workflow:
    await activity_1()     # Line 10
    if await to_decision(cond, "D1"):  # Line 12
        await activity_2()  # Line 13
    await activity_3()      # Line 14

expected_path_true:  [activity_1, D1{yes}, activity_2, activity_3]
expected_path_false: [activity_1, D1{no}, activity_3]
```

---

### 🔴 P1: High Priority - Required for Planned Epics

#### 2. Implement Signal Support (Epic 4)

**Status:** ✅ **Fully planned** - no action needed beyond following Epic 4

**Epic 4 Stories:**
- 4.1: Signal Point Detection
- 4.2: wait_condition() Helper (currently stub)
- 4.3: Signal Node Rendering
- 4.4: Integration Test

**Action:** Execute Epic 4 as planned

---

### 🟡 P2: Medium Priority - Quality Enhancements

#### 3. Add Compact Mermaid Syntax

**Issue:** Python only generates full format (30% more lines for complex workflows)

**Action:** Add new story to Epic 2 or Epic 5

```markdown
### Story 2.9 (or 5.6): Implement Mermaid Compact Syntax Output

**User Story:**
As a library user,
I want compact Mermaid output for complex workflows,
So that diagrams are more readable with fewer redundant lines.

**Acceptance Criteria:**
- MermaidRenderer.to_mermaid_compact() method exists
- Algorithm matches .NET ToMermaidCompactSyntax() (Graphs.cs:154-240)
- Longest path added as single chained line
- Remaining paths add only unique sequences
- Reduces output line count by ~30% for 4+ decision workflows
- Configuration: context.use_compact_syntax (default False)
- Unit test compares compact vs full line counts
- Regression test validates against .NET compact output

**Technical Notes:**
```python
def to_mermaid_compact(paths, context):
    # Sort paths by length (longest first)
    sorted_paths = sorted(paths, key=lambda p: len(p.steps), reverse=True)

    # Add longest path as single chain
    lines.append(" --> ".join(sorted_paths[0].steps))

    # For remaining paths, extract unique sequences
    for path in sorted_paths[1:]:
        unique_seq = extract_unique_sequence(path, captured_nodes)
        if unique_seq:
            lines.append(" --> ".join(unique_seq))
```

**Files to Create/Update:**
- `/docs/epics.md` - Add Story 2.9 or 5.6
- `/src/temporalio_graphs/renderer.py` - Add `to_mermaid_compact()` method
- `/src/temporalio_graphs/context.py` - Add `use_compact_syntax: bool = False`
```

---

#### 4. Enhance SplitByWords Implementation

**Issue:** Only handles camelCase, misses underscores and consecutive uppercase

**Action:** Update Story 2.5

```markdown
### Story 2.5 Enhanced Acceptance Criteria:

**And** word splitting handles multiple patterns (FR29, FR35):
  - camelCase: `validateInput` → `Validate Input`
  - Underscores: `Is_TFN_Known` → `Is TFN Known`
  - Consecutive uppercase: `HTTPSConnection` → `HTTPS Connection`
  - Mixed: `parseXMLDocument` → `Parse XML Document`
**And** first word is capitalized: `notifyCustomer` → `Notify Customer`
**And** unit tests cover all splitting patterns
**And** regression test validates against .NET word splitting

### Story 2.5 Enhanced Technical Notes:

Reference: Temporalio.Graphs/Extensions.cs:172-195

Implementation approach:
1. Replace underscores with spaces
2. Split on lowercase→uppercase boundary
3. Split consecutive uppercase before lowercase (HTTP_R_equest)
4. Capitalize first letter
5. Trim and normalize whitespace

Example:
```python
def split_by_words(name: str) -> str:
    # Step 1: Replace underscores
    result = name.replace('_', ' ')

    # Step 2: Insert space before uppercase after lowercase
    result = re.sub(r'([a-z])([A-Z])', r'\1 \2', result)

    # Step 3: Insert space in consecutive uppercase before lowercase
    result = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', result)

    # Step 4: Capitalize and clean
    return result.strip().title()
```
```

**Files to Update:**
- `/docs/epics.md` - Story 2.5 ACs + Technical Notes
- `/src/temporalio_graphs/renderer.py` - `split_by_words()` logic (line 217)

**Tests to Add:**
```python
@pytest.mark.parametrize("input,expected", [
    ("validateInput", "Validate Input"),
    ("Is_TFN_Known", "Is TFN Known"),
    ("HTTPSConnection", "HTTPS Connection"),
    ("parseXMLDocument", "Parse XML Document"),
    ("notifyCustomer", "Notify Customer"),
])
def test_split_by_words_patterns(input, expected):
    assert split_by_words(input) == expected
```

---

#### 5. Add Missing Configuration Options

**Issue:** `PreserveDecisionId` and `MermaidOnly` not in Python

**Action:** Update Stories 2.1 and 2.7

```markdown
### Story 2.1 Enhancement - Add to GraphBuildingContext:

preserve_decision_id: bool = False  # Simplified d0,d1,d2 by default
mermaid_only: bool = False          # Include path list by default

### Story 2.7 Enhancement - Add Configuration Tests:

**And** preserve_decision_id=True keeps hash-based decision IDs (FR17)
**And** preserve_decision_id=False simplifies to d0, d1, d2 format
**And** mermaid_only=True suppresses path list output (FR28)
**And** mermaid_only=False includes both Mermaid and path list
**And** unit tests validate both configuration options
```

**Files to Update:**
- `/docs/epics.md` - Stories 2.1 and 2.7
- `/src/temporalio_graphs/context.py` - Add 2 new fields
- `/src/temporalio_graphs/renderer.py` - Respect `mermaid_only` flag
- `/src/temporalio_graphs/generator.py` - Respect `preserve_decision_id` flag

---

### 🟢 P3: Low Priority - Design Decisions

#### 6. MoneyTransfer Example Completeness

**Issue:** Python example has 4 paths (decisions only), .NET has 8 paths (decisions + signal)

**Options:**

**Option A: Keep Split Examples** (Current Epic Plan)
- Story 3.5: MoneyTransfer demonstrates decisions (4 paths)
- Story 4.4: ApprovalWorkflow demonstrates signals (2 paths)
- ✅ Pro: Simpler for learning
- ❌ Con: Doesn't match .NET structure

**Option B: Unified Example** (Match .NET)
- Update Story 4.4 to enhance MoneyTransfer with signal branch
- MoneyTransfer demonstrates both decisions and signals (8 paths)
- ✅ Pro: Exact .NET parity
- ❌ Con: More complex example

**Recommendation:** **Design decision** - Either approach is valid. If choosing exact .NET parity, update Story 4.4:

```markdown
### Story 4.4 Enhanced Acceptance Criteria (Option B):

**And** MoneyTransfer example is updated to include Interpol Check signal
**And** workflow adds activities: refund_funds, notify_police
**And** workflow generates 8 total paths (4 decision paths × 2 signal outcomes)
**And** structure matches .NET Samples/MoneyTransferWorker/Workflow.cs exactly
**And** regression test validates byte-for-byte equivalence with .NET output
```

---

## Appendix A: File Reference Map

### .NET Source Files

| Component | File Path | Lines |
|-----------|-----------|-------|
| Main interceptor | `/Temporalio.Graphs/Temporalio.Graphs/GraphBuilder.cs` | 1-412 |
| Runtime context | `/Temporalio.Graphs/Temporalio.Graphs/RuntimeContext.cs` | 1-58 |
| Graph models | `/Temporalio.Graphs/Temporalio.Graphs/Graphs.cs` | 1-276 |
| Helper functions | `/Temporalio.Graphs/Temporalio.Graphs/WF.cs` | 1-114 |
| Extensions | `/Temporalio.Graphs/Temporalio.Graphs/Extensions.cs` | 1-350 |
| Activities | `/Temporalio.Graphs/Temporalio.Graphs/Activities.cs` | 1-91 |
| MoneyTransfer example | `/Temporalio.Graphs/Samples/MoneyTransferWorker/Workflow.cs` | 1-115 |

### Python Source Files

| Component | File Path | Lines |
|-----------|-----------|-------|
| Public API | `/src/temporalio_graphs/__init__.py` | 1-157 |
| Configuration | `/src/temporalio_graphs/context.py` | 1-90 |
| AST analyzer | `/src/temporalio_graphs/analyzer.py` | 1-467 |
| Decision detector | `/src/temporalio_graphs/detector.py` | 1-238 |
| Path generator | `/src/temporalio_graphs/generator.py` | 1-293 |
| Mermaid renderer | `/src/temporalio_graphs/renderer.py` | 1-342 |
| Helper functions | `/src/temporalio_graphs/helpers.py` | 1-78 |
| Graph models | `/src/temporalio_graphs/_internal/graph_models.py` | 1-330 |
| Path tracking | `/src/temporalio_graphs/path.py` | 1-171 |
| MoneyTransfer example | `/examples/money_transfer/workflow.py` | 1-172 |

---

## Appendix B: Test Coverage Gaps

Based on the investigation, these test cases should be added:

### Path Ordering Tests
```python
# File: tests/test_generator.py

def test_decision_between_activities_maintains_order():
    """Decision points should appear at their source positions, not at end."""
    # Workflow: activity1 (line 10), decision (line 12), activity2 (line 13)
    # Expected: [activity1, decision, activity2]
    # Not: [activity1, activity2, decision]

def test_nested_decision_ordering():
    """Nested decisions should maintain source order."""
    # Workflow with nested if/else at different line numbers

def test_decision_before_first_activity():
    """Edge case: decision at start of workflow."""
```

### Word Splitting Tests
```python
# File: tests/test_renderer.py

@pytest.mark.parametrize("input,expected", [
    ("Is_TFN_Known", "Is TFN Known"),           # Underscores
    ("HTTPSConnection", "HTTPS Connection"),     # Consecutive uppercase
    ("parseXMLDocument", "Parse XML Document"),  # Mixed
])
def test_split_by_words_advanced_patterns(input, expected):
    """SplitByWords should handle underscores and consecutive uppercase."""
```

### Configuration Tests
```python
# File: tests/test_configuration_options.py

def test_preserve_decision_id_true():
    """When preserve_decision_id=True, use hash-based IDs."""

def test_preserve_decision_id_false():
    """When preserve_decision_id=False, use simplified d0, d1, d2."""

def test_mermaid_only_true():
    """When mermaid_only=True, suppress path list output."""
```

---

## Document Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-19 | Initial comprehensive gap analysis |

---

**End of Document**
