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

from temporalio_graphs._internal.graph_models import DecisionPoint
from temporalio_graphs.exceptions import WorkflowParseError

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
                decision = DecisionPoint(
                    id=decision_id,
                    name=name,
                    line_number=line_number,
                    true_label="yes",
                    false_label="no",
                )
                self._decisions.append(decision)
                logger.debug(f"Detected decision '{name}' at line {line_number} (id={decision_id})")
            except WorkflowParseError as e:
                # Re-raise parse errors with full context
                raise e

        # Continue traversal to find nested calls
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        """Visit If nodes to detect elif chains as separate decisions.

        This visitor method traverses if/elif/else structures. For elif blocks,
        it identifies to_decision() calls and treats each elif as a separate decision
        point.

        Args:
            node: AST node representing an if/elif/else structure.
        """
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
                    raise WorkflowParseError(
                        f"Line {node.lineno}: to_decision() name argument must be a string. "
                        f"Got {type(keyword.value).__name__}. "
                        f"Please use: to_decision(condition, name='MyDecision')"
                    )

        # Check that we have at least 2 positional arguments (expr, name)
        if len(node.args) < 2:
            raise WorkflowParseError(
                f"Line {node.lineno}: to_decision() requires 2 arguments: "
                f"to_decision(condition, 'name'). "
                f"Missing name argument. "
                f"Please provide a string name for this decision point."
            )

        # Get the second argument (name)
        name_arg = node.args[1]

        # Check if it's a string constant
        if isinstance(name_arg, ast.Constant) and isinstance(name_arg.value, str):
            return name_arg.value

        # Name argument is not a string constant
        raise WorkflowParseError(
            f"Line {node.lineno}: to_decision() name argument must be a string constant. "
            f"Got {type(name_arg).__name__}. "
            f"Please use: to_decision(condition, 'MyDecision')"
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
                f"Line {node.lineno}: to_decision() requires at least 1 argument "
                f"(the boolean expression). "
                f"Please use: to_decision(condition, 'name')"
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
