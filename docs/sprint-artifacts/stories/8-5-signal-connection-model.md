# Story 8.5: Signal Connection Model

Status: review

## Story

As a library developer,
I want SignalConnection and PeerSignalGraph data models to represent cross-workflow signal relationships,
So that the analyzer can build and store connected workflow graphs for visualization.

## Acceptance Criteria

1. **AC12: PeerSignalGraph Model (FR86)** - PeerSignalGraph frozen dataclass exists in `graph_models.py` with fields:
   - root_workflow: WorkflowMetadata for the entry workflow
   - workflows: dict[str, WorkflowMetadata] mapping workflow class name to metadata
   - signal_handlers: dict[str, list[SignalHandler]] mapping signal name to handlers
   - connections: list[SignalConnection] containing all signal flows between workflows
   - unresolved_signals: list[ExternalSignalCall] for signals without matching handlers

2. **AC13: SignalConnection Model** - SignalConnection frozen dataclass exists in `graph_models.py` with fields:
   - sender_workflow: str (name of workflow sending the signal)
   - receiver_workflow: str (name of workflow receiving the signal)
   - signal_name: str (name of the signal being sent/received)
   - sender_line: int (line number where signal() is called)
   - receiver_line: int (line number where @workflow.signal handler is defined)
   - sender_node_id: str (node ID of external signal node)
   - receiver_node_id: str (node ID of signal handler node)

3. **Frozen Dataclasses** - Both SignalConnection and PeerSignalGraph are immutable (frozen=True) following ADR immutability patterns

4. **Type Safety** - All fields have complete type hints for mypy strict mode compliance (ADR-006)

5. **Docstrings** - Both dataclasses have comprehensive Google-style docstrings explaining purpose, args, and usage

6. **Public Exports** - SignalConnection and PeerSignalGraph are exported from `__init__.py` for public API access

7. **Unit Tests** - Unit tests in `tests/test_graph_models.py` verify:
   - SignalConnection instantiation and field access
   - PeerSignalGraph instantiation and field access
   - Immutability (frozen) behavior
   - Default values for collection fields

8. **No Regressions** - All existing Epic 1-8.4 tests continue passing with no failures

## Tasks / Subtasks

- [x] Create SignalConnection dataclass (AC: 2, 3, 4, 5)
  - [x] Add SignalConnection to `src/temporalio_graphs/_internal/graph_models.py`
  - [x] Define frozen dataclass with @dataclass(frozen=True)
  - [x] Add field: sender_workflow (str)
  - [x] Add field: receiver_workflow (str)
  - [x] Add field: signal_name (str)
  - [x] Add field: sender_line (int)
  - [x] Add field: receiver_line (int)
  - [x] Add field: sender_node_id (str)
  - [x] Add field: receiver_node_id (str)
  - [x] Write comprehensive docstring with Args section

- [x] Create PeerSignalGraph dataclass (AC: 1, 3, 4, 5)
  - [x] Add PeerSignalGraph to `src/temporalio_graphs/_internal/graph_models.py`
  - [x] Define frozen dataclass with @dataclass(frozen=True)
  - [x] Add field: root_workflow (WorkflowMetadata)
  - [x] Add field: workflows (dict[str, WorkflowMetadata])
  - [x] Add field: signal_handlers (dict[str, list[SignalHandler]])
  - [x] Add field: connections (list[SignalConnection])
  - [x] Add field: unresolved_signals (list[ExternalSignalCall])
  - [x] Write comprehensive docstring with Args section and example

- [x] Export new dataclasses (AC: 6)
  - [x] Add SignalConnection to graph_models.py __all__ list
  - [x] Add PeerSignalGraph to graph_models.py __all__ list
  - [x] Add SignalConnection to __init__.py exports
  - [x] Add PeerSignalGraph to __init__.py exports

- [x] Add unit tests for SignalConnection (AC: 7)
  - [x] Create `test_signal_connection_creation()` - verify instantiation with all fields
  - [x] Create `test_signal_connection_frozen()` - verify immutability raises error
  - [x] Create `test_signal_connection_field_access()` - verify all fields accessible
  - [x] Create `test_signal_connection_equality()` - verify dataclass equality

- [x] Add unit tests for PeerSignalGraph (AC: 7)
  - [x] Create `test_peer_signal_graph_creation()` - verify instantiation with all fields
  - [x] Create `test_peer_signal_graph_frozen()` - verify immutability raises error
  - [x] Create `test_peer_signal_graph_field_access()` - verify all fields accessible
  - [x] Create `test_peer_signal_graph_with_empty_collections()` - verify default/empty behavior

