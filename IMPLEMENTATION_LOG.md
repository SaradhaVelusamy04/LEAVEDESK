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

### 2. Files Created or Modified
* `.gitignore`
* `.env.example`
* `requirements.txt`
* `pytest.ini`
* `app/__init__.py`
* `app/core/__init__.py`
* `app/core/config.py`
* `app/core/database.py`
* `app/core/exceptions.py`
* `app/core/security.py`
* `app/api/__init__.py`
* `app/api/v1/__init__.py`
* `app/api/v1/health.py`
* `app/main.py`
* `alembic.ini`
* `alembic/env.py`
* `alembic/script.py.mako`
* `tests/conftest.py`
* `tests/test_health.py`

### 3. Key Technical Decisions
* **Bcrypt & JWT:** Used `bcrypt` directly with work factor 12 and `python-jose` for JWT signing, ensuring zero reliance on deprecated standard library modules.
* **Unified Error Schemas:** Enforced standard `{ "detail": "..." }` responses across all exception types (including validation and internal server errors) so clients always receive consistent error structures.
* **Health Check Probe:** `GET /health` runs `SELECT 1` against the database; returns 200 `{"status": "ok"}` on success and 503 `{"status": "error", "detail": "Database connection failed"}` if connectivity drops.

### 4. Tests Executed & Results
* `tests/test_health.py::test_health_check_success` -> PASSED
* `tests/test_health.py::test_health_check_api_v1` -> PASSED
* `tests/test_health.py::test_health_check_db_failure` -> PASSED
* Overall: 3 passed in 0.05s.

### 5. Next Milestone
* **Milestone 2 — Authentication, Users & Seed Data:**
  - Define `User` SQLAlchemy model with role enum and `reports_to_id` self-referential relationship.
  - Generate initial Alembic migration for users table.
  - Implement Pydantic auth schemas (`LoginRequest`, `TokenResponse`, `UserResponse`).
  - Implement `POST /auth/login` and `GET /auth/me`.
  - Implement FastAPI dependencies `get_current_user` and `require_role("manager")`.
  - Create database seeding script `seed.py` with Priya, Arjun, and Meera.
  - Author and run comprehensive authentication test suite.
