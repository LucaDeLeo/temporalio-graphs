"""Pytest configuration and shared fixtures."""

import pytest


@pytest.fixture
def sample_workflow_code():
    """Sample workflow code for testing."""
    return '''
@workflow.defn
class SimpleWorkflow:
    @workflow.run
    async def run(self, amount: int) -> str:
        await workflow.execute_activity(
            withdraw,
            args=[amount],
            start_to_close_timeout=timedelta(seconds=10)
        )
        return "complete"
'''
