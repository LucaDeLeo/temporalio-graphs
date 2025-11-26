# Story 8.9: Public API

Status: done

## Story

As a Python developer using Temporal,
I want a simple `analyze_signal_graph()` function to analyze cross-workflow signal flows,
So that I can generate connected workflow diagrams showing how my workflows communicate via signals with minimal code.

## Acceptance Criteria

1. **AC22: Public API analyze_signal_graph (FR90)** - Given `analyze_signal_graph()` function, then accepts: `entry_workflow` (Path|str), `search_paths` (optional), `context` (optional), returns Mermaid diagram string, raises `FileNotFoundError` if entry_workflow missing, raises `WorkflowParseError` if not valid workflow

2. **AC23: Context Extensions** - Given `GraphBuildingContext`, then includes new fields:
   - `resolve_signal_targets: bool = False`
   - `signal_target_search_paths: tuple[Path, ...] = ()`
   - `signal_resolution_strategy: Literal["by_name", "explicit", "hybrid"] = "by_name"`
   - `signal_visualization_mode: Literal["subgraph", "unified"] = "subgraph"`
   - `signal_max_discovery_depth: int = 10`
   - `warn_unresolved_signals: bool = True`

3. **AC11: Default Search Path** - Given `analyze_signal_graph(entry_workflow)` called with NO `search_paths`, then search_paths defaults to `[entry_workflow.parent]`

4. **Function Signature** - `analyze_signal_graph()` has signature:
   ```python
   def analyze_signal_graph(
       entry_workflow: Path | str,
       search_paths: list[Path | str] | None = None,
       context: GraphBuildingContext | None = None,
   ) -> str:
   ```

5. **Integration with PeerSignalGraphAnalyzer** - Function:
   - Creates `SignalNameResolver` with resolved search_paths
   - Creates `PeerSignalGraphAnalyzer` with resolver and context
   - Calls `analyzer.analyze(entry_path)` to build `PeerSignalGraph`
   - Calls `MermaidRenderer.render_signal_graph(graph)` to produce output

6. **Export from Public API** - `analyze_signal_graph` is:
   - Defined in `src/temporalio_graphs/__init__.py`
   - Added to `__all__` list for explicit public API

7. **Type Safety** - Complete type hints for mypy strict mode compliance (ADR-006)

8. **Google-Style Docstring** - Function has comprehensive docstring with:
   - Description of cross-workflow signal analysis
   - Args section documenting all parameters
   - Returns section describing Mermaid output
   - Raises section listing possible exceptions
   - Example section showing usage (FR41)

9. **Unit Tests** - Unit tests in `tests/test_api.py` verify:
   - `test_analyze_signal_graph_basic()` - basic usage with entry workflow
   - `test_analyze_signal_graph_with_search_paths()` - explicit search paths
   - `test_analyze_signal_graph_default_search_path()` - defaults to entry parent
   - `test_analyze_signal_graph_file_not_found()` - raises FileNotFoundError
   - `test_analyze_signal_graph_invalid_workflow()` - raises WorkflowParseError
   - `test_context_signal_options()` - validates new context fields

10. **No Regressions** - All existing Epic 1-8.8 tests continue passing

## Tasks / Subtasks

- [x] Extend GraphBuildingContext with signal options (AC: 2)
  - [x] In `src/temporalio_graphs/context.py`:
    - [x] Add `resolve_signal_targets: bool = False` field
    - [x] Add `signal_target_search_paths: tuple[Path, ...] = ()` field
    - [x] Add `signal_resolution_strategy: Literal["by_name", "explicit", "hybrid"] = "by_name"` field
    - [x] Add `signal_visualization_mode: Literal["subgraph", "unified"] = "subgraph"` field
    - [x] Add `signal_max_discovery_depth: int = 10` field
    - [x] Add `warn_unresolved_signals: bool = True` field
  - [x] Add required imports (`Path` from pathlib, `Literal` from typing)
  - [x] Update docstring to document new fields

- [x] Implement analyze_signal_graph function (AC: 1, 3, 4, 5, 7, 8)
  - [x] In `src/temporalio_graphs/__init__.py`:
    - [x] Add imports: `SignalNameResolver` from resolver, `Path` from pathlib
    - [x] Define function signature per AC4
    - [x] Implement input validation:
      - [x] Check `entry_workflow is not None`
      - [x] Convert to `Path` object
      - [x] Check file exists, raise `FileNotFoundError` if not
    - [x] Implement search_paths resolution:
      - [x] If `search_paths is None`, default to `[entry_path.parent]` (AC11)
      - [x] Otherwise convert all paths to `Path` objects
    - [x] Create default context if None provided
    - [x] Implement analysis pipeline:
      - [x] Create `SignalNameResolver(search_paths)`
      - [x] Create `PeerSignalGraphAnalyzer(search_paths, resolver, context.signal_max_discovery_depth, context)`
      - [x] Call `analyzer.analyze(entry_path)` to get `PeerSignalGraph`
      - [x] Create `MermaidRenderer(context)`
      - [x] Call `renderer.render_signal_graph(graph)` to get output
    - [x] Return Mermaid diagram string
    - [x] Add comprehensive Google-style docstring (AC8)

