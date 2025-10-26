ARG PYTHON_VERSION=3.14
ARG UV_VERSION=0.9.5
ARG NODE_VERSION=24
ARG TELEGRAM_ENCRYPTION_KEY

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv-stage

FROM public.ecr.aws/docker/library/python:${PYTHON_VERSION}-slim-bookworm AS python-base
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gettext \
    git \
    && rm -rf /var/lib/apt/lists/*
COPY --from=uv-stage /uv /usr/local/bin/uv

FROM python-base AS python-builder
WORKDIR /code
COPY pyproject.toml uv.lock ./
ENV UV_LINK_MODE=copy UV_COMPILE_BYTECODE=1 UV_PYTHON_DOWNLOADS=never
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-group dev

FROM public.ecr.aws/docker/library/node:${NODE_VERSION}-slim AS frontend-builder
WORKDIR /code
RUN corepack enable && pnpm config set store-dir /root/.pnpm-store
COPY package.json pnpm-lock.yaml .npmrc ./
RUN --mount=type=cache,target=/root/.pnpm-store pnpm install --frozen-lockfile
COPY svelte.config.js vite.config.js jsconfig.json tsconfig.eslint.json wuchale.config.js components.json vitest-setup-client.js ./
COPY src ./src
COPY static ./static
COPY messages ./messages
RUN pnpm run build

FROM python-base AS runtime
ARG TELEGRAM_ENCRYPTION_KEY
RUN useradd -m appuser
WORKDIR /code
ENV PATH=/code/.venv/bin:$PATH \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_NO_DEV=1 \
    UV_PROJECT_ENVIRONMENT=/code/.venv
COPY --from=python-builder /code/.venv /code/.venv
COPY manage.py pyproject.toml uv.lock ./
COPY config ./config
COPY feedback_bot ./feedback_bot
COPY messages ./messages
COPY static ./static
COPY --from=frontend-builder /code/build ./build
RUN TELEGRAM_ENCRYPTION_KEY="${TELEGRAM_ENCRYPTION_KEY}" uv run manage.py compilemessages && rm -f /code/code.log
RUN chown appuser:appuser /code
USER appuser
EXPOSE 8001
CMD ["uv", "run", "granian", "--interface", "asgi", "config.asgi:application"]
