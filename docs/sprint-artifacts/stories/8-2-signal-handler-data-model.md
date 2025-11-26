# Story 8.2: Signal Handler Data Model

Status: drafted

## Story

As a library developer,
I want the WorkflowMetadata to include detected signal handlers,
So that downstream components can access signal handler information for cross-workflow visualization.

## Acceptance Criteria

1. **WorkflowMetadata Extension** - WorkflowMetadata dataclass in `src/temporalio_graphs/_internal/graph_models.py` includes `signal_handlers: tuple[SignalHandler, ...] = ()` field (AC6 from Tech Spec lines 943-955)

2. **SignalHandler Import in graph_models** - The SignalHandler class is already defined in graph_models.py (completed in Story 8.1), verify it remains intact with fields: signal_name, method_name, workflow_class, source_line, node_id

3. **Analyzer Integration** - WorkflowAnalyzer in `src/temporalio_graphs/analyzer.py` integrates SignalHandlerDetector to populate signal_handlers field in returned WorkflowMetadata (AC6: "analyze_workflow() populates signal_handlers")

4. **SignalHandlerDetector Import** - analyzer.py imports SignalHandlerDetector from detector module alongside existing detectors

5. **Detector Workflow Class Context** - Analyzer calls `signal_handler_detector.set_workflow_class()` with detected workflow class name before visiting AST (following established pattern from ExternalSignalDetector)

6. **Tuple Conversion** - Signal handlers list from detector is converted to tuple for immutability: `tuple(signal_handler_detector.handlers)`

7. **Empty Default** - When workflow has no signal handlers, signal_handlers field is empty tuple () (default value maintained)

8. **Backward Compatibility** - All existing tests continue passing with no failures (signal_handlers has default value so no breaking changes)

9. **Unit Tests for Metadata** - Unit tests verify WorkflowMetadata correctly stores signal_handlers tuple with proper immutability

10. **Integration Test** - Integration test analyzes a workflow with @workflow.signal handlers and verifies signal_handlers populated in metadata

11. **Type Safety** - All changes pass mypy strict mode with complete type hints

12. **No Regressions** - All existing Epic 1-7 tests (617+) continue passing

## Tasks / Subtasks

- [ ] Extend WorkflowMetadata dataclass (AC: 1, 2, 7)
  - [ ] Add `signal_handlers: tuple[SignalHandler, ...] = ()` field to WorkflowMetadata in `src/temporalio_graphs/_internal/graph_models.py`
  - [ ] Place field after `external_signals` field for logical grouping (Epic 7 -> Epic 8 order)
  - [ ] Verify SignalHandler import exists (from Story 8.1)
  - [ ] Update docstring to document new field

- [ ] Integrate SignalHandlerDetector in analyzer (AC: 3, 4, 5, 6)
  - [ ] Add `SignalHandlerDetector` to imports from `temporalio_graphs.detector` in analyzer.py
  - [ ] Create SignalHandlerDetector instance in `analyze()` method after ExternalSignalDetector
  - [ ] Call `signal_handler_detector.set_workflow_class(self._workflow_class)` to set context
  - [ ] Call `signal_handler_detector.visit(tree)` to detect signal handlers
  - [ ] Store result: `signal_handlers = tuple(signal_handler_detector.handlers)`
  - [ ] Pass `signal_handlers=signal_handlers` to WorkflowMetadata constructor

- [ ] Add unit tests for WorkflowMetadata signal_handlers (AC: 8, 9)
  - [ ] Add test in `tests/test_graph_models.py`: `test_workflow_metadata_signal_handlers_default()`
  - [ ] Add test: `test_workflow_metadata_signal_handlers_populated()`
  - [ ] Add test: `test_workflow_metadata_signal_handlers_immutable()` (tuple is immutable)
  - [ ] Verify existing WorkflowMetadata tests still pass (backward compatibility)

- [ ] Add integration test for analyzer signal handler detection (AC: 10)
  - [ ] Create fixture workflow file with @workflow.signal handlers
  - [ ] Add test in `tests/test_analyzer.py`: `test_analyzer_detects_signal_handlers()`
  - [ ] Verify metadata.signal_handlers contains detected handlers
  - [ ] Verify handler metadata fields (signal_name, method_name, workflow_class, source_line, node_id)

- [ ] Verify no regressions (AC: 11, 12)
  - [ ] Run full test suite: `pytest -v`
  - [ ] Verify all 617+ existing tests pass
  - [ ] Run mypy strict mode: `mypy src/temporalio_graphs/`
  - [ ] Run ruff linting: `ruff check src/temporalio_graphs/`
  - [ ] Verify test coverage remains >=80%

## Dev Notes

### Architecture Patterns and Constraints

**Minimal Change Philosophy** - Story 8.1 already created the SignalHandler dataclass and SignalHandlerDetector. This story focuses solely on:
1. Adding signal_handlers field to WorkflowMetadata
2. Integrating detector into analyzer pipeline

