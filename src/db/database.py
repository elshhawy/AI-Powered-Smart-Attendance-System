# src/db/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from src.core.config import settings


# The engine is the actual connection to PostgreSQL.
# pool_size=10 means keep 10 connections open at all times.
# max_overflow=20 means allow 20 extra connections under heavy load.
# echo=False means don't print every SQL query to the terminal.
#   Set echo=True temporarily if you want to see the SQL being generated.
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    echo=False,
)

# SessionLocal is a factory that creates database sessions.
# autocommit=False means changes don't save automatically — you call db.commit()
# autoflush=False means SQLAlchemy doesn't automatically sync before queries
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base is the parent class for all our SQLAlchemy models.
# When you do class Admin(Base), SQLAlchemy knows Admin is a database table.
class Base(DeclarativeBase):
    pass


def get_db():
    """
    FastAPI dependency. You will use this in every endpoint later.

    It creates a database session, gives it to the endpoint function,
    and then ALWAYS closes it — even if an exception happens.

    Without the try/finally, a crash inside an endpoint would leave
    the session open. After enough crashes, you'd run out of connections
    and the entire app would stop working.
    """
    db = SessionLocal()
    try:
        yield db        # Give the session to whoever called get_db()
    finally:
        db.close()      # Always run this, no matter what