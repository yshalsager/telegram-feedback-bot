# Stage 1: Build dependencies
FROM python:3.13-slim-bookworm AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

WORKDIR /code
COPY pyproject.toml uv.lock /code/
RUN uv sync --frozen --no-cache

# Stage 2: Run-time image
FROM python:3.13-slim-bookworm AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    # for code update
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code
COPY --from=builder /code/.venv ./.venv
ENV PATH="/code/.venv/bin:$PATH"
RUN useradd -m appuser
USER appuser

WORKDIR /code/app
CMD ["python3", "-m", "src"]
