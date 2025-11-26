"""Plain Python file without @workflow.defn decorator.

Used for testing WorkflowParseError when analyzing non-workflow files.
"""


class RegularClass:
    """A regular Python class, not a Temporal workflow."""

    def __init__(self) -> None:
        """Initialize the class."""
        self.value = 0

    def process(self) -> int:
        """Process something."""
        self.value += 1
        return self.value
