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

- [ ] Define `ChildWorkflowCall` data model
  - [ ] Add `ChildWorkflowCall` dataclass to `src/temporalio_graphs/_internal/graph_models.py` with fields: `workflow_name`, `call_site_line`, `call_id`, `parent_workflow`.
  - [ ] Add `NodeType.CHILD_WORKFLOW` to `NodeType` enum in `src/temporalio_graphs/_internal/graph_models.py`.
- [ ] Implement `ChildWorkflowDetector`
  - [ ] Create `ChildWorkflowDetector` class in `src/temporalio_graphs/detector.py`.
  - [ ] Implement `detect(tree: ast.Module)` method to visit `Call` nodes.
  - [ ] Implement logic to identify `workflow.execute_child_workflow` pattern.
  - [ ] Implement extraction logic for both class reference and string literal arguments.
- [ ] Update `WorkflowAnalyzer` integration
  - [ ] Ensure `WorkflowAnalyzer` invokes `ChildWorkflowDetector` (or exposes AST for it).
  - [ ] Store detected child calls in `WorkflowMetadata`.
- [ ] Add Unit Tests
  - [ ] Create `tests/test_detector.py` (or update existing) with test cases for:
    - [ ] Class reference detection.
    - [ ] String literal detection.
    - [ ] Multiple calls in one workflow.
    - [ ] Calls inside control structures.

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

### File List
