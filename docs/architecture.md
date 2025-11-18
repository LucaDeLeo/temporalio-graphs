# Architecture

## Executive Summary

The temporalio-graphs Python library uses **static code analysis** to generate complete workflow visualization diagrams without workflow execution. Built on Python's AST (Abstract Syntax Tree) module, it analyzes workflow source code to detect all possible execution paths and outputs Mermaid flowchart syntax. This architecture achieves feature parity with the proven .NET implementation while leveraging Python-native static analysis instead of runtime interceptors—resulting in faster analysis (<1ms), simpler integration, and no execution overhead.

## Project Initialization

**First implementation story should execute:**

```bash
# Initialize library project with uv
uv init --lib --build-backend hatchling

# Install core dependency
uv add "temporalio>=1.7.1"

# Install development tools
uv add --dev pytest pytest-cov pytest-asyncio mypy ruff

# Verify setup
uv run python -c "import temporalio; print('Temporal SDK ready')"
```

This establishes the base architecture with these decisions:
- **Project Structure:** Modern src/ layout (prevents import issues)
- **Build System:** Hatchling (fast, zero-config, PyPA-maintained)
- **Package Manager:** uv (Rust-based, extremely fast)
- **Type Distribution:** py.typed marker file included

## Decision Summary

| Category | Decision | Version | Affects FR Categories | Rationale |
| -------- | -------- | ------- | --------------------- | --------- |
| **Foundation** |
| Package Manager | uv | latest | All | User requirement. Fast, modern, Rust-based. Handles venv, deps, builds. |
| Build Backend | hatchling | latest | All | Modern, zero-config, PyPA-maintained. Native src/ layout support. |
| Python Version | 3.10+ (3.11+ recommended) | 3.10.0 min | All | NFR-COMPAT-1. AST features stable, dataclass improvements in 3.10+. |
| Project Layout | src/ layout | - | API & Integration | Modern best practice. Prevents accidental imports. Clean separation. |
| **Core Dependencies** |
| Temporal SDK | temporalio | >=1.7.1 | All | Required for workflow type definitions. NFR-COMPAT-2. |
| AST Parser | ast (built-in) | stdlib | Core Graph Generation | Static analysis foundation. No external dependency needed. |
| **Development Tools** |
| Type Checker | mypy | latest strict mode | All | NFR-QUAL-1: 100% public API type coverage. Strict mode enforces quality. |
| Linter | ruff | latest | All | Modern, fast (Rust), replaces flake8/isort. NFR-QUAL-3. |
| Formatter | ruff format | latest | All | Unified with linter. Replaces black. 100-char line length. |
| Test Framework | pytest | >=7.4.0 | All | Industry standard. Clean syntax. Powerful fixtures. |
| Coverage Tool | pytest-cov | >=4.1.0 | All | NFR-QUAL-2: >80% coverage requirement. |
| Async Testing | pytest-asyncio | >=0.21.0 | API & Integration | Support for async workflow helper functions (to_decision, wait_condition). |
| **Architecture Patterns** |
| AST Traversal | Visitor Pattern | - | Core Graph Generation | ast.NodeVisitor for workflow analysis. Clean separation of concerns. |
| Graph Building | Builder Pattern | - | Graph Output | GraphBuildingContext + incremental path construction. |
| Output Rendering | Strategy Pattern | - | Output Format Compliance | Supports multiple output formats (Mermaid now, JSON/DOT future). |
| **Core Modules** |
| Context Management | GraphBuildingContext (dataclass) | - | Configuration & Control | Centralized config. Immutable state. Type-safe options. |
| Path Tracking | GraphPath class | - | Core Graph Generation | Tracks single execution path. Efficient step storage. |
| AST Analysis | WorkflowAnalyzer (ast.NodeVisitor) | - | Core Graph Generation | Visits workflow AST nodes. Detects activities/decisions. |
| Decision Detection | DecisionDetector | - | Decision Node Support | Identifies to_decision() calls, extracts names/branches. |
| Path Generation | PathPermutationGenerator | - | Core Graph Generation | Generates 2^n paths for n decisions. Explosion safeguards. |
| Output Rendering | MermaidRenderer | - | Graph Output, Output Format Compliance | Generates valid Mermaid flowchart syntax. |
| Workflow Helpers | to_decision, wait_condition | - | Decision Node Support, Signal Support | Async functions injected into workflow. Marker for static analysis. |
| **Error Handling** |
| Exception Hierarchy | Custom exceptions | - | Error Handling | TemporalioGraphsError base. Specific subtypes for parse/pattern/generation errors. |
| Error Messages | Actionable with context | - | Error Handling | NFR-USE-2: Include file, line number, suggestions. |
| Logging | Python logging module | - | All | Library best practice: create loggers, don't configure handlers. |
| **Testing Strategy** |
| Unit Tests | Per-module tests | - | All | test_analyzer.py, test_generator.py, etc. Isolate components. |
| Integration Tests | End-to-end workflow analysis | - | Examples & Documentation | Full pipeline: source → AST → paths → Mermaid. |
| Regression Tests | Golden file comparisons | - | Output Format Compliance | Compare output with .NET version. Prevent regressions. |
| Test Organization | Mirror src/ structure | - | All | tests/test_analyzer.py matches src/temporalio_graphs/analyzer.py |

## Project Structure

