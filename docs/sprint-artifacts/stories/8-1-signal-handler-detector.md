# Story 8.1: Signal Handler Detector

Status: review

## Story

As a library developer,
I want to detect `@workflow.signal` decorated methods in workflow classes,
So that I can identify signal handlers for cross-workflow signal visualization.

## Acceptance Criteria

1. **SignalHandlerDetector Class Exists** - SignalHandlerDetector class exists in `src/temporalio_graphs/detector.py` (after ExternalSignalDetector) extending `ast.NodeVisitor` following established detector pattern (FR82)

2. **Async Signal Handler Detection** - Detector implements `visit_AsyncFunctionDef()` to detect `@workflow.signal` decorated async methods and creates SignalHandler with correct metadata (AC1 from Tech Spec lines 921-926)

3. **Sync Signal Handler Detection** - Detector implements `visit_FunctionDef()` to detect `@workflow.signal` decorated sync methods (AC4 from Tech Spec lines 939-941)

4. **Explicit Signal Name Extraction** - Detector extracts signal name from `@workflow.signal(name="custom_name")` decorator argument when explicitly provided (AC2 from Tech Spec lines 928-931)

5. **Method Name as Signal Name** - Detector uses method name as signal name when `@workflow.signal` has no explicit name argument (AC3 from Tech Spec lines 933-937)

6. **Signal Handler Metadata** - Each detected handler creates a SignalHandler with: signal_name, method_name, workflow_class, source_line, node_id using format `sig_handler_{signal_name}_{line_number}` (AC5 from Tech Spec lines 943-957)

7. **Workflow Class Context** - Detector has `set_workflow_class(name: str)` method to store workflow class context for handler metadata

8. **Handlers Property** - Detector has property `handlers` returning `list[SignalHandler]` with all detected signal handlers (copy for immutability)

9. **Decorator Recognition** - Detector recognizes multiple decorator patterns:
   - `@workflow.signal` (bare decorator, no parentheses)
   - `@workflow.signal()` (decorator with empty parentheses)
   - `@workflow.signal(name="custom")` (decorator with explicit name argument)

10. **Multiple Handlers Same Workflow** - Detector handles workflows with multiple signal handlers, detecting all handlers correctly

11. **Complete Test Coverage** - Unit tests in `tests/test_detector.py` achieve 100% coverage for SignalHandlerDetector with tests for: async handler, sync handler, explicit name, method name fallback, multiple handlers, decorator variants

12. **No Regressions** - All existing Epic 1-7 tests continue passing with no failures

## Tasks / Subtasks

- [x] Implement SignalHandlerDetector class structure (AC: 1, 7, 8)
  - [x] Add SignalHandlerDetector class after ExternalSignalDetector in `src/temporalio_graphs/detector.py`
  - [x] Extend `ast.NodeVisitor` following established detector pattern
  - [x] Initialize private attributes: `_handlers: list[SignalHandler]`, `_workflow_class: str`
  - [x] Implement `set_workflow_class(name: str)` method to set workflow class context
  - [x] Implement `handlers` property returning `list[SignalHandler]` (copy for immutability)

- [x] Implement async signal handler detection (AC: 2, 4, 5, 6)
  - [x] Implement `visit_AsyncFunctionDef(node: ast.AsyncFunctionDef)` method
  - [x] Iterate through `node.decorator_list` to check for signal decorators
  - [x] Use `_is_signal_decorator(decorator)` helper to identify `@workflow.signal` decorators
  - [x] Extract signal name using `_extract_signal_name(decorator, node.name)` helper
  - [x] Generate node ID using format: `sig_handler_{signal_name}_{line_number}`
  - [x] Create `SignalHandler` instance with: signal_name, method_name, workflow_class, source_line, node_id
  - [x] Append to `_handlers` list
  - [x] Call `generic_visit(node)` to continue AST traversal

