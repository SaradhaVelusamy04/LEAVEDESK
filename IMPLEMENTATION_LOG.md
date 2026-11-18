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
8. Implemented database seeding script `seed.py` creating:
   - Priya Manager (`priya.manager@leavedesk.test`, role: `manager`, reports_to: None)
   - Arjun Employee (`arjun@leavedesk.test`, role: `employee`, reports_to: Priya)
   - Meera Employee (`meera@leavedesk.test`, role: `employee`, reports_to: Priya)
9. Authored initial Alembic database migration `alembic/versions/0001_create_users_table.py`.
10. Authored comprehensive test suite in `tests/test_auth.py` covering all Section 1 requirements:
    - Successful login for employees and managers.
    - Uniform 401 response for wrong password and unknown email.
    - Expired token handling (401).
    - Tampered token handling (401).
    - Profile endpoint without password hash exposure.
    - Role-based 403 enforcement for employees accessing manager routes.
    - Seed script execution and idempotency.

### 2. Files Created or Modified
* `app/domain/enums.py` (Created)
* `app/models/user.py` (Created)
* `app/schemas/auth.py` (Created)
* `app/repositories/user_repo.py` (Created)
* `app/services/auth_service.py` (Created)
* `app/api/deps.py` (Created)
* `app/api/v1/auth.py` (Created)
* `app/main.py` (Updated to register auth router)
* `seed.py` (Created)
* `alembic/versions/0001_create_users_table.py` (Created)
* `tests/test_auth.py` (Created)
* `requirements.txt` (Added `email-validator`)

### 3. Key Technical Decisions
* **Bcrypt Password Security:** Ensured password hashes are created with 12 rounds of salt and never stored or returned in plain text.
* **Enumeration and Hierarchy:** Built self-referential adjacency list model in SQLAlchemy to cleanly represent managerial hierarchy (`reports_to_id`).
* **Generic 401 Responses:** Standardized detail message `"Invalid email or password"` to prevent user enumeration attacks.
* **Email Validation:** Handled `.test` top-level domains specified in assignment instructions without DNS deliverability rejection.

### 4. Tests Executed & Results
* Ran pytest across all suites: 11 passed in 3.65s (`test_health.py` and `test_auth.py`).

### 5. Next Milestone
* **Milestone 3 — Leave & Work-From-Home (WFH) Management:**
  - Create `LeaveRequest` and `WfhRequest` SQLAlchemy models.
  - Generate Alembic migration for leave and WFH tables.
  - Implement duration calculation logic (`FULL_DAY`, `HALF_DAY`, `HOURS`) in domain rules.
  - Implement WFH date range and 2-working-days validation.
  - Implement concurrency-safe overlap detection using row-level pessimistic locking (`FOR UPDATE`).
  - Implement endpoints: `POST /leaves`, `GET /leaves/me`, `POST /leaves/{id}/cancel`, `POST /wfh`, `GET /wfh/me`, `POST /wfh/{id}/cancel`.
  - Author comprehensive test suite in `tests/test_leaves.py` and `tests/test_wfh.py`.
