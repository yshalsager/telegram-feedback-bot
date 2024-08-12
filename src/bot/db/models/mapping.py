from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, Integer

from src.bot.db.base import Base


class Mapping(Base):
    __tablename__ = 'mappings'

    id: int = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    user_id: int = Column(BigInteger, ForeignKey('chats.user_id'), nullable=False)
    source: int = Column(BigInteger, nullable=False)  # message ID in user chat
    topic_id: int = Column(BigInteger, ForeignKey('topics.topic_id'), nullable=True)
    destination: int = Column(BigInteger, nullable=False)  # message ID in bot chat topic
    outgoing: bool = Column(
        Boolean, nullable=False, default=False
    )  # True for outgoing, False for incoming

    def __repr__(self) -> str:
        return (
            f'Mapping(id={self.id}, user_id={self.user_id}, source={self.source}, '
            f'topic_id={self.topic_id}, destination={self.destination}, outgoing={self.outgoing})'
        )
