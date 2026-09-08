from collections.abc import AsyncGenerator
import ssl
import sys
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.models.base import Base


def _build_engine_kwargs() -> dict:
    """Build create_async_engine kwargs, adding SSL for cloud Postgres (Neon, etc.)."""
    kwargs: dict = {"future": True}

    # Pool configuration: NullPool for tests, connection checking for production
    if "pytest" in sys.modules:
        kwargs["poolclass"] = NullPool
    else:
        kwargs["pool_pre_ping"] = True

    # Detect SSL requirement from the DATABASE_URL query string
    parsed = urlparse(settings.database_url)
    query_params = parse_qs(parsed.query)
    needs_ssl = (
        query_params.get("ssl", [None])[0] in ("require", "true", "verify-full")
        or query_params.get("sslmode", [None])[0] in ("require", "verify-ca", "verify-full")
    )

    if needs_ssl:
        # Create a default SSL context for asyncpg
        ssl_ctx = ssl.create_default_context()
        # Neon and most managed PG services use valid certs; for self-signed, uncomment:
        # ssl_ctx.check_hostname = False
        # ssl_ctx.verify_mode = ssl.CERT_NONE
        kwargs["connect_args"] = {"ssl": ssl_ctx}

        # Strip ssl/sslmode/channel_binding from the URL so asyncpg doesn't choke on unknown params
        clean_params = {k: v for k, v in query_params.items() if k not in ("ssl", "sslmode", "channel_binding")}
        clean_query = urlencode(clean_params, doseq=True)
        kwargs["url"] = urlunparse(parsed._replace(query=clean_query))

    return kwargs


_engine_kwargs = _build_engine_kwargs()
_db_url = _engine_kwargs.pop("url", settings.database_url)
engine = create_async_engine(_db_url, **_engine_kwargs)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
