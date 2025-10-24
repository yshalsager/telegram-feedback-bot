# Telegram Feedback Bots Builder

A self-hosted toolkit for provisioning and operating Telegram feedback bots. The new stack pairs a Django + python-telegram-bot backend with a SvelteKit mini app so owners can manage bots, rotate tokens, review stats, and handle banned users without leaving Telegram. Think of it as Livegram but more powerful.

## Features

### Builder Bot

- `/start` launches the inline menu with a deep link to the mini app.
- `/broadcast` forwards announcements to all builder users.
- `/whitelist`, `/manage`, `/restart`, and `/update` remain available for administrators.

### Mini App Dashboard

- Create feedback bots after validating their tokens against BotFather.
- Update start / receipt messages and link or unlink groups.
- Rotate bot tokens securely with enforced admin approval before re-enabling (when configured).
- Inspect live stats, review audit history of broadcasts, and manage banned users per bot.
- Manage builder access: whitelist, language, admin flags, and removal.

🔒 See the [Privacy Policy](PRIVACY_POLICY.md) for details on data that is stored.

### Feedback Bots

- Route every user conversation into its own forum topic (or the owner chat) for clean threading.
- Forward edits, mirror replies back to the user, and automatically acknowledge receipt with an emoji.
- Provide owner tooling: `/broadcast`, `/ban`, `/unban`, `/banned`, `/delete` (reply to remove a single pair), and `/clear` (reply to drop that message and everything after it in the thread), plus `/start` for users.

## Technology Stack

- **Backend:** Python 3, Django 5, Ninja API, python-telegram-bot 21, Granian (ASGI), SQLite (Postgres optional).
- **Frontend:** SvelteKit, Vite, Tailwind CSS, Bits UI, Telegram Mini App SDK.
- **Packaging & Tooling:** mise, uv, pnpm, Docker, lefthook.
- **Infrastructure extras:** Traefik override (optional), encrypted token storage (Fernet).

## Setup

1. **Clone the repository**

    ```bash
    git clone https://github.com/yshalsager/telegram_feedback_bot.git
    cd telegram_feedback_bot
    ```

2. **Install toolchain with mise**

    ```bash
    mise install
    ```

3. **Create `.env`** (values mirror [`mise.toml`](mise.toml)`[env]`). At minimum:

    ```dotenv
    DJANGO_SECRET_KEY="$(mise r generate-secret-key)"
    TELEGRAM_BUILDER_BOT_TOKEN="123456789:AA..."
    TELEGRAM_BUILDER_BOT_WEBHOOK_URL="https://your-domain.com"
    TELEGRAM_BUILDER_BOT_WEBHOOK_PATH="telegram"
    TELEGRAM_BUILDER_BOT_ADMINS="123456789,987654321"
    TELEGRAM_ADMIN_CHAT_ID="-10000000000"
    TELEGRAM_LOG_TOPIC_ID=1
    TELEGRAM_ENCRYPTION_KEY="$(mise r generate-encryption-key)"
    TELEGRAM_LANGUAGES="en ar"
    POSTGRES_DB="feedback_bot"
    POSTGRES_USER="feedback_bot_user"
    POSTGRES_PASSWORD="super-secret"
    DJANGO_ALLOWED_HOSTS="localhost 127.0.0.1"
    TELEGRAM_NEW_BOT_ADMIN_APPROVAL=true
    ``
    Set `TELEGRAM_BUILDER_BOT_WEBHOOK_URL` to the public HTTPS origin serving Granian. Leave `DJANGO_USE_SQLITE=true` if you prefer SQLite for local experiments.

    ```

4. **Install dependencies**

    ```bash
    mise x uv -- uv sync
    mise x pnpm -- pnpm install
    ```

5. **Run migrations**
    ```bash
    mise x uv -- uv run manage.py migrate
    ```

## Running

### Docker

The compose stack bundles the backend, PTB workers, and Postgres. Copy your `.env` next to `docker-compose.yml`, then:

```bash
docker compose up --build -d
```