- [x] Implement sync signal handler detection (AC: 3)
  - [x] Implement `visit_FunctionDef(node: ast.FunctionDef)` method
  - [x] Same logic as `visit_AsyncFunctionDef` for consistency
  - [x] Iterate decorators, check for signal decorator, extract name, create handler
  - [x] Call `generic_visit(node)` to continue traversal

- [x] Implement decorator recognition (AC: 9)
  - [x] Create private method `_is_signal_decorator(decorator: ast.expr) -> bool`
  - [x] Handle `ast.Attribute`: Check for `workflow.signal` (bare decorator)
  - [x] Handle `ast.Call`: Check if `node.func` is `workflow.signal` (decorator with args)
  - [x] Support both `signal` and `workflow.signal` attribute patterns

- [x] Implement signal name extraction (AC: 4, 5)
  - [x] Create private method `_extract_signal_name(decorator: ast.expr, method_name: str) -> str`
  - [x] If decorator is `ast.Call` with `name=` keyword argument, extract and return that value
  - [x] Otherwise return `method_name` as the signal name (default behavior)
  - [x] Handle `ast.Constant` for string literal extraction

- [x] Add comprehensive unit tests (AC: 11)
  - [x] Create `TestSignalHandlerDetectorBasic` test class
  - [x] Create `test_detect_async_signal_handler()` - basic async handler detection
  - [x] Create `test_detect_sync_signal_handler()` - sync handler detection
  - [x] Create `test_detect_explicit_signal_name()` - `@workflow.signal(name="custom")`
  - [x] Create `test_detect_method_name_as_signal_name()` - `@workflow.signal` without explicit name
  - [x] Create `test_detect_multiple_handlers_same_workflow()` - workflow with 2+ handlers
  - [x] Create `test_bare_decorator_no_parens()` - `@workflow.signal` (no parentheses)
  - [x] Create `test_decorator_empty_parens()` - `@workflow.signal()`
  - [x] Create `test_handlers_property_returns_list()` - verify return type
  - [x] Create `test_handlers_property_immutable()` - verify copy for immutability
  - [x] Create `test_workflow_class_context_stored()` - verify workflow class in metadata
  - [x] Create `test_node_id_format()` - verify `sig_handler_{name}_{line}` format
  - [x] Ensure 100% coverage for SignalHandlerDetector class

- [x] Verify no regressions (AC: 12)
  - [x] Run full test suite: `pytest -v`
  - [x] Verify all 590+ existing tests pass (Epic 1-7 tests) - 617 tests pass
  - [x] Run mypy strict mode: `mypy src/temporalio_graphs/` - No issues
  - [x] Run ruff linting: `ruff check src/temporalio_graphs/` - All checks passed
  - [x] Verify test coverage remains >=80%: `pytest --cov=src/temporalio_graphs --cov-report=term-missing` - 90% coverage

## Dev Notes

### Architecture Patterns and Constraints

**AST Visitor Pattern** - SignalHandlerDetector follows the established detector pattern from Epic 3 (DecisionDetector), Epic 4 (SignalDetector), Epic 6 (ChildWorkflowDetector), and Epic 7 (ExternalSignalDetector). Uses `ast.NodeVisitor` to traverse workflow AST and identify `@workflow.signal` decorated methods.

**Static Analysis Only (ADR-001)** - Detection is purely AST-based with no workflow execution. Identifies signal handlers by decorator patterns on method definitions.

**Immutable Data** - SignalHandler will be frozen dataclass (Story 8.2). Detector returns copy of `_handlers` list via property to prevent external mutation.

**Error Handling** - Follows established patterns. No explicit errors expected for signal handler detection - malformed decorators are simply not recognized as signal handlers (graceful degradation).

**Type Safety (ADR-006)** - Complete type hints required for mypy strict mode. All methods, parameters, return types must be fully typed.

### Key Components

