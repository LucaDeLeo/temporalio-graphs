# API Export Decision - Public API Scope for v0.1.0

**Date:** 2025-11-19
**Context:** Review findings from 2025-11-19 fix plan implementation
**Related Issue:** Fix Plan Issue #1 - Public API Export Mismatch
**Related Epic:** Epic 6 - Cross-Workflow Visualization

---

## Executive Summary

**Decision:** Keep minimal public API surface with **11 symbols in `__all__`** (Option A)

**Impact:** Epic 6 features (`analyze_workflow_graph()` and `MultiWorkflowPath`) remain accessible via direct import but are NOT included in the public `__all__` exports for v0.1.0.

**Rationale:** Conservative approach for newly-completed Epic 6 functionality. Public API expansion deferred to v0.2.0 after stabilization period.

---

## Background

### The Issue

Epic 6 (Cross-Workflow Visualization) introduced two new top-level exports:
- `analyze_workflow_graph()` - Multi-workflow analysis entry point
- `MultiWorkflowPath` - Data model for cross-workflow execution paths

The existing test `test_public_api_clean_minimal_export` expected exactly **11 symbols** in `__all__`, but the implementation had grown to **13 symbols** after Epic 6 completion.

### Options Considered

From `docs/review-2025-11-19-fix-plan.md`:

**Option A: Shrink `__all__` (Conservative)**
- Remove `analyze_workflow_graph` and `MultiWorkflowPath` from public API
- Keep these as internal/experimental features
- Maintains minimal API surface
- **Pros:** Simpler API, backward compatible, easier to maintain
- **Cons:** Users can't access Epic 6 features via public API

**Option B: Update Test Contract (Expansive)**
- Update test to expect 13 symbols
- Document that Epic 6 expanded the public API
- Add symbols to API reference docs
- Requires version bump and CHANGELOG entry
- **Pros:** Makes Epic 6 features officially public
- **Cons:** Larger API surface to maintain, commits to stability

---

## Decision: Option A (Conservative)

### Chosen Approach

**Keep `__all__` at 11 symbols:**
```python
__all__ = [
    "GraphBuildingContext",
    "analyze_workflow",",
    "to_decision",
    "wait_condition",
    "ValidationWarning",
    "ValidationReport",
    "TemporalioGraphsError",
    "WorkflowParseError",
    "UnsupportedPatternError",
    "GraphGenerationError",
    "InvalidDecisionError",
]
```

**NOT exported (available via direct import):**
```python
# Still accessible but not in __all__
from temporalio_graphs import analyze_workflow_graph  # Works
from temporalio_graphs._internal.graph_models import MultiWorkflowPath  # Works
```

### Rationale

1. **Epic 6 is new** - Just completed, needs stabilization period
2. **Minimal API principle** - Easier to add symbols later than remove them
3. **Backward compatibility** - No breaking changes for existing users
4. **Test stability** - Maintains existing test contract
5. **Flexibility** - Can promote to public API in v0.2.0 after validation

### Supporting Evidence

**From fix plan review:**
> "Chose conservative Option A (minimal API surface). No breaking changes to existing API. Clean implementation."

**Test result:**
```bash
tests/test_public_api.py::test_public_api_clean_minimal_export PASSED
```

---

## Impact Assessment

### For Users

**Current State (v0.1.0):**
- Core workflow analysis: ✅ Fully supported via `analyze_workflow()`
- Single workflow visualization: ✅ Public API
- Multi-workflow analysis: ⚠️ Available but requires direct import
- Cross-workflow paths: ⚠️ Available but requires direct import

**User Workaround:**
```python
# Option 1: Direct import (works today)
from temporalio_graphs import analyze_workflow_graph

# Option 2: Wait for v0.2.0 when it may be in __all__
```

### For Maintainers

**Benefits:**
- Smaller public API surface = fewer stability commitments
- Can iterate on Epic 6 APIs without breaking changes
- Clearer separation: stable (Epic 1-5) vs experimental (Epic 6)
- Easier to document and support minimal API

**Trade-offs:**
- Epic 6 features feel "second-class"
- Users may not discover multi-workflow capabilities
- Need to communicate this explicitly in docs

---

## Future Plans

### v0.2.0 Consideration

After Epic 6 stabilization period (estimated 2-3 months), **re-evaluate** adding to `__all__`:

**Criteria for promotion to public API:**
1. No bugs reported in Epic 6 functionality
2. API design validated by real-world usage
3. Documentation complete (tutorial, examples, API reference)
4. Integration tests comprehensive
5. Performance validated at scale

**If criteria met:**
- Add `analyze_workflow_graph` and `MultiWorkflowPath` to `__all__`
- Bump version to v0.2.0 (minor version, new public APIs)
- Update CHANGELOG with API expansion note
- Update test to expect 13 symbols

---

## Implementation Notes

### Code Changes

**File:** `src/temporalio_graphs/__init__.py:35-47`

No changes required - `__all__` already has 11 symbols.

### Test Changes

**File:** `tests/test_public_api.py`

No changes required - test expects 11 symbols and passes.

### Documentation Changes

**This file:** Decision record created ✅
**CHANGELOG.md:** Updated with API stability note ✅
**docs/api-reference.md:** Migration note added for .NET users ✅

---

## Approval

**Decided by:** Development team (Luca + Claude Code)
**Date:** 2025-11-19
**Approval process:** Fix plan review and retrospective
**PO sign-off:** Implicit (chose conservative option, no breaking changes)

---

## References

- Fix Plan: `docs/review-2025-11-19-fix-plan.md` (Issue #1)
- Review: `docs/review-2025-11-19.md`
- Epic 6 Spec: `docs/sprint-artifacts/tech-spec-epic-6.md`
- Test: `tests/test_public_api.py::test_public_api_clean_minimal_export`

---

**Status:** ✅ Implemented and documented
**Next Review:** Before v0.2.0 release (consider promoting Epic 6 to public API)
