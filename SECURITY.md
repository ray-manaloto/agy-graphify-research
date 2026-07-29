# Security Policy

## Reporting Vulnerabilities

If you discover a potential security vulnerability in `agy-graphify-research`, please report it by opening a security advisory or contacting the maintainers directly.

Please do not report security vulnerabilities through public GitHub issues.

## Isolation Policy

This repository implements strict environment isolation guardrails:
- Zero global state mutation in `~/.gemini` or user system folders.
- Mandatory execution verification via pre-commit and post-commit hooks.
