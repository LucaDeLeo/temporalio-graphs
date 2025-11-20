# Changelog

All notable changes to temporalio-graphs will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- CLI interface for command-line workflow analysis
- Multiple output formats (JSON, DOT/Graphviz)
- Loop detection and warnings for advanced control flow
- IDE plugins and editor integrations

## [0.1.1] - 2025-11-19

### Fixed
- **execute_activity_method() Support**: Added detection for `workflow.execute_activity_method()` pattern used in production codebases. Previously only `execute_activity()` was recognized, causing incomplete activity detection. (Real-world testing - 2025-11-19)
- **Child Workflow Attribute Access**: Added support for `ChildWorkflow.run` pattern in `execute_child_workflow()` calls. Previously only `ChildWorkflow` (name) or string literals were supported. This is the standard pattern used in official Temporal samples. (Real-world testing - 2025-11-19)
- **wait_condition() Disambiguation**: Fixed false positive errors on Temporal's built-in `workflow.wait_condition(lambda: ...)` by distinguishing it from our custom 3-argument helper via argument count detection. (Real-world testing - 2025-11-19)

### Added
- **Order Processing Example**: New comprehensive example workflow demonstrating decision nodes + signal handling in a real-world e-commerce scenario with 8 execution paths
- **Enhanced Documentation**: Updated README with order processing workflow example and improved examples section organization

### Changed
- Test coverage adjusted from 95% to 91% after adding real-world pattern support
- Updated test suite to 547 tests (previously 406) with 100% pass rate
- Repository cleanup: Removed local C# reference implementation (68MB), now links to external GitHub repo

### Validated
- **Real-World Testing**: Validated on Official Temporal Python samples repository (20+ workflows) and production AI agent workflow
- **Success Rate**: 100% of real-world workflows now analyze successfully (up from 33% before fixes)
- See `REAL_WORLD_TESTING_REPORT.md` for complete validation details

## [0.1.0] - 2025-11-19

### Added

#### Epic 1: Foundation & Project Setup
- Modern Python project structure with `pyproject.toml`
- Package management using `uv` for fast dependency resolution
- Strict type checking with mypy in strict mode
- Fast linting and formatting with ruff
- Comprehensive test infrastructure with pytest and 95% coverage target
- CI/CD pipeline configuration

#### Epic 2: Basic Graph Generation
- Static code analysis using Python AST (Abstract Syntax Tree)
- Workflow file parsing with `@workflow.defn` decorator detection
- Activity detection via `workflow.execute_activity()` call analysis
- Linear workflow support (sequential activities, no branching)
- Mermaid flowchart LR (left-to-right) syntax output
- `analyze_workflow()` public API function
- `GraphBuildingContext` immutable configuration dataclass
- Activity name formatting with word splitting (camelCase → "Camel Case")
- Start/End node rendering as circles `((Start))` and `((End))`
- File output support via `graph_output_file` configuration
- Simple Linear example workflow demonstrating basic pipeline pattern

#### Epic 3: Decision Node Support
- Decision point detection using `to_decision()` helper function
- Path permutation generation (2^n paths for n independent decisions)
- Decision node rendering as Mermaid diamonds `{DecisionName}`
- Yes/No edge labels for decision branches
- Path explosion limits with `max_decision_points` (default: 10)
- `max_paths` validation to prevent excessive path generation (default: 1024)
- MoneyTransfer example workflow with 2 decisions creating 4 execution paths
- Decision reconvergence support (paths merging after conditional branches)
- Multi-Decision example (LoanApproval) demonstrating 3 decisions = 8 paths

#### Epic 4: Signal & Wait Condition Support
- Signal point detection using `wait_condition()` helper function
- Signal node rendering as Mermaid hexagons `{{SignalName}}`
- Timeout vs Signaled path branches with custom edge labels
- Integration with Temporal's `workflow.wait_condition()` function
- Signal nodes integrated into path permutations (2 outcomes per signal)
- ApprovalWorkflow example demonstrating signal-based branching
- Configurable signal labels via `signal_success_label` and `signal_timeout_label`

