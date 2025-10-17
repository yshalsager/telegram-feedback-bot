"""Async CRUD helper tests for users and bots."""

from __future__ import annotations

import pytest
from feedback_bot import crud
from feedback_bot.models import Bot, BotStats, BroadcastMessage, FeedbackChat, User


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


@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_bot_forward_chat_by_telegram_id_updates_destination():
    owner, _ = await crud.upsert_user({'id': 999})
    bot = await crud.create_bot(
        telegram_id=333444,
        bot_token='FW_TOKEN',  # noqa: S106
        username='link_bot',
        name='Link Bot',
        owner=owner.telegram_id,
        enable_confirmations=True,
        start_message='start',
        feedback_received_message='received',
    )

    updated = await crud.update_bot_forward_chat_by_telegram_id(bot.telegram_id, -100123)

    assert updated is True
    stored = await Bot.objects.aget(pk=bot.pk)
    assert stored.forward_chat_id == -100123

    missing = await crud.update_bot_forward_chat_by_telegram_id(555666, -100999)
    assert missing is False


@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_get_user_returns_user():
    await crud.upsert_user({'id': 123, 'username': 'Visitor'})

    user = await crud.get_user(123)

    assert user is not None
    assert user.username == 'Visitor'


@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_is_admin_user_checks_flag():
    await crud.upsert_user({'id': 111})
    await crud.upsert_user({'id': 112})

    assert await crud.is_admin_user(111) is True
    assert await crud.is_admin_user(112) is False


@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_delete_user_removes_records():
    await crud.upsert_user({'id': 7777})

    deleted = await crud.delete_user(7777)

    assert deleted is True
    assert await crud.get_user(7777) is None


@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_get_users_returns_all_users():
    await crud.upsert_user({'id': 900})
    await crud.upsert_user({'id': 901})

    users = await crud.get_users()

    assert sorted(user.telegram_id for user in users) == [900, 901]


@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_get_user_language_returns_default_when_missing():
    assert await crud.get_user_language(4242) == 'en'


@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_user_language_helpers_update_and_lookup():
    await crud.upsert_user({'id': 3030, 'language_code': 'en'})

    await crud.update_user_language(3030, 'ar')

    assert await crud.get_user_language(3030) == 'ar'


@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_user_is_whitelisted_filters_properly():
    await crud.upsert_user({'id': 4040, 'is_whitelisted': False})
    await crud.upsert_user({'id': 5050, 'is_whitelisted': True})

    assert await crud.user_is_whitelisted(4040) is None
    whitelisted = await crud.user_is_whitelisted(5050)
    assert whitelisted is not None
    assert whitelisted.telegram_id == 5050


@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_get_bots_tokens_returns_decrypted_tokens():
    owner, _ = await crud.upsert_user({'id': 6060})
    await crud.create_bot(
        telegram_id=444001,
        bot_token='TOKEN_ONE',  # noqa: S106
        username='token_bot_1',
        name='Token Bot 1',
        owner=owner.telegram_id,
        enable_confirmations=True,
        start_message='start',
        feedback_received_message='received',
    )
    await crud.create_bot(
        telegram_id=444002,
        bot_token='TOKEN_TWO',  # noqa: S106
        username='token_bot_2',
        name='Token Bot 2',
        owner=owner.telegram_id,
        enable_confirmations=False,
        start_message='start',
        feedback_received_message='received',
    )

    tokens = await crud.get_bots_tokens()

    assert sorted(tokens) == ['TOKEN_ONE', 'TOKEN_TWO']


@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_get_bot_config_returns_enabled_bot():
    owner, _ = await crud.upsert_user({'id': 7070})
    bot = await crud.create_bot(
        telegram_id=555001,
        bot_token='CFG_TOKEN',  # noqa: S106
        username='cfg_bot',
        name='Cfg Bot',
        owner=owner.telegram_id,
        enable_confirmations=True,
        start_message='hello',
        feedback_received_message='reply',
    )

    config = await crud.get_bot_config(str(bot.uuid))

    assert config is not None
    assert config.token == 'CFG_TOKEN'  # noqa: S105
    assert config.forward_chat_id is None


