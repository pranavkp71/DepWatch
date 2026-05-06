# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅        |

## Reporting a Vulnerability

If you discover a security vulnerability, please **do not** open a public issue.

Instead, email the maintainers or open a private security advisory on GitHub.

We will respond within 48 hours and work toward a fix.

## Scope

DepWatch interacts with the GitHub REST API using user-provided tokens. We take the following precautions:

- Tokens are read from environment variables only (never hardcoded)
- No data is stored or transmitted to third parties
- All API calls are read-only

## Best Practices for Users

- Use a GitHub token with **minimal permissions** (public repo read access)
- Store your token in a `.env` file and ensure `.env` is in `.gitignore`
