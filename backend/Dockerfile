FROM ghcr.io/astral-sh/uv:0.13.10 AS uv
FROM python:3.12-slim-bookworm

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app
COPY --from=uv /uv /bin/uv
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev && useradd --create-home --uid 10001 appuser
COPY app ./app
COPY scripts ./scripts
COPY alembic.ini ./
COPY alembic ./alembic
USER appuser
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && python -m scripts.seed_knowledge && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1"]
