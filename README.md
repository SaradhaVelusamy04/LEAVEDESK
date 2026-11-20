# LeaveDesk — Employee Leave & Work-From-Home Management API

[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/FastAPI-0.115.8-green.svg)](https://fastapi.tiangolo.com/)
[![ORM](https://img.shields.io/badge/SQLAlchemy-2.0.38-red.svg)](https://www.sqlalchemy.org/)
[![Database](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
[![Tests](https://img.shields.io/badge/Tests-36%20Passed-brightgreen.svg)]()

> **IQuantsGraph Pvt Ltd — Python Backend Engineering Intern Assignment**  
> Reference: `IQG-ENG-INTERN-API`  
> Author: Senior Backend Engineering & System Architecture Implementation

---

## 1. Project Overview

**LeaveDesk** is an enterprise-grade RESTful API designed to automate and streamline employee leave and Work-From-Home (WFH) management.
The system provides role-based access control (RBAC), multi-format leave duration calculations (`FULL_DAY`, `HALF_DAY`, `HOURS`), working-day business logic, concurrency-safe overlap checking, centralized request state transitions, manager review workflows, and 6-month historical CSV reporting.

---

## 2. Architecture & Design Principles

LeaveDesk is designed as a **Modular Monolith** adhering to **Clean Architecture** principles. It remains a single deployable unit while isolating concerns across decoupled layers:

```
+--------------------------------------------------------------------------+
|                            Presentation Layer                            |
|          FastAPI Routers - Pydantic Request/Response Schemas             |
|          Auth & Role Dependencies - OpenAPI/Swagger Documentation        |
+------------------------------------+-------------------------------------+
                                     |
                                     v
+--------------------------------------------------------------------------+
|                            Application Layer                             |
|          Service Orchestrators (Auth, Leave, WFH, Manager, Report)       |
|          Centralized Status Transition State Machine                     |
+------------------------------------+-------------------------------------+
                                     |
                                     v
+--------------------------------------------------------------------------+
|                              Domain Layer                                |
|          Business Entities & Value Objects - Enumerations                |
|          Duration Calculations - Overlap Rules - Domain Exceptions       |
+------------------------------------+-------------------------------------+
                                     ^
                                     | (Dependency Inversion)
+------------------------------------+-------------------------------------+
|                          Infrastructure Layer                            |
|          SQLAlchemy 2.x Declarative Models & Repositories                |
|          PostgreSQL Database Connections & Sessions                      |
|          Alembic Migrations - Cryptography (Bcrypt / JWT)                |
+--------------------------------------------------------------------------+
```

### Key Architectural Highlights
* **Repository Pattern:** Database queries are encapsulated in repository classes (`UserRepository`, `LeaveRepository`, `WfhRepository`), decoupling business logic from ORM queries.
* **Centralized State Machine:** Lifecycle transitions (`PENDING -> APPROVED`, `PENDING -> REJECTED`, `PENDING -> CANCELLED`) are governed by `RequestStateMachine`. Direct or invalid transitions are strictly rejected with HTTP 409 Conflict.
* **Concurrency-Safe Overlap Prevention:** Implements **pessimistic row locking on the user record** (`SELECT ... FOR UPDATE`) during leave and WFH submissions. This eliminates concurrent submission race conditions per user without incurring database-wide lock contention.
* **Zero Information Leakage:** Generic 401 messages prevent account enumeration on login, and 404 Not Found is returned when attempting to access other users' requests to conceal resource IDs.

---

## 3. Technology Stack

* **Language:** Python 3.11+ (verified up to 3.13)
* **API Framework:** FastAPI 0.115.8
* **Web Server:** Uvicorn 0.34.0 (with uvloop/httptools)
* **Database & ORM:** PostgreSQL 16, SQLAlchemy 2.0.38, Psycopg2-binary 2.9.10
* **Schema Migrations:** Alembic 1.14.1
* **Data Validation:** Pydantic 2.10.6 & Pydantic-Settings 2.7.1
* **Authentication & Cryptography:** JWT (`python-jose 3.4.0`) & `bcrypt 4.2.1`
* **Date Utilities:** `python-dateutil 2.9.0`
* **Testing:** Pytest 8.3.4 & HTTPX 0.28.1 (FastAPI TestClient)
* **DevOps:** Docker & Docker Compose

---

## 4. Project Directory Structure

```
LEAVEDESK/
├── alembic/                       # Database migration environment
│   ├── versions/                  # Migration scripts (0001_users, 0002_leave_wfh)
│   ├── env.py                     # SQLAlchemy metadata configuration
│   └── script.py.mako             # Migration template
├── app/
│   ├── api/                       # Presentation Layer
│   │   ├── deps.py                # Security and authentication dependencies
│   │   └── v1/
│   │       ├── auth.py            # POST /auth/login, GET /auth/me
│   │       ├── leaves.py          # POST /leaves, GET /leaves/me, cancel
│   │       ├── wfh.py             # POST /wfh, GET /wfh/me, cancel
│   │       ├── manager.py         # GET /manager/requests, approve, reject
│   │       ├── reports.py         # GET /reports/leaves
│   │       └── health.py          # GET /health
│   ├── core/                      # Core Infrastructure
│   │   ├── config.py              # Pydantic Settings configuration
│   │   ├── database.py            # SQLAlchemy engine, sessionmaker, base
│   │   ├── exceptions.py          # Centralized error handlers (401, 403, 404, 409, 422, 500)
│   │   └── security.py            # Bcrypt hashing & JWT signing
│   ├── domain/                    # Domain Business Layer
│   │   ├── enums.py               # Roles, Leave types, Durations, Status enums
│   │   ├── rules.py               # Leave duration calculator & working-day rules
│   │   └── state_machine.py       # Centralized RequestStateMachine
│   ├── models/                    # SQLAlchemy ORM Entities
│   │   ├── user.py                # User model with self-referential hierarchy
│   │   ├── leave.py               # LeaveRequest model
│   │   └── wfh.py                 # WfhRequest model
│   ├── repositories/              # Data Access Layer
│   │   ├── user_repo.py
│   │   ├── leave_repo.py
│   │   └── wfh_repo.py
│   ├── schemas/                   # Pydantic DTO Schemas
│   │   ├── auth.py
│   │   ├── leave.py
│   │   ├── wfh.py
│   │   └── manager.py
│   ├── services/                  # Application Orchestration Layer
│   │   ├── auth_service.py
│   │   ├── leave_service.py
│   │   ├── wfh_service.py
│   │   ├── manager_service.py
│   │   └── report_service.py
│   └── main.py                    # FastAPI application factory & middleware
├── Documentation/                 # Engineering Specifications & Planning Documents
│   ├── ARCHITECTURE.md            # Clean Architecture specification, ERD & concurrency design
│   ├── ASSUMPTIONS.md             # Documented business rules & edge case interpretations
│   ├── IMPLEMENTATION_LOG.md      # Chronological milestone execution log & audit history
│   ├── IQG_Intern_Assignment_Backend_API.pdf # Assignment specification document (PDF)
│   ├── PROJECT_PLAN.md            # 7-milestone delivery roadmap & technology rationale
│   └── REQUIREMENT_TRACEABILITY.md # 1:1 Requirement verification matrix (36/36 tests verified)
├── tests/                         # Pytest Automated Test Suite
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
├── pytest.ini                     # Pytest configuration
├── requirements.txt               # Pinned dependencies
├── sample_report.csv              # Verified exported sample CSV
├── seed.py                        # Database seed script
└── README.md                      # Project documentation (this file)
```

---

## 5. Engineering Documentation & Specifications

All core architectural and project governance documents are maintained inside the [`Documentation/`](Documentation/) directory:

* 📐 [**System Architecture (`Documentation/ARCHITECTURE.md`)**](Documentation/ARCHITECTURE.md) — Modular monolith structure, Clean Architecture layers, ERD schema design, and user-level pessimistic locking (`FOR UPDATE`).
* 📋 [**Requirement Traceability Matrix (`Documentation/REQUIREMENT_TRACEABILITY.md`)**](Documentation/REQUIREMENT_TRACEABILITY.md) — 1:1 mapping of every requirement from the PDF brief to code modules with 100% verified test coverage.
* 📝 [**Design Assumptions (`Documentation/ASSUMPTIONS.md`)**](Documentation/ASSUMPTIONS.md) — Explicit domain interpretations for Monday–Friday working days, multi-day WFH spans, partial-day `HOURS` overlap policy, and server-side 6-month calendar calculations.
* 🗺️ [**Project Delivery Plan (`Documentation/PROJECT_PLAN.md`)**](Documentation/PROJECT_PLAN.md) — 7-milestone incremental implementation roadmap and technology decision records.
* 📜 [**Implementation Log (`Documentation/IMPLEMENTATION_LOG.md`)**](Documentation/IMPLEMENTATION_LOG.md) — Step-by-step engineering log tracking changes, decisions, and testing milestones.
* 📄 [**Assignment Brief (`Documentation/IQG_Intern_Assignment_Backend_API.pdf`)**](Documentation/IQG_Intern_Assignment_Backend_API.pdf) — Original 7-page assignment specification PDF issued by IQuantsGraph Pvt Ltd.

---

## 6. Local Setup & Installation

### Prerequisites
* Python 3.11+
* PostgreSQL (or SQLite for local lightweight testing)
* Git

### Step-by-Step Installation

1. **Clone the Repository:**
   ```bash
   git clone <repository-url>
   cd LEAVEDESK
   ```

2. **Create and Activate Virtual Environment:**
   * **Windows (PowerShell):**
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
     *(If script execution is disabled, enable it for your current shell: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`, or run directly using `.\.venv\Scripts\uvicorn.exe`)*
   * **Windows (Command Prompt):**
     ```cmd
     python -m venv .venv
     .\.venv\Scripts\activate.bat
     ```
   * **Linux / macOS:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install Pinned Dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   ```bash
   cp .env.example .env
   ```
   *(Review `.env` and configure your `DATABASE_URL` with your local PostgreSQL or SQLite credentials)*.

5. **Run Database Migrations:**
   ```bash
   alembic upgrade head
   ```

6. **Seed Initial Test Users:**
   ```bash
   python seed.py
   ```

7. **Start the Application Server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

---

## 7. Docker & Docker Compose Deployment

To run the complete production stack (FastAPI backend + PostgreSQL) in isolated containers:

```bash
# Build and run containers in background
docker compose up --build -d

# Check service logs
docker compose logs -f

# Verify running containers
docker compose ps
```

The application container automatically runs migrations (`alembic upgrade head`), executes `seed.py`, and starts Uvicorn on port `8000`.

---

## 8. Interactive API Documentation (Swagger UI)

Once running, access the documentation via your browser:
* **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
* **Health Check Probe:** [http://localhost:8000/health](http://localhost:8000/health)

### Testing via Swagger UI
1. Execute `POST /auth/login` using one of the seed accounts below.
2. Copy the returned `access_token`.
3. Click the **Authorize** button (top right of Swagger UI).
4. Enter token: `Bearer <access_token>`.
5. Execute protected endpoints (`/leaves`, `/wfh`, `/manager/requests`, `/reports/leaves`).

---

## 9. Seed Data & Test Credentials

The database seed script (`seed.py`) configures the following organizational hierarchy:

| Name | Email | Role | Reports To | Testing Password |
| :--- | :--- | :--- | :--- | :--- |
| **Priya Manager** | `priya.manager@leavedesk.test` | `manager` | *None* | `Manager@123` |
| **Arjun Employee**| `arjun@leavedesk.test` | `employee` | Priya Manager | `Employee@123` |
| **Meera Employee**| `meera@leavedesk.test` | `employee` | Priya Manager | `Employee@123` |

---

## 10. Test Execution & Coverage

The test suite contains **36 automated test scenarios** covering every functional requirement, edge case, and validation rule.

To run the complete test suite:
```bash
pytest
```

To run with verbose output:
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

## 11. Design Assumptions & Rationale

As instructed in Sections 8, 16, and 6.4 of the brief, key technical assumptions are documented in [Documentation/ASSUMPTIONS.md](Documentation/ASSUMPTIONS.md):

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

## 12. Known Limitations & Future Improvements

### Known Limitations
* **Public Holiday Integration:** Currently, all Mondays through Fridays are treated as working days. Organizations with fixed regional holiday calendars require calendar integration.
* **Partial-Day Time Slots for HOURS:** The assignment specifies `HOURS` as 1, 2, or 3 hours without morning/afternoon slot tags. While cumulative daily hours are protected, specific start-time collision detection is not modeled.

### Future Improvements
* **Configurable Working Calendar:** Support organizational holiday calendars via database configurations or third-party calendar APIs.
* **Email / Webhook Notifications:** Trigger background tasks (via Celery or FastAPI BackgroundTasks) to notify managers when new requests are submitted, and notify employees when decisions are finalized.
* **Pagination for Queue & History:** Introduce cursor-based or limit/offset pagination on `/manager/requests` and `/leaves/me` for large enterprise teams.
* **Audit Event Stream:** Implement append-only event logging for regulatory compliance and audit history.

---

## 13. Effort Spent per Assignment Section

| Section | Topic | Estimated Effort | Focus Areas |
| :--- | :--- | :--- | :--- |
| **Section 1** | Authentication & Roles | ~2.5 hours | Model hierarchy, Bcrypt hashing, JWT generation/validation, role dependencies, seed script. |
| **Section 2** | Leave & WFH Requests | ~4.0 hours | Duration calculations (`FULL_DAY`, `HALF_DAY`, `HOURS`), working days evaluator, overlap rules, user row locking. |
| **Section 3** | Manager Approval Workflow | ~2.5 hours | Team authorization checking, centralized State Machine, audit trails, comment validations. |
| **Section 4** | 6-Month CSV Reporting | ~2.5 hours | `relativedelta` window arithmetic, multi-day WFH row expansion, summary block formatting, stream responses. |
| **Section 5 & 6**| Architecture, DevOps, Docs & Tests | ~3.5 hours | Clean architecture layering, Docker & Compose, Alembic migrations, full 36-test suite, README. |
| **Total** | | **~15.0 hours** | |
