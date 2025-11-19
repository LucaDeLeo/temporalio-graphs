"""Path list formatting for workflow visualization.

This module provides text-based path list output as an alternative/supplement to
Mermaid diagrams. It converts GraphPath objects into formatted text that shows all
execution paths in a human-readable format.

Key components:
- FormattedPath: Single execution path with activities formatted as text
- PathListOutput: Complete path list with summary statistics
- format_path_list: Converts GraphPath objects to formatted output
"""

from dataclasses import dataclass

from temporalio_graphs.path import GraphPath


@dataclass
class FormattedPath:
    """A single execution path formatted for display.

    Represents one execution path through the workflow with activities extracted
    from the path steps. The format() method renders the path as a readable text
    line showing the sequence: Start → Activity1 → Activity2 → End.

    Args:
        path_number: Sequential path number (1-based) for display
        activities: List of activity names encountered in this path, in order
        decisions: Decision outcomes for this path (decision name → bool value)

    Example:
        >>> path = FormattedPath(
        ...     path_number=1,
        ...     activities=["Withdraw", "CurrencyConvert", "Deposit"],
        ...     decisions={"NeedToConvert": True}
        ... )
        >>> path.format()
        'Path 1: Start → Withdraw → CurrencyConvert → Deposit → End'
    """
    path_number: int
    activities: list[str]
    decisions: dict[str, bool]

    def format(self) -> str:
        """Format path as: Path N: Start → Activity1 → Activity2 → End.

        Returns:
            Formatted path string with arrow-separated steps.

        Example:
            >>> FormattedPath(1, ["Activity1", "Activity2"], {}).format()
            'Path 1: Start → Activity1 → Activity2 → End'
        """
        steps = ["Start"] + self.activities + ["End"]
        return f"Path {self.path_number}: {' → '.join(steps)}"


@dataclass
class PathListOutput:
    """Complete path list with metadata and formatting.

    Aggregates all execution paths with summary statistics. The format() method
    renders a complete report showing:
    - Header with total path count
    - Decision point summary (if any decisions exist)
    - All paths, numbered sequentially

    Args:
        paths: All formatted execution paths
        total_paths: Total number of paths (typically 2^n for n decisions)
        total_decisions: Number of decision points in workflow

    Example:
        >>> paths = [
        ...     FormattedPath(1, ["Withdraw", "Deposit"], {}),
        ...     FormattedPath(2, ["Withdraw", "Convert", "Deposit"], {"NeedToConvert": True})
        ... ]
        >>> output = PathListOutput(paths, total_paths=2, total_decisions=1)
        >>> print(output.format())
        <BLANKLINE>
        --- Execution Paths (2 total) ---
        Decision Points: 1 (2^1 = 2 paths)
        <BLANKLINE>
        Path 1: Start → Withdraw → Deposit → End
        Path 2: Start → Withdraw → Convert → Deposit → End
    """
    paths: list[FormattedPath]
    total_paths: int
    total_decisions: int

    def format(self) -> str:
        """Format complete path list with header and all paths.

        Returns:
            Multi-line string with header, decision info (if any), and all paths.

        Example:
            >>> output = PathListOutput([FormattedPath(1, ["Activity"], {})], 1, 0)
            >>> print(output.format())
            <BLANKLINE>
            --- Execution Paths (1 total) ---
            <BLANKLINE>
            Path 1: Start → Activity → End
        """
        lines = [
            f"\n--- Execution Paths ({self.total_paths} total) ---"
        ]

        # Add decision point summary if decisions exist
        if self.total_decisions > 0:
            lines.append(
                f"Decision Points: {self.total_decisions} "
                f"(2^{self.total_decisions} = {self.total_paths} paths)"
            )

        # Empty line after header
        lines.append("")

        # Add all formatted paths
        for path in self.paths:
            lines.append(path.format())

        return "\n".join(lines)


def format_path_list(paths: list[GraphPath]) -> PathListOutput:
    """Convert GraphPath objects to formatted path list.

    Extracts activities and decisions from each GraphPath and formats them as
    text. Activities are identified by node_type='activity', decisions by
    node_type='decision'. The resulting PathListOutput can be rendered as
    multi-line text showing all execution paths.

    Args:
        paths: All execution paths from path generator. Typically 2^n paths
            for n decision points (e.g., 4 paths for 2 decisions).

    Returns:
        PathListOutput with all paths formatted and ready for display.

    Example:
        >>> from temporalio_graphs.path import GraphPath, PathStep
        >>> path1 = GraphPath(path_id="0b00", steps=[
        ...     PathStep('activity', 'Withdraw'),
        ...     PathStep('activity', 'Deposit')
        ... ], decisions={})
        >>> path2 = GraphPath(path_id="0b01", steps=[
        ...     PathStep('activity', 'Withdraw'),
        ...     PathStep('decision', 'NeedToConvert', decision_id='0', decision_value=True),
        ...     PathStep('activity', 'Convert'),
        ...     PathStep('activity', 'Deposit')
        ... ], decisions={'0': True})
        >>> result = format_path_list([path1, path2])
        >>> print(result.format())
        <BLANKLINE>
        --- Execution Paths (2 total) ---
        Decision Points: 1 (2^1 = 2 paths)
        <BLANKLINE>
        Path 1: Start → Withdraw → Deposit → End
        Path 2: Start → Withdraw → Convert → Deposit → End
    """
    formatted_paths = []

    for i, path in enumerate(paths, 1):
        # Extract activity names using node_type discriminator
        # CRITICAL: Use step.node_type == 'activity', NOT isinstance
        # PathStep is a single dataclass with node_type field, not separate classes
        activities = [
            step.name
            for step in path.steps
            if step.node_type == 'activity'
        ]

        # Extract decision outcomes using node_type discriminator
        decisions = {
            step.name: step.decision_value
            for step in path.steps
            if step.node_type == 'decision' and step.decision_value is not None
        }

        formatted_paths.append(FormattedPath(
            path_number=i,
            activities=activities,
            decisions=decisions
        ))

    # Count total decisions from first path's decisions dict
    # All paths have same decision points, just different values
    total_decisions = len(paths[0].decisions) if paths else 0

    return PathListOutput(
        paths=formatted_paths,
        total_paths=len(paths),
        total_decisions=total_decisions
    )
