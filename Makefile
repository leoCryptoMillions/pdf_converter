# Supported single-user MVP. Use PYTHON=.venv/bin/python (or Windows equivalent).
PYTHON ?= python
.PHONY: help install install-dev run run-local test test-full test-unit test-coverage test-e2e release-check inventory

help:
	@echo "MVP: install install-dev run test test-full test-unit test-coverage test-e2e release-check inventory"
	@echo "Browser checks require npm ci and npx playwright install chromium."

install:
	$(PYTHON) -m pip install --require-hashes -r requirements-mvp.lock

install-dev:
	$(PYTHON) -m pip install --require-hashes -r requirements-mvp-dev.lock

run run-local:
	$(PYTHON) -m apps.local_review_ui

test:
	$(PYTHON) -m pytest -q

test-full test-unit:
	$(PYTHON) -m pytest tests/unit -q -m "mvp or not mvp"

test-coverage:
	$(PYTHON) -m pytest -q -m "mvp or not mvp" --cov=apps --cov=packages --cov-branch --cov-report=html --cov-report=term --cov-fail-under=70

test-e2e:
	$(PYTHON) -m scripts.check_browser

release-check:
	$(PYTHON) -m scripts.check_release --audit

inventory:
	$(PYTHON) -m benchmarks.dependency_inventory --profile mvp
