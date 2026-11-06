FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_ROOT_USER_ACTION=ignore
WORKDIR /app
COPY pyproject.toml ./
RUN pip install . && rm -rf build ./*.egg-info

FROM base AS test
RUN pip install ".[dev]" && rm -rf build ./*.egg-info
COPY . .
CMD ["sh", "-c", "ruff check . && pytest"]

FROM base AS runtime
RUN useradd --system --no-create-home ticketlens
COPY alembic.ini ./
COPY app ./app
COPY migrations ./migrations
USER ticketlens
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