**File Locations:**
- Implementation: `src/temporalio_graphs/detector.py` (add after ExternalSignalDetector, ~line 1016)
- Tests: `tests/test_detector.py` (extend existing file with new test class)
- Dependencies: `src/temporalio_graphs/_internal/graph_models.py` (SignalHandler - Story 8.2)

**AST Patterns to Detect:**

Bare decorator pattern:
```python
# User code:
@workflow.signal
async def ship_order(self, order_id: str) -> None:
    self.should_ship = True

# AST detection:
# visit_AsyncFunctionDef: Check decorator_list for workflow.signal attribute
# --> signal_name = "ship_order" (method name)
# --> Create SignalHandler(signal_name="ship_order", method_name="ship_order", ...)
```

Explicit name pattern:
```python
# User code:
@workflow.signal(name="custom_signal")
async def handler(self, data: str) -> None:
    self.data = data

# AST detection:
# visit_AsyncFunctionDef: Check decorator_list for workflow.signal Call
# --> Extract name="custom_signal" from keyword arguments
# --> signal_name = "custom_signal" (NOT method name)
# --> Create SignalHandler(signal_name="custom_signal", method_name="handler", ...)
```

Sync handler pattern:
```python
# User code:
@workflow.signal
def ship_order(self, order_id: str) -> None:
    self.should_ship = True

# AST detection:
# visit_FunctionDef: Same logic as AsyncFunctionDef
# --> signal_name = "ship_order"
```

**Node ID Format:**
- Format: `sig_handler_{signal_name}_{line_number}`
- Example: `sig_handler_ship_order_67`
- Normalize signal name: spaces to underscores, lowercase

### SignalHandler Dataclass (Story 8.2 dependency)

The SignalHandler dataclass will be created in Story 8.2, but here's the expected structure from Tech Spec:

```python
@dataclass(frozen=True)
class SignalHandler:
    """Represents a @workflow.signal decorated method."""
    signal_name: str        # Name of signal (explicit or method name)
    method_name: str        # Actual method name in workflow class
    workflow_class: str     # Name of containing workflow class
    source_line: int        # Line number of method definition
    node_id: str            # Format: sig_handler_{signal_name}_{line}
```

### Testing Standards

**100% Coverage Target** - All SignalHandlerDetector branches must be tested. Use `pytest --cov=src/temporalio_graphs/detector.py --cov-report=term-missing` to verify.

**Test Organization** - Add new test class `TestSignalHandlerDetector` to `tests/test_detector.py` following existing test structure.

**Fixtures** - Create reusable AST fixtures for sample workflows with signal handlers:
```python
@pytest.fixture
def signal_handler_workflow_ast():
    source = '''
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
    return ast.parse(source)
```

**Edge Cases to Test:**
- Multiple signals in same workflow
- Mix of async and sync handlers
- Handler with explicit name + handler with method name
- Handler inside workflow with no @workflow.run (edge case)
- Handler with complex decorators (stacked decorators)

### Learnings from Previous Story

**From Story 7.1: Implement External Signal Detector (Status: done)**

**Key Detector Pattern Established (Epic 7):**
- ExternalSignalDetector provides proven pattern for detecting method calls and tracking metadata
- AST visitor pattern: `visit_Assign()` and `visit_Await()` for detecting assignments and await expressions
- For SignalHandlerDetector, use `visit_AsyncFunctionDef()` and `visit_FunctionDef()` for method definitions
- Handle both attribute access (`workflow.signal`) and call expressions (`workflow.signal(name="...")`)
- Store metadata in frozen dataclass for immutability
- Return copy of internal list via property

**Type Safety Excellence:**
- Epic 7 achieved mypy strict mode passing
- Complete type hints for all detector methods, parameters, return values
- Use `ast.FunctionDef`, `ast.AsyncFunctionDef`, `ast.expr`, `ast.Attribute`, `ast.Call` for AST types

