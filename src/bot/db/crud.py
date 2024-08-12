from sqlalchemy import func
from sqlalchemy.orm import Query, Session, scoped_session

from src.bot.db.models.chat import Chat
from src.bot.db.models.mapping import Mapping
from src.bot.db.models.stats import Stat
from src.bot.db.models.topic import Topic
from src.common.db.utils import db_exceptions_handler


@db_exceptions_handler
def add_chat_to_db(
    session: scoped_session[Session], user_id: int, user_name: str, chat_type: int
) -> None:
    query: Query = session.query(Chat).filter_by(user_id=user_id)
    if not query.first():
        session.add(Chat(user_id=user_id, user_name=user_name, type=chat_type))
        session.commit()


@db_exceptions_handler
def remove_chat_from_db(session: scoped_session[Session], user_id: int) -> bool:
    query: Query = session.query(Chat).filter_by(user_id=user_id)
    chat = query.first()
    if chat:
        session.delete(chat)
        session.commit()
        return True
    return False


def get_chats_count(session: scoped_session[Session]) -> int:
    return session.query(func.count(Chat.user_id)).scalar() or 0


def get_all_chats(
    session: scoped_session[Session], include_groups_and_channels: bool = False
) -> list[Chat]:
    query: Query = session.query(Chat)
    if not include_groups_and_channels:
        query = query.filter_by(type=0)  # 0=user, 1=group, 2=channel
    return query.all()


# def get_chat_title(session: scoped_session[Session], chat_id: int) -> str:
#     return session.query(Chat.user_name).filter_by(user_id=chat_id).scalar() or ""


def increment_usage_times(session: scoped_session[Session], user_id: int) -> None:
    chat = session.query(Chat).filter_by(user_id=user_id).first()
    if chat:
        chat.usage_times += 1
        session.commit()


@db_exceptions_handler
def add_mapping(
    session: scoped_session[Session],
    user_id: int,
    source: int,
    topic_id: int,
    destination: int,
    outgoing: bool = False,
) -> None:
    query: Query = session.query(Mapping).filter_by(
        user_id=user_id, source=source, destination=destination, outgoing=outgoing
    )
    if not query.first():
        session.add(
            Mapping(
                user_id=user_id,
                source=source,
                topic_id=topic_id,
                destination=destination,
                outgoing=outgoing,
            )
        )
        session.commit()


def get_mapping(
    session: scoped_session[Session],
    user_id: int | None = None,
    source: int | None = None,
    destination: int | None = None,
    outgoing: bool = False,
) -> Mapping | None:
    if not any((user_id, source, destination)):
        raise ValueError('Must provide at least one filter')

    query = session.query(Mapping).filter_by(outgoing=outgoing)
    if user_id:
        query = query.filter_by(user_id=user_id)
    if source:
        query = query.filter_by(source=source)
    if destination:
        query = query.filter_by(destination=destination)
    return query.first()


@db_exceptions_handler
def update_mapping(
    session: scoped_session[Session], user_id: int, source: int, new_destination: int
) -> None:
    mapping = session.query(Mapping).filter_by(user_id=user_id, source=source).first()
    if not mapping:
        return
    mapping.destination = new_destination
    session.commit()


@db_exceptions_handler
def delete_mapping(session: scoped_session[Session], mapping_id: int) -> None:
    session.query(Mapping).filter_by(id=mapping_id).delete()
    session.commit()


@db_exceptions_handler
def remove_user_mappings(session: scoped_session[Session], user_id: int) -> None:
    session.query(Mapping).filter_by(user_id=user_id).delete()
    session.commit()


def get_stats(session: scoped_session[Session]) -> Stat | None:
    return session.query(Stat).first()


def increment_incoming_stats(session: scoped_session[Session]) -> None:
    stats = get_stats(session)
    if not stats:
        session.add(Stat(incoming=1, outgoing=0))
    else:
        stats.incoming += 1
    session.commit()


def increment_outgoing_stats(session: scoped_session[Session]) -> None:
    stats = get_stats(session)
    if not stats:
        session.add(Stat(incoming=0, outgoing=1))
    else:
        stats.outgoing += 1
    session.commit()


def get_topic(session: scoped_session[Session], user_id: int) -> int:
    return session.query(Topic.topic_id).filter_by(user_id=user_id).scalar() or 0


@db_exceptions_handler
def add_topic(session: scoped_session[Session], user_id: int, topic_id: int) -> Topic:
    topic: Topic | None = session.query(Topic).filter_by(user_id=user_id).first()
    if not topic:
        topic = Topic(user_id=user_id, topic_id=topic_id)
        session.add(topic)
    else:
        topic.topic_id = topic_id
    session.commit()
    return topic
