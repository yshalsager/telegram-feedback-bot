"""API tests for miniapp bot endpoints."""

import os
from uuid import UUID, uuid4

import pytest
from feedback_bot import crud
from feedback_bot.telegram.utils.cryptography import generate_bot_webhook_secret
from telegram import Update

BOT_TOKEN = '12345678:abcdefghijklmnopqrstuvwxyzABCD12345'  # noqa: S105
NEW_BOT_TOKEN = '23456789:bcdefghijklmnopqrstuvwxyzABCDE12345'  # noqa: S105
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'


@pytest.mark.api
@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_add_bot_creates_record(miniapp_client, monkeypatch):
    client, auth_state, headers = miniapp_client
    await crud.upsert_user(
        {
            'id': auth_state['user']['id'],
            'username': 'owner',
            'language_code': 'en',
            'is_whitelisted': True,
            'is_admin': True,
        }
    )

    async def fake_validate_bot_token(token: str) -> dict[str, str | int]:
        assert token == BOT_TOKEN
        return {
            'name': 'Sample Bot',
            'telegram_id': 123456789,
            'username': 'sample_bot',
        }

    monkeypatch.setattr(
        'feedback_bot.api.miniapp.bots.validate_bot_token',
        fake_validate_bot_token,
        raising=False,
    )

    payload = {
        'bot_token': BOT_TOKEN,
        'enable_confirmations': True,
        'start_message': 'Hello there!',
        'feedback_received_message': 'Thanks!',
    }

    response = await client.post('/bot/', headers=headers, json=payload)

    assert response.status_code == 200, response.json()
    body = response.json()
    assert body['status'] == 'success'
    assert body['bot']['username'] == 'sample_bot'
    assert await crud.bot_exists(123456789) is True


@pytest.mark.api
@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_add_bot_rejects_duplicate_token(miniapp_client, monkeypatch):
    client, auth_state, headers = miniapp_client
    await crud.upsert_user(
        {
            'id': auth_state['user']['id'],
            'username': 'owner',
            'language_code': 'en',
            'is_whitelisted': True,
            'is_admin': True,
        }
    )

    async def fake_validate(token: str) -> dict[str, str | int]:
        return {
            'name': 'Existing Bot',
            'telegram_id': 999888777,
            'username': 'existing_bot',
        }

    monkeypatch.setattr(
        'feedback_bot.api.miniapp.bots.validate_bot_token',
        fake_validate,
        raising=False,
    )

    payload = {
        'bot_token': BOT_TOKEN,
        'enable_confirmations': True,
        'start_message': 'Hello',
        'feedback_received_message': 'Thanks',
    }

    first_response = await client.post('/bot/', headers=headers, json=payload)
    assert first_response.status_code == 200

    duplicate_response = await client.post('/bot/', headers=headers, json=payload)

    assert duplicate_response.status_code == 400
    body = duplicate_response.json()
    assert body['status'] == 'error'
    assert 'exists' in body['message']


@pytest.mark.api
@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_list_and_update_bot(miniapp_client, monkeypatch):
    client, auth_state, headers = miniapp_client
    await crud.upsert_user(
        {
            'id': auth_state['user']['id'],
            'username': 'owner',
            'is_whitelisted': True,
            'is_admin': True,
        }
    )

    async def fake_validate(_: str) -> dict[str, str | int]:
        return {
            'name': 'Another Bot',
            'telegram_id': 987654321,
            'username': 'another_bot',
        }

    monkeypatch.setattr(
        'feedback_bot.api.miniapp.bots.validate_bot_token',
        fake_validate,
        raising=False,
    )

    await client.post(
        '/bot/',
        headers=headers,
        json={
            'bot_token': BOT_TOKEN,
            'enable_confirmations': True,
            'start_message': 'start',
            'feedback_received_message': 'received',
        },
    )

    bots_response = await client.get('/bot/', headers=headers)
    assert bots_response.status_code == 200
    bots_payload = bots_response.json()
    assert any(bot['username'] == 'another_bot' for bot in bots_payload)

    uuid_str = next(bot['uuid'] for bot in bots_payload if bot['username'] == 'another_bot')

    update_response = await client.put(
        f'/bot/{uuid_str}/',
        headers=headers,
        json={'start_message': 'updated text'},
    )

    assert update_response.status_code == 200
    updated_payload = update_response.json()
    assert updated_payload['start_message'] == 'updated text'

    updated = await crud.get_bot(UUID(uuid_str), auth_state['user']['id'])
    assert updated is not None
    assert updated.start_message == 'updated text'


