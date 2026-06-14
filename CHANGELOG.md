# Changelog

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-06-13

### Fixed
- `03_evals.py --judge` lets the LLM judge adjudicate disagreements, recovering a
  valid answer the substring grader missed (the honesty case) instead of only
  removing passes. The no-judge run now names the brittle-grader false negative
  so the lesson lands either way.

## [0.1.0] - 2026-06-13

### Added
- Five-act build: first call, tools as contracts, evals in CI, cost engineering,
  and the MCP encore.
- Live cost benchmark (naive, cached, routed) that writes measured numbers.
- `scripts/check_docs.py` doc-correctness gate. CI compiles the acts, runs the
  offline benchmark, and self-lints the README.