```
temporalio-graphs/
├── .github/
│   └── workflows/
│       ├── test.yml           # Run tests on push/PR
│       ├── lint.yml           # ruff check + mypy
│       └── publish.yml        # Publish to PyPI on tag
├── .venv/                     # Virtual environment (gitignored)
├── .python-version            # Python version for uv
├── docs/
│   ├── prd.md                 # Product Requirements
│   ├── architecture.md        # This document
│   └── api-reference.md       # Auto-generated API docs
├── examples/
│   ├── money_transfer/
│   │   ├── workflow.py        # MoneyTransfer workflow (from .NET)
│   │   ├── run.py             # Example runner
│   │   └── expected_output.md # Expected Mermaid diagram
│   ├── simple_linear/
│   │   └── workflow.py        # Linear workflow (no decisions)
│   └── multi_decision/
│       └── workflow.py        # Complex branching example
├── src/
│   └── temporalio_graphs/
│       ├── __init__.py        # Public API exports
│       ├── py.typed           # Type distribution marker
│       ├── _version.py        # Version constant
│       ├── context.py         # GraphBuildingContext dataclass
│       ├── path.py            # GraphPath class
│       ├── analyzer.py        # WorkflowAnalyzer (AST visitor)
│       ├── detector.py        # DecisionDetector
│       ├── generator.py       # PathPermutationGenerator
│       ├── renderer.py        # MermaidRenderer
│       ├── helpers.py         # to_decision, wait_condition
│       ├── exceptions.py      # Custom exception hierarchy
│       └── _internal/
│           ├── __init__.py
│           ├── ast_utils.py   # AST helper functions
│           └── graph_models.py # GraphNode, GraphEdge dataclasses
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Pytest fixtures
│   ├── test_context.py
│   ├── test_path.py
│   ├── test_analyzer.py
│   ├── test_detector.py
│   ├── test_generator.py
│   ├── test_renderer.py
│   ├── test_helpers.py
│   ├── test_exceptions.py
│   ├── integration/
│   │   ├── test_money_transfer.py
│   │   ├── test_simple_linear.py
│   │   └── test_multi_decision.py
│   └── fixtures/
│       ├── sample_workflows/  # Test workflow files
│       └── expected_outputs/  # Golden files for regression
├── .gitignore
├── .python-version
├── CHANGELOG.md               # Keep a Changelog format
├── LICENSE                    # MIT License
├── README.md                  # Quick start, examples, badges
├── pyproject.toml             # Project metadata, dependencies, tool config
└── uv.lock                    # Locked dependencies

```

## FR Category to Architecture Mapping

| FR Category | Functional Requirements | Architecture Components | Implementation Notes |
| ----------- | ----------------------- | ----------------------- | -------------------- |
| **Core Graph Generation** | FR1-FR10: Parse workflows, detect activities, generate paths, output Mermaid | analyzer.py (WorkflowAnalyzer), generator.py (PathPermutationGenerator), renderer.py (MermaidRenderer) | AST visitor pattern traverses workflow source. Permutations generated combinatorially. Mermaid syntax built incrementally. |
| **Decision Node Support** | FR11-FR17: Mark decisions, custom names/labels, diamond shapes, 2^n permutations | detector.py (DecisionDetector), helpers.py (to_decision()), generator.py | to_decision() calls detected in AST. Decision ID extracted. Branches labeled yes/no (configurable). |
| **Signal/Wait Condition Support** | FR18-FR22: Mark wait conditions, custom names, hexagon shapes, Signaled/Timeout outcomes | detector.py, helpers.py (wait_condition()), generator.py | wait_condition() detected similarly to decisions. Integrated into path permutation logic. |
| **Graph Output** | FR23-FR30: Mermaid markdown, path list, validation warnings, configurable output | renderer.py (MermaidRenderer), generator.py, context.py (output options) | Mermaid in fenced code blocks. Path list as text. Warnings for unreachable activities. |
| **Configuration & Control** | FR31-FR36: GraphBuildingContext, validation toggle, node labels, name splitting | context.py (GraphBuildingContext dataclass) | All options centralized in context. Immutable configuration pattern. |
| **API & Integration** | FR37-FR44: Public API, type hints, docstrings, async support, clear exceptions | __init__.py (API exports), all modules (type hints), exceptions.py | Clean public API. Full typing for IDE support. Google-style docstrings. |
| **Advanced Patterns** | FR45-FR50: if/else, elif, ternary, sequential, parallel, linear flows | detector.py (pattern detection), generator.py (path generation) | AST patterns: If, IfExp nodes. Control flow analysis for sequencing. Parallelism linearized for MVP. |
| **Output Format Compliance** | FR51-FR55: Valid Mermaid, match .NET structure, naming conventions | renderer.py (syntax generation) | Mermaid validation via rendering tests. .NET comparison in regression tests. |
| **Examples & Documentation** | FR56-FR60: MoneyTransfer example, simple/multi-decision examples, README | examples/ directory, README.md, docstrings | Port .NET MoneyTransfer workflow. Include progressive examples. |
| **Error Handling** | FR61-FR65: Clear errors, pattern warnings, suggestions, validation | exceptions.py, analyzer.py (error detection), detector.py (warnings) | Exception hierarchy with context. Actionable error messages. Validation mode for dry-run. |

## Technology Stack Details

### Core Technologies

**Language & Runtime:**
- Python 3.10.0+ (required minimum)
- Python 3.11+ recommended (improved performance, better error messages)
- Type hints using PEP 484/585/604 syntax
- Dataclasses for immutable configuration (PEP 557)

**Package Management:**
- uv for dependency management, virtual environments, builds
- pyproject.toml (PEP 621) for project metadata
- hatchling build backend for wheel/sdist generation

**Core Library:**
- temporalio SDK >=1.7.1 (workflow type definitions, decorators)
- Python ast module (built-in, no version constraint)
- Python logging module (built-in)
- Python pathlib for cross-platform paths

**Development Tools:**
- pytest >=7.4.0 (test framework)
- pytest-cov >=4.1.0 (coverage measurement, 80% minimum)
- pytest-asyncio >=0.21.0 (async test support)
- mypy latest (strict mode type checking)
- ruff latest (linting + formatting, replaces black/flake8/isort)

**Documentation:**
- Markdown for README, CHANGELOG, examples
- Google-style docstrings for API reference
- Type hints as inline documentation

**Distribution:**
- PyPI registry (package name: temporalio-graphs)
- Wheel (.whl) + source distribution (.tar.gz)
- Semantic versioning (0.1.0 for MVP, 1.0.0 stable)

### Integration Points

**Input Integration:**
- Reads Python source files (.py) from filesystem
- Uses pathlib for path resolution (cross-platform)
- AST parsing via ast.parse() (no execution)

**Output Integration:**
- Returns string (Mermaid markdown) from analyze_workflow()
- Optional file output via context.graph_output_file
- Stdout for CLI usage (future)

**Temporal SDK Integration:**
- Imports workflow decorators for type validation
- Does NOT execute workflows (static analysis only)
- Compatible with Temporal SDK 1.7.1+ (decorator API stable)

