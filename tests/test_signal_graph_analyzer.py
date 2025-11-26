"""Unit tests for PeerSignalGraphAnalyzer.

This test module verifies that PeerSignalGraphAnalyzer correctly builds
cross-workflow signal graphs by recursively discovering connected workflows
via external signals and their handlers.

Test coverage includes:
- Single workflow analysis (no external signals)
- Two connected workflows (A -> B)
- Three workflow chain (A -> B -> C) - AC14 recursive discovery
- Cycle detection (A -> B -> A) - AC15
- Max depth limiting - AC16
- Unresolved signal handling
- Multiple handlers for same signal
"""

import logging
from pathlib import Path

import pytest

from temporalio_graphs._internal.graph_models import (
    ExternalSignalCall,
    PeerSignalGraph,
    SignalConnection,
)
from temporalio_graphs.context import GraphBuildingContext
from temporalio_graphs.signal_graph_analyzer import PeerSignalGraphAnalyzer


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def workflow_standalone(tmp_path: Path) -> Path:
    """Create a standalone workflow with no external signals."""
    code = '''
from temporalio import workflow

@workflow.defn
class StandaloneWorkflow:
    @workflow.signal
    async def some_signal(self, data: str) -> None:
        self.data = data

    @workflow.run
    async def run(self) -> None:
        pass
'''
    path = tmp_path / "standalone_workflow.py"
    path.write_text(code)
    return path


@pytest.fixture
def workflow_a(tmp_path: Path) -> Path:
    """Create workflow A that sends signal_b to workflow B."""
    code = '''
from temporalio import workflow

@workflow.defn
class WorkflowA:
    @workflow.run
    async def run(self) -> None:
        handle = workflow.get_external_workflow_handle("WorkflowB", "wf-b-123")
        await handle.signal("signal_b", "data")
'''
    path = tmp_path / "workflow_a.py"
    path.write_text(code)
    return path


@pytest.fixture
def workflow_b(tmp_path: Path) -> Path:
    """Create workflow B that handles signal_b and sends signal_c."""
    code = '''
from temporalio import workflow

@workflow.defn
class WorkflowB:
    @workflow.signal
    async def signal_b(self, data: str) -> None:
        self.data = data

    @workflow.run
    async def run(self) -> None:
        handle = workflow.get_external_workflow_handle("WorkflowC", "wf-c-123")
        await handle.signal("signal_c", "forwarded")
'''
    path = tmp_path / "workflow_b.py"
    path.write_text(code)
    return path


@pytest.fixture
def workflow_c(tmp_path: Path) -> Path:
    """Create workflow C that handles signal_c (end of chain)."""
    code = '''
from temporalio import workflow

@workflow.defn
class WorkflowC:
    @workflow.signal
    async def signal_c(self, data: str) -> None:
        self.data = data

    @workflow.run
    async def run(self) -> None:
        pass
'''
    path = tmp_path / "workflow_c.py"
    path.write_text(code)
    return path


@pytest.fixture
def workflow_cycle_a(tmp_path: Path) -> Path:
    """Create workflow A for cycle detection (sends to B)."""
    code = '''
from temporalio import workflow

@workflow.defn
class WorkflowCycleA:
    @workflow.signal
    async def signal_from_b(self, data: str) -> None:
        pass

    @workflow.run
    async def run(self) -> None:
        handle = workflow.get_external_workflow_handle("WorkflowCycleB", "wf-cycle-b")
        await handle.signal("signal_to_b", "data")
'''
    path = tmp_path / "workflow_cycle_a.py"
    path.write_text(code)
    return path


@pytest.fixture
def workflow_cycle_b(tmp_path: Path) -> Path:
    """Create workflow B that signals back to A (creates cycle)."""
    code = '''
from temporalio import workflow

@workflow.defn
class WorkflowCycleB:
    @workflow.signal
    async def signal_to_b(self, data: str) -> None:
        pass

    @workflow.run
    async def run(self) -> None:
        handle = workflow.get_external_workflow_handle("WorkflowCycleA", "wf-cycle-a")
        await handle.signal("signal_from_b", "response")
'''
    path = tmp_path / "workflow_cycle_b.py"
    path.write_text(code)
    return path


