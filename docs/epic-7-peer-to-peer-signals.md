# temporalio-graphs-python-port - Epic 7 Breakdown
## Peer-to-Peer Workflow Signaling Visualization

**Author:** Luca
**Date:** 2025-11-20
**Epic Type:** MVP Extension (v0.3.0)
**Tech-Spec:** `docs/tech-spec-epic-7-peer-to-peer-signals.md`

---

## Epic Overview

**Epic 7: Peer-to-Peer Workflow Signaling Visualization**

**Goal:** Enable visualization of asynchronous signal communication between independent Temporal workflows (peer-to-peer pattern)

**Epic Value:** Python developers can visualize peer-to-peer workflow signaling where Workflow A sends external signals to Workflow B. This completes the workflow interaction pattern coverage:
- ✅ Epic 2: Activities (sequential operations)
- ✅ Epic 4: Internal Signals (wait_condition for own state)
- ✅ Epic 6: Parent-Child (execute_child_workflow orchestration)
- 🆕 **Epic 7: Peer-to-Peer Signals (external signal communication)**

Real-world use cases: Order workflow signals Shipping workflow, Payment workflow notifies Fulfillment workflow, Saga compensation patterns.

**Story Count:** 5 stories
**FRs Covered:** FR74-FR81 (8 new functional requirements for peer-to-peer signaling)

---

## Functional Requirements (FR74-FR81)

**Peer-to-Peer Signal Detection (FR74-FR77):**
- FR74: Library can detect `workflow.get_external_workflow_handle()` calls in workflow source
- FR75: Library can detect `.signal()` method calls on external workflow handles
- FR76: Library can extract signal names from `.signal(signal_name, payload)` arguments
- FR77: Library can extract target workflow patterns from handle creation (string literals, format strings, or dynamic)

**Peer-to-Peer Signal Visualization (FR78-FR80):**
- FR78: External signal nodes render in Mermaid as trapezoid shapes `[/SignalName\\]`
- FR79: External signal edges render as dashed lines `-.signal.->` to show asynchronous communication
- FR80: External signal nodes display target workflow pattern when deterministic (e.g., "Signal to shipping-{*}")

**Examples & Documentation (FR81):**
- FR81: Library includes peer-to-peer workflow example demonstrating Order → Shipping signal communication

**Total: 8 New Functional Requirements** (extending from FR73 in Epic 6)

---

## Epic Structure

### Epic 7: Peer-to-Peer Workflow Signaling (5 Stories)

Based on Tech-Spec, breaking down into incremental deliverables:

**Story 7.1: Implement ExternalSignalDetector (AST Detection)**
**Story 7.2: Create ExternalSignalCall Data Model**
**Story 7.3: Integrate External Signal Detection into Analysis Pipeline**
**Story 7.4: Implement Mermaid Rendering for External Signals**
**Story 7.5: Add Peer Signal Workflow Example & Documentation**

---

## Story 7.1: Implement ExternalSignalDetector (AST Detection)

**User Story:**
As a library developer,
I want to detect `get_external_workflow_handle()` and `.signal()` calls in workflow code,
So that I can identify peer-to-peer signal communication for visualization.

**Acceptance Criteria:**

**Given** a workflow with external signal sends exists
**When** ExternalSignalDetector analyzes the AST
**Then** ExternalSignalDetector class exists in `src/temporalio_graphs/detector.py` (after line 756, after ChildWorkflowDetector)
**And** detector extends `ast.NodeVisitor` following established pattern (FR74)
**And** detector implements `visit_Assign()` to track `get_external_workflow_handle()` calls
**And** detector implements `visit_Await()` to detect `.signal()` calls on handles (FR75)
**And** detector stores handle assignments: `{var_name: (target_pattern, line_number)}`
**And** detector matches signal calls to handles via variable name tracking
**And** detector handles patterns:
  - Two-step: `handle = workflow.get_external_workflow_handle("target"); await handle.signal("sig", data)`
  - Inline: `await workflow.get_external_workflow_handle("target").signal("sig", data)`
  - Format string: `workflow.get_external_workflow_handle(f"ship-{order_id}")`
  - Dynamic ID: `workflow.get_external_workflow_handle(compute_id())` (fallback to `<dynamic>`)
**And** detector extracts signal name from first argument of `.signal()` call (FR76)
**And** detector extracts target workflow pattern:
  - String literal → exact pattern (e.g., "shipping-123")
  - Format string (JoinedStr AST node) → pattern with wildcard (e.g., "ship-{*}")
  - Variable reference or function call → `<dynamic>` (FR77)
