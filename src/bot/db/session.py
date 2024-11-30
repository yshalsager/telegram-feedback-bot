"""Database initialization"""

import json
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from src import DATA_DIR
from src.bot.db.base import Base
from src.builder.db.crud import get_bots_ids

engines = {}


def create_db(bot_id: int) -> None:
    """Create database."""
    db_url = f'sqlite:///{DATA_DIR.absolute()}/{bot_id}.db'
    alembic_cfg = Config(Path(__file__).parent / 'alembic.ini')
    alembic_cfg.set_main_option('sqlalchemy.url', db_url)
    command.upgrade(alembic_cfg, 'head')
    engines.update(
        {
            bot_id: create_engine(
                db_url,
                connect_args={'check_same_thread': False},
                json_serializer=lambda obj: json.dumps(obj, ensure_ascii=False),
            )
        }
    )


for bot in get_bots_ids():
    create_db(bot)


@contextmanager
def session_scope(bot_id: int) -> Generator[scoped_session[Session]]:
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
