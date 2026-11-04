# File database: nothing to start or stop. Targets exist so docs stay identical across choices.
.PHONY: db-up db-wait db-down
db-up:
	@mkdir -p data && echo "duckdb: file database, nothing to start"
db-wait:
	@true
db-down:
	@echo "duckdb: nothing to stop"
