# Epic Technical Specification: Peer-to-Peer Workflow Signaling Visualization

Date: 2025-11-20
Author: Luca
Epic ID: 7
Status: Draft

---

## Overview

This epic extends the temporalio-graphs library to visualize asynchronous signal communication between independent Temporal workflows (peer-to-peer pattern). Unlike Epic 4's internal signals (wait_condition for workflow's own state) and Epic 6's parent-child orchestration (execute_child_workflow), this epic addresses external signaling where Workflow A sends signals to Workflow B via `workflow.get_external_workflow_handle()`.

The implementation uses static code analysis to detect external workflow handles, signal method calls, and target workflow patterns. External signals render as distinct trapezoid shapes with dashed edges in Mermaid diagrams, clearly differentiating asynchronous peer communication from synchronous operations.

This completes the library's workflow interaction pattern coverage:
- Epic 2: Activities (sequential operations)
- Epic 4: Internal Signals (wait_condition for own state)
- Epic 6: Parent-Child (execute_child_workflow orchestration)
- **Epic 7: Peer-to-Peer Signals (external signal communication)**

Real-world use cases include order workflows signaling shipping workflows, payment workflows notifying fulfillment workflows, and saga compensation patterns.

## Objectives and Scope

### In Scope

**Detection & Analysis:**
- Detect `workflow.get_external_workflow_handle()` calls in workflow source code (FR74)
- Detect `.signal()` method calls on external workflow handles (FR75)
- Extract signal names from `.signal(signal_name, payload)` arguments (FR76)
- Extract target workflow patterns from handle creation (string literals, format strings, dynamic) (FR77)
- Track handle assignments in AST (two-step and inline patterns)
- Store external signal metadata in WorkflowMetadata

**Visualization:**
- Render external signal nodes as trapezoid shapes in Mermaid: `[/SignalName\\]` (FR78)
- Render external signal edges as dashed lines: `-.signal.->` (FR79)
- Display target workflow pattern in signal labels when deterministic (FR80)
- Apply orange/amber color styling to distinguish external signals
- Support configurable label styles (name-only, target-pattern)

**Data Models:**
- Create ExternalSignalCall dataclass with signal metadata
- Add EXTERNAL_SIGNAL node type to NodeType enum
- Extend WorkflowMetadata to include external_signals tuple
- Ensure frozen (immutable) dataclass per Architecture pattern

**Integration:**
- Integrate ExternalSignalDetector into WorkflowAnalyzer pipeline
- Handle external signals in PathPermutationGenerator (sequential nodes, no branching)
- Add configuration options to GraphBuildingContext (toggle visibility, label style)

**Examples & Documentation:**
- Create Order → Shipping peer signal workflow example (FR81)
- Add peer-to-peer section to README with rendered diagram
- Document ADR-012: Peer-to-Peer Signal Detection strategy
- Update CHANGELOG.md for v0.3.0

### Out of Scope

**Deferred to Future:**
- Runtime signal verification (library is static analysis only)
- Signal payload type analysis (focus on signal flow, not payload structure)
- Bidirectional signal visualization (only outgoing signals from analyzed workflow)
- Signal handler detection in target workflow (only send-side analysis)
- Cross-system signals (signals to non-Temporal services)
- Signal ordering/sequence guarantees (Temporal runtime concern)

**Explicit Exclusions:**
- Inline expansion of target workflow graphs (each workflow analyzed independently)
- Signal execution history analysis (history-based, not static analysis)
- Dynamic workflow ID resolution (fallback to `<dynamic>` pattern)
- Signal delivery guarantees visualization (runtime property)

## System Architecture Alignment

This epic builds on the established static analysis architecture (ADR-001) using Python AST (Abstract Syntax Tree) to detect workflow patterns. It follows the detector pattern established in Epic 3 (DecisionDetector), Epic 4 (SignalDetector), and Epic 6 (ChildWorkflowDetector).

**Architecture Constraints:**
- **ADR-001 (Static Analysis):** External signal detection via AST traversal, no workflow execution
- **ADR-006 (mypy strict):** Complete type hints for ExternalSignalCall, ExternalSignalDetector
- **ADR-010 (>=80% coverage):** Unit tests for detector, integration tests for examples
- **Visitor Pattern:** ExternalSignalDetector extends ast.NodeVisitor for AST traversal
- **Immutable Data:** ExternalSignalCall as frozen dataclass (consistency with WorkflowMetadata)
- **Error Handling:** WorkflowParseError for invalid .signal() calls with actionable suggestions

**Component Alignment:**
- **detector.py:** Add ExternalSignalDetector after ChildWorkflowDetector (~line 756)
- **graph_models.py:** Add ExternalSignalCall dataclass, update NodeType enum
- **analyzer.py:** Instantiate and run ExternalSignalDetector in analysis pipeline
- **generator.py:** Treat external signals as sequential nodes (no path branching)
- **renderer.py:** Handle EXTERNAL_SIGNAL node type with trapezoid syntax and dashed edges
- **context.py:** Add configuration options (show_external_signals, external_signal_label_style)

**Mermaid Rendering Strategy:**
- Trapezoid shape differentiates external signals from activities (rectangles), decisions (diamonds), and internal signals (hexagons)
- Dashed edges visually indicate asynchronous communication (vs solid edges for synchronous calls)
- Orange/amber color styling provides additional visual distinction
- Follows Mermaid flowchart syntax standards for compatibility with renderers

