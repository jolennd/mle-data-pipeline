.PHONY: download
download:
	uv run python -m data_pipeline.ingest.download $(PARTITION) $(if $(FORCE),--force,)

.PHONY: data-load
data-load:
	uv run python -m data_pipeline.ingest.load $(PARTITION)

.PHONY: pipeline-run
pipeline-run:
	uv run python -m data_pipeline.pipeline $(PARTITION)
