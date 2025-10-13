from fast_depends import Depends
from sqlmodel import Session
from prun.database import engine
from fio_wrapper import FIO


def get_session():
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise


def get_fio():
    return FIO()
