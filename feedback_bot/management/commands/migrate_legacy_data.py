"""Migrate data from the legacy builder/bot SQLite databases into Django models."""

from __future__ import annotations

import base64
import json
import os
import sqlite3
from collections.abc import Iterable
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from feedback_bot.models import Bot, BotStats, FeedbackChat, MessageMapping, User


@lru_cache
def _legacy_key() -> bytes:
    key = os.getenv('ENCRYPTION_KEY')
    if not key:
        raise CommandError('ENCRYPTION_KEY environment variable is required for migration')
    return key.encode()


def decrypt_legacy_token(token: str) -> str:
    token_bytes = base64.b64decode(token)
    key_bytes = _legacy_key()
    decrypted = bytes(
        byte ^ key_bytes[index % len(key_bytes)] for index, byte in enumerate(token_bytes)
    )
    return decrypted.decode()


class Command(BaseCommand):
    help = 'Import data from the legacy builder/bot SQLite databases into Django models.'

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            '--builder-db',
            default='feedback_bot.db',
            help='Path to the legacy builder database (default: BASE_DIR/feedback_bot.db)',
        )
        parser.add_argument(
            '--data-dir',
            default='data',
            help='Directory with per-bot databases (default: BASE_DIR/data)',
        )

    def handle(self, *args, **options) -> None:
        base_dir = settings.BASE_DIR
        builder_db = self._resolve_path(base_dir, options['builder_db'])
        data_dir = self._resolve_path(base_dir, options['data_dir'])

        if not builder_db.exists():
            raise CommandError(f'Legacy builder database not found at {builder_db}')
        if not data_dir.exists():
            raise CommandError(f'Legacy data directory not found at {data_dir}')

        with sqlite3.connect(builder_db) as builder_conn:
            builder_conn.row_factory = sqlite3.Row
            users_rows = self._fetch_rows(
                builder_conn, 'SELECT user_id, user_name, language FROM users'
            )
            whitelist_ids = {
                int(row['user_id'])
                for row in self._fetch_rows(builder_conn, 'SELECT user_id FROM whitelist')
            }
            bots_rows = self._fetch_rows(
                builder_conn,
                'SELECT id, username, name, user_id, token, owner, "group", enabled, settings '
                'FROM bots',
            )

        users_map = self._migrate_users(users_rows, whitelist_ids)
        bots_map = self._migrate_bots(bots_rows, users_map)

        migrated_chats = migrated_mappings = migrated_stats = 0
        for legacy_bot_id, bot in bots_map.items():
            db_path = data_dir / f'{legacy_bot_id}.db'
            if not db_path.exists():
                self.stdout.write(
                    self.style.WARNING(f'Skipping bot {legacy_bot_id}: missing {db_path.name}')
                )
                continue
            chats_count, mappings_count, stats_count = self._migrate_bot_data(bot, db_path)
            migrated_chats += chats_count
            migrated_mappings += mappings_count
            migrated_stats += stats_count

        self.stdout.write(
            self.style.SUCCESS(
                'Migration complete: '
                f'{len(users_map)} users, {len(bots_map)} bots, '
                f'{migrated_chats} chats, {migrated_mappings} mappings, {migrated_stats} stats entries'
            )
        )

    def _resolve_path(self, base_dir: Path, raw_path: str) -> Path:
        path = Path(raw_path)
        return path if path.is_absolute() else base_dir / path

    def _fetch_rows(self, conn: sqlite3.Connection, query: str) -> list[sqlite3.Row]:
        cursor = conn.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def _migrate_users(
        self, rows: Iterable[sqlite3.Row], whitelist_ids: set[int]
    ) -> dict[int, User]:
        users: dict[int, User] = {}
        admin_ids = set(settings.TELEGRAM_BUILDER_BOT_ADMINS)

        with transaction.atomic():
            for row in rows:
                telegram_id = int(row['user_id'])
                username = (row['user_name'] or '').strip()
                language = (row['language'] or 'en').strip() or 'en'
                defaults = {
                    'username': username or None,
                    'language_code': language,
                    'is_whitelisted': telegram_id in whitelist_ids,
                    'is_admin': telegram_id in admin_ids,
                }
                user, _ = User.objects.update_or_create(
                    telegram_id=telegram_id,
                    defaults=defaults,
                )
                users[telegram_id] = user

            missing_whitelist = whitelist_ids - users.keys()
            for telegram_id in missing_whitelist:
                defaults = {
                    'username': None,
                    'language_code': 'en',
                    'is_whitelisted': True,
                    'is_admin': telegram_id in admin_ids,
                }
                user, _ = User.objects.update_or_create(
                    telegram_id=telegram_id,
                    defaults=defaults,
                )
                users[telegram_id] = user

        return users

    def _parse_settings(self, payload: str | None) -> dict[str, object]:
        if not payload:
            return {}
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return {}

    def _migrate_bots(self, rows: Iterable[sqlite3.Row], users: dict[int, User]) -> dict[int, Bot]:
        bots: dict[int, Bot] = {}
        start_default = Bot._meta.get_field('start_message').default
        received_default = Bot._meta.get_field('feedback_received_message').default

        with transaction.atomic():
            for row in rows:
                telegram_id = int(row['user_id'])
                owner_id = int(row['owner'])
                owner = users.get(owner_id)
                if owner is None:
                    owner, _ = User.objects.update_or_create(
                        telegram_id=owner_id,
                        defaults={
                            'username': None,
                            'language_code': 'en',
                            'is_whitelisted': False,
                            'is_admin': owner_id in settings.TELEGRAM_BUILDER_BOT_ADMINS,
                        },
                    )
                    users[owner_id] = owner

                settings_payload = self._parse_settings(row['settings'])
                start_message = (settings_payload.get('start_message') or start_default)[:4096]
                received_message = (settings_payload.get('received_message') or received_default)[
                    :4096
                ]

                bot, _ = Bot.objects.get_or_create(
                    telegram_id=telegram_id, defaults={'owner': owner}
                )
                bot.owner = owner
                bot.name = row['name']
                bot.username = row['username']
                forward_chat_id = row['group']
                if forward_chat_id in (None, 0, '0'):
                    bot.forward_chat_id = None
                else:
                    bot.forward_chat_id = int(forward_chat_id)
                bot.enabled = bool(row['enabled'])
                bot.start_message = start_message
                bot.feedback_received_message = received_message
                bot.token = decrypt_legacy_token(row['token'])
                bot.save()
                bots[telegram_id] = bot

        return bots

    def _migrate_bot_data(self, bot: Bot, db_path: Path) -> tuple[int, int, int]:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            chats_rows = self._fetch_rows(conn, 'SELECT user_id, user_name, type FROM chats')
            topics_rows = self._fetch_rows(conn, 'SELECT user_id, topic_id FROM topics')
            mappings_rows = self._fetch_rows(
                conn,
                'SELECT id, user_id, source, destination FROM mappings WHERE outgoing = 0 ORDER BY id',
            )
            stats_rows = self._fetch_rows(conn, 'SELECT incoming, outgoing FROM stats')

        topic_index: dict[int, int | None] = {}
        for row in topics_rows:
            user_id = int(row['user_id'])
            raw_topic = row['topic_id']
            if raw_topic in (None, 0, '0'):
                topic_index[user_id] = None
            else:
                topic_index[user_id] = int(raw_topic)

        with transaction.atomic():
            MessageMapping.objects.filter(bot=bot).delete()
            FeedbackChat.objects.filter(bot=bot).delete()
            BotStats.objects.filter(bot=bot).delete()

            chat_objects: dict[int, FeedbackChat] = {}
            for row in chats_rows:
                if int(row['type']) != 0:
                    continue
                user_id = int(row['user_id'])
                if user_id in chat_objects:
                    continue
                username = (row['user_name'] or '').strip() or None
                topic_value = topic_index.get(user_id)
                chat_objects[user_id] = FeedbackChat.objects.create(
                    bot=bot,
                    user_telegram_id=user_id,
                    username=username,
                    topic_id=topic_value,
                )

            chats_migrated = len(chat_objects)
            seen_sources: set[int] = set()
            mappings_migrated = 0

            for row in mappings_rows:
                user_message_id = int(row['source'])
                if user_message_id in seen_sources:
                    continue
                seen_sources.add(user_message_id)
                user_id = int(row['user_id'])
                chat = chat_objects.get(user_id)
                if chat is None:
                    chat = FeedbackChat.objects.create(
                        bot=bot,
                        user_telegram_id=user_id,
                        username=None,
                        topic_id=topic_index.get(user_id),
                    )
                    chat_objects[user_id] = chat
                    chats_migrated += 1
                owner_message_id = int(row['destination'])
                MessageMapping.objects.create(
                    bot=bot,
                    user_chat=chat,
                    user_message_id=user_message_id,
                    owner_message_id=owner_message_id,
                )
                mappings_migrated += 1

            incoming = outgoing = 0
            if stats_rows:
                totals = stats_rows[0]
                incoming = int(totals['incoming'] or 0)
                outgoing = int(totals['outgoing'] or 0)
            BotStats.objects.create(
                bot=bot,
                incoming_messages=incoming,
                outgoing_messages=outgoing,
            )
            stats_migrated = 1

        return chats_migrated, mappings_migrated, stats_migrated