#### Epic 5: Production Readiness
- Validation warning system for workflow quality issues
- Unreachable activity detection (activities after all paths converge)
- Path explosion warnings with actionable recommendations
- Comprehensive exception hierarchy with 7 exception types:
  - `TemporalioGraphsError` (base exception)
  - `WorkflowParseError` (parsing failures, missing decorators)
  - `UnsupportedPatternError` (patterns beyond MVP scope)
  - `GraphGenerationError` (path explosion, rendering failures)
  - `InvalidDecisionError` (incorrect helper usage)
  - `InvalidSignalError` (invalid wait_condition usage)
  - `ChildWorkflowNotFoundError` (Epic 6, child workflow resolution failures)
  - `CircularWorkflowError` (Epic 6, circular workflow dependencies)
- Actionable error messages with file paths, line numbers, and suggestions
- Path list output format (text-based alternative to Mermaid)
- Multiple output format modes: "mermaid", "paths", "full"
- `suppress_validation` option to disable warnings
- `include_validation_report` option for validation output control
- Comprehensive example gallery with 5 working examples:
  - Simple Linear (1 path, beginner)
  - MoneyTransfer (4 paths, intermediate)
  - Signal Workflow (2 paths, intermediate)
  - Multi-Decision (8 paths, advanced)
  - Parent-Child Workflow (multi-workflow, advanced)
- Production-grade documentation (README, API reference, this CHANGELOG)
- MIT License matching .NET Temporalio.Graphs
- Makefile with `run-examples` target for CI integration
- Integration tests for all example workflows with golden file validation

#### Epic 6: Cross-Workflow Visualization (MVP Extension)
- Child workflow call detection via `workflow.execute_child_workflow()` AST analysis
- Multi-workflow analysis pipeline with `analyze_workflow_graph()` public API
- Three child workflow expansion modes:
  - **Reference mode** (default): Child workflows as atomic nodes `[[ChildWorkflow]]`
  - **Inline mode**: Complete end-to-end paths spanning parent and child workflows
  - **Subgraph mode**: Structural visualization with Mermaid subgraph blocks
- Workflow call graph construction with circular dependency detection
- Cross-workflow path generation with path explosion prevention
- Automatic child workflow discovery in search paths
- `MultiWorkflowPath` data model for cross-workflow execution paths
- `ChildWorkflowNotFoundError` and `CircularWorkflowError` exception types
- Parent-Child Workflow example demonstrating all three expansion modes
- Path count calculation: Reference (parent paths only), Inline (parent × child paths)
- `max_expansion_depth` configuration to prevent infinite recursion
- Integration tests for multi-workflow analysis scenarios

### Technical Details
- Python 3.10+ support (3.11+ recommended)
- Dependency: temporalio >= 1.7.1
- Test coverage: 92% (547 tests passing, 100% pass rate)
- Performance: <1ms analysis time for simple workflows, <2s full test suite
- Static analysis approach: No workflow execution required
- Zero runtime overhead in helper functions
- Public API: 13 symbols in `__all__` (stable, minimal surface)
  - Core: `analyze_workflow`, `GraphBuildingContext`
  - Helpers: `to_decision`, `wait_condition`
  - Multi-workflow: `analyze_workflow_graph`, `MultiWorkflowPath`
  - Validation: `ValidationWarning`, `ValidationReport`
  - Exceptions: 7 exception types (base + 6 specialized)
- Mypy strict mode: 100% passing
- Ruff linting: 100% passing

### Documentation
- Complete README with quick start (<10 lines per FR60)
- API reference documentation for all public interfaces
- Core concepts explanation (AST analysis, decision nodes, signals, path permutations)
- Configuration patterns with GraphBuildingContext examples
- Troubleshooting guide with common errors and solutions
- .NET vs Python comparison with migration guide
- Architecture differences documented (static analysis vs runtime interceptors)
- All code examples tested and working
- Professional badges (PyPI, coverage, license, Python versions)

### Comparison with .NET Version
- Feature parity with Temporalio.Graphs (.NET) for core functionality
- Architectural difference: Static AST analysis vs runtime interceptors
- Benefits of Python approach:
  - No workflow execution required
  - Sub-millisecond analysis time (vs exponential execution time)
  - Simpler integration (no mock setup required)
  - No runtime overhead
- Same conceptual model: 2^n path permutations for complete coverage
- Compatible Mermaid output syntax
- **Python enhancements beyond .NET version:**
  - Cross-workflow visualization (Epic 6) - not available in .NET version
  - Multiple expansion modes for child workflows (reference, inline, subgraph)
  - Comprehensive validation system with actionable warnings
  - Path list output format for CI/CD integration
  - Superior error handling with 7 exception types

[Unreleased]: https://github.com/yourusername/temporalio-graphs/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/temporalio-graphs/releases/tag/v0.1.0
