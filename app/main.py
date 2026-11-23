"""FastAPI application entrypoint."""
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_settings
from app.database import SessionLocal
from app.logging_config import configure_logging
from app.middleware import RequestContextMiddleware
from app.routers import users

configure_logging(get_settings().log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="User Management API",
    version="1.0.0",
    description="CRUD API for user records. Write endpoints require an `X-API-Key` header when API_KEYS is set.",
)
app.add_middleware(RequestContextMiddleware)
app.include_router(users.router)


@app.exception_handler(SQLAlchemyError)
async def db_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.exception("database_error")
    return JSONResponse(status_code=503, content={"detail": "Database unavailable"})


@app.exception_handler(Exception)
async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_exception")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health", tags=["ops"], response_model=None)
def health() -> dict | JSONResponse:
    """Liveness + database readiness check."""
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.exception("health_check_failed")
        return JSONResponse(status_code=503, content={"status": "unhealthy", "database": "down"})
    return {"status": "healthy", "database": "up"}