**Established Integration Pattern** - Follow the pattern from Epic 7 (ExternalSignalDetector integration):
```python
# In analyzer.py analyze() method:
# 1. Create detector instance
external_signal_detector = ExternalSignalDetector()
# 2. Set context (workflow class)
external_signal_detector.set_source_workflow(self._workflow_class)
# 3. Visit AST
external_signal_detector.visit(tree)
# 4. Get results as tuple for immutability
external_signals = tuple(external_signal_detector.external_signals)

# Same pattern for SignalHandlerDetector:
signal_handler_detector = SignalHandlerDetector()
signal_handler_detector.set_workflow_class(self._workflow_class)
signal_handler_detector.visit(tree)
signal_handlers = tuple(signal_handler_detector.handlers)
```

**Immutable Data (ADR-001)** - Use tuple for signal_handlers field (consistent with external_signals) to ensure immutability. Default empty tuple () maintains backward compatibility.

**Type Safety (ADR-006)** - Complete type hints required for mypy strict mode. SignalHandler already has full type annotations from Story 8.1.

### Key Components

**File Locations:**
- WorkflowMetadata extension: `src/temporalio_graphs/_internal/graph_models.py` (line ~537)
- Analyzer integration: `src/temporalio_graphs/analyzer.py` (line ~219 after ExternalSignalDetector)
- Unit tests: `tests/test_graph_models.py`, `tests/test_analyzer.py`

**WorkflowMetadata Field Addition:**
```python
@dataclass
class WorkflowMetadata:
    # ... existing fields ...
    child_workflow_calls: list[ChildWorkflowCall] = field(default_factory=list)
    external_signals: tuple[ExternalSignalCall, ...] = ()
    signal_handlers: tuple[SignalHandler, ...] = ()  # NEW: Epic 8.2
```

**Analyzer Integration:**
```python
# After external_signals detection (line ~224 in analyzer.py):
# Detect signal handlers using SignalHandlerDetector
signal_handler_detector = SignalHandlerDetector()
signal_handler_detector.set_workflow_class(self._workflow_class)
signal_handler_detector.visit(tree)
signal_handlers = tuple(signal_handler_detector.handlers)

# Include in WorkflowMetadata constructor:
return WorkflowMetadata(
    # ... existing fields ...
    external_signals=tuple(external_signals),
    signal_handlers=signal_handlers,  # NEW
    # ...
)
```

### Testing Standards

**Backward Compatibility Test** - Verify existing tests pass without modification. The default `signal_handlers=()` ensures no breaking changes.

**New Unit Tests:**
- `test_workflow_metadata_signal_handlers_default()` - Verify empty tuple default
- `test_workflow_metadata_signal_handlers_populated()` - Verify tuple contains handlers
- `test_workflow_metadata_signal_handlers_immutable()` - Verify tuple immutability

**Integration Test Fixture:**
```python
SIGNAL_HANDLER_WORKFLOW = '''
from temporalio import workflow

@workflow.defn
class ShippingWorkflow:
    def __init__(self):
        self.should_ship = False

    @workflow.run
    async def run(self, shipping_id: str) -> str:
        await workflow.wait_condition(lambda: self.should_ship)
        return "shipped"

    @workflow.signal
    async def ship_order(self, order_id: str) -> None:
        self.should_ship = True
'''
```

### Learnings from Previous Story

**From Story 8.1: Signal Handler Detector (Status: done)**

**SignalHandler Dataclass Complete:**
- Already created in graph_models.py (lines 424-463)
- Frozen dataclass with all required fields
- Full type annotations for mypy strict

**SignalHandlerDetector Complete:**
- Class implemented in detector.py (lines 1020-1189)
- `set_workflow_class()` method available
- `handlers` property returns list[SignalHandler]
- 28 tests covering all patterns

**Integration Pattern from ExternalSignalDetector:**
- Story 7.3 established the pattern for integrating detectors into analyzer
- Create instance -> set context -> visit tree -> get results as tuple
- Same pattern applies for SignalHandlerDetector

### FR Coverage

| AC | FR | Tech Spec Section | Description |
|----|----|--------------------|-------------|
| AC1 | FR83 | Data Models --> WorkflowMetadata | signal_handlers field in metadata |
| AC3 | FR83 | APIs and Interfaces --> WorkflowAnalyzer | Analyzer populates signal_handlers |
| AC6 | FR83 | Data Models --> WorkflowMetadata | Tuple conversion for immutability |

### References

- [Tech Spec Epic 8: AC5-AC6](../tech-spec-epic-8.md#acceptance-criteria-authoritative)
- [Tech Spec Epic 8: WorkflowMetadata Extension](../tech-spec-epic-8.md#data-models-and-contracts)
- [Story 8.1: Signal Handler Detector](8-1-signal-handler-detector.md)
- [Architecture: ADR-001 Static Analysis](../../architecture.md#adr-001-static-analysis-vs-runtime-interceptors)
- [Architecture: ADR-006 Type Safety](../../architecture.md#adr-006-mypy-strict-mode-for-type-safety)

## Dev Agent Record

### Context Reference

_To be populated when story is ready-for-dev_

### Agent Model Used

_To be populated during implementation_

### Debug Log References

_To be populated during implementation_

### Completion Notes List

_To be populated during implementation_

### File List

**Created:**
_To be populated during implementation_

**Modified:**
_To be populated during implementation_
