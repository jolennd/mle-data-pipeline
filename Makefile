-include .env
export
-include make/db.mk
-include make/transform.mk
-include make/orchestrate.mk
-include make/ingest.mk
-include make/docker.mk
-include make/assistant.mk
.PHONY: test-fast test lint format validate-gates

test-fast:
	uv run pytest -m "not dbserver and not docker and not deploy and not model and not data"
test:
	uv run pytest -m "not docker and not deploy"
lint:
	uv run ruff check --no-cache . && uv run ruff format --check .
format:
	uv run ruff format .
validate-gates: lint test-fast