## Detailed Design

### Services and Modules

| Module | Responsibility | Inputs | Outputs | Owner |
|--------|----------------|--------|---------|-------|
| **detector.py (ExternalSignalDetector)** | Detect `get_external_workflow_handle()` and `.signal()` calls in AST | ast.Module (workflow source) | list[ExternalSignalCall] | Story 7.1 |
| **graph_models.py (ExternalSignalCall)** | Store external signal metadata | signal_name, target_pattern, source_line, node_id, source_workflow | Frozen dataclass instance | Story 7.2 |
| **analyzer.py (WorkflowAnalyzer)** | Integrate external signal detection into analysis pipeline | workflow source file | WorkflowMetadata with external_signals | Story 7.3 |
| **generator.py (PathPermutationGenerator)** | Add external signal nodes to execution paths | WorkflowMetadata with external_signals | list[GraphPath] with signal nodes | Story 7.3 |
| **renderer.py (MermaidRenderer)** | Render external signals as trapezoid nodes with dashed edges | GraphPath with EXTERNAL_SIGNAL nodes | Mermaid flowchart syntax | Story 7.4 |
| **context.py (GraphBuildingContext)** | Configure external signal visualization options | User configuration | Immutable context dataclass | Story 7.4 |
| **examples/peer_signal_workflow/** | Demonstrate Order → Shipping external signaling | Order and Shipping workflow files | Mermaid diagram with trapezoid signal node | Story 7.5 |

### Data Models and Contracts

**ExternalSignalCall Dataclass (graph_models.py):**
```python
@dataclass(frozen=True)
class ExternalSignalCall:
    """Represents an external signal send to another workflow.

    Detected when workflow uses get_external_workflow_handle() followed by .signal().
    Supports peer-to-peer workflow communication patterns.
    """
    signal_name: str
    # Signal being sent (e.g., "ship_order")

    target_workflow_pattern: str
    # Target workflow ID pattern:
    #   - String literal: "shipping-123" (exact target)
    #   - Format string: "shipping-{*}" (pattern with wildcard)
    #   - Dynamic: "<dynamic>" (variable reference or function call)

    source_line: int
    # Line number where signal send occurs (for error reporting)

    node_id: str
    # Unique identifier: "ext_sig_{signal_name}_{line_number}"

    source_workflow: str
    # Name of workflow sending the signal (for context)
```

**NodeType Enum Extension (graph_models.py):**
```python
class NodeType(Enum):
    """Graph node types."""
    START = "start"
    END = "end"
    ACTIVITY = "activity"
    DECISION = "decision"
    SIGNAL = "signal"
    CHILD_WORKFLOW = "child_workflow"
    EXTERNAL_SIGNAL = "external_signal"  # NEW: Epic 7
```

**WorkflowMetadata Extension (graph_models.py):**
```python
@dataclass(frozen=True)
class WorkflowMetadata:
    # ... existing fields ...
    external_signals: tuple[ExternalSignalCall, ...] = ()  # NEW: Epic 7
```

**GraphBuildingContext Extension (context.py):**
```python
@dataclass(frozen=True)
class GraphBuildingContext:
    # ... existing fields ...
    show_external_signals: bool = True
    # Toggle peer signals on/off in visualization

    external_signal_label_style: Literal["name-only", "target-pattern"] = "name-only"
    # "name-only": [/Signal 'ship_order'\\]
    # "target-pattern": [/Signal 'ship_order' to shipping-{*}\\]

    external_signal_edge_style: Literal["dashed", "dotted"] = "dashed"
    # Edge style for signal edges (dashed recommended for clarity)
```

**Entity Relationships:**
```
WorkflowMetadata (1) ──< (n) ExternalSignalCall
ExternalSignalCall (1) ──< (1) GraphNode (EXTERNAL_SIGNAL type)
GraphNode (EXTERNAL_SIGNAL) ──< (n) GraphEdge (dashed style)
```

### APIs and Interfaces

**ExternalSignalDetector API (detector.py):**

```python
class ExternalSignalDetector(ast.NodeVisitor):
    """Detects external signal sends in workflow AST.

    Identifies two patterns:
    1. Two-step: handle = workflow.get_external_workflow_handle("target")
                 await handle.signal("sig", data)
    2. Inline:   await workflow.get_external_workflow_handle("target").signal("sig", data)
    """

    def __init__(self) -> None:
        """Initialize detector with empty state."""
        self._external_signals: list[ExternalSignalCall] = []
        self._handle_assignments: dict[str, tuple[str, int]] = {}
        # {var_name: (target_pattern, line_number)}
        self._source_workflow: str = ""

    def set_source_workflow(self, workflow_name: str) -> None:
        """Set the source workflow name for context."""
        self._source_workflow = workflow_name

    def visit_Assign(self, node: ast.Assign) -> None:
        """Detect handle = workflow.get_external_workflow_handle(...)"""
        # Implementation: Track handle assignments
        # Store {var_name: (target_pattern, line_number)}
        self.generic_visit(node)

    def visit_Await(self, node: ast.Await) -> None:
        """Detect await handle.signal(...) or inline pattern."""
        # Implementation: Match signal calls to handles
        # Create ExternalSignalCall instances
        self.generic_visit(node)

    @property
    def external_signals(self) -> list[ExternalSignalCall]:
        """Get detected external signals."""
        return self._external_signals.copy()

    def _extract_target_pattern(self, arg_node: ast.expr) -> str:
        """Extract target workflow pattern from argument node.

        Returns:
            - String literal: exact value (e.g., "shipping-123")
            - JoinedStr (f-string): pattern with wildcard (e.g., "ship-{*}")
            - Variable/Call: "<dynamic>"
        """
        # Implementation details in Story 7.1
```

**WorkflowAnalyzer Integration (analyzer.py):**

```python
class WorkflowAnalyzer:
    def analyze(self, tree: ast.Module, file_path: Path) -> WorkflowMetadata:
        """Analyze workflow AST to extract metadata."""
        # ... existing analysis ...

        # NEW: Epic 7 - Detect external signals
        external_signal_detector = ExternalSignalDetector()
        external_signal_detector.set_source_workflow(workflow_class_name)
        external_signal_detector.visit(tree)
        external_signals = tuple(external_signal_detector.external_signals)

        return WorkflowMetadata(
            # ... existing fields ...
            external_signals=external_signals  # NEW
        )
```

**MermaidRenderer Extension (renderer.py):**

```python
class MermaidRenderer:
    def _render_node(self, node: GraphNode, context: GraphBuildingContext) -> str:
        """Render node in Mermaid syntax."""
        # ... existing node types ...

        if node.node_type == NodeType.EXTERNAL_SIGNAL:
            signal = cast(ExternalSignalCall, node.metadata)
            if context.external_signal_label_style == "target-pattern":
                label = f"Signal '{signal.signal_name}' to {signal.target_workflow_pattern}"
            else:
                label = f"Signal '{signal.signal_name}'"
            return f"{node.node_id}[/{label}\\]"  # Trapezoid shape

    def _render_edge(self, edge: GraphEdge, context: GraphBuildingContext) -> str:
        """Render edge in Mermaid syntax."""
        # ... existing edge logic ...

        # Dashed edge for external signals
        if edge.from_node.node_type == NodeType.EXTERNAL_SIGNAL:
            if context.external_signal_edge_style == "dotted":
                return f"{edge.from_node.node_id} -.signal..> {edge.to_node.node_id}"
            else:  # dashed (default)
                return f"{edge.from_node.node_id} -.signal.-> {edge.to_node.node_id}"

    def _apply_styling(self, nodes: list[GraphNode]) -> list[str]:
        """Apply color styling to nodes."""
        styles = []
        for node in nodes:
            if node.node_type == NodeType.EXTERNAL_SIGNAL:
                # Orange/amber for external signals
                styles.append(f"style {node.node_id} fill:#fff4e6,stroke:#ffa500")
        return styles
```

**Error Handling:**

```python
# detector.py
if not signal_args:
    raise WorkflowParseError(
        f"signal() requires at least 1 argument (signal name) at line {node.lineno}\n"
        f"Suggestion: Use handle.signal('signal_name', payload)"
    )
```

### Workflows and Sequencing

**External Signal Detection Workflow:**

1. **AST Parsing** (WorkflowAnalyzer)
   - Parse workflow source file into AST
   - Instantiate ExternalSignalDetector

2. **Handle Assignment Detection** (visit_Assign)
   - Identify: `handle = workflow.get_external_workflow_handle(target)`
   - Extract target pattern (string literal, f-string, variable)
   - Store: `{var_name: (pattern, line_number)}`

3. **Signal Call Detection** (visit_Await)
   - Identify: `await handle.signal(signal_name, payload)`
   - Match handle variable to stored assignment
   - Extract signal name from first argument

4. **Pattern Resolution**
   - String literal → exact pattern
   - JoinedStr (f-string) → wildcard pattern (`"ship-{*}"`)
   - Variable/Call → `<dynamic>` fallback

5. **Metadata Creation**
   - Create ExternalSignalCall instance
   - Generate node_id: `ext_sig_{signal_name}_{line}`
   - Append to detector's signal list

6. **Pipeline Integration**
   - WorkflowAnalyzer includes external_signals in WorkflowMetadata
   - PathPermutationGenerator adds signal nodes to paths (sequential)
   - MermaidRenderer outputs trapezoid nodes with dashed edges

**Sequence Diagram (Text):**

```
User → analyze_workflow(workflow_file)
analyze_workflow → WorkflowAnalyzer.analyze()
WorkflowAnalyzer → ast.parse(source) → AST
WorkflowAnalyzer → ExternalSignalDetector.visit(AST)
ExternalSignalDetector → visit_Assign() → store handle assignments
ExternalSignalDetector → visit_Await() → detect signal calls
ExternalSignalDetector → return external_signals
WorkflowAnalyzer → return WorkflowMetadata (with external_signals)
analyze_workflow → PathPermutationGenerator.generate(metadata)
PathPermutationGenerator → add signal nodes to paths
analyze_workflow → MermaidRenderer.render(paths)
MermaidRenderer → render trapezoid nodes + dashed edges
analyze_workflow → return Mermaid diagram string
```

**Data Flow:**

```
workflow.py (source file)
  ↓ ast.parse()
AST (Abstract Syntax Tree)
  ↓ ExternalSignalDetector.visit()
list[ExternalSignalCall] (detected signals)
  ↓ WorkflowMetadata construction
WorkflowMetadata (includes external_signals)
  ↓ PathPermutationGenerator.generate()
list[GraphPath] (with EXTERNAL_SIGNAL nodes)
  ↓ MermaidRenderer.render()
Mermaid flowchart syntax (trapezoid + dashed edges)
```

## Non-Functional Requirements

### Performance

**NFR-PERF-1: Analysis Speed**
- Target: <1ms overhead for external signal detection (AST traversal is O(n) where n = nodes)
- Target: <1.5s total for graphs with 10 external signals (includes existing <1s baseline)
- Rationale: External signal detection adds minimal overhead to AST traversal (1-2 additional visitor methods)

**NFR-PERF-2: Memory Efficiency**
- ExternalSignalCall dataclass: ~200 bytes per instance (frozen, no overhead)
- 100 external signals: ~20KB additional memory (negligible impact)
- No path explosion: External signals are sequential nodes (no branching), no 2^n growth

**NFR-PERF-3: Rendering Performance**
- Trapezoid node rendering: O(1) per node (same as existing node types)
- Dashed edge rendering: O(1) per edge (string concatenation)
- Color styling: O(n) where n = external signal nodes (separate loop, non-blocking)

### Security

**NFR-SEC-1: Static Analysis Only**
- No external workflow execution or connection (consistent with ADR-001)
- No network calls to resolve target workflow IDs (purely pattern extraction)
- Path traversal prevented: Uses existing _validate_workflow_file() (pathlib.resolve())

**NFR-SEC-2: Input Validation**
- Validate signal() has at least 1 argument (signal name required)
- Validate get_external_workflow_handle() has exactly 1 argument (workflow_id)
- Raise WorkflowParseError with actionable messages for invalid patterns

**NFR-SEC-3: Safe Pattern Extraction**
- AST node inspection only (no eval(), exec(), compile())
- String literal extraction via ast.Constant.value (safe)
- Format string pattern conversion via AST structure analysis (no string interpolation)

### Reliability/Availability

**NFR-REL-1: Detection Accuracy**
- 100% accuracy for two-step pattern: handle = get_external_workflow_handle(); await handle.signal()
- 100% accuracy for inline pattern: await get_external_workflow_handle().signal()
- 100% accuracy for string literal targets (exact workflow IDs)
- Best-effort for format string targets (convert to wildcard patterns)
- Graceful fallback for dynamic targets (variable/function call → `<dynamic>`)

**NFR-REL-2: Error Handling**
- Clear error messages for missing signal name: "signal() requires at least 1 argument"
- Suggestion included: "Use: handle.signal('signal_name', payload)"
- No silent failures: All detection errors raise WorkflowParseError
- No crashes on malformed signal calls (try/except with informative messages)

**NFR-REL-3: Backward Compatibility**
- Existing workflows without external signals: No impact (empty external_signals tuple)
- Existing public API unchanged (GraphBuildingContext extended, not modified)
- Existing tests continue passing (no regressions in Epic 1-6 functionality)

### Observability

**NFR-OBS-1: Debug Logging**
- Log each detected external signal: `"Detected external signal '{name}' to '{pattern}' at line {line}"`
- Log handle assignments: `"Tracking handle '{var}' → target '{pattern}' at line {line}"`
- Log pattern resolution: `"Resolved target pattern: '{pattern}' (type: {literal|format|dynamic})"`
- Use logging.DEBUG level (not visible by default, opt-in for troubleshooting)

**NFR-OBS-2: Validation Warnings**
- Warn if external signal target is `<dynamic>`: "Target workflow ID is dynamic, cannot verify existence"
- Warn if signal name is variable (not string literal): "Signal name is dynamic, may not match actual runtime signal"
- Include in ValidationReport if context.include_validation_report = True

**NFR-OBS-3: Test Coverage Metrics**
- 100% coverage for ExternalSignalDetector class (all branches, edge cases)
- >=80% overall library coverage maintained (existing Epic 1-6 baseline)
- Coverage report includes detector.py lines in detail

## Dependencies and Integrations

### External Dependencies

**Core (Production):**
- `temporalio>=1.7.1` (existing dependency, no changes)
  - Used for: workflow decorators, type definitions
  - Version constraint: Same as existing (Epic 1-6)

**Development:**
- `pytest>=8.0.0` (existing, no changes)
- `pytest-asyncio>=0.23.0` (existing, no changes)
- `mypy>=1.8.0` (existing, no changes)
- `ruff>=0.2.0` (existing, no changes)
- `pytest-cov>=4.1.0` (existing, no changes)

**No New Dependencies Required.**

### Internal Dependencies

**Module Dependencies:**
- `detector.py (ExternalSignalDetector)` depends on:
  - `ast` (stdlib, built-in)
  - `_internal/graph_models.py` (ExternalSignalCall dataclass)
  - `exceptions.py` (WorkflowParseError)

- `analyzer.py (WorkflowAnalyzer)` depends on:
  - `detector.py` (ExternalSignalDetector)
  - `_internal/graph_models.py` (WorkflowMetadata, ExternalSignalCall)

- `generator.py (PathPermutationGenerator)` depends on:
  - `_internal/graph_models.py` (ExternalSignalCall, NodeType)

- `renderer.py (MermaidRenderer)` depends on:
  - `context.py` (GraphBuildingContext with new fields)
  - `_internal/graph_models.py` (NodeType.EXTERNAL_SIGNAL)

**Story Dependencies (Sequential):**
- Story 7.1 (ExternalSignalDetector) → Story 7.2 (ExternalSignalCall data model)
- Story 7.2 → Story 7.3 (Pipeline integration)
- Story 7.3 → Story 7.4 (Mermaid rendering)
- Story 7.4 → Story 7.5 (Example & documentation)

### Integration Points

**AST Analysis Integration:**
- ExternalSignalDetector follows visitor pattern (established in Epic 3, 4, 6)
- Integrates into WorkflowAnalyzer._run_detectors() (~line 150 in analyzer.py)
- No changes to AST parsing strategy (uses existing ast.parse() flow)

**Path Generation Integration:**
- External signals treated as sequential nodes (like activities in Epic 2)
- No branching logic (signals are one-way sends, not decisions)
- Generator sorts activities, decisions, signals, child workflows, external signals by source line number (consistent with Epic 6 ADR)

**Rendering Integration:**
- MermaidRenderer._render_node() adds case for NodeType.EXTERNAL_SIGNAL
- MermaidRenderer._render_edge() checks for EXTERNAL_SIGNAL nodes to apply dashed style
- MermaidRenderer._apply_styling() adds color for EXTERNAL_SIGNAL nodes
- No changes to existing node types (backward compatible)

**Configuration Integration:**
- GraphBuildingContext extended with 3 new fields (frozen dataclass, immutable)
- Existing context fields unchanged (backward compatible)
- New fields have sensible defaults (show_external_signals=True, label_style="name-only")

## Acceptance Criteria (Authoritative)

**AC1: External Signal Detection (FR74-FR77)**
- GIVEN a workflow with `workflow.get_external_workflow_handle(target)` followed by `.signal(name, payload)`
- WHEN ExternalSignalDetector analyzes the AST
- THEN detector identifies the signal call
- AND extracts signal name from first argument
- AND extracts target workflow pattern (string literal, f-string, or `<dynamic>`)
- AND creates ExternalSignalCall with correct metadata (signal_name, target_pattern, source_line, node_id, source_workflow)

**AC2: Two-Step Pattern Support**
- GIVEN code: `handle = workflow.get_external_workflow_handle("shipping-123"); await handle.signal("ship", data)`
- WHEN detector analyzes AST
- THEN detector matches signal call to handle assignment
- AND stores target_pattern = "shipping-123" (exact)
- AND stores signal_name = "ship"

**AC3: Inline Pattern Support**
- GIVEN code: `await workflow.get_external_workflow_handle("target").signal("notify", payload)`
- WHEN detector analyzes AST
- THEN detector detects inline pattern (no intermediate handle variable)
- AND extracts target and signal name correctly

**AC4: Format String Target Pattern**
- GIVEN code: `workflow.get_external_workflow_handle(f"shipping-{order_id}")`
- WHEN detector extracts target pattern
- THEN pattern = "shipping-{*}" (wildcard substitution)

**AC5: Dynamic Target Fallback**
- GIVEN code: `workflow.get_external_workflow_handle(compute_target())`
- WHEN detector extracts target pattern
- THEN pattern = "<dynamic>" (cannot resolve at static analysis time)

**AC6: ExternalSignalCall Data Model**
- GIVEN ExternalSignalCall dataclass
- THEN dataclass is frozen (immutable)
- AND has fields: signal_name, target_workflow_pattern, source_line, node_id, source_workflow
- AND has complete type hints (mypy strict compliant)
- AND node_id format is "ext_sig_{signal_name}_{line_number}"

**AC7: NodeType Extension**
- GIVEN NodeType enum
- THEN enum includes EXTERNAL_SIGNAL = "external_signal" value
- AND value is distinct from existing types (START, END, ACTIVITY, DECISION, SIGNAL, CHILD_WORKFLOW)

**AC8: WorkflowMetadata Extension**
- GIVEN WorkflowMetadata dataclass
- THEN includes external_signals: tuple[ExternalSignalCall, ...] field
- AND default value is empty tuple ()
- AND field is immutable (frozen dataclass)

**AC9: Pipeline Integration**
- GIVEN WorkflowAnalyzer processes a workflow with external signal
- WHEN analysis completes
- THEN WorkflowMetadata.external_signals contains detected signals
- AND signals are included in generated execution paths
- AND signals appear in execution order (by source line number)

**AC10: Trapezoid Node Rendering (FR78)**
- GIVEN a GraphPath with EXTERNAL_SIGNAL node
- WHEN MermaidRenderer renders the path
- THEN node renders as trapezoid: `node_id[/Signal Name\\]`
- AND syntax is valid Mermaid flowchart

**AC11: Dashed Edge Rendering (FR79)**
- GIVEN an edge from/to EXTERNAL_SIGNAL node
- WHEN MermaidRenderer renders the edge
- THEN edge renders with dashed style: `source -.signal.-> target`
- AND style is configurable (dashed vs dotted)

**AC12: Target Pattern Label (FR80)**
- GIVEN context.external_signal_label_style = "target-pattern"
- WHEN rendering external signal node
- THEN label includes target: `[/Signal 'ship_order' to shipping-{*}\\]`

**AC13: Name-Only Label**
- GIVEN context.external_signal_label_style = "name-only" (default)
- WHEN rendering external signal node
- THEN label shows name only: `[/Signal 'ship_order'\\]`

**AC14: Color Styling**
- GIVEN external signal nodes in graph
- WHEN MermaidRenderer applies styling
- THEN external signal nodes have orange/amber color: `style node_id fill:#fff4e6,stroke:#ffa500`

**AC15: Configuration Options**
- GIVEN GraphBuildingContext
- THEN includes show_external_signals: bool = True
- AND includes external_signal_label_style: Literal["name-only", "target-pattern"] = "name-only"
- AND includes external_signal_edge_style: Literal["dashed", "dotted"] = "dashed"
- AND all fields are type-safe (mypy strict compliant)

**AC16: Hide External Signals**
- GIVEN context.show_external_signals = False
- WHEN rendering paths
- THEN external signal nodes are excluded from output
- AND edges skip over hidden signal nodes

**AC17: Order → Shipping Example (FR81)**
- GIVEN examples/peer_signal_workflow/ directory
- THEN includes order_workflow.py with Order workflow sending external signal
- AND includes shipping_workflow.py with Shipping workflow receiving signal
- AND includes run.py demonstrating analysis of both workflows
- AND includes expected_output.md with golden Mermaid diagram
- AND diagram shows trapezoid signal node with dashed edge

**AC18: Integration Test**
- GIVEN tests/integration/test_peer_signals.py
- WHEN test analyzes Order workflow
- THEN output contains trapezoid signal node syntax `[/...\\]`
- AND output contains dashed edge syntax `-.signal.->`
- AND output contains target pattern (if deterministic)
- AND output matches expected_output.md structure

**AC19: Error Handling**
- GIVEN workflow with `.signal()` call with no arguments
- WHEN detector analyzes AST
- THEN raises WorkflowParseError
- AND message includes "signal() requires at least 1 argument (signal name)"
- AND includes suggestion: "Use: handle.signal('signal_name', payload)"

**AC20: No Regression**
- GIVEN existing Epic 1-6 tests
- WHEN Epic 7 implementation is complete
- THEN all existing tests continue passing
- AND test coverage remains >=80%
- AND mypy strict mode passes
- AND ruff linting passes

## Traceability Mapping

| AC | FR | Spec Section | Component | Test |
|----|----|--------------|-----------| -----|
| AC1 | FR74-FR77 | APIs and Interfaces → ExternalSignalDetector | detector.py (ExternalSignalDetector) | test_detector.py::test_detect_external_signal |
| AC2 | FR74-FR75 | Workflows and Sequencing → Handle Assignment Detection | detector.py (visit_Assign, visit_Await) | test_detector.py::test_detect_two_step_pattern |
| AC3 | FR74-FR75 | Workflows and Sequencing → Signal Call Detection | detector.py (visit_Await inline pattern) | test_detector.py::test_detect_inline_pattern |
| AC4 | FR77 | APIs and Interfaces → _extract_target_pattern | detector.py (_extract_target_pattern) | test_detector.py::test_format_string_target |
| AC5 | FR77 | APIs and Interfaces → _extract_target_pattern | detector.py (dynamic fallback) | test_detector.py::test_dynamic_target_fallback |
| AC6 | FR74-FR77 | Data Models → ExternalSignalCall | graph_models.py (ExternalSignalCall) | test_graph_models.py::test_external_signal_call |
| AC7 | FR78 | Data Models → NodeType Extension | graph_models.py (NodeType enum) | test_graph_models.py::test_node_type_external_signal |
| AC8 | FR74-FR77 | Data Models → WorkflowMetadata Extension | graph_models.py (WorkflowMetadata) | test_analyzer.py::test_metadata_with_external_signals |
| AC9 | FR74-FR77 | Workflows and Sequencing → Pipeline Integration | analyzer.py, generator.py | test_analyzer.py::test_external_signal_integration |
| AC10 | FR78 | APIs and Interfaces → MermaidRenderer._render_node | renderer.py (_render_node) | test_renderer.py::test_trapezoid_node_syntax |
| AC11 | FR79 | APIs and Interfaces → MermaidRenderer._render_edge | renderer.py (_render_edge) | test_renderer.py::test_dashed_edge_syntax |
| AC12 | FR80 | APIs and Interfaces → MermaidRenderer (label style) | renderer.py (target-pattern mode) | test_renderer.py::test_target_pattern_label |
| AC13 | FR80 | APIs and Interfaces → MermaidRenderer (label style) | renderer.py (name-only mode) | test_renderer.py::test_name_only_label |
| AC14 | FR78 | APIs and Interfaces → MermaidRenderer._apply_styling | renderer.py (_apply_styling) | test_renderer.py::test_signal_color_styling |
| AC15 | FR78-FR80 | Data Models → GraphBuildingContext | context.py (GraphBuildingContext) | test_context.py::test_external_signal_options |
| AC16 | FR78-FR80 | APIs and Interfaces → MermaidRenderer (toggle) | renderer.py (show_external_signals=False) | test_renderer.py::test_hide_external_signals |
| AC17 | FR81 | Examples & Documentation | examples/peer_signal_workflow/ | integration/test_peer_signals.py::test_order_workflow |
| AC18 | FR81 | Examples & Documentation | integration test | integration/test_peer_signals.py::test_expected_output |
| AC19 | FR74-FR75 | Non-Functional Requirements → Error Handling | detector.py (validation) | test_detector.py::test_signal_call_no_args_error |
| AC20 | All | Non-Functional Requirements → Reliability | All components | pytest (full suite), mypy, ruff |

## Risks, Assumptions, Open Questions

### Risks

**RISK-1: Dynamic Workflow ID Resolution**
- **Risk:** Cannot resolve dynamic workflow IDs at static analysis time (e.g., `get_external_workflow_handle(compute_id())`)
- **Impact:** Target pattern shows as `<dynamic>`, less useful for visualization
- **Mitigation:** Document limitation in README and ADR-012. Encourage string literals or f-strings for deterministic patterns.
- **Likelihood:** High (common pattern in production workflows)
- **Severity:** Low (library still visualizes signal flow, just without exact target)

**RISK-2: Signal Name as Variable**
- **Risk:** Signal name passed as variable instead of string literal (e.g., `.signal(sig_name, data)`)
- **Impact:** Cannot extract signal name at static analysis time
- **Mitigation:** Detector checks for ast.Constant (string literal). If variable, log warning and use variable name or `<unknown>`.
- **Likelihood:** Medium (less common, most signals use literal names)
- **Severity:** Low (visualization shows signal node, just with generic name)

**RISK-3: Chained Handle Creation**
- **Risk:** Complex chaining: `workflow.get_external_workflow_handle(a).get_external_workflow_handle(b).signal("sig")`
- **Impact:** Nested handle creation not supported in detector
- **Mitigation:** Document as unsupported pattern. Raise WorkflowParseError with suggestion to use intermediate variables.
- **Likelihood:** Very Low (not a Temporal SDK pattern)
- **Severity:** Low (easily refactored)

**RISK-4: Path Explosion with Many Signals**
- **Risk:** Workflows with many external signals may create dense graphs
- **Impact:** Diagram readability degrades
- **Mitigation:** External signals don't create path branching (no 2^n explosion). Dense graphs are a visualization issue, not a performance issue. Users can toggle `show_external_signals=False` to simplify.
- **Likelihood:** Low (most workflows have 1-3 external signals)
- **Severity:** Low (configurable visibility)

### Assumptions

**ASSUMP-1: Temporal SDK API Stability**
- Assumes `workflow.get_external_workflow_handle()` and `.signal()` API remains stable in Temporal SDK >=1.7.1
- Based on: Temporal's commitment to backward compatibility
- Validation: Monitor Temporal SDK release notes for breaking changes

**ASSUMP-2: Single Signal per Handle**
- Assumes most workflows send one signal per handle (not multiple signals to same handle in sequence)
- Based on: Common Temporal patterns observed in examples
- Impact if invalid: Detector supports multiple signals, but visualization may become complex

**ASSUMP-3: ASCII Signal Names**
- Assumes signal names are ASCII strings (not unicode, not binary)
- Based on: Temporal signal name conventions
- Impact if invalid: Mermaid rendering may fail for non-ASCII characters (Mermaid limitation)

**ASSUMP-4: No Circular Signaling**
- Assumes workflows don't have circular signal dependencies (A signals B, B signals A)
- Based on: Circular signaling is a design anti-pattern (deadlock risk)
- Impact if invalid: Library visualizes both directions independently (no cycle detection needed)

### Open Questions

**Q1: Should we support conditional signal sends?**
- Question: If signal send is inside `if` block, how to visualize?
- Current approach: Treat as sequential node (always shown in path)
- Alternative: Branch paths at conditional signal (requires decision node integration)
- Decision: Defer to post-MVP. For MVP, show signal in all paths (simpler). Users can use to_decision() before signal if branching needed.

**Q2: Should we validate target workflow existence?**
- Question: For deterministic targets (string literals), should we check if target workflow file exists?
- Current approach: No validation (static analysis only, no file system lookups beyond current workflow)
- Alternative: Search for target workflow in same directory or search paths
- Decision: No validation for MVP (out of scope). Cross-workflow validation is a separate feature (related to Epic 6 expansion).

**Q3: Should we support signal receive visualization?**
- Question: Should we detect `@workflow.signal` handlers in target workflow and link sender → receiver?
- Current approach: Only visualize send-side (outgoing signals from analyzed workflow)
- Alternative: Bidirectional visualization (requires analyzing both workflows together)
- Decision: Out of scope for MVP. Each workflow analyzed independently. Future: Multi-workflow view could show bidirectional signals (Epic 8+).

**Q4: Should we support external activity signals?**
- Question: Activities can send signals to workflows via activity context. Should we detect these?
- Current approach: Only detect workflow-level `workflow.get_external_workflow_handle()` calls
- Alternative: Analyze activity code for signal sends (requires activity file analysis)
- Decision: Out of scope. Library analyzes workflow code only (ADR-001). Activity internals are black boxes.

## Test Strategy Summary

### Unit Tests (test_detector.py, test_graph_models.py, test_renderer.py, test_context.py)

**ExternalSignalDetector Unit Tests (~100 lines):**
- `test_detect_single_external_signal()` - basic two-step pattern
- `test_detect_inline_external_signal()` - chained call pattern
- `test_detect_format_string_target()` - f-string workflow ID
- `test_detect_dynamic_target()` - variable reference fallback
- `test_detect_multiple_external_signals()` - multiple signals in sequence
- `test_detect_conditional_external_signal()` - signal inside if block
- `test_invalid_signal_call_no_args()` - error handling for missing signal name
- `test_extract_target_pattern_string_literal()` - exact pattern
- `test_extract_target_pattern_format_string()` - wildcard pattern
- `test_extract_target_pattern_dynamic()` - `<dynamic>` fallback
- **Coverage Target:** 100% for ExternalSignalDetector class

**Data Model Unit Tests (~30 lines):**
- `test_external_signal_call_creation()` - create instance with all fields
- `test_external_signal_call_immutability()` - verify frozen=True
- `test_node_type_external_signal()` - verify enum value exists
- `test_workflow_metadata_with_external_signals()` - metadata extension

**Renderer Unit Tests (~100 lines):**
- `test_render_trapezoid_node()` - trapezoid shape syntax `[/...\\]`
- `test_render_dashed_edge()` - dashed edge syntax `-.signal.->`
- `test_external_signal_label_name_only()` - default label format
- `test_external_signal_label_with_target()` - target-pattern label
- `test_external_signal_color_styling()` - orange/amber color
- `test_hide_external_signals_option()` - toggle visibility
- `test_dotted_edge_style()` - alternative edge style

**Context Unit Tests (~20 lines):**
- `test_context_external_signal_defaults()` - verify default values
- `test_context_external_signal_custom()` - verify custom values
- `test_context_immutability()` - verify frozen=True

### Integration Tests (tests/integration/test_peer_signals.py)

**End-to-End Integration Test (~150 lines):**
- `test_analyze_order_workflow_with_external_signal()`:
  - GIVEN Order workflow sending external signal to Shipping workflow
  - WHEN analyze_workflow("order_workflow.py") runs
  - THEN output contains trapezoid signal node
  - AND output contains dashed edge
  - AND output contains target pattern `shipping-{*}`
  - AND output is valid Mermaid syntax

- `test_peer_signal_example_matches_expected_output()`:
  - GIVEN expected_output.md golden file
  - WHEN analyze_workflow("order_workflow.py") runs
  - THEN output structure matches expected (node count, edge count, signal presence)

- `test_shipping_workflow_signal_handler()`:
  - GIVEN Shipping workflow with @workflow.signal handler
  - WHEN analyze_workflow("shipping_workflow.py") runs
  - THEN analysis succeeds (signal handler is internal, not external signal send)
  - AND output does NOT contain external signal node (only wait_condition)

### Regression Tests

**Epic 1-6 Regression (~547 existing tests):**
- Run full test suite: `pytest -v`
- Verify all existing tests pass (no regressions)
- Verify coverage remains >=80% (currently 91%)
- Verify mypy strict mode passes: `mypy src/`
- Verify ruff linting passes: `ruff check src/`

### Performance Tests

**Performance Benchmark (manual verification):**
- Analyze workflow with 10 external signals
- Measure total analysis time: Expected <1.5s (baseline <1s + <0.5s overhead)
- Measure memory usage: Expected <100MB (existing baseline)
- Verify no path explosion (external signals are sequential, not branching)

### Test Coverage Metrics

**Coverage Targets:**
- ExternalSignalDetector: 100% (all branches, edge cases)
- ExternalSignalCall, NodeType: 100% (simple dataclasses)
- WorkflowAnalyzer (external signal integration): >=95%
- PathPermutationGenerator (signal node handling): >=90%
- MermaidRenderer (trapezoid rendering): >=95%
- Overall library: >=80% (maintain existing baseline)

**Coverage Command:**
```bash
pytest --cov=src/temporalio_graphs --cov-report=term-missing --cov-fail-under=80
```

### Validation Checklist

**Pre-Merge Checklist:**
- [ ] All unit tests pass (pytest -v)
- [ ] Integration tests pass (test_peer_signals.py)
- [ ] No regressions in Epic 1-6 tests (547 tests passing)
- [ ] Test coverage >=80% (pytest-cov report)
- [ ] mypy strict mode passes (mypy src/)
- [ ] ruff linting passes (ruff check src/)
- [ ] Example workflow runs successfully (uv run python examples/peer_signal_workflow/run.py)
- [ ] Generated Mermaid validates in Mermaid Live Editor
- [ ] Documentation updated (README, CHANGELOG, architecture.md ADR-012)
- [ ] pyproject.toml version updated to 0.3.0

---

**Tech Spec Status:** Draft - Ready for Story Breakdown
**Epic 7 Version:** v0.3.0
**Story Count:** 5 stories (7.1 through 7.5)
**Estimated Effort:** ~25-30 hours total (5-6 hours per story)

---

_Generated using BMM Epic Tech Context Workflow v6.0_
_Date: 2025-11-20_
_For: temporalio-graphs-python-port - Luca_
