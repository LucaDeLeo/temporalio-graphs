# Epic Technical Specification: Decision Node Support (Branching Workflows)

Date: 2025-11-18
Author: Luca
Epic ID: 3
Status: Draft

---

## Overview

Epic 3 extends the temporalio-graphs library from linear workflow visualization to branching workflow visualization with complete path coverage. This epic implements decision node support, enabling the library to detect conditional logic (if/else, elif chains, ternary operators) in workflows and generate all possible execution paths (2^n paths for n decisions). The implementation adds the `to_decision()` helper function for marking decision points, AST-based decision detection, path permutation generation using combinatorial logic, and Mermaid diamond-shape rendering for decision nodes. This epic delivers the critical capability to visualize real-world workflows with conditional branching, showing users ALL possible execution paths rather than just linear sequences.

## Objectives and Scope

**Primary Objectives:**
- Implement `to_decision()` helper function for marking boolean expressions as decision nodes
- Build DecisionDetector to identify decision points in workflow AST
- Extend PathPermutationGenerator to create 2^n execution path permutations for n decisions
- Implement decision node rendering in Mermaid with diamond shape syntax `{DecisionName}`
- Port and validate MoneyTransfer example workflow from .NET showing 2 decisions = 4 paths

**In Scope:**
- FR11-FR17: Complete decision node support (helper function, custom names, branch labels, diamond shapes, permutations)
- FR46: elif chain detection (multiple sequential decisions)
- FR47: Ternary operator detection wrapped in to_decision()
- FR49: Reconverging branch handling in path generation
- Simple if/else conditionals and nested decisions
- Path explosion safeguards (max_decision_points limit, default 10)
- Decision node ID generation (deterministic hashing or sequential)
- Integration testing with MoneyTransfer workflow (2 decisions, 4 paths)

**Out of Scope (Future Epics):**
- Signal/wait condition support (Epic 4)
- Loop detection and visualization (Post-MVP growth features)
- Dynamic decision detection without to_decision() marker
- Complex control flow patterns (match/case statements, exception branching)
- Runtime-based decision tracking (static analysis only)

## System Architecture Alignment

**Alignment to Static Analysis Architecture:**
This epic builds directly on the AST-based static analysis foundation from Epic 2. The DecisionDetector extends the existing WorkflowAnalyzer (ast.NodeVisitor) pattern to identify `to_decision()` function calls during AST traversal. This aligns with ADR-001 (Static Analysis vs Runtime Interceptors) - we analyze code structure without executing workflows.

**Core Component Integration:**
- **DecisionDetector** (new): Visits ast.Call nodes, identifies to_decision() calls, extracts decision metadata
- **PathPermutationGenerator** (enhanced): Extends from linear path generation (Epic 2) to combinatorial permutation using itertools.product
- **MermaidRenderer** (enhanced): Adds NodeType.DECISION handling, renders diamond shapes, adds branch labels
- **GraphBuildingContext** (existing): Already includes max_decision_points, decision_true_label, decision_false_label configuration

**Performance Constraints:**
- NFR-PERF-1: 5 decisions (32 paths) must generate in <1 second
- NFR-PERF-1: 10 decisions (1024 paths) must generate in <5 seconds
- ADR-008: Default max_decision_points = 10 prevents path explosion (2^10 = 1024 paths)
- Path generation uses itertools.product for efficient O(2^n) permutation with early validation

**Data Flow:**
```
workflow.py → AST Parser → DecisionDetector → WorkflowMetadata.decision_points
                                                         ↓
WorkflowMetadata → PathPermutationGenerator → 2^n GraphPath objects
                                                         ↓
GraphPath[] → MermaidRenderer → Mermaid syntax with diamond decision nodes
```

## Detailed Design

### Services and Modules

**New Module: src/temporalio_graphs/detector.py**
- **DecisionDetector class**: AST visitor that identifies `to_decision()` function calls
- **Responsibilities**:
  - Traverse AST via `visit_Call()` method
  - Detect calls to `to_decision()` function
  - Extract decision name from second argument (string literal)
  - Record source line numbers for error reporting
  - Return `list[DecisionPoint]` to caller
- **Key Methods**:
  - `detect_decisions(tree: ast.AST) -> list[DecisionPoint]`: Main entry point
  - `visit_Call(node: ast.Call) -> None`: AST visitor for Call nodes
  - `_is_to_decision_call(node: ast.Call) -> bool`: Identifies to_decision pattern
  - `_extract_string_literal(node: ast.expr) -> str`: Gets decision name from args
  - `_generate_id(name: str, line: int) -> str`: Creates deterministic decision ID

**New Module: src/temporalio_graphs/helpers.py**
- **to_decision() function**: Workflow helper for marking decision points
- **Responsibilities**:
  - Transparent passthrough of boolean values
  - Marker for static analysis (detected by DecisionDetector)
  - No runtime behavior beyond returning input value
- **Signature**: `async def to_decision(result: bool, name: str) -> bool`
- **Exports**: Public API via `__init__.py`

**Enhanced Module: src/temporalio_graphs/analyzer.py**
- **WorkflowAnalyzer enhancements**:
  - Instantiates and calls DecisionDetector during analysis
  - Adds decision_points to WorkflowMetadata
  - Maintains backward compatibility with linear workflows (0 decisions)
- **New Integration Point**: After activity detection, run decision detection before returning metadata

