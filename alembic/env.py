from alembic import context

from app.config import get_settings
from app.database import Base, engine
import app.models  # noqa: F401  (register models)

target_metadata = Base.metadata


def run_migrations_online() -> None:
    url = get_settings().database_url
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, url=url)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
