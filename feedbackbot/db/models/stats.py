from sqlalchemy import Column, Integer

from feedbackbot.db.base import Base


class Stat(Base):
    __tablename__ = "stats"

    id: int = Column(Integer, nullable=False, primary_key=True, autoincrement=True)  # noqa: A003
    incoming: int = Column(Integer, nullable=False, default=0)
    outgoing: int = Column(Integer, nullable=False, default=0)

    def __repr__(self) -> str:
        return f"<Stats(incoming={self.incoming}, outgoing={self.outgoing})>"