- [x] Verify no regressions (AC: 8)
  - [x] Run full test suite: `pytest -v`
  - [x] Verify all existing tests pass
  - [x] Run mypy strict mode: `mypy src/temporalio_graphs/`
  - [x] Run ruff linting: `ruff check src/temporalio_graphs/`
  - [x] Verify test coverage remains >=80%

## Dev Notes

### Architecture Patterns and Constraints

**Frozen Dataclasses (ADR Immutability)** - Both data models must be frozen following established patterns. This ensures data integrity and supports future caching/hashing use cases.

**Type Safety (ADR-006)** - Complete type hints required for mypy strict mode. Use proper generic types:
- `dict[str, WorkflowMetadata]` for workflows mapping
- `dict[str, list[SignalHandler]]` for handler index
- `list[SignalConnection]` for connections
- `list[ExternalSignalCall]` for unresolved signals

**Docstring Standard** - Follow Google-style docstrings matching existing dataclasses in graph_models.py. Include Args section and Example usage.

### Key Components

**File Locations:**
- Implementation: `src/temporalio_graphs/_internal/graph_models.py` (existing file, add new dataclasses)
- Tests: `tests/test_graph_models.py` (existing file, add new tests)
- Exports: `src/temporalio_graphs/__init__.py` (add new exports)

**SignalConnection Dataclass (Tech Spec lines 189-214):**
```python
@dataclass(frozen=True)
class SignalConnection:
    """Represents a signal flow between two workflows.

    Captures the relationship between an external signal send
    (ExternalSignalCall) and a signal handler (SignalHandler).

    Args:
        sender_workflow: Name of workflow sending the signal.
        receiver_workflow: Name of workflow receiving the signal.
        signal_name: Name of the signal being sent/received.
        sender_line: Line number in sender where signal() is called.
        receiver_line: Line number in receiver where @workflow.signal is.
        sender_node_id: Node ID of the external signal node.
        receiver_node_id: Node ID of the signal handler node.
    """
    sender_workflow: str
    receiver_workflow: str
    signal_name: str
    sender_line: int
    receiver_line: int
    sender_node_id: str
    receiver_node_id: str
```

**PeerSignalGraph Dataclass (Tech Spec lines 216-241):**
```python
@dataclass(frozen=True)
class PeerSignalGraph:
    """Complete graph of workflows connected by peer-to-peer signals.

    The result of cross-workflow signal analysis, containing all
    discovered workflows, their signal handlers, and the connections
    between them.

    Args:
        root_workflow: Entry point workflow for the analysis.
        workflows: All workflows discovered during analysis.
            Maps workflow class name to WorkflowMetadata.
        signal_handlers: All signal handlers discovered.
            Maps signal name to list of handlers (multiple workflows
            may handle the same signal).
        connections: All signal connections between workflows.
        unresolved_signals: External signals where no target was found.
    """
    root_workflow: WorkflowMetadata
    workflows: dict[str, WorkflowMetadata]
    signal_handlers: dict[str, list[SignalHandler]]
    connections: list[SignalConnection]
    unresolved_signals: list[ExternalSignalCall]
```

**Entity Relationships (Tech Spec lines 283-293):**
```
PeerSignalGraph (1) ──< (n) WorkflowMetadata
PeerSignalGraph (1) ──< (n) SignalConnection
PeerSignalGraph (1) ──< (n) ExternalSignalCall (unresolved)

WorkflowMetadata (1) ──< (n) SignalHandler (handlers in this workflow)
WorkflowMetadata (1) ──< (n) ExternalSignalCall (signals sent from this workflow)

SignalConnection (1) ──< (1) ExternalSignalCall (sender side)
SignalConnection (1) ──< (1) SignalHandler (receiver side)
```

### Dependencies from Previous Stories

**From Story 8.1/8.2: SignalHandler Available**
- Frozen dataclass in graph_models.py with: signal_name, method_name, workflow_class, source_line, node_id
- Already exported publicly

**From Epic 7: ExternalSignalCall Available**
- Frozen dataclass with: signal_name, target_workflow_pattern, source_line, node_id, source_workflow
- Already exported publicly

**From Story 8.4: SignalNameResolver Complete**
- Resolver can find handlers by signal name
- Handler index available for PeerSignalGraphAnalyzer (Story 8.6)

### Testing Standards

**Test File Organization** - Add tests to existing `tests/test_graph_models.py` file, which already contains tests for SignalHandler, ExternalSignalCall, etc. Follow existing naming patterns.

