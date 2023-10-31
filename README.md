# Telegram Feedback Bot

A livegram Telegram bot clone with topics support.

## Setup

## Configuration

Copy example.env to .env `cp example.env .env` and edit the following variables:

- `TELEGRAM_BOT_TOKEN`: the Telegram bot token https://telegram.me/BotFather
- `TELEGRAM_BOT_ADMINS`: the Telegram account IDs that will have administrator permissions of the bot
- `TELEGRAM_CHAT_ID`: the Telegram chat ID that will be used as forum.
- `MESSAGE_START`: the message that will be sent to users when they start the bot, can be empty to use the default
  message.
- `MESSAGE_RECEIVED`: the message that will be sent to users when they send a message to the bot, can be empty to
  use the default message.
- `DEBUG`: set to `1` to enable debug logging

## Running

### Docker

- `docker compose up`

### Poetry

- `poetry install`
- `python3 -m src`

## Bot commands

- `/start`, `/help` - sends the main menu

### Admin commands

- `/broadcast` - sends a message to all bot users and groups. Send as a reply to a message previously sent to the bot.
- `/restart` - restarts the bot.