**And** detector generates deterministic signal node IDs: `ext_sig_{signal_name}_{line_number}`
**And** detector records source workflow name for context
**And** detector has property `external_signals` returning `list[ExternalSignalCall]`
**And** detector raises `WorkflowParseError` for invalid patterns:
  - `.signal()` with no arguments → "signal() requires at least 1 argument (signal name)"
  - Suggestion: "Use: handle.signal('signal_name', payload)"
**And** detector logs debug messages for each detected signal: `"Detected external signal '{name}' to '{pattern}' at line {line}"`
**And** unit tests in `tests/test_detector.py` cover:
  - `test_detect_single_external_signal()` - basic two-step pattern
  - `test_detect_inline_external_signal()` - chained call pattern
  - `test_detect_format_string_target()` - f-string workflow ID
  - `test_detect_dynamic_target()` - variable reference fallback
  - `test_detect_multiple_external_signals()` - multiple signals in sequence
  - `test_detect_conditional_external_signal()` - signal inside if block
  - `test_invalid_signal_call_no_args()` - error handling
**And** unit test coverage for ExternalSignalDetector is 100%
**And** all tests pass with no regressions in existing Epic 1-6 tests

**Prerequisites:** Epic 6 complete (ChildWorkflowDetector pattern established)

**Technical Notes:**
- Place ExternalSignalDetector after ChildWorkflowDetector (~line 756 in detector.py)
- ~200 lines of code
- AST node patterns:
  ```python
  # visit_Assign: Detect handle = workflow.get_external_workflow_handle(...)
  Assign(
    targets=[Name(id='handle')],
    value=Call(
      func=Attribute(value=Name(id='workflow'), attr='get_external_workflow_handle'),
      args=[Constant(value="target") | JoinedStr(...) | Name(id='var')]
    )
  )

  # visit_Await: Detect await handle.signal("sig", data)
  Await(
    value=Call(
      func=Attribute(value=Name(id='handle'), attr='signal'),
      args=[Constant(value="sig"), ...]
    )
  )
  ```
- Format string pattern extraction: Convert JoinedStr to "prefix-{*}" pattern
- Covers FR74, FR75, FR76, FR77

---

## Story 7.2: Create ExternalSignalCall Data Model

**User Story:**
As a library developer,
I want a type-safe data structure for external signal metadata,
So that signal information flows correctly through the analysis pipeline.

**Acceptance Criteria:**

**Given** external signals are detected by ExternalSignalDetector
**When** signal metadata is stored
**Then** `ExternalSignalCall` dataclass exists in `src/temporalio_graphs/_internal/graph_models.py`
**And** dataclass is frozen (immutable) per Architecture pattern
**And** dataclass has fields:
  - `signal_name: str` - Signal being sent (e.g., "ship_order")
  - `target_workflow_pattern: str` - Target workflow ID pattern (e.g., "shipping-123", "ship-{*}", or "<dynamic>")
  - `source_line: int` - Line number where signal send occurs
  - `node_id: str` - Unique identifier (e.g., "ext_sig_ship_order_42")
  - `source_workflow: str` - Name of workflow sending signal
**And** dataclass has complete type hints (mypy strict compliant)
**And** dataclass has Google-style docstring with field descriptions
**And** `NodeType` enum in `graph_models.py` includes `EXTERNAL_SIGNAL = "external_signal"` value
**And** `WorkflowMetadata` dataclass in `graph_models.py` includes:
  - `external_signals: tuple[ExternalSignalCall, ...] = ()`
**And** unit tests in `tests/test_graph_models.py` cover:
  - `test_external_signal_call_creation()` - create instance with all fields
  - `test_external_signal_call_immutability()` - verify frozen=True
  - `test_node_type_external_signal()` - verify enum value exists
**And** all tests pass with mypy strict mode validation

**Prerequisites:** Story 7.1 complete (detector needs data structure)

**Technical Notes:**
- Add after `ChildWorkflowCall` dataclass (~line 120 in graph_models.py)
- ~30 lines of code
- Example instantiation:
  ```python
  signal = ExternalSignalCall(
      signal_name="ship_order",
      target_workflow_pattern="shipping-{*}",
      source_line=42,
      node_id="ext_sig_ship_order_42",
      source_workflow="OrderWorkflow"
  )
  ```
- Update `WorkflowMetadata` to include `external_signals` field (default empty tuple)
- Covers FR74-FR77 (data model foundation)

---

## Story 7.3: Integrate External Signal Detection into Analysis Pipeline

**User Story:**
As a library user,
I want external signals to be detected automatically when I analyze workflows,
So that peer-to-peer communication appears in my generated diagrams.

**Acceptance Criteria:**

