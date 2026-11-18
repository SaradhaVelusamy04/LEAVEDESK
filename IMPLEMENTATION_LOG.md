# LeaveDesk — Implementation Log

This log tracks every completed milestone, code additions, architectural decisions, and verification steps taken throughout the development of LeaveDesk.

---

## Milestone 0: Project Analysis, Architecture & Planning

* **Status:** Complete
* **Date:** 2026-11-18
* **Author:** Senior Backend Engineer & System Architect

### 1. Activities Completed
1. Located and read the complete 7-page assignment specification PDF (`IQG_Intern_Assignment_Backend_API.pdf`).
2. Copied the PDF to the root workspace directory `D:\LEAVEDESK\IQG_Intern_Assignment_Backend_API.pdf` for direct accessibility.
3. Inspected the workspace environment and host runtime (Python 3.13.14, Git 2.55.0, Docker Desktop 29.8.2).
4. Synthesized all functional requirements across Sections 1 to 6.
5. Formulated the Clean Architecture & Modular Monolith architecture design.
6. Designed concurrency strategy using row-level pessimistic locking (`SELECT ... FOR UPDATE`) to prevent concurrent leave/WFH overlap race conditions.
7. Prepared foundational governance and planning documents:
   - `PROJECT_PLAN.md`
   - `ARCHITECTURE.md`
   - `REQUIREMENT_TRACEABILITY.md`
   - `ASSUMPTIONS.md`
   - `IMPLEMENTATION_LOG.md`

---

## Milestone 1: Foundation, Environment & Core Scaffolding

* **Status:** Complete
* **Date:** 2026-11-18
* **Author:** Senior Backend Engineer

### 1. Activities Completed
1. Initialized Git repository and configured `.gitignore` for Python, virtual environments, SQLite, and IDE files.
2. Created `.venv` virtual environment and installed pinned dependencies from `requirements.txt` (`FastAPI 0.115.8`, `SQLAlchemy 2.0.38`, `Alembic 1.14.1`, `bcrypt 4.2.1`, `python-jose 3.4.0`, `pydantic 2.10.6`, `pytest 8.3.4`, etc.).
3. Configured environment variables loader `app/core/config.py` using `pydantic-settings` and created `.env.example`.
4. Configured SQLAlchemy 2.x engine, connection pool, declarative base, and session generator in `app/core/database.py`.
5. Created centralized exception handlers in `app/core/exceptions.py` for uniform error responses (401, 403, 404, 409, 422, 500) preventing traceback leakage.
6. Implemented bcrypt password hashing and JWT encoding/decoding utilities in `app/core/security.py`.
7. Created FastAPI application factory in `app/main.py` with CORS middleware, exception handlers, and API docs.
8. Implemented public `GET /health` in `app/api/v1/health.py` with active database connection validation.
9. Initialized and configured Alembic environment in `alembic.ini` and `alembic/env.py`.
10. Built test configuration in `pytest.ini` and `tests/conftest.py` with TestClient fixture.
11. Executed and verified test suite in `tests/test_health.py` (3/3 passed).

---

## Milestone 2: Authentication, Users & Seed Data

* **Status:** Complete
* **Date:** 2026-11-18
* **Author:** Senior Backend Engineer

### 1. Activities Completed
1. Implemented domain enumerations in `app/domain/enums.py` (`RoleEnum`, `LeaveTypeEnum`, `DurationTypeEnum`, `HalfEnum`, `RequestStatusEnum`, `RequestTypeEnum`).
2. Implemented `User` SQLAlchemy model in `app/models/user.py` with email indexing, role mapping, and self-referential `manager` / `direct_reports` hierarchy.
3. Created Pydantic DTO schemas in `app/schemas/auth.py` (`LoginRequest`, `TokenResponse`, `UserResponse`) with regex-based RFC-compliant email validation supporting `.test` domains.
4. Created `UserRepository` in `app/repositories/user_repo.py` implementing clean database access queries.
5. Implemented `AuthService` in `app/services/auth_service.py` with identical generic 401 error message for bad password and unknown email.
6. Implemented FastAPI dependencies in `app/api/deps.py`:
   - `get_current_user`: extracts Bearer token, validates claims, loads user from database.
   - `require_role("manager")`: verifies caller role and returns 403 Forbidden for unauthorized roles.
7. Implemented authentication router in `app/api/v1/auth.py`:
   - `POST /auth/login` (generates JWT bearer token).
   - `GET /auth/me` (returns caller profile without password hash).
8. Implemented database seeding script `seed.py` creating Priya Manager, Arjun Employee, and Meera Employee.
9. Authored initial Alembic database migration `alembic/versions/0001_create_users_table.py`.
10. Authored comprehensive test suite in `tests/test_auth.py` covering all Section 1 requirements (11/11 passed).

---

## Milestone 3: Leave & Work-From-Home (WFH) Management

* **Status:** Complete
* **Date:** 2026-11-18
* **Author:** Senior Backend Engineer

### 1. Activities Completed
1. Implemented domain validation and calculation rules in `app/domain/rules.py` for leave durations and WFH working days (Monday-Friday, max 2 working days).
2. Implemented centralized state machine in `app/domain/state_machine.py` enforcing `PENDING -> APPROVED/REJECTED/CANCELLED` and rejecting invalid transitions with 409 Conflict.
3. Implemented SQLAlchemy entities: `LeaveRequest` and `WfhRequest`.
4. Created Alembic migration `alembic/versions/0002_create_leave_and_wfh_tables.py`.
5. Created Pydantic DTOs: `LeaveCreateRequest`, `LeaveResponse`, `WfhCreateRequest`, `WfhResponse`.
6. Built database repositories: `LeaveRepository` and `WfhRepository`.
7. Implemented application services with user-level pessimistic locking (`with_for_update`) to eliminate overlap race conditions (`LeaveService`, `WfhService`).
8. Implemented API routers: `app/api/v1/leaves.py` and `app/api/v1/wfh.py`.
9. Authored comprehensive test suites: `tests/test_leaves.py` and `tests/test_wfh.py`.
10. Executed and verified test suite: 26/26 tests passed.