- [x] Update public API exports (AC: 6)
  - [x] In `src/temporalio_graphs/__init__.py`:
    - [x] Add `"analyze_signal_graph"` to `__all__` list
    - [x] Add `SignalNameResolver` import (if not already present)

- [x] Create unit tests (AC: 9)
  - [x] Create or extend `tests/test_public_api.py`:
    - [x] `test_analyze_signal_graph_basic()` - analyze single workflow, returns Mermaid string
    - [x] `test_analyze_signal_graph_with_search_paths()` - explicit search paths used
    - [x] `test_analyze_signal_graph_default_search_path()` - verify defaults to entry parent
    - [x] `test_analyze_signal_graph_file_not_found()` - raises FileNotFoundError for missing file
    - [x] `test_analyze_signal_graph_invalid_workflow()` - raises WorkflowParseError for non-workflow
    - [x] `test_context_signal_options()` - verify new GraphBuildingContext fields exist with defaults
    - [x] `test_analyze_signal_graph_with_context()` - custom context passed through pipeline
    - [x] `test_analyze_signal_graph_exported()` - verify in __all__
    - [x] `test_analyze_signal_graph_docstring()` - verify comprehensive docstring
    - [x] `test_analyze_signal_graph_type_hints()` - verify type annotations
  - [x] Create test fixtures:
    - [x] Simple workflow file for basic test (order_workflow.py)
    - [x] Connected workflows for search path test (shipping_workflow.py)
    - [x] Non-workflow Python file for parse error test (not_a_workflow.py)

- [x] Verify no regressions (AC: 10)
  - [x] Run full test suite: `pytest -v`
  - [x] Verify all existing tests pass (701 tests passing)
  - [x] Run mypy strict mode: `mypy src/temporalio_graphs/` (Success)
  - [x] Run ruff linting: `ruff check src/temporalio_graphs/` (All checks passed)
  - [x] Verify test coverage remains >=80% (87.92%)

## Dev Notes

### Architecture Patterns and Constraints

**Public API Design Pattern** - Following the existing `analyze_workflow()` and `analyze_workflow_graph()` patterns in `__init__.py`:
1. Accept Path|str for flexibility
2. Accept optional context with sensible defaults
3. Raise clear exceptions for error conditions
4. Return Mermaid string for easy consumption
5. Comprehensive Google-style docstring with examples

**Function Structure Template:**
```python
def analyze_signal_graph(
    entry_workflow: Path | str,
    search_paths: list[Path | str] | None = None,
    context: GraphBuildingContext | None = None,
) -> str:
    """Analyze workflows and visualize cross-workflow signal connections.

    Starting from an entry workflow, discovers all connected workflows
    by following external signal sends to their signal handlers. Renders
    the complete signal flow graph as a Mermaid diagram with subgraphs.

    Args:
        entry_workflow: Path to the entry point workflow file.
        search_paths: Directories to search for target workflows.
            Defaults to the directory containing entry_workflow.
        context: Configuration options for graph generation.

    Returns:
        Mermaid diagram string showing all connected workflows
        with signal flow edges between them.

    Example:
        >>> result = analyze_signal_graph(
        ...     "workflows/order_workflow.py",
        ...     search_paths=["workflows/", "services/"],
        ... )
        >>> print(result)
        ```mermaid
        flowchart TB
            subgraph OrderWorkflow
                ...
            end
            subgraph ShippingWorkflow
                ...
            end
            ext_sig_ship_order_56 -.ship_order.-> sig_handler_ship_order_67
        ```

    Raises:
        FileNotFoundError: If entry_workflow does not exist.
        WorkflowParseError: If entry_workflow is not a valid workflow.
    """
    entry_path = Path(entry_workflow)
    if not entry_path.exists():
        raise FileNotFoundError(f"Workflow file not found: {entry_path}")

    # Default search paths to entry workflow's directory
    if search_paths is None:
        resolved_paths = [entry_path.parent]
    else:
        resolved_paths = [Path(p) for p in search_paths]

    # Create default context if not provided
    if context is None:
        context = GraphBuildingContext()

    # Create analyzer and analyze
    resolver = SignalNameResolver(resolved_paths)
    analyzer = PeerSignalGraphAnalyzer(
        search_paths=resolved_paths,
        resolver=resolver,
        max_depth=context.signal_max_discovery_depth,
        context=context,
    )
    graph = analyzer.analyze(entry_path)

    # Render to Mermaid
    renderer = MermaidRenderer(context)
    return renderer.render_signal_graph(graph)
```

