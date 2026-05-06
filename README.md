# DepWatch — Dependency Health Scanner

> Know *why* your dependencies are healthy or risky — not just that they are.

DepWatch scans a GitHub repository, extracts its dependencies, and delivers a transparent health report for each one: a **numeric risk score**, evidence **signals**, and an **actionable recommendation**.

## Features

- **Multi-signal analysis** — commits, releases, contributors, and issue activity
- **Risk score (0–10)** — quantifiable health metric for every dependency
- **Confidence levels** — High / Medium / Low based on signal agreement
- **Actionable recommendations** — clear guidance on what to do next
- **Rich CLI output** — color-coded panels with detailed breakdowns
- **FastAPI backend** — REST API for programmatic access

## Installation

### From PyPI

```bash
pip install depwatch-cli
```

### From Source

```bash
git clone https://github.com/pranavkp71/DepWatch.git
cd DepWatch
pip install -e ".[dev]"
```

This creates `dist/dep_watch-X.Y.Z.tar.gz` and `dist/dep_watch-X.Y.Z-py3-none-any.whl`.

## Usage

### Scan a Repository

```bash
depwatch scan https://github.com/fastapi/fastapi
```

### GitHub Token (Recommended)

Set a token to avoid rate limits:

```bash
export GITHUB_TOKEN=ghp_your_token_here
```

Or create a `.env` file:

```
GITHUB_TOKEN=ghp_your_token_here
```

### API Server

```bash
uvicorn app.main:app --reload
```

## Sample Output

```
📦 Found 5 dependencies. Analyzing health...

🟢 5 healthy

╭─────────── pydantic ────────────╮
│ Status: Healthy                 │
│ Risk Score: 0/10                │
│ Confidence: High                │
│                                 │
│ Signals:                        │
│   • Last commit 0 days ago      │
│   • Last release 15 days ago    │
│   • Contributor count: 100      │
│   • Open issues: 560            │
│   • 100 issues updated recently │
│                                 │
│ Action: No action needed        │
╰─────────────────────────────────╯
```

## How Scoring Works

### Health Statuses

| Status | Risk Score | Meaning |
|--------|:----------:|---------|
| 🟢 Healthy | 0 – 3 | Active commits, responsive maintainers |
| 🟡 Warning | 4 – 6 | Slowing activity or low contributor count |
| 🔴 Risky | 7 – 10 | Stale commits, stale releases, solo maintainer |

### Risk Score Weights

| Factor | Points |
|--------|:------:|
| No commits in 90+ days | +3 |
| Releases stale 120+ days | +3 |
| No official releases | +1 |
| Low contributor count (<2) | +2 |
| Stagnant issues (50+, no activity) | +2 |
| Large maintainer base (10+) | −2 |

### Confidence Levels

- **High** — 3+ signals agree
- **Medium** — 2 signals agree
- **Low** — only 1 weak signal

## Limitations

- Only supports GitHub-hosted repositories
- Parses `requirements.txt`, `package.json`, and `pyproject.toml`
- GitHub API rate limits apply (use a token for best results)
- Does not analyze code quality or vulnerabilities directly

## Project Structure

```
depwatch/
├── app/
│   ├── main.py          # FastAPI app & API models
│   ├── github/          # GitHub API client
│   ├── scoring/         # Health scoring engine
│   └── services/        # Dependency scanner + analyzer
├── cli/
│   └── main.py          # Typer CLI with Rich output
├── tests/
│   └── test_scoring.py  # Unit tests
├── .github/             # CI & templates
├── pyproject.toml
├── Makefile
└── README.md
```

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT — see [LICENSE](LICENSE) for details.
