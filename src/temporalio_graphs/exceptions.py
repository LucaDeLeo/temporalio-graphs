"""Exception classes for temporalio_graphs library.

This module defines all custom exceptions raised by the library.
"""

from pathlib import Path


class TemporalioGraphsError(Exception):
    """Base exception for all temporalio_graphs errors.

    All library-specific exceptions inherit from this base class,
    enabling users to catch all library errors with a single except clause.

    Example:
        >>> try:
        ...     result = analyze_workflow("workflow.py")
        ... except TemporalioGraphsError as e:
        ...     print(f"Library error: {e}")
    """

    pass


class WorkflowParseError(TemporalioGraphsError):
    """Raised when workflow parsing fails.

    This exception is raised when:
    - Required decorators (@workflow.defn, @workflow.run) are missing
    - Python syntax errors prevent AST parsing
    - File validation fails (file not found, permission denied)
    - Workflow structure is invalid or malformed

    Args:
        file_path: Path to workflow file where error occurred.
        line: Line number where error occurred (0 if not applicable).
        message: Detailed error description.
        suggestion: Actionable suggestion for fixing the error.

    Attributes:
        file_path: Path to workflow file where error occurred.
        line: Line number where error occurred.
        message: Detailed error description.
        suggestion: Actionable suggestion for fixing the error.

    Example:
        >>> raise WorkflowParseError(
        ...     file_path=Path("workflow.py"),
        ...     line=42,
        ...     message="Missing @workflow.defn decorator",
        ...     suggestion="Add @workflow.defn decorator to workflow class"
        ... )
    """

    def __init__(
        self, file_path: Path, line: int, message: str, suggestion: str
    ) -> None:
        """Initialize WorkflowParseError with file path, line number, and details.

        Args:
            file_path: Path to workflow file where error occurred.
            line: Line number where error occurred (0 if not applicable).
            message: Detailed error description.
            suggestion: Actionable suggestion for fixing the error.
        """
        formatted_message = (
            f"Cannot parse workflow file: {file_path}\n"
            f"Line {line}: {message}\n"
            f"Suggestion: {suggestion}"
        )
        super().__init__(formatted_message)
        self.file_path = file_path
        self.line = line
        self.message = message
        self.suggestion = suggestion


class UnsupportedPatternError(TemporalioGraphsError):
    """Raised when workflow uses patterns beyond MVP scope.

    This exception is raised when the workflow contains patterns that
    cannot be analyzed with static code analysis, such as:
    - Loops (while/for) that would require dynamic execution
    - Dynamic activity names using variables
    - Complex control flow patterns
    - Reflection or metaprogramming

    Args:
        pattern: Description of the unsupported pattern.
        suggestion: Actionable suggestion for refactoring.
        line: Optional line number where pattern was detected.

    Attributes:
        pattern: Description of the unsupported pattern.
        suggestion: Actionable suggestion for refactoring.
        line: Optional line number where pattern was detected.

    Example:
        >>> raise UnsupportedPatternError(
        ...     pattern="while loop",
        ...     suggestion="Refactor loop into linear activities",
        ...     line=23
        ... )
    """

    def __init__(
        self, pattern: str, suggestion: str, line: int | None = None
    ) -> None:
        """Initialize UnsupportedPatternError with pattern details.

        Args:
            pattern: Description of the unsupported pattern.
            suggestion: Actionable suggestion for refactoring.
            line: Optional line number where pattern was detected.
        """
        line_info = f" at line {line}" if line is not None else ""
        formatted_message = (
            f"Unsupported pattern: {pattern}{line_info}\n" f"Suggestion: {suggestion}"
        )
        super().__init__(formatted_message)
        self.pattern = pattern
        self.suggestion = suggestion
        self.line = line


class GraphGenerationError(TemporalioGraphsError):
    """Raised when graph generation fails.

    This exception is raised when:
    - Workflow has too many decision points for path generation
    - Path explosion would exceed configured limits
    - Graph rendering fails due to invalid structure
    - Other graph generation constraints are violated

    Args:
        reason: Detailed reason for the generation failure.
        context: Optional dictionary with additional context (decision count, limits, etc.).

    Attributes:
        reason: Detailed reason for the generation failure.
        context: Optional dictionary with additional context.

    Example:
        >>> raise GraphGenerationError(
        ...     reason="Too many decision points (12) would generate 4096 paths (limit: 1024)",
        ...     context={"decision_count": 12, "limit": 10, "paths": 4096}
        ... )
    """

    def __init__(self, reason: str, context: dict[str, int] | None = None) -> None:
        """Initialize GraphGenerationError with reason and optional context.

        Args:
            reason: Detailed reason for the generation failure.
            context: Optional dictionary with additional context.
        """
        formatted_message = f"Graph generation failed: {reason}"
        if context is not None:
            formatted_message += f"\nContext: {context}"
        super().__init__(formatted_message)
        self.reason = reason
        self.context = context


