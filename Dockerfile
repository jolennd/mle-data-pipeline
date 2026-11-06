# uv is pinned: update the tag on purpose, never use latest.
FROM python:3.13-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY src ./src
RUN uv sync --locked --no-dev

FROM python:3.13-slim
WORKDIR /app
RUN useradd --create-home app
COPY --from=build /app /app
# The orchestration folder and the transform project live outside the package.
COPY flows ./flows
COPY transform ./transform
# data/ is the volume mount point. The transform project writes its build output, so it must be writable.
RUN mkdir -p data && chown -R app:app /app/data /app/transform
USER app
ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "-m", "flows", "all"]
