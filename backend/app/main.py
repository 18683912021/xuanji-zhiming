import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.accounts.auth import provision_development_admin
from app.accounts.router import private
from app.accounts.router import router as auth_router
from app.agent.router import router as agent_router
from app.agent.workflow import build_agent, make_client
from app.core.config import Settings, get_settings
from app.core.db import DbSession, create_database
from app.core.errors import install_error_handling
from app.readings.reports import router as report_router
from app.readings.router import catalog_router
from app.readings.router import router as reading_router
from app.readings.shares import router as share_router


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(api: FastAPI):
        engine, sessions = create_database(settings)
        api.state.sessions = sessions
        api.state.ai_slots = asyncio.Semaphore(settings.ai_max_concurrent)
        client = make_client(settings)
        api.state.ai_client = client
        api.state.agent = (
            build_agent(client, settings.ai_model, provider_name=settings.ai_provider)
            if client and settings.ai_enabled
            else None
        )
        try:
            if settings.development_admin_enabled:
                async with sessions() as db:
                    await provision_development_admin(db, settings)
            yield
        finally:
            if client is not None:
                await client.close()
            await engine.dispose()

    api = FastAPI(
        title="玄机知命 API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    api.state.settings = settings
    install_error_handling(api)
    api.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.web_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
        expose_headers=["X-Request-ID"],
    )

    @api.get("/api/health/live", tags=["运行状态"])
    async def live() -> dict[str, str]:
        return {"status": "ok"}

    @api.get("/api/health/ready", tags=["运行状态"])
    async def ready(db: DbSession) -> dict[str, str]:
        await db.execute(text("select 1 from alembic_version"))
        return {"status": "ok", "database": "ready"}

    for router in (
        auth_router,
        private,
        catalog_router,
        reading_router,
        share_router,
        report_router,
        agent_router,
    ):
        api.include_router(router, prefix="/api/v1")
    return api


app = create_app()
