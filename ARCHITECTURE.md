# LeaveDesk — System Architecture & Design Specification

## 1. Architectural Style: Modular Monolith with Clean Architecture

LeaveDesk follows the **Modular Monolith** architecture pattern with **Clean Architecture** layering.
The application is deployed as a single unified service while strictly segregating boundaries across business modules and architectural layers.

```
+--------------------------------------------------------------------------+
|                            Presentation Layer                            |
|          FastAPI Routers - Pydantic Request/Response Schemas             |
|          Auth & Role Dependencies - OpenAPI/Swagger Specs                |
+------------------------------------+-------------------------------------+
                                     |
                                     v
+--------------------------------------------------------------------------+
|                            Application Layer                             |
|          Service Orchestrators (Auth, Leave, WFH, Manager, Report)       |
|          Centralized Status Transition Manager                           |
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

## 2. Directory Structure

```
d:\LEAVEDESK\
├── alembic\                       # Database migration environment
│   ├── versions\
│   └── env.py
├── app\
│   ├── api\                       # Presentation Layer (FastAPI Routers)
│   │   ├── deps.py                # Dependencies (DB session, current_user, roles)
│   │   └── v1\
│   │       ├── auth.py            # POST /auth/login, GET /auth/me
│   │       ├── leaves.py          # POST /leaves, GET /leaves/me, cancel
│   │       ├── wfh.py             # POST /wfh, GET /wfh/me, cancel
│   │       ├── manager.py         # GET /manager/requests, approve, reject
│   │       ├── reports.py         # GET /reports/leaves
│   │       └── health.py          # GET /health
│   ├── core\                      # Cross-Cutting Infrastructure
│   │   ├── config.py              # Environment variables via Pydantic Settings
│   │   ├── database.py            # SQLAlchemy 2.x engine & async/sync sessionmaker
│   │   ├── security.py            # Bcrypt hashing & JWT encode/decode
│   │   └── exceptions.py          # Unified exception handlers (401, 403, 404, 409, 422, 500)
│   ├── domain\                    # Domain Layer (Pure Business Rules)
│   │   ├── enums.py               # RoleEnum, LeaveTypeEnum, DurationTypeEnum, StatusEnum, etc.
│   │   ├── rules.py               # Leave duration calculator, working-day evaluator
│   │   └── state_machine.py       # RequestStateMachine (PENDING -> APPROVED/REJECTED/CANCELLED)
│   ├── models\                    # Infrastructure Layer (SQLAlchemy ORM Entities)
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── leave.py
│   │   └── wfh.py
│   ├── schemas\                   # Presentation Layer (Pydantic DTOs)
│   │   ├── auth.py
│   │   ├── leave.py
│   │   ├── wfh.py
│   │   ├── manager.py
│   │   └── report.py
│   ├── repositories\              # Infrastructure Data Access Layer
│   │   ├── user_repo.py
│   │   ├── leave_repo.py
│   │   └── wfh_repo.py
│   ├── services\                  # Application Layer (Use Case Coordinators)
│   │   ├── auth_service.py
│   │   ├── leave_service.py
│   │   ├── wfh_service.py
│   │   ├── manager_service.py
│   │   └── report_service.py
│   └── main.py                    # FastAPI Application Factory & Middleware
├── tests\                         # Pytest Test Suite
│   ├── conftest.py                # Test DB fixtures, mock data, TestClient setup
│   ├── test_auth.py
│   ├── test_leaves.py
│   ├── test_wfh.py
│   ├── test_manager.py
│   ├── test_reports.py
│   └── test_health.py
├── .env.example
├── .gitignore
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── seed.py
├── sample_report.csv
└── README.md
```

## 3. Relational Data Model

### Entity-Relationship Diagram (ERD)

```
       +---------------------------------------------+
       |                    users                    |
       +---------------------------------------------+
       | id: UUID / Integer (PK)                     |
       | name: VARCHAR(100)                          |
       | email: VARCHAR(150) (UNIQUE, INDEX)         |
       | hashed_password: VARCHAR(255)               |
       | role: VARCHAR(20) [employee, manager]       |
       | reports_to_id: FK -> users.id (NULLABLE)    |
       | created_at: TIMESTAMPTZ (UTC)               |
       | updated_at: TIMESTAMPTZ (UTC)               |
       +---------------------------------------------+
                 |                       |
                 | (1:N)                 | (1:N)
                 v                       v
