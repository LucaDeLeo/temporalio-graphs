# Story 8.11: Documentation

Status: review

## Story

As a Python developer using Temporal,
I want comprehensive documentation for the cross-workflow signal visualization feature,
So that I can easily understand and use the new `analyze_signal_graph()` function to visualize how my workflows communicate via signals.

## Acceptance Criteria

1. **README.md Updated** - README.md includes a new "Cross-Workflow Signal Visualization" section that:
   - Describes the `analyze_signal_graph()` function
   - Shows a quick example with Order -> Shipping signal flow
   - Explains the subgraph rendering mode with signal connections
   - Documents the new context options (6 fields from AC23 of Story 8.9)

2. **analyze_signal_graph() Documented** - The function documentation includes:
   - Clear description of cross-workflow signal analysis
   - All parameters documented (entry_workflow, search_paths, context)
   - Return value documented (Mermaid diagram string)
   - Usage example showing basic usage and with search_paths

3. **GraphBuildingContext Signal Options** - Document the 6 new context fields:
   - `resolve_signal_targets: bool = False`
   - `signal_target_search_paths: tuple[Path, ...] = ()`
   - `signal_resolution_strategy: Literal["by_name", "explicit", "hybrid"] = "by_name"`
   - `signal_visualization_mode: Literal["subgraph", "unified"] = "subgraph"`
   - `signal_max_discovery_depth: int = 10`
   - `warn_unresolved_signals: bool = True`

4. **CLAUDE.md Epic 8 Status Updated** - CLAUDE.md reflects Epic 8 completion:
   - Update "Current Status" section to include Epic 8 as complete
   - Add Epic 8 to the completed epics list
   - Update version to v0.4.0 if appropriate
   - Document cross-workflow signal visualization capability

5. **examples/signal_flow/ Documented** - The signal flow example is:
   - Referenced in README.md with description
   - Documented in `examples/signal_flow/expected_output.md` (already exists)
   - Listed in the Examples section of README.md

6. **Signal Visualization Syntax Documented** - README includes explanation of:
   - Subgraph syntax: `subgraph WorkflowName ... end`
   - Signal handler hexagons: `{{signal_name}}`
   - External signal trapezoids: `[/Signal 'name' to target\]`
   - Cross-subgraph dashed edges: `-.signal_name.->`
   - Handler styling: blue color `fill:#e6f3ff,stroke:#0066cc`

7. **Troubleshooting Section Updated** - Add cross-workflow signal troubleshooting:
   - "Signals not resolved" - check search_paths include target workflow directories
   - "Unresolved signal [/?/] node" - target workflow not found or no matching handler
   - "Multiple handlers warning" - multiple workflows handle same signal name

8. **No Regressions** - All existing tests continue passing after documentation updates

## Tasks / Subtasks

- [x] Update README.md with Cross-Workflow Signal Visualization section (AC: 1, 2, 5, 6)
  - [x] Add new section after "Multi-workflow graphs" section
  - [x] Add `analyze_signal_graph()` function documentation with example
  - [x] Document signal flow example (Order -> Shipping -> Notification)
  - [x] Explain subgraph rendering mode and signal connections
  - [x] Document signal visualization syntax (hexagons, trapezoids, dashed edges)
  - [x] Add examples/signal_flow/ to Examples section

- [x] Document GraphBuildingContext signal options (AC: 3)
  - [x] Add signal options to Configuration section in README.md
  - [x] Document each of the 6 new fields with descriptions
  - [x] Add example showing custom signal configuration

- [x] Update CLAUDE.md with Epic 8 completion (AC: 4)
  - [x] Update "Current Status" section header
  - [x] Add Epic 8 to completed epics list with description
  - [x] Document the cross-workflow signal visualization capability
  - [x] Update quality metrics if test count changed

- [x] Add signal troubleshooting to README.md (AC: 7)
  - [x] Add "Signals not resolved" troubleshooting entry
  - [x] Add "Unresolved signal [/?/] node" troubleshooting entry
  - [x] Add "Multiple handlers warning" troubleshooting entry

- [x] Verify no regressions (AC: 8)
  - [x] Run full test suite: `pytest -v`
  - [x] Verify all existing tests pass
  - [x] Run mypy strict mode: `mypy src/temporalio_graphs/`
  - [x] Run ruff linting: `ruff check src/temporalio_graphs/`

## Dev Notes

### Architecture Patterns and Constraints

**Documentation Structure** - Following existing README.md patterns:
1. Each major feature has its own section with code examples
2. Configuration section shows GraphBuildingContext usage
3. Troubleshooting section lists common issues with solutions
4. Examples section references all working examples

**README.md Section Order:**
```
# temporalio-graphs
## What it does
## Install
## Quick start
## Configuration (GraphBuildingContext)
## Multi-workflow graphs
## Cross-Workflow Signal Visualization  <-- NEW
## Examples
## Troubleshooting
## Development
## Reference
```

### Key Documentation Content

**analyze_signal_graph() Example:**
```python
from temporalio_graphs import analyze_signal_graph, GraphBuildingContext

# Analyze workflows that signal each other
diagram = analyze_signal_graph(
    "workflows/order_workflow.py",
    search_paths=["workflows/"],
)
print(diagram)  # Mermaid diagram with connected subgraphs
```

**Signal Context Options:**
```python
context = GraphBuildingContext(
    signal_max_discovery_depth=10,  # max workflow discovery depth
    warn_unresolved_signals=True,   # warn when signal has no handler
)
```