**Enhanced Module: src/temporalio_graphs/generator.py**
- **PathPermutationGenerator enhancements**:
  - Handles workflows with decision points (extends Epic 2 linear logic)
  - Generates 2^n paths for n decisions using `itertools.product`
  - Early validation: checks `len(decisions) <= context.max_decision_points`
  - Raises `GraphGenerationError` if limit exceeded
  - Maintains O(2^n) time complexity, optimized via C-based itertools
- **New Methods**:
  - `_build_path_with_decisions(decisions: list[DecisionPoint], choices: tuple[bool, ...]) -> GraphPath`
  - `_check_explosion_limit(num_decisions: int, context: GraphBuildingContext) -> None`

**Enhanced Module: src/temporalio_graphs/renderer.py**
- **MermaidRenderer enhancements**:
  - Adds `NodeType.DECISION` handling
  - Renders decision nodes with diamond syntax: `{DecisionName}`
  - Adds branch labels to edges from decisions (`-- yes -->`, `-- no -->`)
  - Supports custom branch labels via `context.decision_true_label` and `context.decision_false_label`
  - Decision node deduplication (same decision appears once even in multiple paths)

**Module Dependency Graph**:
```
helpers.py (standalone, no deps)
    ↓ (used by workflows)
workflow.py → analyzer.py → detector.py → _internal/graph_models.py (DecisionPoint)
                    ↓
            WorkflowMetadata → generator.py (+ itertools) → GraphPath[]
                                                    ↓
                                            renderer.py → Mermaid string
```

### Data Models and Contracts

**New Dataclass: DecisionPoint** (in `src/temporalio_graphs/_internal/graph_models.py`)

```python
from dataclasses import dataclass

@dataclass
class DecisionPoint:
    """Represents a decision point detected in workflow code.

    Attributes:
        decision_id: Deterministic identifier (hash-based or sequential)
        name: User-provided decision name from to_decision() second argument
        line_number: Source code line number for error reporting
        true_label: Branch label for True path (default "yes", configurable)
        false_label: Branch label for False path (default "no", configurable)
    """
    decision_id: str
    name: str
    line_number: int
    true_label: str = "yes"
    false_label: str = "no"
```

**Enhanced Dataclass: WorkflowMetadata** (in `src/temporalio_graphs/_internal/graph_models.py`)

```python
@dataclass
class WorkflowMetadata:
    """Workflow analysis results (enhanced from Epic 2)."""
    workflow_class: str
    workflow_run_method: str
    activities: list[str]
    decision_points: list[DecisionPoint] = field(default_factory=list)  # NEW in Epic 3
    signal_points: list[SignalPoint] = field(default_factory=list)  # Future Epic 4
    source_file: Path
    total_paths: int  # Computed as 2^len(decision_points)
```

**Enhanced Enum: NodeType** (in `src/temporalio_graphs/_internal/graph_models.py`)

```python
from enum import Enum

class NodeType(Enum):
    """Graph node types (enhanced from Epic 2)."""
    START = "start"
    END = "end"
    ACTIVITY = "activity"
    DECISION = "decision"  # NEW in Epic 3
    SIGNAL = "signal"  # Future Epic 4
```

**Enhanced Dataclass: GraphBuildingContext** (in `src/temporalio_graphs/context.py`)

```python
@dataclass(frozen=True)
class GraphBuildingContext:
    """Configuration for graph generation (partial listing - decision-related fields).

    Complete context exists from Epic 2, Epic 3 uses these fields:
    """
    # ... existing fields from Epic 2 ...
    max_decision_points: int = 10  # ADR-008: Path explosion prevention
    max_paths: int = 1024  # Safety limit (2^10)
    decision_true_label: str = "yes"  # FR13: Customizable branch labels
    decision_false_label: str = "no"  # FR13: Customizable branch labels
```

**Data Contracts:**

**Input Contract** (from user workflow to library):
```python
# User workflow must use to_decision() helper
from temporalio_graphs import to_decision

@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self, amount: int) -> str:
        if await to_decision(amount > 1000, "HighValue"):  # Contract: (bool, str) -> bool
            await workflow.execute_activity(special_handling)
        return "done"
```

**Output Contract** (from DecisionDetector to PathPermutationGenerator):
```python
# DecisionDetector returns list of DecisionPoint objects
decision_points: list[DecisionPoint] = detector.detect_decisions(ast_tree)

# Contract guarantees:
# - Each DecisionPoint has unique decision_id
# - line_number is valid source location
# - name is non-empty string literal
```

**Path Permutation Contract** (from generator to renderer):
```python
# Generator produces 2^n GraphPath objects for n decisions
# Each GraphPath contains decision nodes interleaved with activities
# Contract guarantees:
# - Exactly 2^len(decision_points) paths generated
# - Each path has unique decision value combination
# - All paths start with Start node, end with End node
```

### APIs and Interfaces

**Public API - to_decision() Helper Function** (FR11, FR37)

```python
async def to_decision(result: bool, name: str) -> bool:
    """Mark a boolean expression as a decision node in the workflow graph.

    This helper function enables static analysis to identify decision points
    during AST traversal. The function is transparent—it returns the input
    boolean unchanged, so workflow logic is unaffected.

    Args:
        result: The boolean value to evaluate (e.g., `amount > 1000`)
        name: Human-readable decision name for graph display (e.g., "HighValue")

    Returns:
        The original boolean value (passthrough for workflow logic)

    Example:
        >>> if await to_decision(amount > 1000, "HighValue"):
        >>>     await workflow.execute_activity(special_processing)
        >>>
        >>> # Also works with assignment:
        >>> needs_approval = await to_decision(amount > 10000, "NeedsApproval")
        >>> if needs_approval:
        >>>     await workflow.execute_activity(request_approval)

    Note:
        Must be called with `await` in async workflows. Decision name must be
        a string literal (not a variable) for static analysis to extract it.
    """
    return result
```

