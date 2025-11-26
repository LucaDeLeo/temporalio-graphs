# Story 8.6: Peer Signal Graph Analyzer

Status: drafted

## Story

As a library developer,
I want a PeerSignalGraphAnalyzer class that builds cross-workflow signal graphs with recursive discovery and cycle detection,
So that users can visualize the complete signal flow between multiple interconnected workflows from a single entry point.

## Acceptance Criteria

1. **AC14: Recursive Discovery (FR87)** - Given OrderWorkflow signals ShippingWorkflow signals NotificationWorkflow, when `analyze_signal_flow("order_workflow.py")` is called, then all three workflows are discovered and two connections are created (Order->Shipping, Shipping->Notification).

2. **AC15: Cycle Detection** - Given WorkflowA signals WorkflowB signals WorkflowA (cycle), when analyzer discovers the cycle, then:
   - Connection A->B->A is recorded
   - WorkflowA is NOT re-analyzed (visited check prevents infinite loop)
   - No infinite loop occurs

3. **AC16: Max Depth Limit** - Given signal_max_discovery_depth = 2 and chain A -> B -> C -> D, when analyzer runs, then:
   - Stops at depth 2 (A, B, C discovered; D not analyzed)
   - Warning logged: "Max depth 2 reached, stopping discovery"

4. **PeerSignalGraphAnalyzer Class** - Class exists in `signal_graph_analyzer.py` with:
   - `__init__(search_paths, resolver, max_depth, context)` accepting configuration
   - `analyze(entry_workflow) -> PeerSignalGraph` main analysis method
   - `_discover_connections(metadata, depth)` recursive helper
   - `_analyze_workflow(file_path)` single workflow analysis wrapper
   - `_build_handler_index()` builds signal handler index from discovered workflows

5. **Integration with SignalNameResolver** - Analyzer uses SignalNameResolver (from Story 8.3) to resolve external signals to target workflows

6. **Unresolved Signal Tracking** - External signals with no matching handler are added to `PeerSignalGraph.unresolved_signals` list

7. **Visited Workflow Tracking** - Maintains `_visited_workflows: set[str]` to prevent re-analysis of already-discovered workflows

8. **Connection Recording** - Creates SignalConnection for each resolved external signal (even for cycles) with correct sender/receiver metadata

9. **Type Safety** - Complete type hints for mypy strict mode compliance (ADR-006)

10. **Debug Logging** - Logs discovery events:
    - "Discovered workflow '{name}' at {path}"
    - "Resolved signal '{name}': {sender} --> {receiver}"
    - "Could not resolve signal '{name}' - no matching handler found"
    - "Max depth {depth} reached, stopping discovery"

11. **Unit Tests** - Unit tests in `tests/test_signal_graph_analyzer.py` verify:
    - Single workflow analysis (no external signals)
    - Two connected workflows (A -> B)
    - Three workflow chain (A -> B -> C)
    - Cycle detection (A -> B -> A)
    - Max depth limiting
    - Unresolved signal handling

12. **No Regressions** - All existing Epic 1-8.5 tests continue passing

## Tasks / Subtasks

- [ ] Create PeerSignalGraphAnalyzer class (AC: 4, 5, 9, 10)
  - [ ] Create `src/temporalio_graphs/signal_graph_analyzer.py` new module
  - [ ] Define class with module docstring and Google-style class docstring
  - [ ] Implement `__init__(search_paths, resolver, max_depth, context)`
    - [ ] Store search_paths as list[Path]
    - [ ] Create or accept SignalNameResolver instance
    - [ ] Store max_depth (default: 10)
    - [ ] Store GraphBuildingContext (create default if None)
    - [ ] Initialize analysis state: `_visited_workflows`, `_workflows`, `_connections`, `_unresolved`
  - [ ] Implement `_analyze_workflow(file_path: Path) -> WorkflowMetadata`
    - [ ] Use WorkflowAnalyzer to analyze single workflow file
    - [ ] Handle WorkflowParseError appropriately
    - [ ] Log discovery: "Discovered workflow '{name}' at {path}"

- [ ] Implement main analyze method (AC: 4, 5, 6, 7, 8)
  - [ ] Implement `analyze(entry_workflow: Path) -> PeerSignalGraph`
    - [ ] Build resolver index via `self._resolver.build_index()`
    - [ ] Analyze entry workflow
    - [ ] Store in `_workflows` dict and mark as visited
    - [ ] Call `_discover_connections(metadata, depth=0)`
    - [ ] Build handler index via `_build_handler_index()`
    - [ ] Return PeerSignalGraph with all collected data
  - [ ] Implement `_build_handler_index() -> dict[str, list[SignalHandler]]`
    - [ ] Iterate over `_workflows` values
    - [ ] Collect signal_handlers into dict by signal_name

