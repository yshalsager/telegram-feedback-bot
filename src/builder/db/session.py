"""Database initialization"""

import json

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from src import DB_PATH
from src.builder.db.base import Base

db_engine = create_engine(
    f'sqlite:///{DB_PATH}',
    connect_args={'check_same_thread': False},
    json_serializer=lambda obj: json.dumps(obj, ensure_ascii=False),
)

Base.metadata.create_all(bind=db_engine)

session = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        binds={
            Base: db_engine,
        },
    )
)
