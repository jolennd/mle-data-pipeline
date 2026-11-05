.PHONY: transform transform-test transform-debug
transform:
	uv run python transform/dbt_env.py seed
	uv run python transform/dbt_env.py run
transform-test:
	uv run python transform/dbt_env.py test
transform-debug:
	uv run python transform/dbt_env.py debug
