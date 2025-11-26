"""Unit tests for SignalNameResolver.

This test module verifies that SignalNameResolver correctly resolves external
signals to their target workflows by matching signal names to signal handlers.

Test coverage includes:
- Constructor initialization with search paths
- build_index() method for scanning search paths and building handler index
- resolve() method for single, multiple, and no handler resolution
- Lazy initialization (auto-build on first resolve)
- Workflow metadata caching for performance
- Error handling for invalid files (syntax errors, non-workflow files)
- Edge cases: nested directories, multiple search paths, rebuild index
"""

from pathlib import Path

import pytest

from temporalio_graphs._internal.graph_models import (
    ExternalSignalCall,
    SignalHandler,
)
from temporalio_graphs.resolver import SignalNameResolver


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def resolver_test_dir(tmp_path: Path) -> Path:
    """Create temp directory with sample workflow files containing signal handlers."""
    # Create shipping_workflow.py with @workflow.signal ship_order
    shipping = tmp_path / "shipping_workflow.py"
    shipping.write_text('''
from temporalio import workflow

@workflow.defn
class ShippingWorkflow:
    @workflow.signal
    async def ship_order(self, order_id: str) -> None:
        self.order_id = order_id

    @workflow.run
    async def run(self) -> None:
        pass
''')

    # Create notification_workflow.py with @workflow.signal notify_shipped
    notification = tmp_path / "notification_workflow.py"
    notification.write_text('''
from temporalio import workflow

@workflow.defn
class NotificationWorkflow:
    @workflow.signal
    async def notify_shipped(self, tracking_number: str) -> None:
        self.tracking_number = tracking_number

    @workflow.run
    async def run(self) -> None:
        pass
''')

    return tmp_path


@pytest.fixture
def resolver(resolver_test_dir: Path) -> SignalNameResolver:
    """Create resolver with test directory as search path."""
    return SignalNameResolver([resolver_test_dir])


@pytest.fixture
def multiple_handlers_dir(tmp_path: Path) -> Path:
    """Create temp directory with multiple workflows handling same signal."""
    # Create payment_v1.py with @workflow.signal process_payment
    payment_v1 = tmp_path / "payment_v1.py"
    payment_v1.write_text('''
from temporalio import workflow

@workflow.defn
class PaymentWorkflowV1:
    @workflow.signal
    async def process_payment(self, amount: float) -> None:
        self.amount = amount

    @workflow.run
    async def run(self) -> None:
        pass
''')

    # Create payment_v2.py with @workflow.signal process_payment (same signal name)
    payment_v2 = tmp_path / "payment_v2.py"
    payment_v2.write_text('''
from temporalio import workflow

@workflow.defn
class PaymentWorkflowV2:
    @workflow.signal
    async def process_payment(self, amount: float) -> None:
        self.amount = amount

    @workflow.run
    async def run(self) -> None:
        pass
''')

    return tmp_path


@pytest.fixture
def invalid_files_dir(tmp_path: Path) -> Path:
    """Create temp directory with invalid Python files."""
    # Create valid workflow first
    valid = tmp_path / "valid_workflow.py"
    valid.write_text('''
from temporalio import workflow

@workflow.defn
class ValidWorkflow:
    @workflow.signal
    async def valid_signal(self) -> None:
        pass

    @workflow.run
    async def run(self) -> None:
        pass
''')

    # Create file with syntax error
    syntax_error = tmp_path / "syntax_error.py"
    syntax_error.write_text('''
def broken():
    if True
        pass  # Missing colon after if
''')

    # Create valid Python but not a workflow (no @workflow.defn)
    not_workflow = tmp_path / "not_workflow.py"
    not_workflow.write_text('''
def regular_function():
    return 42
''')

    return tmp_path


@pytest.fixture
def nested_dirs(tmp_path: Path) -> Path:
    """Create temp directory with nested subdirectories containing workflows."""
    # Create nested directory structure
    subdir1 = tmp_path / "subdir1"
    subdir1.mkdir()

    subdir2 = tmp_path / "subdir2" / "deep"
    subdir2.mkdir(parents=True)

    # Create workflow in root
    root_workflow = tmp_path / "root_workflow.py"
    root_workflow.write_text('''
from temporalio import workflow

@workflow.defn
class RootWorkflow:
    @workflow.signal
    async def root_signal(self) -> None:
        pass

    @workflow.run
    async def run(self) -> None:
        pass
''')

    # Create workflow in subdir1
    sub1_workflow = subdir1 / "sub1_workflow.py"
    sub1_workflow.write_text('''
from temporalio import workflow

@workflow.defn
class Sub1Workflow:
    @workflow.signal
    async def sub1_signal(self) -> None:
        pass

    @workflow.run
    async def run(self) -> None:
        pass
''')

    # Create workflow in subdir2/deep
    deep_workflow = subdir2 / "deep_workflow.py"
    deep_workflow.write_text('''
from temporalio import workflow

@workflow.defn
class DeepWorkflow:
    @workflow.signal
    async def deep_signal(self) -> None:
        pass

    @workflow.run
    async def run(self) -> None:
        pass
''')

    return tmp_path


