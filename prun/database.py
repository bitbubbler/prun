from sqlmodel import SQLModel, create_engine

engine = create_engine("sqlite:///prun.db")


def init_db() -> None:
    """Initialize the database by creating all tables."""
    SQLModel.metadata.create_all(engine)