@pytest.fixture
def workflow_d(tmp_path: Path) -> Path:
    """Create workflow D that handles signal_d (for depth testing)."""
    code = '''
from temporalio import workflow

@workflow.defn
class WorkflowD:
    @workflow.signal
    async def signal_d(self, data: str) -> None:
        self.data = data

    @workflow.run
    async def run(self) -> None:
        pass
'''
    path = tmp_path / "workflow_d.py"
    path.write_text(code)
    return path


@pytest.fixture
def workflow_c_sends_d(tmp_path: Path) -> Path:
    """Create workflow C that handles signal_c and sends signal_d (for depth testing)."""
    code = '''
from temporalio import workflow

@workflow.defn
class WorkflowC:
    @workflow.signal
    async def signal_c(self, data: str) -> None:
        self.data = data

    @workflow.run
    async def run(self) -> None:
        handle = workflow.get_external_workflow_handle("WorkflowD", "wf-d-123")
        await handle.signal("signal_d", "deep")
'''
    path = tmp_path / "workflow_c.py"
    path.write_text(code)
    return path


@pytest.fixture
def workflow_with_unresolved(tmp_path: Path) -> Path:
    """Create workflow that sends a signal with no handler."""
    code = '''
from temporalio import workflow

@workflow.defn
class WorkflowWithUnresolved:
    @workflow.run
    async def run(self) -> None:
        handle = workflow.get_external_workflow_handle("Unknown", "unknown-123")
        await handle.signal("nonexistent_signal", "data")
'''
    path = tmp_path / "workflow_unresolved.py"
    path.write_text(code)
    return path


@pytest.fixture
def workflow_multi_handler_1(tmp_path: Path) -> Path:
    """Create first workflow that handles shared_signal."""
    code = '''
from temporalio import workflow

@workflow.defn
class MultiHandler1:
    @workflow.signal
    async def shared_signal(self, data: str) -> None:
        self.data = data

    @workflow.run
    async def run(self) -> None:
        pass
'''
    path = tmp_path / "multi_handler_1.py"
    path.write_text(code)
    return path


@pytest.fixture
def workflow_multi_handler_2(tmp_path: Path) -> Path:
    """Create second workflow that handles shared_signal."""
    code = '''
from temporalio import workflow

@workflow.defn
class MultiHandler2:
    @workflow.signal
    async def shared_signal(self, data: str) -> None:
        self.data = data

    @workflow.run
    async def run(self) -> None:
        pass
'''
    path = tmp_path / "multi_handler_2.py"
    path.write_text(code)
    return path


@pytest.fixture
def workflow_sends_shared(tmp_path: Path) -> Path:
    """Create workflow that sends shared_signal (has multiple handlers)."""
    code = '''
from temporalio import workflow

@workflow.defn
class WorkflowSendsShared:
    @workflow.run
    async def run(self) -> None:
        handle = workflow.get_external_workflow_handle("SomeWorkflow", "some-123")
        await handle.signal("shared_signal", "data")
'''
    path = tmp_path / "workflow_sends_shared.py"
    path.write_text(code)
    return path


# ============================================================================
# Test Classes
# ============================================================================


class TestPeerSignalGraphAnalyzerInit:
    """Tests for PeerSignalGraphAnalyzer constructor."""

    def test_init_with_defaults(self, tmp_path: Path) -> None:
        """Test constructor with minimal parameters."""
        analyzer = PeerSignalGraphAnalyzer(search_paths=[tmp_path])

        assert analyzer._search_paths == [tmp_path]
        assert analyzer._max_depth == 10
        assert analyzer._context is not None
        assert analyzer._resolver is not None

    def test_init_with_custom_max_depth(self, tmp_path: Path) -> None:
        """Test constructor with custom max_depth."""
        analyzer = PeerSignalGraphAnalyzer(
            search_paths=[tmp_path],
            max_depth=5,
        )

        assert analyzer._max_depth == 5

    def test_init_with_custom_context(self, tmp_path: Path) -> None:
        """Test constructor with custom GraphBuildingContext."""
        context = GraphBuildingContext(start_node_label="BEGIN")
        analyzer = PeerSignalGraphAnalyzer(
            search_paths=[tmp_path],
            context=context,
        )

        assert analyzer._context == context

    def test_init_with_custom_resolver(self, tmp_path: Path) -> None:
        """Test constructor with custom resolver."""
        from temporalio_graphs.resolver import SignalNameResolver

        resolver = SignalNameResolver([tmp_path])
        analyzer = PeerSignalGraphAnalyzer(
            search_paths=[tmp_path],
            resolver=resolver,
        )

        assert analyzer._resolver is resolver


