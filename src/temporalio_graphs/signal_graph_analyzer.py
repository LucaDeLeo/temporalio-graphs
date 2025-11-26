"""Peer signal graph analyzer for cross-workflow signal visualization.

This module provides the PeerSignalGraphAnalyzer class which builds cross-workflow
signal graphs by recursively discovering connected workflows via external signals
and their handlers.

Starting from an entry workflow, the analyzer follows external signal calls to
find handler workflows, recursively discovering all interconnected workflows
to build a complete peer-to-peer signal graph.

Example:
    >>> from pathlib import Path
    >>> from temporalio_graphs.signal_graph_analyzer import PeerSignalGraphAnalyzer
    >>> analyzer = PeerSignalGraphAnalyzer(
    ...     search_paths=[Path("workflows/")],
    ...     max_depth=10,
    ... )
    >>> graph = analyzer.analyze(Path("order_workflow.py"))
    >>> print(list(graph.workflows.keys()))
    ['OrderWorkflow', 'ShippingWorkflow', 'NotificationWorkflow']
"""

from __future__ import annotations

import logging
from pathlib import Path

from temporalio_graphs._internal.graph_models import (
    ExternalSignalCall,
    PeerSignalGraph,
    SignalConnection,
    SignalHandler,
    WorkflowMetadata,
)
from temporalio_graphs.analyzer import WorkflowAnalyzer
from temporalio_graphs.context import GraphBuildingContext
from temporalio_graphs.exceptions import WorkflowParseError
from temporalio_graphs.resolver import SignalNameResolver

logger = logging.getLogger(__name__)