### Key Components

**File Locations:**
- Context extension: `src/temporalio_graphs/context.py`
- Public API function: `src/temporalio_graphs/__init__.py`
- Tests: `tests/test_api.py`

**GraphBuildingContext Extension (from Tech Spec lines 254-280):**
```python
@dataclass(frozen=True)
class GraphBuildingContext:
    # ... existing fields ...

    # Epic 8: Cross-workflow signal options
    resolve_signal_targets: bool = False
    signal_target_search_paths: tuple[Path, ...] = ()
    signal_resolution_strategy: Literal["by_name", "explicit", "hybrid"] = "by_name"
    signal_visualization_mode: Literal["subgraph", "unified"] = "subgraph"
    signal_max_discovery_depth: int = 10
    warn_unresolved_signals: bool = True
```

### Dependencies from Previous Stories

**From Story 8.8: render_signal_graph Available**
- `MermaidRenderer.render_signal_graph(graph: PeerSignalGraph)` method exists
- Returns complete Mermaid diagram with subgraphs and cross-subgraph edges

**From Story 8.6: PeerSignalGraphAnalyzer Available**
- `PeerSignalGraphAnalyzer` class with `analyze(entry_workflow: Path)` method
- Returns `PeerSignalGraph` with all connected workflows

**From Story 8.3: SignalNameResolver Available**
- `SignalNameResolver` class with search path support
- Used by `PeerSignalGraphAnalyzer` internally

**From Story 8.5: Data Models**
- `PeerSignalGraph` dataclass containing all graph data
- `SignalConnection` for workflow connections

### Learnings from Previous Stories

**From Story 8.8: Complete Rendering Pipeline**
- render_signal_graph produces valid Mermaid with subgraphs and edges
- 689 tests passing after Story 8.8
- Pattern for handling optional empty lists (connections, unresolved)

**From Story 2.6: analyze_workflow Pattern**
- Input validation with clear exceptions
- Context default handling
- File path conversion with Path()
- Comprehensive docstring with examples

**From Story 6.3: analyze_workflow_graph Pattern**
- Multi-workflow analysis pattern
- Search path resolution with parent directory default
- Call graph analyzer integration

### Edge Cases

1. **Entry workflow has no external signals** - Returns single subgraph diagram with no connections
2. **Entry workflow doesn't exist** - Raises FileNotFoundError with path in message
3. **Entry workflow is invalid Python** - WorkflowParseError from analyzer
4. **Entry workflow has no @workflow.defn** - WorkflowParseError from analyzer
5. **Empty search_paths list** - Uses empty list (no resolution possible)
6. **None context** - Creates default GraphBuildingContext
7. **Search paths don't exist** - Logged warning, graceful degradation

### FR Coverage

| AC | FR | Tech Spec Section | Description |
|----|----|--------------------|-------------|
| AC22 | FR90 | APIs and Interfaces --> analyze_signal_flow (lines 569-638) | Public API function |
| AC23 | FR90 | Data Models --> GraphBuildingContext (lines 254-280) | Context extensions |
| AC11 | FR85 | APIs and Interfaces --> analyze_signal_flow (lines 623-625) | Default search path |

### References

