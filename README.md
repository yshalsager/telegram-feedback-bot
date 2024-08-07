# Telegram Feedback Bots Builder

A bot that builds feedback Telegram bots like Livegram but with topics support.

**Note**: If you don't need a builder and just want one feedback bot, checkout [standalone](https://github.com/yshalsager/telegram-feedback-bot/tree/standalone) branch.

## Features

### Builder

- Create new feedback bots.
- Manage existing bots.
    - Delete bot.
    - Change its token.
    - Change its group.
    - Change bot messages (start, receive feedback, sent message feedback).
- Admin options:
    - Whitelist users and remove them, disabled by default.
    - Broadcast messages to all users.
    - Restart all bots.
    - Enable or disable bots (via /manage).
    - Update bot code (via /update).
- Multi-language support (automatically selected based on Telegram language).

### Bots

- Receive feedback messages from users.
- Each user has its own topic that messages are sent to, so admins can reply to each user individually and chat history
  is clear.
- General topic messages aren't sent to users, so admins can discuss without spamming users.
- Admins can broadcast messages to all users.
- Bot statistics of users, received and sent messages.

## Configuration

Create a .env file and fill it with requires values from `mise.toml` env section.

```toml
[env]
# the Telegram bot token https://telegram.me/BotFather
BOT_TOKEN = '0000000000:aaaaaaaaaaaaaaaaaaaa'
# to connect to MTProto, which we use to upload media files (retrieve from https://my.telegram.org)
API_ID = '0000000'
API_HASH = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
# the Telegram account IDs that will have administrator permissions of the bot
BOT_ADMINS = '000000,000000,000000'
# Chat that will receive the bot messages
CHAT_ID = '-10000000000'
# Group topic that will be used for bot logs
LOG_TOPIC_ID = 1
# Require admin approval to add new bot
NEW_BOT_ADMIN_APPROVAL = "true"
DEBUG = 1
```

Create an encryption key with `mise r generate-encryption-key`
or `python -c "from secrets import token_bytes; print(token_bytes(32).hex())"`
and update `ENCRYPTION_KEY` variable.

## Running

### Docker

- `docker compose up`

### Poetry

- `poetry install`
- `python3 -m src`

## Usage

### Builder

- `/start`: sends the main menu to create and manage bots.
- `/whitelist [user_id]`: adds new users to the whitelist.'
- `/manage`: manage users and bots by admin.
- `/broadcast`: sends a message to all bot users. Send as a reply to a message previously sent to the bot.
- `/restart`: restarts the bot.
- `/update`: updates the bot code.

### Bots

- `/start`: says hello.
- Send a message, it will be forwarded to the bot owner or group.
- Owner can reply to the message and it will be forwarded to the user.
- `/broadcast`: sends a message to all bot users. Send as a reply to a message previously sent to the bot.
- `/stats`: shows bot statistics.

## How it works?

- Instead of using Telegram bots HTTP API (with long polling or webhooks), we
  use [MTProto](https://core.telegram.org/mtproto) directly via Pyrogram, since Pyrogram uses persistent connections via
  TCP sockets to interact with Telegram servers instead of actively asking for updates.
- The builder bot is responsible for creating Pyrogram clients for bots, and managing them.
- Only builder bot owner can enable or disable bots. Builder bot users can create their own feedback bots and manage
  them.
- SQLAlchemy and Alembic are used for database management. When a new bot is created, a new database is created with
  Alembic to ensure the schema is up to date for all bots.
- Feedback bot forwards messages from users to its created bot owner or group, so it can be replied to. The bot will
  only send the reply to the user if message is a reply to user's message.

## Acknowledgements

### Libraries, Tools, etc

- [Python](https://www.python.org/)
- [Pyrogram](https://github.com/Mayuri-Chan/pyrofork)
- [Plate](https://github.com/delivrance/plate)
- [regex](https://github.com/mrabarnett/mrab-regex)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Alembic](https://alembic.sqlalchemy.org/)

## Development

This project uses several tools to streamline the development process:

### mise

We use [mise](https://mise.jdx.dev/) for managing project-level dependencies and environment variables. mise helps
ensure consistent development environments across different machines.

To get started with mise:

1. Install mise by following the instructions on the [official website](https://mise.jdx.dev/).
2. Run `mise install` in the project root to set up the development environment.

### Poetry

[Poetry](https://python-poetry.org/) is used for dependency management and packaging. It provides a clean,
version-controlled way to manage project dependencies.

To set up the project with Poetry:

1. Install Poetry by following the instructions on the [official website](https://python-poetry.org/docs/#installation).
2. Run `poetry install` to install project dependencies.

### Jurigged for Live Reload

We use [Jurigged](https://github.com/breuleux/jurigged) for live code reloading during development. This allows you to
see changes in your code immediately without manually restarting the application.

To use Jurigged:

1. Make sure you have installed the project dependencies using Poetry, including dev
   dependencies `poetry install --with dev`.
2. Run the bot with Jurigged:

```bash
poetry run jurigged -v -m src
```

## Internationalization (i18n)

- We use [Plate](https://github.com/delivrance/plate) library to translate the bot's messages.
- Translations are stored as JSON files in the `src/i18n/locales` directory, the default locale is `en_US`.
- To add a new language, create a new JSON file in the `src/i18n/locales` directory, with the corresponding language
  code,
  translate the messages to that language.