**Given** ExternalSignalDetector and ExternalSignalCall exist
**When** WorkflowAnalyzer processes a workflow file
**Then** `WorkflowAnalyzer` in `src/temporalio_graphs/analyzer.py` instantiates `ExternalSignalDetector`
**And** analyzer imports `ExternalSignalDetector` from `detector` module
**And** analyzer runs `detector.visit(tree)` alongside DecisionDetector, SignalDetector, ChildWorkflowDetector
**And** analyzer sets detector's source_workflow name before visiting AST
**And** analyzer collects external signals: `external_signals = tuple(detector.external_signals)`
**And** analyzer includes external_signals in returned `WorkflowMetadata`
**And** PathPermutationGenerator in `src/temporalio_graphs/generator.py` handles external signals:
  - Treats external signals as sequential nodes (like activities)
  - No branching (signals are one-way sends, not decisions)
  - Adds external signal nodes to path in execution order
**And** integration test in `tests/integration/test_external_signal_detection.py` validates:
  - Workflow with external signal is analyzed via `analyze_workflow()`
  - `WorkflowMetadata.external_signals` list contains detected signals
  - Signal metadata matches expected values (name, target pattern, line number)
**And** existing Epic 1-6 integration tests still pass (no regressions)
**And** test coverage remains >=80%

**Prerequisites:** Story 7.2 complete (data model exists)

**Technical Notes:**
- Modify `WorkflowAnalyzer._run_detectors()` method (~line 150 in analyzer.py)
- Add external signal detector instantiation:
  ```python
  external_signal_detector = ExternalSignalDetector()
  external_signal_detector.set_source_workflow(workflow_metadata.workflow_class)
  external_signal_detector.visit(tree)
  external_signals = tuple(external_signal_detector.external_signals)
  ```
- Update `WorkflowMetadata` construction to include `external_signals=external_signals`
- ~10 lines of code in analyzer.py
- ~20 lines of code in generator.py for handling external signal nodes
- ~100 lines of integration test code
- Covers FR74-FR77 (end-to-end detection pipeline)

---

## Story 7.4: Implement Mermaid Rendering for External Signals

**User Story:**
As a library user,
I want external signals to appear as distinct trapezoid shapes in Mermaid diagrams,
So that I can visually distinguish peer-to-peer signals from other workflow patterns.

**Acceptance Criteria:**

**Given** paths contain external signal nodes
**When** Mermaid rendering runs
**Then** `MermaidRenderer` in `src/temporalio_graphs/renderer.py` handles `NodeType.EXTERNAL_SIGNAL`
**And** external signal nodes render with trapezoid syntax: `node_id[/Signal Name\\]` (FR78)
**And** signal label format:
  - If `target_workflow_pattern` is specific: `[/Signal 'ship_order' to shipping-123\\]`
  - If pattern with wildcard: `[/Signal 'ship_order' to shipping-{*}\\]`
  - If dynamic: `[/Signal 'ship_order' to external workflow\\]` (FR80)
**And** external signal edges render with dashed style: `source_node -.signal.-> signal_node` (FR79)
**And** external signal nodes have orange/amber color styling: `style sig1 fill:#fff4e6,stroke:#ffa500`
**And** node deduplication works correctly (same signal ID appears once)
**And** edge deduplication works correctly (same dashed edge appears once)
**And** generated Mermaid is valid and renders in Mermaid Live Editor
**And** `GraphBuildingContext` in `src/temporalio_graphs/context.py` includes:
  - `show_external_signals: bool = True` (toggle peer signals on/off)
  - `external_signal_label_style: Literal["name-only", "target-pattern"] = "name-only"`
  - `external_signal_edge_style: str = "dashed"` (or "dotted")
**And** context options are respected in rendering (can hide external signals if desired)
**And** unit tests in `tests/test_renderer.py` cover:
  - `test_render_external_signal_node()` - trapezoid shape syntax
  - `test_render_external_signal_edge()` - dashed edge syntax
  - `test_external_signal_label_with_target_pattern()` - label formatting
  - `test_external_signal_styling()` - color/style application
  - `test_hide_external_signals_option()` - toggle via context
**And** all tests pass with Mermaid syntax validation
**And** rendering completes in <1ms for graphs with 10 external signals (NFR-PERF-1)

**Prerequisites:** Story 7.3 complete (signals in metadata)

**Technical Notes:**
- Modify `MermaidRenderer._render_node()` method (~line 200 in renderer.py)
- Add case for `NodeType.EXTERNAL_SIGNAL`:
  ```python
  if node.node_type == NodeType.EXTERNAL_SIGNAL:
      signal = cast(ExternalSignalCall, node.metadata)
      if context.external_signal_label_style == "target-pattern":
          label = f"Signal '{signal.signal_name}' to {signal.target_workflow_pattern}"
      else:
          label = f"Signal '{signal.signal_name}'"
      return f"{node.node_id}[/{label}\\]"
  ```
