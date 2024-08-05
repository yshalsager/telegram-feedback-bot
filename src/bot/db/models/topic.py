from sqlalchemy import BigInteger, Column, ForeignKey, Integer

from src.bot.db.base import Base


class Topic(Base):
    __tablename__ = 'topics'

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    user_id: int = Column(BigInteger, ForeignKey('chats.user_id'), nullable=False)
    topic_id: int = Column(BigInteger, nullable=False)
