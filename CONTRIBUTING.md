# Contributing to WinTriage

Thanks for your interest in improving WinTriage. Contributions are welcome — bug fixes, new artifact sources, performance improvements, and documentation.

## Getting started

1. Fork the repository
2. Create a branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Test on a live Windows system with Administrator privileges
5. Open a pull request with a clear description of what changed and why

## What's useful to contribute

- New artifact sources (Shimcache, Amcache, LNK metadata, scheduled tasks, etc.)
- Better signature checking (WDAC, catalog verification)
- Output formatting improvements (JSON export, CSV, HTML report)
- Performance improvements for large MFT datasets
- Offline image support
- Tests and CI

## Code style

- Standard Python — no formatter enforced, but keep it readable
- Functions should do one thing and be named clearly
- Print output uses ANSI color: red for high-confidence findings, yellow for warnings
- Avoid global state where possible

## Reporting issues

Open a GitHub issue with:
- Windows version and build number
- Python version
- What you ran
- What you expected
- What you got (copy the terminal output)

## License

By contributing, you agree your contributions will be licensed under the MIT License.
