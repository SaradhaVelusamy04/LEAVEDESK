import io
import csv
from datetime import date, datetime, timedelta, timezone
from typing import Optional, Tuple, List, Dict, Any
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.user import User
from app.models.leave import LeaveRequest
from app.models.wfh import WfhRequest
from app.repositories.user_repo import UserRepository
from app.domain.enums import RoleEnum, RequestStatusEnum, RequestTypeEnum
from app.core.exceptions import ResourceNotFoundException, AuthorizationException


class ReportService:
    """Application service for computing and rendering historical leave reports."""

    def __init__(self, db: Session, user_repo: UserRepository):
        self.db = db
        self.user_repo = user_repo

    def get_target_user_and_validate_access(
        self,
        current_user: User,
        employee_id: Optional[int] = None
    ) -> User:
        """Validate access permissions and retrieve the report subject."""
        # 1. Default to self if no employee_id provided
        if employee_id is None or employee_id == current_user.id:
            return current_user

        # 2. If non-manager attempts to access another user's report -> 403
        if current_user.role != RoleEnum.MANAGER.value:
            raise AuthorizationException(
                detail="Employees are only authorized to download their own report"
            )

        # 3. Manager requesting report for employee_id: verify employee reports to this manager
        target_user = self.user_repo.get_by_id(employee_id)
        if not target_user:
            raise ResourceNotFoundException(detail="Employee not found")

        if target_user.reports_to_id != current_user.id:
            raise AuthorizationException(
                detail="Managers can only download reports for their direct reports"
            )

        return target_user

    def generate_leave_report(
        self,
        current_user: User,
        employee_id: Optional[int] = None
    ) -> Tuple[str, str]:
        """Generate 6-calendar-month CSV report and filename."""
        target_user = self.get_target_user_and_validate_access(current_user, employee_id)

        # Server-side 6 calendar months window
        to_date = date.today()
        from_date = to_date - relativedelta(months=6)

        # 1. Query Leave requests within window
        leave_stmt = select(LeaveRequest).where(
            LeaveRequest.user_id == target_user.id,
            LeaveRequest.date >= from_date,
            LeaveRequest.date <= to_date
        )
        leaves = list(self.db.scalars(leave_stmt).all())

        # 2. Query WFH requests overlapping window
        wfh_stmt = select(WfhRequest).where(
            WfhRequest.user_id == target_user.id,
            WfhRequest.end_date >= from_date,
            WfhRequest.start_date <= to_date
        )
        wfh_list = list(self.db.scalars(wfh_stmt).all())

        # Lookup deciders cache for email resolution
        decider_ids = {l.decided_by for l in leaves if l.decided_by} | {w.decided_by for w in wfh_list if w.decided_by}
        deciders_map: Dict[int, str] = {}
        if decider_ids:
            for d_id in decider_ids:
                u = self.user_repo.get_by_id(d_id)
                if u:
                    deciders_map[d_id] = u.email

        # Prepare normalized rows
        report_rows: List[Dict[str, Any]] = []

        # Process Leaves
        for l in leaves:
            report_rows.append({
                "date": l.date,
                "request_type": RequestTypeEnum.LEAVE.value,
                "leave_type": l.leave_type,
                "duration_type": l.duration_type,
                "half": l.half or "",
                "hours": str(l.hours) if l.hours is not None else "",
                "days_counted": l.days_counted,
                "status": l.status,
                "reason": l.reason or "",
                "decided_by": deciders_map.get(l.decided_by, "") if l.decided_by else "",
                "decided_at": l.decided_at.isoformat() if l.decided_at else "",
                "raw_request": l
            })

        # Process WFH requests: one row per working day
        one_day = timedelta(days=1)
        for w in wfh_list:
            cur = max(w.start_date, from_date)
            end_limit = min(w.end_date, to_date)
            while cur <= end_limit:
                if cur.weekday() < 5:  # Working day (Mon-Fri)
                    report_rows.append({
                        "date": cur,
                        "request_type": RequestTypeEnum.WFH.value,
                        "leave_type": "",
                        "duration_type": "",
                        "half": "",
                        "hours": "",
                        "days_counted": 1.0,
                        "status": w.status,
                        "reason": w.reason or "",
                        "decided_by": deciders_map.get(w.decided_by, "") if w.decided_by else "",
                        "decided_at": w.decided_at.isoformat() if w.decided_at else "",
                        "raw_request": w
                    })
                cur += one_day

        # Sort all rows chronologically, oldest first
        report_rows.sort(key=lambda r: r["date"])

        # Summary calculations
        # Total APPROVED leave days to 2 decimal places
        total_approved_leave_days = sum(
            l.days_counted for l in leaves if l.status == RequestStatusEnum.APPROVED.value
        )
        # Total approved WFH days (working days in window)
        total_approved_wfh_days = sum(
            1 for r in report_rows if r["request_type"] == RequestTypeEnum.WFH.value and r["status"] == RequestStatusEnum.APPROVED.value
        )

        # Count PENDING and REJECTED requests (distinct requests)
        all_unique_requests = list(leaves) + list(wfh_list)
        pending_count = sum(1 for req in all_unique_requests if req.status == RequestStatusEnum.PENDING.value)
        rejected_count = sum(1 for req in all_unique_requests if req.status == RequestStatusEnum.REJECTED.value)

        # Build CSV String
        output = io.StringIO()
        fieldnames = [
            "date",
            "request_type",
            "leave_type",
            "duration_type",
            "half",
            "hours",
            "days_counted",
            "status",
            "reason",
            "decided_by",
            "decided_at"
        ]
        writer = csv.writer(output, lineterminator="\n")
        # Write exact CSV header row
        writer.writerow(fieldnames)

        # Write data rows
        for row in report_rows:
            writer.writerow([
                row["date"].isoformat(),
                row["request_type"],
                row["leave_type"],
                row["duration_type"],
                row["half"],
                row["hours"],
                row["days_counted"],
                row["status"],
                row["reason"],
                row["decided_by"],
                row["decided_at"]
            ])

        # Blank line
        writer.writerow([])

        # Summary block
        writer.writerow(["SUMMARY"])
        writer.writerow(["Total Approved Leave Days", f"{total_approved_leave_days:.2f}"])
        writer.writerow(["Total Approved WFH Days", total_approved_wfh_days])
        writer.writerow(["Pending Requests Count", pending_count])
        writer.writerow(["Rejected Requests Count", rejected_count])

        csv_content = output.getvalue()
        output.close()

        # Filename: leave_report_<email>_<from>_<to>.csv
        filename = f"leave_report_{target_user.email}_{from_date.isoformat()}_{to_date.isoformat()}.csv"
        return csv_content, filename
