# DepWatch — Dependency Health Scanner

> Know *why* your dependencies are healthy or risky — not just that they are.

DepWatch scans a GitHub repository, extracts its dependencies, and delivers a transparent health report for each one: a **numeric risk score**, evidence **signals**, and an **actionable recommendation**.

---

## Health Statuses

| Status | Risk Score | Meaning |
|--------|:----------:|---------|
| 🟢 Healthy | 0 – 3 | Active commits, responsive maintainers |
| 🟡 Warning | 4 – 6 | Slowing activity or low contributor count |
| 🔴 Risky | 7 – 10 | Stale commits, stale releases, solo maintainer |

---

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Scan a repository
depwatch scan https://github.com/user/repo

# Run the API server
uvicorn app.main:app --reload
```

Set a `GITHUB_TOKEN` in your `.env` for higher rate limits:
```bash
GITHUB_TOKEN=ghp_your_token_here
```

---

## V1

Each dependency now comes with a **detailed panel** in the CLI:

```
╭──────────── some-library ─────────────╮
│ Status:     Warning                   │
│ Risk Score: 5/10                      │
│ Confidence: High                      │
│                                       │
│ Signals:                              │
│   • Last commit 95 days ago           │
│   • Last release 130 days ago         │
│   • Contributor count: 1              │
│                                       │
│ Action: Monitor this dependency       │
╰───────────────────────────────────────╯
```

### Signal-Based Confidence
Confidence is derived from how many significant factors agree:
- **High** — 3+ signals point the same direction
- **Medium** — 2 signals agree
- **Low** — only 1 weak signal

### Risk Score Weights
| Factor | Points |
|--------|:------:|
| No commits in 90+ days | +3 |
| Releases stale 120+ days | +3 |
| Low contributor count (<2) | +2 |
| Stagnant issues (50+, no activity) | +2 |
| Large maintainer base (10+) | −2 |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI |
| CLI | Typer + Rich |
| Data source | GitHub REST API |
| HTTP client | httpx |

---

## Project Structure

```
depwatch/
├── app/
│   ├── main.py          # FastAPI app & API models
│   ├── github/          # GitHub API client
│   ├── scoring/         # V3 Health scoring engine (HealthReview dataclass)
│   └── services/        # Dependency scanner + analyzer
├── cli/
│   └── main.py          # Typer CLI with Rich panel output
├── tests/
│   └── test_scoring.py  # Unit tests for scoring logic
└── pyproject.toml
```

---

