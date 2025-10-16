"""API tests for miniapp bot endpoints."""

from uuid import UUID, uuid4

import pytest
from feedback_bot import crud

BOT_TOKEN = '12345678:abcdefghijklmnopqrstuvwxyzABCD12345'  # noqa: S105


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

    assert response.status_code == 200
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
