"""Tests for builder filters and whitelist decorator."""

import datetime as dt
from unittest.mock import AsyncMock, Mock

import pytest
from feedback_bot.telegram.builder import filters
from tests.feedback_bot.telegram.factories import build_message, build_update, build_user

from telegram import MessageOriginHiddenUser, MessageOriginUser
from telegram.ext import CallbackContext


@pytest.fixture(autouse=True)
def builder_admin(settings):
    settings.TELEGRAM_BUILDER_BOT_ADMINS = {111}
    return settings


@pytest.mark.ptb
@pytest.mark.asyncio
async def test_is_whitelisted_user_accepts_admin(monkeypatch):
    monkeypatch.setattr(filters, 'get_whitelist_users', AsyncMock(return_value=set()))
    assert await filters.is_whitelisted_user(build_message(111))


@pytest.mark.ptb
@pytest.mark.asyncio
async def test_is_whitelisted_user_checks_db(monkeypatch):
    monkeypatch.setattr(filters, 'get_whitelist_users', AsyncMock(return_value={222}))
    assert await filters.is_whitelisted_user(build_message(222))


@pytest.mark.ptb
@pytest.mark.asyncio
async def test_whitelisted_only_blocks_unknown(monkeypatch):
    monkeypatch.setattr(filters, 'get_whitelist_users', AsyncMock(return_value=set()))
    update = build_update(build_message(999))
    context = CallbackContext(application=Mock())

    called = False

    @filters.whitelisted_only
    async def handler(_update, _context):
        nonlocal called
        called = True

    assert await handler(update, context) is None
    assert not called


@pytest.mark.ptb
@pytest.mark.asyncio
async def test_whitelisted_only_allows_known(monkeypatch):
    monkeypatch.setattr(filters, 'get_whitelist_users', AsyncMock(return_value={222}))
    update = build_update(build_message(222))
    context = CallbackContext(application=Mock())

    @filters.whitelisted_only
    async def handler(_update, _context):
        return 'ok'

    assert await handler(update, context) == 'ok'


def test_is_admin_filter_allows_admin():
    assert filters.is_admin.filter(build_message(111))


def test_is_admin_filter_blocks_non_admin():
    assert not filters.is_admin.filter(build_message(222))


def test_is_reply_to_forwarded_message_accepts_visible_user():
    forwarder = build_message(
        444,
        forward_origin=MessageOriginUser(
            dt.datetime(2025, 1, 1, tzinfo=dt.UTC),
            sender_user=build_user(222, first_name='Origin'),
        ),
    )
    message = build_message(333, reply_to=forwarder)
    assert filters.is_reply_to_forwarded_message.filter(message)


def test_is_reply_to_forwarded_message_accepts_hidden_user():
    forwarder = build_message(
        444,
        forward_origin=MessageOriginHiddenUser(
            dt.datetime(2025, 1, 1, tzinfo=dt.UTC),
            sender_user_name='Anonymous',
        ),
    )
    message = build_message(333, reply_to=forwarder)
    assert filters.is_reply_to_forwarded_message.filter(message)


def test_is_reply_to_forwarded_message_rejects_plain_reply():
    plain_reply = build_message(333, reply_to=build_message(444))
    assert not filters.is_reply_to_forwarded_message.filter(plain_reply)
