# ADR 10: Skip phase 7 (CI/CD)
Status: accepted
Context: This is a pipeline project. The brief has no model, API, container or deploy.
Decision: Skip phase 7 (CI/CD) because there is no container or deploy. A workflow that runs ruff and pytest on pull requests already exists in .github/workflows/tests.yml, so no separate phase is needed.
Consequences: No work or gate for phase 7. No later phase that runs lists it under Requires.