# ============================================================================
# Test Classes
# ============================================================================


class TestSignalNameResolverInit:
    """Tests for SignalNameResolver constructor."""

    def test_init_with_single_path(self, resolver_test_dir: Path) -> None:
        """Test constructor with single search path."""
        resolver = SignalNameResolver([resolver_test_dir])

        assert resolver._search_paths == [resolver_test_dir]
        assert resolver._workflow_cache == {}
        assert resolver._handler_index == {}
        assert resolver._index_built is False

    def test_init_with_multiple_paths(self, tmp_path: Path) -> None:
        """Test constructor with multiple search paths."""
        path1 = tmp_path / "path1"
        path2 = tmp_path / "path2"
        path1.mkdir()
        path2.mkdir()

        resolver = SignalNameResolver([path1, path2])

        assert resolver._search_paths == [path1, path2]
        assert resolver._index_built is False

    def test_init_with_empty_paths(self) -> None:
        """Test constructor with empty search paths list."""
        resolver = SignalNameResolver([])

        assert resolver._search_paths == []
        assert resolver._index_built is False


class TestBuildIndex:
    """Tests for build_index() method."""

    def test_build_index_scans_search_paths(self, resolver: SignalNameResolver) -> None:
        """Test that build_index scans all files in search paths."""
        resolver.build_index()

        assert resolver._index_built is True
        # Should have found handlers in our test workflows
        assert len(resolver._handler_index) >= 2  # ship_order, notify_shipped

    def test_build_index_finds_signal_handlers(
        self, resolver: SignalNameResolver, resolver_test_dir: Path
    ) -> None:
        """Test that build_index correctly indexes signal handlers."""
        resolver.build_index()

        # Check ship_order handler was indexed
        assert "ship_order" in resolver._handler_index
        handlers = resolver._handler_index["ship_order"]
        assert len(handlers) == 1
        path, handler = handlers[0]
        assert handler.signal_name == "ship_order"
        assert handler.workflow_class == "ShippingWorkflow"
        assert path == resolver_test_dir / "shipping_workflow.py"

        # Check notify_shipped handler was indexed
        assert "notify_shipped" in resolver._handler_index
        handlers = resolver._handler_index["notify_shipped"]
        assert len(handlers) == 1
        _, handler = handlers[0]
        assert handler.signal_name == "notify_shipped"
        assert handler.workflow_class == "NotificationWorkflow"

    def test_build_index_skips_invalid_files(
        self, invalid_files_dir: Path
    ) -> None:
        """Test that build_index gracefully skips files that fail to parse."""
        resolver = SignalNameResolver([invalid_files_dir])
        resolver.build_index()

        assert resolver._index_built is True
        # Should have found the valid workflow's handler
        assert "valid_signal" in resolver._handler_index
        # Syntax error and non-workflow files should be skipped without error

    def test_build_index_empty_search_paths(self) -> None:
        """Test build_index with no search paths."""
        resolver = SignalNameResolver([])
        resolver.build_index()

        assert resolver._index_built is True
        assert resolver._handler_index == {}

    def test_build_index_caches_metadata(
        self, resolver: SignalNameResolver, resolver_test_dir: Path
    ) -> None:
        """Test that build_index populates workflow cache."""
        resolver.build_index()

        # Should have cached metadata for workflows with signal handlers
        assert len(resolver._workflow_cache) >= 2
        # Check that cached metadata contains the expected workflows
        cached_paths = list(resolver._workflow_cache.keys())
        assert any("shipping_workflow.py" in str(p) for p in cached_paths)
        assert any("notification_workflow.py" in str(p) for p in cached_paths)

    def test_build_index_nonexistent_path(self, tmp_path: Path) -> None:
        """Test build_index with nonexistent search path."""
        nonexistent = tmp_path / "does_not_exist"
        resolver = SignalNameResolver([nonexistent])

        # Should not raise - logs warning and continues
        resolver.build_index()

        assert resolver._index_built is True
        assert resolver._handler_index == {}

    def test_build_index_file_instead_of_directory(self, tmp_path: Path) -> None:
        """Test build_index when search path is a file not a directory."""
        file_path = tmp_path / "not_a_dir.py"
        file_path.write_text("# Just a file")

        resolver = SignalNameResolver([file_path])
        resolver.build_index()

        assert resolver._index_built is True
        assert resolver._handler_index == {}


