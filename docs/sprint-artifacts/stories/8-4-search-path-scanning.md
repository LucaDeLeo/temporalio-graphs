# Story 8.4: Search Path Scanning

Status: done

## Story

As a library developer,
I want the SignalNameResolver to scan configurable search paths and index signal handlers,
So that external signals can be resolved to their target workflows across the codebase.

## Implementation Status

**ALREADY COMPLETE** - This story's functionality was fully implemented as part of Story 8-3 (Signal Name Resolver).

The `SignalNameResolver.build_index()` method in `src/temporalio_graphs/resolver.py` already implements:
- Recursive directory scanning using `Path.glob("**/*.py")`
- Signal handler indexing into `_handler_index` dict
- Default search path support (via `analyze_signal_flow()` API which will be implemented in Story 8-9)
- Graceful error handling for invalid files
- `__pycache__` directory exclusion

**Test Coverage:**
- 25 tests in `tests/test_resolver.py` verify scanning functionality
- Tests include: nested directories, multiple search paths, invalid files, symlinks

## Acceptance Criteria

1. **AC10: Search Path Scanning (FR85)** - COMPLETE
   - GIVEN search_paths = ["/workflows", "/services"]
   - WHEN SignalNameResolver.build_index() called
   - THEN scans all .py files in both directories recursively
   - AND builds index of signal handlers
   - **Implementation:** `resolver.py` lines 106-146 implement recursive glob scanning

2. **AC11: Default Search Path** - DEFERRED TO STORY 8-9
   - GIVEN analyze_signal_flow(entry_workflow) called with NO search_paths
   - THEN search_paths defaults to [entry_workflow.parent]
   - **Note:** This AC is part of the public API (Story 8-9), not the resolver itself. The resolver accepts search_paths as constructor argument; the default is set by the API layer.

## Tasks / Subtasks

All tasks completed in Story 8-3:

- [x] Recursive directory scanning with `Path.glob("**/*.py")` (AC: 1)
- [x] Handler index building: `_handler_index[signal_name] = [(path, handler), ...]` (AC: 1)
- [x] Skip `__pycache__` directories (quality improvement)
- [x] Graceful error handling for parse failures (NFR-REL-2)
- [x] Logging for observability (NFR-OBS-1)
- [x] Unit tests for nested directories (AC: 1)
- [x] Unit tests for multiple search paths (AC: 1)
- [x] Unit tests for edge cases (symlinks, invalid files)

## Dev Notes

### Why This Story Is Already Complete

Story 8-3 (Signal Name Resolver) was designed to be the core resolver class, and AC3 of that story explicitly covered:
> **Build Index Method** - `build_index()` method scans search paths and builds internal index mapping signal_name to list of (file_path, SignalHandler) tuples (AC10 from Tech Spec lines 979-982)

The tech spec organized stories by component, but the resolver's scanning functionality is integral to `build_index()` and was implemented atomically.

### Key Implementation Details from Story 8-3

**Scanning Implementation (`resolver.py` lines 106-146):**
```python
for search_path in self._search_paths:
    if not search_path.exists():
        logger.warning("Search path does not exist: %s", search_path)
        continue

    # Recursively find all Python files
    for file_path in search_path.glob("**/*.py"):
        # Skip __pycache__ directories
        if "__pycache__" in str(file_path):
            continue

        metadata = self._analyze_file(file_path)
        if metadata and metadata.signal_handlers:
            self._workflow_cache[file_path] = metadata
            for handler in metadata.signal_handlers:
                if handler.signal_name not in self._handler_index:
                    self._handler_index[handler.signal_name] = []
                self._handler_index[handler.signal_name].append((file_path, handler))
```

**Performance Characteristics (NFR-PERF-2):**
- Index built once, reused for all resolutions
- O(n) for scanning n files during build_index()
- O(1) for signal resolution via hash map lookup

**Error Handling (NFR-REL-2):**
- Non-existent search paths: log warning, continue
- Non-directory paths: log warning, continue
- Parse errors: log warning, skip file, continue
- Permission errors: log warning, skip file, continue

### FR Coverage

| AC | FR | Tech Spec Section | Status |
|----|----|--------------------|--------|
| AC10 | FR85 | APIs and Interfaces --> build_index | COMPLETE (Story 8-3) |
| AC11 | FR85 | APIs and Interfaces --> analyze_signal_flow | DEFERRED to Story 8-9 |

### References

- [Tech Spec Epic 8: AC10-AC11](../tech-spec-epic-8.md#acceptance-criteria-authoritative) (lines 979-985)
- [Story 8.3: Signal Name Resolver](8-3-signal-name-resolver.md)
- [resolver.py Implementation](../../../src/temporalio_graphs/resolver.py)
- [test_resolver.py Tests](../../../tests/test_resolver.py)

## Dev Agent Record

### Context Reference

N/A - Story already complete from Story 8-3 implementation

### Agent Model Used

claude-opus-4-5-20251101 (story creation only - no implementation needed)

### Debug Log References

N/A - No new implementation required

### Completion Notes List

1. **Already Implemented**: All scanning functionality was implemented in Story 8-3
2. **Test Coverage**: 25 tests verify all scanning scenarios
3. **AC11 Deferred**: Default search path behavior is part of public API (Story 8-9)
4. **Story Status**: Marked as `done` since functionality exists and is tested

### File List

**Created:**
- None (functionality already exists)

**Modified:**
- `docs/sprint-artifacts/stories/8-4-search-path-scanning.md` - This story file

**Verified Existing:**
- `src/temporalio_graphs/resolver.py` - Contains build_index() with scanning
- `tests/test_resolver.py` - Contains 25 tests including scanning tests