class TestAnalyzeSingleWorkflow:
    """Tests for analyzing single workflow with no external signals."""

    def test_analyze_single_workflow_no_signals(
        self, workflow_standalone: Path, tmp_path: Path
    ) -> None:
        """Test analyzing workflow with no external signals."""
        analyzer = PeerSignalGraphAnalyzer(
            search_paths=[tmp_path],
            max_depth=10,
        )

        graph = analyzer.analyze(workflow_standalone)

        # Should only have the root workflow
        assert len(graph.workflows) == 1
        assert "StandaloneWorkflow" in graph.workflows

        # No connections or unresolved signals
        assert len(graph.connections) == 0
        assert len(graph.unresolved_signals) == 0

        # Root workflow should be set
        assert graph.root_workflow.workflow_class == "StandaloneWorkflow"

        # Signal handlers should be populated
        assert "some_signal" in graph.signal_handlers
        assert len(graph.signal_handlers["some_signal"]) == 1


class TestAnalyzeTwoConnectedWorkflows:
    """Tests for analyzing two connected workflows (A -> B)."""

    def test_analyze_two_connected_workflows(
        self, workflow_a: Path, workflow_b: Path, tmp_path: Path
    ) -> None:
        """Test analyzer discovers connected workflows."""
        # Need to create workflow_b fixture first to have it in search path
        analyzer = PeerSignalGraphAnalyzer(
            search_paths=[tmp_path],
            max_depth=10,
        )

        graph = analyzer.analyze(workflow_a)

        # Should have both workflows
        assert len(graph.workflows) == 2
        assert "WorkflowA" in graph.workflows
        assert "WorkflowB" in graph.workflows

        # Should have one connection
        assert len(graph.connections) == 1
        conn = graph.connections[0]
        assert conn.sender_workflow == "WorkflowA"
        assert conn.receiver_workflow == "WorkflowB"
        assert conn.signal_name == "signal_b"

        # Root workflow should be WorkflowA
        assert graph.root_workflow.workflow_class == "WorkflowA"


class TestAnalyzeThreeWorkflowChain:
    """Tests for analyzing three workflow chain (A -> B -> C) - AC14."""

    def test_analyze_three_workflow_chain(
        self, workflow_a: Path, workflow_b: Path, workflow_c: Path, tmp_path: Path
    ) -> None:
        """Test AC14: Recursive discovery of three connected workflows."""
        analyzer = PeerSignalGraphAnalyzer(
            search_paths=[tmp_path],
            max_depth=10,
        )

        graph = analyzer.analyze(workflow_a)

        # Should have all three workflows
        assert len(graph.workflows) == 3
        assert "WorkflowA" in graph.workflows
        assert "WorkflowB" in graph.workflows
        assert "WorkflowC" in graph.workflows

        # Should have two connections
        assert len(graph.connections) == 2

        # Find connections by signal name
        conn_b = next(c for c in graph.connections if c.signal_name == "signal_b")
        conn_c = next(c for c in graph.connections if c.signal_name == "signal_c")

        assert conn_b.sender_workflow == "WorkflowA"
        assert conn_b.receiver_workflow == "WorkflowB"

        assert conn_c.sender_workflow == "WorkflowB"
        assert conn_c.receiver_workflow == "WorkflowC"


class TestCycleDetection:
    """Tests for cycle detection (A -> B -> A) - AC15."""

    def test_cycle_detection_no_infinite_loop(
        self, workflow_cycle_a: Path, workflow_cycle_b: Path, tmp_path: Path
    ) -> None:
        """Test AC15: Cycle A -> B -> A detected without infinite loop."""
        analyzer = PeerSignalGraphAnalyzer(
            search_paths=[tmp_path],
            max_depth=10,
        )

        # Should complete without infinite loop
        graph = analyzer.analyze(workflow_cycle_a)

        # Both workflows should be discovered
        assert len(graph.workflows) == 2
        assert "WorkflowCycleA" in graph.workflows
        assert "WorkflowCycleB" in graph.workflows

        # Both connections should be recorded (A->B and B->A)
        assert len(graph.connections) == 2

        # Verify both connections exist
        senders = {c.sender_workflow for c in graph.connections}
        receivers = {c.receiver_workflow for c in graph.connections}
        assert "WorkflowCycleA" in senders
        assert "WorkflowCycleB" in senders
        assert "WorkflowCycleA" in receivers
        assert "WorkflowCycleB" in receivers


