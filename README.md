# LeaveDesk — Employee Leave & Work-From-Home Management API

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.8-green.svg)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.38-red.svg)](https://www.sqlalchemy.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
[![Tests](https://img.shields.io/badge/Tests-36%20Scenarios-brightgreen.svg)]()

> **IQuantsGraph Pvt Ltd — Python Backend Engineering Intern Assignment**  
> Reference: `IQG-ENG-INTERN-API`

---

## 1. Project Overview

**LeaveDesk** is a RESTful API designed to automate and streamline employee leave and Work-From-Home (WFH) management.

The system provides role-based access control (RBAC), multiple leave duration types (`FULL_DAY`, `HALF_DAY`, `HOURS`), working-day calculations, request overlap validation, centralized request state transitions, manager review workflows, and six-month historical CSV reporting.

## 2. Architecture & Design Principles

LeaveDesk follows a **Modular Monolith** architecture inspired by **Clean Architecture** principles. It remains a single deployable application while separating presentation, application, domain, and infrastructure responsibilities.

```text
+--------------------------------------------------------------------------+
|                         Presentation Layer                               |
|       FastAPI Routers - Pydantic Schemas - Authentication Dependencies  |
|                    OpenAPI / Swagger Documentation                      |
+------------------------------------+-------------------------------------+
                                     |
                                     v
+--------------------------------------------------------------------------+
|                         Application Layer                                |
|           Services - Business Workflow Orchestration                     |
|                  Request State Transition Logic                          |
+------------------------------------+-------------------------------------+
                                     |
                                     v
+--------------------------------------------------------------------------+
|                            Domain Layer                                  |
|           Business Rules - Enums - Duration Calculations                 |
|                    Overlap Validation - State Rules                      |
+------------------------------------+-------------------------------------+
                                     |
                                     v
+--------------------------------------------------------------------------+
|                        Infrastructure Layer                              |
|       SQLAlchemy Models - Repositories - PostgreSQL - Alembic             |
|                    Password Hashing - JWT Security                      |
+--------------------------------------------------------------------------+
```

### Key Architectural Highlights

- **Repository Pattern:** Database access is encapsulated in repository classes such as `UserRepository`, `LeaveRepository`, and `WfhRepository`, keeping query logic separate from service orchestration.
- **Centralized State Machine:** Request lifecycle transitions (`PENDING -> APPROVED`, `PENDING -> REJECTED`, and `PENDING -> CANCELLED`) are managed through `RequestStateMachine`. Invalid transitions are rejected with HTTP 409 Conflict.
- **Concurrency Control:** Leave and WFH submissions use user-level row locking (`SELECT ... FOR UPDATE`) during conflict validation when supported by the database, helping serialize concurrent submissions for the same user.
- **Consistent Access Control:** Generic login failure responses prevent account enumeration. Requests for resources belonging to other employees return 404 where required by the assignment, while unauthorized role or manager access returns 403.

## 3. Technology Stack

| Category | Technology |
|---|---|
| Language | Python 3.11+ |
| API Framework | FastAPI 0.115.8 |
| Web Server | Uvicorn 0.34.0 |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0.38 |
| Database Driver | Psycopg2-binary 2.9.10 |
| Schema Migrations | Alembic 1.14.1 |
| Data Validation | Pydantic 2.10.6 |
| Configuration | Pydantic Settings 2.7.1 |
| Authentication | JWT using python-jose 3.4.0 |
| Password Hashing | bcrypt 4.2.1 |
| Date Utilities | python-dateutil 2.9.0 |
| Testing | Pytest 8.3.4, HTTPX 0.28.1 |
| Containerization | Docker and Docker Compose |

## 4. Project Directory Structure

```
d:\LEAVEDESK\
├── alembic\                       # Database migration environment
│   ├── versions\                  # Migration scripts (0001_users, 0002_leave_wfh)
│   └── env.py                     # SQLAlchemy metadata configuration
├── app\
│   ├── api\                       # Presentation Layer
│   │   ├── deps.py                # Security and authentication dependencies
│   │   └── v1\
│   │       ├── auth.py            # POST /auth/login, GET /auth/me
│   │       ├── leaves.py          # POST /leaves, GET /leaves/me, cancel
│   │       ├── wfh.py             # POST /wfh, GET /wfh/me, cancel
│   │       ├── manager.py         # GET /manager/requests, approve, reject
│   │       ├── reports.py         # GET /reports/leaves
│   │       └── health.py          # GET /health
│   ├── core\                      # Core Infrastructure
│   │   ├── config.py              # Pydantic Settings configuration
│   │   ├── database.py            # SQLAlchemy engine, sessionmaker, base
│   │   ├── exceptions.py          # Centralized error handlers (401, 403, 404, 409, 422, 500)
│   │   └── security.py            # Bcrypt hashing & JWT signing
│   ├── domain\                    # Domain Business Layer
│   │   ├── enums.py               # Roles, Leave types, Durations, Status enums
│   │   ├── rules.py               # Leave duration calculator & working-day rules
│   │   └── state_machine.py       # Centralized RequestStateMachine
│   ├── models\                    # SQLAlchemy ORM Entities
│   │   ├── user.py                # User model with self-referential hierarchy
│   │   ├── leave.py               # LeaveRequest model
│   │   └── wfh.py                 # WfhRequest model
│   ├── repositories\              # Data Access Layer
│   │   ├── user_repo.py
│   │   ├── leave_repo.py
│   │   └── wfh_repo.py
│   ├── schemas\                   # Pydantic DTO Schemas
│   │   ├── auth.py
│   │   ├── leave.py
│   │   ├── wfh.py
│   │   └── manager.py
│   ├── services\                  # Application Orchestration Layer
│   │   ├── auth_service.py
│   │   ├── leave_service.py
│   │   ├── wfh_service.py
│   │   ├── manager_service.py
│   │   └── report_service.py
│   └── main.py                    # FastAPI application factory & middleware
├── tests\                         # Pytest Automated Test Suite
│   ├── conftest.py                # DB fixtures, TestClient setup
│   ├── test_health.py             # Health check tests
│   ├── test_auth.py               # Authentication and role enforcement tests
│   ├── test_leaves.py             # Leave duration, overlap, and cancel tests
│   ├── test_wfh.py                # WFH working-day rules and cancel tests
│   ├── test_manager.py            # Review queue and approval/rejection tests
│   └── test_reports.py            # CSV report generation & access control tests
├── .env.example                   # Environment configuration template
├── .gitignore                     # Git ignore rules
├── alembic.ini                    # Alembic configuration
├── Dockerfile                     # Multi-stage container definition
├── docker-compose.yml             # Orchestration for PostgreSQL + API
├── requirements.txt               # Pinned dependencies
├── seed.py                        # Database seed script
├── sample_report.csv              # Verified exported sample CSV
├── ARCHITECTURE.md                # System architecture documentation
├── ASSUMPTIONS.md                 # Explicit design assumptions
├── PROJECT_PLAN.md                # Implementation roadmap
├── REQUIREMENT_TRACEABILITY.md    # 1:1 Requirement verification matrix
└── IMPLEMENTATION_LOG.md          # Chronological milestone execution log
```

---

## 5. Local Setup & Installation

### Prerequisites
* Python 3.11+
* PostgreSQL (or Docker)
* Git

### Installation Steps

**1. Clone the repository**

```bash
git clone <repository-url>
cd LEAVEDESK
```

2. **Create and Activate Virtual Environment:**
   ```bash
   # Windows
   python -m venv .venv
   .\.venv\Scripts\activate

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

**3. Install dependencies**

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. **Configure Environment Variables:**
   ```bash
   cp .env.example .env
   ```
   *(Update `DATABASE_URL` with your local PostgreSQL credentials if running without Docker).*

```bash
alembic upgrade head
```

**6. Seed initial test users**

```bash
python seed.py
```

**7. Start the application**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 7. Docker Deployment

## 6. Docker & Docker Compose Deployment

To run the complete production-ready stack (FastAPI backend + PostgreSQL) in isolated containers:

```bash
# Build and run containers in background
docker-compose up --build -d

# Check service logs
docker-compose logs -f

# Verify running containers
docker-compose ps
```

The application automatically runs migrations and seeds sample data upon startup. It is accessible at `http://localhost:8000`.

---

## 7. Interactive API Documentation (Swagger UI)

Open your web browser and navigate to:
* **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Testing in Swagger UI
1. Execute `POST /auth/login` using one of the seed accounts below.
2. Copy the returned `access_token`.
3. Click the **Authorize** button (top right of Swagger UI).
4. Enter token as: `Bearer <access_token>`.
5. Execute protected endpoints (`/leaves`, `/wfh`, `/manager/requests`, `/reports/leaves`).

---

## 8. Seed Data & Test Credentials

The database seed script (`seed.py`) configures the following organizational hierarchy:

| Name | Email | Role | Reports To | Password |
| :--- | :--- | :--- | :--- | :--- |
| **Priya Manager** | `priya.manager@leavedesk.test` | `manager` | *None* | `Manager@123` |
| **Arjun Employee**| `arjun@leavedesk.test` | `employee` | Priya Manager | `Employee@123` |
| **Meera Employee**| `meera@leavedesk.test` | `employee` | Priya Manager | `Employee@123` |

These credentials are for local development and testing only. Passwords are stored as bcrypt hashes in the database.

## 10. Test Execution & Coverage

The automated test suite is organized by functional area and covers authentication, authorization, leave and WFH rules, manager workflows, and CSV reporting.

Run all tests:

```bash
pytest
```

Run tests with detailed output:

```bash
pytest -v
```

*(Or without activating venv: `.\.venv\Scripts\pytest.exe -v`)*

### Verified Test Summary
* **Authentication Tests (`tests/test_auth.py`):** 8 passed (login, generic 401, expired tokens, tampered tokens, profile masking, 403 role enforcement, seed idempotency).
* **Health Check Tests (`tests/test_health.py`):** 3 passed (live DB probe, /api/v1 routing, 503 on DB drop).
* **Leave Management Tests (`tests/test_leaves.py`):** 8 passed (`FULL_DAY`, `HALF_DAY`, half-day coexistence, `HOURS` duration math, 422 rejected values, overlap 409 conflicts, chronological listing, owner-only cancellation).
* **WFH Management Tests (`tests/test_wfh.py`):** 7 passed (1-day, 2-day Friday-Monday spans, 422 on > 2 working days, weekend-only rejection, WFH overlap, FULL_DAY leave conflict, cancellation).
* **Manager Workflow Tests (`tests/test_manager.py`):** 7 passed (direct report queue, employee 403 blocks, approval audit trail, mandatory 5-char rejection comment, 403 for other teams, 409 on already-decided requests).
* **Reporting Tests (`tests/test_reports.py`):** 3 passed (empty report valid CSV, 6-month calculation, sorting, multi-day WFH row expansion, summary block, RBAC permissions).

---

## 10. Design Assumptions & Rationale

As instructed in Sections 8, 16, and 6.4 of the brief, key technical assumptions have been documented:

1. **Working Days Definition:**
   * Working days are defined strictly as Monday through Friday (`weekday() < 5`).
   * Weekends (Saturday and Sunday) are non-working days.
   * No static holiday calendar is assumed.
2. **WFH Spans:**
   * A WFH request from Friday to Monday comprises 2 working days (Friday and Monday), which is valid under the 2-working-day limit.
   * Requests covering 0 working days (e.g. Saturday to Sunday) are rejected with HTTP 422.
3. **Leave Duration & Overlap Rules:**
   * `FULL_DAY` blocks any active leave or WFH request on that date for the same user (409 Conflict).
   * `FIRST_HALF` and `SECOND_HALF` can coexist on the same date for the same user.
   * Two identical half-days conflict with HTTP 409.
   * `HOURS` leaves cannot overlap with `FULL_DAY` or another `HOURS` leave on the same date.
4. **Server-Side 6-Month Reporting Window:**
   * The reporting window is computed dynamically on the server: `today - relativedelta(months=6)` to `today`. Client-supplied date windows are never trusted.
   * Multi-day WFH requests are expanded to **one row per working day** in the CSV data rows with `request_type=WFH`, `days_counted=1.0`.
   * The CSV summary block computes total approved leave days to two decimal places, total approved WFH days, and counts of pending and rejected requests.

---

## 11. Known Limitations & Future Improvements

### Known Limitations

- **Public Holiday Integration:** The current working-day calculation treats all weekdays as working days. Regional and organizational holidays are not included.
- **Partial-Day Time Slots:** `HOURS` requests represent a number of hours but do not model specific start and end times. Therefore, time-slot-level collision detection is not implemented.

### Future Improvements
* **Configurable Working Calendar:** Support organizational holiday calendars via database configurations or third-party calendar APIs.
* **Email / Webhook Notifications:** Trigger background tasks (via Celery or FastAPI BackgroundTasks) to notify managers when new requests are submitted, and notify employees when decisions are finalized.
* **Pagination for Queue & History:** Introduce cursor-based or limit/offset pagination on `/manager/requests` and `/leaves/me` for large enterprise teams.
* **Audit Event Stream:** Implement append-only event logging for regulatory compliance and audit history.

---

## 12. Effort Spent per Assignment Section

| Section | Topic | Estimated Effort | Focus Areas |
| :--- | :--- | :--- | :--- |
| **Section 1** | Authentication & Roles | ~2.5 hours | Model hierarchy, Bcrypt hashing, JWT generation/validation, role dependencies, seed script. |
| **Section 2** | Leave & WFH Requests | ~4.0 hours | Duration calculations (`FULL_DAY`, `HALF_DAY`, `HOURS`), working days evaluator, overlap rules, user row locking. |
| **Section 3** | Manager Approval Workflow | ~2.5 hours | Team authorization checking, centralized State Machine, audit trails, comment validations. |
| **Section 4** | 6-Month CSV Reporting | ~2.5 hours | `relativedelta` window arithmetic, multi-day WFH row expansion, summary block formatting, stream responses. |
| **Section 5 & 6**| Architecture, DevOps, Docs & Tests | ~3.5 hours | Clean architecture layering, Docker & Compose, Alembic migrations, full 36-test suite, README. |
| **Total** | | **~15.0 hours** | |