class TestResolve:
    """Tests for resolve() method."""

    def test_resolve_single_handler(
        self, resolver: SignalNameResolver, resolver_test_dir: Path
    ) -> None:
        """Test resolving signal with one matching handler."""
        signal = ExternalSignalCall(
            signal_name="ship_order",
            target_workflow_pattern="shipping-123",
            source_line=10,
            node_id="ext_sig_ship_order_10",
            source_workflow="OrderWorkflow",
        )

        handlers = resolver.resolve(signal)

        assert len(handlers) == 1
        path, handler = handlers[0]
        assert handler.signal_name == "ship_order"
        assert handler.workflow_class == "ShippingWorkflow"
        assert path == resolver_test_dir / "shipping_workflow.py"

    def test_resolve_multiple_handlers(
        self, multiple_handlers_dir: Path
    ) -> None:
        """Test resolving signal with multiple handlers (same signal name)."""
        resolver = SignalNameResolver([multiple_handlers_dir])

        signal = ExternalSignalCall(
            signal_name="process_payment",
            target_workflow_pattern="payment-*",
            source_line=25,
            node_id="ext_sig_process_payment_25",
            source_workflow="CheckoutWorkflow",
        )

        handlers = resolver.resolve(signal)

        assert len(handlers) == 2
        workflow_classes = {h.workflow_class for _, h in handlers}
        assert "PaymentWorkflowV1" in workflow_classes
        assert "PaymentWorkflowV2" in workflow_classes

    def test_resolve_no_handler(self, resolver: SignalNameResolver) -> None:
        """Test resolving signal with no matching handler."""
        signal = ExternalSignalCall(
            signal_name="nonexistent_signal",
            target_workflow_pattern="some-workflow",
            source_line=5,
            node_id="ext_sig_nonexistent_signal_5",
            source_workflow="SomeWorkflow",
        )

        handlers = resolver.resolve(signal)

        assert handlers == []

    def test_resolve_auto_builds_index(
        self, resolver: SignalNameResolver
    ) -> None:
        """Test that resolve() automatically builds index if not built."""
        # Verify index not built yet
        assert resolver._index_built is False

        signal = ExternalSignalCall(
            signal_name="ship_order",
            target_workflow_pattern="shipping-123",
            source_line=10,
            node_id="ext_sig_ship_order_10",
            source_workflow="OrderWorkflow",
        )

        handlers = resolver.resolve(signal)

        # Index should now be built
        assert resolver._index_built is True
        assert len(handlers) == 1

    def test_resolve_returns_file_path_and_handler(
        self, resolver: SignalNameResolver, resolver_test_dir: Path
    ) -> None:
        """Test that resolve returns tuple of (Path, SignalHandler)."""
        signal = ExternalSignalCall(
            signal_name="ship_order",
            target_workflow_pattern="shipping-123",
            source_line=10,
            node_id="ext_sig_ship_order_10",
            source_workflow="OrderWorkflow",
        )

        handlers = resolver.resolve(signal)

        assert len(handlers) == 1
        path, handler = handlers[0]

        # Verify path is a Path object
        assert isinstance(path, Path)
        assert path.exists()
        assert path.name == "shipping_workflow.py"

        # Verify handler is a SignalHandler
        assert isinstance(handler, SignalHandler)
        assert handler.signal_name == "ship_order"
        assert handler.method_name == "ship_order"
        assert handler.workflow_class == "ShippingWorkflow"


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_resolve_after_rebuild_index(
        self, resolver_test_dir: Path
    ) -> None:
        """Test that index can be rebuilt and resolve works after rebuild."""
        resolver = SignalNameResolver([resolver_test_dir])

        # Build index first time
        resolver.build_index()
        assert resolver._index_built is True

        # Rebuild index
        resolver.build_index()
        assert resolver._index_built is True

        # Resolve should still work
        signal = ExternalSignalCall(
            signal_name="ship_order",
            target_workflow_pattern="shipping-123",
            source_line=10,
            node_id="ext_sig_ship_order_10",
            source_workflow="OrderWorkflow",
        )
        handlers = resolver.resolve(signal)
        assert len(handlers) == 1

    def test_resolver_with_nested_directories(
        self, nested_dirs: Path
    ) -> None:
        """Test that resolver finds workflows in nested subdirectories."""
        resolver = SignalNameResolver([nested_dirs])
        resolver.build_index()

        # Should find all three signals
        assert "root_signal" in resolver._handler_index
        assert "sub1_signal" in resolver._handler_index
        assert "deep_signal" in resolver._handler_index

    def test_resolver_multiple_search_paths(
        self, resolver_test_dir: Path, multiple_handlers_dir: Path
    ) -> None:
        """Test resolver with multiple search paths."""
        resolver = SignalNameResolver([resolver_test_dir, multiple_handlers_dir])
        resolver.build_index()

        # Should find handlers from both directories
        assert "ship_order" in resolver._handler_index
        assert "notify_shipped" in resolver._handler_index
        assert "process_payment" in resolver._handler_index

    def test_resolver_with_symlinks(self, tmp_path: Path) -> None:
        """Test resolver handles symlinks gracefully."""
        # Create a directory with a workflow
        actual_dir = tmp_path / "actual"
        actual_dir.mkdir()

        workflow = actual_dir / "workflow.py"
        workflow.write_text('''
from temporalio import workflow

@workflow.defn
class SymlinkWorkflow:
    @workflow.signal
    async def symlink_signal(self) -> None:
        pass

    @workflow.run
    async def run(self) -> None:
        pass
''')

        # Create a symlink to the directory
        symlink_dir = tmp_path / "symlink"
        try:
            symlink_dir.symlink_to(actual_dir)
        except OSError:
            # Skip test on systems that don't support symlinks
            pytest.skip("Symlinks not supported on this system")

        resolver = SignalNameResolver([symlink_dir])
        resolver.build_index()

        # Should find the handler through the symlink
        assert "symlink_signal" in resolver._handler_index

    def test_resolver_ignores_pycache(self, resolver_test_dir: Path) -> None:
        """Test that resolver ignores __pycache__ directories."""
        # Create a __pycache__ directory with a .py file
        pycache = resolver_test_dir / "__pycache__"
        pycache.mkdir()
        cached_file = pycache / "cached_workflow.cpython-311.py"
        cached_file.write_text('''
from temporalio import workflow

@workflow.defn
class CachedWorkflow:
    @workflow.signal
    async def cached_signal(self) -> None:
        pass

    @workflow.run
    async def run(self) -> None:
        pass
''')

        resolver = SignalNameResolver([resolver_test_dir])
        resolver.build_index()

        # Should NOT find the cached_signal (from __pycache__)
        assert "cached_signal" not in resolver._handler_index
        # Should still find the legitimate handlers
        assert "ship_order" in resolver._handler_index

    def test_resolver_with_workflow_with_multiple_signals(
        self, tmp_path: Path
    ) -> None:
        """Test workflow with multiple signal handlers."""
        workflow = tmp_path / "multi_signal_workflow.py"
        workflow.write_text('''
from temporalio import workflow

@workflow.defn
class MultiSignalWorkflow:
    @workflow.signal
    async def signal_one(self) -> None:
        pass

    @workflow.signal
    async def signal_two(self) -> None:
        pass

    @workflow.signal(name="custom_name")
    async def signal_three(self) -> None:
        pass

    @workflow.run
    async def run(self) -> None:
        pass
''')

        resolver = SignalNameResolver([tmp_path])
        resolver.build_index()

        # Should find all three signals
        assert "signal_one" in resolver._handler_index
        assert "signal_two" in resolver._handler_index
        assert "custom_name" in resolver._handler_index

        # All handlers should reference the same workflow class
        for signal_name in ["signal_one", "signal_two", "custom_name"]:
            handlers = resolver._handler_index[signal_name]
            assert len(handlers) == 1
            _, handler = handlers[0]
            assert handler.workflow_class == "MultiSignalWorkflow"


