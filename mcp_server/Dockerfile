FROM ghcr.io/astral-sh/uv:latest AS uv
FROM python:3.12-slim

COPY --from=uv /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev 2>/dev/null || uv sync --no-dev

COPY server.py seed.py ./
RUN uv run seed.py

ENV KPI_DB=/app/kpi.db
EXPOSE 9000
CMD ["uv", "run", "server.py"]