@pytest.mark.api
@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_bot_disabling_removes_webhook(miniapp_client, monkeypatch, settings):
    client, auth_state, headers = miniapp_client
    settings.TELEGRAM_NEW_BOT_ADMIN_APPROVAL = False
    settings.TELEGRAM_BUILDER_BOT_WEBHOOK_URL = 'https://example.com'
    await crud.upsert_user(
        {
            'id': auth_state['user']['id'],
            'username': 'owner',
            'is_whitelisted': True,
            'is_admin': True,
        }
    )

    operations: list[tuple[str, object, object, object]] = []

    async def fake_delete_webhook(self, *args, **kwargs):
        assert self.token == BOT_TOKEN
        operations.append(('delete', None, None, None))

    monkeypatch.setattr('telegram.Bot.delete_webhook', fake_delete_webhook)

    await crud.create_bot(
        telegram_id=123456789,
        bot_token=BOT_TOKEN,
        username='toggle_bot',
        name='Toggle Bot',
        owner=auth_state['user']['id'],
        enable_confirmations=True,
        start_message='start',
        feedback_received_message='received',
    )

    stored_bot = (await crud.get_bots(auth_state['user']['id']))[0]

    disable_response = await client.put(
        f'/bot/{stored_bot.uuid}/',
        headers=headers,
        json={'enabled': False},
    )

    assert disable_response.status_code == 200, disable_response.json()
    assert operations == [('delete', None, None, None)]
    disabled = await crud.get_bot(stored_bot.uuid, auth_state['user']['id'])
    assert disabled is not None
    assert disabled.enabled is False


@pytest.mark.api
@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_bot_enabling_sets_webhook(miniapp_client, monkeypatch, settings):
    client, auth_state, headers = miniapp_client
    settings.TELEGRAM_NEW_BOT_ADMIN_APPROVAL = False
    settings.TELEGRAM_BUILDER_BOT_WEBHOOK_URL = 'https://example.com'
    await crud.upsert_user(
        {
            'id': auth_state['user']['id'],
            'username': 'owner',
            'is_whitelisted': True,
            'is_admin': True,
        }
    )

    operations: list[tuple[str, object, object, object]] = []

    async def fake_set_webhook(
        self, webhook_url, *_, secret_token=None, allowed_updates=None, **__
    ):
        assert self.token == BOT_TOKEN
        operations.append(('set', webhook_url, secret_token, allowed_updates))

    async def fake_delete_webhook(self, *args, **kwargs):
        assert self.token == BOT_TOKEN
        operations.append(('delete', None, None, None))

    monkeypatch.setattr('telegram.Bot.set_webhook', fake_set_webhook)
    monkeypatch.setattr('telegram.Bot.delete_webhook', fake_delete_webhook)

    await crud.create_bot(
        telegram_id=333222111,
        bot_token=BOT_TOKEN,
        username='toggle_bot',
        name='Toggle Bot',
        owner=auth_state['user']['id'],
        enable_confirmations=True,
        start_message='start',
        feedback_received_message='received',
    )

    stored_bot = (await crud.get_bots(auth_state['user']['id']))[0]
    await crud.update_bot_settings(stored_bot.uuid, auth_state['user']['id'], {'enabled': False})
    operations.clear()

    enable_response = await client.put(
        f'/bot/{stored_bot.uuid}/',
        headers=headers,
        json={'enabled': True},
    )

    assert enable_response.status_code == 200, enable_response.json()
    assert operations
    action, url, secret, allowed = operations[0]
    assert action == 'set'
    expected_url = f'{settings.TELEGRAM_BUILDER_BOT_WEBHOOK_URL}/api/webhook/{stored_bot.uuid}/'
    assert url == expected_url
    assert secret == generate_bot_webhook_secret(str(stored_bot.uuid))
    assert allowed is not None
    enabled = await crud.get_bot(stored_bot.uuid, auth_state['user']['id'])
    assert enabled is not None
    assert enabled.enabled is True