**Signal Flow Visualization Example:**
```
OrderWorkflow                 ShippingWorkflow              NotificationWorkflow
+------------------+          +------------------+          +---------------------+
| process_order    |          | @workflow.signal |          | @workflow.signal    |
|        |         |  signal  |   ship_order     |  signal  |   notify_shipped    |
|        v         |--------->|        |         |--------->|         |           |
| [ship_order]     |          |        v         |          |         v           |
|        |         |          | ship_package     |          | send_notification   |
|        v         |          |        |         |          +---------------------+
| complete_order   |          |        v         |
+------------------+          | [notify_shipped] |
                              +------------------+
```

### CLAUDE.md Updates

**Current Status Section Update:**
```markdown
**Completed Epics (1-8):**
- Epic 1: Foundation & Project Setup
- Epic 2: Basic Graph Generation (Linear Workflows)
- Epic 3: Decision Node Support (Branching Workflows)
- Epic 4: Signal & Wait Condition Support
- Epic 5: Production Hardening & Quality
- Epic 6: Cross-Workflow Visualization (Parent-Child)
- Epic 7: Peer-to-Peer Workflow Signaling (External Signals)
- Epic 8: Cross-Workflow Signal Visualization (Connected Subgraphs)
```

### Learnings from Previous Stories

**From Story 8.10: Integration Tests Complete**
- 716 tests passing, 87.92% coverage
- examples/signal_flow/ directory already exists with all required files
- expected_output.md provides good documentation template

**From Story 5.5: Production-Grade Documentation**
- README.md follows established pattern with sections
- Code examples should be minimal but complete
- Troubleshooting section highly valuable for users

### Files to Modify

**README.md:**
- Add new section "Cross-Workflow Signal Visualization"
- Update "Examples" section with signal_flow reference
- Update "Troubleshooting" section with signal-related issues
- Update "Configuration" section with signal context options

**CLAUDE.md:**
- Update "Current Status" section
- Update completed epics list
- Add Epic 8 capabilities description

### FR Coverage

This story covers documentation requirements implicit in Epic 8:
- Document analyze_signal_graph() function (FR90)
- Document context extensions (FR90)
- Provide usage examples
- Update project status documentation

### References

- [Tech Spec Epic 8: Examples & Documentation](../tech-spec-epic-8.md#in-scope) (lines 86-91)
- [Story 8.10: Integration Tests](8-10-integration-tests.md) - Example files created
- [Story 8.9: Public API](8-9-public-api.md) - Function implementation details
- [examples/signal_flow/expected_output.md](../../../examples/signal_flow/expected_output.md) - Golden diagram
- [Existing README.md](../../../README.md) - Documentation patterns

## Dev Agent Record

### Context Reference

`docs/sprint-artifacts/story-contexts/8-11-documentation-context.xml`

### Agent Model Used

claude-opus-4-5-20251101

### Debug Log References

N/A - documentation-only story

### Completion Notes List

**Implementation Summary:**
- Updated README.md with comprehensive Cross-Workflow Signal Visualization documentation
- Added "Signal Visualization Options" subsection to Configuration section (6 new context fields)
- Added signal_flow example reference to Examples section
- Added 3 signal-related troubleshooting entries
- Updated CLAUDE.md with Epic 8 completion status (Epics 1-8 complete)
- Updated quality metrics: 716 tests, 88% coverage

**Key Documentation Additions:**
1. README.md - New "Cross-Workflow Signal Visualization" section with:
   - `analyze_signal_graph()` function usage example
   - Mermaid output example showing Order -> Shipping -> Notification chain
   - Signal visualization syntax reference table
   - Signal types comparison table (Internal vs Parent-Child vs Peer-to-Peer)

2. README.md - Configuration section additions:
   - 6 new GraphBuildingContext signal options documented with table
   - Example code showing custom signal configuration

3. README.md - Examples section:
   - Added `examples/signal_flow/run.py` with description

4. README.md - Troubleshooting section:
   - "Signals not resolved" - search_paths configuration
   - "Unresolved signal `[/?/]` node" - handler not found
   - "Multiple handlers warning" - naming conflicts

5. CLAUDE.md updates:
   - Current Status updated to reflect Epics 1-8 complete
   - Quality metrics updated: 716 tests, 88% coverage
   - Core Components list updated with Epic 6-8 analyzers
   - Examples section updated to include signal_flow/

**Files Modified:**
- README.md - Added ~80 lines of documentation
- CLAUDE.md - Updated status, metrics, components list

**Files Created:**
- None (documentation-only story)

**Test Results:**
- 716 tests passing
- 87.92% coverage
- mypy: Success (no issues found in 16 source files)
- ruff check: All checks passed

**Acceptance Criteria Satisfaction:**
- AC1: README.md Updated - SATISFIED (new Cross-Workflow Signal Visualization section added)
- AC2: analyze_signal_graph() Documented - SATISFIED (function with parameters and examples)
- AC3: GraphBuildingContext Signal Options - SATISFIED (6 fields documented in table)
- AC4: CLAUDE.md Epic 8 Status Updated - SATISFIED (Epics 1-8 listed as complete)
- AC5: examples/signal_flow/ Documented - SATISFIED (added to Examples section)
- AC6: Signal Visualization Syntax Documented - SATISFIED (syntax table with hexagons, trapezoids, dashed edges)
- AC7: Troubleshooting Section Updated - SATISFIED (3 signal-related entries added)
- AC8: No Regressions - SATISFIED (716 tests pass, mypy and ruff clean)