**IDE Integration:**
- Type hints enable autocomplete (VS Code, PyCharm)
- py.typed marker enables type checking in consumer projects
- No IDE-specific dependencies

**CI/CD Integration:**
- pytest for automated testing
- mypy for type checking in CI
- ruff for linting in CI
- GitHub Actions workflows (test, lint, publish)

## Implementation Patterns

These patterns ensure consistent implementation across all AI agents:

### NAMING PATTERNS

**Python Conventions (PEP 8):**
- **Classes:** PascalCase
  - `GraphBuildingContext`, `WorkflowAnalyzer`, `MermaidRenderer`
- **Functions/Methods:** snake_case
  - `analyze_workflow()`, `generate_mermaid()`, `to_decision()`
- **Private Methods:** _leading_underscore
  - `_visit_if_node()`, `_extract_activity_name()`, `_build_mermaid_node()`
- **Constants:** UPPER_SNAKE_CASE
  - `MAX_DECISION_POINTS = 10`, `DEFAULT_LINE_LENGTH = 100`
- **Module Files:** snake_case
  - `context.py`, `analyzer.py`, `graph_models.py`
- **Test Files:** test_*.py
  - `test_analyzer.py`, `test_generator.py`

**Workflow-Specific Naming:**
- Decision node names: User-provided string in to_decision(result, "name")
- Activity names: Extracted from workflow code (split camelCase → "Camel Case" if configured)
- Graph node IDs: Deterministic generation (hash-based or sequential)

**Example Enforcement:**
```python
# CORRECT
class WorkflowAnalyzer(ast.NodeVisitor):
    def __init__(self, context: GraphBuildingContext):
        self._decision_count = 0

    def _visit_call_node(self, node: ast.Call) -> None:
        ...

# INCORRECT
class workflowAnalyzer(ast.NodeVisitor):  # Wrong case
    def __init__(self, context: GraphBuildingContext):
        self.decisionCount = 0  # Wrong convention

    def visitCallNode(self, node: ast.Call) -> None:  # Wrong convention
        ...
```

### STRUCTURE PATTERNS

**Module Organization:**
- One primary class per file (exception: small related dataclasses)
- Public API exported from `__init__.py` only
- Internal utilities in `_internal/` subpackage (not part of public API)
- Test files mirror source structure (src/analyzer.py → tests/test_analyzer.py)

**Import Organization (enforced by ruff):**
```python
# 1. Standard library imports
import ast
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# 2. Third-party imports
from temporalio import workflow

# 3. Local application imports
from temporalio_graphs.context import GraphBuildingContext
from temporalio_graphs.exceptions import WorkflowParseError
```

**Test Organization:**
```
tests/
├── test_context.py        # Unit: GraphBuildingContext
├── test_analyzer.py       # Unit: WorkflowAnalyzer
├── integration/
│   └── test_money_transfer.py  # Integration: full workflow
└── fixtures/
    └── sample_workflows/        # Test data
```

**File Structure Standard:**
```python
"""Module-level docstring explaining purpose."""

import ...

logger = logging.getLogger(__name__)

# Type aliases (if any)
ActivityName = str

# Constants
MAX_DECISIONS = 10

# Classes
class MyClass:
    """Class docstring."""
    ...

# Public functions
def public_function():
    """Function docstring."""
    ...

# Private/internal functions
def _internal_helper():
    ...
```

### FORMAT PATTERNS

**Type Hints (PEP 484/585):**
```python
# All public functions MUST have full type hints
def analyze_workflow(
    workflow_file: Path | str,  # Union with | (Python 3.10+)
    context: Optional[GraphBuildingContext] = None,
    output_format: Literal["mermaid", "json", "paths"] = "mermaid"
) -> str:
    """Full docstring with Args/Returns."""
    ...

# Return types always specified (no implicit None)
def _internal_helper() -> None:
    ...

# Generics use built-in types (Python 3.9+)
def get_paths(self) -> list[GraphPath]:  # Not List[GraphPath]
    ...
```

**Docstring Format (Google Style):**
```python
def to_decision(result: bool, name: str) -> bool:
    """Mark a boolean expression as a decision node in the workflow graph.

    This helper function allows static analysis to identify decision points
    during AST traversal. The function is transparent—it returns the input
    boolean unchanged.

    Args:
        result: The boolean value to evaluate (e.g., `amount > 1000`)
        name: Human-readable decision name for graph display (e.g., "NeedToConvert")

    Returns:
        The original boolean value (passthrough for workflow logic)

    Example:
        >>> if await to_decision(amount > 1000, "HighValue"):
        >>>     await workflow.execute_activity(special_processing)

    Note:
        This function must be called with `await` in async workflows.
    """
    return result
```

**Error Message Format:**
```python
# Actionable errors with context
raise WorkflowParseError(
    f"Cannot parse workflow file: {workflow_file}\n"
    f"Line {node.lineno}: Unexpected AST node type '{type(node).__name__}'\n"
    f"Suggestion: Ensure workflow uses @workflow.defn decorator"
)

# Validation warnings with details
logger.warning(
    f"Unreachable activity detected: '{activity_name}' at line {lineno}\n"
    f"This activity is defined but never called in any execution path.\n"
    f"Consider removing or checking workflow logic."
)
```

**Code Formatting (ruff):**
- Line length: 100 characters (modern display standard)
- String quotes: Double quotes preferred (configurable)
- Trailing commas: Required in multi-line collections
- Blank lines: 2 before top-level classes/functions, 1 before methods

### COMMUNICATION PATTERNS

**AST Visitor Pattern:**
```python
# All AST visitors follow this pattern
class WorkflowAnalyzer(ast.NodeVisitor):
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        # Check for @workflow.defn decorator
        ...
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        # Check for @workflow.run decorator
        ...
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # Check for execute_activity, to_decision, wait_condition
        ...
        self.generic_visit(node)
```

**Builder Pattern (Graph Construction):**
```python
# Incremental graph building
context = GraphBuildingContext(split_names_by_words=True)
path = GraphPath()
path.add_activity("Withdraw")
path.add_decision("need_convert", True, "NeedToConvert")
path.add_activity("CurrencyConvert")
```

