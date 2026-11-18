from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get(
    "/leaves",
    summary="Download 6-Month Leave & WFH Report",
    description=(
        "Download a CSV report of leave and WFH history for the last 6 calendar months. "
        "Employees can download their own report. Managers can specify ?employee_id=<id> for direct reports."
    ),
    responses={
        200: {
            "description": "CSV file download",
            "content": {"text/csv": {}}
        },
        401: {"description": "Authentication required"},
        403: {"description": "Unauthorized access to another employee's report"},
        404: {"description": "Employee not found"}
    }
)
def download_leave_report(
    employee_id: Optional[int] = Query(None, description="Direct report employee ID (managers only)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate and stream 6-month CSV report."""
    service = ReportService(db, UserRepository(db))
    csv_content, filename = service.generate_leave_report(current_user, employee_id=employee_id)

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "text/csv; charset=utf-8"
        }
    )
