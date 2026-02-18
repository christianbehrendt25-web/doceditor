from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session

Base = declarative_base()
engine = None
SessionFactory = None
ScopedSession = None


def init_db(database_url: str):
    global engine, SessionFactory, ScopedSession

    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    engine = create_engine(database_url, connect_args=connect_args)
    SessionFactory = sessionmaker(bind=engine)
    ScopedSession = scoped_session(SessionFactory)
    Base.metadata.create_all(engine)


def get_session():
    return ScopedSession()
