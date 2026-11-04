# Convention: flows/__main__.py takes a partition value, or the word "serve".
.PHONY: orch-server orch-block orch-clean flow-run flow-serve
orch-server:
	uv run prefect server start
orch-block:
	@test -f flows/create_block.py || (echo "no flows/create_block.py: not needed for file or duckdb pipelines"; exit 0)
	@test ! -f flows/create_block.py || uv run python flows/create_block.py
# Use before a run if an old server or a saved API address causes "Failed to reach API".
orch-clean:
	-uv run prefect server stop
	uv run prefect config set PREFECT_SERVER_ALLOW_EPHEMERAL_MODE=true
	-uv run prefect config unset PREFECT_API_URL --yes
flow-run:
	@test -n "$(PARTITION)" || (echo "usage: make flow-run PARTITION=<value>"; exit 1)
	uv run python -m flows $(PARTITION)
flow-serve:
	uv run python -m flows serve
