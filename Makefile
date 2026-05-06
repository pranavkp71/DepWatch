.PHONY: lint format test build clean install

## Install with dev dependencies
install:
	pip install -e ".[dev]"

## Run linter
lint:
	ruff check .

## Auto-format code
format:
	ruff format .

## Run tests
test:
	pytest

## Build distribution
build:
	python -m build

## Remove build artifacts
clean:
	rm -rf dist/ build/ *.egg-info