@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_get_bots_respects_admin_visibility():
    admin, _ = await crud.upsert_user({'id': 111})
    owner2, _ = await crud.upsert_user({'id': 8080})
    bot_admin = await crud.create_bot(
        telegram_id=666001,
        bot_token='ADM_TOKEN',  # noqa: S106
        username='adm_bot',
        name='Admin Bot',
        owner=admin.telegram_id,
        enable_confirmations=True,
        start_message='start',
        feedback_received_message='received',
    )
    bot_owner = await crud.create_bot(
        telegram_id=666002,
        bot_token='OWN_TOKEN',  # noqa: S106
        username='owner_bot',
        name='Owner Bot',
        owner=owner2.telegram_id,
        enable_confirmations=False,
        start_message='start',
        feedback_received_message='received',
    )

    admin_view = await crud.get_bots(admin.telegram_id)
    non_admin_view = await crud.get_bots(owner2.telegram_id)

    assert {bot.username for bot in admin_view} == {bot_admin.username, bot_owner.username}
    assert [bot.username for bot in non_admin_view] == [bot_owner.username]


@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_bot_settings_applies_changes():
    owner, _ = await crud.upsert_user({'id': 9090})
    bot = await crud.create_bot(
        telegram_id=777001,
        bot_token='UPD_TOKEN',  # noqa: S106
        username='upd_bot',
        name='Upd Bot',
        owner=owner.telegram_id,
        enable_confirmations=True,
        start_message='hello',
        feedback_received_message='thanks',
    )

    updated = await crud.update_bot_settings(
        bot.uuid,
        owner.telegram_id,
        {'start_message': 'new', 'confirmations_on': False},
    )

    assert updated is not None
    assert updated.start_message == 'new'
    assert updated.confirmations_on is False


@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_bot_settings_requires_valid_filters():
    owner, _ = await crud.upsert_user({'id': 10010})
    bot = await crud.create_bot(
        telegram_id=888001,
        bot_token='UPD_NONE',  # noqa: S106
        username='upd_none',
        name='Upd None',
        owner=owner.telegram_id,
        enable_confirmations=True,
        start_message='hello',
        feedback_received_message='thanks',
    )

    assert await crud.update_bot_settings(bot.uuid, owner.telegram_id, {}) is None
    assert await crud.update_bot_settings(bot.uuid, 424242, {'start_message': 'nope'}) is None


@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_get_builder_broadcast_targets_returns_owner_ids():
    owner_a, _ = await crud.upsert_user({'id': 12000})
    owner_b, _ = await crud.upsert_user({'id': 13000})
    await crud.create_bot(
        telegram_id=999100,
        bot_token='BROAD_A',  # noqa: S106
        username='broadcast_a',
        name='Broadcast A',
        owner=owner_a.telegram_id,
        enable_confirmations=True,
        start_message='start',
        feedback_received_message='received',
    )
    await crud.create_bot(
        telegram_id=999200,
        bot_token='BROAD_B',  # noqa: S106
        username='broadcast_b',
        name='Broadcast B',
        owner=owner_b.telegram_id,
        enable_confirmations=True,
        start_message='start',
        feedback_received_message='received',
    )

    targets = await crud.get_builder_broadcast_targets()

    assert sorted(targets) == [12000, 13000]


@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_get_feedback_chat_targets_supports_bot_and_id():
    owner, _ = await crud.upsert_user({'id': 14000})
    bot = await crud.create_bot(
        telegram_id=999300,
        bot_token='CHAT_TOKEN',  # noqa: S106
        username='chatbot',
        name='Chat Bot',
        owner=owner.telegram_id,
        enable_confirmations=True,
        start_message='hey',
        feedback_received_message='received',
    )
    await FeedbackChat.objects.acreate(bot=bot, user_telegram_id=1, username='one')
    await FeedbackChat.objects.acreate(bot=bot, user_telegram_id=2, username='two')

    targets_from_instance = await crud.get_feedback_chat_targets(bot)
    targets_from_id = await crud.get_feedback_chat_targets(bot.id)

    assert sorted(targets_from_instance) == [1, 2]
    assert sorted(targets_from_id) == [1, 2]


