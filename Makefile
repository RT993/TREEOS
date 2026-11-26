# TREE OS development entry points (CLAUDE.md sections 12-13).
# Python tooling lives in a project-local virtual environment (.venv),
# never in the system Python.

PYTHON ?= python3
VENV   ?= .venv
VPY    := $(VENV)/bin

.PHONY: help venv lint format-check typecheck test shellcheck js-lint js-test check clean

help:
	@echo "Targets:"
	@echo "  venv         Create .venv and install requirements-dev.txt"
	@echo "  lint         Ruff lint and format check (Python)"
	@echo "  typecheck    mypy (Python)"
	@echo "  test         pytest"
	@echo "  shellcheck   ShellCheck on tracked shell scripts"
	@echo "  js-lint      ESLint (JavaScript)"
	@echo "  js-test      Node unit tests for JavaScript logic"
	@echo "  check        Run every quality gate"
	@echo "  clean        Remove caches and .venv"

$(VPY)/pytest: requirements-dev.txt
	$(PYTHON) -m venv $(VENV)
	$(VPY)/pip install --upgrade pip
	$(VPY)/pip install -r requirements-dev.txt
	@touch $(VPY)/pytest

venv: $(VPY)/pytest

lint: venv
	$(VPY)/ruff check .
	$(VPY)/ruff format --check .

typecheck: venv
	$(VPY)/mypy

test: venv
	$(VPY)/pytest

shellcheck:
	@files="$$(git ls-files '*.sh' '*.bash')"; \
	if [ -z "$$files" ]; then \
		echo "shellcheck: no tracked shell scripts"; \
	else \
		shellcheck $$files; \
	fi

js-lint:
	npm ci --no-audit --no-fund
	npx eslint .

js-test:
	node --test tests/js/pinned-apps.test.mjs

check: lint typecheck test shellcheck js-lint js-test
	@echo "All quality gates passed."

clean:
	rm -rf $(VENV) .pytest_cache .ruff_cache .mypy_cache node_modules
