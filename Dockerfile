# Stage 1: Build dependencies
FROM python:3.13-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="$POETRY_HOME/bin:$PATH"
WORKDIR /code
COPY pyproject.toml poetry.lock* ./
RUN poetry install --with main --no-root

# Stage 2: Run-time image
FROM python:3.13-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/code/.venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    # for code update
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code
COPY --from=builder /code/.venv ./.venv
RUN useradd -m appuser
USER appuser

WORKDIR /code/app
CMD ["python3", "-m", "src"]
