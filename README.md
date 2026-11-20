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

```text
LEAVEDESK/
├── alembic/
│   ├── versions/                  # Database migration scripts
│   ├── env.py                     # Alembic environment configuration
│   └── script.py.mako             # Migration template
├── app/
│   ├── api/
│   │   ├── deps.py                # Authentication and authorization dependencies
│   │   └── v1/
│   │       ├── auth.py             # Login and current-user endpoints
│   │       ├── leaves.py           # Leave creation, listing, cancellation
│   │       ├── wfh.py               # WFH creation, listing, cancellation
│   │       ├── manager.py           # Manager review and decision endpoints
│   │       ├── reports.py           # CSV report endpoint
│   │       └── health.py            # Health check endpoint
│   ├── core/
│   │   ├── config.py                # Application settings
│   │   ├── database.py              # SQLAlchemy engine and sessions
│   │   ├── exceptions.py             # Centralized exception handlers
│   │   └── security.py               # Password hashing and JWT utilities
│   ├── domain/
│   │   ├── enums.py                  # Roles, leave types, durations, statuses
│   │   ├── rules.py                  # Duration and working-day calculations
│   │   └── state_machine.py          # Request lifecycle transitions
│   ├── models/                       # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── leave.py
│   │   └── wfh.py
│   ├── repositories/                 # Database query operations
│   │   ├── user_repo.py
│   │   ├── leave_repo.py
│   │   └── wfh_repo.py
│   ├── schemas/                      # Pydantic request and response schemas
│   │   ├── auth.py
│   │   ├── leave.py
│   │   ├── wfh.py
│   │   └── manager.py
│   ├── services/                     # Application business logic
│   │   ├── auth_service.py
│   │   ├── leave_service.py
│   │   ├── wfh_service.py
│   │   ├── manager_service.py
│   │   └── report_service.py
│   └── main.py                       # FastAPI application setup
├── Documentation/
│   ├── ARCHITECTURE.md               # Architecture and database design
│   ├── ASSUMPTIONS.md                # Business rules and assumptions
│   ├── IMPLEMENTATION_LOG.md         # Implementation history
│   ├── IQG_Intern_Assignment_Backend_API.pdf
│   ├── PROJECT_PLAN.md               # Project milestones and planning
│   └── REQUIREMENT_TRACEABILITY.md   # Requirement-to-test mapping
├── tests/
│   ├── conftest.py                   # Test fixtures and database setup
│   ├── test_health.py
│   ├── test_auth.py
│   ├── test_leaves.py
│   ├── test_wfh.py
│   ├── test_manager.py
│   └── test_reports.py
├── .env.example                      # Environment variable template
├── .gitignore
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
├── requirements.txt
├── sample_report.csv
├── seed.py                           # Initial test-user seeding
└── README.md
```

## 5. Engineering Documentation

The `Documentation/` directory contains supporting design and implementation documents:

- **[System Architecture](Documentation/ARCHITECTURE.md):** Application layers, database design, entity relationships, and concurrency-control approach.
- **[Requirement Traceability Matrix](Documentation/REQUIREMENT_TRACEABILITY.md):** Mapping of assignment requirements to implementation modules and tests.
- **[Design Assumptions](Documentation/ASSUMPTIONS.md):** Working-day definitions, WFH rules, leave overlap behavior, and reporting assumptions.
- **[Project Delivery Plan](Documentation/PROJECT_PLAN.md):** Development milestones and technology decisions.
- **[Implementation Log](Documentation/IMPLEMENTATION_LOG.md):** Chronological record of development activities and implementation decisions.
- **[Original Assignment Brief](Documentation/IQG_Intern_Assignment_Backend_API.pdf):** Assignment specification provided by IQuantsGraph Pvt Ltd.

## 6. Local Setup & Installation

### Prerequisites

- Python 3.11 or later
- PostgreSQL 16 (or a supported local test database configuration)
- Git

### Installation Steps

**1. Clone the repository**

```bash
git clone <repository-url>
cd LEAVEDESK
```

**2. Create and activate a virtual environment**

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```

Linux / macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**3. Install dependencies**

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**4. Configure environment variables**

```bash
cp .env.example .env
```

Update the `.env` file with the appropriate database URL, JWT secret, and other required application settings.

**5. Apply database migrations**

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

The application can also be started using Docker Compose.

```bash
# Build and start the services
docker compose up --build -d

# View service logs
docker compose logs -f

# Check running containers
docker compose ps

