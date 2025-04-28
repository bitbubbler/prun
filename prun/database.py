from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
from contextlib import contextmanager

engine = create_engine("sqlite:///prun.db")


def init_db() -> None:
    """Initialize the database by creating all tables."""
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Get a database session with automatic transaction management.

    Yields:
        SQLModel session
    """
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
