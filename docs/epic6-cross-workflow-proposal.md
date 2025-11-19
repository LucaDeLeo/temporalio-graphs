# Sprint Change Proposal: Add Cross-Workflow Visualization Support (Epic 6)

**Project:** temporalio-graphs-python-port
**Date:** 2025-11-19
**Author:** Bob (Scrum Master)
**Sponsor:** Luca (Bounty Sponsor Request)
**Status:** ✅ APPROVED

---

## Executive Summary

The bounty sponsor has requested "cross-workflow support, end to end." This proposal adds Epic 6: Cross-Workflow Visualization to enable parent-child workflow relationships and complete end-to-end execution flow analysis.

**Approved Plan:**
- Complete Epic 5 (Production Readiness) first
- Add Epic 6 as "MVP Extension" (5 stories, 8 new FRs)
- Timeline: +1 week after v0.1.0 release
- Version: v0.1.0 (Core MVP) → v0.2.0 (MVP Extension)

---

## 1. Issue Summary

### Problem
Library currently analyzes single workflows only. Real-world Temporal apps use parent-child workflow patterns (`workflow.execute_child_workflow()`). Cannot visualize complete end-to-end flows spanning multiple workflows.

### Trigger
Bounty sponsor requirement for "cross-workflow support, end to end"

### Impact
- Cannot visualize parent-child workflow relationships
- Missing workflow call graphs for multi-workflow applications
- Limits adoption for production Temporal applications

---

## 2. Epic Impact

### Current Status
- Epics 1-4: Complete ✅
- Epic 5: 40% complete (2/5 stories done)

### Changes Required
- **Epic 5:** Continue unchanged
- **Epic 6 (NEW):** Cross-Workflow Visualization
  - Story 6.1: Detect Child Workflow Calls (3h)
  - Story 6.2: Child Workflow Node Rendering (3h)
  - Story 6.3: Multi-Workflow Analysis Pipeline (5h)
  - Story 6.4: End-to-End Path Generation (4h)
  - Story 6.5: Integration Test with Example (3h)

---

## 3. Artifact Impact

| Artifact | Changes |
|----------|---------|
| PRD | Add FR66-FR73 (8 new FRs), clarify MVP scope |
| Architecture | Add WorkflowCallGraphAnalyzer, new data models, ADR-011 |
| Epics Doc | Add Epic 6 specification |
| Tests | Parent-child fixtures, integration tests |
| Examples | examples/parent_child_workflow/ |
| Docs | README, API reference updates |

---

## 4. Recommended Approach

**Hybrid: Direct Adjustment + MVP Scope Clarification**

### Phase 1: Complete Epic 5 (10-15h)
- Stories 5-3, 5-4, 5-5
- Deliverable: v0.1.0 (Core MVP)

### Phase 2: Update Artifacts (4-5h, concurrent)
- Update PRD, Architecture, Epics documents

### Phase 3: Implement Epic 6 (20-25h)
- 5 stories for cross-workflow support
- Deliverable: v0.2.0 (MVP Extension)

**Total: ~35-45 hours (~1 week)**

---

## 5. Implementation Handoff

### Agent Responsibilities

**Scrum Master (sm):**
- Update PRD, Epics doc, sprint-status.yaml
- Coordinate handoffs

**Solution Architect (architect):**
- Design WorkflowCallGraphAnalyzer
- Write ADR-011
- Update Architecture document

**Developer (dev):**
- Complete Epic 5
- Implement Epic 6
- Create parent-child example

---

## 6. MVP Definition

**Core MVP (v0.1.0):** Epics 1-5 (65 FRs) - UNCHANGED
**MVP Extension (v0.2.0):** Epic 6 (8 FRs) - NEW
**Total:** 6 epics, 28 stories, 73 FRs

---

## 7. Timeline

- Epic 5: ~1-2 days
- Artifacts: concurrent
- Epic 6: ~3-4 days
- **Total extension:** ~1 week

---

## Approval

**Status:** ✅ APPROVED by Luca (2025-11-19)

**Next Steps:**
1. SM: Update PRD, Epics doc
2. Architect: Update Architecture, write ADR-011
3. Dev: Continue Epic 5, then Epic 6

---

_Generated with BMAD Correct Course Workflow_
_Scrum Master: Bob_
_Project: temporalio-graphs-python-port_