Static assets from the SvelteKit build are served by Granian under `/app/`. Attach volume `data/` if you need to persist exported artifacts.

### Manual (mise + uv + pnpm)

Run backend and frontend separately during development:

```bash
# Backend API + Telegram bots
mise x uv -- uv run granian --interface asgi config.asgi:application

# Frontend mini app
mise x pnpm -- pnpm run dev
```

Or let mise orchestrate everything:

```bash
mise run migrate
mise run api-dev   # starts Granian with autoreload
mise run client-dev
```

For a production build of the mini app:

```bash
mise x pnpm -- pnpm run build
```

The compiled bundle lands in `build/` and is mounted automatically by Granian when `GRANIAN_STATIC_PATH_*` variables are set (default values already point there).

## Telegram Webhook Notes

- Set the builder webhook by exposing Granian at `https://<domain>/api/webhook/<TELEGRAM_BUILDER_BOT_WEBHOOK_PATH>/`.
- Each managed bot receives a dedicated webhook at `/api/webhook/<bot_uuid>/`; secrets are generated from `TELEGRAM_ENCRYPTION_KEY`.
- When admin approval is enabled (`TELEGRAM_NEW_BOT_ADMIN_APPROVAL=true`), new bots start disabled until a builder admin activates them from the dashboard.

## Testing

```bash
# Backend tests
mise x uv -- uv run pytest

# Frontend unit tests
mise x pnpm -- pnpm run test

# Linting & type checks
mise x pnpm -- pnpm run lint
mise x pnpm -- pnpm run check
```

## Migrating from the legacy Pyrogram version

1. **Create backups** of your existing `feedback_bot.db` builder database and the per-bot files inside `data/` (or whichever paths you configured).
2. **Populate environment variables** used by the legacy stack. Export the old `ENCRYPTION_KEY` (the XOR key from the Pyrogram build) alongside the new `.env` variables.
3. **Install and migrate** the Django project as described above, then run:
    ```bash
    mise x uv -- uv run manage.py migrate_legacy_data --builder-db feedback_bot.db --data-dir data
    ```
    Adjust the paths if your legacy assets live elsewhere. The command can be re-run safely; it upserts records.
4. **Review migrated bots** in the mini app. Re-enable each bot once you are satisfied (admin approval still applies when `TELEGRAM_NEW_BOT_ADMIN_APPROVAL=true`).
5. **Reset webhooks** by redeploying the app or restarting `granian` so the builder and managed bots pick up their new webhook endpoints.

## Project Layout

- `config/` – Django project configuration and ASGI entrypoint.
- `feedback_bot/` – Backend app (API, models, telegram builders, PTB handlers).
- `src/` – SvelteKit mini app served inside Telegram.
- `data/` – Shared volume for runtime assets (bot storage, exports).
- `docker-compose.yml` – Production-ready stack with Postgres + Granian.
- `mise.toml` – Task runner and environment defaults.

### Historical Versions
- [Original Pyrogram-based builder](https://github.com/yshalsager/telegram-feedback-bot/blob/master/README.md)
- [Standalone single-bot edition](https://github.com/yshalsager/telegram-feedback-bot/blob/standalone/README.md)

## Acknowledgements

- [Django](https://www.djangoproject.com/), [Ninja](https://django-ninja.dev/), and [Granian](https://github.com/emmett-framework/granian) for the backend.
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) for Telegram integrations.
- [SvelteKit](https://kit.svelte.dev/), [Tailwind CSS](https://tailwindcss.com/), and [Bits UI](https://www.bits-ui.com/) for the mini app.
- [uv](https://github.com/astral-sh/uv) and [mise](https://mise.jdx.dev/) for fast, reproducible environments.

## Development Tips

- `mise r` starts migrations, Granian, and the SvelteKit dev server in one go.
- Use `mise x uv -- uv run manage.py shell_plus` for interactive debugging.
- Internationalization helpers live under `src/locales` and `feedback_bot/locale`; run `mise r i18n_update` after editing strings.
