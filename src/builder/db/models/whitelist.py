from sqlalchemy import BigInteger, Column

from src.builder.db.base import Base


class Whitelist(Base):
    __tablename__ = 'whitelist'

    user_id: int = Column(BigInteger, primary_key=True, nullable=False, unique=True)

    def __repr__(self) -> str:
        return f'<Whitelist(user_id={self.user_id})>'
