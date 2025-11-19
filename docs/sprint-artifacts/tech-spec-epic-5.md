# Epic Technical Specification: Production Readiness

Date: 2025-11-19
Author: Luca
Epic ID: 5
Status: Draft

---

## Overview

This epic transforms the temporalio-graphs library from a functional prototype into a production-ready developer tool. It adds validation warnings to catch workflow quality issues (unreachable activities, unused code), implements a comprehensive error handling hierarchy with actionable messages, provides multiple output formats (path lists, validation reports), creates a complete example gallery demonstrating all library features, and delivers production-grade documentation enabling rapid adoption.

**Epic Goal:** Add validation, error handling, examples, and documentation for production use.

**Epic Value Statement:** Library is production-ready with comprehensive error messages, validation warnings, complete examples, and documentation. Users can confidently adopt the library knowing it has robust error handling and clear guidance for common use cases and troubleshooting.

**Strategic Context from PRD:**
- FR23-FR30: Graph output features (validation warnings, path lists, configurable output)
- FR56-FR60: Examples & documentation (MoneyTransfer, linear, multi-decision, README quick start)
- FR61-FR65: Error handling (clear parse errors, pattern warnings, suggestions, decorator validation)
- NFR-USE-2: Clear, actionable error messages with context
- NFR-USE-3: Documentation quality (understandable, copy-paste ready, comprehensive)

This epic completes the MVP by ensuring the library meets production quality standards. After Epic 5, the library is ready for PyPI publication and real-world adoption by Python developers in the Temporal community.

## Objectives and Scope

### In Scope

**Validation and Quality Warnings:**
- Detection of unreachable activities (defined but never called in any path)
- Detection of unused activities (called but results in dead code)
- Validation report generation with file paths, line numbers, and descriptions
- Configurable suppression of validation warnings via GraphBuildingContext
- Integration of warnings into standard output after Mermaid diagram

**Comprehensive Error Handling:**
- Complete exception hierarchy: TemporalioGraphsError base with specific subtypes
- WorkflowParseError for file parsing failures (missing decorators, syntax errors)
- UnsupportedPatternError for patterns beyond MVP scope (loops, dynamic activities)
- GraphGenerationError for path explosion and rendering failures
- InvalidDecisionError for incorrect helper function usage
- All exceptions include: file path, line number, error description, actionable suggestion
- Error messages in clear language without technical jargon

**Multiple Output Formats:**
- Text list of all execution paths (Path 1: Start → Activity1 → Activity2 → End)
- Numbered paths with decision outcomes visible
- Path list can be included with Mermaid output or returned separately
- Configurable output suppression for minimal Mermaid-only output
- File output support via GraphBuildingContext.graph_output_file

**Example Gallery:**
- Simple linear workflow example (already exists from Epic 2)
- MoneyTransfer workflow with decisions (already exists from Epic 3)
- Signal workflow with wait conditions (already exists from Epic 4)
- NEW: Multi-decision workflow example (3+ decisions, 8+ paths)
- Each example includes: workflow.py, run.py, expected_output.md
- All examples are runnable and CI-tested

**Production Documentation:**
- README.md with project overview, installation, quick start (<10 lines)
- PyPI badges: version, test coverage, license, Python versions
- API reference (auto-generated from docstrings or manual)
- Migration guide from .NET Temporalio.Graphs (architecture differences)
- Troubleshooting section: common errors, unsupported patterns, performance tips
- Changelog following Keep a Changelog format
- MIT license file (matching .NET version)

### Out of Scope

**Advanced Output Formats (Post-MVP):**
- JSON output format (nodes/edges as structured data)
- DOT format for Graphviz rendering
- PlantUML sequence diagram format
- Custom output format plugins

**Interactive Visualization (Vision):**
- Web UI for graph exploration
- Click-on-node details display
- Path highlighting and filtering
- Version diff visualization

**CLI Interface (Post-MVP):**
- Command-line tool: `temporalio-graphs analyze workflow.py`
- Batch processing for multiple workflows
- Configuration file support (.temporalio-graphs.yaml)

**Advanced Validation (Post-MVP):**
- Complexity metrics (cyclomatic complexity, path count statistics)
- Coverage analysis (which paths have tests)
- Performance estimation (activity counts per path)
- Deadlock or infinite loop detection

**IDE Integration (Vision):**
- VS Code extension for inline visualization
- PyCharm plugin support
- Jupyter notebook integration for interactive display

## System Architecture Alignment

**Builds on Epic 1-4 Foundation:**
- Uses existing GraphBuildingContext (Epic 2.1) for validation configuration
- Extends WorkflowAnalyzer (Epic 2.2) for validation logic
- Leverages PathPermutationGenerator (Epic 2.4, 3.3) for path coverage analysis
- Adds to MermaidRenderer (Epic 2.5) for path list formatting
- Exports new public APIs from __init__.py (Epic 2.6)

**Architecture Decisions Applied:**
- ADR-006 (mypy strict mode): All new code 100% typed
- ADR-007 (ruff): Linting/formatting for error handling and validation modules
- ADR-009 (Google-style docstrings): All examples and documentation
- ADR-010 (>80% coverage): Validation and error handling achieve 100% coverage

**Module Organization:**
- `src/temporalio_graphs/exceptions.py`: Complete exception hierarchy
- `src/temporalio_graphs/validator.py`: NEW - Validation logic for quality warnings
- `src/temporalio_graphs/formatter.py`: NEW - Path list and report formatting
- `examples/multi_decision/`: NEW - Complex workflow example
- `docs/api-reference.md`: NEW - API documentation
- `CHANGELOG.md`: NEW - Version history
- `LICENSE`: NEW - MIT license

**Performance Targets (NFR-PERF-1):**
- Validation adds <10ms overhead to analysis
- Path list generation <5ms for 100 paths
- Error message formatting <1ms per exception

**Integration Points:**
- Validation runs after path generation, before rendering
- Error handling wraps all major operations (parse, analyze, generate, render)
- Path list formatter integrates with MermaidRenderer output
- Examples are independent runnable scripts

## Detailed Design

### Services and Modules