**Test Coverage Standard:**
- Story 7.1 achieved 100% coverage for ExternalSignalDetector
- 21 tests organized in 6 test classes covering all patterns and edge cases
- Test organization: dedicated test class per detector following consistent pattern

**AST Traversal Best Practices:**
- Always call `generic_visit(node)` to continue traversal after custom node handling
- Use `lineno` attribute for error reporting and node identification
- Check `node.decorator_list` for method decorators
- Handle `ast.Constant` for string literals in decorator arguments

**From Story 7.5: Add Peer Signal Workflow Example and Documentation (Status: done)**

**Shipping Workflow Pattern:**
- Shipping workflow in Epic 7 examples demonstrates signal handler pattern:
  - `@workflow.signal async def ship_order(self, order_id: str) -> None`
  - Handler sets internal state that `wait_condition()` checks
- This pattern will be detected by SignalHandlerDetector
- Shows real-world use case for signal handler detection

**Documentation Clarity:**
- Clear distinction between internal signals (wait_condition), parent-child (execute_child_workflow), and peer-to-peer (get_external_workflow_handle)
- Epic 8 adds fourth category: signal handlers (the receive side of peer-to-peer)

### FR Coverage

| AC | FR | Tech Spec Section | Description |
|----|----|--------------------|-------------|
| AC1 | FR82 | APIs and Interfaces --> SignalHandlerDetector | Signal handler detection via AST |
| AC2 | FR82 | APIs and Interfaces --> _extract_signal_name | Explicit signal name extraction |
| AC3 | FR82 | APIs and Interfaces --> visit_FunctionDef | Sync signal handler support |
| AC4 | FR82 | APIs and Interfaces --> _is_signal_decorator | Decorator pattern recognition |
| AC5 | FR82 | Data Models --> SignalHandler | Handler metadata structure |
| AC6 | FR82 | Traceability Mapping | test_detector.py coverage |

### References

