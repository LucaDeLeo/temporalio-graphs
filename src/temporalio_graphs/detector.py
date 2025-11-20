"""Decision point detector for identifying to_decision() calls in workflows.

This module provides the DecisionDetector class which uses Python's Abstract Syntax
Tree (AST) to identify and extract decision point metadata from Temporal workflow
code. A decision point is marked by an explicit to_decision() helper call.

The detector implements the Visitor Pattern via ast.NodeVisitor to traverse workflow
AST and extract decision metadata including names, line numbers, and boolean expressions.

Example:
    >>> import ast
    >>> from temporalio_graphs.detector import DecisionDetector
    >>> source = '''
    ... if await to_decision(amount > 1000, "HighValue"):
    ...     pass
    ... '''
    >>> tree = ast.parse(source)
    >>> detector = DecisionDetector()
    >>> detector.visit(tree)
    >>> print(len(detector.decisions))
    1
    >>> print(detector.decisions[0].name)
    HighValue
"""

import ast
import logging
from pathlib import Path

from temporalio_graphs._internal.graph_models import ChildWorkflowCall, DecisionPoint, SignalPoint
from temporalio_graphs.exceptions import InvalidSignalError, WorkflowParseError

logger = logging.getLogger(__name__)


class DecisionDetector(ast.NodeVisitor):
    """Detects to_decision() helper calls in workflow AST.

    This class extends ast.NodeVisitor to traverse Python workflow source files
    and extract decision point metadata. It identifies explicit to_decision() calls,
    extracts decision names and boolean expressions, and tracks source line numbers.

    The detector handles various patterns:
    - Simple if statements: if await to_decision(condition, "Name"):
    - Result assignments: result = await to_decision(expr, "Choice")
    - elif chains: multiple decisions detected separately
    - Ternary operators: to_decision(x if test else y, "Ternary")

    Attributes:
        _decisions: List of detected DecisionPoint objects.
        _decision_counter: Sequential counter for generating unique decision IDs.

    Example:
        >>> detector = DecisionDetector()
        >>> tree = ast.parse(workflow_source)
        >>> detector.visit(tree)
        >>> for decision in detector.decisions:
        ...     print(f"Decision: {decision.name} at line {decision.line_number}")
    """

    def __init__(self) -> None:
        """Initialize the decision detector with empty state."""
        self._decisions: list[DecisionPoint] = []
        self._decision_counter: int = 0
        # Map from decision line number to (true_branch_lines, false_branch_lines)
        self._decision_branches: dict[int, tuple[list[int], list[int]]] = {}

    def visit_Call(self, node: ast.Call) -> None:
        """Visit Call nodes to identify to_decision() function calls.

        This visitor method is called for each function call in the AST. It checks
        if the call is to the to_decision() function and extracts decision metadata
        if found.

        Args:
            node: AST node representing a function call.
        """
        if self._is_to_decision_call(node):
            try:
                name = self._extract_decision_name(node)
                self._extract_decision_expression(node)  # Validate expression exists
                line_number = node.lineno

                decision_id = self._generate_decision_id()

                # Look up branch activities for this decision
                true_branch_lines: list[int] = []
                false_branch_lines: list[int] = []
                if line_number in self._decision_branches:
                    true_branch_lines, false_branch_lines = self._decision_branches[line_number]

                decision = DecisionPoint(
                    id=decision_id,
                    name=name,
                    line_number=line_number,
                    line_num=line_number,  # For execution order sorting
                    true_label="yes",
                    false_label="no",
                    true_branch_activities=tuple(true_branch_lines),
                    false_branch_activities=tuple(false_branch_lines),
                )
                self._decisions.append(decision)
                logger.debug(
                    f"Detected decision '{name}' at line {line_number} (id={decision_id}) "
                    f"with {len(true_branch_lines)} true-branch activities, "
                    f"{len(false_branch_lines)} false-branch activities"
                )
            except WorkflowParseError as e:
                # Re-raise parse errors with full context
                raise e

        # Continue traversal to find nested calls
        self.generic_visit(node)

    def _collect_activity_lines(self, nodes: list[ast.stmt]) -> list[int]:
        """Collect line numbers of all execute_activity calls in a block.

        Args:
            nodes: List of AST statement nodes to search.

        Returns:
            List of line numbers where execute_activity is called.
        """
        activity_lines = []

        class ActivityCollector(ast.NodeVisitor):
            def visit_Await(self, node: ast.Await) -> None:
                if isinstance(node.value, ast.Call):
                    call = node.value
                    # Check for workflow.execute_activity, execute_activity_method, or standalone
                    if isinstance(call.func, ast.Attribute):
                        if call.func.attr in ("execute_activity", "execute_activity_method"):
                            activity_lines.append(node.lineno)
                    elif isinstance(call.func, ast.Name):
                        if call.func.id in ("execute_activity", "execute_activity_method"):
                            activity_lines.append(node.lineno)
                self.generic_visit(node)

        collector = ActivityCollector()
        for stmt in nodes:
            collector.visit(stmt)
        return activity_lines

    def visit_If(self, node: ast.If) -> None:
        """Visit If nodes to detect elif chains as separate decisions.

        This visitor method traverses if/elif/else structures. For elif blocks,
        it identifies to_decision() calls and treats each elif as a separate decision
        point.

        Also tracks which activities are in the true/false branches for control flow.

        Args:
            node: AST node representing an if/elif/else structure.
        """
        # Check if this If node's test contains a to_decision() call
        # If so, we need to track its branch activities
        decision_call = None
        if isinstance(node.test, ast.Await) and isinstance(node.test.value, ast.Call):
            if self._is_to_decision_call(node.test.value):
                decision_call = node.test.value
        elif isinstance(node.test, ast.Call):
            if self._is_to_decision_call(node.test):
                decision_call = node.test

        # If this is a decision block, collect branch activities
        if decision_call:
            true_activities = self._collect_activity_lines(node.body)
            false_activities = self._collect_activity_lines(node.orelse)

            # Store branch info keyed by decision line number
            # This will be looked up when creating the DecisionPoint
            self._decision_branches[decision_call.lineno] = (true_activities, false_activities)

        # Process the if condition
        self.visit(node.test) if hasattr(node, "test") else None

        # Visit the body
        for child in node.body:
            self.visit(child)

        # Handle elif chains (orelse contains another If)
        if node.orelse:
            for child in node.orelse:
                self.visit(child)

    def _is_to_decision_call(self, node: ast.Call) -> bool:
        """Check if a Call node is a to_decision() function call.

        This helper method identifies calls to the to_decision() function by matching
        against the function name. It handles both simple names and attribute access
        (though typically to_decision is imported directly).

        Args:
            node: AST Call node to check.

        Returns:
            True if the call is to to_decision(), False otherwise.
        """
        # Check for simple name: to_decision(...)
        if isinstance(node.func, ast.Name):
            return node.func.id == "to_decision"

        # Check for attribute access: something.to_decision(...)
        if isinstance(node.func, ast.Attribute):
            return node.func.attr == "to_decision"

        return False

    def _extract_decision_name(self, node: ast.Call) -> str:
        """Extract decision name from to_decision() function arguments.

        The decision name is the second argument (first is the boolean expression).
        This helper expects the name to be a string constant.

        Args:
            node: AST Call node for to_decision() call.

        Returns:
            Decision name as a string.

        Raises:
            WorkflowParseError: If name argument missing, not a string, or invalid.
        """
        # Check for keyword argument first: name="MyDecision"
        for keyword in node.keywords:
            if keyword.arg == "name":
                if isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
                    return keyword.value.value
                else:
                    type_name = type(keyword.value).__name__
                    raise WorkflowParseError(
                        file_path=Path("unknown"),
                        line=node.lineno,
                        message=f"to_decision() name argument must be a string. Got {type_name}",
                        suggestion="Use: to_decision(condition, name='MyDecision')",
                    )

        # Check that we have at least 2 positional arguments (expr, name)
        if len(node.args) < 2:
            msg = "to_decision() requires 2 arguments: to_decision(condition, 'name')"
            raise WorkflowParseError(
                file_path=Path("unknown"),
                line=node.lineno,
                message=f"{msg}. Missing name argument",
                suggestion="Provide a string name for this decision point",
            )

        # Get the second argument (name)
        name_arg = node.args[1]

        # Check if it's a string constant
        if isinstance(name_arg, ast.Constant) and isinstance(name_arg.value, str):
            return name_arg.value

        # Name argument is not a string constant
        type_name = type(name_arg).__name__
        raise WorkflowParseError(
            file_path=Path("unknown"),
            line=node.lineno,
            message=f"to_decision() name argument must be a string constant. Got {type_name}",
            suggestion="Use: to_decision(condition, 'MyDecision')",
        )

    def _extract_decision_expression(self, node: ast.Call) -> ast.expr:
        """Extract boolean expression from first argument of to_decision().

        The first argument is the boolean expression that determines the decision.
        This can be a simple comparison (amount > 1000), complex expression
        ((a > 100) and (b < 50)), or ternary operator (x if condition else y).

        Args:
            node: AST Call node for to_decision() call.

        Returns:
            AST node representing the boolean expression.

        Raises:
            WorkflowParseError: If expression argument is missing.
        """
        if len(node.args) < 1:
            raise WorkflowParseError(
                file_path=Path("unknown"),
                line=node.lineno,
                message="to_decision() requires at least 1 argument (the boolean expression)",
                suggestion="Use: to_decision(condition, 'name')",
            )

        return node.args[0]

    def _generate_decision_id(self) -> str:
        """Generate a unique ID for a decision point.

        IDs are sequential (d0, d1, d2, ...) for simplicity and determinism.

        Returns:
            Unique decision ID string.
        """
        decision_id = f"d{self._decision_counter}"
        self._decision_counter += 1
        return decision_id

    @property
    def decisions(self) -> list[DecisionPoint]:
        """Read-only list of detected decision points.

        Returns:
            List of DecisionPoint objects extracted during AST traversal.
        """
        return self._decisions