- Modify `MermaidRenderer._render_edges()` for dashed style:
  ```python
  if edge.from_node.node_type == NodeType.EXTERNAL_SIGNAL or edge.to_node.node_type == NodeType.EXTERNAL_SIGNAL:
      return f"{edge.from_node.node_id} -.signal.-> {edge.to_node.node_id}"
  ```
- Add color styling after graph generation:
  ```python
  for node in nodes:
      if node.node_type == NodeType.EXTERNAL_SIGNAL:
          lines.append(f"style {node.node_id} fill:#fff4e6,stroke:#ffa500")
  ```
- ~30 lines of code in renderer.py
- ~5 lines of code in context.py
- ~100 lines of test code
- Covers FR78, FR79, FR80

---

## Story 7.5: Add Peer Signal Workflow Example & Documentation

**User Story:**
As a library user,
I want a complete example of peer-to-peer workflow signaling,
So that I can understand how to visualize workflows that signal each other.

**Acceptance Criteria:**

**Given** external signal support is fully implemented
**When** peer signal example is analyzed
**Then** `examples/peer_signal_workflow/` directory exists
**And** `order_workflow.py` exists with Order workflow that:
  - Processes order via `execute_activity(process_order, ...)`
  - Sends external signal: `await workflow.get_external_workflow_handle(f"shipping-{order_id}").signal("ship_order", order_id)`
  - Returns "order_complete"
**And** `shipping_workflow.py` exists with Shipping workflow that:
  - Waits for ship signal: `await workflow.wait_condition(lambda: self.should_ship, ...)`
  - Has signal handler: `@workflow.signal async def ship_order(self, order_id: str): self.should_ship = True`
  - Executes shipping activity: `await workflow.execute_activity(ship_package, ...)`
  - Returns "shipped"
**And** `run.py` exists demonstrating how to analyze both workflows:
  ```python
  from temporalio_graphs import analyze_workflow

  order_result = analyze_workflow("order_workflow.py")
  print("Order Workflow:")
  print(order_result)

  shipping_result = analyze_workflow("shipping_workflow.py")
  print("\nShipping Workflow:")
  print(shipping_result)
  ```
**And** `expected_output.md` exists with golden Mermaid diagram showing:
  - Order workflow with trapezoid signal node `[/Signal 'ship_order' to shipping-{*}\\]`
  - Dashed edge showing signal flow
  - Orange/amber color styling on signal node
**And** integration test `tests/integration/test_peer_signals.py` validates:
  - `analyze_workflow("examples/peer_signal_workflow/order_workflow.py")` succeeds
  - Output contains trapezoid signal node
  - Output contains dashed edge `-.signal.->`
  - Output contains target pattern `shipping-{*}`
  - Output matches expected_output.md structure (FR81)
**And** README.md updated with section "Peer-to-Peer Workflow Signaling":
  - Explains difference between internal signals, parent-child, and peer-to-peer
  - Shows Order → Shipping example code
  - Links to full example in `examples/peer_signal_workflow/`
  - Includes rendered Mermaid diagram
**And** `docs/architecture.md` updated with **ADR-012: Peer-to-Peer Signal Detection**:
  - Documents design decision for best-effort static analysis
  - Explains limitation of dynamic workflow IDs
  - Describes pattern matching strategy (string literals, format strings, fallback)
  - Lists visualization modes (reference only for MVP, inline/system deferred)
**And** CHANGELOG.md updated with Epic 7 changes (see tech-spec for format)
**And** pyproject.toml version updated to `0.3.0`
**And** all documentation examples are tested and working
**And** example runs successfully: `uv run python examples/peer_signal_workflow/run.py`

**Prerequisites:** Story 7.4 complete (rendering works)

**Technical Notes:**
- Example workflow structure (order_workflow.py):
  ```python
  @workflow.defn
  class OrderWorkflow:
      @workflow.run
      async def run(self, order_id: str) -> str:
          await workflow.execute_activity(process_order, args=[order_id], ...)

          # Peer-to-peer signal send
          shipping_handle = workflow.get_external_workflow_handle(f"shipping-{order_id}")
          await shipping_handle.signal("ship_order", order_id)

          return "order_complete"
  ```
