FROM python:3.12-alpine as base
ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

RUN addgroup -g 1000 bot && \
    adduser -u 1000 -G bot -h /home/bot -D bot && \
    mkdir /app && chown -R bot:bot /app
WORKDIR /app

FROM base as builder
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=1.8.3
ENV PATH="/home/bot/.local/bin:${PATH}"

RUN pip install "poetry==$POETRY_VERSION"
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.in-project true && \
    poetry install --only=main --no-root --no-interaction --no-ansi

FROM base as final

COPY --from=builder /app/.venv ./.venv
COPY .env .

RUN chown -R bot:bot /app
USER bot
