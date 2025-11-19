"""MoneyTransfer workflow analysis example runner.

This script demonstrates how to use the temporalio-graphs library to analyze
a Temporal workflow with decision points and generate a visualization diagram.

The MoneyTransfer workflow models an international money transfer with 2 decision
points, creating 4 possible execution paths. This example shows how the library
generates a complete Mermaid flowchart showing all possible paths.

Usage:
    python examples/money_transfer/run.py

Output:
    Prints a Mermaid flowchart diagram representing the MoneyTransfer workflow
    with 2 decision diamonds and all 4 execution paths.

This example validates that:
1. The MoneyTransfer workflow file can be analyzed
2. Both decision points are detected (NeedToConvert, IsTFN_Known)
3. All 5 activities are detected (Withdraw, CurrencyConvert, NotifyAto, TakeNonResidentTax, Deposit)
4. Exactly 4 paths are generated (2^2 combinations)
5. The correct Mermaid diagram with decision nodes is produced
"""

from pathlib import Path

from temporalio_graphs import analyze_workflow


def main() -> None:
    """Analyze the MoneyTransfer workflow and print the diagram.

    This function demonstrates the usage of the analyze_workflow API:
    - Import the function from temporalio_graphs
    - Resolve the path to the workflow file
    - Call analyze_workflow with the file path
    - Print the resulting Mermaid diagram
    """
    # Path to the MoneyTransfer workflow
    workflow_file = Path(__file__).parent / "workflow.py"

    # Analyze the workflow using the public API
    # Returns a Mermaid diagram as a string
    diagram = analyze_workflow(workflow_file)

    # Print the diagram
    print(diagram)


if __name__ == "__main__":
    main()
