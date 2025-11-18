"""AST-based workflow analyzer for extracting Temporal workflow structure.

This module provides the WorkflowAnalyzer class which uses Python's Abstract Syntax
Tree (AST) to parse Temporal workflow source files and extract workflow metadata
including class definitions, run methods, and structural information.

The analyzer implements the Visitor Pattern via ast.NodeVisitor to traverse workflow
source code without executing it, enabling fast (<1ms) static analysis of workflow
structure.

Example:
    >>> from pathlib import Path
    >>> from temporalio_graphs.analyzer import WorkflowAnalyzer
    >>> analyzer = WorkflowAnalyzer()
    >>> metadata = analyzer.analyze("workflows/money_transfer.py")
    >>> print(f"Workflow: {metadata.workflow_class}")
    Workflow: MoneyTransferWorkflow
    >>> print(f"Run method: {metadata.workflow_run_method}")
    Run method: run
"""

import ast
import logging
from pathlib import Path

from temporalio_graphs._internal.graph_models import WorkflowMetadata
from temporalio_graphs.exceptions import WorkflowParseError

logger = logging.getLogger(__name__)


class WorkflowAnalyzer(ast.NodeVisitor):
    """AST-based analyzer for extracting Temporal workflow structure.

    This class extends ast.NodeVisitor to traverse Python workflow source files
    and extract workflow metadata including the workflow class decorated with
    @workflow.defn and the run method decorated with @workflow.run.

    The analyzer uses static code analysis without executing the workflow code,
    achieving sub-millisecond performance for typical workflow files.

    Attributes:
        _workflow_class: Name of the detected workflow class (None if not found).
        _workflow_run_method: Name of the detected run method (None if not found).
        _source_file: Path to the workflow source file being analyzed.
        _line_numbers: Dictionary mapping element names to source line numbers.

    Example:
        >>> analyzer = WorkflowAnalyzer()
        >>> metadata = analyzer.analyze("workflows/money_transfer.py")
        >>> assert metadata.workflow_class == "MoneyTransferWorkflow"
        >>> assert metadata.workflow_run_method == "run"
        >>> assert metadata.total_paths == 1  # Linear workflow in Epic 2
    """

    def __init__(self) -> None:
        """Initialize the workflow analyzer with empty state."""
        self._workflow_class: str | None = None
        self._workflow_run_method: str | None = None
        self._source_file: Path | None = None
        self._line_numbers: dict[str, int] = {}
        self._inside_workflow_class: bool = False

    def analyze(self, workflow_file: Path | str) -> WorkflowMetadata:
        """Analyze a workflow source file and extract workflow metadata.

        This method parses the workflow source file using Python's AST parser,
        traverses the syntax tree to find @workflow.defn classes and @workflow.run
        methods, and returns a WorkflowMetadata object with the extracted structure.

        Args:
            workflow_file: Path to workflow source file (relative or absolute).
                Can be a Path object or string path.

        Returns:
            WorkflowMetadata object containing:
                - workflow_class: Name of the workflow class
                - workflow_run_method: Name of the run method
                - activities: Empty list (populated in Story 2.3)
                - decision_points: Empty list (populated in Epic 3)
                - signal_points: Empty list (populated in Epic 4)
                - source_file: Absolute path to analyzed file
                - total_paths: 1 for linear workflows

        Raises:
            FileNotFoundError: If workflow_file does not exist.
            PermissionError: If workflow_file cannot be read.
            WorkflowParseError: If no @workflow.defn class found, syntax errors,
                or workflow structure is invalid.

        Example:
            >>> analyzer = WorkflowAnalyzer()
            >>> metadata = analyzer.analyze("workflows/my_workflow.py")
            >>> print(metadata.workflow_class)
            MyWorkflow
        """
        # Reset state for new analysis
        self._workflow_class = None
        self._workflow_run_method = None
        self._line_numbers = {}
        self._inside_workflow_class = False

        # Convert to absolute path
        path = Path(workflow_file).resolve()
        self._source_file = path

        # Validate file exists
        if not path.exists():
            raise FileNotFoundError(
                f"Workflow file not found: {path}\nPlease check the file path and try again."
            )

        # Validate file is readable
        try:
            source = path.read_text(encoding="utf-8")
        except PermissionError as e:
            raise PermissionError(
                f"Cannot read workflow file: {path}\nPermission denied: {e}"
            ) from e

        # Warn if file extension is not .py
        if path.suffix != ".py":
            logger.warning(
                f"File does not have .py extension: {path}\n"
                f"Analysis may fail if file is not valid Python code."
            )

        # Parse AST
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as e:
            raise WorkflowParseError(
                f"Syntax error in workflow file: {path}\n"
                f"Line {e.lineno}: {e.msg}\n"
                f"Please fix the syntax error and try again."
            ) from e

        # Traverse AST to find workflow elements
        self.visit(tree)

        # Check if workflow class was found
        if self._workflow_class is None:
            raise WorkflowParseError(
                f"No @workflow.defn decorated class found in {path}\n"
                f"Ensure the workflow class has @workflow.defn decorator from temporalio"
            )

        # Check if run method was found
        if self._workflow_run_method is None:
            raise WorkflowParseError(
                f"No @workflow.run decorated method found in workflow class "
                f"'{self._workflow_class}'\n"
                f"Ensure the workflow class has a @workflow.run decorated method"
            )

        # Build and return WorkflowMetadata
        return WorkflowMetadata(
            workflow_class=self._workflow_class,
            workflow_run_method=self._workflow_run_method,
            activities=[],  # Populated in Story 2.3
            decision_points=[],  # Populated in Epic 3
            signal_points=[],  # Populated in Epic 4
            source_file=path,
            total_paths=1,  # Linear workflows only in Epic 2
        )

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition nodes to find @workflow.defn decorated classes.

        This visitor method is called for each class definition in the AST.
        It checks if the class has a @workflow.defn decorator and stores the
        class name and line number if found.

        Args:
            node: AST node representing a class definition.
        """
        # Check if class has @workflow.defn decorator
        for decorator in node.decorator_list:
            if self._is_workflow_decorator(decorator, "defn"):
                self._workflow_class = node.name
                self._line_numbers["workflow_class"] = node.lineno
                self._inside_workflow_class = True
                logger.debug(f"Found workflow class: {node.name} at line {node.lineno}")
                break

        # Continue traversal to find run method inside class
        self.generic_visit(node)

        # Reset flag after visiting class
        self._inside_workflow_class = False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition nodes to find @workflow.run decorated methods.

        This visitor method is called for each function/method definition in the AST.
        It checks if the method has a @workflow.run decorator (only within detected
        workflow classes) and stores the method name and line number if found.

        Args:
            node: AST node representing a function/method definition.
        """
        # Only process if inside a workflow class
        if not self._inside_workflow_class:
            return

        # Check if method has @workflow.run decorator
        for decorator in node.decorator_list:
            if self._is_workflow_decorator(decorator, "run"):
                self._workflow_run_method = node.name
                self._line_numbers["workflow_run_method"] = node.lineno
                logger.debug(f"Found run method: {node.name} at line {node.lineno}")
                break

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition nodes to find @workflow.run methods.

        This visitor method handles async methods, which are common in Temporal
        workflows. It delegates to the same logic as visit_FunctionDef.

        Args:
            node: AST node representing an async function/method definition.
        """
        # Only process if inside a workflow class
        if not self._inside_workflow_class:
            return

        # Check if method has @workflow.run decorator
        for decorator in node.decorator_list:
            if self._is_workflow_decorator(decorator, "run"):
                self._workflow_run_method = node.name
                self._line_numbers["workflow_run_method"] = node.lineno
                logger.debug(f"Found async run method: {node.name} at line {node.lineno}")
                break

    def _is_workflow_decorator(self, decorator: ast.expr, target: str) -> bool:
        """Check if a decorator is a workflow decorator (@workflow.defn or @workflow.run).

        This helper method identifies Temporal workflow decorators by matching
        AST patterns for both attribute access (@workflow.defn) and direct
        imports (if user imports defn/run directly).

        Args:
            decorator: AST expression node representing the decorator.
            target: Target decorator name ("defn" or "run").

        Returns:
            True if decorator matches @workflow.{target}, False otherwise.

        Example:
            Matches these patterns:
            - @workflow.defn (ast.Attribute with value.id="workflow", attr="defn")
            - @workflow.run (ast.Attribute with value.id="workflow", attr="run")
            - @defn (ast.Name with id="defn", if imported directly)
        """
        # Handle attribute access: @workflow.defn or @workflow.run
        if isinstance(decorator, ast.Attribute):
            if decorator.attr == target:
                if isinstance(decorator.value, ast.Name) and decorator.value.id == "workflow":
                    return True

        # Handle direct import: @defn or @run (from temporalio.workflow import defn)
        if isinstance(decorator, ast.Name):
            if decorator.id == target:
                return True

        return False
