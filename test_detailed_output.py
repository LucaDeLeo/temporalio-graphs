#!/usr/bin/env python3
"""
Detailed output test for temporalio-graphs on real workflows
Shows full Mermaid diagrams to understand what's being captured
"""
from pathlib import Path
from temporalio_graphs import analyze_workflow, GraphBuildingContext

# Test workflows
WORKFLOWS = [
    ("Hello Activity", "/Users/luca/dev/bounty/repo-examples/samples-python/hello/hello_activity.py"),
    ("Polling Periodic", "/Users/luca/dev/bounty/repo-examples/samples-python/polling/periodic_sequence/workflows.py"),
    ("AI Agent", "/Users/luca/dev/bounty/repo-examples/temporal-ai-agent/workflows/agent_goal_workflow.py"),
]

def print_sep(char="=", length=80):
    print(char * length)

for name, path in WORKFLOWS:
    print_sep()
    print(f"{name}: {path}")
    print_sep("-")

    result = analyze_workflow(Path(path))
    print(result)
    print()
