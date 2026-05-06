# Release Guide

How to build and publish DepWatch to PyPI.

## Prerequisites

```bash
pip install build twine
```

## 1. Build the Package

```bash
python -m build
```

This creates `dist/depwatch_cli-X.Y.Z.tar.gz` and `dist/depwatch_cli-X.Y.Z-py3-none-any.whl`.

## 2. Test on TestPyPI

```bash
twine upload --repository testpypi dist/*
```

Verify installation:
```bash
pip install --index-url https://test.pypi.org/simple/ depwatch-cli
```

## 3. Publish to PyPI

```bash
twine upload dist/*
```

## 4. Post-Release Checklist

- [ ] Tag the release: `git tag v0.1.0 && git push --tags`
- [ ] Create a GitHub Release with notes from `CHANGELOG.md`
- [ ] Update version in `pyproject.toml` for next cycle