**Strategy Pattern (Output Rendering):**
```python
# Current: Direct rendering
renderer = MermaidRenderer(context)
output = renderer.render(paths)

# Future: Strategy-based
renderer = get_renderer("mermaid", context)  # or "json", "dot"
output = renderer.render(paths)
```

### LIFECYCLE PATTERNS

**Graph Generation Flow:**
1. **Input Validation:** Check file exists, readable, is Python file
2. **AST Parsing:** Parse source with ast.parse(), catch syntax errors
3. **Workflow Detection:** Find @workflow.defn class, @workflow.run method
4. **Activity/Decision Detection:** Traverse AST, collect activities and decisions
5. **Path Permutation:** Generate 2^n paths for n decisions (with explosion check)
6. **Graph Construction:** Build node/edge graph from paths
7. **Validation:** Check for unreachable activities, unused decisions
8. **Output Rendering:** Generate Mermaid syntax from graph
9. **Result Return:** Return string or write to file

**Error Recovery:**
- **Parse Error:** Raise WorkflowParseError, suggest syntax check
- **No Workflow Found:** Raise WorkflowParseError, suggest decorator check
- **Too Many Decisions:** Raise GraphGenerationError, suggest refactoring
- **Unsupported Pattern:** Raise UnsupportedPatternError (e.g., loops) or log warning (e.g., dynamic names)
- **Render Error:** Raise GraphGenerationError with node details

### LOCATION PATTERNS

**Source Code Organization:**
- Core logic: `src/temporalio_graphs/`
- Public API: `src/temporalio_graphs/__init__.py`
- Internal utilities: `src/temporalio_graphs/_internal/`
- Tests: `tests/` (mirror src structure)
- Examples: `examples/` (runnable workflow samples)
- Documentation: `docs/` (architecture, API reference)
- Build artifacts: `dist/` (gitignored)

**Test Fixture Locations:**
- Sample workflows: `tests/fixtures/sample_workflows/`
- Expected outputs: `tests/fixtures/expected_outputs/`
- Golden files: `tests/fixtures/golden/` (regression baselines)

**Configuration File Locations:**
- Project config: `pyproject.toml` (root)
- Python version: `.python-version` (root)
- Gitignore: `.gitignore` (root)
- CI workflows: `.github/workflows/`

### CONSISTENCY RULES

**Node ID Generation:**
- Start node: Always `"s"` (lowercase s)
- End node: Always `"e"` (lowercase e)
- Activity nodes: Sequential integers `"1"`, `"2"`, `"3"`
- Decision nodes: Hash of decision name + position (deterministic)
- Signal nodes: Hash of signal name + position (deterministic)

**Mermaid Syntax Conventions:**
- Start/End: `s((Start))`, `e((End))`
- Activity: `1[ActivityName]`
- Decision: `0{DecisionName}`
- Signal: `2{{SignalName}}`
- Edge labels: `-- yes -->`, `-- no -->`, `-- Signaled -->`, `-- Timeout -->`

**Path Ordering:**
- Depth-first traversal for path generation
- Deterministic ordering (same workflow → same path order)
- Path IDs: Sequential `"path_0"`, `"path_1"`, etc.