class SignalDetector(ast.NodeVisitor):
    """Detects wait_condition() helper calls in workflow AST.

    This class extends ast.NodeVisitor to traverse Python workflow source files
    and extract signal point metadata. It identifies wait_condition() calls,
    extracts signal names, condition expressions, timeout expressions, and tracks
    source line numbers.

    The detector handles various patterns:
    - Direct calls: await wait_condition(condition, timeout, "Name")
    - Attribute calls: await workflow.wait_condition(condition, timeout, "Name")
    - Result assignments: result = await wait_condition(...)

    Attributes:
        _signals: List of detected SignalPoint objects.
        _signal_counter: Sequential counter for generating unique signal IDs.

    Example:
        >>> detector = SignalDetector()
        >>> tree = ast.parse(workflow_source)
        >>> detector.visit(tree)
        >>> for signal in detector.signals:
        ...     print(f"Signal: {signal.name} at line {signal.source_line}")
    """

    def __init__(self) -> None:
        """Initialize the signal detector with empty state."""
        self._signals: list[SignalPoint] = []
        self._signal_counter: int = 0
        # Track branch activities for signals:
        # {signal_line: (signaled_activities, timeout_activities)}
        self._signal_branches: dict[int, tuple[list[int], list[int]]] = {}

    def visit_Call(self, node: ast.Call) -> None:
        """Visit Call nodes to identify wait_condition() function calls.

        This visitor method is called for each function call in the AST. It checks
        if the call is to the wait_condition() function and extracts signal metadata
        if found.

        Args:
            node: AST node representing a function call.
        """
        if self._is_wait_condition_call(node):
            try:
                signal_point = self._extract_signal_metadata(node)
                self._signals.append(signal_point)
                logger.debug(
                    f"Detected signal '{signal_point.name}' at line {signal_point.source_line} "
                    f"(id={signal_point.node_id})"
                )
            except InvalidSignalError as e:
                # Re-raise signal errors with full context
                raise e

        # Continue traversal to find nested calls
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        """Visit If nodes to track signal branch activities.

        This visitor method traverses if/else structures that contain wait_condition()
        results. For patterns like `if await wait_condition(...):`, it tracks which
        activities are in the signaled (true) vs timeout (false) branches.

        Args:
            node: AST node representing an if/elif/else structure.
        """
        # Check if this If node's test contains a wait_condition() call
        signal_call = None
        if isinstance(node.test, ast.Await) and isinstance(node.test.value, ast.Call):
            if self._is_wait_condition_call(node.test.value):
                signal_call = node.test.value
        elif isinstance(node.test, ast.Name):
            # Pattern: result = await wait_condition(...); if result:
            # We need to find the assignment, but for now we skip this pattern
            pass

        # If this is a signal-conditional block, collect branch activities
        if signal_call:
            signaled_activities = self._collect_activity_lines(node.body)
            timeout_activities = self._collect_activity_lines(node.orelse)

            # Store branch info keyed by signal line number
            self._signal_branches[signal_call.lineno] = (signaled_activities, timeout_activities)

        # Continue visiting child nodes
        if hasattr(node, "test"):
            self.visit(node.test)

        for child in node.body:
            self.visit(child)

        if node.orelse:
            for child in node.orelse:
                self.visit(child)

    def _collect_activity_lines(self, nodes: list[ast.stmt]) -> list[int]:
        """Collect line numbers of all execute_activity calls in a block.

        Args:
            nodes: List of AST statement nodes to search.

        Returns:
            List of line numbers where execute_activity is called.
        """
        activity_lines = []

        class ActivityCollector(ast.NodeVisitor):
            def visit_Await(self, node: ast.Await) -> None:
                if isinstance(node.value, ast.Call):
                    call = node.value
                    # Check for workflow.execute_activity, execute_activity_method, or standalone
                    if isinstance(call.func, ast.Attribute):
                        if call.func.attr in ("execute_activity", "execute_activity_method"):
                            activity_lines.append(node.lineno)
                    elif isinstance(call.func, ast.Name):
                        if call.func.id in ("execute_activity", "execute_activity_method"):
                            activity_lines.append(node.lineno)
                self.generic_visit(node)

        collector = ActivityCollector()
        for stmt in nodes:
            collector.visit(stmt)
        return activity_lines

    def _is_wait_condition_call(self, node: ast.Call) -> bool:
        """Check if a Call node is a wait_condition() function call.

        This helper method identifies calls to our custom wait_condition() helper
        (imported from temporalio_graphs.helpers). It distinguishes between:

        - Our custom helper: wait_condition(condition, timeout, name) - 3 args
        - Temporal built-in: workflow.wait_condition(lambda: ...) - 1 arg

        The distinction is made by checking argument count:
        - 3 args: Our custom helper (detected)
        - 1 arg: Temporal's built-in (ignored)

        Args:
            node: AST Call node to check.

        Returns:
            True if the call is to our custom wait_condition() helper, False otherwise.
        """
        # Check for simple name: wait_condition(...)
        if isinstance(node.func, ast.Name) and node.func.id == "wait_condition":
            return True

        # Check for attribute access: workflow.wait_condition(...)
        # We need to distinguish between our helper and Temporal's built-in by arg count
        if isinstance(node.func, ast.Attribute) and node.func.attr == "wait_condition":
            # Our custom helper has 3 args, Temporal's built-in has 1 arg
            # Only process if it has 3 args (our custom helper)
            return len(node.args) == 3

        return False

    def _extract_signal_metadata(self, node: ast.Call) -> SignalPoint:
        """Extract signal name and metadata from wait_condition call.

        The wait_condition() call requires 3 arguments:
        1. condition: Lambda or callable for condition check
        2. timeout: timedelta for timeout duration
        3. name: String literal signal name

        Args:
            node: AST Call node for wait_condition() call.

        Returns:
            SignalPoint object with extracted metadata.

        Raises:
            InvalidSignalError: If wait_condition() has fewer than 3 arguments.
        """
        if len(node.args) < 3:
            raise InvalidSignalError(
                file_path="<unknown>",
                line=node.lineno,
                message=(
                    f"wait_condition() requires 3 arguments "
                    f"(condition, timeout, name), got {len(node.args)}"
                ),
            )

        # Extract signal name (3rd argument)
        name_arg = node.args[2]
        if isinstance(name_arg, ast.Constant) and isinstance(name_arg.value, str):
            name = name_arg.value
        else:
            logger.warning(
                f"Signal name at line {node.lineno} is not a string literal - using 'UnnamedSignal'"
            )
            name = "UnnamedSignal"

        # Extract condition expression (1st argument)
        condition_expr = ast.unparse(node.args[0]) if node.args else ""

        # Extract timeout expression (2nd argument)
        timeout_expr = ast.unparse(node.args[1]) if len(node.args) > 1 else ""

        # Generate node ID
        node_id = self._generate_signal_id(name, node.lineno)

        # Get branch activities if available
        signaled_activities: tuple[int, ...] = ()
        timeout_activities: tuple[int, ...] = ()
        if node.lineno in self._signal_branches:
            signaled_list, timeout_list = self._signal_branches[node.lineno]
            signaled_activities = tuple(signaled_list)
            timeout_activities = tuple(timeout_list)

        return SignalPoint(
            name=name,
            condition_expr=condition_expr,
            timeout_expr=timeout_expr,
            source_line=node.lineno,
            node_id=node_id,
            signaled_branch_activities=signaled_activities,
            timeout_branch_activities=timeout_activities,
        )

    def _generate_signal_id(self, name: str, line: int) -> str:
        """Generate deterministic node ID for signal.

        Creates a unique identifier using signal name and source line number.
        This ensures deterministic IDs for regression testing.

        Args:
            name: Signal name from wait_condition() call.
            line: Source line number where signal is defined.

        Returns:
            Deterministic signal node ID in format: sig_{name}_{line}
        """
        # Use name + line for uniqueness and determinism
        safe_name = name.replace(" ", "_").lower()
        return f"sig_{safe_name}_{line}"

    @property
    def signals(self) -> list[SignalPoint]:
        """Read-only list of detected signal points.

        Returns:
            List of SignalPoint objects extracted during AST traversal.
        """
        return self._signals


