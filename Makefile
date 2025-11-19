.PHONY: help run-examples test lint format clean

help:
	@echo "Available targets:"
	@echo "  run-examples  - Run all example workflows"
	@echo "  test          - Run all tests"
	@echo "  lint          - Run linters (mypy, ruff)"
	@echo "  format        - Format code with ruff"
	@echo "  clean         - Remove temporary files"

run-examples:
	@echo "Running all example workflows..."
	@echo "\n=== Simple Linear Example ==="
	python examples/simple_linear/run.py
	@echo "\n=== Money Transfer Example ==="
	python examples/money_transfer/run.py
	@echo "\n=== Signal Workflow Example ==="
	python examples/signal_workflow/run.py
	@echo "\n=== Multi-Decision Example ==="
	python examples/multi_decision/run.py
	@echo "\n✓ All examples completed successfully"

test:
	pytest -v --cov=src/temporalio_graphs

lint:
	mypy src/
	ruff check src/ tests/ examples/

format:
	ruff format src/ tests/ examples/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov
