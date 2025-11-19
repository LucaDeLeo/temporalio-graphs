"""Multi-workflow call graph analyzer for cross-workflow visualization.

This module provides the WorkflowCallGraphAnalyzer class which recursively analyzes
parent and child workflows to build a complete workflow call graph. It handles:
- Child workflow file resolution via import tracking and filesystem search
- Circular dependency detection with backtracking
- Recursion depth limits to prevent infinite loops
- Parent-child relationship tracking for cross-workflow visualization

Example:
    >>> from pathlib import Path
    >>> from temporalio_graphs.call_graph_analyzer import WorkflowCallGraphAnalyzer
    >>> from temporalio_graphs.context import GraphBuildingContext
    >>> context = GraphBuildingContext(max_expansion_depth=2)
    >>> analyzer = WorkflowCallGraphAnalyzer(context)
    >>> call_graph = analyzer.analyze(Path("parent_workflow.py"))
    >>> print(f"Total workflows: {call_graph.total_workflows}")
    Total workflows: 3
"""

import ast
import logging
from pathlib import Path

from temporalio_graphs._internal.graph_models import (
    ChildWorkflowCall,
    WorkflowCallGraph,
    WorkflowMetadata,
)
from temporalio_graphs.analyzer import WorkflowAnalyzer
from temporalio_graphs.context import GraphBuildingContext
from temporalio_graphs.exceptions import ChildWorkflowNotFoundError, CircularWorkflowError

logger = logging.getLogger(__name__)


