# Packaging and Distribution Guide

This guide covers how to build, distribute, and use the temporalio-graphs library.

## Package Structure Verification ✅

Before packaging, verify all required files are in place:

```bash
# Check package structure
tree -L 3 src/
# Should show:
# src/
# └── temporalio_graphs/
#     ├── __init__.py          # Public API with __all__
#     ├── py.typed             # Type hints marker
#     ├── analyzer.py
#     ├── context.py
#     ├── detector.py
#     └── ...

# Verify essential files
ls -la pyproject.toml LICENSE README.md CHANGELOG.md
```

**Required Files (All Present ✅):**
- ✅ `pyproject.toml` - Package metadata and build config
- ✅ `README.md` - PyPI description (auto-included)
- ✅ `LICENSE` - MIT License
- ✅ `src/temporalio_graphs/py.typed` - Type hints marker
- ✅ `src/temporalio_graphs/__init__.py` - Public API with `__all__`
- ✅ `CHANGELOG.md` - Version history (optional but recommended)

---

## Building the Package

### Method 1: Using `uv` (Recommended - Fast)

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build wheel and source distribution
uv build

# Output:
# dist/
#   ├── temporalio_graphs-0.1.0-py3-none-any.whl  (wheel - preferred)
#   └── temporalio_graphs-0.1.0.tar.gz            (source)
```

**Build Outputs:**
- **Wheel (`.whl`)**: Binary distribution, faster installation
- **Source (`.tar.gz`)**: Source distribution, fallback for compatibility

### Method 2: Using `build` (Standard)

```bash
# Install build tool
pip install build

# Build package
python -m build

# Same output as uv build
```

### Verify Build

```bash
# Check wheel contents
unzip -l dist/temporalio_graphs-0.1.0-py3-none-any.whl

