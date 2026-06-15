# claude-prompt-to-production operator commands. POSIX-make-friendly.
.DEFAULT_GOAL := help
.PHONY: help setup demo test check

help:
	@printf 'claude-prompt-to-production\n\n'
	@printf '  make setup   Install the Python deps (one time)\n'
	@printf '  make demo    Render the cost table from sample data, offline, no API key\n'
	@printf '  make test    Run the eval-set self-test\n'
	@printf '  make check   Run the doc-correctness gate\n'

setup:
	pip install -q -r requirements.txt

demo:
	@printf '== same workload, three ways (sample data, no API key needed) ==\n'
	python 04_cost_engineering.py

test:
	python eval_lint.py --selftest

check:
	python scripts/check_docs.py
