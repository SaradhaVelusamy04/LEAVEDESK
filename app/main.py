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
from app.api.v1.leaves import router as leaves_router
from app.api.v1.wfh import router as wfh_router
from app.api.v1.manager import router as manager_router
from app.api.v1.reports import router as reports_router


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

    # Routers (mounted both at root and with /api/v1 prefix)
    # Register all API routers under the versioned API prefix
    # Routers: register both root-level and versioned API routes
    for router in (
        health_router,
        auth_router,
        leaves_router,
        wfh_router,
        manager_router,
        reports_router,
    ):
        app.include_router(router)
        #app.include_router(router, prefix=settings.API_V1_STR)
    return app


app = create_application()


@app.get("/", tags=["Root"])
def root():
    return {
        "application": "LeaveDesk",
        "description": "Employee Leave and Work-From-Home Management API",
        "message": "Welcome to LeaveDesk!",
        "documentation": "/docs",
        "health": "/health"
    }
