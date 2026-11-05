.PHONY: download
download:
	uv run python -m data_pipeline.ingest.download $(PARTITION) $(if $(FORCE),--force,)
