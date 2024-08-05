from typing import TypeAlias

from sqlalchemy import Row, func
from sqlalchemy.orm import Query

from src.builder.db.models.bot import Bot
from src.builder.db.models.user import User
from src.builder.db.session import session
from src.common.db.utils import db_exceptions_handler

TBot: TypeAlias = Row[tuple[str, str, bool, int, int | None, str, str, str]]  # noqa: UP040


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
            token=token,
            owner=owner,
            enabled=enabled,
        )
        session.add(bot)
    else:
        bot.token = token
        bot.enabled = enabled
    session.commit()
    return bot


def get_bot(user_id: int | str) -> TBot | None:
    return (
        session.query(
            Bot.username,
            Bot.name,
            Bot.enabled,
            Bot.owner,
            Bot.group,
            Bot.start_message,
            Bot.received_message,
            Bot.sent_message,
        )
        .filter(Bot.user_id == user_id)
        .first()
    )


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
        (f'{bot.user_id}:{bot.token}', bot.owner, bot.username)
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
    if start_message:
        bot.start_message = start_message[:4096]
    if received_message:
        bot.received_message = received_message[:4096]
    if sent_message:
        bot.sent_message = sent_message[:4096]
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