class InvalidDecisionError(TemporalioGraphsError):
    """Raised when to_decision() or wait_condition() used incorrectly.

    This exception is raised when helper functions are called with
    invalid parameters or in invalid contexts:
    - to_decision() called without name parameter
    - wait_condition() called with invalid timeout
    - Helper function called outside workflow context
    - Other helper function validation failures

    Args:
        function: Name of the helper function (e.g., "to_decision", "wait_condition").
        issue: Description of what's wrong with the usage.
        suggestion: Actionable suggestion for correct usage.

    Attributes:
        function: Name of the helper function.
        issue: Description of what's wrong with the usage.
        suggestion: Actionable suggestion for correct usage.

    Example:
        >>> raise InvalidDecisionError(
        ...     function="to_decision",
        ...     issue="Missing decision name parameter",
        ...     suggestion="Provide decision name as second argument"
        ... )
    """

    def __init__(self, function: str, issue: str, suggestion: str) -> None:
        """Initialize InvalidDecisionError with function details.

        Args:
            function: Name of the helper function.
            issue: Description of what's wrong with the usage.
            suggestion: Actionable suggestion for correct usage.
        """
        formatted_message = (
            f"Invalid {function} usage: {issue}\n" f"Suggestion: {suggestion}"
        )
        super().__init__(formatted_message)
        self.function = function
        self.issue = issue
        self.suggestion = suggestion


class InvalidSignalError(TemporalioGraphsError):
    """Raised when wait_condition() call is invalid or malformed.

    This exception is raised when:
    - wait_condition() called with fewer than 3 required arguments
    - Signal name argument is missing or invalid
    - Other signal-specific validation failures

    Args:
        file_path: Path to workflow file where error occurred
        line: Line number of invalid wait_condition() call
        message: Detailed error description with actionable suggestion
    """

    def __init__(self, file_path: str, line: int, message: str) -> None:
        """Initialize InvalidSignalError with file path, line number, and message.

        Args:
            file_path: Path to workflow file where error occurred.
            line: Line number of invalid wait_condition() call.
            message: Detailed error description with actionable suggestion.
        """
        full_message = f"{file_path}:{line}: {message}"
        super().__init__(full_message)
        self.file_path = file_path
        self.line = line


class ChildWorkflowNotFoundError(TemporalioGraphsError):
    """Raised when child workflow file cannot be resolved.

    This exception is raised during multi-workflow analysis when a child workflow
    referenced in execute_child_workflow() cannot be located:
    - Child workflow class not found in parent file
    - Child workflow not found in any imported modules
    - Child workflow not found in any search paths
    - Import tracking failed to resolve module path

    Args:
        workflow_name: Name of the child workflow class that could not be found.
        search_paths: List of paths that were searched for the workflow file.
        parent_workflow: Optional name of parent workflow containing the call.

    Attributes:
        workflow_name: Name of the child workflow class that could not be found.
        search_paths: List of paths that were searched for the workflow file.
        parent_workflow: Optional name of parent workflow containing the call.

    Example:
        >>> raise ChildWorkflowNotFoundError(
        ...     workflow_name="ProcessOrderWorkflow",
        ...     search_paths=[Path("workflows"), Path(".")],
        ...     parent_workflow="CheckoutWorkflow"
        ... )
    """

    def __init__(
        self,
        workflow_name: str,
        search_paths: list[Path],
        parent_workflow: str | None = None,
    ) -> None:
        """Initialize ChildWorkflowNotFoundError with workflow name and search paths.

        Args:
            workflow_name: Name of the child workflow class that could not be found.
            search_paths: List of paths that were searched for the workflow file.
            parent_workflow: Optional name of parent workflow containing the call.
        """
        parent_info = f" (called from {parent_workflow})" if parent_workflow else ""
        search_paths_str = ", ".join(str(p) for p in search_paths)
        formatted_message = (
            f"Child workflow '{workflow_name}'{parent_info} could not be found.\n"
            f"Searched in: {search_paths_str}\n"
            f"Suggestion: Ensure the workflow class is defined in a .py file within "
            f"the search paths, or import it explicitly in the parent workflow file."
        )
        super().__init__(formatted_message)
        self.workflow_name = workflow_name
        self.search_paths = search_paths
        self.parent_workflow = parent_workflow


class CircularWorkflowError(TemporalioGraphsError):
    """Raised when circular workflow reference is detected.

    This exception is raised during multi-workflow analysis when a workflow
    calls itself (directly or indirectly), creating a circular dependency:
    - Direct recursion: WorkflowA → WorkflowA
    - Indirect cycle: WorkflowA → WorkflowB → WorkflowA
    - Complex cycle: WorkflowA → WorkflowB → WorkflowC → WorkflowA

    Args:
        workflow_chain: List of workflow class names forming the circular chain.
            Last element is the workflow that creates the cycle.

    Attributes:
        workflow_chain: List of workflow class names forming the circular chain.

    Example:
        >>> raise CircularWorkflowError(
        ...     workflow_chain=["CheckoutWorkflow", "PaymentWorkflow", "CheckoutWorkflow"]
        ... )
    """

    def __init__(self, workflow_chain: list[str]) -> None:
        """Initialize CircularWorkflowError with the workflow chain.

        Args:
            workflow_chain: List of workflow class names forming the circular chain.
        """
        chain_str = " → ".join(workflow_chain)
        formatted_message = (
            f"Circular workflow reference detected: {chain_str}\n"
            f"Suggestion: Refactor workflows to eliminate circular dependencies. "
            f"Consider using signals or activities to break the cycle."
        )
        super().__init__(formatted_message)
        self.workflow_chain = workflow_chain