**Logging Levels:**
- DEBUG: AST node visits, path generation steps
- INFO: Analysis start/complete, file loaded
- WARNING: Validation warnings (unreachable activities)
- ERROR: Analysis failures, unsupported patterns
- CRITICAL: Not used (library doesn't have critical failures)

## Data Architecture

### Core Data Models

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Literal
from enum import Enum

@dataclass(frozen=True)
class GraphBuildingContext:
    """Configuration for graph generation (immutable)."""
    is_building_graph: bool = True
    exit_after_building_graph: bool = False
    graph_output_file: Optional[Path] = None
    split_names_by_words: bool = True
    suppress_validation: bool = False
    start_node_label: str = "Start"
    end_node_label: str = "End"
    max_decision_points: int = 10
    max_paths: int = 1024  # Safety limit (2^10)
    decision_true_label: str = "yes"
    decision_false_label: str = "no"
    signal_success_label: str = "Signaled"
    signal_timeout_label: str = "Timeout"

class NodeType(Enum):
    """Graph node types."""
    START = "start"
    END = "end"
    ACTIVITY = "activity"
    DECISION = "decision"
    SIGNAL = "signal"

@dataclass
class GraphNode:
    """Represents a node in the workflow graph."""
    node_id: str
    node_type: NodeType
    display_name: str
    source_line: Optional[int] = None  # For error reporting

    def to_mermaid(self) -> str:
        """Convert node to Mermaid syntax."""
        if self.node_type == NodeType.START:
            return f"{self.node_id}(({self.display_name}))"
        elif self.node_type == NodeType.END:
            return f"{self.node_id}(({self.display_name}))"
        elif self.node_type == NodeType.ACTIVITY:
            return f"{self.node_id}[{self.display_name}]"
        elif self.node_type == NodeType.DECISION:
            return f"{self.node_id}{{{self.display_name}}}"
        elif self.node_type == NodeType.SIGNAL:
            return f"{self.node_id}{{{{{self.display_name}}}}}"

@dataclass
class GraphEdge:
    """Represents an edge between nodes."""
    from_node: str
    to_node: str
    label: Optional[str] = None

    def to_mermaid(self) -> str:
        """Convert edge to Mermaid syntax."""
        if self.label:
            return f"{self.from_node} -- {self.label} --> {self.to_node}"
        return f"{self.from_node} --> {self.to_node}"

@dataclass
class GraphPath:
    """Tracks a single execution path through the workflow."""
    path_id: str
    steps: list[str] = field(default_factory=list)
    decisions: dict[str, bool] = field(default_factory=dict)

    def add_activity(self, name: str) -> str:
        """Add activity to path, return node ID."""
        node_id = str(len(self.steps))
        self.steps.append(name)
        return node_id

    def add_decision(self, id: str, value: bool, name: str) -> str:
        """Add decision to path, return node ID."""
        self.decisions[id] = value
        self.steps.append(f"Decision:{name}={value}")
        return id

    def add_signal(self, name: str, outcome: str) -> str:
        """Add signal to path, return node ID."""
        node_id = str(len(self.steps))
        self.steps.append(f"Signal:{name}={outcome}")
        return node_id

@dataclass
class WorkflowMetadata:
    """Metadata extracted from workflow AST."""
    workflow_class: str
    workflow_run_method: str
    activities: list[str]
    decision_points: list[str]
    signal_points: list[str]
    source_file: Path
    total_paths: int  # 2^n for n decisions
```

### Data Flow

```
1. Input:
   workflow.py (Python source file)
   ↓

2. AST Parsing:
   ast.parse(source) → ast.Module
   ↓

3. Analysis (WorkflowAnalyzer):
   ast.Module → WorkflowMetadata
   (Extract: activities, decisions, signals)
   ↓

4. Path Generation (PathPermutationGenerator):
   WorkflowMetadata → list[GraphPath]
   (Generate: 2^n permutations)
   ↓

5. Graph Construction:
   list[GraphPath] → (nodes: list[GraphNode], edges: list[GraphEdge])
   ↓

6. Rendering (MermaidRenderer):
   (nodes, edges) → str (Mermaid syntax)
   ↓

7. Output:
   "```mermaid\nflowchart LR\n...\n```"
```

### Data Relationships

```
WorkflowMetadata (1) ──< (n) DecisionPoint
                 (1) ──< (n) ActivityCall
                 (1) ──< (n) SignalPoint

GraphPath (1) ──< (n) GraphStep
          (1) ──< (n) DecisionValue

GraphNode (1) ──< (n) GraphEdge (from_node)
          (1) ──< (n) GraphEdge (to_node)

MermaidDiagram (1) ──< (n) GraphNode
               (1) ──< (n) GraphEdge
```

### Persistence

**No Database:** This is a stateless analysis library. No persistent storage beyond:
- Optional output file (via context.graph_output_file)
- Temporary in-memory structures during analysis

**No State Management:** Each analysis is independent. No caching between calls (future optimization opportunity).

## API Contracts

### Primary Entry Point

```python
def analyze_workflow(
    workflow_file: Path | str,
    context: Optional[GraphBuildingContext] = None,
    output_format: Literal["mermaid", "json", "paths"] = "mermaid"
) -> str:
    """Analyze workflow source file and return graph representation.

    Args:
        workflow_file: Path to Python workflow source file
        context: Optional configuration (uses defaults if None)
        output_format: Output format - "mermaid" (default), "json", or "paths"

    Returns:
        Graph representation as string in requested format

    Raises:
        WorkflowParseError: If workflow file cannot be parsed
        UnsupportedPatternError: If workflow uses unsupported patterns
        GraphGenerationError: If graph cannot be generated

    Example:
        >>> from temporalio_graphs import analyze_workflow
        >>> result = analyze_workflow("my_workflow.py")
        >>> print(result)  # Mermaid diagram
    """
```



### Workflow Helper Functions

```python
def to_decision(result: bool, name: str) -> bool:
    """Mark boolean expression as decision node.

    This is a marker function for static analysis. At runtime, it simply
    returns the input boolean unchanged. During static analysis, it marks
    the boolean as a decision point in the workflow graph.

    Args:
        result: Boolean expression result
        name: Display name for decision node (e.g., "NeedToConvert")

    Returns:
        The input boolean value (transparent passthrough)

    Example:
        >>> if to_decision(amount > 1000, "HighValue"):
        >>>     await workflow.execute_activity(special_handling)
    """
    return result

async def wait_condition(
    condition_check: Callable[[], bool],
    timeout: timedelta,
    name: str
) -> bool:
    """Mark wait condition as signal node.

    This wraps workflow.wait_condition() to mark it as a signal node in
    the graph. Static analysis detects this call and creates a signal node
    with two outcomes: "Signaled" and "Timeout".

    Args:
        condition_check: Callable that checks condition
        timeout: Maximum time to wait
        name: Display name for signal node (e.g., "WaitForApproval")

    Returns:
        True if condition met before timeout, False otherwise

    Example:
        >>> approved = await wait_condition(
        >>>     lambda: workflow.is_approved,
        >>>     timedelta(hours=24),
        >>>     "WaitForApproval"
        >>> )
    """
    return await workflow.wait_condition(condition_check, timeout)
```

### Exception Hierarchy

```python
class TemporalioGraphsError(Exception):
    """Base exception for all library errors."""
    pass

class WorkflowParseError(TemporalioGraphsError):
    """Raised when workflow file cannot be parsed."""
    pass

class UnsupportedPatternError(TemporalioGraphsError):
    """Raised when workflow uses unsupported patterns."""
    def __init__(self, pattern: str, suggestion: str):
        super().__init__(
            f"Unsupported pattern: {pattern}\n"
            f"Suggestion: {suggestion}"
        )

class GraphGenerationError(TemporalioGraphsError):
    """Raised when graph cannot be generated."""
    pass

class InvalidDecisionError(TemporalioGraphsError):
    """Raised when to_decision() is used incorrectly."""
    pass
```

## Security Architecture

### Input Validation

**File Path Validation:**
```python
def _validate_workflow_file(workflow_file: Path | str) -> Path:
    """Validate and resolve workflow file path."""
    path = Path(workflow_file).resolve()  # Resolve symlinks, prevent traversal

    if not path.exists():
        raise WorkflowParseError(f"Workflow file not found: {path}")

    if not path.is_file():
        raise WorkflowParseError(f"Path is not a file: {path}")

    if path.suffix != ".py":
        logger.warning(f"File does not have .py extension: {path}")

    # Check readability
    try:
        path.read_text()
    except PermissionError:
        raise WorkflowParseError(f"Cannot read file (permission denied): {path}")

    return path
```

**AST Safety:**
- Python's `ast.parse()` is safe - it parses source into AST without executing
- No use of `eval()`, `exec()`, `compile()` with mode='exec'
- No dynamic code execution whatsoever

### No Code Execution

**Critical Security Property:**
This library performs STATIC ANALYSIS ONLY. Workflow code is never executed.

```python
# SAFE: Parse workflow into AST
tree = ast.parse(source_code)

# NEVER DONE: Execute workflow code
# exec(source_code)  # ❌ FORBIDDEN
# eval(expression)   # ❌ FORBIDDEN
```

### Dependency Security

**Minimal Attack Surface:**
- Only required dependency: `temporalio` SDK (official Temporal client)
- No transitive dependencies beyond Temporal's own deps
- Development dependencies isolated (not installed in production)

**Dependency Auditing:**
```bash
# Regular security scans in CI
uv pip check
pip-audit  # Future: automated vulnerability scanning
```

### Path Traversal Prevention

**Safe Path Handling:**
```python
# Use pathlib.resolve() to prevent directory traversal
safe_path = Path(user_input).resolve()

# Ensure path is within expected directories (if applicable)
if not safe_path.is_relative_to(project_root):
    raise SecurityError("Path outside project scope")
```

### No Network Access

**Completely Offline:**
- No network calls
- No HTTP requests
- No external API access
- Pure local file analysis

### Threat Model Summary

| Threat | Mitigation | Risk Level |
| ------ | ---------- | ---------- |
| Malicious workflow code execution | Static analysis only (no exec/eval) | ✅ Eliminated |
| Path traversal attacks | Path.resolve() + validation | ✅ Mitigated |
| Dependency vulnerabilities | Minimal dependencies + auditing | 🟡 Low |
| Denial of Service (path explosion) | max_decision_points limit (10 default) | ✅ Mitigated |
| Information disclosure | No external communication | ✅ Eliminated |
| Code injection | No dynamic code execution | ✅ Eliminated |

## Performance Considerations

### Performance Targets (from NFR-PERF-1)

- **Simple workflows:** <0.001s (1ms)
- **5 decision points (32 paths):** <1 second
- **10 decision points (1024 paths):** <5 seconds
- **Memory usage:** <100MB for typical workflows

### Optimization Strategies

**1. AST Parsing (Already Fast):**
- Python's `ast.parse()` is C-implemented
- Typical workflow file (<500 lines): <1ms parse time
- No optimization needed

**2. Path Explosion Management:**
```python
class PathPermutationGenerator:
    def generate_paths(
        self,
        decisions: list[DecisionPoint],
        context: GraphBuildingContext
    ) -> list[GraphPath]:
        """Generate all path permutations with explosion safeguards."""
        num_decisions = len(decisions)

        # Early exit for linear workflows
        if num_decisions == 0:
            return [self._create_linear_path()]

        # Check explosion limit BEFORE generation
        total_paths = 2 ** num_decisions
        if total_paths > context.max_paths:
            raise GraphGenerationError(
                f"Too many decision points ({num_decisions}) would generate "
                f"{total_paths} paths (limit: {context.max_paths})\n"
                f"Suggestion: Refactor workflow or increase max_paths limit"
            )

        # Generate paths using itertools.product (efficient)
        from itertools import product
        return [
            self._build_path(decisions, choices)
            for choices in product([True, False], repeat=num_decisions)
        ]
```

**3. Efficient Data Structures:**
```python
# Use __slots__ for frequently-created objects (memory savings)
@dataclass(slots=True)
class GraphNode:
    node_id: str
    node_type: NodeType
    display_name: str

# Use sets for deduplication (O(1) lookup)
seen_edges = set()  # set[(from, to)]
for edge in edges:
    key = (edge.from_node, edge.to_node)
    if key not in seen_edges:
        seen_edges.add(key)
        mermaid_edges.append(edge.to_mermaid())
```

**4. Mermaid Generation Optimization:**
```python
from io import StringIO

def _build_mermaid(nodes: list[GraphNode], edges: list[GraphEdge]) -> str:
    """Build Mermaid diagram efficiently using StringIO."""
    output = StringIO()

    output.write("```mermaid\nflowchart LR\n")

    # Write nodes (deduplicated)
    seen_nodes = set()
    for node in nodes:
        if node.node_id not in seen_nodes:
            output.write(f"{node.to_mermaid()}\n")
            seen_nodes.add(node.node_id)

    # Write edges (deduplicated)
    seen_edges = set()
    for edge in edges:
        key = (edge.from_node, edge.to_node, edge.label)
        if key not in seen_edges:
            output.write(f"{edge.to_mermaid()}\n")
            seen_edges.add(key)

    output.write("```\n")
    return output.getvalue()
```

**5. Lazy Evaluation (Future Optimization):**
```python
# Current: Generate all paths upfront
paths = generator.generate_all_paths()

# Future: Use generators for memory efficiency
def generate_paths_lazy(self) -> Iterator[GraphPath]:
    """Yield paths one at a time (memory efficient)."""
    for choices in product([True, False], repeat=num_decisions):
        yield self._build_path(decisions, choices)

# Allows processing paths without storing all in memory
for path in generator.generate_paths_lazy():
    process_path(path)
```

**6. Caching (Future Optimization):**
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def _split_camel_case(name: str) -> str:
    """Cache name splitting results (frequent operation)."""
    return re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
```

### Performance Monitoring

**Built-in Timing (Development Mode):**
```python
import time
import logging

logger = logging.getLogger(__name__)

def analyze_workflow(workflow_file: Path, context: GraphBuildingContext) -> str:
    """Analyze workflow with performance logging."""
    start = time.perf_counter()

    # Analysis steps...
    parse_time = time.perf_counter() - start
    logger.debug(f"AST parsing: {parse_time*1000:.2f}ms")

    # Path generation...
    gen_time = time.perf_counter() - parse_time
    logger.debug(f"Path generation: {gen_time*1000:.2f}ms")

    total_time = time.perf_counter() - start
    logger.info(f"Total analysis: {total_time*1000:.2f}ms")
```

## Deployment Architecture

### Package Distribution

**PyPI Distribution:**
```bash
# Build package
uv build  # Creates dist/temporalio_graphs-0.1.0.tar.gz and .whl

# Publish to PyPI (automated via GitHub Actions on tag)
uv publish
```

**GitHub Actions Workflow:**
```yaml
# .github/workflows/publish.yml
name: Publish to PyPI
on:
  push:
    tags:
      - 'v*'
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - run: uv build
      - run: uv publish
        env:
          UV_PUBLISH_TOKEN: ${{ secrets.PYPI_API_TOKEN }}
```

**Version Management:**
```python
# src/temporalio_graphs/_version.py
__version__ = "0.1.0"

# pyproject.toml
[project]
version = "0.1.0"  # Single source of truth
```

### Installation

**End Users:**
```bash
# Using pip
pip install temporalio-graphs

# Using uv (recommended)
uv add temporalio-graphs

# Using poetry
poetry add temporalio-graphs
```

**Development Setup:**
```bash
# Clone repository
git clone https://github.com/yourusername/temporalio-graphs.git
cd temporalio-graphs

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
uv sync

# Install in editable mode for development
uv pip install -e .

# Run tests
pytest

# Run type checking
mypy src/

# Run linting
ruff check src/
```

### Platform Support

**Pure Python (No Compilation Needed):**
- Works on Linux, macOS, Windows
- No C extensions, no platform-specific code
- pathlib ensures cross-platform path handling

**Python Version Compatibility:**
- Minimum: Python 3.10.0
- Tested: Python 3.10, 3.11, 3.12
- CI Matrix: Test on all supported versions

**Wheel Distribution:**
- Universal wheel (py3-none-any.whl)
- Fast installation (no build step)
- Compatible with all platforms

## Development Environment

### Prerequisites

- **Python 3.10+** (3.11+ recommended)
  - Check: `python --version`
  - Install: [python.org](https://www.python.org) or via pyenv/asdf

- **uv package manager**
  - Install: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - Verify: `uv --version`

- **Git**
  - Check: `git --version`
  - Install: [git-scm.com](https://git-scm.com)

### Setup Commands

```bash
# 1. Initialize project (if starting fresh)
uv init --lib --build-backend hatchling
cd temporalio-graphs

# 2. Create virtual environment
uv venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 3. Install dependencies
uv add "temporalio>=1.7.1"

# 4. Install development tools
uv add --dev \
    pytest \
    pytest-cov \
    pytest-asyncio \
    mypy \
    ruff

# 5. Verify installation
uv run python -c "import temporalio; print('Temporal SDK:', temporalio.__version__)"

# 6. Run tests to verify setup
uv run pytest

# 7. Run type checking
uv run mypy src/

# 8. Run linting
uv run ruff check src/
```

### Development Workflow

```bash
# Make code changes...

# Run tests (fast feedback)
pytest -v

# Run tests with coverage
pytest --cov=src/temporalio_graphs --cov-report=term-missing

# Type check
mypy src/

# Lint and format
ruff check src/
ruff format src/

# Run all checks (pre-commit)
pytest && mypy src/ && ruff check src/

# Build package locally
uv build

# Install local build for testing
uv pip install dist/temporalio_graphs-0.1.0-py3-none-any.whl
```

### IDE Setup

**VS Code (.vscode/settings.json):**
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "python.analysis.typeCheckingMode": "strict",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  },
  "mypy.runUsingActiveInterpreter": true
}
```

**PyCharm:**
- Set Python interpreter to `.venv/bin/python`
- Enable pytest as test runner
- Configure mypy as external tool
- Install Ruff plugin for formatting

### Environment Variables

None required for development. All configuration in pyproject.toml.

## Architecture Decision Records (ADRs)

### ADR-001: Static Analysis vs Runtime Interceptors

**Context:**
The .NET Temporalio.Graphs uses runtime interceptors to track workflow execution and generate graphs. Python's Temporal SDK has more limited interceptor capabilities - specifically, interceptors cannot mock activity return values to force different execution paths.

**Decision:**
Use static code analysis (Python AST) instead of runtime interceptors.

**Rationale:**
1. **Spike Validation:** Phase 0.5 spike tested 3 approaches. Static analysis (approach 3) was fastest (<1ms) and most reliable.
2. **Python SDK Limitations:** Cannot mock activity returns via interceptors (unlike .NET).
3. **Performance:** No workflow execution needed. Analysis is instant vs exponential execution time for 2^n paths.
4. **Correctness:** Generates ALL possible paths without needing to execute each one.
5. **Simplicity:** Fewer dependencies. No complex mocking infrastructure.

**Consequences:**
- ✅ Extremely fast analysis (<1ms for simple workflows)
- ✅ No workflow execution required
- ✅ Generates complete path coverage
- ⚠️ Requires users to mark decisions explicitly with to_decision()
- ⚠️ Cannot detect runtime-only patterns (dynamic activity names, reflection)

**Status:** Accepted ✅

---

### ADR-002: uv as Package Manager

**Context:**
Python has multiple package managers: pip, poetry, PDM, pipenv, uv. Need to choose one for development and documentation.

**Decision:**
Use uv as the primary package manager.

**Rationale:**
1. **User Requirement:** Global CLAUDE.md specifies "always ALWAYS use uv"
2. **Performance:** uv is written in Rust, extremely fast (10-100x faster than pip)
3. **Modern:** Released in 2024 by Astral (makers of ruff), follows best practices
4. **All-in-One:** Handles venv, dependencies, builds, publishing
5. **uv.lock:** Deterministic dependency resolution (similar to poetry.lock)

**Consequences:**
- ✅ Consistent with user environment
- ✅ Fast dependency resolution and installation
- ✅ Modern tooling, actively maintained
- ⚠️ Newer tool (less mature than pip/poetry)
- ⚠️ Documentation examples use uv (may confuse users expecting pip)

**Status:** Accepted ✅

---

### ADR-003: Hatchling as Build Backend

**Context:**
Modern Python projects use pyproject.toml with a build backend. Options: setuptools, hatchling, PDM-backend, flit-core, maturin.

**Decision:**
Use hatchling as the build backend.

**Rationale:**
1. **Zero Configuration:** Works out-of-box with src/ layout, no extra setup
2. **PyPA Maintained:** Built by Python Packaging Authority, follows standards
3. **Modern:** Designed for pyproject.toml-only builds (no setup.py)
4. **Fast:** Efficient builds, good uv compatibility
5. **No Legacy Baggage:** Unlike setuptools, clean modern design

**Consequences:**
- ✅ Simple pyproject.toml configuration
- ✅ Native src/ layout support
- ✅ Fast builds
- ✅ Official PyPA tool (trustworthy, maintained)
- ⚠️ Less widely used than setuptools (but growing adoption)

**Status:** Accepted ✅

---

### ADR-004: src/ Layout for Package Structure

**Context:**
Python packages can use flat layout (package/ at root) or src layout (src/package/).

**Decision:**
Use src/ layout: `src/temporalio_graphs/`

**Rationale:**
1. **Modern Best Practice:** Recommended by Python Packaging User Guide
2. **Prevents Import Issues:** Can't accidentally import from local files during development
3. **Test Isolation:** Forces tests to import installed package, not local files
4. **Build Clarity:** Clear separation between source and build artifacts
5. **Tool Support:** Hatchling, uv, pytest all support src/ layout natively

**Consequences:**
- ✅ Prevents common import bugs
- ✅ Better test reliability
- ✅ Industry best practice
- ⚠️ Slightly more complex project structure (extra src/ directory)

**Status:** Accepted ✅

---

### ADR-005: Explicit Decision Marking with to_decision()

**Context:**
How should the library identify decision points in workflows? Options:
1. Automatically detect all if/else statements
2. Require explicit marking with to_decision()
3. Hybrid: auto-detect with opt-in for custom names

**Decision:**
Require explicit marking with `to_decision(condition, "name")` helper function.

**Rationale:**
1. **Signal vs Noise:** Not all if statements are workflow decisions (internal logic, validation)
2. **Named Nodes:** Users provide meaningful names for graph display
3. **Intentional:** Makes decision points explicit, self-documenting
4. **Matches .NET:** Conceptually similar to .NET's runtime tracking
5. **Control:** Users control what appears in graph

**Consequences:**
- ✅ Clean, meaningful graphs (no noise from internal logic)
- ✅ User-controlled decision names
- ✅ Self-documenting workflow code
- ⚠️ Requires workflow code modification (adds to_decision calls)
- ⚠️ Manual effort (can't auto-generate from existing workflows)

**Status:** Accepted ✅

---

### ADR-006: mypy Strict Mode for Type Safety

**Context:**
Type checking can be optional, basic, or strict. NFR-QUAL-1 requires 100% type hint coverage for public APIs.

**Decision:**
Use mypy in strict mode for all source code.

**Rationale:**
1. **NFR Requirement:** NFR-QUAL-1 mandates complete type safety
2. **API Quality:** Strict typing enables excellent IDE autocomplete
3. **Error Prevention:** Catch type errors before runtime
4. **Documentation:** Type hints serve as inline API documentation
5. **Library Best Practice:** Libraries should have stricter typing than applications

**Consequences:**
- ✅ Excellent IDE support (autocomplete, hints)
- ✅ Fewer runtime type errors
- ✅ Self-documenting API
- ⚠️ More upfront effort (adding type hints)
- ⚠️ Stricter than typical Python projects

**Status:** Accepted ✅

---

### ADR-007: Ruff for Linting and Formatting

**Context:**
Python linting typically uses flake8, pylint, or ruff. Formatting uses black or ruff format.

**Decision:**
Use ruff for both linting and formatting.

**Rationale:**
1. **Unified Tool:** Single tool replaces flake8, isort, black
2. **Performance:** Written in Rust, extremely fast
3. **Modern:** Released 2023, rapidly adopted by major projects
4. **Astral Ecosystem:** Same team as uv (consistent tooling)
5. **PRD Mention:** PRD specifically mentions ruff

**Consequences:**
- ✅ Fast linting and formatting
- ✅ Single tool for multiple tasks
- ✅ Modern, actively developed
- ✅ Growing industry adoption
- ⚠️ Newer tool (less mature than black/flake8)

**Status:** Accepted ✅

---

### ADR-008: Path Explosion Limit (max_decision_points = 10)

**Context:**
Workflows with n decision points generate 2^n paths. This grows exponentially: 10 decisions = 1024 paths, 20 decisions = 1,048,576 paths. Need safeguards against path explosion.

**Decision:**
Set default `max_decision_points = 10` (1024 paths max), configurable via GraphBuildingContext.

**Rationale:**
1. **Performance:** NFR-PERF-1 targets <5s for 10 decisions (1024 paths)
2. **Memory:** Prevent out-of-memory errors on complex workflows
3. **Usability:** Most workflows have <10 decisions. Beyond that, graph becomes unreadable anyway.
4. **Configurable:** Advanced users can increase limit if needed
5. **Fail Fast:** Better to error early than freeze/crash

**Consequences:**
- ✅ Prevents path explosion DoS
- ✅ Keeps analysis fast
- ✅ Encourages workflow refactoring (>10 decisions = too complex)
- ⚠️ May block analysis of very complex workflows
- ✅ Configurable override available

**Status:** Accepted ✅

---

### ADR-009: Google-Style Docstrings

**Context:**
Python supports multiple docstring formats: Google, NumPy, reStructuredText. PRD mentions "Google/NumPy style."

**Decision:**
Use Google-style docstrings for all public APIs.

**Rationale:**
1. **Readability:** Google style is clean, easy to read in code
2. **Tool Support:** Sphinx, mkdocs, pydoc all support Google style
3. **Consistency:** Pick one style and use everywhere
4. **PRD Alignment:** PRD lists Google first
5. **Industry Adoption:** Widely used in Python community

**Consequences:**
- ✅ Readable docstrings
- ✅ Tool compatibility
- ✅ Consistent documentation style
- ⚠️ Contributors must learn Google docstring format

**Status:** Accepted ✅

---

### ADR-010: pytest >80% Coverage Requirement

**Context:**
NFR-QUAL-2 requires >80% unit test coverage. Need strategy for achieving and maintaining this.

**Decision:**
Use pytest with pytest-cov, enforce 80% minimum coverage in CI, target 100% for core graph generation logic.

**Rationale:**
1. **NFR Requirement:** Explicit requirement in PRD
2. **Quality Assurance:** High coverage catches regressions
3. **Core Logic:** 100% coverage for analyzer/generator ensures correctness
4. **CI Enforcement:** pytest-cov can fail builds if coverage drops
5. **Industry Standard:** 80% is achievable, realistic target

**Consequences:**
- ✅ High confidence in correctness
- ✅ Catch regressions early
- ✅ Enforced via CI
- ⚠️ Requires effort to write comprehensive tests
- ✅ Encourages testable design

**Status:** Accepted ✅

---

_Generated by BMAD Decision Architecture Workflow v1.0_
_Date: 2025-11-18_
_For: Luca_
