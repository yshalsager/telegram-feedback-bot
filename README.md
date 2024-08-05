# Telegram Feedback Bots Builder

A bot that builds feedback Telegram bot like Livegram but with topics support.

## Features

### Builder

- Create new feedback bots.
- Manage existing bots.
    - Delete bot.
    - Change its token.
    - Change its group.
    - Change bot messages (start, receive feedback, sent message feedback).
- Admin options:
    - Broadcast messages to all users.
    - Restart all bots.
    - Enable or disable bots (via @bot manage).
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

## Running

### Docker

- `docker compose up`

### Poetry

- `poetry install`
- `python3 -m src`

## Usage

### Builder

- `/start`: sends the main menu to create and manage bots.
- `@bot manage`: list bots to enable or disable.
- `/broadcast`: sends a message to all bot users. Send as a reply to a message previously sent to the bot.
- `/restart`: restarts the bot.

### Bots

- `/start`: says hello.
- Send a message, it will be forwarded to the bot owner or group.
- Owner can reply to the message and it will be forwarded to the user.
- `/broadcast`: sends a message to all bot users. Send as a reply to a message previously sent to the bot.
- `/stats`: shows bot statistics.
