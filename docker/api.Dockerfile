FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-install-project
COPY src ./src
COPY benchmarks ./benchmarks
COPY policies ./policies
COPY seeds ./seeds
RUN uv sync --locked --no-dev
RUN useradd --create-home --uid 10001 careloop
USER careloop
EXPOSE 8000
CMD ["uv", "run", "--locked", "uvicorn", "careloop.web_api.server:app", "--host", "0.0.0.0", "--port", "8000"]