- Example workflow structure (shipping_workflow.py):
  ```python
  @workflow.defn
  class ShippingWorkflow:
      def __init__(self):
          self.should_ship = False

      @workflow.run
      async def run(self, shipping_id: str) -> str:
          # Wait for external signal
          await workflow.wait_condition(lambda: self.should_ship, timedelta(hours=24))

          await workflow.execute_activity(ship_package, args=[shipping_id], ...)
          return "shipped"

      @workflow.signal
      async def ship_order(self, order_id: str) -> None:
          self.should_ship = True
  ```
- Expected Mermaid diagram shows Order workflow with external signal node
- ~200 lines of example code
- ~100 lines of integration test code
- ~150 lines of documentation updates
- Covers FR81 (example & documentation)

---

## FR Coverage Matrix - Epic 7

Complete mapping of all 8 new FRs to specific stories:

| FR | Description | Epic.Story | Notes |
|----|-------------|------------|-------|
| FR74 | Detect `workflow.get_external_workflow_handle()` calls | 7.1 | AST visit_Assign detection |
| FR75 | Detect `.signal()` method calls on external handles | 7.1 | AST visit_Await detection |
| FR76 | Extract signal names from `.signal(signal_name, ...)` | 7.1 | Argument extraction |
| FR77 | Extract target workflow patterns | 7.1 | String literal, f-string, or dynamic |
| FR78 | Render external signal nodes as trapezoids in Mermaid | 7.4 | `[/SignalName\\]` syntax |
| FR79 | Render external signal edges as dashed lines | 7.4 | `-.signal.->` syntax |
| FR80 | Display target workflow pattern in signal labels | 7.4 | Label formatting with pattern |
| FR81 | Peer-to-peer workflow example (Order → Shipping) | 7.5 | Integration example |

**All 8 new FRs mapped to implementation stories.**

---

## Summary

### Epic 7 Breakdown Complete

✅ **1 Epic Created:** Peer-to-Peer Workflow Signaling Visualization

✅ **5 Stories Total** - Each sized for single dev agent completion

✅ **8 New FRs Covered** (FR74-FR81) - Extending from Epic 6's FR73

✅ **Tech-Spec Integrated** - Static analysis approach for external signals, AST patterns, Mermaid rendering

✅ **User Value Validated** - Completes workflow interaction pattern coverage:
- Epic 2: Activities (sequential operations)
- Epic 4: Internal Signals (wait_condition)
- Epic 6: Parent-Child (execute_child_workflow)
- Epic 7: **Peer-to-Peer** (get_external_workflow_handle + signal)

### Context Incorporated

**From Tech-Spec:**
- Static analysis strategy with best-effort pattern matching (string literals, format strings, dynamic fallback)
- AST visitor pattern extending established detector architecture
- Mermaid trapezoid shape rendering with dashed edges for async communication
- ExternalSignalDetector follows DecisionDetector, SignalDetector, ChildWorkflowDetector patterns
- ~25-30 hour estimated effort across 5 stories

**From Existing Architecture:**
- ADR-001 (Static Analysis) drives AST-based approach
- ADR-006 (mypy strict) enforces type safety
- ADR-010 (>=80% coverage) applied to all stories
- ExternalSignalCall dataclass follows frozen=True immutability pattern
- Error handling follows WorkflowParseError with actionable suggestions

**Epic Stories Add Tactical Implementation Details:**
- Exact AST node structures (Assign, Await, Call, JoinedStr)
- Mermaid trapezoid syntax `/\ ... /\` and dashed edge `-.signal.->`
- Color styling (orange/amber for external signals)
- Test coverage requirements (100% for ExternalSignalDetector)
- Integration test specifications (Order → Shipping example)

### Development Sequence

**Epic 7 Story Execution (Sequential):**
1. Story 7.1: ExternalSignalDetector (AST detection foundation)
2. Story 7.2: ExternalSignalCall data model (type-safe structure)
3. Story 7.3: Pipeline integration (analyzer + generator)
4. Story 7.4: Mermaid rendering (trapezoid nodes + dashed edges)
5. Story 7.5: Example + documentation (Order → Shipping)

**Dependency Chain:**
- 7.1 → 7.2 (detector needs data structure)
- 7.2 → 7.3 (pipeline needs both detector + data model)
- 7.3 → 7.4 (renderer needs signals in metadata)
- 7.4 → 7.5 (example needs rendering to work)

**Deliverable:** v0.3.0 with complete peer-to-peer workflow signaling visualization capability

---

_Epic 7 breakdown created for temporalio-graphs-python-port - Peer-to-peer workflow signaling visualization using static analysis._

_Generated using BMM Epic and Story Decomposition Workflow - 2025-11-20_

_For implementation: Use the `create-story` workflow to generate individual story implementation plans from this epic breakdown._
