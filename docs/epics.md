# temporalio-graphs-python-port - Epic Breakdown

**Author:** Luca
**Date:** 2025-11-18
**Project Type:** developer_tool (Python library/package)
**Domain:** general
**Complexity:** low

---

## Overview

This document provides the complete epic and story breakdown for temporalio-graphs-python-port, decomposing the requirements from the [PRD](./prd.md) into implementable stories.

**Living Document Notice:** This is the initial version created from PRD and Architecture. It will be updated if UX Design workflows add additional context.

## Workflow Mode

🆕 **INITIAL CREATION MODE**

No existing epics found - creating the initial epic breakdown from PRD and Architecture.

## Available Context

**Available Context:**
- ✅ PRD (required) - 65 functional requirements covering complete feature parity with .NET version
- ✅ Architecture (complete technical decisions, static analysis approach validated by spike)
- ℹ️ UX Design: Not applicable (developer tool - library with programmatic API, no UI)

**Context Incorporated:**
- PRD requirements define WHAT capabilities exist (strategic level)
- Architecture defines HOW to implement (technical decisions, patterns, stack)
- This epic breakdown will add ALL implementation details (tactical level)

---

## Functional Requirements Inventory

Extracting all 65 functional requirements from PRD to ensure complete coverage:

**Core Graph Generation (FR1-FR10):**
- FR1: Library can parse Python workflow source files using AST analysis
- FR2: Library can detect @workflow.defn decorated classes and @workflow.run methods
- FR3: Library can identify activity calls (workflow.execute_activity())
- FR4: Library can extract activity names from execute_activity() calls
- FR5: Library can detect decision points (if/else statements, ternary operators)
- FR6: Library can generate 2^n execution path permutations for n independent decision points
- FR7: Library can track execution paths as sequences of activity names and decision nodes
- FR8: Library can output graph definitions in Mermaid flowchart syntax
- FR9: Library can generate Start and End nodes with configurable labels
- FR10: Library can deduplicate identical path segments in graph output

**Decision Node Support (FR11-FR17):**
- FR11: Users can mark boolean expressions as decision nodes using to_decision() helper function
- FR12: Decision nodes can have custom display names
- FR13: Decision nodes can have custom true/false branch labels (default: "yes"/"no")
- FR14: Decision nodes render in Mermaid as diamond shapes ({decision})
- FR15: Each decision node generates exactly 2 branches (true/false paths)
- FR16: Nested decisions create proper path permutations (2^n total paths)
- FR17: Decision IDs can be preserved or simplified (numeric) based on configuration

**Signal/Wait Condition Support (FR18-FR22):**
- FR18: Users can mark wait conditions as signal nodes using wait_condition() wrapper
- FR19: Signal nodes can have custom names for graph display
- FR20: Signal nodes render in Mermaid as hexagon shapes ({{signal}})
- FR21: Signal nodes have two outcomes: "Signaled" and "Timeout"
- FR22: Signal nodes integrate into path permutation generation

**Graph Output (FR23-FR30):**
- FR23: Library can generate complete Mermaid markdown with fenced code blocks
- FR24: Library can generate a list of all unique execution paths (text format)
- FR25: Library can identify and warn about unreachable activities
- FR26: Library can identify and warn about activities defined but never called
- FR27: Library can generate validation reports listing warnings
- FR28: Users can configure output to Mermaid-only (suppress path list and warnings)
- FR29: Users can configure node name formatting (split camelCase into "Camel Case")
- FR30: Library can write output to specified file path or return as string

**Configuration & Control (FR31-FR36):**
- FR31: Users can configure graph generation through GraphBuildingContext dataclass
- FR32: Users can enable/disable validation warnings
- FR33: Users can customize Start node label/format
- FR34: Users can customize End node label/format
- FR35: Users can control node name word-splitting behavior
- FR36: Users can control decision ID preservation (hash vs numeric)

**API & Integration (FR37-FR44):**
- FR37: Library exports clean public API: GraphBuilder, GraphBuildingContext, to_decision, wait_condition
- FR38: Library provides GraphPath class for tracking execution paths
- FR39: Library provides GraphGenerator class for rendering graphs
- FR40: All public APIs have complete type hints (mypy strict compatible)
- FR41: All public functions have docstrings with usage examples
- FR42: Library can analyze workflows without modifying user workflow code (except adding decision/signal helpers)
- FR43: Library can handle async workflow methods
- FR44: Library raises clear exceptions for unsupported workflow patterns

**Advanced Patterns (FR45-FR50):**
- FR45: Library can handle simple if/else conditionals
- FR46: Library can handle elif chains (multiple decision points)
- FR47: Library can handle ternary operators as decision points
- FR48: Library can handle sequential activity calls (linear paths)
- FR49: Library can handle parallel branches that reconverge
- FR50: Library can handle workflows with no decision points (linear flow)

**Output Format Compliance (FR51-FR55):**
- FR51: Generated Mermaid syntax is valid and renders correctly in Mermaid editors
- FR52: Graph structure matches .NET Temporalio.Graphs output for equivalent workflows
- FR53: Node naming follows Mermaid naming conventions
- FR54: Edge labels follow Mermaid syntax (-- label -->)
- FR55: Decision node format matches .NET output structure

**Examples & Documentation (FR56-FR60):**
- FR56: Library includes working MoneyTransfer workflow example (ported from .NET)
- FR57: MoneyTransfer example demonstrates decision nodes, signal nodes, and multiple paths
- FR58: Library includes simple linear workflow example
- FR59: Library includes multi-decision workflow example
- FR60: README provides quick start guide with <10 lines of example code

**Cross-Workflow Visualization (FR66-FR73):**
- FR66: Library can detect child workflow calls (workflow.execute_child_workflow())
- FR67: Library can extract child workflow class names from execute_child_workflow() calls
- FR68: Library can render child workflow nodes in Mermaid with distinct visual style
- FR69: Library can analyze multiple related workflows in a single call (parent + children)
- FR70: Library can generate end-to-end execution paths spanning parent and child workflows
- FR71: Library can render workflow call graphs showing parent-child relationships
- FR72: Child workflow nodes link to child workflow graphs (navigation/reference)
- FR73: Library includes parent-child workflow example demonstrating cross-workflow visualization

**Error Handling (FR61-FR65):**
- FR61: Library provides clear error messages when workflow file cannot be parsed
- FR62: Library warns when workflow patterns are too complex to analyze
- FR63: Library provides suggestions when unsupported patterns are detected
- FR64: Library gracefully handles missing/invalid workflow decorators
- FR65: Library validates that decision helper functions are used correctly

**Total: 73 Functional Requirements** (65 Core MVP + 8 Cross-Workflow Extension)

---

## Epic Structure Summary

Based on natural groupings that deliver incremental user value:

### Epic 1: Foundation & Project Setup
**Goal:** Establish project infrastructure and development environment
**User Value:** Enables all subsequent development work (greenfield exception)
**Story Count:** 1
**FRs Covered:** Infrastructure for all FRs (no direct FR mapping)

### Epic 2: Basic Graph Generation (Linear Workflows)
**Goal:** Generate Mermaid diagrams from workflows with sequential activities (no branching)
**User Value:** Python developers can visualize their linear Temporal workflows
**Story Count:** 8
**FRs Covered:** FR1-FR10, FR31-FR36, FR37-FR44, FR45, FR48, FR50-FR55 (~35 FRs)

### Epic 3: Decision Node Support (Branching Workflows)
**Goal:** Add decision node visualization for conditional workflow paths
**User Value:** Python developers can visualize branching workflows with complete path coverage
**Story Count:** 5
**FRs Covered:** FR11-FR17, FR46-FR47, FR49 (10 FRs)

### Epic 4: Signal & Wait Condition Support
**Goal:** Add signal node visualization for wait conditions and timeouts
**User Value:** Python developers can visualize workflows with wait conditions and signals
**Story Count:** 4
**FRs Covered:** FR18-FR22 (5 FRs)

### Epic 5: Production Readiness
**Goal:** Add validation, error handling, examples, and documentation for production use
**User Value:** Library is production-ready with comprehensive docs and robust error handling
**Story Count:** 5
**FRs Covered:** FR23-FR30, FR56-FR65 (18 FRs)

### Epic 6: Cross-Workflow Visualization (MVP Extension)
**Goal:** Enable visualization of parent-child workflow relationships and complete end-to-end execution flows
**User Value:** Python developers can visualize complete multi-workflow applications showing parent-child relationships and cross-workflow execution paths
**Story Count:** 5
**FRs Covered:** FR66-FR73 (8 FRs)

**Total: 6 Epics, 28 Stories, 73 FRs Covered**
**Core MVP (v0.1.0):** Epics 1-5, 23 Stories, 65 FRs
**MVP Extension (v0.2.0):** Epic 6, 5 Stories, 8 FRs

---

## FR Coverage Map

This table shows which FRs are addressed by each epic:

