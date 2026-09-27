"""Create the FastAPI application."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import actions, exports, inventory, vehicles
from app.api.errors import add_error_handlers
from app.db import make_engine, make_session_factory
from app.observability import add_observability


def create_app(database_url: str | None = None) -> FastAPI:
    """Build the application. The database comes from DATABASE_URL unless given here."""
    engine = make_engine(database_url)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        yield
        engine.dispose()

    app = FastAPI(
        title="Intelligent Inventory Dashboard API",
        version="0.1.0",
        description=(
            "Helps dealership managers see their vehicle stock, find vehicles that have "
            "been in stock for more than 90 days, and record what to do about them."
        ),
        lifespan=lifespan,
    )
    app.state.engine = engine
    app.state.session_factory = make_session_factory(engine)

    add_observability(app)
    add_error_handlers(app)
    app.include_router(vehicles.router)
    app.include_router(actions.router)
    app.include_router(inventory.router)
    app.include_router(exports.router)
    return app


app = create_app()