- [ ] Implement recursive discovery (AC: 1, 2, 3)
  - [ ] Implement `_discover_connections(metadata: WorkflowMetadata, depth: int) -> None`
    - [ ] Check max depth limit, log warning if exceeded (AC16)
    - [ ] Iterate over `metadata.external_signals`
    - [ ] Call `self._resolver.resolve(external_signal)` for each
    - [ ] If no targets: add to `_unresolved`, log warning
    - [ ] For each target (path, handler):
      - [ ] Analyze target workflow via `_analyze_workflow(path)`
      - [ ] Check if already visited (cycle detection - AC15)
      - [ ] If not visited: add to `_workflows`, mark visited, recurse
      - [ ] Create SignalConnection (even for cycles) (AC8)
      - [ ] Log connection: "Resolved signal '{name}': {sender} --> {receiver}"

- [ ] Add public exports
  - [ ] Add PeerSignalGraphAnalyzer to `src/temporalio_graphs/__init__.py` imports
  - [ ] Add to `__all__` list

- [ ] Create unit tests (AC: 11)
  - [ ] Create `tests/test_signal_graph_analyzer.py` new test file
  - [ ] Create test fixtures:
    - [ ] `workflow_a.py` - sends signal_b
    - [ ] `workflow_b.py` - handles signal_b, sends signal_c
    - [ ] `workflow_c.py` - handles signal_c
    - [ ] `workflow_cycle_a.py` - sends signal to cycle_b
    - [ ] `workflow_cycle_b.py` - handles signal, sends back to cycle_a
  - [ ] Write `test_analyze_single_workflow()` - no external signals
  - [ ] Write `test_analyze_two_connected_workflows()` - A -> B
  - [ ] Write `test_analyze_three_workflow_chain()` - A -> B -> C (AC14)
  - [ ] Write `test_cycle_detection()` - A -> B -> A (AC15)
  - [ ] Write `test_max_depth_limit()` - stops at configured depth (AC16)
  - [ ] Write `test_unresolved_signal()` - signal with no handler
  - [ ] Write `test_multiple_handlers_same_signal()` - both returned

- [ ] Verify no regressions (AC: 12)
  - [ ] Run full test suite: `pytest -v`
  - [ ] Verify all existing tests pass
  - [ ] Run mypy strict mode: `mypy src/temporalio_graphs/`
  - [ ] Run ruff linting: `ruff check src/temporalio_graphs/`
  - [ ] Verify test coverage remains >=80%

## Dev Notes

### Architecture Patterns and Constraints

**Visitor Pattern** - The analyzer follows a visitor/traversal pattern similar to the existing detectors. It "visits" workflows starting from entry point and recursively explores connections.

**Cycle Detection** - Use a `set[str]` to track visited workflow class names. When a workflow is encountered that's already in the set, record the connection but don't recurse further.

**Depth Limiting** - Pass `depth` parameter through recursive calls. Check against `max_depth` at start of `_discover_connections()`.

**Dependency Injection** - Accept optional `resolver` parameter to allow testing with mock resolvers.

### Key Components

**File Locations:**
- Implementation: `src/temporalio_graphs/signal_graph_analyzer.py` (NEW)
- Tests: `tests/test_signal_graph_analyzer.py` (NEW)
- Exports: `src/temporalio_graphs/__init__.py` (update)

**PeerSignalGraphAnalyzer API (Tech Spec lines 444-565):**
```python
class PeerSignalGraphAnalyzer:
    """Analyzes workflows and builds cross-workflow signal graph.

    Starting from an entry workflow, discovers all connected workflows
    by following external signal --> signal handler connections.

    Example:
        >>> analyzer = PeerSignalGraphAnalyzer(
        ...     search_paths=[Path("./workflows/")],
        ...     max_depth=10,
        ... )
        >>> graph = analyzer.analyze(Path("order_workflow.py"))
        >>> print(graph.workflows.keys())
        ['OrderWorkflow', 'ShippingWorkflow', 'NotificationWorkflow']
    """

    def __init__(
        self,
        search_paths: list[Path],
        resolver: SignalNameResolver | None = None,
        max_depth: int = 10,
        context: GraphBuildingContext | None = None,
    ) -> None:
        ...

    def analyze(self, entry_workflow: Path) -> PeerSignalGraph:
        ...

    def _discover_connections(
        self,
        metadata: WorkflowMetadata,
        depth: int
    ) -> None:
        ...
```

**Recursive Discovery Algorithm:**
```
analyze(entry_workflow):
    1. Build resolver index (scans search paths)
    2. Analyze entry workflow -> metadata
    3. Store metadata in workflows dict
    4. Mark entry workflow as visited
    5. _discover_connections(metadata, depth=0)
    6. Build handler index from discovered workflows
    7. Return PeerSignalGraph

_discover_connections(metadata, depth):
    1. If depth >= max_depth: log warning, return
    2. For each external_signal in metadata.external_signals:
       a. targets = resolver.resolve(signal)
       b. If no targets: add to unresolved, log warning, continue
       c. For each (path, handler) in targets:
          i.  Analyze target workflow
          ii. If not visited:
              - Store in workflows
              - Mark visited
              - Recurse: _discover_connections(target, depth+1)
          iii. Create SignalConnection (always, even for cycles)
          iv. Add connection to connections list
```

