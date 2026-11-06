# Data lives in the named volume "data". Only docker-clean deletes it, and it asks first.
.PHONY: docker-build docker-up docker-flow docker-pipeline docker-results docker-down docker-clean docker-test
docker-build:
	docker compose build
docker-up:
	docker compose up -d --wait prefect
docker-flow: docker-up
	docker compose run --rm flow
docker-pipeline:
	@test -n "$(PARTITION)" || (echo "usage: make docker-pipeline PARTITION=<value>"; exit 1)
	docker compose run --rm pipeline $(PARTITION)
docker-results:
	docker compose run --rm --entrypoint ls pipeline -la data/processed
docker-down:
	docker compose down
docker-clean:
	@read -p "Delete the Docker data volume (downloads, database, results)? [y/N] " a; [ "$$a" = "y" ] || (echo "kept"; exit 1)
	docker compose down -v
docker-test:
	uv run pytest -m docker
