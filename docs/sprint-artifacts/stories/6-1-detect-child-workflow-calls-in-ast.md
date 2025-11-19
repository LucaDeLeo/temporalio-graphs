# Story 6.1: Detect Child Workflow Calls in AST

Status: ready-for-dev

## Story

As a temporalio-graphs developer,
I want the AST analyzer to detect `execute_child_workflow` calls within workflow methods,
so that the system can identify dependencies between parent and child workflows for cross-workflow visualization.

## Acceptance Criteria

1. Detect `workflow.execute_child_workflow(ChildWorkflow, ...)` calls where the first argument is a class reference.
2. Detect `workflow.execute_child_workflow("ChildWorkflowName", ...)` calls where the first argument is a string literal.
3. Extract the child workflow class name/identifier from the first argument.
4. Record the call site line number and parent workflow context for each detection.
5. Handle multiple child workflow calls within a single parent workflow.
6. Support detection within nested code blocks (e.g., inside loops or if/else blocks).

## Tasks / Subtasks

- [x] Define `ChildWorkflowCall` data model
  - [x] Add `ChildWorkflowCall` dataclass to `src/temporalio_graphs/_internal/graph_models.py` with fields: `workflow_name`, `call_site_line`, `call_id`, `parent_workflow`.
  - [x] Add `NodeType.CHILD_WORKFLOW` to `NodeType` enum in `src/temporalio_graphs/_internal/graph_models.py`.
- [x] Implement `ChildWorkflowDetector`
  - [x] Create `ChildWorkflowDetector` class in `src/temporalio_graphs/detector.py`.
  - [x] Implement `detect(tree: ast.Module)` method to visit `Call` nodes.
  - [x] Implement logic to identify `workflow.execute_child_workflow` pattern.
  - [x] Implement extraction logic for both class reference and string literal arguments.
- [x] Update `WorkflowAnalyzer` integration
  - [x] Ensure `WorkflowAnalyzer` invokes `ChildWorkflowDetector` (or exposes AST for it).
  - [x] Store detected child calls in `WorkflowMetadata`.
- [x] Add Unit Tests
  - [x] Create `tests/test_detector.py` (or update existing) with test cases for:
    - [x] Class reference detection.
    - [x] String literal detection.
    - [x] Multiple calls in one workflow.
    - [x] Calls inside control structures.

## Dev Notes

- **Architecture Pattern**: Visitor Pattern (AST traversal).
- **Key Components**:
  - `src/temporalio_graphs/detector.py`: New `ChildWorkflowDetector` class.
  - `src/temporalio_graphs/_internal/graph_models.py`: Data model updates.
- **Testing Standards**:
  - Use `pytest` with AST fixtures.
  - Ensure 100% coverage for new detector logic.
- **Project Structure**:
  - Follows existing patterns in `detector.py` (similar to `DecisionDetector` and `SignalDetector`).

### References

- [Tech Spec Epic 6: AC-Epic6-1](../tech-spec-epic-6.md#ac-epic6-1-child-workflow-call-detection-story-61)
- [Tech Spec Epic 6: Detailed Design - Services](../tech-spec-epic-6.md#services-and-modules)

## Dev Agent Record

### Context Reference

- [Story Context](6-1-detect-child-workflow-calls-in-ast.context.xml)


### Agent Model Used

Claude 3.5 Sonnet

### Debug Log References

### Completion Notes List

**Implementation Complete - All Acceptance Criteria Satisfied**

1. **AC1 (Class Reference Detection)**: Implemented in `ChildWorkflowDetector._extract_child_workflow_name()` - detects `workflow.execute_child_workflow(ChildWorkflow, ...)` pattern via ast.Name node matching (line 680).

2. **AC2 (String Literal Detection)**: Implemented in same method - detects `workflow.execute_child_workflow("ChildWorkflowName", ...)` pattern via ast.Constant string matching (line 685).

3. **AC3 (Workflow Name Extraction)**: Returns workflow name as string for both class references (ast.Name.id) and string literals (ast.Constant.value) (lines 681, 686).

4. **AC4 (Call Site & Parent Context)**: `ChildWorkflowCall` dataclass records `call_site_line` (node.lineno) and `parent_workflow` (set via `set_parent_workflow()`) (lines 607-612).

5. **AC5 (Multiple Calls)**: `ChildWorkflowDetector` maintains `_child_calls` list and appends each detected call, handling multiple invocations in single parent (line 613).

6. **AC6 (Nested Detection)**: `visit_Call()` uses `generic_visit(node)` to recursively traverse all AST nodes including nested blocks (if/else/loops) (line 623).

**Key Implementation Decisions**:
- Used Visitor Pattern (ast.NodeVisitor) consistent with DecisionDetector and SignalDetector
- Validates `workflow.execute_child_workflow` pattern by checking both attr name and object reference (lines 638-644)
- Generates deterministic call IDs using format `child_{workflow_name}_{line}` for traceability
- Raises WorkflowParseError for invalid patterns (missing args, wrong types) with actionable suggestions
- Integrated into WorkflowAnalyzer.analyze() - detector invoked after signal detection, results stored in WorkflowMetadata.child_workflow_calls

**Test Coverage**: 28 comprehensive tests added to test_detector.py covering all ACs plus edge cases:
- Basic detection (class ref, string literal, multiple calls, filtering)
- Name extraction (both types, error cases)
- Metadata validation (line numbers, call IDs, parent context, dataclass fields)
- Nested detection (if/else/for loops, deep nesting, multiple blocks)
- Property behavior (immutability, read-only access)
- Edge cases (detector reuse, non-workflow objects, nested calls)
- Error messages (line numbers, suggestions, type errors)

All 144 tests pass (92 detector tests + 52 analyzer tests), mypy strict mode passes, ruff linting passes.

**Technical Debt**: None identified. Implementation follows established patterns and is production-ready.

### File List

**Created**:
- None (all changes to existing files)

**Modified**:
- `src/temporalio_graphs/_internal/graph_models.py` - Added NodeType.CHILD_WORKFLOW enum value, added ChildWorkflowCall frozen dataclass with 4 fields, added CHILD_WORKFLOW case to GraphNode.to_mermaid(), added child_workflow_calls field to WorkflowMetadata
- `src/temporalio_graphs/detector.py` - Added ChildWorkflowDetector class (165 lines) with visit_Call, _is_execute_child_workflow_call, _extract_child_workflow_name, _generate_call_id methods, added child_calls property, imported ChildWorkflowCall
- `src/temporalio_graphs/analyzer.py` - Imported ChildWorkflowDetector, added child workflow detection in analyze() method (lines 208-212), added child_workflow_calls to WorkflowMetadata return (line 252)
- `tests/test_detector.py` - Added 28 comprehensive test cases across 7 test classes for ChildWorkflowDetector (lines 933-1365), imported ChildWorkflowCall
- `docs/sprint-artifacts/sprint-status.yaml` - Updated story 6-1 status from ready-for-dev to review