class TestMaxDepthLimit:
    """Tests for max depth limiting - AC16."""

    def test_max_depth_limit_stops_discovery(
        self,
        workflow_a: Path,
        workflow_b: Path,
        workflow_c_sends_d: Path,
        workflow_d: Path,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test AC16: Max depth limits discovery with warning."""
        # Rename workflow_c_sends_d to workflow_c.py (fixture already creates it correctly)
        # Setup: A -> B -> C -> D, with max_depth=2

        analyzer = PeerSignalGraphAnalyzer(
            search_paths=[tmp_path],
            max_depth=2,
        )

        with caplog.at_level(logging.WARNING):
            graph = analyzer.analyze(workflow_a)

        # At depth 0 (entry): WorkflowA analyzed
        # At depth 1: WorkflowB discovered
        # At depth 2: Max depth reached, warning logged
        # WorkflowC may be analyzed but D should not be discovered

        # Verify warning was logged
        assert any("Max depth 2 reached" in record.message for record in caplog.records)

    def test_max_depth_1_discovers_only_immediate(
        self, workflow_a: Path, workflow_b: Path, workflow_c: Path, tmp_path: Path
    ) -> None:
        """Test max_depth=1 only discovers immediate connections."""
        analyzer = PeerSignalGraphAnalyzer(
            search_paths=[tmp_path],
            max_depth=1,
        )

        graph = analyzer.analyze(workflow_a)

        # Should discover A and B, but not C
        # depth 0: process A's signals
        # depth 1: max reached, don't process B's signals
        assert "WorkflowA" in graph.workflows
        assert "WorkflowB" in graph.workflows
        # C should not be discovered since we stop at depth 1
        assert "WorkflowC" not in graph.workflows


class TestUnresolvedSignals:
    """Tests for unresolved signal handling."""

    def test_unresolved_signal_tracked(
        self, workflow_with_unresolved: Path, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that unresolved signals are tracked in graph."""
        analyzer = PeerSignalGraphAnalyzer(
            search_paths=[tmp_path],
            max_depth=10,
        )

        with caplog.at_level(logging.WARNING):
            graph = analyzer.analyze(workflow_with_unresolved)

        # Should have only root workflow
        assert len(graph.workflows) == 1
        assert "WorkflowWithUnresolved" in graph.workflows

        # Should have unresolved signal
        assert len(graph.unresolved_signals) == 1
        assert graph.unresolved_signals[0].signal_name == "nonexistent_signal"

        # Warning should be logged
        assert any(
            "Could not resolve signal 'nonexistent_signal'" in record.message
            for record in caplog.records
        )


class TestMultipleHandlersSameSignal:
    """Tests for signals with multiple handlers."""

    def test_multiple_handlers_same_signal(
        self,
        workflow_sends_shared: Path,
        workflow_multi_handler_1: Path,
        workflow_multi_handler_2: Path,
        tmp_path: Path,
    ) -> None:
        """Test that multiple handlers for same signal create multiple connections."""
        analyzer = PeerSignalGraphAnalyzer(
            search_paths=[tmp_path],
            max_depth=10,
        )

        graph = analyzer.analyze(workflow_sends_shared)

        # Should have 3 workflows (sender + both handlers)
        assert len(graph.workflows) == 3
        assert "WorkflowSendsShared" in graph.workflows
        assert "MultiHandler1" in graph.workflows
        assert "MultiHandler2" in graph.workflows

        # Should have 2 connections (one to each handler)
        assert len(graph.connections) == 2

        # Both connections should have same signal name but different receivers
        receiver_workflows = {c.receiver_workflow for c in graph.connections}
        assert "MultiHandler1" in receiver_workflows
        assert "MultiHandler2" in receiver_workflows

        # Both connections should be from the sender
        for conn in graph.connections:
            assert conn.sender_workflow == "WorkflowSendsShared"
            assert conn.signal_name == "shared_signal"


class TestBuildHandlerIndex:
    """Tests for _build_handler_index method."""

    def test_build_handler_index(
        self, workflow_a: Path, workflow_b: Path, workflow_c: Path, tmp_path: Path
    ) -> None:
        """Test that signal handler index is built from discovered workflows."""
        analyzer = PeerSignalGraphAnalyzer(
            search_paths=[tmp_path],
            max_depth=10,
        )

        graph = analyzer.analyze(workflow_a)

        # Should have handlers for signal_b and signal_c
        assert "signal_b" in graph.signal_handlers
        assert "signal_c" in graph.signal_handlers

        # Each should have one handler
        assert len(graph.signal_handlers["signal_b"]) == 1
        assert len(graph.signal_handlers["signal_c"]) == 1

        # Verify handler metadata
        handler_b = graph.signal_handlers["signal_b"][0]
        assert handler_b.workflow_class == "WorkflowB"
        assert handler_b.signal_name == "signal_b"

        handler_c = graph.signal_handlers["signal_c"][0]
        assert handler_c.workflow_class == "WorkflowC"
        assert handler_c.signal_name == "signal_c"


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_search_paths(self, workflow_a: Path, tmp_path: Path) -> None:
        """Test with empty search paths - all signals unresolved."""
        # Create analyzer with empty search path (no handlers can be found)
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        analyzer = PeerSignalGraphAnalyzer(
            search_paths=[empty_dir],
            max_depth=10,
        )

        graph = analyzer.analyze(workflow_a)

        # Only root workflow
        assert len(graph.workflows) == 1

        # signal_b should be unresolved
        assert len(graph.unresolved_signals) == 1
        assert graph.unresolved_signals[0].signal_name == "signal_b"

    def test_graph_is_frozen_dataclass(
        self, workflow_a: Path, workflow_b: Path, tmp_path: Path
    ) -> None:
        """Test that PeerSignalGraph is a frozen dataclass."""
        analyzer = PeerSignalGraphAnalyzer(
            search_paths=[tmp_path],
            max_depth=10,
        )

        graph = analyzer.analyze(workflow_a)

        # Verify graph is PeerSignalGraph instance
        assert isinstance(graph, PeerSignalGraph)

        # Verify it's frozen (immutable) - should raise FrozenInstanceError
        with pytest.raises(Exception):  # FrozenInstanceError
            graph.root_workflow = None  # type: ignore[misc]

    def test_analyze_resets_state(
        self, workflow_a: Path, workflow_b: Path, tmp_path: Path
    ) -> None:
        """Test that analyze() resets internal state between calls."""
        analyzer = PeerSignalGraphAnalyzer(
            search_paths=[tmp_path],
            max_depth=10,
        )

        # First analysis
        graph1 = analyzer.analyze(workflow_a)
        assert len(graph1.workflows) == 2

        # Second analysis with same entry should work identically
        graph2 = analyzer.analyze(workflow_a)
        assert len(graph2.workflows) == 2
        assert "WorkflowA" in graph2.workflows
        assert "WorkflowB" in graph2.workflows


class TestSignalConnectionMetadata:
    """Tests for SignalConnection metadata correctness."""

    def test_signal_connection_has_correct_metadata(
        self, workflow_a: Path, workflow_b: Path, tmp_path: Path
    ) -> None:
        """Test that SignalConnection has all required metadata."""
        analyzer = PeerSignalGraphAnalyzer(
            search_paths=[tmp_path],
            max_depth=10,
        )

        graph = analyzer.analyze(workflow_a)

        assert len(graph.connections) == 1
        conn = graph.connections[0]

        # Verify all fields are populated
        assert conn.sender_workflow == "WorkflowA"
        assert conn.receiver_workflow == "WorkflowB"
        assert conn.signal_name == "signal_b"
        assert conn.sender_line > 0
        assert conn.receiver_line > 0
        assert conn.sender_node_id.startswith("ext_sig_")
        assert conn.receiver_node_id.startswith("sig_handler_")

    def test_connection_recorded_even_for_cycle(
        self, workflow_cycle_a: Path, workflow_cycle_b: Path, tmp_path: Path
    ) -> None:
        """Test that connections are recorded even when cycle is detected."""
        analyzer = PeerSignalGraphAnalyzer(
            search_paths=[tmp_path],
            max_depth=10,
        )

        graph = analyzer.analyze(workflow_cycle_a)

        # Both connections should be recorded
        assert len(graph.connections) == 2

        # Find the cycle-back connection (B -> A)
        cycle_back = next(
            (c for c in graph.connections if c.sender_workflow == "WorkflowCycleB"),
            None,
        )
        assert cycle_back is not None
        assert cycle_back.receiver_workflow == "WorkflowCycleA"
        assert cycle_back.signal_name == "signal_from_b"