| Epic | FRs Covered | Description |
|------|-------------|-------------|
| **Epic 1: Foundation** | Infrastructure | Project setup (uv, hatchling, src/ layout, dependencies, build system) |
| **Epic 2: Basic Graph Generation** | FR1-FR10, FR31-FR36, FR37-FR44, FR45, FR48, FR50-FR55 | AST parsing, activity detection, linear path generation, Mermaid output, configuration, public API, type safety, basic patterns |
| **Epic 3: Decision Support** | FR11-FR17, FR46-FR47, FR49 | Decision nodes, to_decision() helper, path permutations, branching logic, elif chains, ternary operators |
| **Epic 4: Signal Support** | FR18-FR22 | Signal nodes, wait_condition() helper, timeout handling, hexagon rendering |
| **Epic 5: Production Ready** | FR23-FR30, FR56-FR65 | Validation warnings, path lists, error hierarchy, examples, documentation |
| **Epic 6: Cross-Workflow** | FR66-FR73 | Child workflow detection, cross-workflow rendering, multi-workflow analysis, end-to-end path generation, parent-child examples |

**FR Coverage Validation:**
- FR1-FR10: Epic 2 ✓
- FR11-FR17: Epic 3 ✓
- FR18-FR22: Epic 4 ✓
- FR23-FR30: Epic 5 ✓
- FR31-FR36: Epic 2 ✓
- FR37-FR44: Epic 2 ✓
- FR45-FR50: Epic 2 (FR45, 48, 50), Epic 3 (FR46, 47, 49) ✓
- FR51-FR55: Epic 2 ✓
- FR56-FR60: Epic 5 ✓
- FR61-FR65: Epic 5 ✓
- FR66-FR73: Epic 6 ✓

**All 73 FRs are covered across the 6 epics.**
**Core MVP (65 FRs):** Epics 1-5
**Extension (8 FRs):** Epic 6

---

## Epic 1: Foundation & Project Setup

**Goal:** Establish project infrastructure enabling all subsequent development

**Epic Value:** Creates foundation for Python library development with modern tooling (uv, hatchling), proper project structure (src/ layout), and development environment setup. This is the greenfield exception - pure infrastructure setup that enables all subsequent user-facing features.

**FRs Covered:** Infrastructure foundation (no direct FR mapping - enables all 65 FRs)

### Story 1.1: Initialize Python Library Project with Modern Tooling

**User Story:**
As a Python library developer,
I want a properly initialized project with modern build tools and dependencies,
So that I can begin implementing graph generation features with confidence in the project structure.

**Acceptance Criteria:**

**Given** a fresh project directory
**When** project initialization is executed
**Then** project uses uv package manager per global user requirements
**And** project structure follows src/ layout per Architecture ADR-004
**And** build backend is hatchling per Architecture ADR-003
**And** Python 3.10+ is set as minimum version per Architecture
**And** temporalio SDK >=1.7.1 is installed as core dependency
**And** development tools are installed: pytest, pytest-cov, pytest-asyncio, mypy, ruff
**And** pyproject.toml contains complete project metadata (name, version, description, dependencies)
**And** src/temporalio_graphs/ directory structure is created
**And** py.typed marker file exists in src/temporalio_graphs/
**And** __init__.py files exist for package recognition
**And** .python-version file specifies Python 3.11 (recommended)
**And** .gitignore excludes .venv/, dist/, __pycache__/, *.pyc, .pytest_cache/, .mypy_cache/
**And** verification command `uv run python -c "import temporalio; print('Ready')"` succeeds

**Prerequisites:** None (first story in project)

**Technical Notes:**
- Execute: `uv init --lib --build-backend hatchling`
- Create structure:
  ```
  temporalio-graphs/
  ├── .python-version (3.11)
  ├── pyproject.toml
  ├── README.md (placeholder)
  ├── src/
  │   └── temporalio_graphs/
  │       ├── __init__.py
  │       └── py.typed
  ├── tests/
  │   └── __init__.py
  └── examples/
  ```
- pyproject.toml must include:
  ```toml
  [project]
  name = "temporalio-graphs"
  version = "0.1.0"
  description = "Generate complete workflow visualization diagrams from Temporal workflows using static code analysis"
  requires-python = ">=3.10"
  dependencies = ["temporalio>=1.7.1"]

  [build-system]
  requires = ["hatchling"]
  build-backend = "hatchling.build"

  [tool.mypy]
  strict = true

  [tool.ruff]
  line-length = 100
  ```
- Install commands:
  ```bash
  uv add "temporalio>=1.7.1"
  uv add --dev pytest pytest-cov pytest-asyncio mypy ruff
  ```
- This story implements Architecture "Project Initialization" section and establishes ADR-001 through ADR-004 decisions

---

## Epic 2: Basic Graph Generation (Linear Workflows)

**Goal:** Generate Mermaid diagrams from workflows with sequential activities (no decision points)

**Epic Value:** Python developers can analyze their linear Temporal workflows and generate complete Mermaid diagrams showing activity sequences. This delivers the CORE capability - taking a workflow.py file and outputting a visualization, enabling immediate value even before branching support.

**FRs Covered:** FR1-FR10 (Core graph generation), FR31-FR36 (Configuration), FR37-FR44 (API & Integration), FR45, FR48, FR50 (Linear patterns), FR51-FR55 (Output compliance)

### Story 2.1: Implement Core Data Models with Type Safety

**User Story:**
As a library developer,
I want strongly-typed data models for graph building,
So that the code is maintainable and provides excellent IDE support.

**Acceptance Criteria:**

**Given** the project foundation exists
**When** core data models are implemented
**Then** GraphBuildingContext dataclass exists in src/temporalio_graphs/context.py
**And** GraphBuildingContext is frozen (immutable) per Architecture pattern
**And** GraphBuildingContext contains fields: is_building_graph, exit_after_building_graph, graph_output_file, split_names_by_words, suppress_validation, start_node_label, end_node_label, max_decision_points (default 10), max_paths (default 1024)
**And** NodeType enum exists with values: START, END, ACTIVITY, DECISION, SIGNAL
**And** GraphNode dataclass exists in src/temporalio_graphs/_internal/graph_models.py with fields: node_id, node_type, display_name, source_line
**And** GraphNode has to_mermaid() method returning correct syntax per node type
**And** GraphEdge dataclass exists with fields: from_node, to_node, label
**And** GraphEdge has to_mermaid() method for edge syntax
**And** GraphPath class exists in src/temporalio_graphs/path.py with methods: add_activity(), add_decision(), add_signal()
**And** WorkflowMetadata dataclass exists with fields: workflow_class, workflow_run_method, activities, decision_points, signal_points, source_file, total_paths
**And** all classes have complete type hints (mypy strict compliant) per NFR-QUAL-1
**And** all public classes have Google-style docstrings per Architecture ADR-009
**And** unit tests in tests/test_context.py and tests/test_path.py achieve 100% coverage

**Prerequisites:** Story 1.1 (Project initialized)

**Technical Notes:**
- Implement per Architecture "Core Data Models" section (lines 519-619)
- Use @dataclass(frozen=True) for immutability where appropriate
- NodeType enum structure:
  ```python
  class NodeType(Enum):
      START = "start"
      END = "end"
      ACTIVITY = "activity"
      DECISION = "decision"
      SIGNAL = "signal"
  ```
- GraphNode.to_mermaid() must generate:
  - START/END: `s((Start))`, `e((End))`
  - ACTIVITY: `1[ActivityName]`
  - DECISION: `0{DecisionName}`
  - SIGNAL: `2{{SignalName}}`
- Covers FR31, FR33-FR36, FR40 (configuration and type safety)

### Story 2.2: Implement AST-Based Workflow Analyzer

**User Story:**
As a library developer,
I want to parse Python workflow files and extract workflow structure,
So that I can identify activities and workflow methods for graph generation.

**Acceptance Criteria:**

**Given** a Python workflow source file exists
**When** WorkflowAnalyzer processes the file
**Then** WorkflowAnalyzer class exists in src/temporalio_graphs/analyzer.py extending ast.NodeVisitor
**And** analyzer detects @workflow.defn decorated classes (FR2)
**And** analyzer detects @workflow.run decorated methods (FR2)
**And** analyzer visits ClassDef nodes and checks for workflow decorator
**And** analyzer visits FunctionDef nodes and checks for run decorator
**And** analyzer extracts workflow class name and run method name
**And** analyzer stores source line numbers for error reporting per NFR-USE-2
**And** analyzer completes in <1ms for simple workflows per NFR-PERF-1
**And** analyzer raises WorkflowParseError if no @workflow.defn found (FR61, FR64)
**And** error message includes file path, line number, and suggestion per Architecture
**And** WorkflowMetadata is returned with extracted information
**And** all public methods have complete type hints passing mypy strict
**And** tests/test_analyzer.py covers: valid workflow, missing decorator, invalid Python syntax
**And** unit test coverage is 100% for WorkflowAnalyzer class per NFR-QUAL-2

**Prerequisites:** Story 2.1 (Data models exist)

