"""Workflow class with no methods at all."""

from temporalio import workflow


@workflow.defn
class EmptyWorkflow:
    """Empty workflow with no methods."""

    pass
