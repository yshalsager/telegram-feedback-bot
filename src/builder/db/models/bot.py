from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql.functions import current_timestamp

from src.builder.db.base import Base


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
    start_message: str = Column(String(4096), nullable=True)
    received_message: str = Column(String(4096), nullable=True)
    sent_message: str = Column(String(4096), nullable=True)
    created_at = Column(DateTime, nullable=False, default=current_timestamp())

    def __repr__(self) -> str:
        return f'Bot(user_name="@{self.username}", owner={self.owner}, group={self.group}, enabled={self.enabled})'
