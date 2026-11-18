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
1. Implemented domain validation and calculation rules in `app/domain/rules.py`:
   - `validate_and_calculate_leave_days`: calculates days_counted (`FULL_DAY` = 1.0, `HALF_DAY` = 0.5, `HOURS` = hours / 8), and rejects invalid hours, fractional values, and mismatched combinations with 422.
   - `calculate_working_days`: evaluates working days (Monday-Friday) between `start_date` and `end_date` inclusive, enforcing between 1 and 2 working days (rejects 0 working days or > 2 working days with 422).
2. Implemented centralized state machine in `app/domain/state_machine.py` enforcing `PENDING -> APPROVED/REJECTED/CANCELLED` and rejecting invalid transitions with 409 Conflict.
3. Implemented SQLAlchemy entities:
   - `LeaveRequest` in `app/models/leave.py`
   - `WfhRequest` in `app/models/wfh.py`
4. Created Alembic migration `alembic/versions/0002_create_leave_and_wfh_tables.py`.
5. Created Pydantic DTOs:
   - `LeaveCreateRequest` and `LeaveResponse` in `app/schemas/leave.py`
   - `WfhCreateRequest` and `WfhResponse` in `app/schemas/wfh.py`
6. Built database repositories:
   - `LeaveRepository` in `app/repositories/leave_repo.py`
   - `WfhRepository` in `app/repositories/wfh_repo.py`
7. Implemented application services with user-level pessimistic locking (`with_for_update`) to eliminate overlap race conditions:
   - `LeaveService` in `app/services/leave_service.py`
   - `WfhService` in `app/services/wfh_service.py`
8. Implemented API routers in presentation layer:
   - `POST /leaves`, `GET /leaves/me`, `POST /leaves/{id}/cancel` in `app/api/v1/leaves.py`
   - `POST /wfh`, `GET /wfh/me`, `POST /wfh/{id}/cancel` in `app/api/v1/wfh.py`
9. Registered endpoints in `app/main.py`.
10. Authored comprehensive test suites:
    - `tests/test_leaves.py` (8 test scenarios)
    - `tests/test_wfh.py` (7 test scenarios)
11. Executed and verified test suite: 26/26 tests passed.

### 2. Files Created or Modified
* `app/domain/rules.py` (Created)
* `app/domain/state_machine.py` (Created)
* `app/models/leave.py` (Created)
* `app/models/wfh.py` (Created)
* `app/schemas/leave.py` (Created)
* `app/schemas/wfh.py` (Created)
* `app/repositories/leave_repo.py` (Created)
* `app/repositories/wfh_repo.py` (Created)
* `app/services/leave_service.py` (Created)
* `app/services/wfh_service.py` (Created)
* `app/api/v1/leaves.py` (Created)
* `app/api/v1/wfh.py` (Created)
* `app/main.py` (Updated to register leave and wfh routers)
* `alembic/versions/0002_create_leave_and_wfh_tables.py` (Created)
* `tests/conftest.py` (Updated fixture for clean DB isolation)
* `tests/test_leaves.py` (Created)
* `tests/test_wfh.py` (Created)

### 3. Key Technical Decisions
* **Duration Rule Enforcement:** Delegated duration calculation to pure domain functions (`app/domain/rules.py`), executing before database queries.
* **Concurrency Locking:** Serialized concurrent leave/WFH submissions per user using row-level pessimistic locking (`with_for_update`), preventing simultaneous conflicting submissions.
* **Resource Privacy:** Enforced 404 Not Found (instead of 403) when attempting to access or cancel requests owned by another user, preventing resource enumeration.

### 4. Tests Executed & Results
* Ran full test suite across all modules: 26 passed in 13.82s.

### 5. Next Milestone
* **Milestone 4 — Manager Approval Workflow:**
  - Build `GET /manager/requests` returning direct reports' requests (defaults to `status=PENDING`, optional filters: `status`, `employee_id`, `from_date`, `to_date`).
  - Build decision endpoints:
    - `POST /manager/leaves/{id}/approve` & `POST /manager/leaves/{id}/reject`
    - `POST /manager/wfh/{id}/approve` & `POST /manager/wfh/{id}/reject`
  - Enforce role check: manager only (403 for employees).
  - Enforce hierarchy check: direct reports only (403 for requests outside manager's team).
  - Enforce rejection comment minimum length (>= 5 characters).
  - Enforce state machine (deciding non-pending request returns 409 Conflict).
  - Record audit trail: `decided_by`, `decided_at` (UTC timestamp), and `decision_comment`.
  - Author comprehensive test suite in `tests/test_manager.py`.