**Internal API - DecisionDetector Class**

```python
class DecisionDetector(ast.NodeVisitor):
    """AST visitor that detects to_decision() calls in workflow code."""

    def __init__(self):
        """Initialize detector with empty decision list."""
        self.decision_points: list[DecisionPoint] = []

    def detect_decisions(self, tree: ast.AST) -> list[DecisionPoint]:
        """Visit AST and extract all decision points.

        Args:
            tree: Parsed AST from workflow source code

        Returns:
            List of DecisionPoint objects, one per to_decision() call

        Raises:
            UnsupportedPatternError: If decision name is not a string literal
        """
        self.decision_points = []  # Reset for reuse
        self.visit(tree)
        return self.decision_points

    def visit_Call(self, node: ast.Call) -> None:
        """Check if this Call node is a to_decision() invocation."""
        if self._is_to_decision_call(node):
            decision_name = self._extract_decision_name(node)
            decision_id = self._generate_decision_id(decision_name, node.lineno)
            self.decision_points.append(DecisionPoint(
                decision_id=decision_id,
                name=decision_name,
                line_number=node.lineno
            ))
        self.generic_visit(node)

    def _is_to_decision_call(self, node: ast.Call) -> bool:
        """Check if Call node is to_decision() function."""
        return (
            isinstance(node.func, ast.Name) and
            node.func.id == "to_decision"
        )

    def _extract_decision_name(self, node: ast.Call) -> str:
        """Extract decision name from second argument (must be string literal)."""
        if len(node.args) < 2:
            raise InvalidDecisionError(
                f"to_decision() requires 2 arguments at line {node.lineno}"
            )
        name_arg = node.args[1]
        if isinstance(name_arg, ast.Constant) and isinstance(name_arg.value, str):
            return name_arg.value
        raise UnsupportedPatternError(
            "decision name must be string literal",
            f"Use to_decision(expr, \"DecisionName\") at line {node.lineno}"
        )

    def _generate_decision_id(self, name: str, line: int) -> str:
        """Generate deterministic decision ID (FR17)."""
        # Option 1: Sequential (simpler, recommended)
        return str(len(self.decision_points))

        # Option 2: Hash-based (preserves names, more stable across edits)
        # import hashlib
        # return hashlib.sha256(f"{name}:{line}".encode()).hexdigest()[:8]
```

**Internal API - PathPermutationGenerator Enhancements** (FR6, FR15, FR16)

```python
class PathPermutationGenerator:
    """Generates all possible execution paths through workflow (enhanced from Epic 2)."""

    def generate_paths(
        self,
        metadata: WorkflowMetadata,
        context: GraphBuildingContext
    ) -> list[GraphPath]:
        """Generate 2^n paths for n decisions.

        Args:
            metadata: Workflow metadata with activities and decision_points
            context: Configuration including max_decision_points limit

        Returns:
            List of GraphPath objects, one per unique execution path

        Raises:
            GraphGenerationError: If decision count exceeds max_decision_points
        """
        decisions = metadata.decision_points

        # Handle linear workflows (0 decisions)
        if not decisions:
            return [self._create_linear_path(metadata)]

        # Explosion check (ADR-008)
        self._check_explosion_limit(len(decisions), context)

        # Generate 2^n permutations using itertools.product
        from itertools import product
        paths = []
        for decision_values in product([True, False], repeat=len(decisions)):
            path = self._build_path_with_decisions(
                metadata,
                decisions,
                decision_values,
                context
            )
            paths.append(path)

        return paths

    def _check_explosion_limit(
        self,
        num_decisions: int,
        context: GraphBuildingContext
    ) -> None:
        """Validate decision count is within limits."""
        if num_decisions > context.max_decision_points:
            total_paths = 2 ** num_decisions
            raise GraphGenerationError(
                f"Too many decision points ({num_decisions}) would generate "
                f"{total_paths} paths (limit: {context.max_paths})\n"
                f"Suggestion: Refactor workflow to reduce decisions, or increase "
                f"max_decision_points in GraphBuildingContext"
            )

    def _build_path_with_decisions(
        self,
        metadata: WorkflowMetadata,
        decisions: list[DecisionPoint],
        decision_values: tuple[bool, ...],
        context: GraphBuildingContext
    ) -> GraphPath:
        """Build single path with specific decision values."""
        path = GraphPath(path_id=f"path_{len(self._paths_built)}")

        # Add Start node
        path.add_node("s", NodeType.START, context.start_node_label)

        # Interleave activities and decisions based on AST order
        # (Simplified - actual implementation tracks position in workflow)
        for activity in metadata.activities:
            path.add_activity(activity)

        for i, (decision, value) in enumerate(zip(decisions, decision_values)):
            label = decision.true_label if value else decision.false_label
            path.add_decision(decision.decision_id, value, decision.name, label)

        # Add End node
        path.add_node("e", NodeType.END, context.end_node_label)

        return path
```

### Workflows and Sequencing

**Decision Detection and Path Generation Workflow:**

**Phase 1: AST Parsing** (existing from Epic 2)
1. User calls `analyze_workflow("workflow.py", context)`
2. WorkflowAnalyzer reads file and calls `ast.parse(source)`
3. AST tree structure created in memory
4. WorkflowAnalyzer visits ClassDef nodes to find `@workflow.defn`