- [Tech Spec Epic 8: Public API](../tech-spec-epic-8.md#apis-and-interfaces) (lines 567-638)
- [Tech Spec Epic 8: GraphBuildingContext Extension](../tech-spec-epic-8.md#data-models-and-contracts) (lines 254-280)
- [Tech Spec Epic 8: AC22, AC23](../tech-spec-epic-8.md#acceptance-criteria-authoritative) (lines 1051-1066)
- [Architecture: ADR-006 Type Safety](../../architecture.md#adr-006-mypy-strict-mode-for-type-safety)
- [Story 8.8: Cross-Subgraph Edges](8-8-cross-subgraph-edges.md)
- [Story 8.6: Peer Signal Graph Analyzer](8-6-peer-signal-graph-analyzer.md)
- [Existing analyze_workflow() Implementation](../../../src/temporalio_graphs/__init__.py)

## Dev Agent Record

### Context Reference

`docs/sprint-artifacts/story-contexts/8-9-public-api-context.xml`

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None - implementation proceeded without issues.

### Completion Notes List

**Implementation Summary:**
1. Extended GraphBuildingContext with 6 new fields for Epic 8 signal visualization (lines 134-173 in context.py)
2. Implemented analyze_signal_graph() public API function (lines 244-355 in __init__.py)
3. Added 12 new unit tests for the public API (lines 439-645 in test_public_api.py)
4. Created test fixtures for peer signal workflow testing (tests/fixtures/peer_signal_workflows/)

**Key Implementation Decisions:**
- Used FileNotFoundError (not WorkflowParseError) for missing entry_workflow to provide clear distinction between "file doesn't exist" vs "file exists but isn't valid"
- Followed existing analyze_workflow() and analyze_workflow_graph() patterns for consistency
- Default search_paths to [entry_workflow.parent] enables zero-config usage when workflows are co-located
- Function integrates SignalNameResolver -> PeerSignalGraphAnalyzer -> MermaidRenderer pipeline

**Files Modified:**
- src/temporalio_graphs/context.py - Added 6 new context fields with docstrings (lines 134-173)
- src/temporalio_graphs/__init__.py - Added SignalNameResolver import, analyze_signal_graph to __all__, function implementation (lines 35, 45, 244-355)
- tests/test_public_api.py - Updated __all__ test, added 4 new test classes with 12 tests (lines 359, 434-645)

**Files Created:**
- tests/fixtures/peer_signal_workflows/order_workflow.py - Entry workflow with external signal
- tests/fixtures/peer_signal_workflows/shipping_workflow.py - Target workflow with signal handler
- tests/fixtures/peer_signal_workflows/not_a_workflow.py - Non-workflow Python file for error testing
- tests/fixtures/peer_signal_workflows/invalid_python.py - Syntax error file for error testing

**Test Results:**
- 701 tests passing (12 new tests added)
- 87.92% test coverage (above 80% threshold)
- mypy strict mode: Success (no issues)
- ruff linting: All checks passed

**AC Satisfaction Evidence:**
- AC22 (FR90): analyze_signal_graph() implemented with Path|str input, search_paths, context - test_analyze_signal_graph_basic() at line 442
- AC23: 6 new GraphBuildingContext fields with defaults - test_context_signal_options_exist() at line 536
- AC11 (FR85): Default search path to entry_workflow.parent - test_analyze_signal_graph_default_search_path() at line 490
- AC4: Function signature matches spec - verified in test_analyze_signal_graph_type_hints() at line 631
- AC5: Integration with PeerSignalGraphAnalyzer/MermaidRenderer - test_analyze_signal_graph_with_search_paths() at line 472 shows resolved connections
- AC6: Exported in __all__ - test_analyze_signal_graph_exported() at line 596
- AC7: Complete type hints - test_analyze_signal_graph_type_hints() at line 631
- AC8: Google-style docstring - test_analyze_signal_graph_docstring() at line 609
- AC9: Unit tests created - 12 tests in 4 test classes
- AC10: No regressions - 701 tests pass, 87.92% coverage

## Senior Developer Review (AI)

### Review Outcome: APPROVED

**Review Date:** 2025-11-26
**Reviewer:** Claude Opus 4.5 (Senior Developer Code Review Specialist)

### Executive Summary

Story 8-9 has been thoroughly reviewed and APPROVED. The implementation follows existing API patterns excellently, provides comprehensive documentation, and includes robust test coverage. All 10 acceptance criteria have been validated with code evidence.

### Acceptance Criteria Validation

| AC | Status | Evidence |
|----|--------|----------|
| AC22: Public API analyze_signal_graph (FR90) | IMPLEMENTED | `src/temporalio_graphs/__init__.py:244-355` - Function accepts Path\|str entry_workflow, optional search_paths, optional context, returns Mermaid string, raises FileNotFoundError (line 329) and WorkflowParseError (via analyzer) |
| AC23: Context Extensions | IMPLEMENTED | `src/temporalio_graphs/context.py:134-173` - All 6 fields added with correct types and defaults: resolve_signal_targets=False, signal_target_search_paths=(), signal_resolution_strategy="by_name", signal_visualization_mode="subgraph", signal_max_discovery_depth=10, warn_unresolved_signals=True |
| AC11: Default Search Path | IMPLEMENTED | `src/temporalio_graphs/__init__.py:332-333` - When search_paths is None, defaults to [entry_path.parent] |
| AC4: Function Signature | IMPLEMENTED | `src/temporalio_graphs/__init__.py:244-248` - Exact signature match: `def analyze_signal_graph(entry_workflow: Path \| str, search_paths: list[Path \| str] \| None = None, context: GraphBuildingContext \| None = None) -> str` |
| AC5: Integration with PeerSignalGraphAnalyzer | IMPLEMENTED | `src/temporalio_graphs/__init__.py:341-355` - Creates SignalNameResolver, PeerSignalGraphAnalyzer, calls analyzer.analyze(), renders via MermaidRenderer.render_signal_graph() |
| AC6: Export from Public API | IMPLEMENTED | `src/temporalio_graphs/__init__.py:45` - "analyze_signal_graph" added to __all__ list |
| AC7: Type Safety | IMPLEMENTED | All parameters and return type have complete type hints, mypy strict mode passes with 0 issues |
| AC8: Google-Style Docstring | IMPLEMENTED | `src/temporalio_graphs/__init__.py:249-320` - Comprehensive docstring with Args, Returns, Raises, Example sections |
| AC9: Unit Tests | IMPLEMENTED | `tests/test_public_api.py:439-645` - 12 new tests in 4 test classes covering basic usage, error handling, context options, and exports |
| AC10: No Regressions | IMPLEMENTED | 701 tests pass, 87.92% coverage, mypy clean, ruff clean |

### Task Completion Validation

| Task | Status | Evidence |
|------|--------|----------|
| Extend GraphBuildingContext with signal options | VERIFIED | `context.py:134-173` - 6 fields with docstrings |
| Implement analyze_signal_graph function | VERIFIED | `__init__.py:244-355` - Complete implementation |
| Update public API exports | VERIFIED | `__init__.py:45` - Added to __all__ |
| Create unit tests | VERIFIED | `test_public_api.py:439-645` - 12 tests |
| Verify no regressions | VERIFIED | 701 tests pass, coverage 87.92% |

### Code Quality Assessment

**Strengths:**
1. **API Consistency** - analyze_signal_graph() follows the exact same patterns as analyze_workflow() and analyze_workflow_graph() (input validation, context defaults, Path conversion)
2. **Error Handling** - Proper distinction between FileNotFoundError (file missing) vs WorkflowParseError (invalid workflow)
3. **Type Safety** - Complete type hints, mypy strict mode clean
4. **Documentation** - Comprehensive Google-style docstring with examples
5. **Test Coverage** - 12 focused tests covering happy path, error cases, context options

**Code Organization:**
- Clean separation between input validation, path resolution, analysis, and rendering
- Follows existing patterns in the codebase
- No dead code or unnecessary complexity

### Test Coverage Analysis

| Test Area | Coverage | Notes |
|-----------|----------|-------|
| Basic functionality | 100% | test_analyze_signal_graph_basic, test_analyze_signal_graph_string_path |
| Search paths | 100% | test_analyze_signal_graph_with_search_paths, test_analyze_signal_graph_default_search_path |
| Error handling | 100% | test_analyze_signal_graph_file_not_found, test_analyze_signal_graph_invalid_workflow |
| Context options | 100% | test_context_signal_options_exist, test_context_signal_options_custom_values, test_analyze_signal_graph_with_context |
| Export/Documentation | 100% | test_analyze_signal_graph_exported, test_analyze_signal_graph_docstring, test_analyze_signal_graph_type_hints |

**Test Fixtures:**
- `order_workflow.py` - Entry workflow with external signal
- `shipping_workflow.py` - Target workflow with signal handler
- `not_a_workflow.py` - Non-workflow file for error testing
- `invalid_python.py` - Syntax error file for error testing

### Security Notes

No security concerns identified. The function:
- Only reads files (no writes except optional graph_output_file in context)
- Uses Path for safe path handling
- No user input reaches shell or eval

### Action Items

None. Implementation is complete and meets all acceptance criteria.

### Issues Summary

| Severity | Count | Details |
|----------|-------|---------|
| CRITICAL | 0 | - |
| HIGH | 0 | - |
| MEDIUM | 0 | - |
| LOW | 0 | - |

### Verification Commands

```bash
# All tests pass
pytest tests/test_public_api.py -v  # 37 tests pass

# Full test suite passes
pytest -v  # 701 tests pass, 87.92% coverage

# Type checking clean
mypy src/temporalio_graphs/__init__.py src/temporalio_graphs/context.py --strict  # Success: no issues

# Linting clean
ruff check src/temporalio_graphs/__init__.py src/temporalio_graphs/context.py  # All checks passed

# Function works end-to-end
python -c "from temporalio_graphs import analyze_signal_graph; print(analyze_signal_graph('tests/fixtures/peer_signal_workflows/order_workflow.py'))"
```

### Next Steps

Story is complete and ready for deployment. Proceed to Story 8-10 (Integration Tests) and Story 8-11 (Documentation).