+-------------------------------+  +-------------------------------+
|        leave_requests         |  |         wfh_requests          |
+-------------------------------+  +-------------------------------+
| id: UUID / Integer (PK)       |  | id: UUID / Integer (PK)       |
| user_id: FK -> users.id       |  | user_id: FK -> users.id       |
| date: DATE (INDEX)            |  | start_date: DATE (INDEX)      |
| leave_type: VARCHAR(20)       |  | end_date: DATE (INDEX)        |
| duration_type: VARCHAR(20)    |  | working_days_count: INTEGER   |
| half: VARCHAR(20) NULLABLE    |  | reason: TEXT NULLABLE         |
| hours: INTEGER NULLABLE       |  | status: VARCHAR(20)           |
| days_counted: NUMERIC(4,3)    |  | decided_by: FK -> users.id    |
| reason: TEXT NULLABLE         |  | decided_at: TIMESTAMPTZ (UTC) |
| status: VARCHAR(20)           |  | decision_comment: TEXT NULL   |
| decided_by: FK -> users.id    |  | created_at: TIMESTAMPTZ (UTC) |
| decided_at: TIMESTAMPTZ (UTC) |  | updated_at: TIMESTAMPTZ (UTC) |
| decision_comment: TEXT NULL   |  +-------------------------------+
| created_at: TIMESTAMPTZ (UTC) |
| updated_at: TIMESTAMPTZ (UTC) |
+-------------------------------+
```

## 4. State Machine & Status Lifecycle

All request lifecycle transitions are managed through a unified domain state machine (`RequestStateMachine`):

```
                      +-------------------+
                      |      SUBMIT       |
                      +---------+---------+
                                |
                                v
                      +-------------------+
                      |      PENDING      |
                      +----+-----+----+---+
                           |     |    |
          manager approves |     |    | employee cancels
          +----------------+     |    +----------------+
          |                      |                     |
          v                      | manager rejects     v
+-------------------+            v           +-------------------+
|     APPROVED      |  +-------------------+ |     CANCELLED     |
+-------------------+  |     REJECTED      | +-------------------+
                       +-------------------+
```

### Transition Matrix
| Current State | Target State | Permitted Initiator | Allowed? | Error Code |
| :--- | :--- | :--- | :--- | :--- |
| **PENDING** | APPROVED | Direct Manager | **YES** | - |
| **PENDING** | REJECTED | Direct Manager (min 5 char comment) | **YES** | - |
| **PENDING** | CANCELLED | Owner (Employee) | **YES** | - |
| **APPROVED** | ANY | Any | **NO** | 409 Conflict |
| **REJECTED** | ANY | Any | **NO** | 409 Conflict |
| **CANCELLED**| ANY | Any | **NO** | 409 Conflict |

## 5. Concurrency & Overlap Prevention Strategy

A critical requirement in Section 12 is:
> *"Consider concurrent requests when implementing overlap detection. A simple application-level check followed by an insert is not sufficient protection against simultaneous conflicting requests. Use suitable database transaction isolation or locking strategies and explain the decision."*

### The Race Condition Problem
If two requests for the same employee on the same date arrive concurrently in parallel worker threads:
1. Thread A executes `SELECT ... WHERE date = '2026-11-20' AND status IN ('PENDING', 'APPROVED')` -> finds 0 records.
2. Thread B executes `SELECT ... WHERE date = '2026-11-20' AND status IN ('PENDING', 'APPROVED')` -> finds 0 records.
3. Thread A inserts a `FULL_DAY` leave. Commits.
4. Thread B inserts another `FULL_DAY` leave. Commits.
Result: Two conflicting leaves exist simultaneously.

### Our Strategy: User-Scoped Pessimistic Concurrency Control
We implement **Pessimistic Locking on the User Resource** within a transactional boundary:
1. When evaluating a leave or WFH creation request, the transaction locks the user row:
   ```sql
   SELECT id FROM users WHERE id = :user_id FOR UPDATE;
   ```
2. Because the user row is locked for the duration of the transaction, all concurrent leave and WFH submissions for that specific user are serialized.
3. Once serialized, the overlap detection query is guaranteed to observe committed state without phantom inserts.
4. **Why this approach is superior:**
   - **PostgreSQL exclusion constraints (`EXCLUDE USING GIST`)** are complex to configure across disparate tables (`leave_requests` vs `wfh_requests`) and do not cleanly handle partial-day conditions (e.g. `FIRST_HALF` + `SECOND_HALF` allowed, but `FULL_DAY` disallowed).
   - **User row locking (`FOR UPDATE`)** provides perfect serialization *per user* without creating database-wide bottlenecks (different employees submit concurrently with zero lock contention).
   - High throughput and mathematically zero overlap race conditions.

## 6. Security & Authorization Architecture

1. **Password Security:** Salted hashes generated via `bcrypt` (work factor 12).
2. **Token Security:** Signed JWTs using `HS256` with configurable expiration (default 60 minutes) and configurable secret key.
3. **Role Enforcement:** FastAPI dependencies `get_current_user` and `require_role("manager")`.
4. **Ownership Verification:**
   - Employees querying `/leaves/me` or `/wfh/me` are scoped directly to `current_user.id`.
   - Access to `/leaves/{id}/cancel` checks `request.user_id == current_user.id`; if mismatched, returns **404 Not Found** (to prevent resource enumeration).
5. **Manager Hierarchy Verification:**
   - Manager endpoints verify that the request's creator has `user.reports_to_id == manager.id`. If not, returns **403 Forbidden**.