**Phase 2: Decision Detection** (NEW in Epic 3)
1. WorkflowAnalyzer instantiates `DecisionDetector()`
2. Calls `detector.detect_decisions(ast_tree)`
3. DecisionDetector traverses AST via `visit_Call()` for each Call node
4. For each call matching pattern `to_decision(expr, "Name")`:
   - Extract decision name from args[1] (must be string literal)
   - Generate deterministic decision_id
   - Record source line_number
   - Create DecisionPoint object
   - Append to detector.decision_points list
5. Return `list[DecisionPoint]` to WorkflowAnalyzer
6. Add to WorkflowMetadata.decision_points

**Phase 3: Path Permutation** (ENHANCED in Epic 3)
1. PathPermutationGenerator receives WorkflowMetadata
2. Extract decision_points list: `decisions = metadata.decision_points`
3. Validate: `if len(decisions) > context.max_decision_points: raise Error`
4. Generate permutations: `itertools.product([True, False], repeat=len(decisions))`
   - Example: 2 decisions → [(True, True), (True, False), (False, True), (False, False)]
5. For each permutation tuple:
   - Build GraphPath with activities and decision nodes
   - Track which branch taken (True/False) for each decision
   - Add decision nodes to path with appropriate labels
6. Return list of 2^n GraphPath objects

**Phase 4: Mermaid Rendering** (ENHANCED in Epic 3)
1. MermaidRenderer receives GraphPath list
2. Extract unique nodes from all paths (deduplicate)
3. Build edges between nodes based on path sequences
4. For NodeType.DECISION nodes:
   - Render with diamond syntax: `{decision_id}{DecisionName}`
   - Add branch label to outgoing edges: `-- yes -->` or `-- no -->`
5. Generate Mermaid flowchart syntax
6. Return complete Mermaid markdown string

**Sequence Diagram:**
```
User → analyze_workflow(file, context)
  ↓
WorkflowAnalyzer
  ├→ ast.parse(source) → AST
  ├→ DecisionDetector.detect_decisions(AST)
  │   └→ visit_Call() for each Call node
  │       └→ if to_decision() → extract name → DecisionPoint
  │   └→ return list[DecisionPoint]
  ├→ ActivityDetector (existing from Epic 2)
  └→ return WorkflowMetadata(activities, decision_points)
  ↓
PathPermutationGenerator
  ├→ check len(decisions) <= max_decision_points
  ├→ itertools.product([True, False], repeat=n)
  ├→ for each permutation:
  │   └→ build GraphPath with decision values
  └→ return list[GraphPath] (2^n paths)
  ↓
MermaidRenderer
  ├→ deduplicate nodes
  ├→ build edges with labels
  ├→ render decision nodes as diamonds
  └→ return Mermaid string
  ↓
Return to user
```

**Key Sequencing Invariants:**
- Decision detection MUST happen before path generation (need decision count for explosion check)
- Explosion limit check MUST happen before itertools.product (fail fast)
- Node deduplication MUST happen during rendering (same decision appears in multiple paths)
- Decision IDs MUST be deterministic (same workflow → same IDs every time)

## Non-Functional Requirements

### Performance

**NFR-PERF-1: Analysis Speed** (from PRD)
- **Requirement**: 5 decisions (32 paths) generate in <1 second
- **Requirement**: 10 decisions (1024 paths) generate in <5 seconds
- **Implementation**: `itertools.product` uses C-optimized combinatorics, O(2^n) time complexity unavoidable
- **Measurement**: Unit tests with `time.perf_counter()` validate targets
- **Test**: `test_performance_32_paths` and `test_performance_1024_paths` enforce timing

**NFR-PERF-2: Memory Efficiency** (ADR-008)
- **Requirement**: Path explosion safeguard prevents runaway memory use
- **Implementation**: `max_decision_points = 10` default limit (2^10 = 1024 paths max)
- **Memory estimate**: Each GraphPath ~1KB, 1024 paths = ~1MB (acceptable)
- **Early validation**: Check decision count BEFORE generating permutations (fail fast)
- **User override**: Configurable via `GraphBuildingContext(max_decision_points=15)` if needed

**Performance Optimization Strategy:**
- **DecisionDetector**: Single AST traversal, O(n) nodes visited, <0.5ms typical
- **PathPermutationGenerator**: Uses `itertools.product` (C implementation), minimal Python overhead
- **No premature optimization**: Simple, correct implementation first; profile if needed
- **Future optimization**: Lazy path generation (yield paths one at a time) if memory becomes issue

### Security

**No New Security Concerns**
- Epic 3 maintains Epic 2 security model: static analysis only, no code execution
- `to_decision()` is pure function with no side effects
- `DecisionDetector` only reads AST, never modifies source code
- No network access, no file writes (except configured output file)
- All security properties from ADR-001 (Static Analysis) preserved

### Reliability/Availability

**NFR-REL-1: Correctness** (from PRD)
- **Requirement**: All 2^n permutations correctly generated (no missing paths)
- **Validation**: Unit tests verify: 1 decision → 2 paths, 2 decisions → 4 paths, 3 decisions → 8 paths
- **Regression**: MoneyTransfer output must match .NET version structurally (FR52)
- **Test strategy**: Golden file comparison against .NET reference implementation

**Determinism:**
- Same workflow → same decision IDs → same path ordering → same Mermaid output
- Decision ID generation is deterministic (sequential or hash-based)
- `itertools.product` produces permutations in lexicographic order (stable)

**Error Handling:**
- Clear error when decision name is not string literal
- Clear error when `max_decision_points` exceeded
- Error messages include line numbers, suggestions for fix
- No silent failures (all errors raise exceptions)

