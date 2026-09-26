from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
poolclass = StaticPool if settings.database_url == "sqlite://" else None

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    poolclass=poolclass,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    import models.entities  # noqa: F401  (register mappings)

    Base.metadata.create_all(bind=engine)
