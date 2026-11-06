# ADR 3: Project scope
Status: accepted (replaces the former ADRs 3 to 11, which recorded each out-of-scope item separately)
Context: The brief asks for a pipeline: download three monthly files, transform them into revenue per day, and orchestrate the runs. It asks for no model, no API and no hosted service.
Decision: In scope: download, raw load, staging, star schema, daily mart, export, plain entry point, Prefect orchestration, and a local container (ADR 18). Not in scope:
- Refactoring a notebook into a package: there was no existing notebook code; the package was written test-first.
- Model training, evaluation and a prediction endpoint: there is no model.
- A resource API: nothing needs to query the data over HTTP.
- Deployment to a host and monitoring with dashboards and alerts: the pipeline runs locally.
- A separate CI/CD pipeline: `.github/workflows/tests.yml` already runs lint and the fast tests on every push and pull request.
Consequences: The repository has no API, model or deploy code. Adding any of these later needs a new ADR that changes this scope.