class WorkflowCallGraphAnalyzer:
    """Analyzer for building workflow call graphs through recursive analysis.

    This class orchestrates multi-workflow analysis by:
    1. Analyzing the entry workflow to extract child workflow calls
    2. Resolving child workflow files via import tracking and filesystem search
    3. Recursively analyzing each child workflow up to max_expansion_depth
    4. Detecting circular dependencies and preventing infinite recursion
    5. Building a complete WorkflowCallGraph with all relationships

    The analyzer uses WorkflowAnalyzer internally for each workflow file and
    implements three-tier file resolution:
    - Priority 1: Check if workflow is in same file as parent
    - Priority 2: Track imports and resolve via import statements
    - Priority 3: Scan search paths for matching workflow class

    Attributes:
        _context: GraphBuildingContext with configuration including max_expansion_depth.
        _visited_workflows: Set of workflow names in current analysis chain for cycle detection.
        _current_depth: Current recursion depth (0 = entry workflow).

    Example:
        >>> context = GraphBuildingContext(max_expansion_depth=2)
        >>> analyzer = WorkflowCallGraphAnalyzer(context)
        >>> call_graph = analyzer.analyze(
        ...     entry_workflow=Path("workflows/checkout.py"),
        ...     search_paths=[Path("workflows"), Path("common")]
        ... )
        >>> print(f"Root: {call_graph.root_workflow.workflow_class}")
        Root: CheckoutWorkflow
        >>> print(f"Children: {list(call_graph.child_workflows.keys())}")
        Children: ['PaymentWorkflow', 'NotificationWorkflow']
    """

    def __init__(self, context: GraphBuildingContext) -> None:
        """Initialize the workflow call graph analyzer.

        Args:
            context: GraphBuildingContext with configuration including max_expansion_depth
                limit for controlling recursion depth.
        """
        self._context = context
        self._visited_workflows: set[str] = set()
        self._current_depth: int = 0

    def analyze(
        self, entry_workflow: Path, search_paths: list[Path] | None = None
    ) -> WorkflowCallGraph:
        """Analyze entry workflow and recursively discover all child workflows.

        This method performs complete multi-workflow analysis:
        1. Analyzes entry workflow to get WorkflowMetadata with child calls
        2. Resolves each child workflow file using import tracking + search
        3. Recursively analyzes children up to max_expansion_depth
        4. Detects circular dependencies and raises CircularWorkflowError
        5. Builds WorkflowCallGraph with all workflows and relationships

        Args:
            entry_workflow: Path to entry workflow file (parent workflow).
            search_paths: Optional list of directories to search for child workflows.
                If None, defaults to [entry_workflow.parent] (same directory as entry).

        Returns:
            WorkflowCallGraph containing:
                - root_workflow: WorkflowMetadata for entry workflow
                - child_workflows: Dict mapping child names to WorkflowMetadata
                - call_relationships: List of (parent, child) tuples
                - all_child_calls: Complete list of ChildWorkflowCall objects
                - total_workflows: Count of all workflows (root + children)

        Raises:
            FileNotFoundError: If entry_workflow does not exist.
            ChildWorkflowNotFoundError: If child workflow cannot be resolved.
            CircularWorkflowError: If circular workflow dependency detected.
            WorkflowParseError: If workflow file cannot be parsed.

        Example:
            >>> analyzer = WorkflowCallGraphAnalyzer(GraphBuildingContext())
            >>> call_graph = analyzer.analyze(Path("parent.py"))
            >>> assert call_graph.total_workflows >= 1
            >>> assert call_graph.root_workflow.workflow_class is not None
        """
        # Default search paths to parent directory if not specified (AC7)
        if search_paths is None:
            search_paths = [entry_workflow.parent]

        # Resolve entry workflow to absolute path for security (NFR-SEC-Epic6-1)
        entry_workflow = entry_workflow.resolve()

        # Reset state for new analysis
        self._visited_workflows = set()
        self._current_depth = 0

        # Analyze entry workflow to get root metadata
        # First, check how many @workflow.defn classes are in the file
        source = entry_workflow.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(entry_workflow))

        workflow_classes = []
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                # Check if decorated with @workflow.defn
                for decorator in node.decorator_list:
                    if (
                        isinstance(decorator, ast.Attribute)
                        and isinstance(decorator.value, ast.Name)
                        and decorator.value.id == "workflow"
                        and decorator.attr == "defn"
                    ):
                        workflow_classes.append(node.name)

        # If multiple workflows in file, use the last one (convention) but isolate it
        if len(workflow_classes) > 1:
            target_workflow = workflow_classes[-1]
            root_metadata = self._analyze_workflow_from_file(target_workflow, entry_workflow)
        else:
            # Single workflow, safe to analyze directly
            analyzer = WorkflowAnalyzer()
            root_metadata = analyzer.analyze(entry_workflow, self._context)

        logger.info(
            f"Starting multi-workflow analysis from entry workflow: "
            f"{root_metadata.workflow_class}"
        )
        logger.debug(
            f"Entry workflow has {len(root_metadata.child_workflow_calls)} child calls"
        )

        # Initialize call graph structures
        child_workflows: dict[str, WorkflowMetadata] = {}
        call_relationships: list[tuple[str, str]] = []
        all_child_calls: list[ChildWorkflowCall] = []

        # Collect child calls from root
        all_child_calls.extend(root_metadata.child_workflow_calls)

        # Recursively analyze child workflows
        self._analyze_children(
            parent_metadata=root_metadata,
            parent_file=entry_workflow,
            search_paths=search_paths,
            child_workflows=child_workflows,
            call_relationships=call_relationships,
            all_child_calls=all_child_calls,
        )

        total_workflows = 1 + len(child_workflows)

        logger.info(
            f"Multi-workflow analysis complete: {total_workflows} workflows discovered"
        )

        return WorkflowCallGraph(
            root_workflow=root_metadata,
            child_workflows=child_workflows,
            call_relationships=call_relationships,
            all_child_calls=all_child_calls,
            total_workflows=total_workflows,
        )

    def _analyze_children(
        self,
        parent_metadata: WorkflowMetadata,
        parent_file: Path,
        search_paths: list[Path],
        child_workflows: dict[str, WorkflowMetadata],
        call_relationships: list[tuple[str, str]],
        all_child_calls: list[ChildWorkflowCall],
    ) -> None:
        """Recursively analyze child workflows from a parent workflow.

        This method processes all child workflow calls from the parent, resolves
        their files, checks for circular dependencies, enforces depth limits,
        and recursively analyzes each child's children.

        Args:
            parent_metadata: WorkflowMetadata for the parent workflow.
            parent_file: Path to parent workflow file (for import tracking).
            search_paths: List of directories to search for child workflows.
            child_workflows: Mutable dict to populate with child WorkflowMetadata.
            call_relationships: Mutable list to populate with (parent, child) tuples.
            all_child_calls: Mutable list to collect all ChildWorkflowCall objects.
        """
        # Check depth limit before processing children (AC4)
        if self._current_depth >= self._context.max_expansion_depth:
            logger.warning(
                f"Max expansion depth ({self._context.max_expansion_depth}) reached. "
                f"Skipping children of {parent_metadata.workflow_class}"
            )
            return

        # CRITICAL-2 FIX: Add parent to visited set for circular detection
        # This ensures children can detect if they try to call back to parent
        parent_workflow_name = parent_metadata.workflow_class
        self._visited_workflows.add(parent_workflow_name)

        # CRITICAL-1 FIX: Increment depth BEFORE processing children
        # Entry=0, Direct children=1, Grandchildren=2
        self._current_depth += 1

        try:
            # Process each child workflow call
            for child_call in parent_metadata.child_workflow_calls:
                workflow_name = child_call.workflow_name

                # Check for circular dependency (AC3)
                if workflow_name in self._visited_workflows:
                    # Build complete workflow chain for error message
                    workflow_chain = list(self._visited_workflows) + [workflow_name]
                    logger.error(
                        f"Circular workflow reference detected: {' → '.join(workflow_chain)}"
                    )
                    raise CircularWorkflowError(workflow_chain)

                # Skip if already analyzed (from different branch)
                if workflow_name in child_workflows:
                    logger.debug(
                        f"Child workflow {workflow_name} already analyzed, reusing metadata"
                    )
                    # Still need to record this call relationship
                    call_relationships.append(
                        (parent_metadata.workflow_class, workflow_name)
                    )
                    continue

                # Add to visited set for cycle detection
                self._visited_workflows.add(workflow_name)

                try:
                    # Resolve child workflow file (AC2)
                    child_file = self._resolve_child_workflow_file(
                        workflow_name=workflow_name,
                        parent_file=parent_file,
                        search_paths=search_paths,
                    )

                    logger.debug(
                        f"Resolved child workflow {workflow_name} to file: {child_file}"
                    )

                    # Analyze child workflow
                    # Use special method if workflow is in file with multiple workflows
                    child_metadata = self._analyze_workflow_from_file(workflow_name, child_file)

                    # Store child metadata (AC6)
                    child_workflows[workflow_name] = child_metadata

                    # Record call relationship (AC5)
                    call_relationships.append(
                        (parent_metadata.workflow_class, workflow_name)
                    )

                    # Collect child's child calls
                    all_child_calls.extend(child_metadata.child_workflow_calls)

                    logger.info(
                        f"Analyzed child workflow {workflow_name} "
                        f"(depth={self._current_depth}, "
                        f"child_calls={len(child_metadata.child_workflow_calls)})"
                    )

                    # Recursively analyze grandchildren (no need to increment/decrement here)
                    self._analyze_children(
                        parent_metadata=child_metadata,
                        parent_file=child_file,
                        search_paths=search_paths,
                        child_workflows=child_workflows,
                        call_relationships=call_relationships,
                        all_child_calls=all_child_calls,
                    )

                finally:
                    # Backtracking: Remove from visited set after analysis completes (AC3)
                    # This allows same workflow called from different branches (DAG structure)
                    self._visited_workflows.discard(workflow_name)

        finally:
            # CRITICAL-1 FIX: Decrement depth after processing all children
            self._current_depth -= 1
            # CRITICAL-2 FIX: Remove parent from visited set (backtracking)
            self._visited_workflows.discard(parent_workflow_name)

    def _resolve_child_workflow_file(
        self,
        workflow_name: str,
        parent_file: Path,
        search_paths: list[Path],
    ) -> Path:
        """Resolve child workflow file using three-tier resolution strategy.

        Resolution priority (per tech spec):
        1. Check if workflow is defined in same file as parent
        2. Track imports and resolve via import statements
        3. Scan search paths for .py files with matching @workflow.defn class

        Args:
            workflow_name: Name of child workflow class to resolve.
            parent_file: Path to parent workflow file (for import tracking).
            search_paths: List of directories to search for workflow files.

        Returns:
            Absolute Path to child workflow file.

        Raises:
            ChildWorkflowNotFoundError: If child workflow cannot be found after
                exhaustive search across all resolution methods.

        Example:
            >>> analyzer = WorkflowCallGraphAnalyzer(GraphBuildingContext())
            >>> child_file = analyzer._resolve_child_workflow_file(
            ...     workflow_name="ProcessOrderWorkflow",
            ...     parent_file=Path("checkout.py"),
            ...     search_paths=[Path("workflows")]
            ... )
        """
        # Priority 1: Check if workflow is in same file as parent
        if self._is_workflow_in_file(workflow_name, parent_file):
            logger.debug(
                f"Child workflow {workflow_name} found in same file as parent: {parent_file}"
            )
            return parent_file.resolve()

        # Priority 2: Track imports and resolve via import statements
        import_map = self._build_import_map(parent_file)
        if workflow_name in import_map:
            module_path = import_map[workflow_name]
            resolved_file = self._resolve_module_to_file(module_path, parent_file)
            if resolved_file is not None and resolved_file.exists():
                logger.debug(
                    f"Child workflow {workflow_name} resolved via imports: {resolved_file}"
                )
                return resolved_file

        # Priority 3: Scan search paths for matching workflow class
        for search_path in search_paths:
            resolved_file = self._scan_search_path(workflow_name, search_path)
            if resolved_file is not None:
                logger.debug(
                    f"Child workflow {workflow_name} found via filesystem search: {resolved_file}"
                )
                return resolved_file

        # Not found after exhaustive search (AC8)
        logger.error(
            f"Child workflow {workflow_name} not found in any search paths: {search_paths}"
        )
        raise ChildWorkflowNotFoundError(
            workflow_name=workflow_name,
            search_paths=search_paths,
            parent_workflow=parent_file.stem,
        )

    def _is_workflow_in_file(self, workflow_name: str, file_path: Path) -> bool:
        """Check if workflow class is defined in the given file.

        Args:
            workflow_name: Name of workflow class to find.
            file_path: Path to Python file to search.

        Returns:
            True if workflow class with @workflow.defn decorator found in file.
        """
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(file_path))

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == workflow_name:
                    # Check if class has @workflow.defn decorator
                    for decorator in node.decorator_list:
                        if self._is_workflow_decorator(decorator):
                            return True
            return False
        except Exception as e:
            logger.warning(f"Error checking if {workflow_name} in {file_path}: {e}")
            return False

    def _analyze_workflow_from_file(
        self, workflow_name: str, file_path: Path
    ) -> WorkflowMetadata:
        """Analyze a specific workflow class from a file that may contain multiple workflows.

        When multiple workflows are defined in the same file, we need to extract
        just the target workflow. This method creates a temporary file with only
        the target workflow class to ensure WorkflowAnalyzer processes the correct one.

        Args:
            workflow_name: Name of the workflow class to analyze.
            file_path: Path to file containing the workflow class.

        Returns:
            WorkflowMetadata for the specified workflow class.
        """
        import tempfile

        try:
            # Read and parse the file
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(file_path))

            # Find the target workflow class
            target_class = None
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == workflow_name:
                    target_class = node
                    break

            if target_class is None:
                raise ChildWorkflowNotFoundError(
                    workflow_name=workflow_name,
                    search_paths=[file_path.parent],
                    parent_workflow=file_path.stem,
                )

            # Create a temporary file with just the target workflow class and necessary imports
            # Extract imports from original file
            imports = [
                node
                for node in tree.body
                if isinstance(node, (ast.Import, ast.ImportFrom))
            ]

            # Build new module with imports + target class
            new_tree = ast.Module(body=imports + [target_class], type_ignores=[])

            # Write to temporary file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False, dir=file_path.parent
            ) as f:
                f.write(ast.unparse(new_tree))
                temp_file = Path(f.name)

            try:
                # Analyze the temporary file
                analyzer = WorkflowAnalyzer()
                metadata = analyzer.analyze(temp_file, self._context)

                # Update source_file to point to original file (not temp)
                # Create new metadata with correct source file
                return WorkflowMetadata(
                    workflow_class=metadata.workflow_class,
                    workflow_run_method=metadata.workflow_run_method,
                    activities=metadata.activities,
                    decision_points=metadata.decision_points,
                    signal_points=metadata.signal_points,
                    child_workflow_calls=metadata.child_workflow_calls,
                    source_file=file_path,  # Use original file path
                    total_paths=metadata.total_paths,
                )
            finally:
                # Clean up temporary file
                temp_file.unlink()

        except Exception as e:
            logger.error(f"Error analyzing workflow {workflow_name} from {file_path}: {e}")
            raise

    def _is_workflow_decorator(self, decorator: ast.expr) -> bool:
        """Check if decorator is @workflow.defn.

        Args:
            decorator: AST decorator node.

        Returns:
            True if decorator is @workflow.defn or @defn.
        """
        # Handle @workflow.defn
        if isinstance(decorator, ast.Attribute):
            if decorator.attr == "defn":
                if isinstance(decorator.value, ast.Name) and decorator.value.id == "workflow":
                    return True
        # Handle @defn (direct import)
        if isinstance(decorator, ast.Name):
            if decorator.id == "defn":
                return True
        return False

    def _build_import_map(self, file_path: Path) -> dict[str, str]:
        """Build mapping of class names to module paths from import statements.

        Parses parent file's AST for Import and ImportFrom nodes and builds
        a dictionary mapping imported class names to their module paths.

        Args:
            file_path: Path to parent workflow file.

        Returns:
            Dictionary mapping class names to module paths.
            Example: {"PaymentWorkflow": "workflows.payment"}

        Example:
            >>> # For file with: from workflows.payment import PaymentWorkflow
            >>> import_map = analyzer._build_import_map(Path("checkout.py"))
            >>> assert import_map["PaymentWorkflow"] == "workflows.payment"
        """
        import_map: dict[str, str] = {}

        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(file_path))

            for node in ast.walk(tree):
                # Handle: from module import ClassName
                if isinstance(node, ast.ImportFrom):
                    if node.module is not None:
                        for alias in node.names:
                            # alias.name is the imported name (e.g., "PaymentWorkflow")
                            # alias.asname is the "as" name (e.g., "PW" in "import X as PW")
                            imported_name = alias.asname if alias.asname else alias.name
                            import_map[imported_name] = node.module

                # Handle: import module (less common for workflows)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        # For "import workflows.payment as payment"
                        imported_name = alias.asname if alias.asname else alias.name
                        import_map[imported_name] = alias.name

            logger.debug(f"Built import map from {file_path}: {import_map}")
            return import_map

        except Exception as e:
            logger.warning(f"Error building import map from {file_path}: {e}")
            return {}

    def _resolve_module_to_file(
        self, module_path: str, parent_file: Path
    ) -> Path | None:
        """Resolve module path to file path.

        Converts module path (e.g., "workflows.payment") to file path
        (e.g., "workflows/payment.py"). Handles relative and absolute imports.

        Args:
            module_path: Python module path (dot-separated).
            parent_file: Path to parent workflow file (for relative imports).

        Returns:
            Path to module file if resolvable, None otherwise.

        Example:
            >>> # For module_path="workflows.payment"
            >>> resolved = analyzer._resolve_module_to_file("workflows.payment", parent_file)
            >>> # Returns Path("workflows/payment.py")
        """
        try:
            # Convert module path to file path
            # workflows.payment -> workflows/payment.py
            file_path = Path(module_path.replace(".", "/") + ".py")

            # Try absolute path first
            if file_path.exists():
                return file_path.resolve()

            # Try relative to parent file's directory
            relative_path = parent_file.parent / file_path
            if relative_path.exists():
                return relative_path.resolve()

            return None

        except Exception as e:
            logger.warning(f"Error resolving module {module_path} to file: {e}")
            return None

    def _scan_search_path(
        self, workflow_name: str, search_path: Path
    ) -> Path | None:
        """Scan search path for workflow class definition.

        Recursively scans search_path for .py files and checks each file
        for a class matching workflow_name with @workflow.defn decorator.

        Args:
            workflow_name: Name of workflow class to find.
            search_path: Directory to search recursively.

        Returns:
            Path to file containing workflow class, or None if not found.

        Example:
            >>> result = analyzer._scan_search_path("PaymentWorkflow", Path("workflows"))
            >>> # Returns Path("workflows/payment.py") if found
        """
        try:
            # Resolve search path for security (NFR-SEC-Epic6-1)
            search_path = search_path.resolve()

            # Recursively find all .py files in search path
            for py_file in search_path.rglob("*.py"):
                if self._is_workflow_in_file(workflow_name, py_file):
                    return py_file

            return None

        except Exception as e:
            logger.warning(f"Error scanning search path {search_path}: {e}")
            return None
