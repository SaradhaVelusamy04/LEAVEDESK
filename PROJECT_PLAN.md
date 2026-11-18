# LeaveDesk — Project Implementation Plan

## 1. Project Overview
LeaveDesk is an enterprise-grade REST API backend for Employee Leave and Work-From-Home (WFH) Management built for IQuantsGraph Pvt Ltd.
It supports role-based workflows for employees and managers, multi-format leave duration calculations, strict overlap and working-day validations, centralized state machine transitions, audit logging, and 6-month historical CSV reporting.

## 2. Technology Stack & Decision Rationale
* **Language & Runtime:** Python 3.11+
  * *Rationale:* Type hint support, modern performance enhancements, standard datetime and async capabilities.
* **Web Framework:** FastAPI
  * *Rationale:* High-performance async support, automated OpenAPI/Swagger generation, first-class dependency injection, Pydantic v2 data validation.
* **Database & ORM:** PostgreSQL + SQLAlchemy 2.0
  * *Rationale:* Relational integrity, ACID compliance, declarative 2.0 mapping, strong transactional semantics for concurrency control.
* **Migrations:** Alembic
  * *Rationale:* Explicit database schema evolution tracking, reproducible schema deployment.
* **Authentication & Cryptography:** JWT (`python-jose` / `pyjwt`) with `passlib` / `bcrypt`
  * *Rationale:* Stateless, standard bearer tokens, cryptographically secure salted password hashing.
* **Testing:** `pytest` + `httpx` (`TestClient`)
  * *Rationale:* Industry standard test runner, fixture support, rapid isolated API testing.
* **Containerization:** Docker + Docker Compose
  * *Rationale:* Reproducible multi-service deployment (PostgreSQL + API), zero-drift execution.

## 3. Milestones & Delivery Roadmap

### Milestone 0: Project Analysis, Architecture & Planning (Current)
* Read and cross-reference all 7 pages of `IQG_Intern_Assignment_Backend_API.pdf`.
* Audit environment, directory structure, and tooling.
* Deliver foundational governance documents:
  * `PROJECT_PLAN.md`
  * `ARCHITECTURE.md`
  * `REQUIREMENT_TRACEABILITY.md`
  * `ASSUMPTIONS.md`
  * `IMPLEMENTATION_LOG.md`
* Human Review & Approval checkpoint.

### Milestone 1: Foundation, Environment & Core Scaffolding
* Initialize Git repository and `.gitignore`.
* Define `requirements.txt` with pinned dependencies.
* Configure environment management (`app/core/config.py` using `pydantic-settings`, `.env.example`).
* Configure SQLAlchemy 2.x engine, sessionmaker, and DB base (`app/core/database.py`).
* Setup logging and centralized API error handlers (`app/core/errors.py`).
* Implement public `GET /health` with active DB probe.
* Configure Alembic environment.

### Milestone 2: Authentication, Users & Seed Data
* Implement `User` model with `RoleEnum` (`employee`, `manager`) and self-referential `reports_to_id`.
* Implement password hashing utility (`bcrypt`) and JWT manager (configurable expiry, default 60 min).
* Implement authentication endpoints:
  * `POST /auth/login` (Generic 401 on unknown email or bad password).
  * `GET /auth/me` (Authenticated caller profile, never exposes password hash).
* Implement FastAPI dependencies: `get_current_user`, `require_role("manager")`.
* Create `seed.py` with the 3 required seed users (Priya, Arjun, Meera).
* Author comprehensive authentication test suite.

### Milestone 3: Leave & Work-From-Home (WFH) Management
* Define models: `LeaveRequest`, `WfhRequest`.
* Implement Leave duration validation logic:
  * `FULL_DAY`: 1.0 day.
  * `HALF_DAY`: `FIRST_HALF` or `SECOND_HALF`, 0.5 day.
  * `HOURS`: 1, 2, 3 integers, `hours / 8` days. 422 on invalid combinations or fractional/missing fields.
* Implement WFH validation:
  * `start_date` to `end_date` inclusive, max 2 working days (Monday-Friday logic).
* Implement robust concurrency-safe overlap detection (409 Conflict):
  * `FULL_DAY` blocks any other active leave/WFH on that day.
  * `HALF_DAY` coexistence only between `FIRST_HALF` and `SECOND_HALF`.
  * WFH blocks active WFH and FULL_DAY leaves.
* Implement employee endpoints:
  * `POST /leaves`, `GET /leaves/me`, `POST /leaves/{id}/cancel`
  * `POST /wfh`, `GET /wfh/me`, `POST /wfh/{id}/cancel`
  * Enforce 404 for resources not owned by caller.
* Author unit and integration tests for leave and WFH.

### Milestone 4: Manager Approval Workflow & State Machine
* Implement centralized status transition engine (`app/domain/state_machine.py`):
  * Allowed: `PENDING -> APPROVED`, `PENDING -> REJECTED`, `PENDING -> CANCELLED`.
  * All other transitions strictly rejected with 409 Conflict.
* Implement Manager endpoints:
  * `GET /manager/requests` (Direct reports only, default `status=PENDING`, optional filters).
  * `POST /manager/leaves/{id}/approve` & `POST /manager/leaves/{id}/reject`.
  * `POST /manager/wfh/{id}/approve` & `POST /manager/wfh/{id}/reject`.
* Enforce 403 Forbidden when an employee accesses manager routes or when a manager attempts to decide a non-direct report's request.
* Enforce minimum 5-character comment on rejection; optional comment on approval.
* Audit trail: record `decided_by`, `decided_at` (UTC timestamp), and `decision_comment`.
* Author manager workflow test suite.

### Milestone 5: Reporting Engine (6-Month CSV Export)
* Implement exact 6-calendar-month calculation (`dateutil.relativedelta(months=6)` to `today`).
* Enforce server-side date range calculation.
* Build query layer aggregating leave and WFH records sorted oldest first.
* Expand WFH multi-day requests into one row per working day (`days_counted=1.0`).
* Generate exact CSV format:
  * Exact headers: `date,request_type,leave_type,duration_type,half,hours,days_counted,status,reason,decided_by,decided_at`
  * Data rows.
  * Blank line separator.
  * Summary section: Total APPROVED leave days (2 decimal places), total approved WFH days, count of PENDING and REJECTED requests.
* Enforce access: caller only, or manager requesting direct report (`?employee_id=<id>`). Others 403.
* Graceful empty CSV response for users with 0 records.
* Author reporting test suite.

### Milestone 6: DevOps, Documentation & Final Engineering Quality
* Author production-ready multi-stage `Dockerfile`.
* Author `docker-compose.yml` (backend service + PostgreSQL health check service).
* Generate and commit verified `sample_report.csv`.
* Author comprehensive `README.md` containing all setup, execution, architectural, and effort breakdown details.
* Execute end-to-end regression test suite with 100% test pass guarantee.