**Technical Notes:**
- Implement per Architecture "AST Visitor Pattern" (lines 405-422)
- Use ast.parse(source_code) to get AST (FR1)
- Visitor pattern:
  ```python
  class WorkflowAnalyzer(ast.NodeVisitor):
      def visit_ClassDef(self, node: ast.ClassDef) -> None:
          # Check decorators for workflow.defn
          for decorator in node.decorator_list:
              if self._is_workflow_decorator(decorator):
                  self._workflow_class = node.name

      def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
          # Check for @workflow.run
          ...
  ```
- Test fixtures in tests/fixtures/sample_workflows/
- Covers FR1, FR2, FR40, FR43, FR61, FR64

### Story 2.3: Implement Activity Call Detection

**User Story:**
As a library developer,
I want to detect all activity calls in workflow code,
So that I can build graph nodes representing each activity.

**Acceptance Criteria:**

**Given** a workflow AST has been parsed
**When** activity detection runs
**Then** analyzer visits ast.Call nodes looking for workflow.execute_activity() (FR3)
**And** activity names are extracted from execute_activity() call arguments (FR4)
**And** activity calls are detected with patterns:
  - `workflow.execute_activity(my_activity, ...)`
  - `await workflow.execute_activity(my_activity, ...)`
  - `await workflow.execute_activity("activity_name", ...)`
**And** activity names handle both direct function references and string names
**And** source line numbers are recorded for each activity
**And** activities list is stored in WorkflowMetadata
**And** handles sequential activity calls (FR48)
**And** duplicate activity calls are allowed (same activity called multiple times)
**And** unit tests cover: simple linear workflow, multiple activities, duplicate activities, no activities (empty workflow)
**And** test coverage is 100% for activity detection logic
**And** detection completes in <0.5ms for workflows with 10 activities

**Prerequisites:** Story 2.2 (AST parser exists)

**Technical Notes:**
- Extend WorkflowAnalyzer with visit_Call method
- Check if call is attribute access (node.func.attr == "execute_activity")
- Extract activity name from first argument:
  ```python
  def visit_Call(self, node: ast.Call) -> None:
      if self._is_execute_activity_call(node):
          activity_name = self._extract_activity_name(node.args[0])
          self._activities.append((activity_name, node.lineno))
  ```
- Handle both ast.Name nodes (function ref) and ast.Constant (string)
- Covers FR3, FR4, FR48, FR50

### Story 2.4: Implement Basic Path Generator for Linear Workflows

**User Story:**
As a library developer,
I want to generate execution paths from activity sequences,
So that I can create graph representations of linear workflows.

**Acceptance Criteria:**

**Given** workflow metadata with activity list exists
**When** path generation runs for workflow with no decisions
**Then** PathPermutationGenerator class exists in src/temporalio_graphs/generator.py
**And** generator creates single linear path for workflows with no decisions (FR50)
**And** path includes Start node, all activities in sequence, and End node (FR9)
**And** GraphPath is built incrementally using add_activity() method (FR7)
**And** node IDs are generated deterministically (Start="s", End="e", activities="1","2","3"...)
**And** path generation handles workflows with 1 activity, many activities, and no activities
**And** empty workflows generate Start→End path
**And** performance: generates path in <0.1ms for 100 activities per NFR-PERF-1
**And** unit tests cover: empty workflow, single activity, multiple activities, long sequence (100 activities)
**And** test coverage is 100% for PathPermutationGenerator class

**Prerequisites:** Story 2.3 (Activity detection works)

**Technical Notes:**
- Implement per Architecture "Graph Generation Flow" (lines 447-457)
- For linear workflows (no decisions), create single GraphPath:
  ```python
  path = GraphPath(path_id="path_0")
  path.add_node("s", NodeType.START, context.start_node_label)
  for activity in activities:
      path.add_activity(activity.name)
  path.add_node("e", NodeType.END, context.end_node_label)
  ```
- Decision support will be added in Epic 3 (2^n permutations)
- Covers FR6 (trivial case: 2^0=1 path), FR7, FR9, FR50

### Story 2.5: Implement Mermaid Renderer with Format Compliance

**User Story:**
As a library user,
I want generated Mermaid syntax to be valid and render correctly,
So that I can use diagrams in documentation and viewers.

**Acceptance Criteria:**