class TestAnalyzeFile:
    """Tests for _analyze_file() helper method."""

    def test_analyze_file_valid_workflow(
        self, resolver_test_dir: Path
    ) -> None:
        """Test _analyze_file with valid workflow file."""
        resolver = SignalNameResolver([resolver_test_dir])
        file_path = resolver_test_dir / "shipping_workflow.py"

        metadata = resolver._analyze_file(file_path)

        assert metadata is not None
        assert metadata.workflow_class == "ShippingWorkflow"
        assert len(metadata.signal_handlers) == 1
        assert metadata.signal_handlers[0].signal_name == "ship_order"

    def test_analyze_file_syntax_error(self, invalid_files_dir: Path) -> None:
        """Test _analyze_file returns None for syntax error."""
        resolver = SignalNameResolver([invalid_files_dir])
        file_path = invalid_files_dir / "syntax_error.py"

        metadata = resolver._analyze_file(file_path)

        assert metadata is None

    def test_analyze_file_not_workflow(self, invalid_files_dir: Path) -> None:
        """Test _analyze_file returns None for non-workflow file."""
        resolver = SignalNameResolver([invalid_files_dir])
        file_path = invalid_files_dir / "not_workflow.py"

        metadata = resolver._analyze_file(file_path)

        assert metadata is None

    def test_analyze_file_not_found(self, tmp_path: Path) -> None:
        """Test _analyze_file returns None for non-existent file."""
        resolver = SignalNameResolver([tmp_path])
        file_path = tmp_path / "does_not_exist.py"

        metadata = resolver._analyze_file(file_path)

        assert metadata is None
