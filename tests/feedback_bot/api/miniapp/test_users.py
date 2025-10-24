"""API tests for the miniapp user endpoints."""

import pytest
from feedback_bot import crud


@pytest.mark.api
@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_validate_user_returns_authenticated_payload(miniapp_client):
    client, auth_state, headers = miniapp_client
    await crud.upsert_user(
        {
            'id': auth_state['user']['id'],
            'username': auth_state['user']['username'],
            'is_whitelisted': True,
            'is_admin': True,
        }
    )

    response = await client.post('/validate_user/', headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'success'
    assert body['user']['id'] == auth_state['user']['id']
    assert body['user']['is_admin'] is True


@pytest.mark.api
@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_add_user_creates_record(miniapp_client):
    client, auth_state, headers = miniapp_client
    await crud.upsert_user(
        {
            'id': auth_state['user']['id'],
            'username': auth_state['user']['username'],
            'is_whitelisted': True,
            'is_admin': True,
        }
    )

    payload = {
        'telegram_id': 555,
        'username': '@New_User ',
        'language_code': 'ar',
        'is_whitelisted': True,
        'is_admin': False,
    }

    response = await client.post('/user/', headers=headers, json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'success'
    created = await crud.get_user(555)
    assert created is not None
    assert created.username == 'New_User'
    assert created.language_code == 'ar'


@pytest.mark.api
@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_add_user_rejects_long_username(miniapp_client):
    client, auth_state, headers = miniapp_client
    await crud.upsert_user(
        {
            'id': auth_state['user']['id'],
            'username': auth_state['user']['username'],
            'is_whitelisted': True,
            'is_admin': True,
        }
    )

    payload = {
        'telegram_id': 556,
        'username': 'a' * 40,
        'language_code': 'en',
        'is_whitelisted': True,
        'is_admin': False,
    }

    response = await client.post('/user/', headers=headers, json=payload)

    assert response.status_code == 422
    body = response.json()
    assert 'detail' in body
    error = body['detail'][0]
    assert error['loc'][-1] == 'username'
    assert error['type'] == 'string_too_long'


@pytest.mark.api
@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_add_user_rejects_invalid_username_characters(miniapp_client):
    client, auth_state, headers = miniapp_client
    await crud.upsert_user(
        {
            'id': auth_state['user']['id'],
            'username': auth_state['user']['username'],
            'is_whitelisted': True,
            'is_admin': True,
        }
    )

    payload = {
        'telegram_id': 557,
        'username': 'bad name!',
        'language_code': 'en',
        'is_whitelisted': True,
        'is_admin': False,
    }

    response = await client.post('/user/', headers=headers, json=payload)

    assert response.status_code == 400
    body = response.json()
    assert body['status'] == 'error'
    assert 'username' in body['message'].lower()


@pytest.mark.api
@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_manage_user_updates_changes(miniapp_client):
    client, auth_state, headers = miniapp_client
    await crud.upsert_user(
        {
            'id': auth_state['user']['id'],
            'username': auth_state['user']['username'],
            'is_whitelisted': True,
            'is_admin': True,
        }
    )
    await crud.upsert_user({'id': 600, 'username': 'orig', 'language_code': 'en'})

    payload = {'username': 'updated', 'language_code': 'ar', 'is_whitelisted': True}

    response = await client.put('/user/600/', headers=headers, json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'success'
    updated = await crud.get_user(600)
    assert updated is not None
    assert updated.username == 'updated'
    assert updated.language_code == 'ar'


@pytest.mark.api
@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_manage_user_without_changes_returns_error(miniapp_client):
    client, auth_state, headers = miniapp_client
    await crud.upsert_user(
        {
            'id': auth_state['user']['id'],
            'username': auth_state['user']['username'],
            'is_whitelisted': True,
            'is_admin': True,
        }
    )
    await crud.upsert_user({'id': 601, 'username': 'same', 'language_code': 'en'})

    response = await client.put('/user/601/', headers=headers, json={'username': 'same'})

    assert response.status_code == 400
    body = response.json()
    assert body['status'] == 'error'


@pytest.mark.api
@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_delete_user_removes_user_and_bots(miniapp_client):
    client, auth_state, headers = miniapp_client
    await crud.upsert_user(
        {
            'id': auth_state['user']['id'],
            'username': auth_state['user']['username'],
            'is_whitelisted': True,
            'is_admin': True,
        }
    )

    target_id = 800
    await crud.upsert_user(
        {
            'id': target_id,
            'username': 'target_user',
            'language_code': 'en',
            'is_whitelisted': True,
            'is_admin': False,
        }
    )

    bot = await crud.create_bot(
        telegram_id=555666777,
        bot_token='87654321:ABCDEFGHIJKLMNOPQRSTUVWXYZABCDE1234567890',  # noqa: S106
        username='target_bot',
        name='Target Bot',
        owner=target_id,
        start_message='start',
        feedback_received_message='received',
    )

    response = await client.delete(f'/user/{target_id}/', headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'success'
    assert await crud.get_user(target_id) is None
    assert await crud.bot_exists(bot.telegram_id) is False


@pytest.mark.api
@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_delete_user_rejects_builder_admin(miniapp_client):
    client, auth_state, headers = miniapp_client
    await crud.upsert_user(
        {
            'id': auth_state['user']['id'],
            'username': auth_state['user']['username'],
            'is_whitelisted': True,
            'is_admin': True,
        }
    )

    response = await client.delete(f'/user/{auth_state["user"]["id"]}/', headers=headers)

    assert response.status_code == 403
    payload = response.json()
    assert payload['status'] == 'error'
    assert 'admin' in payload['message'].lower()


@pytest.mark.api
@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_retrieve_user_requires_admin(miniapp_client):
    client, auth_state, headers = miniapp_client
    await crud.upsert_user({'id': 700, 'username': 'target'})

    auth_state['user'] = {'id': 2, 'username': 'viewer', 'language_code': 'en'}

    response = await client.get('/user/700/', headers=headers)

    assert response.status_code == 403
    body = response.json()
    assert body['status'] == 'error'


@pytest.mark.api
@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_list_users_requires_admin(miniapp_client):
    client, auth_state, headers = miniapp_client

    auth_state['user'] = {'id': 99, 'username': 'viewer', 'language_code': 'en', 'is_admin': False}
    await crud.upsert_user(
        {'id': 99, 'username': 'viewer', 'is_whitelisted': True, 'is_admin': False}
    )

    response = await client.get('/user/', headers=headers)

    assert response.status_code == 403
    body = response.json()
    assert body['status'] == 'error'


@pytest.mark.api
@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_set_language_updates_user_record(miniapp_client):
    client, auth_state, headers = miniapp_client
    await crud.upsert_user(
        {
            'id': auth_state['user']['id'],
            'username': auth_state['user']['username'],
            'language_code': 'en',
            'is_whitelisted': True,
            'is_admin': True,
        }
    )

    auth_state['user']['language_code'] = 'en'

    response = await client.post('/set_language/', headers=headers, json={'language': 'ar'})

    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'success'
    updated = await crud.get_user(auth_state['user']['id'])
    assert updated is not None
    assert updated.language_code == 'ar'
    assert body['user']['language_code'] == 'ar'