- [Tech Spec Epic 8: SignalHandlerDetector API](../tech-spec-epic-8.md#apis-and-interfaces)
- [Tech Spec Epic 8: AC1-AC4](../tech-spec-epic-8.md#acceptance-criteria-authoritative)
- [Architecture: ADR-001 Static Analysis](../../architecture.md#adr-001-static-analysis-vs-runtime-interceptors)
- [Architecture: ADR-006 Type Safety](../../architecture.md#adr-006-mypy-strict-mode-for-type-safety)
- [Architecture: ADR-013 Cross-Workflow Signal Visualization](../../architecture.md#adr-013-cross-workflow-signal-visualization-strategy)
- [Story 7.1: External Signal Detector Pattern](7-1-implement-external-signal-detector.md)
- [Epics: Epic 8 Overview](../epics.md)

## Dev Agent Record

### Context Reference

- `/Users/luca/dev/bounty/docs/sprint-artifacts/story-contexts/8-1-signal-handler-detector-context.xml`

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - No debugging required, implementation was straightforward.

### Completion Notes List

1. **SignalHandler Dataclass** - Created frozen dataclass in `graph_models.py` with fields: signal_name, method_name, workflow_class, source_line, node_id. Placed after ExternalSignalCall for logical grouping.

2. **SignalHandlerDetector Class** - Implemented following the established detector pattern from ExternalSignalDetector. Key methods:
   - `set_workflow_class(name: str)` - Sets workflow context
   - `visit_AsyncFunctionDef()` / `visit_FunctionDef()` - Detect signal handlers
   - `_check_for_signal_handler()` - Shared logic for async/sync detection
   - `_is_signal_decorator()` - Handles bare, empty parens, and name= decorator patterns
   - `_extract_signal_name()` - Extracts explicit name or falls back to method name
   - `_generate_node_id()` - Creates `sig_handler_{name}_{line}` format IDs
   - `handlers` property - Returns copy of internal list for immutability

3. **Decorator Pattern Recognition** - Successfully handles three patterns:
   - `@workflow.signal` (bare attribute)
   - `@workflow.signal()` (call with empty args)
   - `@workflow.signal(name="custom")` (call with keyword arg)

4. **Test Coverage** - Added 28 comprehensive tests organized in 6 test classes:
   - TestSignalHandlerDetectorBasic (4 tests)
   - TestSignalHandlerNameExtraction (5 tests)
   - TestSignalHandlerMetadata (6 tests)
   - TestSignalHandlerProperty (3 tests)
   - TestSignalHandlerEdgeCases (10 tests)

5. **Quality Validation** - All validations passed:
   - mypy strict mode: No issues
   - ruff check: All checks passed
   - Full test suite: 617 tests pass, 90% coverage

### File List

**Created:**
- None (all changes to existing files)

**Modified:**
- `/Users/luca/dev/bounty/src/temporalio_graphs/_internal/graph_models.py` - Added SignalHandler frozen dataclass (lines 424-463)
- `/Users/luca/dev/bounty/src/temporalio_graphs/detector.py` - Added SignalHandlerDetector class (lines 1020-1189) and SignalHandler import
- `/Users/luca/dev/bounty/tests/test_detector.py` - Added 28 comprehensive tests for SignalHandlerDetector (lines 1783-2398)
- `/Users/luca/dev/bounty/docs/sprint-artifacts/sprint-status.yaml` - Updated story status: ready-for-dev -> in-progress -> review

## Senior Developer Review (AI)

### Review Date
2025-11-26

### Review Outcome
**APPROVED**

### Executive Summary
Story 8-1 implementation is complete and meets all acceptance criteria. The SignalHandlerDetector class follows the established detector patterns from Epic 7 (ExternalSignalDetector) with excellent code quality. All 12 acceptance criteria are fully implemented with evidence. Test coverage is comprehensive with 28 tests achieving 100% coverage for the new code. No regressions found - all 617 tests pass.

### Acceptance Criteria Validation

| AC | Description | Status | Evidence |
|----|-------------|--------|----------|
| AC1 | SignalHandlerDetector class exists in detector.py after ExternalSignalDetector extending ast.NodeVisitor | IMPLEMENTED | `/Users/luca/dev/bounty/src/temporalio_graphs/detector.py:1020-1057` - Class defined at line 1020, extends ast.NodeVisitor |
| AC2 | Async signal handler detection via visit_AsyncFunctionDef() | IMPLEMENTED | `/Users/luca/dev/bounty/src/temporalio_graphs/detector.py:1072-1079` - Implements visit_AsyncFunctionDef with decorator check |
| AC3 | Sync signal handler detection via visit_FunctionDef() | IMPLEMENTED | `/Users/luca/dev/bounty/src/temporalio_graphs/detector.py:1081-1088` - Implements visit_FunctionDef with same logic |
| AC4 | Explicit signal name extraction from @workflow.signal(name="custom_name") | IMPLEMENTED | `/Users/luca/dev/bounty/src/temporalio_graphs/detector.py:1144-1162` - _extract_signal_name checks ast.Call keywords |
| AC5 | Method name as signal name when no explicit name | IMPLEMENTED | `/Users/luca/dev/bounty/src/temporalio_graphs/detector.py:1162` - Returns method_name as fallback |
| AC6 | SignalHandler metadata with all required fields | IMPLEMENTED | `/Users/luca/dev/bounty/src/temporalio_graphs/_internal/graph_models.py:424-463` - Frozen dataclass with signal_name, method_name, workflow_class, source_line, node_id |
| AC7 | set_workflow_class(name: str) method | IMPLEMENTED | `/Users/luca/dev/bounty/src/temporalio_graphs/detector.py:1064-1070` - Method stores workflow class context |
| AC8 | handlers property returning list[SignalHandler] (copy for immutability) | IMPLEMENTED | `/Users/luca/dev/bounty/src/temporalio_graphs/detector.py:1181-1189` - Returns list(self._handlers) |
| AC9 | Decorator recognition for bare, empty parens, and name= patterns | IMPLEMENTED | `/Users/luca/dev/bounty/src/temporalio_graphs/detector.py:1118-1142` - _is_signal_decorator handles all three patterns |
| AC10 | Multiple handlers same workflow | IMPLEMENTED | Tests verify detection of 3 handlers in single workflow |
| AC11 | Complete test coverage | IMPLEMENTED | `/Users/luca/dev/bounty/tests/test_detector.py:1784-2398` - 28 tests organized in 5 test classes |
| AC12 | No regressions | IMPLEMENTED | 617 tests pass, 89.53% coverage |

### Task Completion Validation

| Task | Status | Evidence |
|------|--------|----------|
| Implement SignalHandlerDetector class structure (AC: 1, 7, 8) | VERIFIED | detector.py:1020-1189 - Complete class implementation |
| Implement async signal handler detection (AC: 2, 4, 5, 6) | VERIFIED | detector.py:1072-1116 - visit_AsyncFunctionDef with helper methods |
| Implement sync signal handler detection (AC: 3) | VERIFIED | detector.py:1081-1088 - visit_FunctionDef delegates to _check_for_signal_handler |
| Implement decorator recognition (AC: 9) | VERIFIED | detector.py:1118-1142 - Handles ast.Attribute and ast.Call patterns |
| Implement signal name extraction (AC: 4, 5) | VERIFIED | detector.py:1144-1162 - Extracts from keywords or falls back to method name |
| Add comprehensive unit tests (AC: 11) | VERIFIED | test_detector.py:1784-2398 - 28 tests covering all patterns |
| Verify no regressions (AC: 12) | VERIFIED | 617 tests pass, mypy clean, ruff clean |

### Code Quality Assessment

**Architecture Alignment**: EXCELLENT
- Follows established detector pattern from ExternalSignalDetector (Epic 7)
- Uses ast.NodeVisitor correctly with generic_visit() calls
- Proper separation of concerns with helper methods

**Code Organization**: EXCELLENT
- Clear method structure: visit_* methods, _is_* helper, _extract_* helper, _generate_* helper
- Proper type annotations throughout
- Comprehensive docstrings with examples

**Error Handling**: GOOD
- Graceful degradation - malformed decorators simply not recognized
- No exceptions raised during detection (per story design)
- Logging for debug visibility

**Type Safety**: EXCELLENT
- All methods fully typed
- mypy strict mode passes with no issues
- Proper use of union types (ast.FunctionDef | ast.AsyncFunctionDef)

### Test Coverage Analysis

**Coverage Statistics:**
- SignalHandlerDetector: 100% coverage for new code
- 28 new tests in 5 test classes
- Full test suite: 617 tests, 89.53% coverage (>80% requirement)

**Test Quality Assessment:**
- TestSignalHandlerDetectorBasic (4 tests): Basic async/sync detection, multiple handlers, non-signal filtering
- TestSignalHandlerNameExtraction (5 tests): Explicit name, method name fallback, decorator variants
- TestSignalHandlerMetadata (6 tests): Workflow class context, source line, node ID format
- TestSignalHandlerProperty (3 tests): Returns list, immutability, read-only
- TestSignalHandlerEdgeCases (10 tests): Stacked decorators, nested classes, complex types, detector reuse, immutability

### Security Assessment
No security concerns identified. The detector performs static AST analysis only with no code execution.

### Action Items

**LOW Severity:**
- None - implementation is complete and well-structured

### Quality Metrics Summary
- Tests: 617 passed (all existing + 28 new)
- Coverage: 89.53% (exceeds 80% requirement)
- mypy strict: No issues
- ruff: All checks passed
- Test execution time: <2s

### Recommendation
APPROVED - Story implementation is complete, high quality, and ready for merge. The SignalHandlerDetector follows established patterns and is thoroughly tested. No issues require attention before closing this story.
