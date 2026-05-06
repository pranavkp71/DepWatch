# Changelog

All notable changes to DepWatch will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/).

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
