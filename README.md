# temporalio-graphs

Generate complete workflow visualizations as Mermaid diagrams for Temporal workflows using static code analysis.

## Status

🚧 **Under Development** - Epic 2 (Basic Graph Generation) In Progress
- Story 2-1: Core Data Models ✅
- Story 2-2: AST Workflow Analyzer ✅
- Story 2-3: Activity Detection 🔄 (Review)
- Story 2-4: Path Generator ✅
- Story 2-5: Mermaid Renderer ✅
- Story 2-6: Public API Entry Point ✅ (This Release)
- Story 2-7: Configuration Options (Next)

## Overview

Unlike DAG-based workflow engines, Temporal workflows don't provide complete visualization of all possible execution paths. This library generates Mermaid diagrams showing **ALL** possible workflow paths by analyzing workflow code structure using Python's AST (Abstract Syntax Tree).

### Key Innovation

- **Static Analysis Approach**: Analyzes workflow code without executing it
- **Complete Path Coverage**: Generates 2^n paths for n decision points
- **Fast**: < 1ms analysis time vs exponential execution time
- **No Runtime Dependencies**: Works on source code directly

## Architecture Decision

After evaluating three approaches (mock execution, history parsing, static analysis), we chose **static code analysis** because:

1. Python Temporal SDK interceptors cannot mock activity return values (unlike .NET)
2. Generates ALL possible paths without workflow execution
3. Performance: sub-millisecond vs exponential execution time
4. Matches conceptual model of .NET reference implementation

See `/spike/EXECUTIVE_SUMMARY.md` for detailed rationale.

## Installation

```bash
# Once published to PyPI
pip install temporalio-graphs

# Development installation
git clone https://github.com/yourusername/temporalio-graphs
cd temporalio-graphs
uv venv
source .venv/bin/activate
uv sync
```

## Quick Start

### Basic Usage (3 lines)

Analyze a workflow and get a Mermaid diagram:

```python
from temporalio_graphs import analyze_workflow

result = analyze_workflow("my_workflow.py")
print(result)  # Prints Mermaid diagram
```

### Running the Example

Try the included example right now:

```bash
python examples/simple_linear/run.py
```

This analyzes a simple workflow with 3 sequential activities and outputs:

```mermaid
flowchart LR
s((Start))
1[validate_input]
2[process_data]
3[save_result]
e((End))
s --> 1
1 --> 2
2 --> 3
3 --> e
```

See `/examples/simple_linear/` for the complete working example with explanations.

### Advanced Usage with Custom Configuration

Customize node labels and output location:

```python
from temporalio_graphs import analyze_workflow, GraphBuildingContext

context = GraphBuildingContext(
    split_names_by_words=False,
    start_node_label="BEGIN",
    end_node_label="FINISH",
    graph_output_file="workflow_diagram.md"
)
result = analyze_workflow("my_workflow.py", context)
```

## Configuration

All configuration options are provided via the `GraphBuildingContext` dataclass. The context is immutable and flows through the entire analysis pipeline. Default values support typical use cases; customize for specific requirements.

### Configuration Options

| Option | Type | Default | Purpose |
|--------|------|---------|---------|
| `split_names_by_words` | bool | True | Convert camelCase activity names to "camel Case" in labels |
| `start_node_label` | str | "Start" | Custom label for workflow start node |
| `end_node_label` | str | "End" | Custom label for workflow end node |
| `suppress_validation` | bool | False | Disable validation warnings (e.g., path explosion) |
| `max_decision_points` | int | 10 | Maximum allowed decision points (prevents 2^n path explosion) |
| `max_paths` | int | 1024 | Maximum allowed total execution paths |
| `graph_output_file` | Path \| None | None | Write output to file instead of returning string |

### Configuration Examples

#### Example 1: Disable Word Splitting for Acronyms

When your activities use acronyms or prefer exact naming:

```python
from temporalio_graphs import analyze_workflow, GraphBuildingContext

context = GraphBuildingContext(split_names_by_words=False)
result = analyze_workflow("workflow.py", context)
# Output: "fetchAPIData" stays as "fetchAPIData", not "fetch A P I Data"
```

#### Example 2: Custom Domain Terminology

Use domain-specific labels for start/end nodes:

```python
context = GraphBuildingContext(
    start_node_label="Initiate",
    end_node_label="Complete"
)
result = analyze_workflow("workflow.py", context)
# Output: "i((Initiate)) --> ... --> e((Complete))"
```

#### Example 3: Complex Workflows with Many Decisions

Increase limits for workflows with many decision points (Epic 3+):

```python
context = GraphBuildingContext(
    max_decision_points=15,  # Allows up to 32,768 paths (2^15)
    max_paths=32768
)
result = analyze_workflow("workflow.py", context)
# Note: May generate large diagrams; consider breaking into sub-workflows
```

