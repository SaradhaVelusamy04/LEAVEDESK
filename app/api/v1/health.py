from fastapi import APIRouter, status, Response
from app.core.database import check_db_connection

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Health Check",
    description="Returns service health status and verifies active database connectivity.",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "System is healthy and database is connected",
            "content": {"application/json": {"example": {"status": "ok"}}}
        },
        503: {
            "description": "Database connectivity failed",
            "content": {"application/json": {"example": {"status": "error", "detail": "Database connection failed"}}}
        }
    }
)
def get_health(response: Response):
    """Public health probe checking service status and database connectivity."""
    db_alive = check_db_connection()
    if not db_alive:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "error", "detail": "Database connection failed"}
    return {"status": "ok"}