---

## Milestone 4: Manager Approval Workflow & State Machine

* **Status:** Complete
* **Date:** 2026-11-18
* **Author:** Senior Backend Engineer

### 1. Activities Completed
1. Extended `LeaveRepository` and `WfhRepository` with `get_team_leaves` and `get_team_wfh` supporting direct reports scoping and filters (`status`, `employee_id`, `from_date`, `to_date`).
2. Implemented `ManagerService` in `app/services/manager_service.py`:
   - `get_review_queue`: aggregates leave and WFH requests for manager's direct reports, default `status=PENDING`.
   - `decide_leave`: enforces direct-report authorization check (403 for non-reports), centralized state transition check (409 for non-pending), rejection comment length validation (min 5 chars), and audit recording (`decided_by`, `decided_at` UTC, `decision_comment`).
   - `decide_wfh`: enforces same direct-report authorization, state transition, and audit trail rules for WFH requests.
3. Implemented presentation DTOs in `app/schemas/manager.py`:
   - `DecisionApproveRequest` (optional comment)
   - `DecisionRejectRequest` (mandatory comment with >= 5 chars validation)
   - `ManagerRequestsResponse`
4. Implemented manager API router in `app/api/v1/manager.py`:
   - `GET /manager/requests`
   - `POST /manager/leaves/{id}/approve` & `POST /manager/leaves/{id}/reject`
   - `POST /manager/wfh/{id}/approve` & `POST /manager/wfh/{id}/reject`
   - Protected with `require_role("manager")` dependency.
5. Registered `manager_router` in `app/main.py`.
6. Authored comprehensive test suite in `tests/test_manager.py`:
   - Review queue defaults to PENDING and returns direct reports only.
   - Non-manager (employee) receives 403 Forbidden on all manager routes.
   - Manager approving leave records full audit trail.
   - Manager rejecting leave requires at least 5 characters (422 on empty or short comment).
   - Manager attempting to decide another team's request receives 403 Forbidden.
   - Deciding an already decided request returns 409 Conflict.
   - Manager approving WFH requests.
7. Executed full test suite: 33/33 tests passed.

---

## Milestone 5: Reporting Engine (6-Month CSV Export)

* **Status:** Complete
* **Date:** 2026-11-18
* **Author:** Senior Backend Engineer

### 1. Activities Completed
1. Implemented server-side 6-calendar-month date window calculation in `ReportService` using `dateutil.relativedelta` (`from_date = today - relativedelta(months=6)` to `to_date = today`).
2. Built aggregation query layer across `LeaveRequest` and `WfhRequest` records for the target employee within the 6-month window.
3. Implemented multi-day WFH row expansion: generates one individual row per working day (Monday-Friday) with `request_type=WFH` and `days_counted=1.0`.
4. Structured CSV generation according to exact specification:
   - Header: `date,request_type,leave_type,duration_type,half,hours,days_counted,status,reason,decided_by,decided_at`
   - Data rows sorted chronologically oldest first.
   - Decider email resolved for `decided_by` column.
   - Blank line separator.
   - Summary block: Total APPROVED leave days (2 decimal places), total approved WFH days, count of PENDING and REJECTED requests.
5. Implemented role-based access control in `GET /reports/leaves`:
   - Employees can only download their own report.
   - Passing `?employee_id=<id>` by a non-manager returns 403 Forbidden.
   - Managers can pass `?employee_id=<id>` for direct reports; accessing another manager's direct report returns 403 Forbidden.
   - Handles empty history gracefully: returns valid CSV with header and zero-valued summary block without error.
6. Implemented endpoint `GET /reports/leaves` in `app/api/v1/reports.py` with `Content-Type: text/csv` and `Content-Disposition: attachment; filename=leave_report_<email>_<from>_<to>.csv`.
7. Generated verified `sample_report.csv` from a clean sample run.
8. Authored comprehensive test suite in `tests/test_reports.py` (3 test scenarios).
9. Executed full test suite: 36/36 tests passed.

### 2. Files Created or Modified
* `app/services/report_service.py` (Created)
* `app/api/v1/reports.py` (Created)
* `app/main.py` (Registered `reports_router`)
* `sample_report.csv` (Generated & Verified)
* `tests/test_reports.py` (Created)

### 3. Key Technical Decisions
* **Strict Server-Side Window:** Rejected client-side date tampering by computing the 6-calendar-month boundary exclusively on the server using `dateutil.relativedelta`.
* **WFH Multi-Day Expansion:** Decomposed WFH spans into discrete working day instances so leave and WFH rows can be chronologically interleaved and accurately aggregated.
* **Dual Download Modes:** Seamlessly supported employee self-service and managerial team auditing through single endpoint with permission checking.

### 4. Tests Executed & Results
* Ran full test suite across all modules: 36 passed in 22.30s.

### 5. Next Milestone
* **Milestone 6 — DevOps, Documentation & Final Engineering Quality:**
  - Author multi-stage, secure `Dockerfile`.
  - Author `docker-compose.yml` for backend API and PostgreSQL services with health check dependencies.
  - Author exhaustive, production-grade `README.md`.
  - Perform full test regression and clean workspace check.
  - Final requirement traceability matrix audit.
