from sqlalchemy import BigInteger, Column, DateTime, Integer, String
from sqlalchemy.sql.functions import current_timestamp

from feedbackbot.db.base import Base


class Chat(Base):
    __tablename__ = "chats"

    user_id: int = Column(BigInteger, unique=True, primary_key=True, nullable=False)
    user_name: str = Column(String, nullable=False)
    type: int = Column(  # noqa: A003
        Integer, nullable=False
    )  # 0=user, 1=group, 2=channel
    usage_times: int = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=current_timestamp())

    def __repr__(self) -> str:
        return f"<Chat(user_id={self.user_id}, user_name={self.user_name}, type={self.type})>"
