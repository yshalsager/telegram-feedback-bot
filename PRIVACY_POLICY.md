# Privacy Policy

_Last updated: 2025-10-24_

## Overview

Telegram Feedback Bots Builder is an open-source project you self-host to provision and manage Telegram feedback bots. This document explains what information the software stores when you run it, why it is stored, and how it is used.

## Data Stored by the Software

### Builder Users

- Telegram user ID, username, preferred language
- Flags indicating whitelist and admin status
- Record creation and update timestamps

### Managed Bots

- Telegram bot ID, bot username, friendly name
- Encrypted bot token (stored with Fernet encryption)
- Generated bot UUID used for webhook URLs
- Configurable start/feedback message templates
- Communication mode settings (standard, private, or anonymous) that determine what user details are shown to moderators when forwarding
- Anti-flood settings (toggle state and cooldown duration in seconds)
- Media type flags for accepting/rejecting photos, videos, voice messages, documents, and stickers
- Forwarding destination (owner chat or linked group)
- Enabled/disabled status and timestamps

### Feedback Chats & Message Mappings

- Per-user chat records: Telegram ID, username, forum topic/thread ID when a group is linked
- Chat metadata timestamps (created/updated) and rate-limit markers (last message time, last warning time)
- Message mappings: IDs of user messages and their forwarded/replied counterparts so responses reach the right recipient

### Usage Statistics

- Per-bot counters for incoming and outgoing messages

### Banned Users

- Telegram ID of banned users
- Optional reason text and timestamps

### Broadcast Logs

- Target chat ID and message ID for each broadcast copy (both builder-wide and per bot)

### System Logs & Operational Files

- Application logs (for example, `telegram_feedback_bot.log`) capturing events, warnings, and errors
- Optional restart metadata (for example, `restart.json`) to resume pending restarts

> **Note:** No plain-text bot tokens or message content are stored beyond the IDs required for routing.

## Why the Data Is Stored

- **Provisioning:** Supports bot onboarding, token rotation, and owner management.
- **Routing:** Message mappings are required to forward conversations and relay replies accurately.
- **Moderation:** Banned-user lists and broadcast history enable operators to manage abuse and announcements.
- **Operations:** Logs and stats assist with monitoring, debugging, and capacity planning.

## Retention

- Records remain until you delete them via the UI/commands or purge the database manually.
- Message mappings are removed when you delete the conversation or use the `/delete` command.
- Log retention follows your deployment configuration; remove log files if you do not need the audit trail.

## Protection Measures

- Bot tokens are encrypted before storage and require the configured encryption key to decrypt.
- Database files reside on your infrastructure. Restrict OS-level access and secure container/VM boundaries.
- Webhook secrets are derived from bot UUIDs and held only in memory when registering webhooks.

## Third Parties

- Telegram delivers updates to your deployment via webhooks; Telegram’s own policies apply to traffic on their platform.
- No additional third-party services are integrated by default. If you add analytics or monitoring, update this policy accordingly.

## Responsibilities

Because the project is self-hosted, you control the environment. You are responsible for:

- Securing servers, databases, and secrets (for example, `.env` files)
- Informing users of your deployment about data handling in accordance with local regulations
- Honouring any applicable data deletion or export requests
