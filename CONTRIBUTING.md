# Contributing to DepWatch

Thanks for your interest in contributing! Here's how to get started.

## Development Setup

```bash
# Clone the repo
git clone https://github.com/pranavkp71/DepWatch.git
cd DepWatch

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest
```

## Linting & Formatting

```bash
ruff check .
ruff format .
```

## Making Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-change`)
3. Make your changes
4. Run tests and linting
5. Commit with a clear message (`git commit -m "feat: add X"`)
6. Push and open a Pull Request


## Code of Conduct

Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## Questions?

Open an issue — we're happy to help.