@pytest.mark.api
@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_bot_enabling_rolls_back_on_webhook_failure(
    miniapp_client, monkeypatch, settings
):
    client, auth_state, headers = miniapp_client
    settings.TELEGRAM_NEW_BOT_ADMIN_APPROVAL = False
    settings.TELEGRAM_BUILDER_BOT_WEBHOOK_URL = 'https://example.com'
    await crud.upsert_user(
        {
            'id': auth_state['user']['id'],
            'username': 'admin_user',
            'is_whitelisted': True,
            'is_admin': True,
        }
    )

    async def fake_set_webhook(self, *args, **kwargs):
        assert self.token == BOT_TOKEN
        raise RuntimeError('webhook failed')

    monkeypatch.setattr('telegram.Bot.set_webhook', fake_set_webhook)

    bot = await crud.create_bot(
        telegram_id=555444333,
        bot_token=BOT_TOKEN,
        username='failing_bot',
        name='Failing Bot',
        owner=auth_state['user']['id'],
        enable_confirmations=True,
        start_message='start',
        feedback_received_message='received',
    )
    await crud.update_bot_settings(bot.uuid, auth_state['user']['id'], {'enabled': False})

    response = await client.put(
        f'/bot/{bot.uuid}/',
        headers=headers,
        json={'enabled': True},
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload['status'] == 'error'
    assert 'webhook' in payload['message']

    stored = await crud.get_bot(bot.uuid, auth_state['user']['id'])
    assert stored is not None
    assert stored.enabled is False


@pytest.mark.api
@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_bot_enable_requires_admin_when_approval_enabled(miniapp_client, settings):
    client, auth_state, headers = miniapp_client
    auth_state['user']['is_admin'] = False
    settings.TELEGRAM_NEW_BOT_ADMIN_APPROVAL = True

    await crud.upsert_user(
        {
            'id': auth_state['user']['id'],
            'username': 'owner',
            'is_whitelisted': True,
            'is_admin': False,
        }
    )

    bot = await crud.create_bot(
        telegram_id=111222333,
        bot_token=BOT_TOKEN,
        username='approval_bot',
        name='Approval Bot',
        owner=auth_state['user']['id'],
        enable_confirmations=True,
        start_message='start',
        feedback_received_message='received',
    )

    response = await client.put(
        f'/bot/{bot.uuid}/',
        headers=headers,
        json={'enabled': True},
    )

    assert response.status_code == 403
    payload = response.json()
    assert payload['status'] == 'error'
    assert 'approval' in payload['message'].lower()

    stored = await crud.get_bot(bot.uuid, auth_state['user']['id'])
    assert stored is not None
    assert stored.enabled is False


@pytest.mark.api
@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_bot_token_rotates_successfully(miniapp_client, monkeypatch, settings):
    client, auth_state, headers = miniapp_client
    settings.TELEGRAM_NEW_BOT_ADMIN_APPROVAL = False
    settings.TELEGRAM_BUILDER_BOT_WEBHOOK_URL = 'https://builder.example'

    await crud.upsert_user(
        {
            'id': auth_state['user']['id'],
            'username': 'owner',
            'is_whitelisted': True,
            'is_admin': True,
        }
    )

    bot = await crud.create_bot(
        telegram_id=222111000,
        bot_token=BOT_TOKEN,
        username='rotate_bot',
        name='Rotate Bot',
        owner=auth_state['user']['id'],
        enable_confirmations=True,
        start_message='hello',
        feedback_received_message='thanks',
    )

    async def fake_validate(token: str) -> dict[str, str | int]:
        assert token == NEW_BOT_TOKEN
        return {
            'name': 'Rotated Bot',
            'telegram_id': bot.telegram_id,
            'username': 'rotated_bot',
        }

    async def fake_set_webhook(self, url, *, secret_token=None, allowed_updates=None):
        assert self.token == NEW_BOT_TOKEN
        assert url == f'https://builder.example/api/webhook/{bot.uuid}/'
        assert secret_token == generate_bot_webhook_secret(str(bot.uuid))
        assert allowed_updates == Update.ALL_TYPES

    monkeypatch.setattr(
        'feedback_bot.api.miniapp.bots.validate_bot_token',
        fake_validate,
        raising=False,
    )
    monkeypatch.setattr('telegram.Bot.set_webhook', fake_set_webhook)

    response = await client.put(
        f'/bot/{bot.uuid}/',
        headers=headers,
        json={'bot_token': NEW_BOT_TOKEN},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['name'] == 'Rotated Bot'
    assert payload['username'] == 'rotated_bot'

    stored_token = await crud.get_bot_token(bot.uuid, auth_state['user']['id'])
    assert stored_token == NEW_BOT_TOKEN


@pytest.mark.api
@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_bot_token_rejects_mismatch(miniapp_client, monkeypatch):
    client, auth_state, headers = miniapp_client

    await crud.upsert_user(
        {
            'id': auth_state['user']['id'],
            'username': 'owner',
            'is_whitelisted': True,
            'is_admin': True,
        }
    )

    bot = await crud.create_bot(
        telegram_id=321654987,
        bot_token=BOT_TOKEN,
        username='mismatch_bot',
        name='Mismatch Bot',
        owner=auth_state['user']['id'],
        enable_confirmations=True,
        start_message='start',
        feedback_received_message='received',
    )

    async def fake_validate(_: str) -> dict[str, str | int]:
        return {
            'name': 'Wrong Bot',
            'telegram_id': bot.telegram_id + 1,
            'username': 'wrong_bot',
        }

    monkeypatch.setattr(
        'feedback_bot.api.miniapp.bots.validate_bot_token',
        fake_validate,
        raising=False,
    )

    response = await client.put(
        f'/bot/{bot.uuid}/',
        headers=headers,
        json={'bot_token': NEW_BOT_TOKEN},
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload['status'] == 'error'
    assert payload['message'] == 'Token belongs to a different bot.'

    stored_token = await crud.get_bot_token(bot.uuid, auth_state['user']['id'])
    assert stored_token == BOT_TOKEN


@pytest.mark.api
@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_bot_token_rejects_builder_token(miniapp_client, monkeypatch, settings):
    client, auth_state, headers = miniapp_client
    builder_token = '34567890:CDEFGHIJKLMNOPQRSTUVWXYZabcde12345'  # noqa: S105
    settings.TELEGRAM_BUILDER_BOT_TOKEN = builder_token

    await crud.upsert_user(
        {
            'id': auth_state['user']['id'],
            'username': 'owner',
            'is_whitelisted': True,
            'is_admin': True,
        }
    )

    bot = await crud.create_bot(
        telegram_id=456987123,
        bot_token=BOT_TOKEN,
        username='builder_block',
        name='Builder Block',
        owner=auth_state['user']['id'],
        enable_confirmations=True,
        start_message='start',
        feedback_received_message='received',
    )

    def fail_validator(_: str) -> dict[str, str | int]:  # pragma: no cover - should not run
        raise AssertionError('validate_bot_token must not be called')

    monkeypatch.setattr(
        'feedback_bot.api.miniapp.bots.validate_bot_token',
        fail_validator,
        raising=False,
    )

    response = await client.put(
        f'/bot/{bot.uuid}/',
        headers=headers,
        json={'bot_token': builder_token},
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload['status'] == 'error'
    assert payload['message'] == 'You cannot use the builder bot token.'

    stored_token = await crud.get_bot_token(bot.uuid, auth_state['user']['id'])
    assert stored_token == BOT_TOKEN


@pytest.mark.api
@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_bot_token_rolls_back_on_webhook_failure(
    miniapp_client, monkeypatch, settings
):
    client, auth_state, headers = miniapp_client
    settings.TELEGRAM_NEW_BOT_ADMIN_APPROVAL = False
    settings.TELEGRAM_BUILDER_BOT_WEBHOOK_URL = 'https://builder.example'

    await crud.upsert_user(
        {
            'id': auth_state['user']['id'],
            'username': 'owner',
            'is_whitelisted': True,
            'is_admin': True,
        }
    )

    bot = await crud.create_bot(
        telegram_id=159357258,
        bot_token=BOT_TOKEN,
        username='rollback_bot',
        name='Rollback Bot',
        owner=auth_state['user']['id'],
        enable_confirmations=True,
        start_message='start',
        feedback_received_message='received',
    )

    async def fake_validate(token: str) -> dict[str, str | int]:
        assert token == NEW_BOT_TOKEN
        return {
            'name': 'Rollback Bot',
            'telegram_id': bot.telegram_id,
            'username': 'rollback_bot',
        }

    async def fail_webhook(self, *args, **kwargs):
        raise RuntimeError('set_webhook failed')

    monkeypatch.setattr(
        'feedback_bot.api.miniapp.bots.validate_bot_token',
        fake_validate,
        raising=False,
    )
    monkeypatch.setattr('telegram.Bot.set_webhook', fail_webhook)

    response = await client.put(
        f'/bot/{bot.uuid}/',
        headers=headers,
        json={'bot_token': NEW_BOT_TOKEN},
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload['status'] == 'error'
    assert 'webhook' in payload['message']

    stored_token = await crud.get_bot_token(bot.uuid, auth_state['user']['id'])
    assert stored_token == BOT_TOKEN


@pytest.mark.api
@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_unlink_bot_forward_chat(miniapp_client, monkeypatch):
    client, auth_state, headers = miniapp_client
    await crud.upsert_user(
        {
            'id': auth_state['user']['id'],
            'username': 'owner',
            'is_whitelisted': True,
            'is_admin': True,
        }
    )

    async def fake_validate(_: str) -> dict[str, str | int]:
        return {
            'name': 'Linkable Bot',
            'telegram_id': 222333444,
            'username': 'linkable_bot',
        }

    monkeypatch.setattr(
        'feedback_bot.api.miniapp.bots.validate_bot_token',
        fake_validate,
        raising=False,
    )

    create_response = await client.post(
        '/bot/',
        headers=headers,
        json={
            'bot_token': BOT_TOKEN,
            'enable_confirmations': True,
            'start_message': 'start',
            'feedback_received_message': 'received',
        },
    )
    assert create_response.status_code == 200

    stored_bot = (await crud.get_bots(auth_state['user']['id']))[0]
    await crud.update_bot_settings(
        stored_bot.uuid, auth_state['user']['id'], {'forward_chat_id': -100001}
    )

    unlink_response = await client.delete(f'/bot/{stored_bot.uuid}/forward_chat/', headers=headers)

    assert unlink_response.status_code == 200
    payload = unlink_response.json()
    assert payload['status'] == 'success'
    assert 'bot' not in payload

    refreshed = await crud.get_bot(stored_bot.uuid, auth_state['user']['id'])
    assert refreshed is not None
    assert refreshed.forward_chat_id is None

    missing = await client.delete(f'/bot/{uuid4()}/forward_chat/', headers=headers)
    assert missing.status_code == 404


@pytest.mark.api
@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_add_bot_rejects_builder_token(miniapp_client, monkeypatch, settings):
    client, auth_state, headers = miniapp_client
    await crud.upsert_user(
        {
            'id': auth_state['user']['id'],
            'username': 'owner',
            'language_code': 'en',
            'is_whitelisted': True,
            'is_admin': True,
        }
    )

    settings.TELEGRAM_BUILDER_BOT_TOKEN = BOT_TOKEN

    async def fake_validate(token: str):  # pragma: no cover - should not be called
        raise AssertionError('validate_bot_token must not be invoked for builder token')

    monkeypatch.setattr(
        'feedback_bot.api.miniapp.bots.validate_bot_token',
        fake_validate,
        raising=False,
    )

    payload = {
        'bot_token': BOT_TOKEN,
        'enable_confirmations': True,
        'start_message': 'start',
        'feedback_received_message': 'received',
    }

    response = await client.post('/bot/', headers=headers, json=payload)

    assert response.status_code == 400
    body = response.json()
    assert body['status'] == 'error'
    assert 'builder' in body['message']


@pytest.mark.api
@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_add_bot_invalid_token_surfaces_error(miniapp_client, monkeypatch):
    client, auth_state, headers = miniapp_client
    await crud.upsert_user(
        {
            'id': auth_state['user']['id'],
            'username': 'owner',
            'language_code': 'en',
            'is_whitelisted': True,
            'is_admin': True,
        }
    )

    async def fake_validate(_: str):
        raise RuntimeError('broken token')

    monkeypatch.setattr(
        'feedback_bot.api.miniapp.bots.validate_bot_token',
        fake_validate,
        raising=False,
    )

    payload = {
        'bot_token': BOT_TOKEN,
        'enable_confirmations': True,
        'start_message': 'hello',
        'feedback_received_message': 'bye',
    }

    response = await client.post('/bot/', headers=headers, json=payload)

    assert response.status_code == 400
    body = response.json()
    assert body['status'] == 'error'
    assert 'broken token' in body['message']


@pytest.mark.api
@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_admin_can_toggle_foreign_bot(miniapp_client, monkeypatch, settings):
    client, auth_state, headers = miniapp_client
    settings.TELEGRAM_NEW_BOT_ADMIN_APPROVAL = False
    settings.TELEGRAM_BUILDER_BOT_WEBHOOK_URL = 'https://example.com'
    owner_id = 2000
    await crud.upsert_user(
        {
            'id': owner_id,
            'username': 'owner_user',
            'is_whitelisted': True,
            'is_admin': False,
        }
    )

    operations: list[tuple[str, object, object, object]] = []

    async def fake_set_webhook(
        self, webhook_url, *_, secret_token=None, allowed_updates=None, **__
    ):
        assert self.token == BOT_TOKEN
        operations.append(('set', webhook_url, secret_token, allowed_updates))

    monkeypatch.setattr('telegram.Bot.set_webhook', fake_set_webhook)

    bot = await crud.create_bot(
        telegram_id=777666555,
        bot_token=BOT_TOKEN,
        username='foreign_bot',
        name='Foreign Bot',
        owner=owner_id,
        enable_confirmations=True,
        start_message='start',
        feedback_received_message='received',
    )

    await crud.update_bot_settings(bot.uuid, owner_id, {'enabled': False})
    operations.clear()

    response = await client.put(
        f'/bot/{bot.uuid}/',
        headers=headers,
        json={'enabled': True},
    )

    assert response.status_code == 200
    assert operations
    action, url, secret, allowed = operations[0]
    assert action == 'set'
    expected_url = f'{settings.TELEGRAM_BUILDER_BOT_WEBHOOK_URL}/api/webhook/{bot.uuid}/'
    assert url == expected_url
    assert secret == generate_bot_webhook_secret(str(bot.uuid))
    assert allowed is not None
    updated = await crud.get_bot(bot.uuid, auth_state['user']['id'])
    assert updated is not None
    assert updated.enabled is True


@pytest.mark.api
@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_bot_stats_endpoint_returns_counts(miniapp_client, monkeypatch):
    client, auth_state, headers = miniapp_client
    await crud.upsert_user(
        {
            'id': auth_state['user']['id'],
            'username': 'owner',
            'is_whitelisted': True,
            'is_admin': True,
        }
    )

    async def fake_validate(_: str) -> dict[str, str | int]:
        return {
            'name': 'Stats Bot',
            'telegram_id': 313233334,
            'username': 'stats_bot',
        }

    monkeypatch.setattr(
        'feedback_bot.api.miniapp.bots.validate_bot_token',
        fake_validate,
        raising=False,
    )

    await client.post(
        '/bot/',
        headers=headers,
        json={
            'bot_token': BOT_TOKEN,
            'enable_confirmations': True,
            'start_message': 'start',
            'feedback_received_message': 'received',
        },
    )

    bots_response = await client.get('/bot/', headers=headers)
    assert bots_response.status_code == 200
    bots_payload = bots_response.json()
    uuid_str = next(bot['uuid'] for bot in bots_payload if bot['username'] == 'stats_bot')

    bot = await crud.get_bot(UUID(uuid_str), auth_state['user']['id'])
    assert bot is not None
    await crud.bump_incoming_messages(bot)
    await crud.bump_incoming_messages(bot)
    await crud.bump_outgoing_messages(bot)

    stats_response = await client.get(f'/bot/{uuid_str}/stats/', headers=headers)
    assert stats_response.status_code == 200
    stats_payload = stats_response.json()
    assert stats_payload['incoming_messages'] == 2
    assert stats_payload['outgoing_messages'] == 1


@pytest.mark.api
@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_banned_users_management(miniapp_client, monkeypatch):
    client, auth_state, headers = miniapp_client

    await crud.upsert_user(
        {
            'id': auth_state['user']['id'],
            'username': 'owner',
            'is_whitelisted': True,
            'is_admin': True,
        }
    )

    async def fake_validate(_: str) -> dict[str, str | int]:
        return {
            'name': 'Ban-able Bot',
            'telegram_id': 515151,
            'username': 'ban_bot',
        }

    monkeypatch.setattr(
        'feedback_bot.api.miniapp.bots.validate_bot_token',
        fake_validate,
        raising=False,
    )

    create_response = await client.post(
        '/bot/',
        headers=headers,
        json={
            'bot_token': BOT_TOKEN,
            'enable_confirmations': True,
            'start_message': 'start',
            'feedback_received_message': 'received',
        },
    )
    assert create_response.status_code == 200

    stored_bot = (await crud.get_bots(auth_state['user']['id']))[0]

    ban_response = await client.post(
        f'/bot/{stored_bot.uuid}/banned_users/',
        headers=headers,
        json={'user_telegram_id': 4242, 'reason': 'spam reports'},
    )
    assert ban_response.status_code == 200
    ban_payload = ban_response.json()
    assert ban_payload['status'] == 'success'
    assert ban_payload['user_telegram_id'] == 4242
    assert ban_payload['created'] is True
    assert ban_payload['reason'] == 'spam reports'

    duplicate_ban = await client.post(
        f'/bot/{stored_bot.uuid}/banned_users/',
        headers=headers,
        json={'user_telegram_id': 4242, 'reason': 'multiple spam submissions'},
    )
    assert duplicate_ban.status_code == 200
    duplicate_payload = duplicate_ban.json()
    assert duplicate_payload['created'] is False
    assert duplicate_payload['reason'] == 'multiple spam submissions'

    list_response = await client.get(
        f'/bot/{stored_bot.uuid}/banned_users/',
        headers=headers,
    )
    assert list_response.status_code == 200
    bans_payload = list_response.json()
    assert len(bans_payload) == 1
    entry = bans_payload[0]
    assert entry['user_telegram_id'] == 4242
    assert 'created_at' in entry
    assert entry.get('reason') == 'multiple spam submissions'

    unban_response = await client.delete(
        f'/bot/{stored_bot.uuid}/banned_users/4242/',
        headers=headers,
    )
    assert unban_response.status_code == 200
    unban_payload = unban_response.json()
    assert unban_payload['removed'] is True

    empty_list = await client.get(
        f'/bot/{stored_bot.uuid}/banned_users/',
        headers=headers,
    )
    assert empty_list.status_code == 200
    assert empty_list.json() == []

    second_unban = await client.delete(
        f'/bot/{stored_bot.uuid}/banned_users/4242/',
        headers=headers,
    )
    assert second_unban.status_code == 200
    assert second_unban.json()['removed'] is False

    missing_bot = await client.get(f'/bot/{uuid4()}/banned_users/', headers=headers)
    assert missing_bot.status_code == 404


@pytest.mark.api
@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_delete_bot_removes_record(miniapp_client, monkeypatch):
    client, auth_state, headers = miniapp_client
    await crud.upsert_user(
        {
            'id': auth_state['user']['id'],
            'username': 'owner',
            'is_whitelisted': True,
            'is_admin': True,
        }
    )

    async def fake_validate(_: str) -> dict[str, str | int]:
        return {
            'name': 'Disposable Bot',
            'telegram_id': 444555666,
            'username': 'disposable_bot',
        }

    monkeypatch.setattr(
        'feedback_bot.api.miniapp.bots.validate_bot_token',
        fake_validate,
        raising=False,
    )

    create_response = await client.post(
        '/bot/',
        headers=headers,
        json={
            'bot_token': BOT_TOKEN,
            'enable_confirmations': True,
            'start_message': 'Hi',
            'feedback_received_message': 'Bye',
        },
    )
    assert create_response.status_code == 200

    stored_bot = (await crud.get_bots(auth_state['user']['id']))[0]

    delete_response = await client.delete(f'/bot/{stored_bot.uuid}/', headers=headers)

    assert delete_response.status_code == 200
    assert await crud.get_bot(stored_bot.uuid, auth_state['user']['id']) is None

    not_found = await client.delete(f'/bot/{stored_bot.uuid}/', headers=headers)
    assert not_found.status_code == 404
