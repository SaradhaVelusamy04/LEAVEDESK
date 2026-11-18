from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)
from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router


def create_application() -> FastAPI:
    """Application factory for LeaveDesk API."""
    app = FastAPI(
        title="LeaveDesk API",
        description=(
            "Enterprise Employee Leave and Work-From-Home (WFH) Management REST API. "
            "Built with FastAPI, PostgreSQL, SQLAlchemy 2.x, and Clean Architecture principles."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    # CORS Middleware configuration
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Exception Handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Health router
    app.include_router(health_router)
    app.include_router(health_router, prefix=settings.API_V1_STR)

    # Auth router (mounted at /auth and /api/v1/auth)
    app.include_router(auth_router)
    app.include_router(auth_router, prefix=settings.API_V1_STR)

    return app


app = create_application()