class ChildWorkflowDetector(ast.NodeVisitor):
    """Detects execute_child_workflow() calls in workflow AST.

    This class extends ast.NodeVisitor to traverse Python workflow source files
    and extract child workflow call metadata. It identifies workflow.execute_child_workflow()
    calls, extracts child workflow names (from class references or string literals),
    and tracks source line numbers for cross-workflow visualization.

    The detector handles various patterns:
    - Class reference: workflow.execute_child_workflow(ChildWorkflow, ...)
    - String literal: workflow.execute_child_workflow("ChildWorkflowName", ...)
    - Multiple calls: Detects all child workflow invocations in parent workflow
    - Nested blocks: Detects calls inside if/else, loops, etc.

    Attributes:
        _child_calls: List of detected ChildWorkflowCall objects.
        _parent_workflow: Name of the parent workflow class.

    Example:
        >>> detector = ChildWorkflowDetector()
        >>> tree = ast.parse(workflow_source)
        >>> detector.set_parent_workflow("ParentWorkflow")
        >>> detector.visit(tree)
        >>> for call in detector.child_calls:
        ...     print(f"Child: {call.workflow_name} at line {call.call_site_line}")
    """

    def __init__(self) -> None:
        """Initialize the child workflow detector with empty state."""
        self._child_calls: list[ChildWorkflowCall] = []
        self._parent_workflow: str = ""

    def set_parent_workflow(self, parent_workflow: str) -> None:
        """Set the parent workflow name for context.

        Args:
            parent_workflow: Name of the parent workflow class.
        """
        self._parent_workflow = parent_workflow

    def visit_Call(self, node: ast.Call) -> None:
        """Visit Call nodes to identify execute_child_workflow() function calls.

        This visitor method is called for each function call in the AST. It checks
        if the call is to workflow.execute_child_workflow() and extracts child
        workflow metadata if found.

        Args:
            node: AST node representing a function call.
        """
        if self._is_execute_child_workflow_call(node):
            try:
                workflow_name = self._extract_child_workflow_name(node)
                call_id = self._generate_call_id(workflow_name, node.lineno)

                child_call = ChildWorkflowCall(
                    workflow_name=workflow_name,
                    call_site_line=node.lineno,
                    call_id=call_id,
                    parent_workflow=self._parent_workflow,
                )
                self._child_calls.append(child_call)
                logger.debug(
                    f"Detected child workflow '{workflow_name}' at line {node.lineno} "
                    f"in parent '{self._parent_workflow}' (id={call_id})"
                )
            except WorkflowParseError as e:
                # Re-raise parse errors with full context
                raise e

        # Continue traversal to find nested calls
        self.generic_visit(node)

    def _is_execute_child_workflow_call(self, node: ast.Call) -> bool:
        """Check if a Call node is an execute_child_workflow() call.

        This helper method identifies calls to workflow.execute_child_workflow()
        by matching against the function name pattern.

        Args:
            node: AST Call node to check.

        Returns:
            True if the call is to execute_child_workflow(), False otherwise.
        """
        # Check for attribute access: workflow.execute_child_workflow(...)
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == "execute_child_workflow":
                # Verify it's called on workflow object
                if isinstance(node.func.value, ast.Name):
                    if node.func.value.id == "workflow":
                        return True
        return False

    def _extract_child_workflow_name(self, node: ast.Call) -> str:
        """Extract child workflow name from execute_child_workflow() call.

        The workflow name can be provided as either:
        1. Class reference: execute_child_workflow(MyWorkflow, ...)
        2. String literal: execute_child_workflow("MyWorkflow", ...)

        Args:
            node: AST Call node for execute_child_workflow() call.

        Returns:
            Child workflow name as a string.

        Raises:
            WorkflowParseError: If workflow name argument is missing or invalid.
        """
        # Check that we have at least 1 argument (the workflow reference)
        if len(node.args) < 1:
            raise WorkflowParseError(
                file_path=Path("unknown"),
                line=node.lineno,
                message=(
                    "execute_child_workflow() requires at least 1 argument "
                    "(workflow class or name)"
                ),
                suggestion=(
                    "Use: workflow.execute_child_workflow(ChildWorkflow, ...) or "
                    "workflow.execute_child_workflow('ChildWorkflowName', ...)"
                ),
            )

        # Get the first argument (workflow reference)
        workflow_arg = node.args[0]

        # Handle class reference: execute_child_workflow(MyWorkflow, ...)
        if isinstance(workflow_arg, ast.Name):
            return workflow_arg.id

        # Handle string literal: execute_child_workflow("MyWorkflow", ...)
        if isinstance(workflow_arg, ast.Constant) and isinstance(workflow_arg.value, str):
            return workflow_arg.value

        # Handle attribute access: execute_child_workflow(MyWorkflow.run, ...)
        # Extract the class name from the attribute access
        if isinstance(workflow_arg, ast.Attribute):
            if isinstance(workflow_arg.value, ast.Name):
                return workflow_arg.value.id
            else:
                # Handle more complex attribute chains if needed
                type_name = type(workflow_arg.value).__name__
                raise WorkflowParseError(
                    file_path=Path("unknown"),
                    line=node.lineno,
                    message=(
                        f"execute_child_workflow() attribute access too complex. "
                        f"Expected ClassName.run, got nested {type_name}"
                    ),
                    suggestion="Use simple pattern: workflow.execute_child_workflow(ChildWorkflow.run, ...)",
                )

        # Workflow argument is not a class reference or string literal
        type_name = type(workflow_arg).__name__
        raise WorkflowParseError(
            file_path=Path("unknown"),
            line=node.lineno,
            message=(
                f"execute_child_workflow() first argument must be a class reference "
                f"or string. Got {type_name}"
            ),
            suggestion=(
                "Use: workflow.execute_child_workflow(ChildWorkflow, ...) or "
                "workflow.execute_child_workflow('ChildWorkflowName', ...)"
            ),
        )

    def _generate_call_id(self, workflow_name: str, line: int) -> str:
        """Generate deterministic call ID for child workflow call.

        Creates a unique identifier using workflow name and source line number.
        This ensures deterministic IDs for regression testing.

        Args:
            workflow_name: Child workflow name from execute_child_workflow() call.
            line: Source line number where call is made.

        Returns:
            Deterministic call ID in format: child_{workflow_name}_{line}
        """
        # Use name + line for uniqueness and determinism
        safe_name = workflow_name.replace(" ", "_").lower()
        return f"child_{safe_name}_{line}"

    @property
    def child_calls(self) -> list[ChildWorkflowCall]:
        """Read-only list of detected child workflow calls.

        Returns:
            List of ChildWorkflowCall objects extracted during AST traversal.
        """
        return self._child_calls
