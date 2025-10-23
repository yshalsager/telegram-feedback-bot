ARG PYTHON_VERSION=3.14-rc
ARG UV_VERSION=0.8.19
ARG NODE_VERSION=24

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
COPY frontend ./frontend
COPY static ./static
RUN pnpm run build

FROM python-base AS runtime
RUN useradd -m appuser
WORKDIR /code
ENV PATH=/code/.venv/bin:$PATH \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never
COPY --from=python-builder --chown=appuser:appuser /code/.venv /code/.venv
COPY --chown=appuser:appuser manage.py pyproject.toml uv.lock alembic.ini ./
COPY --chown=appuser:appuser config feedback_bot src messages static ./
COPY --from=frontend-builder --chown=appuser:appuser /code/build ./build
RUN TELEGRAM_BUILDER_BOT_ADMINS=0 TELEGRAM_BUILDER_BOT_TOKEN=dummy TELEGRAM_ENCRYPTION_KEY=dummy uv run python manage.py compilemessages
USER appuser
EXPOSE 8001
CMD ["uv", "run", "granian", "--interface", "asgi", "config.asgi:application"]
