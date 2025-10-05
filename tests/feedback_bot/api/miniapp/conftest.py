import os

import pytest
from config.urls import api
from feedback_bot.api.miniapp import miniapp_auth
from ninja.testing import TestAsyncClient


@pytest.fixture
def miniapp_client(monkeypatch, settings):
    settings.TELEGRAM_LANGUAGES = ['en', 'ar']
    settings.TELEGRAM_BUILDER_BOT_ADMINS = {1}
    settings.TELEGRAM_NEW_BOT_ADMIN_APPROVAL = True
    settings.DEBUG = False
    os.environ.setdefault('NINJA_SKIP_REGISTRY', '1')

    auth_state = {
        'user': {
            'id': 1,
            'username': 'admin',
            'language_code': 'en',
            'is_admin': True,
        }
    }

    async def fake_auth(self, request, token):  # pragma: no cover - behaviour tested via endpoints
        return auth_state['user']

    monkeypatch.setattr(
        miniapp_auth,
        'authenticate',
        fake_auth.__get__(miniapp_auth, type(miniapp_auth)),
    )

    client = TestAsyncClient(api)
    headers = {'Authorization': 'Bearer token'}
    return client, auth_state, headers
