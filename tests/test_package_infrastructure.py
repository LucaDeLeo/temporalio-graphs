"""Infrastructure smoke tests - verify package setup is correct."""

import temporalio_graphs


def test_package_version() -> None:
    """Verify package version is accessible."""
    assert temporalio_graphs.__version__ == "0.1.0"


def test_package_has_docstring() -> None:
    """Verify package has documentation."""
    assert temporalio_graphs.__doc__ is not None
    assert len(temporalio_graphs.__doc__) > 0
