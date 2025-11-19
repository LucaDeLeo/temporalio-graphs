"""Exception classes for temporalio_graphs library.

This module defines all custom exceptions raised by the library.
"""


class TemporalioGraphsError(Exception):
    """Base exception for all temporalio_graphs errors."""

    pass


class WorkflowParseError(TemporalioGraphsError):
    """Raised when workflow parsing fails.

    This exception is raised when:
    - Required decorators (@workflow.defn, @workflow.run) are missing
    - Python syntax errors prevent AST parsing
    - File validation fails (file not found, not valid Python)
    - Workflow structure is invalid or malformed
    """

    pass


class GraphGenerationError(TemporalioGraphsError):
    """Raised when graph generation fails.

    This exception is raised when:
    - Workflow has too many decision points for path generation
    - Path explosion would exceed configured limits
    - Other graph generation constraints are violated
    """

    pass


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