#### Example 4: File Output for CI/CD Integration

Automatically write generated diagrams to files:

```python
from pathlib import Path

context = GraphBuildingContext(
    graph_output_file=Path("docs/workflow_diagram.md")
)
result = analyze_workflow("workflow.py", context)
# File is created at docs/workflow_diagram.md
# Result is still returned and can be printed/processed
```

#### Example 5: Quick Analysis Without Validation

Suppress validation warnings for rapid iteration:

```python
context = GraphBuildingContext(suppress_validation=True)
result = analyze_workflow("workflow.py", context)
# No validation warnings printed, only diagram output
```

#### Example 6: Combined Configuration

Use multiple options together for full control:

```python
from pathlib import Path

context = GraphBuildingContext(
    split_names_by_words=False,
    start_node_label="WORKFLOW_START",
    end_node_label="WORKFLOW_END",
    suppress_validation=True,
    max_decision_points=10,
    graph_output_file=Path("output/diagram.md")
)
result = analyze_workflow("complex_workflow.py", context)
```

### Performance Implications

- **Word Splitting**: O(n) where n = activity name length. Negligible performance impact.
- **Max Decision Points**: Prevents path explosion. Default (10) generates up to 1024 paths. Epic 3 will support decision-based path generation; larger limits increase generation time exponentially (2^n).
- **File Output**: Adds I/O time proportional to diagram size. Minimal impact (<5ms typical).

### Configuration Validation

Invalid configuration raises `ValueError` with clear error messages:

```python
# Negative max_decision_points raises ValueError
context = GraphBuildingContext(max_decision_points=-1)
# ValueError: max_decision_points must be positive, got -1.
# Consider increasing this value (default: 10)
```

All configuration is validated when `analyze_workflow()` is called.

## Features

### Completed (Epic 2: Basic Graph Generation)

- ✅ Static code analysis using Python AST
- ✅ Linear workflow detection (0 decision points)
- ✅ Activity tracking and sequencing
- ✅ Mermaid flowchart LR syntax output
- ✅ Public API with analyze_workflow() function
- ✅ Type-safe configuration via GraphBuildingContext
- ✅ Complete test coverage (>95%)

### Planned (Epic 3+)

- 🚧 Decision point detection (if/else, conditions)
- 🚧 Path permutation generation (2^n paths for n decisions)
- 🚧 Signal and wait condition support
- 🚧 CLI interface
- 🚧 Multiple output formats (JSON, path lists)

## Project Structure

```
/spike/                          # Architecture validation (COMPLETE)
  ├── EXECUTIVE_SUMMARY.md       # Decision rationale
  ├── findings.md                # Technical analysis
  └── temporal-spike/            # Working prototypes
      └── approach3_static_analysis.py  # ✅ RECOMMENDED

/src/temporalio_graphs/          # Python implementation (IN PROGRESS)
/tests/                          # Test suite
/examples/                       # Example workflows
```

## Development

```bash
# Setup environment (always use uv)
uv venv
source .venv/bin/activate
uv sync

# Run tests
pytest -v --cov=src/temporalio_graphs

# Type checking
mypy src/

# Linting
ruff check src/
ruff format src/
```

## Implementation Plan

See [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) for the complete 15.5-hour phased implementation plan with 7 quality gate reviews.

**Current Status**: Phase 0.5 Complete ✅ - Ready for Phase 1

## How It Works

1. **AST Parsing**: Parse Python workflow source files
2. **Decision Detection**: Identify branching logic (if/else, conditions)
3. **Path Generation**: Create 2^n execution paths for n decisions
4. **Graph Building**: Construct workflow graph from paths
5. **Mermaid Output**: Convert to flowchart syntax

## Example Output

MoneyTransfer workflow with 2 decision points generates 4 paths:

```mermaid
flowchart LR
s((Start)) --> Withdraw --> 0{NeedToConvert}
0{NeedToConvert} -- yes --> CurrencyConvert --> 1{IsTFN_Known}
0{NeedToConvert} -- no --> 1{IsTFN_Known}
1{IsTFN_Known} -- yes --> NotifyAto --> Deposit --> e((End))
1{IsTFN_Known} -- no --> TakeNonResidentTax --> Deposit
```

## Contributing

Contributions welcome! Please see the implementation plan for current priorities.

## License

MIT

## Sponsors

This project is made possible by the generous support of:

- [@davidhw](https://github.com/davidhw) - Original bounty sponsor

## Credits

Python port of [Temporalio.Graphs (.NET)](https://github.com/oleg-shilo/Temporalio.Graphs) with architectural adaptations for Python SDK constraints.
