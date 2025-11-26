"""Signal name resolver for cross-workflow signal visualization.

This module provides the SignalNameResolver class which resolves external signals
to their target workflows by matching signal names to signal handlers. This enables
cross-workflow signal connections for visualization in peer-to-peer signaling scenarios.

The resolver uses static analysis via WorkflowAnalyzer to scan workflow files and
build an index of signal handlers for O(1) lookup during resolution.

Example:
    >>> from pathlib import Path
    >>> from temporalio_graphs.resolver import SignalNameResolver
    >>> from temporalio_graphs._internal.graph_models import ExternalSignalCall
    >>> resolver = SignalNameResolver([Path("workflows/")])
    >>> signal = ExternalSignalCall(
    ...     signal_name="ship_order",
    ...     target_workflow_pattern="shipping-123",
    ...     source_line=45,
    ...     node_id="ext_sig_ship_order_45",
    ...     source_workflow="OrderWorkflow"
    ... )
    >>> handlers = resolver.resolve(signal)
    >>> for path, handler in handlers:
    ...     print(f"Found handler in {path}: {handler.workflow_class}.{handler.method_name}")
"""

from __future__ import annotations

import logging
from pathlib import Path

from temporalio_graphs._internal.graph_models import (
    ExternalSignalCall,
    SignalHandler,
    WorkflowMetadata,
)
from temporalio_graphs.analyzer import WorkflowAnalyzer
from temporalio_graphs.exceptions import WorkflowParseError

logger = logging.getLogger(__name__)


class SignalNameResolver:
    """Resolves external signals to target workflows by signal name.

    Searches for workflows that have a @workflow.signal handler with a name
    matching the external signal's signal_name. The resolver builds an index
    of signal handlers from provided search paths for efficient O(1) lookup.

    The resolver supports lazy initialization - the index is built on the first
    call to resolve() if build_index() hasn't been called explicitly.

    Attributes:
        _search_paths: List of directories to search for workflow files.
        _workflow_cache: Cache of analyzed workflow metadata by file path.
        _handler_index: Index mapping signal names to (file_path, handler) tuples.
        _index_built: Flag indicating whether the index has been built.

    Example:
        >>> from pathlib import Path
        >>> resolver = SignalNameResolver([Path("workflows/")])
        >>> resolver.build_index()  # Optional: index is built lazily
        >>> signal = ExternalSignalCall(...)
        >>> handlers = resolver.resolve(signal)
        >>> for path, handler in handlers:
        ...     print(f"{handler.signal_name} handled by {handler.workflow_class}")
    """

    def __init__(self, search_paths: list[Path]) -> None:
        """Initialize resolver with search paths.

        Args:
            search_paths: List of directories to search for workflow files
                containing signal handlers. Files are searched recursively
                using **/*.py glob pattern.
        """
        self._search_paths = search_paths
        self._workflow_cache: dict[Path, WorkflowMetadata] = {}
        self._handler_index: dict[str, list[tuple[Path, SignalHandler]]] = {}
        self._index_built = False

    def build_index(self) -> None:
        """Scan search paths and index all signal handlers.

        This method scans all Python files in the search paths, analyzes them
        using WorkflowAnalyzer, and builds an index mapping signal names to
        their handlers. Files that fail to parse are skipped with a warning.

        The index can be rebuilt by calling this method again, which clears
        the existing cache and index before rebuilding.

        Raises:
            No exceptions are raised - invalid files are skipped with warning.
        """
        logger.debug(
            "Building signal handler index from %d search paths", len(self._search_paths)
        )

        # Clear existing cache and index for rebuild
        self._workflow_cache.clear()
        self._handler_index.clear()

        files_scanned = 0
        handlers_found = 0

        for search_path in self._search_paths:
            if not search_path.exists():
                logger.warning("Search path does not exist: %s", search_path)
                continue

            if not search_path.is_dir():
                logger.warning("Search path is not a directory: %s", search_path)
                continue

            # Recursively find all Python files
            for file_path in search_path.glob("**/*.py"):
                # Skip __pycache__ directories and other non-source files
                if "__pycache__" in str(file_path):
                    continue

                metadata = self._analyze_file(file_path)
                if metadata is None:
                    continue

                files_scanned += 1

                # Skip files with no signal handlers
                if not metadata.signal_handlers:
                    continue

                # Cache the metadata
                self._workflow_cache[file_path] = metadata

                # Index each signal handler
                for handler in metadata.signal_handlers:
                    signal_name = handler.signal_name
                    if signal_name not in self._handler_index:
                        self._handler_index[signal_name] = []
                    self._handler_index[signal_name].append((file_path, handler))
                    handlers_found += 1
                    logger.debug(
                        "Found @workflow.signal handler '%s' in %s",
                        signal_name,
                        file_path,
                    )

        self._index_built = True
        logger.info(
            "Signal handler index built: %d handlers from %d files",
            handlers_found,
            files_scanned,
        )

    def resolve(
        self, signal: ExternalSignalCall
    ) -> list[tuple[Path, SignalHandler]]:
        """Find workflows that handle the given signal.

        Returns all signal handlers that match the signal's signal_name.
        If the index hasn't been built yet, it is built automatically
        (lazy initialization).

        Args:
            signal: ExternalSignalCall representing the signal to resolve.
                The signal_name field is used to find matching handlers.

        Returns:
            List of (file_path, SignalHandler) tuples for all workflows
            that have a handler for the signal name. Returns empty list
            if no handler is found.

        Example:
            >>> signal = ExternalSignalCall(
            ...     signal_name="ship_order",
            ...     target_workflow_pattern="shipping-123",
            ...     source_line=45,
            ...     node_id="ext_sig_ship_order_45",
            ...     source_workflow="OrderWorkflow"
            ... )
            >>> handlers = resolver.resolve(signal)
            >>> len(handlers)
            1
            >>> path, handler = handlers[0]
            >>> handler.signal_name
            'ship_order'
        """
        # Lazy initialization: build index on first resolve call
        if not self._index_built:
            self.build_index()

        # O(1) lookup in handler index
        return self._handler_index.get(signal.signal_name, [])

    def _analyze_file(self, file_path: Path) -> WorkflowMetadata | None:
        """Analyze single file for workflow metadata.

        This helper method reads and analyzes a Python file using WorkflowAnalyzer
        to extract workflow metadata including signal handlers. Errors are handled
        gracefully - files that fail to parse are skipped with a warning.

        Args:
            file_path: Path to the Python file to analyze.

        Returns:
            WorkflowMetadata if analysis succeeded, None if file failed to parse
            or is not a valid workflow file.
        """
        try:
            analyzer = WorkflowAnalyzer()
            metadata = analyzer.analyze(file_path)
            return metadata
        except WorkflowParseError as e:
            # Expected for non-workflow Python files (no @workflow.defn)
            logger.debug("Skipping file %s: %s", file_path, e.message)
            return None
        except SyntaxError as e:
            logger.warning("Skipping file %s: syntax error at line %s", file_path, e.lineno)
            return None
        except FileNotFoundError:
            logger.warning("Skipping file %s: file not found", file_path)
            return None
        except PermissionError:
            logger.warning("Skipping file %s: permission denied", file_path)
            return None
        except Exception as e:
            # Catch any unexpected errors to ensure one bad file doesn't break entire scan
            logger.warning("Skipping file %s: unexpected error: %s", file_path, e)
            return None
