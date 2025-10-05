"""Async CRUD helper tests for users and bots."""

from __future__ import annotations

import pytest
from feedback_bot import crud
from feedback_bot.models import Bot, User


@pytest.fixture(autouse=True)
def configure_settings(settings):
    settings.TELEGRAM_LANGUAGES = ['en']
    settings.TELEGRAM_BUILDER_BOT_ADMINS = {111}
    settings.TELEGRAM_NEW_BOT_ADMIN_APPROVAL = False
    return settings


@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_upsert_user_creates_user():
    user_data = {'id': 111, 'username': 'Alice'}

    user, created = await crud.upsert_user(user_data)

    assert created is True
    assert user.telegram_id == 111
    assert user.username == 'Alice'
    assert user.is_admin is True
    assert user.is_whitelisted is True


@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_upsert_user_updates_existing_user():
    await crud.upsert_user({'id': 222, 'username': 'Initial', 'is_whitelisted': True})

    _, created = await crud.upsert_user(
        {'id': 222, 'username': ' Updated ', 'is_whitelisted': False}
    )

    assert created is False
    updated = await User.objects.aget(telegram_id=222)
    assert updated.username == 'Updated'
    assert updated.is_whitelisted is False


@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_user_details_modifies_fields():
    await crud.upsert_user({'id': 333, 'username': 'OldName'})

    updated = await crud.update_user_details(333, {'username': 'NewName', 'language_code': 'ar'})

    assert updated is not None
    assert updated.username == 'NewName'
    assert updated.language_code == 'ar'


@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_user_details_returns_none_when_missing():
    result = await crud.update_user_details(999, {'username': 'Ghost'})

    assert result is None


@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_get_whitelist_users_filters_only_whitelisted():
    await crud.upsert_user({'id': 444, 'is_whitelisted': True})
    await crud.upsert_user({'id': 555, 'is_whitelisted': False})

    whitelist = await crud.get_whitelist_users()

    assert whitelist == [444]


@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_create_bot_persists_and_returns_decrypted_token():
    owner, _ = await crud.upsert_user({'id': 666, 'username': 'owner'})

    bot = await crud.create_bot(
        telegram_id=999999,
        bot_token='TEST_TOKEN',  # noqa: S106
        username='test_bot',
        name='Test Bot',
        owner=owner.telegram_id,
        enable_confirmations=True,
        start_message='hi',
        feedback_received_message='thanks',
    )

    assert isinstance(bot, Bot)
    assert bot.owner_id == owner.telegram_id
    assert bot.token == 'TEST_TOKEN'  # noqa: S105

    keys = await crud.get_bots_keys()
    assert [(str(uuid), token) for uuid, token in keys] == [(str(bot.uuid), 'TEST_TOKEN')]


@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_delete_bot_removes_entry():
    owner, _ = await crud.upsert_user({'id': 777})
    bot = await crud.create_bot(
        telegram_id=111111,
        bot_token='DEL_TOKEN',  # noqa: S106
        username='delete_bot',
        name='Delete Bot',
        owner=owner.telegram_id,
        enable_confirmations=False,
        start_message='start',
        feedback_received_message='received',
    )

    deleted = await crud.delete_bot(bot.uuid, owner.telegram_id)
    assert deleted is True
    assert await crud.get_bot(bot.uuid, owner.telegram_id) is None


@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_bot_exists_checks_presence():
    owner, _ = await crud.upsert_user({'id': 888})
    await crud.create_bot(
        telegram_id=222222,
        bot_token='BOT_TOKEN',  # noqa: S106
        username='exists_bot',
        name='Exists Bot',
        owner=owner.telegram_id,
        enable_confirmations=False,
        start_message='start',
        feedback_received_message='received',
    )

    assert await crud.bot_exists(222222) is True
    assert await crud.bot_exists(333333) is False