### Dependencies from Previous Stories

**From Story 8.3: SignalNameResolver Available**
- `resolver.resolve(signal) -> list[tuple[Path, SignalHandler]]`
- `resolver.build_index()` scans search paths

**From Story 8.5: Data Models Available**
- SignalConnection: sender_workflow, receiver_workflow, signal_name, lines, node_ids
- PeerSignalGraph: root_workflow, workflows, signal_handlers, connections, unresolved_signals

**From Story 8.2: WorkflowMetadata.signal_handlers**
- WorkflowMetadata has signal_handlers: tuple[SignalHandler, ...]

**From Epic 7: ExternalSignalCall Available**
- WorkflowMetadata has external_signals: tuple[ExternalSignalCall, ...]

### Testing Standards

**Test Fixtures** - Create temporary workflow files in pytest fixtures using `tmp_path`. Each test creates the necessary workflow structure.

**Test Coverage Target** - 100% coverage for signal_graph_analyzer.py

**Test Structure:**
```python
@pytest.fixture
def workflow_a(tmp_path: Path) -> Path:
    """Create workflow A that sends signal_b."""
    code = '''
from temporalio import workflow

@workflow.defn
class WorkflowA:
    @workflow.run
    async def run(self) -> None:
        handle = workflow.get_external_workflow_handle("WorkflowB", "wf-b-123")
        await handle.signal("signal_b", "data")
'''
    path = tmp_path / "workflow_a.py"
    path.write_text(code)
    return path


def test_analyze_two_connected_workflows(
    workflow_a: Path, workflow_b: Path, tmp_path: Path
) -> None:
    """Test analyzer discovers connected workflows."""
    analyzer = PeerSignalGraphAnalyzer(
        search_paths=[tmp_path],
        max_depth=10,
    )
    graph = analyzer.analyze(workflow_a)

    assert len(graph.workflows) == 2
    assert "WorkflowA" in graph.workflows
    assert "WorkflowB" in graph.workflows
    assert len(graph.connections) == 1

    conn = graph.connections[0]
    assert conn.sender_workflow == "WorkflowA"
    assert conn.receiver_workflow == "WorkflowB"
    assert conn.signal_name == "signal_b"
```

### Learnings from Previous Stories

**From Story 8.5: Data Model Pattern**
- PeerSignalGraph uses mutable collections internally during analysis, then returned as frozen dataclass
- Analyzer builds the graph incrementally, PeerSignalGraph captures final state

**From Story 8.3: Resolver Integration**
- SignalNameResolver.build_index() must be called before resolve()
- Resolver handles graceful degradation for invalid files
- Returns list[(Path, SignalHandler)] - multiple handlers possible

**From Story 8.4: Search Path Behavior**
- Recursive **/*.py globbing
- Skips __pycache__ directories
- Handles FileNotFoundError, PermissionError gracefully

### Edge Cases

1. **No external signals** - Entry workflow has no external_signals, PeerSignalGraph has only root workflow
2. **All signals unresolved** - No matching handlers found, all signals in unresolved_signals
3. **Empty search paths** - No handlers indexed, all signals unresolved
4. **Circular signals** - WorkflowA -> WorkflowB -> WorkflowA, both connections recorded, no infinite loop
5. **Deep chain at max depth** - Stops discovery but records partial graph

### FR Coverage

| AC | FR | Tech Spec Section | Description |
|----|----|--------------------|-------------|
| AC14 | FR87 | APIs and Interfaces --> _discover_connections (lines 524-564) | Recursive discovery |
| AC15 | FR87 | APIs and Interfaces --> _discover_connections (lines 546-552) | Cycle detection |
| AC16 | FR87 | APIs and Interfaces --> _discover_connections (lines 530-531) | Max depth limit |

### References

- [Tech Spec Epic 8: PeerSignalGraphAnalyzer API](../tech-spec-epic-8.md#apis-and-interfaces) (lines 444-565)
- [Tech Spec Epic 8: AC14-AC16](../tech-spec-epic-8.md#acceptance-criteria-authoritative) (lines 1003-1021)
- [Tech Spec Epic 8: Workflows and Sequencing](../tech-spec-epic-8.md#workflows-and-sequencing) (lines 713-806)
- [Architecture: ADR-006 Type Safety](../../architecture.md#adr-006-mypy-strict-mode-for-type-safety)
- [Story 8.3: Signal Name Resolver](8-3-signal-name-resolver.md)
- [Story 8.5: Signal Connection Model](8-5-signal-connection-model.md)

## Dev Agent Record

### Context Reference

`docs/sprint-artifacts/story-contexts/8-6-peer-signal-graph-analyzer-context.xml`

### Agent Model Used

(To be filled during implementation)

### Debug Log References

(To be filled during implementation)

### Completion Notes List

(To be filled during implementation)

### File List

**Created:**
- `src/temporalio_graphs/signal_graph_analyzer.py`
- `tests/test_signal_graph_analyzer.py`

**Modified:**
- `src/temporalio_graphs/__init__.py` - Add PeerSignalGraphAnalyzer export
