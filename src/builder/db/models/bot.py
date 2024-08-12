from typing import Any

from pydantic import BaseModel
from sqlalchemy import JSON, BigInteger, Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.sql.functions import current_timestamp

from src.builder.db.base import Base


class BotSettings(BaseModel):
    start_message: str | None = None
    received_message: str | None = None
    sent_message: str | None = None
    confirmations: bool = True


class Bot(Base):
    __tablename__ = 'bots'

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    username: str = Column(String(32), nullable=False, unique=True)
    # first_name (32) + space (1) + last_name (32)
    name: str = Column(String(65), nullable=False, unique=True)
    user_id: int = Column(BigInteger, unique=True, nullable=False)
    token: str = Column(String(45), nullable=False, unique=True)
    owner: int = Column(BigInteger, nullable=False)
    group: int | None = Column(BigInteger, nullable=True)
    enabled: bool = Column(Boolean, nullable=False, default=False)
    settings: dict[str, Any] = Column(
        JSON, nullable=False, default=lambda: BotSettings().model_dump()
    )
    created_at = Column(DateTime, nullable=False, default=current_timestamp())

    @property
    def bot_settings(self) -> BotSettings:
        return BotSettings(**self.settings)

    @bot_settings.setter
    def bot_settings(self, value: BotSettings) -> None:
        self.settings = value.model_dump()
        flag_modified(self, 'settings')

    def __repr__(self) -> str:
        return f'Bot(user_name="@{self.username}", owner={self.owner}, group={self.group}, enabled={self.enabled})'
