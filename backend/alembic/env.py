import asyncio

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from app.accounts import models as account_models  # noqa: F401
from app.agent import models as agent_models  # noqa: F401
from app.core.config import get_settings
from app.core.db import Base
from app.readings import models as reading_models  # noqa: F401


def run_migrations(connection=None):
    options = {"target_metadata": Base.metadata}
    if connection is None:
        options.update(url=get_settings().database_url, literal_binds=True)
    else:
        options["connection"] = connection

    context.configure(**options)
    with context.begin_transaction():
        context.run_migrations()


async def online():
    engine = create_async_engine(get_settings().database_url, poolclass=pool.NullPool)
    try:
        async with engine.connect() as connection:
            await connection.run_sync(run_migrations)
    finally:
        await engine.dispose()


if context.is_offline_mode():
    run_migrations()
else:
    asyncio.run(online())