# Should include:
# - temporalio_graphs/*.py
# - temporalio_graphs/py.typed
# - temporalio_graphs-0.1.0.dist-info/METADATA
# - temporalio_graphs-0.1.0.dist-info/LICENSE
```

---

## Publishing to PyPI

### Prerequisites

1. **PyPI Account**: Register at https://pypi.org/account/register/
2. **API Token**: Create at https://pypi.org/manage/account/token/
   - Scope: "Entire account" or specific project
   - Save token securely (shown only once)

3. **Configure Authentication**:

```bash
# Create/edit ~/.pypirc
cat > ~/.pypirc << 'EOF'
[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmc...  # Your API token
EOF

chmod 600 ~/.pypirc  # Secure permissions
```

### Test Upload to TestPyPI (Recommended First)

```bash
# 1. Register on TestPyPI: https://test.pypi.org/account/register/

# 2. Upload to TestPyPI
uv publish --publish-url https://test.pypi.org/legacy/
# or
twine upload --repository testpypi dist/*

# 3. Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ temporalio-graphs

# 4. Verify it works
python -c "from temporalio_graphs import analyze_workflow; print('Success!')"
```

### Production Upload to PyPI

```bash
# Upload to PyPI
uv publish
# or
twine upload dist/*

# Expected output:
# Uploading distributions to https://upload.pypi.org/legacy/
# Uploading temporalio_graphs-0.1.0-py3-none-any.whl
# Uploading temporalio_graphs-0.1.0.tar.gz
# View at: https://pypi.org/project/temporalio-graphs/0.1.0/
```

### Publishing Checklist

Before publishing, ensure:
- [ ] All tests passing (`pytest`)
- [ ] Type checking passing (`mypy src/`)
- [ ] Linting passing (`ruff check src/`)
- [ ] Version bumped in `pyproject.toml`
- [ ] CHANGELOG.md updated with version
- [ ] README.md accurate and up-to-date
- [ ] Git tag created: `git tag v0.1.0`
- [ ] Clean build directory (`rm -rf dist/ build/`)

---

## Installation for End Users

### Quick Installation (Recommended)

```bash
# Using pip (most common)
pip install temporalio-graphs

# Using uv (fastest)
uv pip install temporalio-graphs

# Using poetry
poetry add temporalio-graphs
```

### Installation with Extras

```bash
# Development installation (includes test tools)
pip install temporalio-graphs[dev]

# From specific version
pip install temporalio-graphs==0.1.0

# Latest pre-release (if available)
pip install --pre temporalio-graphs
```

### Verify Installation

```bash
# Check installation
python -c "import temporalio_graphs; print(temporalio_graphs.__version__)"
# Output: 0.1.0

# Check type hints available
python -c "from temporalio_graphs import analyze_workflow; print(analyze_workflow.__annotations__)"
```

---

## Usage Examples

### 1. Basic Usage (3 lines)

```python
from temporalio_graphs import analyze_workflow

result = analyze_workflow("my_workflow.py")
print(result)
```

**Output**: Complete Mermaid diagram showing all workflow paths

---

### 2. Save to File

```python
from temporalio_graphs import analyze_workflow, GraphBuildingContext
from pathlib import Path

# Method 1: Configure output file
context = GraphBuildingContext(
    graph_output_file=Path("docs/workflow_diagram.md")
)
analyze_workflow("workflow.py", context)

# Method 2: Save manually
result = analyze_workflow("workflow.py")
Path("diagram.md").write_text(result)
```

---

### 3. Custom Configuration

```python
from temporalio_graphs import analyze_workflow, GraphBuildingContext

# Customize labels and behavior
context = GraphBuildingContext(
    split_names_by_words=False,        # Keep camelCase names
    start_node_label="Initialize",      # Custom start label
    end_node_label="Complete",          # Custom end label
    suppress_validation=True,           # Disable warnings
    max_decision_points=15,             # Allow more decisions
    max_paths=32768                     # Allow more paths
)

result = analyze_workflow("complex_workflow.py", context)
```

---

### 4. Error Handling

```python
from temporalio_graphs import (
    analyze_workflow,
    TemporalioGraphsError,
    WorkflowParseError,
    GraphGenerationError
)

try:
    result = analyze_workflow("workflow.py")
    print(result)
except WorkflowParseError as e:
    print(f"Parse error: {e.message}")
    print(f"File: {e.file_path}:{e.line}")
    print(f"Suggestion: {e.suggestion}")
except GraphGenerationError as e:
    print(f"Generation error: {e}")
except TemporalioGraphsError as e:
    print(f"Library error: {e}")
```

---

### 5. Multi-Workflow Analysis

```python
from temporalio_graphs import analyze_workflow_graph, GraphBuildingContext

# Analyze parent workflow with child workflows
context = GraphBuildingContext(
    child_workflow_expansion="inline"  # or "reference", "subgraph"
)

result = analyze_workflow_graph("parent_workflow.py", context)
print(result)
```

---

### 6. Integration in CI/CD

```python
# ci_workflow_check.py
from pathlib import Path
from temporalio_graphs import analyze_workflow

def generate_workflow_docs():
    """Generate workflow diagrams for documentation"""
    workflows = Path("src/workflows").glob("*.py")

    for workflow_file in workflows:
        output_file = Path(f"docs/diagrams/{workflow_file.stem}.md")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        diagram = analyze_workflow(workflow_file)
        output_file.write_text(diagram)
        print(f"Generated: {output_file}")

if __name__ == "__main__":
    generate_workflow_docs()
```

**Run in CI:**
```bash
python ci_workflow_check.py
git add docs/diagrams/
git commit -m "docs: update workflow diagrams"
```

---

### 7. Type Hints Support

The package includes full type hints with `py.typed` marker:

```python
from temporalio_graphs import analyze_workflow, GraphBuildingContext
from pathlib import Path

# Type checkers (mypy, pyright) will validate:
result: str = analyze_workflow(Path("workflow.py"))  # ✅ Valid
context: GraphBuildingContext = GraphBuildingContext(max_paths=2048)  # ✅ Valid

# These will show type errors:
# analyze_workflow(123)  # ❌ Error: Expected str or Path
# GraphBuildingContext(invalid_arg=True)  # ❌ Error: Unknown argument
```

---

## Project Integration Patterns

### Pattern 1: Add to requirements.txt

```txt
# requirements.txt
temporalio>=1.7.1
temporalio-graphs>=0.1.0
```

Install:
```bash
pip install -r requirements.txt
```

---

### Pattern 2: Add to pyproject.toml

```toml
# pyproject.toml
[project]
dependencies = [
    "temporalio>=1.7.1",
    "temporalio-graphs>=0.1.0",
]

[project.optional-dependencies]
dev = [
    "temporalio-graphs>=0.1.0",  # Optional: dev-only
    "pytest>=8.0.0",
]
```

Install:
```bash
pip install -e .              # Install project dependencies
pip install -e ".[dev]"       # Install with dev dependencies
```

---

### Pattern 3: Poetry Integration

```bash
# Add dependency
poetry add temporalio-graphs

# Add as dev dependency (optional)
poetry add --group dev temporalio-graphs
```

```toml
# pyproject.toml (poetry)
[tool.poetry.dependencies]
python = "^3.10"
temporalio = "^1.7.1"
temporalio-graphs = "^0.1.0"
```

---

### Pattern 4: Docker Integration

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Generate workflow diagrams at build time
COPY src/workflows/ /app/workflows/
RUN python -c "from temporalio_graphs import analyze_workflow; \
    from pathlib import Path; \
    [Path(f'/docs/{f.stem}.md').write_text(analyze_workflow(f)) \
     for f in Path('/app/workflows').glob('*.py')]"
```

---

## Version Management

### Semantic Versioning

Follow SemVer (MAJOR.MINOR.PATCH):
- **MAJOR**: Breaking API changes (0.x.x → 1.0.0)
- **MINOR**: New features, backward compatible (0.1.0 → 0.2.0)
- **PATCH**: Bug fixes, backward compatible (0.1.0 → 0.1.1)

### Release Process

```bash
# 1. Update version in pyproject.toml
sed -i 's/version = "0.1.0"/version = "0.2.0"/' pyproject.toml

# 2. Update CHANGELOG.md
# Add new version section with changes

# 3. Update __init__.py version
sed -i 's/__version__ = "0.1.0"/__version__ = "0.2.0"/' src/temporalio_graphs/__init__.py

# 4. Commit changes
git add pyproject.toml CHANGELOG.md src/temporalio_graphs/__init__.py
git commit -m "chore: bump version to 0.2.0"

# 5. Create git tag
git tag -a v0.2.0 -m "Release version 0.2.0"
git push origin main --tags

# 6. Build and publish
rm -rf dist/
uv build
uv publish
```

---

## Troubleshooting

### Issue: Build fails with "No module named 'temporalio'"

**Solution**: Dependencies not installed
```bash
uv sync  # Install dependencies first
uv build  # Then build
```

---

### Issue: PyPI upload fails with "File already exists"

**Solution**: Version already published
```bash
# Bump version in pyproject.toml
# Then rebuild and publish
uv build
uv publish
```

---

### Issue: Import fails after installation

**Solution**: Check package name
```bash
# ❌ Wrong
import temporalio_graphs  # Dash in name

# ✅ Correct
from temporalio_graphs import analyze_workflow  # Underscore in import
```

---

### Issue: Type hints not working

**Verify py.typed exists:**
```bash
python -c "import temporalio_graphs; import pkg_resources; \
    print(pkg_resources.resource_filename('temporalio_graphs', 'py.typed'))"
```

---

## Best Practices

1. **Always test before publishing**:
   ```bash
   pytest -v --cov=src/temporalio_graphs
   mypy src/
   ruff check src/
   ```

2. **Use TestPyPI first** for new releases

3. **Version tagging**:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

4. **Clean builds**:
   ```bash
   rm -rf dist/ build/ *.egg-info
   uv build
   ```

5. **Changelog updates**: Document all changes in CHANGELOG.md

---

## Quick Reference

### Build & Publish
```bash
# Build
uv build

# Test publish
uv publish --publish-url https://test.pypi.org/legacy/

# Production publish
uv publish
```

### Install
```bash
# End user
pip install temporalio-graphs

# Developer
git clone <repo>
cd temporalio-graphs
uv sync
```

### Use
```python
from temporalio_graphs import analyze_workflow
result = analyze_workflow("workflow.py")
print(result)
```

---

## Resources

- **PyPI Package**: https://pypi.org/project/temporalio-graphs/
- **Source Code**: https://github.com/yourusername/temporalio-graphs
- **Documentation**: README.md, docs/api-reference.md
- **Issues**: https://github.com/yourusername/temporalio-graphs/issues
- **Python Packaging Guide**: https://packaging.python.org/
