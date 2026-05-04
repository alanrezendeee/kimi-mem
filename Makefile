.PHONY: install test lint clean dev status

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

lint:
	ruff check kimi_mem/

format:
	ruff format kimi_mem/

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

dev:
	python3 -m venv .venv
	.venv/bin/pip install -e ".[dev]"

status:
	kimi-mem status

hooks-install:
	kimi-mem install

hooks-uninstall:
	kimi-mem uninstall
