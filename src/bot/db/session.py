"""Database initialization"""

import json
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from src.bot.db.base import Base
from src.builder.db.crud import get_bots_ids

engines = {}


def create_db(bot_id: int) -> None:
    """Create database."""
    db_engine = create_engine(
        f'sqlite:///data/{bot_id}.db',
        connect_args={'check_same_thread': False},
        json_serializer=lambda obj: json.dumps(obj, ensure_ascii=False),
    )
    Base.metadata.create_all(bind=db_engine)
    engines.update({bot_id: db_engine})


for bot in get_bots_ids():
    create_db(bot)


@contextmanager
def session_scope(bot_id: int) -> Generator[scoped_session[Session], None, None]:
    """Provides a transactional scope around a series of operations."""
    session = scoped_session(
        sessionmaker(
            autocommit=False,
            autoflush=True,
            binds={
                Base: engines[bot_id],
            },
        )
    )
    try:
        yield session
        session.commit()
    except Exception as err:
        session.rollback()
        raise err
    finally:
        session.close()
