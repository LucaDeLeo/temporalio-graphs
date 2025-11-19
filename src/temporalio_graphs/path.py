"""Execution path tracking for workflow graph generation.

This module provides the GraphPath class which tracks a single execution path
through a workflow, recording all activities, decisions, and signals encountered
along that path.
"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class PathStep:
    """Represents a single step in a workflow execution path.

    A step can be an activity, decision, or signal (Epic 4). This typed structure
    eliminates the need for string parsing to determine node types, making the
    code more robust and type-safe.

    Args:
        node_type: Type of node ('activity', 'decision', 'signal')
        name: Human-readable name (e.g., 'withdraw_funds', 'NeedToConvert')
        decision_id: Unique decision ID (e.g., 'd0', 'd1'), only for decisions
        decision_value: Boolean value for this path (True/False), only for decisions
        signal_outcome: Signal result ('Signaled'/'Timeout'), only for signals (Epic 4)

    Example:
        >>> # Activity step
        >>> PathStep('activity', 'withdraw_funds')
        PathStep(node_type='activity', name='withdraw_funds', decision_id=None, decision_value=None)

        >>> # Decision step
        >>> PathStep('decision', 'NeedToConvert', decision_id='d0', decision_value=True)
        PathStep(node_type='decision', name='NeedToConvert', decision_id='d0', decision_value=True)
    """
    node_type: Literal['activity', 'decision', 'signal']
    name: str
    decision_id: str | None = None
    decision_value: bool | None = None
    signal_outcome: str | None = None  # Epic 4: 'Signaled' or 'Timeout'


@dataclass
class GraphPath:
    """Tracks a single execution path through a workflow.

    A GraphPath represents one possible execution sequence through a workflow,
    with all activities, decisions, and signals recorded in order. Each path
    corresponds to a unique combination of decision outcomes (true/false) and
    signal results (success/timeout).

    The class maintains:
    - A unique path identifier
    - An ordered list of steps (activity names, decision names, etc.)
    - A mapping of decision IDs to their values (true/false) for this path

    Node IDs are auto-generated sequentially for activities ("1", "2", "3", ...),
    ensuring each activity gets a unique identifier in the resulting graph.

    Epic 2 scope: Only activity tracking is fully implemented. Decision and signal
    methods are stubs that will be completed in Epic 3 and Epic 4 respectively.

    Args:
        path_id: Unique identifier for this execution path. Typically a
            sequential number or a binary string representing decision choices
            (e.g., "0b00", "0b01", "0b10", "0b11" for 2 decisions).
        steps: Ordered list of step names encountered in this path. Includes
            activities, decisions, and signals. Empty by default.
        decisions: Mapping of decision IDs to their boolean values for this
            specific path. Empty by default. Used in Epic 3.

    Example:
        >>> # Create a new path
        >>> path = GraphPath(path_id="0b00")
        >>> assert path.steps == []
        >>> assert path.decisions == {}

        >>> # Add activities to the path
        >>> node_id_1 = path.add_activity("ValidateInput")
        >>> node_id_2 = path.add_activity("ProcessOrder")
        >>> node_id_3 = path.add_activity("SendConfirmation")
        >>> assert node_id_1 == "1"
        >>> assert node_id_2 == "2"
        >>> assert node_id_3 == "3"
        >>> assert path.steps == ["ValidateInput", "ProcessOrder", "SendConfirmation"]

        >>> # Decision tracking (Epic 3)
        >>> # decision_id = path.add_decision("0", True, "HighValue")
        >>> # Not implemented in Epic 2 - raises NotImplementedError

        >>> # Signal tracking (Epic 4)
        >>> # signal_id = path.add_signal("WaitForApproval", "Signaled")
        >>> # Not implemented in Epic 2 - raises NotImplementedError
    """

    path_id: str
    steps: list[PathStep] = field(default_factory=list)
    decisions: dict[str, bool] = field(default_factory=dict)

    def add_activity(self, name: str) -> str:
        """Add an activity to this execution path.

        Records the activity name in the steps list and generates a unique
        node ID for the activity. Node IDs are sequential integers starting
        from 1: "1", "2", "3", etc.

        The activity counter is maintained by counting existing steps. This
        ensures consistent ID generation across path generation.

        Args:
            name: Activity method name (e.g., "ValidateInput", "ProcessOrder").
                May be formatted with split_names_by_words in the renderer.

        Returns:
            Auto-generated node ID for this activity. Sequential string starting
            from "1".

        Example:
            >>> path = GraphPath(path_id="0")
            >>> path.add_activity("Withdraw")
            '1'
            >>> path.add_activity("CurrencyConvert")
            '2'
            >>> path.add_activity("Deposit")
            '3'
            >>> [step.name for step in path.steps]
            ['Withdraw', 'CurrencyConvert', 'Deposit']
        """
        step = PathStep(node_type='activity', name=name)
        self.steps.append(step)
        # Generate sequential node ID: count of all steps so far
        node_id = str(len(self.steps))
        return node_id

    def add_decision(self, id: str, value: bool, name: str) -> str:
        """Add a decision point to this execution path.

        Records the decision ID and its boolean value for this path, adds the
        decision name to the steps list, and generates a unique node ID for the
        decision diamond in the graph.

        This method is called during path generation in PathPermutationGenerator
        to track decisions encountered along each execution path. A decision point
        with value=True represents the "yes" branch; value=False represents
        the "no" branch.

        Args:
            id: Unique identifier for the decision point (e.g., "0", "1").
            value: Boolean value of the decision for this path (True or False).
                True = "yes" branch, False = "no" branch.
            name: Human-readable decision name (e.g., "HighValue", "NeedToConvert").

        Returns:
            Node ID for the decision node. Follows same sequential format as
            add_activity(): "1", "2", "3", etc.

        Example:
            >>> path = GraphPath(path_id="0b01")
            >>> node_id = path.add_decision("0", True, "HighValue")
            >>> node_id
            '1'
            >>> [step.name for step in path.steps]
            ['HighValue']
            >>> path.decisions
            {'0': True}
        """
        # Record the decision value in the decisions dict
        self.decisions[id] = value

        # Add decision step to the steps list with type information
        step = PathStep(
            node_type='decision',
            name=name,
            decision_id=id,
            decision_value=value
        )
        self.steps.append(step)

        # Generate sequential node ID: count of all steps so far
        node_id = str(len(self.steps))

        return node_id

    def add_signal(self, name: str, outcome: str) -> str:
        """Add a signal point to this execution path.

        Records the signal name and outcome (e.g., "Signaled" or "Timeout")
        for this path, adds the signal to the steps list, and generates a unique
        node ID for the signal hexagon in the graph.

        This method is called during path generation in PathPermutationGenerator
        to track signals encountered along each execution path. A signal with
        outcome="Signaled" represents successful signal receipt; outcome="Timeout"
        represents the timeout branch.

        Args:
            name: Human-readable signal name (e.g., "WaitForApproval").
            outcome: Signal result for this path ("Signaled" or "Timeout").

        Returns:
            Node ID for the signal node. Follows same sequential format as
            add_activity(): "1", "2", "3", etc.

        Example:
            >>> path = GraphPath(path_id="0b10")
            >>> node_id = path.add_signal("WaitForApproval", "Signaled")
            >>> node_id
            '1'
            >>> [step.name for step in path.steps]
            ['WaitForApproval']
            >>> [step.signal_outcome for step in path.steps]
            ['Signaled']
        """
        # Add signal step to the steps list with type information
        step = PathStep(
            node_type='signal',
            name=name,
            signal_outcome=outcome
        )
        self.steps.append(step)

        # Generate sequential node ID: count of all steps so far
        node_id = str(len(self.steps))

        return node_id
