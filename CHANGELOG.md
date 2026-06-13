# Changelog

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-13

### Added
- Five-act build: first call, tools as contracts, evals in CI, cost engineering,
  and the MCP encore.
- Live cost benchmark (naive, cached, routed) that writes measured numbers.
- `scripts/check_docs.py` doc-correctness gate; CI compiles the acts, runs the
  offline benchmark, and self-lints the README.