### Observability

**Logging Strategy** (for debugging and performance monitoring)

```python
import logging
logger = logging.getLogger(__name__)

# Decision detection logging
logger.debug(f"Found {len(decision_points)} decision points in workflow")
logger.debug(f"Decision names: {[d.name for d in decision_points]}")

# Path generation logging
logger.debug(f"Generating {2**len(decisions)} path permutations")
logger.info(f"Path generation complete: {len(paths)} paths created")

# Performance logging (if enabled)
logger.debug(f"Decision detection: {detection_time*1000:.2f}ms")
logger.debug(f"Path permutation: {generation_time*1000:.2f}ms")
```

**Log Levels:**
- **DEBUG**: AST traversal details, decision extraction, path count, timing
- **INFO**: High-level workflow analysis status
- **WARNING**: Not used in Epic 3 (Epic 5 will add validation warnings)
- **ERROR**: Exception details (UnsupportedPatternError, GraphGenerationError)

**No Built-in Metrics:**
- Library doesn't export metrics (prometheus, statsd, etc.)
- Users can wrap `analyze_workflow()` to add their own instrumentation

## Dependencies and Integrations

**Runtime Dependencies (pyproject.toml):**
```toml
[project]
dependencies = [
    "temporalio>=1.7.1",  # Existing from Epic 2
]
```

**Python Standard Library (NEW usage in Epic 3):**
- `itertools.product` - Combinatorial permutation generation (Epic 3)
- `ast` - Existing from Epic 2 (no changes)
- `dataclasses`, `typing`, `pathlib` - Existing from Epic 2

**Development Dependencies (no changes):**
```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.21.0",
    "mypy",
    "ruff",
]
```

**Internal Module Dependencies:**
- `detector.py` → depends on: `ast`, `_internal/graph_models.DecisionPoint`, `exceptions`
- `helpers.py` → depends on: nothing (standalone pure function)
- `analyzer.py` → NEW dependency: `detector.DecisionDetector`
- `generator.py` → NEW dependency: `itertools.product`
- `renderer.py` → NEW usage: `NodeType.DECISION` (enum value added in Epic 2, used in Epic 3)

