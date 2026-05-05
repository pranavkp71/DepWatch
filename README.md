# 🔍 DepWatch — Dependency Health Scanner

> Are your dependencies risky right now?

DepWatch scans a GitHub repository, extracts its dependencies, and gives each one a simple health rating:

| Status | Meaning |
|--------|---------|
| 🟢 Healthy | Active commits + responsive maintainers |
| 🟡 Warning | Low contributors or slowing activity |
| 🔴 Risky | No recent commits or unresponsive issues |

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# CLI
depwatch scan https://github.com/user/project

# API server
uvicorn app.main:app --reload
```

## Tech Stack

- **Backend** — FastAPI
- **CLI** — Typer + Rich
- **Data source** — GitHub REST API
- **HTTP client** — httpx

## Project Structure

```
depwatch/
├── app/
│   ├── main.py          # FastAPI app
│   ├── github/          # GitHub API client
│   ├── scoring/         # Health scoring logic
│   └── services/        # Shared utilities
├── cli/
│   └── main.py          # Typer CLI
├── tests/
├── pyproject.toml
└── README.md
```

## License

MIT