| Module/Class | Responsibilities | Inputs | Outputs | Owner |
|--------------|------------------|--------|---------|-------|
| **exceptions.py** | Define exception hierarchy | Error context (file, line, message) | Formatted exception instances | Error Handling |
| TemporalioGraphsError | Base exception for all library errors | Exception message | Exception instance | Error Handling |
| WorkflowParseError | Parse failures (missing decorators, syntax) | File path, line, message, suggestion | Formatted error with context | Error Handling |
| UnsupportedPatternError | Unsupported workflow patterns (loops, dynamic) | Pattern name, suggestion | Formatted error with workaround | Error Handling |
| GraphGenerationError | Path explosion, rendering failures | Error type, context | Formatted error with limit info | Error Handling |
| InvalidDecisionError | Incorrect to_decision() or wait_condition() usage | Function name, issue, suggestion | Formatted error with fix | Error Handling |
| **validator.py** | Validate workflow quality, detect issues | WorkflowMetadata, list[GraphPath] | list[ValidationWarning] | Validation |
| WorkflowValidator | Main validation orchestrator | Metadata, paths, context | Validation report | Validation |
| UnreachableActivityDetector | Find activities defined but never called | All activities vs called activities | list[UnreachableWarning] | Validation |
| UnusedActivityDetector | Find activities with no downstream impact | Activity call graph | list[UnusedWarning] | Validation |
| ValidationWarning | Data model for validation issues | Type, location, description, severity | Warning instance | Validation |
| **formatter.py** | Format output (path lists, validation reports) | list[GraphPath], list[ValidationWarning] | Formatted strings | Output Formatting |
| PathListFormatter | Generate text list of all execution paths | list[GraphPath] | Multi-line path list string | Output Formatting |
| ValidationReportFormatter | Format validation warnings for display | list[ValidationWarning] | Formatted warning report | Output Formatting |
| **examples/multi_decision/** | Demonstrate complex workflow with 3+ decisions | N/A (example code) | Example workflow, output | Documentation |
| **docs/** | Production documentation suite | Library features, API signatures | Markdown documentation | Documentation |

**Module Dependencies:**
```
exceptions.py (no dependencies - base)
  ↑
validator.py (imports: exceptions, context, path, _internal/graph_models)
  ↑
formatter.py (imports: path, validator)
  ↑
renderer.py (extended to use formatter for path lists)
  ↑
analyze_workflow() (orchestrates validation + formatting)
```

### Data Models and Contracts

**Exception Hierarchy:**
```python
class TemporalioGraphsError(Exception):
    """Base exception for all library errors."""
    pass

class WorkflowParseError(TemporalioGraphsError):
    """Raised when workflow file cannot be parsed or analyzed."""
    def __init__(self, file_path: Path, line: int, message: str, suggestion: str):
        super().__init__(
            f"Cannot parse workflow file: {file_path}\n"
            f"Line {line}: {message}\n"
            f"Suggestion: {suggestion}"
        )
        self.file_path = file_path
        self.line = line
        self.message = message
        self.suggestion = suggestion

class UnsupportedPatternError(TemporalioGraphsError):
    """Raised when workflow uses patterns beyond MVP scope."""
    def __init__(self, pattern: str, suggestion: str, line: Optional[int] = None):
        msg = f"Unsupported pattern: {pattern}"
        if line:
            msg += f" at line {line}"
        msg += f"\nSuggestion: {suggestion}"
        super().__init__(msg)
        self.pattern = pattern
        self.suggestion = suggestion
        self.line = line

class GraphGenerationError(TemporalioGraphsError):
    """Raised when graph cannot be generated from workflow."""
    def __init__(self, reason: str, context: Optional[dict] = None):
        msg = f"Graph generation failed: {reason}"
        if context:
            msg += f"\nContext: {context}"
        super().__init__(msg)
        self.reason = reason
        self.context = context

class InvalidDecisionError(TemporalioGraphsError):
    """Raised when to_decision() or wait_condition() used incorrectly."""
    def __init__(self, function: str, issue: str, suggestion: str):
        super().__init__(
            f"Invalid {function} usage: {issue}\n"
            f"Suggestion: {suggestion}"
        )
        self.function = function
        self.issue = issue
        self.suggestion = suggestion
```

**Validation Data Models:**
```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class WarningSeverity(Enum):
    """Severity levels for validation warnings."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"  # Future: for critical issues

@dataclass
class ValidationWarning:
    """Represents a single validation issue."""
    severity: WarningSeverity
    category: str  # "unreachable", "unused", "complexity", etc.
    message: str
    file_path: Path
    line: Optional[int] = None
    activity_name: Optional[str] = None
    suggestion: Optional[str] = None

    def format(self) -> str:
        """Format warning for display."""
        icon = "⚠️" if self.severity == WarningSeverity.WARNING else "ℹ️"
        location = f"line {self.line}" if self.line else "unknown location"
        msg = f"{icon} [{self.category.upper()}] {self.message}"
        if self.activity_name:
            msg += f": '{self.activity_name}'"
        msg += f" at {location}"
        if self.suggestion:
            msg += f"\n   Suggestion: {self.suggestion}"
        return msg

@dataclass
class ValidationReport:
    """Complete validation results."""
    warnings: list[ValidationWarning]
    total_activities: int
    total_paths: int
    unreachable_count: int
    unused_count: int

    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

    def format(self) -> str:
        """Format full validation report."""
        if not self.has_warnings():
            return ""

        lines = [
            "\n--- Validation Report ---",
            f"Total Paths: {self.total_paths}",
            f"Total Activities: {self.total_activities}",
            f"Warnings: {len(self.warnings)}",
            ""
        ]
        for warning in self.warnings:
            lines.append(warning.format())
        return "\n".join(lines)
```

**Path List Data Structures:**
```python
@dataclass
class FormattedPath:
    """A single execution path formatted for display."""
    path_number: int
    activities: list[str]  # Activity names in order
    decisions: dict[str, bool]  # Decision name → outcome

    def format(self) -> str:
        """Format as: Path 1: Start → Activity1 → Activity2 → End"""
        steps = ["Start"] + self.activities + ["End"]
        return f"Path {self.path_number}: {' → '.join(steps)}"

@dataclass
class PathListOutput:
    """Complete path list with metadata."""
    paths: list[FormattedPath]
    total_paths: int
    total_decisions: int

    def format(self) -> str:
        """Format complete path list."""
        lines = [
            f"\n--- Execution Paths ({self.total_paths} total) ---"
        ]
        if self.total_decisions > 0:
            lines.append(f"Decision Points: {self.total_decisions} (2^{self.total_decisions} = {self.total_paths} paths)")
        lines.append("")

        for path in self.paths:
            lines.append(path.format())

        return "\n".join(lines)
```

**GraphBuildingContext Extensions:**
```python
# Additions to existing GraphBuildingContext (from Epic 2.1)
@dataclass(frozen=True)
class GraphBuildingContext:
    # ... existing fields ...
    suppress_validation: bool = False  # If True, skip validation warnings
    include_path_list: bool = True     # If True, include path list in output
    include_validation_report: bool = True  # If True, include validation report
    output_format: Literal["mermaid", "paths", "full"] = "full"  # Output mode
    # "mermaid": Just Mermaid diagram
    # "paths": Just path list
    # "full": Mermaid + paths + validation (default)
```

### APIs and Interfaces

**Public API Extensions:**
```python
# src/temporalio_graphs/__init__.py
from temporalio_graphs.exceptions import (
    TemporalioGraphsError,
    WorkflowParseError,
    UnsupportedPatternError,
    GraphGenerationError,
    InvalidDecisionError,
)
from temporalio_graphs.validator import ValidationWarning, ValidationReport

__all__ = [
    # Existing exports from Epic 2-4
    "GraphBuildingContext",
    "analyze_workflow",
    "to_decision",
    "wait_condition",
    # New Epic 5 exports
    "TemporalioGraphsError",
    "WorkflowParseError",
    "UnsupportedPatternError",
    "GraphGenerationError",
    "InvalidDecisionError",
    "ValidationWarning",
    "ValidationReport",
]
```

**Validation API:**
```python
# src/temporalio_graphs/validator.py

def validate_workflow(
    metadata: WorkflowMetadata,
    paths: list[GraphPath],
    context: GraphBuildingContext
) -> ValidationReport:
    """Validate workflow quality and detect issues.

    Args:
        metadata: Workflow metadata from AST analysis
        paths: All generated execution paths
        context: Graph building configuration

    Returns:
        ValidationReport with all warnings

    Raises:
        None - validation never fails, only warns

    Example:
        >>> report = validate_workflow(metadata, paths, context)
        >>> if report.has_warnings():
        >>>     print(report.format())
    """
    warnings = []

    if not context.suppress_validation:
        # Detect unreachable activities
        warnings.extend(detect_unreachable_activities(metadata, paths))

        # Detect unused activities (future enhancement)
        # warnings.extend(detect_unused_activities(metadata, paths))

    return ValidationReport(
        warnings=warnings,
        total_activities=len(metadata.activities),
        total_paths=len(paths),
        unreachable_count=len([w for w in warnings if w.category == "unreachable"]),
        unused_count=0  # Future
    )

def detect_unreachable_activities(
    metadata: WorkflowMetadata,
    paths: list[GraphPath]
) -> list[ValidationWarning]:
    """Find activities defined but never called in any execution path."""
    # Collect all activities mentioned in AST
    defined_activities = {
        (activity.name, activity.line)
        for activity in metadata.activities
    }

    # Collect all activities in generated paths
    called_activities = set()
    for path in paths:
        for step in path.steps:
            if isinstance(step, ActivityStep):
                called_activities.add(step.name)

    # Find unreachable
    warnings = []
    for activity_name, line in defined_activities:
        if activity_name not in called_activities:
            warnings.append(ValidationWarning(
                severity=WarningSeverity.WARNING,
                category="unreachable",
                message="Activity is defined but never called in any execution path",
                file_path=metadata.source_file,
                line=line,
                activity_name=activity_name,
                suggestion="Remove unused activity or check workflow logic"
            ))

    return warnings
```

**Formatter API:**
```python
# src/temporalio_graphs/formatter.py

def format_path_list(paths: list[GraphPath]) -> PathListOutput:
    """Convert GraphPath objects to formatted path list.

    Args:
        paths: All execution paths from generator

    Returns:
        PathListOutput with formatted paths

    Example:
        >>> path_list = format_path_list(paths)
        >>> print(path_list.format())
        Path 1: Start → Withdraw → Deposit → End
        Path 2: Start → Withdraw → Convert → Deposit → End
    """
    formatted_paths = []

    for i, path in enumerate(paths, 1):
        # Extract activity names from path steps
        activities = [
            step.name
            for step in path.steps
            if isinstance(step, ActivityStep)
        ]

        # Extract decision outcomes
        decisions = {
            step.name: step.value
            for step in path.steps
            if isinstance(step, DecisionStep)
        }

        formatted_paths.append(FormattedPath(
            path_number=i,
            activities=activities,
            decisions=decisions
        ))

    # Count decisions (same across all paths)
    total_decisions = len(paths[0].decisions) if paths else 0

    return PathListOutput(
        paths=formatted_paths,
        total_paths=len(paths),
        total_decisions=total_decisions
    )
```

**Extended analyze_workflow() Function:**
```python
# Modified src/temporalio_graphs/analyzer.py

def analyze_workflow(
    workflow_file: Path | str,
    context: Optional[GraphBuildingContext] = None,
    output_format: Optional[Literal["mermaid", "paths", "full"]] = None
) -> str:
    """Analyze workflow source file and return graph representation.

    Args:
        workflow_file: Path to Python workflow source file
        context: Optional configuration (uses defaults if None)
        output_format: Override context.output_format if provided

    Returns:
        Graph representation as string:
        - "mermaid": Just Mermaid diagram
        - "paths": Just path list
        - "full": Mermaid + path list + validation report (default)

    Raises:
        WorkflowParseError: If workflow file cannot be parsed
        UnsupportedPatternError: If workflow uses unsupported patterns
        GraphGenerationError: If graph cannot be generated

    Example:
        >>> # Full output (default)
        >>> result = analyze_workflow("workflow.py")
        >>> print(result)
        ```mermaid
        flowchart LR
        ...
        ```

        --- Execution Paths (4 total) ---
        Path 1: Start → Withdraw → Deposit → End
        ...

        --- Validation Report ---
        ⚠️ [UNREACHABLE] Activity never called: 'special_handling' at line 42

        >>> # Mermaid only
        >>> context = GraphBuildingContext(output_format="mermaid")
        >>> result = analyze_workflow("workflow.py", context)
    """
    # Validate and normalize inputs
    ctx = context or GraphBuildingContext()
    fmt = output_format or ctx.output_format
    path = _validate_workflow_file(workflow_file)

    try:
        # Parse AST
        source = path.read_text()
        tree = ast.parse(source)

        # Analyze workflow
        analyzer = WorkflowAnalyzer(ctx)
        metadata = analyzer.analyze(tree)

        # Generate paths
        generator = PathPermutationGenerator(ctx)
        paths = generator.generate(metadata)

        # Validate (if not suppressed)
        validation_report = validate_workflow(metadata, paths, ctx)

        # Render outputs based on format
        output_parts = []

        if fmt in ("mermaid", "full"):
            renderer = MermaidRenderer(ctx)
            mermaid_output = renderer.render(paths)
            output_parts.append(mermaid_output)

        if fmt in ("paths", "full") and ctx.include_path_list:
            path_list = format_path_list(paths)
            output_parts.append(path_list.format())

        if fmt == "full" and ctx.include_validation_report and validation_report.has_warnings():
            output_parts.append(validation_report.format())

        # Write to file if configured
        result = "\n".join(output_parts)
        if ctx.graph_output_file:
            ctx.graph_output_file.write_text(result)

        return result

    except SyntaxError as e:
        raise WorkflowParseError(
            file_path=path,
            line=e.lineno or 0,
            message=f"Invalid Python syntax: {e.msg}",
            suggestion="Check workflow file for syntax errors"
        )
    except FileNotFoundError:
        raise WorkflowParseError(
            file_path=path,
            line=0,
            message="Workflow file not found",
            suggestion="Verify file path is correct"
        )
```

### Workflows and Sequencing

**Validation Workflow (Epic 5.1):**
```
1. analyze_workflow() completes path generation
   ↓
2. validate_workflow(metadata, paths, context) called
   ↓
3. If context.suppress_validation == True:
   → Return empty ValidationReport
   ↓
4. detect_unreachable_activities():
   a. Extract all activity definitions from metadata
   b. Extract all activity calls from paths
   c. Compare: defined - called = unreachable
   d. Create ValidationWarning for each unreachable activity
   ↓
5. (Future) detect_unused_activities():
   a. Build activity call graph
   b. Identify activities with no downstream impact
   c. Create ValidationWarning for each unused activity
   ↓
6. Construct ValidationReport with all warnings
   ↓
7. Return ValidationReport to analyze_workflow()
   ↓
8. If context.include_validation_report and report.has_warnings():
   → Append report.format() to output
```

**Error Handling Workflow (Epic 5.2):**
```
User calls analyze_workflow(path, context)
   ↓
Try:
   ├─ _validate_workflow_file(path)
   │  ├─ Path.resolve() (prevent traversal)
   │  ├─ Check exists → WorkflowParseError if not
   │  ├─ Check is_file → WorkflowParseError if not
   │  └─ Check readable → WorkflowParseError if permission denied
   │
   ├─ ast.parse(source)
   │  └─ SyntaxError → WorkflowParseError with line number
   │
   ├─ WorkflowAnalyzer.analyze(tree)
   │  ├─ No @workflow.defn found → WorkflowParseError
   │  ├─ No @workflow.run found → WorkflowParseError
   │  ├─ Loop detected → UnsupportedPatternError
   │  └─ Dynamic activity name → UnsupportedPatternError (warning, not error)
   │
   ├─ PathPermutationGenerator.generate(metadata)
   │  ├─ decision_count > max_decision_points → GraphGenerationError
   │  └─ total_paths > max_paths → GraphGenerationError
   │
   └─ MermaidRenderer.render(paths)
      └─ Invalid node structure → GraphGenerationError

Except (all exceptions include context: file, line, suggestion)
   └─ Re-raise as specific TemporalioGraphsError subtype
```

**Path List Generation Workflow (Epic 5.3):**
```
1. PathPermutationGenerator completes
   → list[GraphPath] available
   ↓
2. format_path_list(paths) called
   ↓
3. For each GraphPath:
   a. Extract ActivityStep objects → activities list
   b. Extract DecisionStep objects → decisions dict
   c. Create FormattedPath(number, activities, decisions)
   ↓
4. Calculate total_decisions (same across all paths)
   ↓
5. Construct PathListOutput(paths, total_paths, total_decisions)
   ↓
6. PathListOutput.format() generates text:
   ```
   --- Execution Paths (4 total) ---
   Decision Points: 2 (2^2 = 4 paths)

   Path 1: Start → Withdraw → CurrencyConvert → NotifyAto → Deposit → End
   Path 2: Start → Withdraw → CurrencyConvert → TakeNonResidentTax → Deposit → End
   Path 3: Start → Withdraw → NotifyAto → Deposit → End
   Path 4: Start → Withdraw → TakeNonResidentTax → Deposit → End
   ```
   ↓
7. Return formatted string to analyze_workflow()
   ↓
8. If context.include_path_list:
   → Append to output after Mermaid diagram
```

**Example Development Workflow (Epic 5.4):**
```
1. Design example workflow concept
   (e.g., LoanApproval with 3 decisions)
   ↓
2. Implement workflow.py:
   a. Import temporalio decorators
   b. Import to_decision helper
   c. Define @workflow.defn class
   d. Implement @workflow.run method
   e. Add 3+ decision points with to_decision()
   f. Add sequential activities
   ↓
3. Create run.py demonstrating usage:
   a. Import analyze_workflow
   b. Call with example workflow
   c. Print results
   d. Save to expected_output.md
   ↓
4. Run and capture expected output:
   ```bash
   cd examples/multi_decision
   python run.py > expected_output.md
   ```
   ↓
5. Create integration test:
   a. Read workflow.py
   b. Call analyze_workflow()
   c. Compare output to expected_output.md (structural match)
   d. Validate: correct path count (2^n), valid Mermaid, all activities present
   ↓
6. Document in README:
   a. Add example to Examples section
   b. Link to example code
   c. Explain what pattern it demonstrates
```

**Documentation Creation Workflow (Epic 5.5):**
```
1. README.md:
   a. Project overview and value proposition
   b. Installation instructions (pip install temporalio-graphs)
   c. Quick start example (<10 lines demonstrating analyze_workflow)
   d. Link to all examples with descriptions
   e. Configuration options overview
   f. Architecture explanation (static analysis vs .NET interceptors)
   g. Badge placeholders (PyPI, coverage, license)
   ↓
2. docs/api-reference.md:
   a. Extract function signatures from source docstrings
   b. Document GraphBuildingContext fields
   c. Document all public functions: analyze_workflow, to_decision, wait_condition
   d. Document exception hierarchy
   e. Include usage examples for each API
   ↓
3. CHANGELOG.md:
   a. Follow Keep a Changelog format
   b. Document 0.1.0 initial release with all features
   c. List all FRs implemented
   d. Note breaking changes from .NET (static analysis approach)
   ↓
4. LICENSE:
   a. Copy MIT license text
   b. Update copyright year and author
   c. Match .NET Temporalio.Graphs license
   ↓
5. Migration guide (in README or separate doc):
   a. Compare .NET interceptor approach vs Python static analysis
   b. Explain to_decision() vs .NET automatic tracking
   c. Show equivalent code patterns (C# vs Python)
   d. Note any feature differences
   ↓
6. Troubleshooting section:
   a. Common error: Missing @workflow.defn → solution
   b. Common error: Path explosion → solution (increase limit or refactor)
   c. Common error: Dynamic activity names → solution (use string literals)
   d. Performance tips: Keep decisions <10, use linear workflows when possible
   e. Unsupported patterns: Loops, reflection → workarounds
```

## Non-Functional Requirements

### Performance

**NFR-PERF-1 Validation Overhead:**
- Validation logic adds <10ms to total analysis time
- Unreachable activity detection: O(n) where n = activities
- Target: <5ms for workflows with 50 activities
- No memory overhead beyond ValidationWarning list

**NFR-PERF-2 Path List Generation:**
- Path list formatting: <5ms for 100 paths
- Linear complexity: O(paths × activities per path)
- String building uses efficient concatenation (join, not +=)

**NFR-PERF-3 Error Message Formatting:**
- Exception construction: <1ms per error
- No expensive operations in __init__ (no file I/O, no network)
- Lazy formatting (only when str(exception) called)

**Performance Validation:**
```python
# Performance test in tests/test_performance.py
def test_validation_performance():
    # Workflow with 50 activities
    metadata = create_large_workflow(num_activities=50)
    paths = generate_paths(metadata)

    start = time.perf_counter()
    report = validate_workflow(metadata, paths, context)
    duration = time.perf_counter() - start

    assert duration < 0.01  # <10ms
```

### Security

**SEC-1 Exception Information Disclosure:**
- Error messages include file paths (safe - user's own files)
- No sensitive data (API keys, credentials) in exceptions
- Stack traces available for debugging (standard Python behavior)
- No arbitrary code execution in error handlers

**SEC-2 Validation Safety:**
- Validation is read-only (no file modifications)
- No external network calls during validation
- No execution of workflow code
- Safe AST traversal only

**SEC-3 Example Code Security:**
- All examples use placeholder data (no real credentials)
- Examples demonstrate best practices (no anti-patterns)
- No dependency on external services
- Runnable in isolated environment

### Reliability

**REL-1 Validation Correctness:**
- Unreachable activity detection: 100% accuracy (all defined activities checked)
- False positive rate: 0% (only flag genuinely unreachable activities)
- Validation never causes analysis to fail (warnings only, not errors)

**REL-2 Error Handling Robustness:**
- All exceptions caught and wrapped in TemporalioGraphsError subtypes
- No silent failures (all errors reported clearly)
- Stack traces preserved for debugging (via exception chaining)
- Graceful degradation (validation can be disabled)

**REL-3 Example Reliability:**
- All examples tested in CI on every commit
- Examples use pinned dependency versions (temporalio>=1.7.1)
- Expected outputs validated against actual outputs (golden file tests)
- Examples runnable on all supported platforms (Linux, macOS, Windows)

**REL-4 Documentation Accuracy:**
- All code examples extracted from tested source
- API signatures auto-generated from actual code
- Version numbers in docs match pyproject.toml
- Changelog updated on every release

### Observability

**OBS-1 Logging Strategy:**
```python
import logging

logger = logging.getLogger("temporalio_graphs")

# Validation logging
logger.info(f"Validation complete: {len(warnings)} warnings found")
logger.debug(f"Unreachable activities: {unreachable_list}")

# Error logging
logger.error(f"Workflow parse failed: {file_path}", exc_info=True)

# Performance logging (debug mode)
logger.debug(f"Validation took {duration*1000:.2f}ms")
```

**OBS-2 Validation Metrics:**
- Track warning counts by category (unreachable, unused, complexity)
- Log validation report summary (total warnings, total paths, total activities)
- Optional verbose mode for detailed validation output

**OBS-3 Error Context:**
- All exceptions include: file path, line number, error type
- Exception chaining preserves original exceptions (via `from`)
- Actionable suggestions in every error message

## Dependencies and Integrations

**Core Dependencies (No Changes from Epic 1-4):**
- Python 3.10+ (requirement)
- temporalio SDK >=1.7.1 (runtime dependency)
- Python ast module (built-in, for AST parsing)

**Development Dependencies (No Changes):**
- pytest >=8.0.0 (testing framework)
- pytest-cov >=4.1.0 (coverage measurement, 80% minimum)
- pytest-asyncio >=0.23.0 (async test support)
- mypy >=1.8.0 (type checking, strict mode)
- ruff >=0.2.0 (linting and formatting)

**New Internal Module Dependencies:**
```python
# exceptions.py
from pathlib import Path
from typing import Optional

# validator.py
from temporalio_graphs.context import GraphBuildingContext
from temporalio_graphs.path import GraphPath
from temporalio_graphs._internal.graph_models import WorkflowMetadata, ActivityStep
from temporalio_graphs.exceptions import TemporalioGraphsError
from dataclasses import dataclass
from enum import Enum

# formatter.py
from temporalio_graphs.path import GraphPath
from temporalio_graphs.validator import ValidationReport
from dataclasses import dataclass

# Updated analyzer.py
from temporalio_graphs.validator import validate_workflow
from temporalio_graphs.formatter import format_path_list
from temporalio_graphs.exceptions import WorkflowParseError, GraphGenerationError
```

**Documentation Tools (Optional):**
- mkdocs or Sphinx for API reference generation (post-MVP)
- shields.io for README badges (static, no runtime dependency)

**Integration Points:**
- Validation integrates into analyze_workflow() after path generation
- Formatter integrates into analyze_workflow() for output assembly
- Exceptions used throughout all modules (parse, analyze, generate, render)

## Acceptance Criteria (Authoritative)

### AC-5.1: Validation Warnings for Graph Quality

**Given** workflow analysis has completed successfully
**When** validation is enabled (context.suppress_validation=False)
**Then** system detects all activities defined in AST but never called in any execution path (FR25)
**And** system creates ValidationWarning for each unreachable activity with: severity=WARNING, category="unreachable", file path, line number, activity name
**And** system suggests: "Remove unused activity or check workflow logic"
**And** validation report includes total counts: total_activities, total_paths, unreachable_count
**And** validation report can be suppressed by setting context.suppress_validation=True (FR32)
**And** validation report formatted output includes warning icon (⚠️), category, message, location
**And** validation adds <10ms overhead per NFR-PERF-1
**And** unit tests achieve 100% coverage for validation logic
**And** integration test demonstrates validation warnings in MoneyTransfer workflow (if activity added but not called)

### AC-5.2: Comprehensive Error Handling Hierarchy

**Given** various error conditions can occur during workflow analysis
**When** errors are encountered
**Then** TemporalioGraphsError base exception exists in exceptions.py
**And** WorkflowParseError is raised when: workflow file not found, syntax error, missing @workflow.defn, missing @workflow.run (FR61, FR64)
**And** UnsupportedPatternError is raised when: loops detected, dynamic activity names used (FR62)
**And** GraphGenerationError is raised when: decision_points > max_decision_points, total_paths > max_paths, rendering fails
**And** InvalidDecisionError is raised when: to_decision() or wait_condition() used incorrectly (FR65)
**And** all exceptions include: file_path, line number (when available), error description, actionable suggestion (FR63, NFR-USE-2)
**And** error message format:
```
Cannot parse workflow file: /path/to/workflow.py
Line 42: Missing @workflow.defn decorator
Suggestion: Add @workflow.defn decorator to workflow class
```
**And** all exceptions tested with unit tests verifying message format and context
**And** integration tests verify error messages are helpful for common mistakes

### AC-5.3: Path List Output Format

**Given** paths have been generated from workflow analysis
**When** path list output is requested (context.include_path_list=True or output_format="paths")
**Then** system generates text list of all unique execution paths (FR24)
**And** each path formatted as: "Path N: Start → Activity1 → Activity2 → End"
**And** paths are numbered sequentially starting from 1
**And** path list includes header: "--- Execution Paths (N total) ---"
**And** path list includes decision count info: "Decision Points: N (2^N = M paths)"
**And** path list can be output standalone (output_format="paths") or with Mermaid (output_format="full")
**And** path list can be suppressed (context.include_path_list=False or output_format="mermaid")
**And** path list generation completes in <5ms for 100 paths per NFR-PERF-2
**And** unit tests validate path list format for: linear workflow (1 path), 2 decisions (4 paths), 3 decisions (8 paths)
**And** integration test validates MoneyTransfer path list shows 4 paths correctly

### AC-5.4: Comprehensive Example Gallery

**Given** library features are complete
**When** example gallery is created
**Then** examples/simple_linear/ exists from Epic 2.8 with: workflow.py, run.py, expected_output.md (FR58)
**And** examples/money_transfer/ exists from Epic 3.5 with: workflow.py, run.py, expected_output.md (FR56, FR57)
**And** examples/signal_workflow/ exists from Epic 4.4 with: workflow.py, run.py, expected_output.md
**And** examples/multi_decision/ (NEW) exists with: workflow.py (3 decisions = 8 paths), run.py, expected_output.md (FR59)
**And** multi_decision workflow demonstrates: 3+ independent decision points, nested conditionals, path count validation
**And** all examples are runnable: `cd examples/<name> && python run.py` produces expected output
**And** all examples tested in tests/integration/ with golden file comparison
**And** each example documented in README with: description, link to code, what pattern it demonstrates
**And** CI runs all examples on every commit

### AC-5.5: Production-Grade Documentation

**Given** all features are implemented and tested
**When** documentation is complete
**Then** README.md exists with: project overview, installation (pip install temporalio-graphs), quick start example <10 lines (FR60)
**And** README includes PyPI badges: version, test coverage, license (MIT), Python versions (3.10, 3.11, 3.12)
**And** README links to all 4 examples with descriptions
**And** README explains core concepts: AST static analysis, decision nodes (to_decision), signal nodes (wait_condition)
**And** README shows configuration examples: suppress validation, change output format, customize node labels
**And** docs/api-reference.md or README section documents: GraphBuildingContext fields, analyze_workflow signature, to_decision signature, wait_condition signature, exception hierarchy
**And** API reference includes usage examples for each public function
**And** CHANGELOG.md exists following Keep a Changelog format with 0.1.0 release notes
**And** LICENSE file is MIT license (matching .NET version per NFR-QUAL-4)
**And** documentation includes migration guide from .NET: architecture differences (static vs interceptor), code pattern equivalents (C# vs Python)
**And** troubleshooting section covers: missing @workflow.defn error + fix, path explosion error + fix, dynamic activity names warning + workaround, performance tips
**And** all code examples in documentation are tested (extracted from examples/ or tested separately)
**And** documentation is clear and accessible to intermediate Python developers (no advanced AST knowledge required)

## Traceability Mapping

| AC | Component | Test Coverage |
|----|-----------|---------------|
| **AC-5.1: Validation Warnings** |
| Detect unreachable activities | validator.py:detect_unreachable_activities() | tests/test_validator.py::test_unreachable_activity_detection |
| ValidationWarning data model | validator.py:ValidationWarning | tests/test_validator.py::test_validation_warning_format |
| Suppress validation flag | context.py:GraphBuildingContext.suppress_validation | tests/test_validator.py::test_suppress_validation |
| Validation report format | validator.py:ValidationReport.format() | tests/test_validator.py::test_validation_report_format |
| Performance <10ms | validator.py:validate_workflow() | tests/test_performance.py::test_validation_performance |
| Integration test | Full pipeline | tests/integration/test_validation_warnings.py |
| **AC-5.2: Error Handling** |
| TemporalioGraphsError base | exceptions.py:TemporalioGraphsError | tests/test_exceptions.py::test_base_exception |
| WorkflowParseError | exceptions.py:WorkflowParseError | tests/test_exceptions.py::test_workflow_parse_error |
| UnsupportedPatternError | exceptions.py:UnsupportedPatternError | tests/test_exceptions.py::test_unsupported_pattern_error |
| GraphGenerationError | exceptions.py:GraphGenerationError | tests/test_exceptions.py::test_graph_generation_error |
| InvalidDecisionError | exceptions.py:InvalidDecisionError | tests/test_exceptions.py::test_invalid_decision_error |
| Error message format | All exception __init__ methods | tests/test_exceptions.py::test_error_message_format |
| Actionable suggestions | All exception suggestion fields | tests/integration/test_error_handling.py |
| **AC-5.3: Path List Output** |
| FormattedPath data model | formatter.py:FormattedPath | tests/test_formatter.py::test_formatted_path |
| PathListOutput.format() | formatter.py:PathListOutput.format() | tests/test_formatter.py::test_path_list_format |
| Include/suppress path list | context.py:include_path_list | tests/test_formatter.py::test_suppress_path_list |
| Output format modes | analyzer.py:output_format parameter | tests/test_analyzer.py::test_output_formats |
| Performance <5ms | formatter.py:format_path_list() | tests/test_performance.py::test_path_list_performance |
| MoneyTransfer integration | Full pipeline | tests/integration/test_money_transfer.py::test_path_list_output |
| **AC-5.4: Example Gallery** |
| Simple linear example | examples/simple_linear/ | tests/integration/test_simple_linear.py |
| MoneyTransfer example | examples/money_transfer/ | tests/integration/test_money_transfer.py |
| Signal example | examples/signal_workflow/ | tests/integration/test_signal_workflow.py |
| Multi-decision example | examples/multi_decision/ | tests/integration/test_multi_decision.py |
| All examples runnable | run.py in each example | CI: make run-examples |
| Golden file tests | expected_output.md comparison | All integration tests |
| README documentation | README.md Examples section | Manual review |
| **AC-5.5: Documentation** |
| README structure | README.md | Manual review + CI check |
| Quick start <10 lines | README.md Quick Start section | Manual review |
| API reference | docs/api-reference.md or README | Manual review |
| CHANGELOG | CHANGELOG.md | Manual review |
| LICENSE MIT | LICENSE file | CI: make check-license |
| Migration guide | README.md or docs/migration.md | Manual review |
| Troubleshooting section | README.md Troubleshooting | Manual review |
| Code examples tested | examples/ directory | Integration tests |

## Test Strategy Summary

### Unit Tests (Target: 100% coverage for new modules)

**exceptions.py (5 tests):**
- test_base_exception: Instantiate TemporalioGraphsError
- test_workflow_parse_error: Message format with file/line/suggestion
- test_unsupported_pattern_error: Pattern name and suggestion
- test_graph_generation_error: Reason and context dict
- test_invalid_decision_error: Function name, issue, suggestion

**validator.py (8 tests):**
- test_unreachable_activity_detection: Single unreachable activity found
- test_no_unreachable_activities: All activities called
- test_multiple_unreachable_activities: Multiple warnings generated
- test_validation_warning_format: Warning.format() output
- test_validation_report_format: Report.format() with warnings
- test_validation_report_no_warnings: Empty report
- test_suppress_validation: No warnings when suppressed
- test_validation_warning_severity: INFO vs WARNING levels

**formatter.py (6 tests):**
- test_formatted_path_single_activity: Path with 1 activity
- test_formatted_path_multiple_activities: Path with 3+ activities
- test_path_list_format_linear: 1 path (no decisions)
- test_path_list_format_decisions: 4 paths (2 decisions)
- test_path_list_output_header: Header includes total paths and decision count
- test_suppress_path_list: Empty output when include_path_list=False

### Integration Tests (5 tests)

**test_validation_warnings.py:**
- test_unreachable_activity_warning_in_output: Full pipeline with unreachable activity shows warning

**test_error_handling.py:**
- test_missing_decorator_error: WorkflowParseError with helpful message
- test_path_explosion_error: GraphGenerationError when max_decision_points exceeded
- test_unsupported_loop_error: UnsupportedPatternError for while loop

**test_multi_decision.py:**
- test_multi_decision_example: 3 decisions → 8 paths, valid Mermaid, correct path list
- test_multi_decision_golden_file: Compare output to expected_output.md

### Performance Tests (2 tests)

**test_performance.py:**
- test_validation_performance: Validation <10ms for 50 activities
- test_path_list_performance: Path list <5ms for 100 paths

### Example Tests (Already covered in Epic 2-4, validation in Epic 5)

**test_simple_linear.py:** (Epic 2.8)
**test_money_transfer.py:** (Epic 3.5)
**test_signal_workflow.py:** (Epic 4.4)
**test_multi_decision.py:** (Epic 5.4 - NEW)

### Documentation Tests (Manual + CI Automation)

**README validation:**
- CI: Check README has all required sections (Installation, Quick Start, Examples, API)
- CI: Validate all example links resolve
- CI: Extract and run Quick Start code snippet

**License validation:**
- CI: Verify LICENSE file is MIT
- CI: Check copyright year is current

**Changelog validation:**
- CI: Verify CHANGELOG.md follows Keep a Changelog format
- CI: Check latest version matches pyproject.toml

## Risks, Assumptions, Open Questions

### Risks

**RISK-1: Validation False Positives**
- **Description:** Unreachable activity detection may flag activities that are reachable via complex logic (e.g., nested conditionals not using to_decision())
- **Impact:** Medium - Users may see warnings for valid code
- **Mitigation:**
  - Make warnings suppressible (context.suppress_validation)
  - Clear documentation explaining when false positives occur
  - Consider adding "ignore" comment support (post-MVP)
- **Status:** Mitigated by suppression flag

**RISK-2: Documentation Maintenance Burden**
- **Description:** Documentation may become outdated as library evolves
- **Impact:** Medium - Users may see incorrect examples or API signatures
- **Mitigation:**
  - Extract code examples from tested files (examples/)
  - CI checks for README structure and links
  - Version documentation with releases
  - Use docstring auto-generation where possible (future)
- **Status:** Mitigated by CI checks and example extraction

**RISK-3: Example Complexity Creep**
- **Description:** Examples may become too complex to serve as learning tools
- **Impact:** Low - Users may struggle to understand examples
- **Mitigation:**
  - Keep examples simple and focused (single pattern each)
  - Add comments explaining each step
  - Progressive complexity (simple → intermediate → complex)
  - Review examples for clarity during story review
- **Status:** Mitigated by design

**RISK-4: Error Message Localization**
- **Description:** All error messages are in English, limiting international adoption
- **Impact:** Low for MVP - Library targets English-speaking Python community initially
- **Mitigation:**
  - Accept English-only for MVP
  - Design exception structure to support future localization (separate message templates)
  - Consider i18n in post-MVP if demand exists
- **Status:** Accepted for MVP

### Assumptions

**ASSUME-1: Users Read Documentation**
- Assumption: Users will read README and examples before reporting issues
- Validation: README is comprehensive and examples are clear
- Fallback: If assumption fails, add FAQ section based on GitHub issues

**ASSUME-2: Validation Warnings Are Helpful**
- Assumption: Users find unreachable activity warnings valuable
- Validation: Validation is suppressible if users disagree
- Fallback: Gather feedback during early adoption, adjust warnings if too noisy

**ASSUME-3: Path List Format Is Sufficient**
- Assumption: Text format (Path N: Start → A → B → End) is clear enough
- Validation: Integration tests demonstrate readability
- Fallback: Add alternative formats (JSON, table) in post-MVP if users request

**ASSUME-4: Mypy Strict Mode Is Achievable**
- Assumption: All Epic 5 code can achieve mypy strict compliance
- Validation: Existing Epic 1-4 code already mypy strict
- Fallback: If strict mode blocks progress, relax to standard type checking (low probability)

**ASSUME-5: Examples Cover Common Use Cases**
- Assumption: 4 examples (linear, MoneyTransfer, signal, multi-decision) cover 80% of user needs
- Validation: Examples demonstrate all major features (activities, decisions, signals, paths)
- Fallback: Add more examples post-MVP based on user feedback

### Open Questions

**QUESTION-1: Should validation include "unused activity" detection?**
- **Context:** FR26 mentions "activities defined but never called" which overlaps with "unreachable"
- **Options:**
  1. Include unused activity detection in Epic 5.1 (requires call graph analysis)
  2. Defer to post-MVP (simpler MVP scope)
  3. Combine with unreachable detection (may be same thing)
- **Decision:** Start with unreachable detection only. Add unused activity detection post-MVP if users request it and it's distinct from unreachable.
- **Rationale:** Unreachable detection covers FR25 and likely FR26. Call graph analysis adds complexity.

**QUESTION-2: Should API reference be auto-generated or manual?**
- **Context:** Docs can be generated from docstrings (Sphinx, mkdocs) or written manually
- **Options:**
  1. Manual docs/api-reference.md (simpler, MVP scope)
  2. Auto-generated with Sphinx (more maintainable long-term)
  3. Inline in README (simplest)
- **Decision:** Start with manual API reference in README or separate markdown. Add auto-generation post-MVP.
- **Rationale:** Avoid adding Sphinx/mkdocs dependency for MVP. Manual docs are faster to create and sufficient for initial release.

**QUESTION-3: Should examples include error handling demonstrations?**
- **Context:** Examples could show try/except usage for library exceptions
- **Options:**
  1. Yes - Add error handling to run.py in examples
  2. No - Keep examples focused on happy path
  3. Separate - Create examples/error_handling/ example
- **Decision:** Keep happy path in main examples. Add error handling example snippet in README troubleshooting section.
- **Rationale:** Examples should be simple and focused. Error handling can be demonstrated in docs.

**QUESTION-4: Should path list include decision outcomes?**
- **Context:** Current design: "Path 1: Start → A → B → End". Could show decisions: "Path 1 (NeedToConvert=yes, IsTFN=no): Start → A → B → End"
- **Options:**
  1. Yes - Include decision outcomes in path description
  2. No - Keep path list simple (just activities)
  3. Optional - Add context.include_decision_outcomes flag
- **Decision:** Keep simple for MVP (just activities). Add decision outcomes post-MVP if users request.
- **Rationale:** Simplicity for MVP. Decision outcomes visible in Mermaid diagram already.

**QUESTION-5: Should validation warnings be color-coded in terminal?**
- **Context:** Warnings could use ANSI color codes for better visibility (yellow for warnings, red for errors)
- **Options:**
  1. Yes - Add color support via termcolor or colorama
  2. No - Plain text only (better for file output)
  3. Optional - Detect TTY and color automatically
- **Decision:** Plain text only for MVP. Colors add dependency and complexity.
- **Rationale:** Library output may be written to files or parsed by tools. Colors complicate this. Post-MVP enhancement if users request.

---

_Tech Spec for Epic 5: Production Readiness created on 2025-11-19._
_Ready for story creation and implementation._
