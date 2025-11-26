# temporalio-graphs-python-port - Product Requirements Document

**Author:** Luca
**Date:** 2025-11-18
**Version:** 1.0

---

## Executive Summary

Port the .NET Temporalio.Graphs library to Python, providing Python developers with the same capability to generate complete workflow visualization diagrams from Temporal workflows.

**The Problem:**
Temporal workflows don't provide visualization of all possible execution paths. Unlike DAG-based workflow engines with upfront graph definitions, Temporal's flexible architecture only shows executed steps (Timeline View), not the complete workflow structure. This creates a capability gap when teams need to understand, document, or review all possible execution branches before/without running the workflow.

**The Solution:**
A Python library (`temporalio-graphs`) that analyzes workflow source code using Python AST (Abstract Syntax Tree) to generate Mermaid diagrams showing ALL possible execution paths. Unlike history-based tools that only show executed paths, this library generates the complete 2^n permutation space for n decision points.

**Why Python Needs This:**
The .NET Temporal ecosystem already has this capability. Python developers deserve feature parity. This port brings proven functionality to Python using an architecture validated by the Phase 0.5 spike - static code analysis instead of .NET's runtime interceptor approach.

### What Makes This Special

**Complete Path Visualization Without Execution:**
Existing Python tools (like Temporal Diagram Generator) parse workflow execution history - they only show paths that were actually taken. This library generates ALL possible execution paths through static code analysis, without running the workflow. For a workflow with 3 decisions, it shows all 8 (2^3) paths.

