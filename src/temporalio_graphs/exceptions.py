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
