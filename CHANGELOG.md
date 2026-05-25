# Changelog

All notable changes to DepWatch will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- Transitive Dependency Analysis (MVP)
  - Recursive resolution of nested dependencies via PyPI metadata
  - Cycle detection and depth limiting to prevent runaway scans
  - New `--transitive` / `-t` flag for the `scan` command
  - New `--depth` / `-d` option to control recursion depth
  - Enhanced CLI output with `[direct]` vs `[transitive]` labels
  - Visible dependency paths for nested packages (e.g., `pkg-a → pkg-b → risky-pkg`)
  - Integration of transitive analysis into the FastAPI `/scan` endpoint

## [0.1.0] — 2026-05-06

### Added
- CLI tool: `depwatch scan <github-url>`
- Multi-signal health scoring engine (commits, releases, contributors, issues)
- Numeric risk score (0–10) per dependency
- Signal-based confidence levels (High / Medium / Low)
- Actionable recommendations for each dependency
- Rich panel output in terminal
- FastAPI backend with `/scan` endpoint
- GitHub REST API integration with token support
