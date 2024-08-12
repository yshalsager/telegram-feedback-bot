from datetime import datetime
from typing import TypeAlias

from sqlalchemy import Row, func
from sqlalchemy.orm import Query

from src.builder.db.models.bot import Bot
from src.builder.db.models.user import User
from src.builder.db.models.whitelist import Whitelist
from src.builder.db.session import session
from src.common.db.utils import db_exceptions_handler
from src.common.utils.cryptography import decrypt_token, encrypt_token

TBot: TypeAlias = Row[tuple[str, str, bool, int, int | None, str, str, str, datetime]]  # noqa: UP040


# whitelist
@db_exceptions_handler
def get_whitelist() -> list[int]:
    return [user.user_id for user in session.query(Whitelist).all()]


@db_exceptions_handler
def is_whitelisted(user_id: int) -> bool:
    return session.query(Whitelist).filter(Whitelist.user_id == user_id).first() is not None


@db_exceptions_handler
def add_to_whitelist(user_id: int) -> None:
    query: Query[Whitelist] = session.query(Whitelist).filter(Whitelist.user_id == user_id)
    if not query.first():
        session.add(Whitelist(user_id=user_id))
        session.commit()


@db_exceptions_handler
def remove_from_whitelist(user_id: int) -> None:
    whitelist_user = session.query(Whitelist).filter(Whitelist.user_id == user_id).first()
    if whitelist_user:
        session.delete(whitelist_user)
        session.commit()


# users
@db_exceptions_handler
def get_user(user_id: int) -> User | None:
    return session.query(User).filter(User.user_id == user_id).first()


@db_exceptions_handler
def add_user(user_id: int, user_name: str, language: str = 'en') -> None:
    query: Query[User] = session.query(User).filter(User.user_id == user_id)
    if not query.first():
        session.add(User(user_id=user_id, user_name=user_name, language=language))
        session.commit()


@db_exceptions_handler
def update_user_language(user_id: int, language: str) -> bool:
    user: User | None = session.query(User).filter(User.user_id == user_id).first()
    if not user:
        return False
    user.language = language
    session.commit()
    return True


# bots
@db_exceptions_handler
def add_bot(
    user_id: int,
    name: str,
    username: str,
    token: str,
    owner: int,
    enabled: bool = False,
) -> Bot:
    bot: Bot | None = session.query(Bot).filter(Bot.username == username).first()
    if not bot:
        bot = Bot(
            username=username,
            name=name,
            user_id=user_id,
            token=encrypt_token(token),
            owner=owner,
            enabled=enabled,
        )
        session.add(bot)
    else:
        bot.token = encrypt_token(token)
        bot.enabled = enabled
    session.commit()
    return bot


def get_bot(user_id: int | str) -> Bot | None:
    return session.query(Bot).filter(Bot.user_id == user_id).first()


@db_exceptions_handler
def remove_bot(user_id: str | int, owner_id: str | int) -> bool:
    bot: Bot | None = (
        session.query(Bot).filter(Bot.user_id == user_id, Bot.owner == owner_id).first()
    )
    if not bot:
        return False
    session.delete(bot)
    session.commit()
    return True


def get_bots_count() -> int:
    return session.query(func.count(Bot.user_id)).scalar() or 0


def get_all_bots() -> list[Row[tuple[int, str, str, int, bool]]]:
    return session.query(Bot.user_id, Bot.username, Bot.name, Bot.owner, Bot.enabled).all()


def get_bots_ids() -> list[int]:
    return [bot.user_id for bot in session.query(Bot.user_id).all()]


def get_bots_tokens() -> list[tuple[str, int, str]]:
    return [
        (f'{bot.user_id}:{decrypt_token(bot.token)}', bot.owner, bot.username)
        for bot in session.query(Bot.user_id, Bot.token, Bot.owner, Bot.username)
        .filter(Bot.enabled == True)
        .all()
    ]


def get_all_owners() -> list[Row[tuple[int]]]:
    return session.query(Bot.owner).distinct().all()


def get_user_bots(owner: int) -> list[Row[tuple[str, int, str]]]:
    return session.query(Bot.name, Bot.user_id, Bot.username).filter(Bot.owner == owner).all()


def get_bot_owner(user_id: int | str) -> int:
    return session.query(Bot.owner).filter(Bot.user_id == user_id).scalar() or 0


@db_exceptions_handler
def update_bot_messages(
    user_id: int, start_message: str = '', received_message: str = '', sent_message: str = ''
) -> bool:
    bot: Bot | None = session.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot:
        return False
    settings = bot.bot_settings
    if start_message:
        settings.start_message = start_message[:4096]
    if received_message:
        settings.received_message = received_message[:4096]
    if sent_message:
        settings.sent_message = sent_message[:4096]
    bot.bot_settings = settings
    session.commit()
    return True


@db_exceptions_handler
def update_bot_status(user_id: int | str) -> Bot | None:
    bot: Bot | None = session.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot:
        return None
    bot.enabled = not bot.enabled
    session.commit()
    return bot


@db_exceptions_handler
def update_bot_group(user_id: int, group_id: int) -> bool:
    bot: Bot | None = session.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot:
        return False
    bot.group = group_id
    session.commit()
    return True


@db_exceptions_handler
def delete_bot_group(user_id: int | str) -> bool:
    bot: Bot | None = session.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot:
        return False
    bot.group = None
    session.commit()
    return True


@db_exceptions_handler
def update_bot_confirmations(user_id: int | str) -> Bot | None:
    bot: Bot | None = session.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot:
        return None
    settings = bot.bot_settings
    settings.confirmations = not settings.confirmations
    bot.bot_settings = settings
    session.commit()
    return bot
