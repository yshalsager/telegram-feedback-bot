from sqlalchemy import BigInteger, Column, DateTime, String
from sqlalchemy.sql.functions import current_timestamp

from src.builder.db.base import Base


class User(Base):
    __tablename__ = 'users'

    user_id: int = Column(BigInteger, unique=True, primary_key=True, nullable=False)
    user_name: str = Column(String, nullable=False)
    language: str = Column(String(2), nullable=False, default='en')
    created_at = Column(DateTime, nullable=False, default=current_timestamp())

    def __repr__(self) -> str:
        return (
            f'<User(user_id={self.user_id}, user_name={self.user_name}, language={self.language})>'
        )