class PeerSignalGraphAnalyzer:
    """Analyzes workflows and builds cross-workflow signal graph.

    Starting from an entry workflow, discovers all connected workflows
    by following external signal --> signal handler connections. Uses
    recursive discovery with cycle detection and depth limiting.

    The analyzer uses SignalNameResolver to find workflows that handle
    each external signal, then recursively analyzes those workflows
    to discover their external signals, building a complete graph of
    all interconnected workflows.

    Attributes:
        _search_paths: List of directories to search for workflows.
        _resolver: SignalNameResolver for finding signal handlers.
        _max_depth: Maximum recursion depth for discovery.
        _context: GraphBuildingContext for configuration.
        _visited_workflows: Set of workflow names already analyzed.
        _workflows: Dictionary of discovered workflow metadata.
        _connections: List of signal connections found.
        _unresolved: List of external signals with no handler.

    Example:
        >>> analyzer = PeerSignalGraphAnalyzer(
        ...     search_paths=[Path("./workflows/")],
        ...     max_depth=10,
        ... )
        >>> graph = analyzer.analyze(Path("order_workflow.py"))
        >>> print(list(graph.workflows.keys()))
        ['OrderWorkflow', 'ShippingWorkflow', 'NotificationWorkflow']
    """

    def __init__(
        self,
        search_paths: list[Path],
        resolver: SignalNameResolver | None = None,
        max_depth: int = 10,
        context: GraphBuildingContext | None = None,
    ) -> None:
        """Initialize the peer signal graph analyzer.

        Args:
            search_paths: Directories to search for target workflows.
            resolver: Custom resolver instance. If None, creates SignalNameResolver.
            max_depth: Maximum recursion depth for discovery (default: 10).
            context: Graph building configuration (default: GraphBuildingContext()).
        """
        self._search_paths = search_paths
        self._resolver = resolver if resolver is not None else SignalNameResolver(search_paths)
        self._max_depth = max_depth
        self._context = context if context is not None else GraphBuildingContext()

        # Analysis state - reset for each analyze() call
        self._visited_workflows: set[str] = set()
        self._workflows: dict[str, WorkflowMetadata] = {}
        self._connections: list[SignalConnection] = []
        self._unresolved: list[ExternalSignalCall] = []

    def analyze(self, entry_workflow: Path) -> PeerSignalGraph:
        """Analyze entry workflow and discover all connected workflows.

        Starting from the entry workflow, recursively discovers all workflows
        connected via external signals. Builds a complete peer signal graph
        containing all workflows, their signal handlers, connections between
        workflows, and any unresolved signals.

        Args:
            entry_workflow: Path to the entry point workflow file.

        Returns:
            PeerSignalGraph containing all discovered workflows,
            their signal handlers, and connections between them.

        Raises:
            WorkflowParseError: If entry_workflow cannot be parsed.
        """
        # Reset analysis state for new analysis
        self._visited_workflows = set()
        self._workflows = {}
        self._connections = []
        self._unresolved = []

        # Build resolver index for signal handler lookup
        self._resolver.build_index()

        # Analyze entry workflow
        entry_metadata = self._analyze_workflow(entry_workflow)

        # Store entry workflow
        self._workflows[entry_metadata.workflow_class] = entry_metadata
        self._visited_workflows.add(entry_metadata.workflow_class)

        logger.debug(
            "Starting signal graph analysis from entry workflow '%s' at %s",
            entry_metadata.workflow_class,
            entry_workflow,
        )

        # Recursively discover connected workflows
        self._discover_connections(entry_metadata, depth=0)

        # Build handler index from discovered workflows
        signal_handlers = self._build_handler_index()

        logger.info(
            "Signal graph analysis complete: %d workflows, %d connections, %d unresolved",
            len(self._workflows),
            len(self._connections),
            len(self._unresolved),
        )

        return PeerSignalGraph(
            root_workflow=entry_metadata,
            workflows=self._workflows,
            signal_handlers=signal_handlers,
            connections=self._connections,
            unresolved_signals=self._unresolved,
        )

    def _discover_connections(
        self,
        metadata: WorkflowMetadata,
        depth: int,
    ) -> None:
        """Recursively discover workflows connected by signals.

        For each external signal in the workflow, resolves the target
        handler workflow(s) and recursively discovers their connections.
        Implements cycle detection via visited set and depth limiting.

        Args:
            metadata: WorkflowMetadata of current workflow to process.
            depth: Current recursion depth (0 = entry workflow).
        """
        # Check max depth limit
        if depth >= self._max_depth:
            logger.warning(
                "Max depth %d reached, stopping discovery",
                self._max_depth,
            )
            return

        # Process each external signal
        for external_signal in metadata.external_signals:
            # Resolve signal to target handlers
            targets = self._resolver.resolve(external_signal)

            # Handle unresolved signals
            if not targets:
                self._unresolved.append(external_signal)
                logger.warning(
                    "Could not resolve signal '%s' - no matching handler found",
                    external_signal.signal_name,
                )
                continue

            # Process each target handler
            for target_path, handler in targets:
                try:
                    # Analyze target workflow
                    target_metadata = self._analyze_workflow(target_path)
                except WorkflowParseError as e:
                    logger.warning(
                        "Could not analyze target workflow at %s: %s",
                        target_path,
                        e.message,
                    )
                    continue

                # Create connection (always, even for cycles)
                connection = SignalConnection(
                    sender_workflow=metadata.workflow_class,
                    receiver_workflow=target_metadata.workflow_class,
                    signal_name=external_signal.signal_name,
                    sender_line=external_signal.source_line,
                    receiver_line=handler.source_line,
                    sender_node_id=external_signal.node_id,
                    receiver_node_id=handler.node_id,
                )
                self._connections.append(connection)

                logger.debug(
                    "Resolved signal '%s': %s --> %s",
                    external_signal.signal_name,
                    metadata.workflow_class,
                    target_metadata.workflow_class,
                )

                # Check if already visited (cycle detection)
                if target_metadata.workflow_class in self._visited_workflows:
                    # Connection recorded above, but don't recurse (cycle detected)
                    logger.debug(
                        "Cycle detected: %s already visited, skipping recursion",
                        target_metadata.workflow_class,
                    )
                    continue

                # Store target workflow and mark as visited
                self._workflows[target_metadata.workflow_class] = target_metadata
                self._visited_workflows.add(target_metadata.workflow_class)

                logger.debug(
                    "Discovered workflow '%s' at %s",
                    target_metadata.workflow_class,
                    target_path,
                )

                # Recurse to discover target's connections
                self._discover_connections(target_metadata, depth + 1)

    def _analyze_workflow(self, file_path: Path) -> WorkflowMetadata:
        """Analyze single workflow file and return metadata.

        Args:
            file_path: Path to workflow file to analyze.

        Returns:
            WorkflowMetadata for the workflow.

        Raises:
            WorkflowParseError: If file cannot be parsed.
        """
        analyzer = WorkflowAnalyzer()
        metadata = analyzer.analyze(file_path, self._context)

        logger.debug(
            "Discovered workflow '%s' at %s",
            metadata.workflow_class,
            file_path,
        )

        return metadata

    def _build_handler_index(self) -> dict[str, list[SignalHandler]]:
        """Build signal handler index from discovered workflows.

        Iterates over all discovered workflows and collects their signal
        handlers into a dictionary indexed by signal name.

        Returns:
            Dictionary mapping signal names to lists of handlers.
        """
        handler_index: dict[str, list[SignalHandler]] = {}

        for workflow_metadata in self._workflows.values():
            for handler in workflow_metadata.signal_handlers:
                if handler.signal_name not in handler_index:
                    handler_index[handler.signal_name] = []
                handler_index[handler.signal_name].append(handler)

        return handler_index