**Test Structure:**
```python
class TestSignalConnection:
    def test_signal_connection_creation(self) -> None:
        """Test SignalConnection instantiation."""
        conn = SignalConnection(
            sender_workflow="OrderWorkflow",
            receiver_workflow="ShippingWorkflow",
            signal_name="ship_order",
            sender_line=56,
            receiver_line=67,
            sender_node_id="ext_sig_ship_order_56",
            receiver_node_id="sig_handler_ship_order_67",
        )
        assert conn.sender_workflow == "OrderWorkflow"
        assert conn.receiver_workflow == "ShippingWorkflow"
        # ... etc

    def test_signal_connection_frozen(self) -> None:
        """Test SignalConnection is immutable."""
        conn = SignalConnection(...)
        with pytest.raises(FrozenInstanceError):
            conn.sender_workflow = "NewWorkflow"  # type: ignore


class TestPeerSignalGraph:
    def test_peer_signal_graph_creation(self) -> None:
        """Test PeerSignalGraph instantiation."""
        ...
```

**Expected Test Count** - Target ~8-10 new tests covering both dataclasses.

### Learnings from Previous Stories

**From Story 8.3/8.4: Resolver Pattern**
- SignalNameResolver builds handler index as dict[str, list[tuple[Path, SignalHandler]]]
- PeerSignalGraph.signal_handlers uses similar structure but without Path: dict[str, list[SignalHandler]]
- The PeerSignalGraphAnalyzer (Story 8.6) will build this from resolver results

**From Story 8.2: WorkflowMetadata Extension**
- WorkflowMetadata already has signal_handlers: tuple[SignalHandler, ...]
- PeerSignalGraph.workflows will contain these extended WorkflowMetadata instances

**From Epic 7: ExternalSignalCall Pattern**
- Already frozen dataclass with source_workflow field
- Used in WorkflowMetadata.external_signals: tuple[ExternalSignalCall, ...]
- PeerSignalGraph.unresolved_signals uses list[ExternalSignalCall] for mutability during analysis

### FR Coverage

| AC | FR | Tech Spec Section | Description |
|----|----|--------------------|-------------|
| AC12 | FR86 | Data Models --> PeerSignalGraph (lines 216-241) | PeerSignalGraph dataclass |
| AC13 | FR86 | Data Models --> SignalConnection (lines 189-214) | SignalConnection dataclass |

### References

- [Tech Spec Epic 8: Data Models](../tech-spec-epic-8.md#data-models-and-contracts) (lines 152-293)
- [Tech Spec Epic 8: AC12-AC13](../tech-spec-epic-8.md#acceptance-criteria-authoritative) (lines 985-1001)
- [Architecture: ADR-006 Type Safety](../../architecture.md#adr-006-mypy-strict-mode-for-type-safety)
- [Story 8.3: Signal Name Resolver](8-3-signal-name-resolver.md)
- [Story 8.4: Search Path Scanning](8-4-search-path-scanning.md)

## Dev Agent Record

### Context Reference

`docs/sprint-artifacts/story-contexts/8-5-signal-connection-model-context.xml`

### Agent Model Used

claude-opus-4-5-20251101

### Debug Log References

N/A - Implementation completed without issues.

### Completion Notes List

**Implementation Summary:**
- Added SignalConnection frozen dataclass (7 fields) after ExternalSignalCall in graph_models.py (lines 424-458)
- Added PeerSignalGraph frozen dataclass (5 fields) at end of graph_models.py (lines 732-764)
- Both dataclasses follow ADR immutability patterns with @dataclass(frozen=True)
- Comprehensive Google-style docstrings with Args and Example sections
- All fields have complete type hints for mypy strict mode compliance
- Exported both dataclasses from __init__.py (__all__ list updated)
- Added 8 unit tests (4 for SignalConnection, 4 for PeerSignalGraph)
- Updated test_public_api.py to expect the new exports

**Key Decisions:**
- Placed SignalConnection BEFORE SignalHandler in graph_models.py (logical ordering: sender before receiver)
- Placed PeerSignalGraph AFTER WorkflowCallGraph at end of file (depends on all other dataclasses)
- Used function-based tests (not class-based) following existing test file pattern
- No default values for PeerSignalGraph collection fields - all required per Story Context spec

**Validation Results:**
- pytest: 656 tests passed (8 new tests for this story)
- mypy strict: No issues found in 15 source files
- ruff: All checks passed
- Coverage: 89.56% (>80% threshold)

### File List

**Created:**
None

**Modified:**
- `src/temporalio_graphs/_internal/graph_models.py` - Added SignalConnection (lines 424-458) and PeerSignalGraph (lines 732-764) dataclasses
- `src/temporalio_graphs/__init__.py` - Added imports and exports for SignalConnection and PeerSignalGraph
- `tests/test_graph_models.py` - Added 8 unit tests for SignalConnection and PeerSignalGraph
- `tests/test_public_api.py` - Updated expected exports to include new dataclasses