**External Tool Integration:**
- **Mermaid Live Editor** (https://mermaid.live): Validation target for generated syntax
- **.NET Temporalio.Graphs**: Reference implementation for regression testing

**User Workflow Integration:**
- Users must import `to_decision` helper: `from temporalio_graphs import to_decision`
- Users must add `await to_decision(expr, "Name")` calls to workflow code
- No changes to Temporal SDK usage (workflows run normally with or without graph generation)

**Backward Compatibility:**
- Epic 3 is 100% backward compatible with Epic 2
- Linear workflows (0 decisions) continue to work exactly as before
- New `to_decision()` export added to public API (non-breaking addition)
- `GraphBuildingContext` fields added with sensible defaults (non-breaking)

## Acceptance Criteria (Authoritative)

**Story 3.1: Decision Point Detection** (FR5, FR12, FR46, FR47)
- [ ] DecisionDetector class exists in `src/temporalio_graphs/detector.py`
- [ ] Detector identifies `to_decision()` function calls in AST via `visit_Call()`
- [ ] Detector extracts decision name from second argument (string literal validation)
- [ ] Detector handles pattern: `if await to_decision(condition, "Name"):`
- [ ] Detector identifies elif chains as multiple sequential decisions (FR46)
- [ ] Detector identifies ternary operators: `value = await to_decision(x if y else z, "Name")` (FR47)
- [ ] Detector records source line_number for each decision for error reporting
- [ ] `decision_points` list added to WorkflowMetadata dataclass
- [ ] Unit tests cover: single decision, multiple decisions, nested decisions, elif chain, ternary
- [ ] 100% test coverage for DecisionDetector class

**Story 3.2: to_decision() Helper Function** (FR11, FR12, FR37, FR40, FR41, FR43)
- [ ] Function exists in `src/temporalio_graphs/helpers.py`
- [ ] Signature: `async def to_decision(result: bool, name: str) -> bool`
- [ ] Returns input boolean unchanged (transparent passthrough)
- [ ] Async-compatible for workflow use (can be awaited) (FR43)
- [ ] Complete type hints pass mypy strict mode (FR40)
- [ ] Google-style docstring with usage example (FR41)
- [ ] Exported from public API via `__init__.py` (FR37)
- [ ] Unit tests verify correct boolean return for True and False values
- [ ] Integration test demonstrates function works in actual workflow

**Story 3.3: Path Permutation Generator** (FR6, FR13, FR15, FR16, FR49, NFR-PERF-1, NFR-PERF-2)
- [ ] Generator creates 2^n paths for n independent decisions (FR6, FR16)
- [ ] Each decision generates exactly 2 branches (true/false) (FR15)
- [ ] Branch labels default to "yes" and "no" (FR13)
- [ ] Custom branch labels supported via `context.decision_true_label` and `context.decision_false_label`
- [ ] Decision nodes included in GraphPath with correct values
- [ ] Nested decisions create proper permutations (2 decisions → 4 paths) (FR16)
- [ ] Reconverging branches handled correctly (activities after decision in all paths) (FR49)
- [ ] Generator uses `itertools.product([True, False], repeat=n)` for efficient permutation
- [ ] Generator checks `len(decisions) <= context.max_decision_points` BEFORE generation
- [ ] `GraphGenerationError` raised if decision_points > limit (default 10)
- [ ] Error message suggests refactoring or increasing limit
- [ ] Performance: 32 paths (5 decisions) generated in <1 second (NFR-PERF-1)
- [ ] Performance: 1024 paths (10 decisions) generated in <5 seconds (NFR-PERF-1)
- [ ] Safety: max_paths limit prevents memory exhaustion (NFR-PERF-2)
- [ ] Unit tests: 1 decision (2 paths), 2 decisions (4 paths), 3 decisions (8 paths), explosion limit
- [ ] Test validates all permutations generated (no missing paths)

**Story 3.4: Decision Node Rendering** (FR13, FR14, FR15, FR17, FR51, FR52, FR55)
- [ ] Decision nodes render with diamond syntax: `0{DecisionName}` (FR14)
- [ ] Decision node IDs deterministic (sequential numbering recommended) (FR17)
- [ ] True branches render with label: `-- yes -->` (default)
- [ ] False branches render with label: `-- no -->` (default)
- [ ] Custom branch labels supported via configuration
- [ ] Decision nodes deduplicate correctly (same decision ID appears once in output)
- [ ] Edges from decisions to activities render correctly
- [ ] Parallel branches from decision reconverge properly
- [ ] Generated Mermaid is valid and renders in Mermaid Live Editor (FR51)
- [ ] Output matches .NET Temporalio.Graphs structure for equivalent workflows (FR52, FR55)
- [ ] Unit tests compare against .NET golden files for regression
- [ ] Tests cover: single decision, multiple decisions, nested decisions

**Story 3.5: MoneyTransfer Integration** (FR52, FR56, FR57)
- [ ] `examples/money_transfer/workflow.py` exists (ported from .NET) (FR56)
- [ ] Workflow has 2 decision points: "NeedToConvert" and "IsTFN_Known" (FR57)
- [ ] Workflow generates exactly 4 paths (2^2) (FR57)
- [ ] Workflow includes all 5 activities: Withdraw, CurrencyConvert, NotifyAto, TakeNonResidentTax, Deposit
- [ ] `analyze_workflow()` produces valid Mermaid output
- [ ] Output structure matches .NET Temporalio.Graphs output (FR52, FR57)
- [ ] Generated graph clearly shows all 4 execution paths
- [ ] `examples/money_transfer/run.py` demonstrates usage
- [ ] `examples/money_transfer/expected_output.md` contains golden Mermaid diagram
- [ ] `tests/integration/test_money_transfer.py` validates output
- [ ] Regression test compares output against .NET golden file (structural equivalence)
- [ ] Test passes with 100% accuracy
- [ ] Example documented in README

**Total: 45 Acceptance Criteria** (all must pass for Epic 3 completion)

## Traceability Mapping

| FR | Description | Spec Section | Component(s) | API/Interfaces | Test Idea |
|----|-------------|--------------|--------------|----------------|-----------|
| FR11 | to_decision() helper | APIs & Interfaces | helpers.py | `async def to_decision(result: bool, name: str) -> bool` | test_to_decision_returns_true, test_to_decision_returns_false |
| FR12 | Custom decision names | Data Models | DecisionPoint.name | DecisionDetector._extract_decision_name() | test_decision_name_extraction_from_string_literal |
| FR13 | Custom branch labels | Data Models, NFRs | GraphBuildingContext.decision_true_label | MermaidRenderer edge labels | test_custom_branch_labels_override_default |
| FR14 | Diamond shapes | APIs & Interfaces, Workflows | MermaidRenderer | GraphNode.to_mermaid() for DECISION | test_decision_node_renders_diamond_syntax |
| FR15 | 2 branches per decision | Workflows & Sequencing | PathPermutationGenerator | itertools.product([True, False], ...) | test_single_decision_two_paths |
| FR16 | Nested permutations | Workflows & Sequencing | PathPermutationGenerator | product(..., repeat=n) | test_two_decisions_four_paths, test_three_decisions_eight_paths |
| FR17 | Decision ID preservation | APIs & Interfaces | DecisionDetector._generate_decision_id() | Sequential or hash-based | test_decision_ids_deterministic |
| FR46 | elif chains | Workflows & Sequencing | DecisionDetector | visit_If for If nodes | test_elif_chain_multiple_decisions |
| FR47 | Ternary operators | Workflows & Sequencing | DecisionDetector | visit_IfExp for IfExp nodes | test_ternary_wrapped_in_to_decision |
| FR49 | Reconverging branches | Workflows & Sequencing | PathPermutationGenerator | Path building logic | test_activities_after_decision_in_all_paths |

**Component → Test File Mapping:**
- `detector.py` → `tests/test_detector.py` (unit tests for decision detection)
- `helpers.py` → `tests/test_helpers.py` (unit tests for to_decision function)
- `generator.py` → `tests/test_generator.py` (enhanced with decision permutation tests)
- `renderer.py` → `tests/test_renderer.py` (enhanced with decision node rendering tests)
- Integration → `tests/integration/test_money_transfer.py` (full pipeline validation)

**FR → Story → Test Coverage:**
- FR11, FR12 → Story 3.1, 3.2 → test_detector.py, test_helpers.py
- FR13, FR14, FR15, FR17 → Story 3.4 → test_renderer.py
- FR16 → Story 3.3 → test_generator.py
- FR46, FR47, FR49 → Story 3.1, 3.3 → test_detector.py, test_generator.py
- FR52, FR56, FR57 → Story 3.5 → test_money_transfer.py (integration)

## Risks, Assumptions, Open Questions

### Risks

**RISK-1: Path Explosion Performance Degradation**
- **Severity:** High
- **Probability:** Medium
- **Description:** Users with workflows containing >10 decisions could attempt to generate >1024 paths, causing memory exhaustion or timeout
- **Mitigation:**
  - ADR-008 enforces default `max_decision_points = 10`
  - Early validation check raises clear error before permutation starts
  - Error message suggests workflow refactoring or increasing limit
- **Fallback:** User can override limit via `GraphBuildingContext(max_decision_points=15)` if they understand the tradeoff
- **Impact:** Medium (users blocked, but clear guidance provided)

**RISK-2: MoneyTransfer Output Mismatch with .NET**
- **Severity:** Medium
- **Probability:** Low
- **Description:** Python implementation may generate different Mermaid syntax structure than .NET version, failing FR52 compliance
- **Mitigation:**
  - Story 3.5 includes golden file regression test
  - Use structural equivalence check (nodes + edges) rather than byte-for-byte
  - Document any intentional differences (e.g., decision ID format)
- **Fallback:** If differences are minor and semantically equivalent, document as "implementation variation"
- **Impact:** Low (mainly documentation/explanation effort)

**RISK-3: to_decision() Adoption Friction**
- **Severity:** Low
- **Probability:** High
- **Description:** Users may resist modifying workflow code to add `to_decision()` calls, perceiving it as invasive
- **Mitigation:**
  - Clear documentation explaining why explicit marking is needed (ADR-005)
  - MoneyTransfer example demonstrates pattern is reasonable
  - Error message when decisions not detected suggests adding to_decision()
- **Fallback:** Future enhancement (post-MVP) could auto-detect some obvious decisions, but this is out of scope for Epic 3
- **Impact:** Low (user education and documentation issue)

**RISK-4: Dynamic Decision Names Not Supported**
- **Severity:** Low
- **Probability:** Medium
- **Description:** Users attempt dynamic names like `to_decision(x > y, f"Check_{variable}")`, which static analysis cannot extract
- **Mitigation:**
  - DecisionDetector validates args[1] is string literal (ast.Constant)
  - Raise `UnsupportedPatternError` with clear message
  - Suggestion: "Use static string literal for decision name"
- **Fallback:** None needed (this is by design, static analysis limitation)
- **Impact:** Low (users can refactor to static names)

### Assumptions

**ASSUMPTION-1: Users willing to add to_decision() markers**
- **Basis:** ADR-005 decision, .NET version requires similar marking
- **Validation:** MoneyTransfer example demonstrates pattern
- **Impact if wrong:** Low adoption, need auto-detection feature (post-MVP)
- **Confidence:** High

**ASSUMPTION-2: itertools.product performance sufficient for 2^10 permutations**
- **Basis:** Architecture spike validated static analysis is <1ms, itertools is C-implemented
- **Validation:** Performance unit tests enforce <1s for 32 paths, <5s for 1024 paths
- **Impact if wrong:** Performance targets missed, need optimization or lower default limit
- **Confidence:** High (proven in spike)

**ASSUMPTION-3: .NET MoneyTransfer output is canonical reference**
- **Basis:** .NET version is production code in Temporalio.Graphs repo, approved by Temporal team
- **Validation:** Reference implementation accessible at Temporalio.Graphs/Samples/
- **Impact if wrong:** Regression test harder to define (need different baseline)
- **Confidence:** High

**ASSUMPTION-4: Sequential decision IDs acceptable for MVP**
- **Basis:** Simpler than hash-based, deterministic, FR17 allows configuration
- **Validation:** Can switch to hash-based later if needed
- **Impact if wrong:** Decision IDs less stable across edits (minor UX issue)
- **Confidence:** Medium (may need to revisit based on user feedback)

### Open Questions

**Q-1: Sequential vs Hash-Based Decision IDs** (FR17)
- **Question:** Should decision IDs be sequential (0, 1, 2...) or hash-based (SHA256 of name+line)?
- **Options:**
  - Sequential: Simpler, predictable, but changes if decision order changes
  - Hash: More stable across edits, but harder to debug
- **Recommendation:** Sequential for MVP (Story 3.1), make configurable later if needed
- **Decision owner:** Tech lead during Story 3.1 implementation
- **Status:** Open (recommend sequential)

**Q-2: How to handle dynamic decision names**
- **Question:** User writes `to_decision(x > y, f"Check_{variable}")` - should we support this?
- **Options:**
  - Support via eval (unsafe, rejected)
  - Extract static part "Check_" (complex, limited value)
  - Raise clear error (simple, forces good practice)
- **Recommendation:** Raise `UnsupportedPatternError` with suggestion to use static string
- **Decision owner:** Story 3.1 implementation
- **Status:** Open (recommend error)

**Q-3: elif rendering - single multi-branch node or multiple binary nodes**
- **Question:** Should `if X: ... elif Y: ... elif Z: ...` show as one 3-branch node or three 2-branch nodes?
- **Options:**
  - Single multi-branch: More compact, but Mermaid diamonds are binary
  - Multiple binary: Matches Mermaid capabilities, FR46 says "multiple decisions"
- **Recommendation:** Multiple binary decision nodes (simpler, matches FR46 wording, consistent with .NET)
- **Decision owner:** Already decided by FR46 ("elif chains as multiple decision points")
- **Status:** Resolved (multiple binary nodes)

## Test Strategy Summary

### Unit Testing (>80% coverage target, 100% for core logic)

**tests/test_detector.py** (DecisionDetector - 100% coverage)
```python
def test_single_decision_detection():
    """Verify single to_decision() call identified."""

def test_multiple_decisions_detection():
    """Multiple to_decision() calls in one workflow."""

def test_nested_decisions_detection():
    """Decision inside if branch of another decision."""

def test_elif_chain_detection():
    """elif creates multiple DecisionPoint objects (FR46)."""

def test_ternary_operator_detection():
    """IfExp node wrapped in to_decision (FR47)."""

def test_decision_name_extraction():
    """String literal from args[1] extracted correctly."""

def test_dynamic_name_raises_error():
    """f-string or variable raises UnsupportedPatternError."""

def test_line_number_recording():
    """Source line captured for error reporting."""

def test_no_decisions_empty_list():
    """Workflow without to_decision returns []."""
```

**tests/test_helpers.py** (to_decision - 100% coverage)
```python
def test_to_decision_returns_true():
    """Verify True passthrough."""
    assert await to_decision(True, "Test") == True

def test_to_decision_returns_false():
    """Verify False passthrough."""
    assert await to_decision(False, "Test") == False

def test_to_decision_async_compatible():
    """Can be awaited in async context."""

def test_to_decision_type_hints():
    """mypy strict validation passes."""
```

**tests/test_generator.py** (Enhanced from Epic 2 - 100% for decision logic)
```python
def test_zero_decisions_single_path():
    """Linear workflow preserved from Epic 2."""

def test_one_decision_two_paths():
    """Binary branching (FR15)."""
    assert len(paths) == 2

def test_two_decisions_four_paths():
    """Combinatorial (FR16)."""
    assert len(paths) == 4

def test_three_decisions_eight_paths():
    """Validate 2^n formula."""
    assert len(paths) == 8

def test_explosion_limit_raises_error():
    """max_decision_points enforcement (ADR-008)."""
    with pytest.raises(GraphGenerationError):
        generator.generate_paths(metadata_with_11_decisions, context)

def test_nested_decisions_all_permutations():
    """No missing paths in nested structure."""

def test_reconverging_branches():
    """Activities after decision in all paths (FR49)."""

def test_performance_32_paths():
    """<1 second for 5 decisions (NFR-PERF-1)."""
    start = time.perf_counter()
    generator.generate_paths(metadata_5_decisions, context)
    assert time.perf_counter() - start < 1.0

def test_performance_1024_paths():
    """<5 seconds for 10 decisions."""
    start = time.perf_counter()
    generator.generate_paths(metadata_10_decisions, context)
    assert time.perf_counter() - start < 5.0
```

**tests/test_renderer.py** (Enhanced from Epic 2 - 100% for decision rendering)
```python
def test_decision_node_diamond_syntax():
    """Verify {DecisionName} format (FR14)."""

def test_decision_id_deterministic():
    """Same workflow → same IDs (FR17)."""

def test_true_branch_label_default():
    """Default 'yes' label."""

def test_false_branch_label_default():
    """Default 'no' label."""

def test_custom_branch_labels():
    """Configuration override (FR13)."""
    context = GraphBuildingContext(decision_true_label="T", decision_false_label="F")

def test_decision_node_deduplication():
    """Decision appears once in output."""

def test_edges_from_decision():
    """Both branches render correctly."""

def test_mermaid_validates_in_editor():
    """Output valid in Mermaid Live Editor (FR51)."""
```

### Integration Testing (Full pipeline validation)

**tests/integration/test_money_transfer.py** (Story 3.5)
```python
def test_money_transfer_four_paths():
    """2 decisions → 4 paths (FR57)."""
    result = analyze_workflow("examples/money_transfer/workflow.py")
    paths = extract_paths(result)
    assert len(paths) == 4

def test_money_transfer_activity_sequence():
    """All 5 activities present in paths."""

def test_money_transfer_decision_names():
    """'NeedToConvert' and 'IsTFN_Known' (FR56, FR57)."""

def test_money_transfer_mermaid_valid():
    """Output renders correctly."""

def test_money_transfer_vs_dotnet_golden():
    """Regression vs .NET output (FR52)."""
    python_output = analyze_workflow("examples/money_transfer/workflow.py")
    golden = read_file("tests/fixtures/golden/money_transfer_dotnet.md")
    assert structurally_equivalent(python_output, golden)

def test_money_transfer_performance():
    """<1 second total analysis."""
```

### Regression Testing (NFR-REL-1)

**Golden File Strategy:**
- `tests/fixtures/golden/money_transfer_dotnet.md` - Expected .NET output
- Comparison: Structural equivalence (nodes + edges match, order may differ)
- CI enforcement: pytest fails if regression detected

### Test Coverage Metrics
- Overall project: >80% (NFR-QUAL-2)
- Core decision logic: 100% (detector, generator decision paths, renderer decision nodes)
- Integration: MoneyTransfer full pipeline
- Measurement: `pytest --cov=src/temporalio_graphs --cov-fail-under=80`

### Edge Cases Tested
- Workflow with 0 decisions (linear flow, Epic 2 compatibility)
- Workflow with exactly `max_decision_points` (boundary case)
- Workflow with `max_decision_points + 1` (error case)
- Dynamic decision names (error case, UnsupportedPatternError)
- Missing to_decision() wrapper (no decisions detected, warning in Epic 5)
- Nested decisions at multiple levels (permutation correctness)
- Reconverging branches with activities after merge point (FR49)

---

**Epic 3 Technical Specification Complete**

This spec provides complete implementation guidance for Decision Node Support, covering all 10 FRs (11-17, 46-47, 49) across 5 stories with detailed technical design, acceptance criteria, traceability, and comprehensive test strategy.
