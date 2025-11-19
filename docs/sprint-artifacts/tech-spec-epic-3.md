# Epic Technical Specification: Decision Node Support (Branching Workflows)

Date: 2025-11-18
Author: Luca
Epic ID: 3
Status: Draft

---

## Overview

Epic 3 extends the temporalio-graphs library from linear workflow visualization to branching workflow visualization with complete path coverage. This epic implements decision node support, enabling the library to detect conditional logic (if/else, elif chains, ternary operators) in workflows and generate all possible execution paths (2^n paths for n decisions). The implementation adds the `to_decision()` helper function for marking decision points, AST-based decision detection, path permutation generation using combinatorial logic, and Mermaid diamond-shape rendering for decision nodes. This epic delivers the critical capability to visualize real-world workflows with conditional branching, showing users ALL possible execution paths rather than just linear sequences.

## Objectives and Scope

**Primary Objectives:**
- Implement `to_decision()` helper function for marking boolean expressions as decision nodes
- Build DecisionDetector to identify decision points in workflow AST
- Extend PathPermutationGenerator to create 2^n execution path permutations for n decisions
- Implement decision node rendering in Mermaid with diamond shape syntax `{DecisionName}`
- Port and validate MoneyTransfer example workflow from .NET showing 2 decisions = 4 paths

**In Scope:**
- FR11-FR17: Complete decision node support (helper function, custom names, branch labels, diamond shapes, permutations)
- FR46: elif chain detection (multiple sequential decisions)
- FR47: Ternary operator detection wrapped in to_decision()
- FR49: Reconverging branch handling in path generation
- Simple if/else conditionals and nested decisions
- Path explosion safeguards (max_decision_points limit, default 10)
- Decision node ID generation (deterministic hashing or sequential)
- Integration testing with MoneyTransfer workflow (2 decisions, 4 paths)

**Out of Scope (Future Epics):**
- Signal/wait condition support (Epic 4)
- Loop detection and visualization (Post-MVP growth features)
- Dynamic decision detection without to_decision() marker
- Complex control flow patterns (match/case statements, exception branching)
- Runtime-based decision tracking (static analysis only)

## System Architecture Alignment

**Alignment to Static Analysis Architecture:**
This epic builds directly on the AST-based static analysis foundation from Epic 2. The DecisionDetector extends the existing WorkflowAnalyzer (ast.NodeVisitor) pattern to identify `to_decision()` function calls during AST traversal. This aligns with ADR-001 (Static Analysis vs Runtime Interceptors) - we analyze code structure without executing workflows.

**Core Component Integration:**
- **DecisionDetector** (new): Visits ast.Call nodes, identifies to_decision() calls, extracts decision metadata
- **PathPermutationGenerator** (enhanced): Extends from linear path generation (Epic 2) to combinatorial permutation using itertools.product
- **MermaidRenderer** (enhanced): Adds NodeType.DECISION handling, renders diamond shapes, adds branch labels
- **GraphBuildingContext** (existing): Already includes max_decision_points, decision_true_label, decision_false_label configuration

**Performance Constraints:**
- NFR-PERF-1: 5 decisions (32 paths) must generate in <1 second
- NFR-PERF-1: 10 decisions (1024 paths) must generate in <5 seconds
- ADR-008: Default max_decision_points = 10 prevents path explosion (2^10 = 1024 paths)
- Path generation uses itertools.product for efficient O(2^n) permutation with early validation

**Data Flow:**
```
workflow.py → AST Parser → DecisionDetector → WorkflowMetadata.decision_points
                                                         ↓
WorkflowMetadata → PathPermutationGenerator → 2^n GraphPath objects
                                                         ↓
GraphPath[] → MermaidRenderer → Mermaid syntax with diamond decision nodes
```

## Detailed Design

### Services and Modules

{{services_modules}}

### Data Models and Contracts

{{data_models}}

### APIs and Interfaces

{{apis_interfaces}}

### Workflows and Sequencing

{{workflows_sequencing}}

## Non-Functional Requirements

### Performance

{{nfr_performance}}

### Security

{{nfr_security}}

### Reliability/Availability

{{nfr_reliability}}

### Observability

{{nfr_observability}}

## Dependencies and Integrations

{{dependencies_integrations}}

## Acceptance Criteria (Authoritative)

{{acceptance_criteria}}

## Traceability Mapping

{{traceability_mapping}}

## Risks, Assumptions, Open Questions

{{risks_assumptions_questions}}

## Test Strategy Summary

{{test_strategy}}