@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_record_broadcast_message_handles_builder_and_bot():
    builder_record = await crud.record_broadcast_message(bot=None, chat_id=10, message_id=20)

    owner, _ = await crud.upsert_user({'id': 15000})
    bot = await crud.create_bot(
        telegram_id=999400,
        bot_token='BROAD_REC',  # noqa: S106
        username='broadcast_rec',
        name='Broadcast Rec',
        owner=owner.telegram_id,
        enable_confirmations=True,
        start_message='start',
        feedback_received_message='received',
    )

    bot_record = await crud.record_broadcast_message(bot=bot, chat_id=11, message_id=21)

    assert isinstance(builder_record, BroadcastMessage)
    assert builder_record.bot_id is None
    assert builder_record.chat_id == 10
    assert isinstance(bot_record, BroadcastMessage)
    assert bot_record.bot_id == bot.id
    assert bot_record.chat_id == 11


@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_ensure_feedback_chat_updates_username():
    owner, _ = await crud.upsert_user({'id': 16000})
    bot = await crud.create_bot(
        telegram_id=999500,
        bot_token='CHAT_UPD',  # noqa: S106
        username='chat_upd',
        name='Chat Upd',
        owner=owner.telegram_id,
        enable_confirmations=True,
        start_message='start',
        feedback_received_message='received',
    )

    chat = await crud.ensure_feedback_chat(bot, 200, 'first')
    assert chat.username == 'first'

    chat = await crud.ensure_feedback_chat(bot, 200, 'second')
    assert chat.username == 'second'


@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_mapping_helpers_create_and_fetch_records():
    owner, _ = await crud.upsert_user({'id': 17000})
    bot = await crud.create_bot(
        telegram_id=999600,
        bot_token='MAP_TOKEN',  # noqa: S106
        username='map_bot',
        name='Map Bot',
        owner=owner.telegram_id,
        enable_confirmations=True,
        start_message='start',
        feedback_received_message='received',
    )
    chat = await crud.ensure_feedback_chat(bot, 300, 'mapuser')

    await crud.save_incoming_mapping(bot, chat, user_message_id=11, owner_message_id=22)
    mapping = await crud.get_user_message_mapping(bot, 300, 11)
    assert mapping is not None
    assert mapping.owner_message_id == 22

    await crud.update_incoming_mapping(bot, user_message_id=11, owner_message_id=33)
    mapping = await crud.get_user_message_mapping(bot, 300, 11)
    assert mapping.owner_message_id == 33

    await crud.save_outgoing_mapping(bot, chat, user_message_id=44, owner_message_id=55)
    outgoing = await crud.get_owner_message_mapping(bot, 55)
    assert outgoing is not None
    assert outgoing.user_message_id == 44


@pytest.mark.django
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_clear_feedback_chat_mappings_and_bump_stats():
    owner, _ = await crud.upsert_user({'id': 18000})
    bot = await crud.create_bot(
        telegram_id=999700,
        bot_token='STAT_TOKEN',  # noqa: S106
        username='stat_bot',
        name='Stat Bot',
        owner=owner.telegram_id,
        enable_confirmations=True,
        start_message='start',
        feedback_received_message='received',
    )
    chat = await crud.ensure_feedback_chat(bot, 400, 'statuser')

    await crud.save_incoming_mapping(bot, chat, user_message_id=1, owner_message_id=2)
    await crud.save_outgoing_mapping(bot, chat, user_message_id=3, owner_message_id=4)

    await crud.bump_incoming_messages(bot)
    await crud.bump_outgoing_messages(bot)

    stats = await BotStats.objects.aget(bot=bot)
    assert stats.incoming_messages == 1
    assert stats.outgoing_messages == 1

    await crud.clear_feedback_chat_mappings(bot, chat)

    assert await crud.get_user_message_mapping(bot, 400, 1) is None
    assert await crud.get_owner_message_mapping(bot, 4) is None
