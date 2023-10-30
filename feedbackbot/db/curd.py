from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from sqlalchemy import func
from sqlalchemy.orm import Query

from feedbackbot.db.models.chat import Chat
from feedbackbot.db.models.mapping import Mapping
from feedbackbot.db.models.stats import Stat
from feedbackbot.db.models.topic import Topic
from feedbackbot.db.session import session

F = TypeVar("F", bound=Callable[..., Any])


def db_exceptions_handler(function: F) -> F:
    @wraps(function)
    def wrapper(*args: Any, **kwargs: Any) -> F:
        try:
            return cast(F, function(*args, **kwargs))
        except Exception as err:
            session.rollback()
            raise err

    return cast(F, wrapper)


@db_exceptions_handler
def add_chat_to_db(user_id: int, user_name: str, chat_type: int) -> None:
    query: Query = session.query(Chat).filter(Chat.user_id == user_id)
    if not query.first():
        session.add(Chat(user_id=user_id, user_name=user_name, type=chat_type))
        session.commit()


@db_exceptions_handler
def remove_chat_from_db(user_id: int) -> bool:
    query: Query = session.query(Chat).filter(Chat.user_id == user_id)
    chat = query.first()
    if chat:
        session.delete(chat)
        session.commit()
        return True
    return False


def get_chats_count() -> int:
    return session.query(func.count(Chat.user_id)).scalar() or 0


def get_all_chats(include_groups_and_channels: bool = False) -> list[Chat]:
    query: Query = session.query(Chat)
    if not include_groups_and_channels:
        query = query.filter(Chat.type == 0)  # 0=user, 1=group, 2=channel
    return query.all()


def get_chat_title(chat_id: int) -> str:
    return session.query(Chat.user_name).filter(Chat.user_id == chat_id).scalar() or ""


def increment_usage_times(user_id: int) -> None:
    chat = session.query(Chat).filter(Chat.user_id == user_id).first()
    if chat:
        chat.usage_times += 1
        session.commit()


@db_exceptions_handler
def add_mapping(user_id: int, source: int, topic_id: int, destination: int) -> None:
    query: Query = session.query(Mapping).filter(
        Mapping.user_id == user_id, Mapping.source == source, Mapping.destination == destination
    )
    if not query.first():
        session.add(
            Mapping(user_id=user_id, source=source, topic_id=topic_id, destination=destination)
        )
        session.commit()


def get_mapping(user_id: int, source: int) -> Mapping | None:
    return session.query(Mapping).filter(Chat.user_id == user_id, Mapping.source == source).first()


def get_stats() -> Stat | None:
    return session.query(Stat).first()


def increment_incoming_stats() -> None:
    stats = get_stats()
    if not stats:
        session.add(Stat(incoming=1, outgoing=0))
    else:
        stats.incoming += 1
    session.commit()


def increment_outgoing_stats() -> None:
    stats = get_stats()
    if not stats:
        session.add(Stat(incoming=0, outgoing=1))
    else:
        stats.outgoing += 1
    session.commit()


def get_topic(user_id: int) -> int:
    return session.query(Topic.topic_id).filter(Topic.user_id == user_id).scalar() or -1


def get_user_id_of_topic(topic_id: int) -> int:
    return session.query(Topic.user_id).filter(Topic.topic_id == topic_id).scalar() or -1


@db_exceptions_handler
def add_topic(user_id: int, topic_id: int) -> None:
    if not get_topic(user_id):
        session.add(Topic(user_id=user_id, topic_id=topic_id))
        session.commit()