# Stop the services
docker compose down
```

The application container is configured to run database migrations, seed initial users, and start the FastAPI application. Refer to the Docker configuration for the exact startup sequence.

## 8. Interactive API Documentation

After starting the application, access:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

### Testing through Swagger UI

1. Execute `POST /auth/login` using one of the seed accounts.
2. Copy the returned `access_token`.
3. Select **Authorize** in Swagger UI.
4. Enter the bearer token.
5. Test protected endpoints such as `/leaves`, `/wfh`, `/manager/requests`, and `/reports/leaves`.

### Main API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/auth/login` | Authenticate a user |
| GET | `/auth/me` | Retrieve current-user details |
| GET | `/health` | Check application and database health |
| POST | `/leaves` | Submit a leave request |
| GET | `/leaves/me` | List the employee's leave requests |
| POST | `/leaves/{id}/cancel` | Cancel a pending leave request |
| POST | `/wfh` | Submit a WFH request |
| GET | `/wfh/me` | List the employee's WFH requests |
| POST | `/wfh/{id}/cancel` | Cancel a pending WFH request |
| GET | `/manager/requests` | Retrieve direct-report requests |
| POST | `/manager/leaves/{id}/approve` | Approve a leave request |
| POST | `/manager/leaves/{id}/reject` | Reject a leave request |
| POST | `/manager/wfh/{id}/approve` | Approve a WFH request |
| POST | `/manager/wfh/{id}/reject` | Reject a WFH request |
| GET | `/reports/leaves` | Download the leave and WFH CSV report |

## 9. Seed Data & Test Credentials

The seed script (`seed.py`) creates the following sample organizational hierarchy:

| Name | Email | Role | Reports To | Testing Password |
|---|---|---|---|---|
| Priya Manager | `priya.manager@leavedesk.test` | manager | None | `Manager@123` |
| Arjun Employee | `arjun.employee@leavedesk.test` | employee | Priya Manager | `Employee@123` |
| Meera Employee | `meera.employee@leavedesk.test` | employee | Priya Manager | `Employee@123` |

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

### Test Suite Breakdown

| Test Module | Scenarios | Areas Covered |
|---|---:|---|
| `test_auth.py` | 8 | Login, invalid credentials, token validation, profile response, role access, seed behavior |
| `test_health.py` | 3 | Health endpoint and database availability |
| `test_leaves.py` | 8 | Leave durations, validation, overlap rules, listing, cancellation |
| `test_wfh.py` | 7 | Working-day calculations, WFH limits, overlap, cancellation |
| `test_manager.py` | 7 | Manager queue, authorization, approval, rejection, state conflicts |
| `test_reports.py` | 3 | CSV generation, date window, sorting, summary, access control |
| **Total** | **36** | **Functional and edge-case scenarios** |

Run the test suite before submission and update the test count if the suite changes.

## 11. Design Assumptions & Rationale

The following business-rule interpretations are documented in `Documentation/ASSUMPTIONS.md`.

### Working-Day Definition

- Monday through Friday are treated as working days.
- Saturday and Sunday are treated as non-working days.
- Public holidays are not excluded unless a holiday calendar is introduced.

### WFH Date Spans

- WFH duration is calculated using working days within the inclusive start and end dates.
- A Friday-to-Monday request counts as two working days.
- A request covering zero working days, such as Saturday to Sunday, is rejected.

### Leave Duration and Overlap Rules

- A `FULL_DAY` request conflicts with other active leave requests on the same date.
- `FIRST_HALF` and `SECOND_HALF` requests can coexist on the same date.
- Duplicate half-day requests conflict.
- `HOURS` requests support the permitted hour values specified in the assignment.
- Overlap validation is applied to active requests according to the implemented business rules.

### Reporting Window

- The reporting period is calculated on the server using the current date and a six-calendar-month lookback.
- Multi-day WFH requests are represented as one CSV row per working day.
- The report includes approved leave and WFH totals, along with pending and rejected request counts.

## 12. Development Effort

The following table records the approximate time spent implementing and validating each major assignment section. Update the time values with your actual effort before submission.

| Assignment Section | Work Completed | Time Spent |
|---|---|---|
| Section 1 — Authentication & Roles | Login, JWT, password hashing, user roles, authorization | ~3.5 hours |
| Section 2 — Leave & WFH Management | Request creation, duration rules, overlap validation, cancellation | ~4 hours |
| Section 3 — Manager Workflow | Review queue, approvals, rejections, decision tracking | ~3 hours |
| Section 4 — CSV Reporting | Six-month report, CSV formatting, summary calculations | ~2.5 hours |
| Section 5 — API Reference | Endpoint organization and Swagger documentation | ~2.5 hours |
| Section 6 — Testing & Submission | Automated tests, debugging, README, Git and repository preparation | ~3.5 hours |
| **Total** | | **19 hours** |

## 13. Known Limitations & Future Improvements

### Known Limitations

- **Public Holiday Integration:** The current working-day calculation treats all weekdays as working days. Regional and organizational holidays are not included.
- **Partial-Day Time Slots:** `HOURS` requests represent a number of hours but do not model specific start and end times. Therefore, time-slot-level collision detection is not implemented.

### Future Improvements

- **Configurable Working Calendar:** Integrate organization-specific working days and public holiday calendars.
- **Notifications:** Add email or webhook notifications for new requests and manager decisions.
- **Pagination:** Introduce pagination for employee request history and manager review queues.
- **Audit Event Stream:** Maintain an append-only event history for request lifecycle changes and compliance auditing.
- **Deployment and Monitoring:** Add CI/CD automation, structured logging, health monitoring, and production deployment configuration.

---

**Project:** LeaveDesk — Employee Leave & Work-From-Home Management API  
**Assignment:** IQuantsGraph Pvt Ltd — Python Backend Engineering Intern  
**Reference:** `IQG-ENG-INTERN-API`