**Proven .NET Model, Python Innovation:**
Functionally equivalent to the .NET version (already endorsed on Temporal's Code Exchange), but architecturally superior - no runtime mocking needed, faster analysis (<1ms vs seconds), simpler integration.

**Decision Nodes & Signals:**
Handles workflow patterns not natively visualized by Temporal: decision points (if/else branches) and signal nodes (wait_condition), making the graph truly complete.

---

## Project Classification

**Technical Type:** developer_tool (Python library/package)
**Domain:** general
**Complexity:** low

**Classification Rationale:**
This is a developer tool - specifically a Python library distributed via PyPI. Target users are Python developers working with Temporal workflows who need visualization capabilities. Domain is general software development (not regulated/specialized). Technical complexity is manageable - Python AST parsing is well-documented, and the spike validated the approach.

---

## Success Criteria

**Feature Parity with .NET Version:**
- Generates identical Mermaid diagram structure for equivalent workflows
- Supports all .NET features: decision nodes, signals, path listing, validation warnings
- API is Pythonic but functionally equivalent to .NET's `GraphBuildingContext`

**Technical Quality:**
- MoneyTransfer example workflow produces expected Mermaid output
- >80% unit test coverage
- Type-safe API (passes mypy strict mode)
- Performance: <1 second for workflows with 5 decision points (32 paths)

**Developer Experience:**
- Simple integration: `pip install temporalio-graphs`
- Clear documentation with working examples
- Intuitive API matching Python conventions
- Comprehensive error messages for unsupported patterns

**Deliverables:**
- PyPI-ready package (`temporalio-graphs`)
- Complete test suite (unit + integration)
- Working MoneyTransfer example
- README with quick start guide
- API reference documentation

---

## Product Scope

### MVP - Core (v0.1.0)

**Core Graph Generation (Match .NET Core Features):**
- Parse Python workflow source files using AST
- Detect activity calls (`workflow.execute_activity()`)
- Identify decision points (if/else, ternary operators)
- Generate 2^n path permutations for n decisions
- Output Mermaid flowchart syntax
- Support decision nodes with `to_decision()` helper
- Support signal nodes with `wait_condition()` wrapper
- Generate execution path list (all unique paths)
- Validation warnings (e.g., unreachable activities)

**Python Package Structure:**
- Installable via `pip install temporalio-graphs`
- Core classes: `GraphBuildingContext`, `GraphPath`, `GraphGenerator`
- Workflow helpers: `to_decision()`, `wait_condition()`
- Clean public API with type hints
- Configuration options matching .NET (split names, suppress validation, etc.)

**Documentation & Examples:**
- README with installation and quick start
- MoneyTransfer workflow example (port from .NET)
- API reference for core classes
- Integration guide

**Quality:**
- >80% test coverage
- Working MoneyTransfer example producing expected output
- Type-safe (mypy strict)

### MVP Extension (v0.2.0) - Cross-Workflow Support

**Cross-Workflow Visualization (Epic 6):**
- Detect child workflow calls (`workflow.execute_child_workflow()`)
- Render child workflow nodes in Mermaid diagrams
- Analyze multiple related workflows as a call graph
- Generate end-to-end execution paths spanning parent and child workflows
- Support workflow composition patterns (parent → child relationships)

**Examples & Documentation:**
- Parent-child workflow example (`examples/parent_child_workflow/`)
- Updated README with cross-workflow usage
- Extended API reference for multi-workflow analysis

**Version Timeline:**
- v0.1.0 (Core MVP): Epics 1-5, single-workflow analysis (65 FRs)
- v0.2.0 (MVP Extension): Epic 6, cross-workflow support (+8 FRs, total 73 FRs)
- Delivery: v0.2.0 releases ~1 week after v0.1.0

### Growth Features (Post-MVP)

**Advanced Workflow Patterns:**
- Nested conditionals (complex branching)
- Loop detection and visualization (while/for)
- Dynamic activity registration
- Exception handling paths (try/except branches)

**CLI Enhancements:**
- Command-line interface: `temporalio-graphs analyze workflow.py --output diagram.md`
- Batch processing (analyze multiple workflows)
- Configuration file support (`.temporalio-graphs.yaml`)
- Multiple output formats (Mermaid, DOT, PlantUML, JSON)

**Developer Experience:**
- VS Code extension for inline visualization
- Jupyter notebook integration (display graphs in cells)
- Pre-commit hook for auto-generating workflow docs
- GitHub Action for CI/CD integration

**Analysis Features:**
- Complexity metrics (cyclomatic complexity, path count)
- Coverage analysis (which paths have tests)
- Performance estimation (activity counts per path)

### Vision (Future)

**Interactive Visualization:**
- Web UI for interactive graph exploration (port .NET sample)
- Click on nodes to see activity details
- Highlight specific execution paths
- Compare graphs between versions (diff visualization)

**Runtime Integration:**
- Dynamic graph generation from running workflows
- Overlay current execution state on complete graph
- Real-time path highlighting during execution
- Integration with Temporal Web UI

**AI-Assisted Analysis:**
- Natural language workflow documentation generation
- Suggest workflow optimizations based on graph structure
- Identify potential deadlocks or infinite loops
- Generate test cases for untested paths

**Ecosystem Integration:**
- Direct integration with Temporal Cloud
- Plugin for popular Python IDEs (PyCharm, VS Code)
- Integration with documentation generators (Sphinx, MkDocs)
- OpenAPI-style workflow specification generation

---

## Developer Tool Specific Requirements

**Language & Platform:**
- Python 3.10+ required (3.11+ recommended for best performance)
- Cross-platform (Windows, macOS, Linux)
- No platform-specific dependencies

**Package Distribution:**
- PyPI distribution as `temporalio-graphs`
- Semantic versioning (SemVer)
- Changelog maintained for each release
- Installation via pip/uv/poetry

**API Design:**
- Pythonic naming conventions (snake_case functions, PascalCase classes)
- Type hints for all public APIs (PEP 484)
- Docstrings following Google/NumPy style
- No breaking changes without major version bump

**Documentation Requirements:**
- README.md with badges (PyPI version, test coverage, license)
- Quick start example (<10 lines of code to first graph)
- API reference (auto-generated from docstrings)
- Migration guide from .NET version (key API differences)
- Example gallery (simple, intermediate, complex workflows)
- Troubleshooting guide (common issues, unsupported patterns)

**Integration:**
- Works with Temporal SDK 1.7.1+ (specify supported versions)
- No modifications to user workflow code required (except adding helpers for decisions)
- Compatible with popular Python tools (pytest, mypy, ruff, black)
- Async-compatible (doesn't block event loops)

**Developer Experience:**
- Clear error messages with actionable suggestions
- Warning for unsupported workflow patterns (with workarounds)
- Validation mode (dry-run to check compatibility)
- Verbose mode for debugging AST parsing
- Configuration via code or config file

**Code Quality:**
- Type checking: mypy strict mode passes
- Linting: ruff clean (no violations)
- Formatting: consistent style (black/ruff compatible)
- Security: no known vulnerabilities (automated scanning)
- License: MIT (matching .NET version)

---

## Functional Requirements

### Core Graph Generation

**FR1:** Library can parse Python workflow source files using AST analysis
**FR2:** Library can detect `@workflow.defn` decorated classes and `@workflow.run` methods
**FR3:** Library can identify activity calls (`workflow.execute_activity()`)
**FR4:** Library can extract activity names from `execute_activity()` calls
**FR5:** Library can detect decision points (if/else statements, ternary operators)
**FR6:** Library can generate 2^n execution path permutations for n independent decision points
**FR7:** Library can track execution paths as sequences of activity names and decision nodes
**FR8:** Library can output graph definitions in Mermaid flowchart syntax
**FR9:** Library can generate Start and End nodes with configurable labels
**FR10:** Library can deduplicate identical path segments in graph output

### Decision Node Support

**FR11:** Users can mark boolean expressions as decision nodes using `to_decision()` helper function (synchronous, no await needed)
**FR12:** Decision nodes can have custom display names
**FR13:** Decision nodes can have custom true/false branch labels (default: "yes"/"no")
**FR14:** Decision nodes render in Mermaid as diamond shapes (`{decision}`)
**FR15:** Each decision node generates exactly 2 branches (true/false paths)
**FR16:** Nested decisions create proper path permutations (2^n total paths)
**FR17:** Decision IDs can be preserved or simplified (numeric) based on configuration

### Signal/Wait Condition Support

**FR18:** Users can mark wait conditions as signal nodes using `wait_condition()` wrapper
**FR19:** Signal nodes can have custom names for graph display
**FR20:** Signal nodes render in Mermaid as hexagon shapes (`{{signal}}`)
**FR21:** Signal nodes have two outcomes: "Signaled" and "Timeout"
**FR22:** Signal nodes integrate into path permutation generation

### Graph Output

**FR23:** Library can generate complete Mermaid markdown with fenced code blocks
**FR24:** Library can generate a list of all unique execution paths (text format)
**FR25:** Library can identify and warn about unreachable activities
**FR26:** Library can identify and warn about activities defined but never called
**FR27:** Library can generate validation reports listing warnings
**FR28:** Users can configure output to Mermaid-only (suppress path list and warnings)
**FR29:** Users can configure node name formatting (split camelCase into "Camel Case")
**FR30:** Library can write output to specified file path or return as string

### Configuration & Control

**FR31:** Users can configure graph generation through `GraphBuildingContext` dataclass
**FR32:** Users can enable/disable validation warnings
**FR33:** Users can customize Start node label/format
**FR34:** Users can customize End node label/format
**FR35:** Users can control node name word-splitting behavior
**FR36:** Users can control decision ID preservation (hash vs numeric)

### API & Integration

**FR37:** Library exports clean public API: `analyze_workflow`, `GraphBuildingContext`, `to_decision`, `wait_condition`
**FR38:** Library provides `GraphPath` class for tracking execution paths
**FR39:** Library provides `GraphGenerator` class for rendering graphs
**FR40:** All public APIs have complete type hints (mypy strict compatible)
**FR41:** All public functions have docstrings with usage examples
**FR42:** Library can analyze workflows without modifying user workflow code (except adding decision/signal helpers)
**FR43:** Library can handle async workflow methods
**FR44:** Library raises clear exceptions for unsupported workflow patterns

### Advanced Patterns (MVP Scope)

**FR45:** Library can handle simple if/else conditionals
**FR46:** Library can handle elif chains (multiple decision points)
**FR47:** Library can handle ternary operators as decision points
**FR48:** Library can handle sequential activity calls (linear paths)
**FR49:** Library can handle parallel branches that reconverge (linearized for MVP)
**FR50:** Library can handle workflows with no decision points (linear flow)

### Output Format Compliance

**FR51:** Generated Mermaid syntax is valid and renders correctly in Mermaid editors
**FR52:** Graph structure matches .NET Temporalio.Graphs output for equivalent workflows
**FR53:** Node naming follows Mermaid naming conventions
**FR54:** Edge labels follow Mermaid syntax (`-- label -->`)
**FR55:** Decision node format matches .NET output structure

### Examples & Documentation

**FR56:** Library includes working MoneyTransfer workflow example (ported from .NET)
**FR57:** MoneyTransfer example demonstrates decision nodes, signal nodes, and multiple paths
**FR58:** Library includes simple linear workflow example
**FR59:** Library includes multi-decision workflow example
**FR60:** README provides quick start guide with <10 lines of example code

### Error Handling

**FR61:** Library provides clear error messages when workflow file cannot be parsed
**FR62:** Library warns when workflow patterns are too complex to analyze
**FR63:** Library provides suggestions when unsupported patterns are detected
**FR64:** Library gracefully handles missing/invalid workflow decorators
**FR65:** Library validates that decision helper functions are used correctly
**FR66:** Library raises UnsupportedPatternError for loops (while/for) in MVP

### Cross-Workflow Visualization (Epic 6)

**FR67:** Library can detect child workflow calls (`workflow.execute_child_workflow()`) in workflow source code
**FR68:** Library can extract child workflow type/class from `execute_child_workflow()` call arguments
**FR69:** Child workflow nodes render as distinct nodes in Mermaid diagrams (using subgraph or special notation)
**FR70:** Child workflow nodes display the workflow type name in the graph
**FR71:** Library can analyze multiple related workflows in a single operation (multi-workflow analysis pipeline)
**FR72:** Library can build workflow call graphs showing parent-child relationships
**FR73:** Library can generate end-to-end execution paths that span parent and child workflows
**FR74:** Library includes working parent-child workflow example demonstrating cross-workflow visualization

### Peer-to-Peer Signal Visualization (Epic 7)

**FR75:** Library can detect `workflow.get_external_workflow_handle()` calls in workflow source code
**FR76:** Library can detect `.signal()` method calls on external workflow handles
**FR77:** Library can extract signal names from `.signal(signal_name, payload)` arguments
**FR78:** Library can extract target workflow patterns from handle creation (string literals, format strings, dynamic)
**FR79:** External signal nodes render as trapezoid shapes in Mermaid: `[/SignalName\]`
**FR80:** External signal edges render as dashed lines: `-.signal.->`
**FR81:** Library includes working Order --> Shipping peer signal workflow example

### Cross-Workflow Signal Visualization (Epic 8)

**FR82:** Library can detect `@workflow.signal` decorated methods in workflow classes (signal handlers)
**FR83:** Library can extract signal name from decorator (explicit name or method name as default)
**FR84:** Library can resolve external signals to target workflows by matching signal names to handlers
**FR85:** Library can scan configurable search paths for workflow files to build signal handler index
**FR86:** Library can build cross-workflow signal graph from entry point with recursive discovery
**FR87:** Library handles circular signal dependencies (detect, record connection, don't re-analyze)
**FR88:** Cross-workflow diagrams render as Mermaid subgraphs with signal handlers as hexagon nodes
**FR89:** Signal connections render as dashed edges between subgraphs
**FR90:** Library provides `analyze_signal_flow()` function for cross-workflow signal visualization

---

**Total Functional Requirements:** 90

These FRs ensure feature parity with the .NET version while accounting for Python-specific architecture (static analysis vs runtime interceptors).

---

## Non-Functional Requirements

### Performance

**NFR-PERF-1: Analysis Speed**
- AST parsing and graph generation completes in <1 second for workflows with up to 5 decision points (32 paths)
- No execution required - pure static analysis
- Target: <0.001 seconds for simple workflows (validated by spike)
- Target: <5 seconds for complex workflows (10 decision points, 1024 paths)

**NFR-PERF-2: Memory Efficiency**
- Library uses <100MB memory for analyzing typical workflows
- No memory leaks during repeated analysis
- Path explosion safeguards prevent runaway memory use (max paths limit)

**NFR-PERF-3: Startup Time**
- Package import time <500ms
- No heavy initialization on import
- Lazy loading for optional features

### Code Quality

**NFR-QUAL-1: Type Safety**
- 100% type hint coverage for public APIs
- Passes mypy --strict with no errors or type: ignore comments
- Type stubs (.pyi files) generated if needed

**NFR-QUAL-2: Test Coverage**
- >80% unit test coverage (measured by pytest-cov)
- 100% coverage for core graph generation logic
- Integration tests for all examples
- Regression tests comparing output with .NET version

**NFR-QUAL-3: Code Style**
- Passes ruff check with no violations
- Consistent formatting (ruff format)
- Clear, readable code with appropriate comments
- Docstrings for all public classes/functions

**NFR-QUAL-4: Security**
- No known security vulnerabilities (automated scanning)
- Safe file I/O (proper path validation)
- No arbitrary code execution risks
- Dependency security audit passes

### Reliability

**NFR-REL-1: Correctness**
- MoneyTransfer example produces output structurally identical to .NET version
- All permutations correctly generated (no missing or duplicate paths)
- Mermaid syntax validates in all standard Mermaid renderers

**NFR-REL-2: Error Handling**
- No silent failures - all errors reported clearly
- Graceful degradation for unsupported patterns
- Comprehensive exception hierarchy
- Stack traces useful for debugging

**NFR-REL-3: Stability**
- No crashes on malformed workflow code
- Handles edge cases (empty workflows, no activities, etc.)
- Thread-safe if used in multi-threaded context
- No side effects (pure analysis, doesn't modify inputs)

### Usability

**NFR-USE-1: API Intuitiveness**
- Pythonic API matching community conventions
- Function names clearly indicate purpose
- Sensible defaults (minimal configuration required)
- Type hints enable IDE autocomplete

**NFR-USE-2: Error Messages**
- Clear, actionable error messages
- Include suggestions for fixing common issues
- Reference documentation for complex errors
- No technical jargon in user-facing messages

**NFR-USE-3: Documentation Quality**
- README understandable by Python developers familiar with Temporal
- Examples copy-paste ready (work without modification)
- API reference comprehensive and accurate
- Migration guide from .NET helps C# developers

### Compatibility

**NFR-COMPAT-1: Python Version Support**
- Officially supports Python 3.10, 3.11, 3.12
- Tested on all supported versions in CI
- Clear documentation of minimum version and reason
- No use of features from unreleased Python versions

**NFR-COMPAT-2: Temporal SDK Compatibility**
- Works with Temporal SDK 1.7.1+ (specified in dependencies)
- Documents breaking changes between SDK versions
- Warns if incompatible SDK version detected
- Pin SDK version in tests for reproducibility

**NFR-COMPAT-3: Platform Support**
- Works on Linux, macOS, Windows
- No platform-specific code without fallbacks
- CI testing on all major platforms
- Path handling uses pathlib (cross-platform)

**NFR-COMPAT-4: Dependency Minimalism**
- Only required dependency: `temporalio` SDK
- No large transitive dependencies
- Development dependencies clearly separated
- Optional dependencies for extra features (if any)

### Maintainability

**NFR-MAINT-1: Code Organization**
- Clear module structure following best practices
- Single Responsibility Principle for classes
- Logical file organization
- Internal APIs clearly distinguished from public

**NFR-MAINT-2: Testing Infrastructure**
- Fast test suite (<30 seconds for all tests)
- Tests are deterministic (no flakiness)
- Easy to add new test cases
- Golden file fixtures for regression testing

**NFR-MAINT-3: CI/CD**
- Automated testing on every commit
- Automated linting and type checking
- Automated security scanning
- Automated PyPI publishing (tagged releases)

---

_This PRD captures the essence of temporalio-graphs-python-port - bringing complete workflow visualization to the Python Temporal ecosystem through static code analysis, matching the proven .NET implementation with Python-native architecture._

_Created for bounty implementation - based on .NET Temporalio.Graphs reference and validated Phase 0.5 architecture spike._

---

## Reference Materials

- **.NET Implementation:** `/Users/luca/dev/bounty/Temporalio.Graphs`
- **Implementation Plan:** `/Users/luca/dev/bounty/IMPLEMENTATION_PLAN.md` (15.5-hour phased approach)
- **Architecture Spike:** `/Users/luca/dev/bounty/spike/EXECUTIVE_SUMMARY.md` (validates static analysis approach)
- **Spike Code:** `/Users/luca/dev/bounty/spike/temporal-spike/approach3_static_analysis.py`
- **Project Status:** Phase 0.5 complete, ready for Phase 1 implementation

## Next Steps

1. **Validate PRD** - Review this document for completeness
2. **Create Architecture Document** - Technical design based on static analysis approach
3. **Generate Epic Breakdown** - Break down 65 FRs into implementable epics and stories
4. **Begin Phase 1** - Foundation implementation per IMPLEMENTATION_PLAN.md