**Given** a list of GraphPath objects exists
**When** Mermaid rendering is invoked
**Then** MermaidRenderer class exists in src/temporalio_graphs/renderer.py
**And** renderer generates valid Mermaid flowchart syntax (FR8, FR51)
**And** output starts with triple-backtick fenced code block: \`\`\`mermaid
**And** flowchart direction is "LR" (left to right)
**And** Start node renders as: `s((Start))`
**And** End node renders as: `e((End))`
**And** Activity nodes render as: `1[ActivityName]`
**And** edges render as: `node1 --> node2` (FR54)
**And** nodes are deduplicated (same node ID appears once) (FR10)
**And** edges are deduplicated (same connection appears once) (FR10)
**And** node names support word splitting when context.split_names_by_words=True (FR29, FR35)
**And** camelCase names split to "Camel Case" when enabled
**And** generated Mermaid validates in Mermaid Live Editor
**And** output structure matches .NET Temporalio.Graphs for equivalent workflows (FR52)
**And** fenced code block closes with \`\`\`
**And** unit tests compare output against golden files from .NET version (FR52)
**And** tests cover: simple linear workflow, multiple activities, word splitting enabled/disabled
**And** rendering completes in <1ms for 50-node graphs per NFR-PERF-1

**Prerequisites:** Story 2.4 (Path generation works)

**Technical Notes:**
- Implement per Architecture "Mermaid Generation Optimization" (lines 984-1010)
- Use StringIO for efficient string building
- Node deduplication using set of seen node IDs
- Edge deduplication using set of (from, to, label) tuples
- Word splitting regex: `re.sub(r'([a-z])([A-Z])', r'\1 \2', name)`
- Golden file regression tests: tests/fixtures/expected_outputs/
- Output format:
  ```
  ```mermaid
  flowchart LR
  s((Start)) --> 1[Activity Name]
  1[Activity Name] --> e((End))
  ```
  ```
- Covers FR8, FR9, FR10, FR29, FR35, FR51-FR55

### Story 2.6: Implement Public API Entry Point

**User Story:**
As a Python developer using Temporal,
I want a simple function to analyze my workflows,
So that I can generate diagrams with minimal code.

**Acceptance Criteria:**

**Given** all core components are implemented
**When** I import and use the public API
**Then** analyze_workflow() function exists in src/temporalio_graphs/__init__.py (FR37)
**And** function signature is: `analyze_workflow(workflow_file: Path | str, context: Optional[GraphBuildingContext] = None, output_format: Literal["mermaid", "json", "paths"] = "mermaid") -> str`
**And** function accepts Path or str for workflow_file parameter
**And** function uses default GraphBuildingContext if none provided
**And** function validates workflow file exists and is readable per Architecture security
**And** function calls WorkflowAnalyzer to parse AST
**And** function calls PathPermutationGenerator to generate paths
**And** function calls MermaidRenderer to generate output
**And** function returns Mermaid markdown string (FR8, FR23)
**And** function writes to file if context.graph_output_file is set (FR30)
**And** function raises clear exceptions for errors (FR44, FR61)
**And** public API exports: GraphBuildingContext, analyze_workflow (FR37)
**And** all exported symbols have complete type hints (FR40)
**And** all public functions have Google-style docstrings with examples (FR41)
**And** quick start example works in <10 lines of code (FR60)
**And** integration test demonstrates end-to-end usage
**And** API is Pythonic and intuitive per NFR-USE-1

**Prerequisites:** Story 2.5 (Renderer works)

**Technical Notes:**
- Implement per Architecture "Primary Entry Point" (lines 683-709)
- __init__.py exports:
  ```python
  from temporalio_graphs.context import GraphBuildingContext
  from temporalio_graphs.analyzer import analyze_workflow

  __all__ = ["GraphBuildingContext", "analyze_workflow"]
  ```
- Quick start example:
  ```python
  from temporalio_graphs import analyze_workflow
  result = analyze_workflow("my_workflow.py")
  print(result)  # Shows Mermaid diagram
  ```
- File validation per Architecture "Input Validation" (lines 829-851)
- Covers FR8, FR23, FR30, FR37, FR40, FR41, FR42, FR43, FR44, FR60

### Story 2.7: Implement Configuration Options

**User Story:**
As a library user,
I want to customize graph generation behavior,
So that I can control output format and validation.

**Acceptance Criteria:**

**Given** the public API is working
**When** I create GraphBuildingContext with custom options
**Then** split_names_by_words option controls camelCase splitting (FR29, FR35)
**And** suppress_validation option disables validation warnings (FR32)
**And** start_node_label and end_node_label customize node labels (FR33, FR34)
**And** max_decision_points limits permutation explosion (FR36, NFR-PERF-2)
**And** graph_output_file path enables writing to file (FR30)
**And** all configuration options work correctly in analyze_workflow()
**And** configuration is passed through entire pipeline (analyzer → generator → renderer)
**And** invalid configuration raises clear error (e.g., negative max_decision_points)
**And** unit tests cover each configuration option independently
**And** integration test demonstrates multiple options working together
**And** documentation examples show common configuration patterns

**Prerequisites:** Story 2.6 (Public API exists)

**Technical Notes:**
- GraphBuildingContext already implemented in Story 2.1
- This story ensures all options are wired through pipeline
- Example usage:
  ```python
  context = GraphBuildingContext(
      split_names_by_words=False,
      start_node_label="BEGIN",
      max_decision_points=15
  )
  result = analyze_workflow("workflow.py", context)
  ```
- Covers FR28, FR29, FR30, FR31, FR32, FR33, FR34, FR35, FR36

### Story 2.8: Add Integration Test with Simple Linear Workflow Example

**User Story:**
As a library developer,
I want comprehensive integration tests,
So that I can ensure the entire pipeline works correctly.

**Acceptance Criteria:**

**Given** all core components are implemented
**When** integration tests run
**Then** tests/integration/test_simple_linear.py exists
**And** test creates complete workflow file with 3-4 activities
**And** test calls analyze_workflow() on the workflow file
**And** test validates Mermaid output is valid syntax
**And** test checks output contains: Start node, all activities in order, End node
**And** test validates node IDs are correct (s, 1, 2, 3, e)
**And** test validates edges connect correctly (s→1→2→3→e)
**And** examples/simple_linear/workflow.py exists as runnable example (FR58)
**And** examples/simple_linear/run.py demonstrates usage
**And** examples/simple_linear/expected_output.md contains golden Mermaid diagram
**And** integration test passes with 100% success rate
**And** test runs in <500ms total per NFR-MAINT-2
**And** example is documented in README as quick start

**Prerequisites:** Story 2.7 (All features working)

**Technical Notes:**
- Example workflow structure:
  ```python
  @workflow.defn
  class SimpleWorkflow:
      @workflow.run
      async def run(self) -> str:
          await workflow.execute_activity(validate_input, ...)
          await workflow.execute_activity(process_data, ...)
          await workflow.execute_activity(save_result, ...)
          return "complete"
  ```
- Expected Mermaid:
  ```mermaid
  flowchart LR
  s((Start)) --> 1[Validate Input]
  1 --> 2[Process Data]
  2 --> 3[Save Result]
  3 --> e((End))
  ```
- Integration test validates full pipeline: file → AST → paths → Mermaid
- Covers FR58 (simple linear example), validates Epic 2 delivery

---

## Epic 3: Decision Node Support (Branching Workflows)

**Goal:** Add decision node visualization for conditional workflow paths with complete path coverage

**Epic Value:** Python developers can visualize branching workflows showing ALL possible execution paths (2^n paths for n decisions). This extends the core capability from linear to branching workflows, enabling visualization of real-world workflow logic with conditionals.

**FRs Covered:** FR11-FR17 (Decision node support), FR46-FR47 (elif chains, ternary operators), FR49 (reconverging branches)

### Story 3.1: Implement Decision Point Detection in AST

**User Story:**
As a library developer,
I want to detect to_decision() helper calls in workflow code,
So that I can identify which boolean expressions should appear as decision nodes.

**Acceptance Criteria:**

**Given** a workflow with if statements exists
**When** DecisionDetector analyzes the AST
**Then** DecisionDetector class exists in src/temporalio_graphs/detector.py
**And** detector identifies calls to to_decision() function (FR11)
**And** detector extracts decision name from second argument (FR12)
**And** detector extracts boolean expression from first argument
**And** detector records source line number for error reporting
**And** detector handles patterns:
  - `if await to_decision(condition, "Name"):`
  - `result = await to_decision(amount > 1000, "HighValue")`
**And** detector identifies elif chains as multiple decisions (FR46)
**And** detector identifies ternary operators wrapped in to_decision (FR47)
**And** detector stores decision metadata: id, name, line number, true_label, false_label
**And** decision_points list is added to WorkflowMetadata
**And** unit tests cover: single decision, multiple decisions, nested decisions, elif chain
**And** test coverage is 100% for DecisionDetector

**Prerequisites:** Story 2.2 (AST parser exists)

**Technical Notes:**
- Extend WorkflowAnalyzer to call DecisionDetector
- Detect to_decision() calls in visit_Call:
  ```python
  def visit_Call(self, node: ast.Call) -> None:
      if self._is_to_decision_call(node):
          decision_name = self._extract_string_arg(node.args[1])
          self._decisions.append((decision_name, node.lineno))
  ```
- Handle IfExp nodes (ternary) with to_decision wrapper (FR47)
- Covers FR11, FR12, FR46, FR47

### Story 3.2: Implement to_decision() Helper Function

**User Story:**
As a Python developer using Temporal,
I want a helper function to mark decision points in my workflow,
So that they appear as decision nodes in the generated graph.

**Acceptance Criteria:**

**Given** I'm writing a Temporal workflow
**When** I use to_decision() to mark conditionals
**Then** to_decision() function exists in src/temporalio_graphs/helpers.py (FR11)
**And** function signature is: `async def to_decision(result: bool, name: str) -> bool`
**And** function returns the input boolean unchanged (transparent passthrough)
**And** function is async-compatible for workflow use (FR43)
**And** function has complete type hints (FR40)
**And** function has Google-style docstring with usage example (FR41)
**And** docstring example shows: `if await to_decision(amount > 1000, "HighValue"):`
**And** function is exported from public API (FR37)
**And** unit tests verify function returns correct boolean value
**And** integration test shows function works in actual workflow
**And** documentation explains when and how to use to_decision()

**Prerequisites:** Story 3.1 (Decision detection works)

**Technical Notes:**
- Implement per Architecture "Workflow Helper Functions" (lines 748-795)
- Simple implementation:
  ```python
  async def to_decision(result: bool, name: str) -> bool:
      """Mark a boolean expression as a decision node in the workflow graph.

      Args:
          result: The boolean value to evaluate
          name: Human-readable decision name for graph display

      Returns:
          The original boolean value (passthrough)

      Example:
          >>> if await to_decision(amount > 1000, "HighValue"):
          >>>     await workflow.execute_activity(special_handling)
      """
      return result
  ```
- Export from __init__.py
- Covers FR11, FR12, FR40, FR41, FR43

### Story 3.3: Implement Path Permutation Generator for Decisions

**User Story:**
As a library developer,
I want to generate all possible execution paths through decision points,
So that the graph shows complete workflow coverage.

**Acceptance Criteria:**

**Given** workflow metadata contains decision points
**When** path generation runs for workflow with decisions
**Then** generator creates 2^n paths for n independent decisions (FR6, FR16)
**And** each decision generates exactly 2 branches (true/false) (FR15)
**And** branch labels default to "yes" and "no" (FR13)
**And** custom branch labels are supported via configuration
**And** decision nodes render with diamond syntax in paths
**And** nested decisions create proper permutations (FR16)
**And** reconverging branches are handled correctly (FR49)
**And** generator uses itertools.product for efficient permutation
**And** generator checks decision count against max_decision_points before generation
**And** generator raises GraphGenerationError if decision_points > limit (default 10)
**And** error message suggests refactoring or increasing limit
**And** performance: generates 32 paths (5 decisions) in <1 second per NFR-PERF-1
**And** performance: generates 1024 paths (10 decisions) in <5 seconds
**And** safety: max_paths limit prevents memory exhaustion per NFR-PERF-2
**And** unit tests cover: 1 decision (2 paths), 2 decisions (4 paths), 3 decisions (8 paths), explosion limit
**And** test validates all permutations are generated (no missing paths)

**Prerequisites:** Story 2.4 (Basic path generator exists), Story 3.1 (Decisions detected)

**Technical Notes:**
- Implement per Architecture "Path Explosion Management" (lines 935-963)
- Use itertools.product for permutations:
  ```python
  from itertools import product

  num_decisions = len(decisions)
  total_paths = 2 ** num_decisions

  if total_paths > context.max_paths:
      raise GraphGenerationError(f"Too many paths: {total_paths}")

  for choices in product([True, False], repeat=num_decisions):
      path = self._build_path(decisions, choices)
      paths.append(path)
  ```
- Each path includes decision nodes with branch taken
- Covers FR6, FR13, FR15, FR16, FR49, NFR-PERF-1, NFR-PERF-2

### Story 3.4: Implement Decision Node Rendering in Mermaid

**User Story:**
As a library user,
I want decision points to appear as diamond shapes in Mermaid,
So that the graph clearly shows conditional branches.

**Acceptance Criteria:**

**Given** paths contain decision nodes
**When** Mermaid rendering runs
**Then** decision nodes render with diamond syntax: `0{DecisionName}` (FR14)
**And** decision node IDs are deterministic (hash-based or numeric) (FR17)
**And** true branches render with label: `-- yes -->` (default)
**And** false branches render with label: `-- no -->` (default)
**And** custom branch labels are supported via configuration
**And** decision nodes deduplicate correctly (same decision appears once)
**And** edges from decisions to activities render correctly
**And** parallel branches from decision reconverge properly
**And** generated Mermaid is valid and renders in Mermaid Live Editor
**And** output matches .NET Temporalio.Graphs structure for equivalent workflows
**And** unit tests compare against .NET golden files
**And** tests cover: single decision, multiple decisions, nested decisions

**Prerequisites:** Story 3.3 (Path permutations work), Story 2.5 (Renderer exists)

**Technical Notes:**
- Extend MermaidRenderer to handle NodeType.DECISION
- GraphNode.to_mermaid() for DECISION type:
  ```python
  if self.node_type == NodeType.DECISION:
      return f"{self.node_id}{{{self.display_name}}}"
  ```
- Edge labels from decision nodes:
  ```python
  edge_label = context.decision_true_label if branch else context.decision_false_label
  edge = GraphEdge(decision_id, next_node_id, edge_label)
  ```
- Covers FR13, FR14, FR15, FR17

### Story 3.5: Add Integration Test with MoneyTransfer Example

**User Story:**
As a library developer,
I want the MoneyTransfer example from .NET to work identically,
So that I can validate feature parity with the original implementation.

**Acceptance Criteria:**

**Given** decision support is fully implemented
**When** MoneyTransfer workflow is analyzed
**Then** examples/money_transfer/workflow.py exists (ported from .NET) (FR56)
**And** workflow has 2 decision points: "NeedToConvert" and "IsTFN_Known" (FR57)
**And** workflow generates 4 paths (2^2) (FR57)
**And** workflow includes activities: Withdraw, CurrencyConvert, NotifyAto, TakeNonResidentTax, Deposit
**And** analyze_workflow() produces valid Mermaid output
**And** output structure matches .NET Temporalio.Graphs output (FR52, FR57)
**And** generated graph shows all 4 execution paths clearly
**And** examples/money_transfer/run.py demonstrates usage
**And** examples/money_transfer/expected_output.md contains golden Mermaid diagram
**And** tests/integration/test_money_transfer.py validates output
**And** regression test compares output against .NET golden file
**And** test passes with 100% accuracy (byte-for-byte match or structural equivalence)
**And** example is documented in README

**Prerequisites:** Story 3.4 (Decision rendering works)

**Technical Notes:**
- Port from Temporalio.Graphs/Samples/MoneyTransferWorker/
- Expected workflow structure:
  ```python
  @workflow.defn
  class MoneyTransferWorkflow:
      @workflow.run
      async def run(self, transfer: TransferInput) -> str:
          await workflow.execute_activity(withdraw, ...)

          if await to_decision(transfer.source_currency != transfer.dest_currency, "NeedToConvert"):
              await workflow.execute_activity(currency_convert, ...)

          if await to_decision(transfer.tfn_known, "IsTFN_Known"):
              await workflow.execute_activity(notify_ato, ...)
          else:
              await workflow.execute_activity(take_non_resident_tax, ...)

          await workflow.execute_activity(deposit, ...)
          return "complete"
  ```
- Expected Mermaid shows 4 paths with diamond decision nodes
- Regression test critical for NFR-REL-1 (correctness)
- Covers FR52, FR56, FR57, NFR-REL-1

---

## Epic 4: Signal & Wait Condition Support

**Goal:** Add signal node visualization for wait conditions and timeout handling

**Epic Value:** Python developers can visualize workflows with wait conditions, showing both "Signaled" and "Timeout" outcome paths. This completes the node type coverage (activities, decisions, signals) enabling visualization of workflows with asynchronous signal patterns.

**FRs Covered:** FR18-FR22 (Signal/wait condition support)

### Story 4.1: Implement Signal Point Detection in AST

**User Story:**
As a library developer,
I want to detect wait_condition() wrapper calls in workflow code,
So that I can identify which waits should appear as signal nodes.

**Acceptance Criteria:**

**Given** a workflow with wait_condition exists
**When** detector analyzes the AST
**Then** detector identifies calls to wait_condition() function (FR18)
**And** detector extracts signal name from third argument (FR19)
**And** detector records source line number
**And** detector handles pattern: `await wait_condition(lambda: check, timeout, "SignalName")`
**And** signal_points list is added to WorkflowMetadata
**And** unit tests cover: single signal, multiple signals, signal with decision
**And** test coverage is 100% for signal detection

**Prerequisites:** Story 3.1 (DecisionDetector pattern established)

**Technical Notes:**
- Extend DecisionDetector or create SignalDetector in detector.py
- Similar pattern to decision detection:
  ```python
  def visit_Call(self, node: ast.Call) -> None:
      if self._is_wait_condition_call(node):
          signal_name = self._extract_string_arg(node.args[2])
          self._signals.append((signal_name, node.lineno))
  ```
- Covers FR18, FR19

### Story 4.2: Implement wait_condition() Helper Function

**User Story:**
As a Python developer using Temporal,
I want a helper function to mark wait conditions in my workflow,
So that they appear as signal nodes in the generated graph.

**Acceptance Criteria:**

**Given** I'm writing a Temporal workflow with signals
**When** I use wait_condition() to mark waits
**Then** wait_condition() function exists in src/temporalio_graphs/helpers.py (FR18)
**And** function signature is: `async def wait_condition(condition_check: Callable[[], bool], timeout: timedelta, name: str) -> bool`
**And** function wraps workflow.wait_condition() internally
**And** function returns True if condition met, False if timeout
**And** function is async-compatible (FR43)
**And** function has complete type hints (FR40)
**And** function has Google-style docstring with usage example (FR41)
**And** function is exported from public API (FR37)
**And** unit tests verify function behavior
**And** integration test shows function works in workflow

**Prerequisites:** Story 4.1 (Signal detection works), Story 3.2 (Helper pattern established)

**Technical Notes:**
- Implement per Architecture "Workflow Helper Functions" (lines 773-795)
- Implementation:
  ```python
  async def wait_condition(
      condition_check: Callable[[], bool],
      timeout: timedelta,
      name: str
  ) -> bool:
      """Mark a wait condition as a signal node in the workflow graph.

      Args:
          condition_check: Callable that checks condition
          timeout: Maximum time to wait
          name: Display name for signal node

      Returns:
          True if condition met before timeout, False otherwise
      """
      return await workflow.wait_condition(condition_check, timeout)
  ```
- Covers FR18, FR19, FR40, FR41, FR43

### Story 4.3: Implement Signal Node Rendering in Mermaid

**User Story:**
As a library user,
I want signal nodes to appear as hexagons in Mermaid,
So that wait conditions are visually distinct from decisions.

**Acceptance Criteria:**

**Given** paths contain signal nodes
**When** Mermaid rendering runs
**Then** signal nodes render with hexagon syntax: `2{{SignalName}}` (FR20)
**And** signal node IDs are deterministic
**And** "Signaled" branch renders with label: `-- Signaled -->` (FR21)
**And** "Timeout" branch renders with label: `-- Timeout -->` (FR21)
**And** custom signal labels are supported via configuration
**And** signal nodes integrate into path permutation (each signal = 2 paths) (FR22)
**And** generated Mermaid is valid and renders correctly
**And** unit tests cover: single signal, signal + decision, multiple signals

**Prerequisites:** Story 4.2 (wait_condition works), Story 3.4 (Node rendering pattern)

**Technical Notes:**
- Extend MermaidRenderer to handle NodeType.SIGNAL
- GraphNode.to_mermaid() for SIGNAL type:
  ```python
  if self.node_type == NodeType.SIGNAL:
      return f"{self.node_id}{{{{{self.display_name}}}}}"  # Double braces for hexagon
  ```
- Signal behaves like decision (2 branches) but different labels
- Covers FR20, FR21, FR22

### Story 4.4: Add Integration Test with Signal Example

**User Story:**
As a library developer,
I want an example workflow with signals,
So that users can see how to visualize wait conditions.

**Acceptance Criteria:**

**Given** signal support is fully implemented
**When** signal example workflow is analyzed
**Then** examples/signal_workflow/workflow.py exists
**And** workflow contains wait_condition for approval signal
**And** workflow shows "Signaled" and "Timeout" paths
**And** analyze_workflow() produces valid Mermaid with hexagon nodes
**And** examples/signal_workflow/expected_output.md contains golden diagram
**And** tests/integration/test_signal_workflow.py validates output
**And** test passes with 100% accuracy
**And** example is documented

**Prerequisites:** Story 4.3 (Signal rendering works)

**Technical Notes:**
- Example workflow structure:
  ```python
  @workflow.defn
  class ApprovalWorkflow:
      @workflow.run
      async def run(self) -> str:
          await workflow.execute_activity(submit_request, ...)

          approved = await wait_condition(
              lambda: self.is_approved,
              timedelta(hours=24),
              "WaitForApproval"
          )

          if approved:
              await workflow.execute_activity(process_approved, ...)
          else:
              await workflow.execute_activity(handle_timeout, ...)

          return "complete"
  ```
- Expected Mermaid shows hexagon signal node with Signaled/Timeout branches
- Covers FR18-FR22 validation

---

## Epic 5: Production Readiness

**Goal:** Add validation, error handling, examples, and documentation for production-grade library

**Epic Value:** Library is production-ready with comprehensive error messages, validation warnings, complete examples, and documentation. Users can confidently adopt the library knowing it has robust error handling and clear guidance.

**FRs Covered:** FR23-FR30 (Graph output features), FR56-FR60 (Examples & docs), FR61-FR65 (Error handling)

### Story 5.1: Implement Validation Warnings for Graph Quality

**User Story:**
As a library user,
I want warnings about potential workflow issues,
So that I can identify unreachable code or unused activities.

**Acceptance Criteria:**

**Given** workflow analysis is complete
**When** validation runs
**Then** library identifies unreachable activities (FR25)
**And** library identifies activities defined but never called (FR26)
**And** validation warnings are collected in list
**And** warnings include file path, line number, activity name, and description
**And** warnings can be suppressed via context.suppress_validation (FR32)
**And** validation report lists all warnings when enabled (FR27)
**And** warnings are output after Mermaid diagram (FR28 - can suppress)
**And** warning format is clear and actionable per NFR-USE-2
**And** unit tests cover: unreachable activity, unused activity, no warnings, suppressed warnings
**And** integration test demonstrates validation warnings in output

**Prerequisites:** Story 2.8 (Basic graph generation complete)

**Technical Notes:**
- Add validation logic to generator or analyzer
- Check for unreachable activities:
  ```python
  defined_activities = set(all activities found in AST)
  called_activities = set(activities in generated paths)
  unreachable = defined_activities - called_activities
  ```
- Warning format:
  ```
  ⚠️ Validation Warnings:
  - Unreachable activity: 'special_handling' at line 42
    This activity is defined but never called in any execution path.
  ```
- Covers FR25, FR26, FR27, FR28, FR32

### Story 5.2: Implement Comprehensive Error Handling Hierarchy

**User Story:**
As a library user,
I want clear error messages when something goes wrong,
So that I can quickly understand and fix issues.

**Acceptance Criteria:**

**Given** various error conditions can occur
**When** errors are encountered
**Then** exception hierarchy exists in src/temporalio_graphs/exceptions.py
**And** TemporalioGraphsError is base exception class
**And** WorkflowParseError is raised when file cannot be parsed (FR61)
**And** UnsupportedPatternError is raised for unsupported patterns (FR62)
**And** GraphGenerationError is raised when graph cannot be generated
**And** InvalidDecisionError is raised for incorrect helper usage (FR65)
**And** all exceptions include file path, line number, error description
**And** all exceptions include actionable suggestions per NFR-USE-2 (FR63)
**And** error messages are clear and jargon-free
**And** examples of clear error messages:
  - "Cannot parse workflow file: {path}\nLine {n}: Missing @workflow.defn decorator\nSuggestion: Add @workflow.defn decorator to workflow class"
  - "Too many decision points ({n}) would generate {2^n} paths (limit: {limit})\nSuggestion: Refactor workflow or increase max_decision_points"
**And** unit tests cover each exception type
**And** integration tests verify error messages are helpful

**Prerequisites:** Story 2.2 (Basic error handling exists)

**Technical Notes:**
- Implement per Architecture "Exception Hierarchy" (lines 799-823)
- Exception structure:
  ```python
  class TemporalioGraphsError(Exception):
      """Base exception for all library errors."""
      pass

  class WorkflowParseError(TemporalioGraphsError):
      """Raised when workflow file cannot be parsed."""
      def __init__(self, file_path: Path, line: int, message: str, suggestion: str):
          super().__init__(
              f"Cannot parse workflow file: {file_path}\n"
              f"Line {line}: {message}\n"
              f"Suggestion: {suggestion}"
          )
  ```
- Covers FR61, FR62, FR63, FR64, FR65, NFR-USE-2

### Story 5.3: Implement Path List Output Format

**User Story:**
As a library user,
I want to see a text list of all execution paths,
So that I can understand workflow coverage without reading the graph.

**Acceptance Criteria:**

**Given** paths have been generated
**When** path list output is requested
**Then** library generates text list of all unique execution paths (FR24)
**And** each path shows sequence of activity names
**And** decision outcomes are shown in path description
**And** paths are numbered sequentially (Path 1, Path 2, etc.)
**And** format is human-readable:
  ```
  Path 1: Start → Withdraw → Currency Convert → Notify ATO → Deposit → End
  Path 2: Start → Withdraw → Currency Convert → Take Non-Resident Tax → Deposit → End
  Path 3: Start → Withdraw → Notify ATO → Deposit → End
  Path 4: Start → Withdraw → Take Non-Resident Tax → Deposit → End
  ```
**And** path list can be included in Mermaid output or returned separately
**And** path list can be suppressed via configuration (FR28)
**And** unit tests validate path list format
**And** integration test shows path list for MoneyTransfer (4 paths)

**Prerequisites:** Story 3.5 (Path permutations working)

**Technical Notes:**
- Add path list generation to MermaidRenderer or separate formatter
- Extract path sequence from GraphPath:
  ```python
  def format_path_list(paths: list[GraphPath]) -> str:
      lines = []
      for i, path in enumerate(paths, 1):
          activities = " → ".join(step.name for step in path.steps)
          lines.append(f"Path {i}: {activities}")
      return "\n".join(lines)
  ```
- Covers FR24, FR28

### Story 5.4: Create Comprehensive Example Gallery

**User Story:**
As a library user,
I want multiple example workflows,
So that I can learn different visualization patterns.

**Acceptance Criteria:**

**Given** library features are complete
**When** examples are created
**Then** examples/simple_linear/ exists with linear workflow (FR58) ✓ (from Story 2.8)
**And** examples/money_transfer/ exists with decision nodes (FR56, FR57) ✓ (from Story 3.5)
**And** examples/multi_decision/ exists with 3+ decisions (FR59)
**And** examples/signal_workflow/ exists with wait conditions ✓ (from Story 4.4)
**And** each example has: workflow.py, run.py, expected_output.md
**And** all examples are runnable and produce correct output
**And** multi_decision example shows 8+ paths (3 decisions = 2^3)
**And** each example is documented in README
**And** examples are tested in CI
**And** examples demonstrate best practices

**Prerequisites:** Story 3.5 (MoneyTransfer), Story 4.4 (Signals), Story 2.8 (Linear)

**Technical Notes:**
- Multi-decision example (3 decisions):
  ```python
  @workflow.defn
  class LoanApprovalWorkflow:
      @workflow.run
      async def run(self, application: LoanApp) -> str:
          await workflow.execute_activity(validate_application, ...)

          if await to_decision(application.amount > 10000, "HighValue"):
              await workflow.execute_activity(manager_review, ...)

          if await to_decision(application.credit_score < 600, "LowCredit"):
              await workflow.execute_activity(require_collateral, ...)

          if await to_decision(application.has_existing_loans, "ExistingLoans"):
              await workflow.execute_activity(debt_ratio_check, ...)

          await workflow.execute_activity(approve_loan, ...)
          return "approved"
  ```
- Covers FR56, FR57, FR58, FR59

### Story 5.5: Create Production-Grade Documentation

**User Story:**
As a library user,
I want comprehensive documentation,
So that I can quickly adopt the library and troubleshoot issues.

**Acceptance Criteria:**

**Given** all features are implemented
**When** documentation is complete
**Then** README.md contains: project overview, installation instructions, quick start guide (<10 lines) (FR60)
**And** README has badges: PyPI version, test coverage, license, Python versions
**And** README links to all examples
**And** README explains core concepts: AST analysis, decision nodes, signal nodes
**And** README shows common configuration patterns
**And** docs/api-reference.md contains: all public classes/functions with signatures and examples
**And** API reference is auto-generated from docstrings (Google style)
**And** CHANGELOG.md exists following Keep a Changelog format
**And** LICENSE file is MIT (matching .NET version per NFR-QUAL-4)
**And** documentation explains difference from .NET version (static analysis vs interceptors)
**And** documentation shows migration guide from .NET for C# developers
**And** troubleshooting section covers: common errors, unsupported patterns, performance tips
**And** documentation is clear and accessible to intermediate Python developers
**And** all documentation examples are tested and working

**Prerequisites:** Story 5.4 (Examples complete)

**Technical Notes:**
- Quick start example (<10 lines):
  ```python
  # Install
  pip install temporalio-graphs

  # Use
  from temporalio_graphs import analyze_workflow
  result = analyze_workflow("my_workflow.py")
  print(result)  # Mermaid diagram
  ```
- Consider using mkdocs or Sphinx for API docs (future)
- README badges from shields.io
- Covers FR60, NFR-USE-3

---

## Epic 6: Cross-Workflow Visualization (MVP Extension)

**Goal:** Enable visualization of parent-child workflow relationships and complete end-to-end execution flows

**Epic Value:** Python developers can visualize complete multi-workflow applications showing parent-child relationships and cross-workflow execution paths. Real-world Temporal applications commonly use parent-child workflow patterns - this epic enables visualization of complete system flows spanning multiple workflows, essential for understanding complex workflow orchestrations.

**FRs Covered:** FR66-FR73 (Cross-workflow visualization)

### Story 6.1: Detect Child Workflow Calls in AST

**User Story:**
As a library developer,
I want to detect execute_child_workflow() calls in workflow code,
So that I can identify parent-child workflow relationships for visualization.

**Acceptance Criteria:**

**Given** a workflow file contains child workflow calls
**When** WorkflowAnalyzer processes the file
**Then** analyzer detects workflow.execute_child_workflow() calls (FR66)
**And** analyzer extracts child workflow class names from arguments (FR67)
**And** analyzer handles patterns:
  - `await workflow.execute_child_workflow(ChildWorkflow, ...)`
  - `await workflow.execute_child_workflow("ChildWorkflowName", ...)`
**And** analyzer records source line numbers for each child workflow call
**And** child_workflows list is added to WorkflowMetadata
**And** child workflow metadata includes: child_class_name, call_site_line, parent_activity_context
**And** multiple calls to same child workflow are tracked separately
**And** unit tests cover: single child, multiple children, nested child calls, no children
**And** test coverage is 100% for child workflow detection logic
**And** detection completes in <1ms per NFR-PERF-1

**Prerequisites:** Story 2.3 (Activity detection pattern established)

**Technical Notes:**
- Extend WorkflowAnalyzer.visit_Call() to detect execute_child_workflow
- Similar pattern to activity detection:
  ```python
  def visit_Call(self, node: ast.Call) -> None:
      if self._is_execute_child_workflow_call(node):
          child_name = self._extract_workflow_name(node.args[0])
          self._child_workflows.append((child_name, node.lineno))
  ```
- ChildWorkflowCall dataclass in graph_models.py
- Covers FR66, FR67

### Story 6.2: Implement Child Workflow Node Rendering in Mermaid

**User Story:**
As a library user,
I want child workflow calls to appear distinctly in Mermaid diagrams,
So that I can visually distinguish workflow orchestration from activity execution.

**Acceptance Criteria:**

**Given** paths contain child workflow nodes
**When** Mermaid rendering runs
**Then** child workflow nodes render with distinct visual style (FR68)
**And** child workflow nodes use subroutine/subprocess shape: `1[[ChildWorkflow]]`
**And** child workflow node IDs are deterministic
**And** node labels show child workflow name
**And** child workflow nodes integrate into path generation like activities
**And** generated Mermaid is valid and renders in Mermaid Live Editor
**And** visual distinction is clear between activities (rectangles) and child workflows (subroutines)
**And** unit tests cover: single child workflow, multiple child workflows, child workflow with decisions
**And** rendering completes in <1ms for graphs with child workflows

**Prerequisites:** Story 6.1 (Child workflow detection works), Story 2.5 (Renderer exists)

**Technical Notes:**
- Extend NodeType enum with CHILD_WORKFLOW
- GraphNode.to_mermaid() for CHILD_WORKFLOW type:
  ```python
  if self.node_type == NodeType.CHILD_WORKFLOW:
      return f"{self.node_id}[[{self.display_name}]]"  # Subroutine shape
  ```
- Extend MermaidRenderer to handle CHILD_WORKFLOW nodes
- Covers FR68

### Story 6.3: Implement Multi-Workflow Analysis Pipeline

**User Story:**
As a library user,
I want to analyze parent and child workflows together,
So that I can see the complete workflow call graph for my application.

**Acceptance Criteria:**

**Given** a parent workflow calls child workflows
**When** multi-workflow analysis is invoked
**Then** WorkflowCallGraphAnalyzer class exists in src/temporalio_graphs/call_graph.py
**And** analyzer accepts parent workflow file and discovers child workflows (FR69)
**And** analyzer recursively analyzes all referenced child workflow files
**And** analyzer builds workflow call graph showing parent-child relationships (FR71)
**And** analyzer handles workflow resolution:
  - Same directory as parent
  - Explicit file path mapping (configuration)
  - Import-based resolution
**And** analyzer detects circular workflow references and raises clear error
**And** analyzer creates separate WorkflowMetadata for each workflow
**And** WorkflowCallGraph dataclass contains all workflow metadata and relationships
**And** public API extended: `analyze_workflow_graph(parent_file: Path, workflow_paths: Optional[Dict[str, Path]] = None) -> WorkflowCallGraph`
**And** unit tests cover: parent + 1 child, parent + multiple children, multi-level hierarchy, circular reference detection
**And** integration test with 3-level workflow hierarchy

**Prerequisites:** Story 6.2 (Child workflow rendering works)

**Technical Notes:**
- New WorkflowCallGraphAnalyzer class
- WorkflowCallGraph dataclass:
  ```python
  @dataclass(frozen=True)
  class WorkflowCallGraph:
      workflows: Dict[str, WorkflowMetadata]  # workflow_name -> metadata
      call_relationships: List[Tuple[str, str]]  # (parent, child) edges
      root_workflow: str
  ```
- Recursive analysis with visited set to prevent infinite loops
- Covers FR69, FR71

### Story 6.4: Implement End-to-End Path Generation Across Workflows

**User Story:**
As a library user,
I want execution paths that span parent and child workflows,
So that I can understand complete end-to-end flow through my workflow system.

**Acceptance Criteria:**

**Given** workflow call graph with parent-child relationships exists
**When** path generation runs for multi-workflow graph
**Then** generator creates paths spanning parent and child workflows (FR70)
**And** child workflow execution is expanded inline in parent path
**And** path shows: Parent Start → Parent Activities → Child Workflow Start → Child Activities → Child Workflow End → Parent Continues → Parent End
**And** decision points in both parent and child create full permutations
**And** 2^(n_parent + n_child) total paths generated for independent decisions
**And** child workflow boundary is visually indicated in path
**And** max_paths limit applies to total cross-workflow paths
**And** performance: generates cross-workflow paths efficiently (< 5s for 10 total decisions)
**And** unit tests cover: linear parent with linear child, parent with decisions + child with decisions, multiple children
**And** integration test validates path count matches expected permutations

**Prerequisites:** Story 6.3 (Call graph analysis works), Story 3.3 (Path permutations)

**Technical Notes:**
- Extend PathPermutationGenerator for cross-workflow paths
- When encountering child workflow node:
  1. Generate all parent paths up to child call
  2. Generate all child workflow paths
  3. Cross product: parent_paths_before × child_paths × parent_paths_after
- Inline expansion strategy:
  ```python
  path: Start → Activity1 → [ChildStart → ChildActivity → ChildEnd] → Activity2 → End
  ```
- Covers FR70

### Story 6.5: Add Integration Test with Parent-Child Workflow Example

**User Story:**
As a library user,
I want a complete parent-child workflow example,
So that I can understand how to visualize multi-workflow applications.

**Acceptance Criteria:**

**Given** cross-workflow support is fully implemented
**When** parent-child example is analyzed
**Then** examples/parent_child_workflow/ exists (FR73)
**And** example includes: parent_workflow.py, child_workflow.py, run.py, expected_output.md
**And** parent workflow calls child workflow with execute_child_workflow
**And** parent has 1 decision point, child has 1 decision point (4 total paths)
**And** analyze_workflow_graph() produces valid Mermaid with subroutine nodes
**And** generated diagram shows clear parent-child relationship (FR72)
**And** example demonstrates navigation between parent and child graphs
**And** tests/integration/test_parent_child.py validates output
**And** test validates path count (4 paths for 2 independent decisions)
**And** test validates child workflow nodes use [[ ]] syntax
**And** example is documented in README
**And** integration test passes with 100% accuracy

**Prerequisites:** Story 6.4 (Cross-workflow path generation works)

**Technical Notes:**
- Example workflow structure:
  ```python
  # parent_workflow.py
  @workflow.defn
  class OrderWorkflow:
      @workflow.run
      async def run(self, order: Order) -> str:
          await workflow.execute_activity(validate_order, ...)

          if await to_decision(order.amount > 1000, "HighValue"):
              await workflow.execute_activity(manager_approval, ...)

          # Call child workflow
          await workflow.execute_child_workflow(PaymentWorkflow, ...)

          await workflow.execute_activity(ship_order, ...)
          return "complete"

  # child_workflow.py
  @workflow.defn
  class PaymentWorkflow:
      @workflow.run
      async def run(self, payment: Payment) -> str:
          await workflow.execute_activity(process_payment, ...)

          if await to_decision(payment.requires_3ds, "Requires3DS"):
              await workflow.execute_activity(verify_3ds, ...)

          return "paid"
  ```
- Expected: 4 paths (2^2 decisions: parent decision × child decision)
- Covers FR72, FR73

---

## FR Coverage Matrix

Complete mapping of all 73 FRs to specific stories:

| FR | Description | Epic.Story | Notes |
|----|-------------|------------|-------|
| FR1 | Parse Python workflow source files using AST | 2.2 | WorkflowAnalyzer |
| FR2 | Detect @workflow.defn and @workflow.run decorators | 2.2 | AST visitor pattern |
| FR3 | Identify activity calls | 2.3 | Activity detector |
| FR4 | Extract activity names | 2.3 | From execute_activity args |
| FR5 | Detect decision points | 3.1 | DecisionDetector |
| FR6 | Generate 2^n path permutations | 3.3 | PathPermutationGenerator |
| FR7 | Track execution paths | 2.4 | GraphPath class |
| FR8 | Output Mermaid flowchart syntax | 2.5 | MermaidRenderer |
| FR9 | Generate Start and End nodes | 2.4 | Node creation |
| FR10 | Deduplicate path segments | 2.5 | Renderer deduplication |
| FR11 | to_decision() helper function | 3.2 | Workflow helper |
| FR12 | Custom decision names | 3.1, 3.2 | Name parameter |
| FR13 | Custom branch labels | 3.3 | Configuration |
| FR14 | Diamond decision shapes | 3.4 | Mermaid syntax |
| FR15 | 2 branches per decision | 3.3 | True/false paths |
| FR16 | Nested decision permutations | 3.3 | Combinatorial generation |
| FR17 | Decision ID preservation | 3.4 | ID generation |
| FR18 | wait_condition() wrapper | 4.2 | Signal helper |
| FR19 | Custom signal names | 4.1, 4.2 | Name parameter |
| FR20 | Hexagon signal shapes | 4.3 | Mermaid syntax |
| FR21 | Signaled/Timeout outcomes | 4.3 | Branch labels |
| FR22 | Signal path integration | 4.3 | Permutation logic |
| FR23 | Complete Mermaid markdown | 2.5 | Fenced code blocks |
| FR24 | Path list output | 5.3 | Text format |
| FR25 | Warn unreachable activities | 5.1 | Validation |
| FR26 | Warn unused activities | 5.1 | Validation |
| FR27 | Validation reports | 5.1 | Warning list |
| FR28 | Configurable output | 2.7 | Context options |
| FR29 | Node name formatting | 2.5, 2.7 | Word splitting |
| FR30 | Write to file or return string | 2.6 | Output handling |
| FR31 | GraphBuildingContext configuration | 2.1, 2.7 | Dataclass |
| FR32 | Enable/disable warnings | 2.7, 5.1 | suppress_validation |
| FR33 | Custom Start node label | 2.7 | Configuration |
| FR34 | Custom End node label | 2.7 | Configuration |
| FR35 | Control name splitting | 2.7 | Configuration |
| FR36 | Control decision ID format | 2.7 | Configuration |
| FR37 | Clean public API exports | 2.6 | __init__.py |
| FR38 | GraphPath class | 2.1 | Data model |
| FR39 | GraphGenerator class | 2.4 | Path generation |
| FR40 | Complete type hints | 2.1, 2.2, all stories | Mypy strict |
| FR41 | Docstrings with examples | All stories | Google style |
| FR42 | Analyze without modifying code | 2.2 | Static analysis |
| FR43 | Handle async workflows | 2.2, 3.2, 4.2 | Async support |
| FR44 | Clear exceptions | 2.6, 5.2 | Error handling |
| FR45 | Handle if/else conditionals | 3.1 | Pattern support |
| FR46 | Handle elif chains | 3.1 | Multiple decisions |
| FR47 | Handle ternary operators | 3.1 | IfExp nodes |
| FR48 | Handle sequential activities | 2.3, 2.4 | Linear paths |
| FR49 | Handle reconverging branches | 3.3 | Path generation |
| FR50 | Handle linear workflows | 2.4, 2.8 | No decisions |
| FR51 | Valid Mermaid syntax | 2.5 | Format compliance |
| FR52 | Match .NET output | 2.5, 3.5 | Regression tests |
| FR53 | Mermaid naming conventions | 2.5 | Node IDs |
| FR54 | Edge label syntax | 2.5 | Arrow format |
| FR55 | Decision format matches .NET | 3.4 | Diamond syntax |
| FR56 | MoneyTransfer example | 3.5 | .NET port |
| FR57 | MoneyTransfer demonstrates all features | 3.5 | Integration test |
| FR58 | Simple linear example | 2.8 | Basic workflow |
| FR59 | Multi-decision example | 5.4 | 3+ decisions |
| FR60 | Quick start guide <10 lines | 2.6, 5.5 | README |
| FR61 | Clear parse error messages | 2.2, 5.2 | WorkflowParseError |
| FR62 | Warn complex patterns | 5.2 | UnsupportedPatternError |
| FR63 | Suggestions for unsupported patterns | 5.2 | Error messages |
| FR64 | Handle missing decorators | 2.2 | Validation |
| FR65 | Validate helper function usage | 5.2 | InvalidDecisionError |
| FR66 | Detect child workflow calls | 6.1 | execute_child_workflow detection |
| FR67 | Extract child workflow class names | 6.1 | AST argument extraction |
| FR68 | Render child workflow nodes distinctly | 6.2 | Subroutine shape [[ ]] |
| FR69 | Analyze multiple workflows together | 6.3 | WorkflowCallGraphAnalyzer |
| FR70 | Generate end-to-end cross-workflow paths | 6.4 | Path spanning parent + child |
| FR71 | Render workflow call graphs | 6.3 | Parent-child relationships |
| FR72 | Child workflow node navigation/linking | 6.5 | Graph references |
| FR73 | Parent-child workflow example | 6.5 | Integration example |

**All 73 FRs mapped to implementation stories.**
**Core MVP (65 FRs):** FR1-FR65 across Epics 1-5
**MVP Extension (8 FRs):** FR66-FR73 in Epic 6

---

## Summary

### Epic Breakdown Complete

✅ **6 Epics Created:**
1. Foundation & Project Setup (1 story)
2. Basic Graph Generation (8 stories)
3. Decision Node Support (5 stories)
4. Signal & Wait Condition Support (4 stories)
5. Production Readiness (5 stories)
6. Cross-Workflow Visualization (5 stories) - MVP Extension

✅ **28 Stories Total** - Each sized for single dev agent completion

✅ **73 FRs Fully Covered** - All functional requirements mapped to stories
  - Core MVP: 65 FRs (Epics 1-5)
  - Extension: 8 FRs (Epic 6)

✅ **Architecture Integrated** - Static analysis approach, uv, mypy strict, src/ layout, performance targets

✅ **User Value Validated** - Each epic delivers incremental capability:
- Epic 1: Project foundation (greenfield exception)
- Epic 2: **Visualize linear workflows** (core value delivered)
- Epic 3: **Visualize branching workflows** (decision support added)
- Epic 4: **Visualize wait conditions** (signal support added)
- Epic 5: **Production-grade library** (robust, documented, tested) - v0.1.0 Core MVP
- Epic 6: **Visualize multi-workflow systems** (parent-child workflows, end-to-end flows) - v0.2.0 MVP Extension

### Context Incorporated

**From PRD:**
- 73 FRs provide strategic WHAT (capabilities exist) - 65 Core MVP + 8 Cross-Workflow Extension
- Success criteria, NFRs, and project classification inform acceptance criteria
- .NET feature parity ensures completeness, with Python-specific extension for cross-workflow visualization

**From Architecture:**
- Static analysis approach (ADR-001) drives AST-based implementation
- uv package manager (ADR-002) used in Story 1.1
- hatchling build backend (ADR-003) in project initialization
- src/ layout (ADR-004) for project structure
- mypy strict mode (ADR-006) for type safety in all stories
- ruff for linting/formatting (ADR-007)
- Path explosion limit (ADR-008) in Story 3.3
- Google-style docstrings (ADR-009) in all stories
- >80% coverage requirement (ADR-010) in test acceptance criteria

**Epic Stories Add Tactical HOW:**
- Exact function signatures and class structures
- Specific AST patterns to detect (visit_ClassDef, visit_Call, etc.)
- Performance targets (<1ms parsing, 2^n permutations in <5s)
- Test coverage requirements (100% for core logic)
- Error message formats with line numbers and suggestions
- Integration test specifications with golden file comparisons

### Next Steps

1. ✅ **PRD Validated** - All requirements captured
2. ✅ **Architecture Complete** - Technical decisions documented
3. ✅ **Epic Breakdown Complete** - This document
4. **Ready for Phase 4: Sprint Planning** - Use `/bmad:bmm:workflows:sprint-planning` workflow
5. **Implementation** - Use `/bmad:bmm:workflows:create-story` for each story, then `/bmad:bmm:workflows:dev-story` to implement

**Development Sequence:**

**Phase 1 - Core MVP (v0.1.0):**
- Epic 1 → Epic 2 → Epic 3 → Epic 4 → Epic 5
- Epic 2 stories must be sequential (2.1→2.2→2.3→2.4→2.5→2.6→2.7→2.8)
- Epic 3 can partially overlap Epic 2 after Story 2.3
- Epic 4 follows similar pattern to Epic 3
- Epic 5 stories can partially parallel

**Phase 2 - MVP Extension (v0.2.0):**
- Epic 6 (after Epic 5 complete)
- Epic 6 stories must be sequential (6.1→6.2→6.3→6.4→6.5)
- Builds on Epic 2 (AST analysis) and Epic 3 (path permutations) patterns
- Deliverable: Complete cross-workflow visualization capability

---

_Epic breakdown created for temporalio-graphs-python-port - Python library for complete workflow visualization using static code analysis._

_Generated using BMM Epic and Story Decomposition Workflow - 2025-11-18_

_For implementation: Use the `create-story` workflow to generate individual story implementation plans from this epic breakdown._
