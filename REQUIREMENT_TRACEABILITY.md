# LeaveDesk — Requirement Traceability Matrix (RTM)

This document maps every requirement from `IQG_Intern_Assignment_Backend_API.pdf` and the Master Engineering Prompt to its design, architectural module, target files, and verification test cases.

| Req ID | Specification / Requirement | Target Module / Layer | Implementation Path | Planned Verification Test |
| :--- | :--- | :--- | :--- | :--- |
| **AUTH-01** | `POST /auth/login` accepts email & password, returns JWT with `token_type: "bearer"` | Presentation / App | `app/api/v1/auth.py`, `app/services/auth_service.py` | `test_auth_login_success` |
| **AUTH-02** | Passwords stored strictly as bcrypt hashes; never plain-text, never returned | Infrastructure / Domain | `app/core/security.py`, `app/models/user.py` | `test_password_is_hashed_and_not_exposed` |
| **AUTH-03** | Generic 401 message for unknown email OR wrong password | Presentation / App | `app/api/v1/auth.py` | `test_login_invalid_email_and_password_generic_401` |
| **AUTH-04** | Tokens expire after configurable time (default 60m); expired/tampered returns 401 | Infrastructure / Core | `app/core/security.py`, `app/api/deps.py` | `test_expired_and_tampered_jwt_token` |
| **AUTH-05** | `GET /auth/me` returns `id`, `name`, `email`, `role`, `manager_id` (never password) | Presentation | `app/api/v1/auth.py`, `app/schemas/auth.py` | `test_get_current_user_profile` |
| **AUTH-06** | Role check enforced on API; employee calling manager route receives 403 | Presentation / Core | `app/api/deps.py` (`require_role`) | `test_employee_calling_manager_route_returns_403` |
| **SEED-01** | `seed.py` creates 3 sample users (Priya Manager, Arjun Employee, Meera Employee) | CLI / Infrastructure | `seed.py` | `test_seed_users_can_authenticate` |
| **LEAVE-01**| `POST /leaves` creates leave with status `PENDING`, accepts date, leave_type, duration_type, etc. | Presentation / Domain | `app/api/v1/leaves.py`, `app/domain/rules.py` | `test_create_leave_pending_status` |
| **LEAVE-02**| Supported leave types: `CASUAL`, `SICK`, `EARNED` | Domain | `app/domain/enums.py` | `test_leave_types_validation` |
| **LEAVE-03**| `FULL_DAY` counts as 1.0 day; no extra fields | Domain | `app/domain/rules.py` | `test_leave_full_day_counted` |
| **LEAVE-04**| `HALF_DAY` requires `half` (`FIRST_HALF` or `SECOND_HALF`), counts as 0.5 day | Domain / Schema | `app/domain/rules.py`, `app/schemas/leave.py` | `test_leave_half_day_validation` |
| **LEAVE-05**| `HOURS` requires integer 1, 2, or 3, counted as `hours / 8`. Reject other numbers, decimals, or strings with 422 | Domain / Schema | `app/domain/rules.py`, `app/schemas/leave.py` | `test_leave_hours_validation_and_rejected_values` |
| **LEAVE-06**| Reject half on `FULL_DAY`/`HOURS`; reject hours on `FULL_DAY`/`HALF_DAY` with 422 | Presentation / Schema | `app/schemas/leave.py` | `test_mismatched_duration_fields_422` |
| **LEAVE-07**| Overlap: `FULL_DAY` blocks any active leave; `FIRST_HALF` and `SECOND_HALF` can coexist; two identical halves conflict; return 409 | Application / Domain | `app/services/leave_service.py` | `test_leave_overlap_scenarios` |
| **LEAVE-08**| `GET /leaves/me` returns caller's requests newest first, with status, from_date, to_date filters | Application / Repo | `app/api/v1/leaves.py`, `app/repositories/leave_repo.py` | `test_get_my_leaves_filtering_and_sorting` |
| **LEAVE-09**| `POST /leaves/{id}/cancel` sets status to CANCELLED only if PENDING; non-owner returns 404; non-pending returns 409 | Application / Domain | `app/api/v1/leaves.py`, `app/domain/state_machine.py`| `test_cancel_leave_permissions_and_state_rules` |
| **WFH-01**  | `POST /wfh` accepts `start_date` and `end_date` (inclusive, max 2 working days), optional reason, status PENDING | Presentation / Domain | `app/api/v1/wfh.py`, `app/domain/rules.py` | `test_create_wfh_success` |
| **WFH-02**  | Reject WFH exceeding 2 working days with 422 | Domain | `app/domain/rules.py` | `test_wfh_max_two_working_days` |
| **WFH-03**  | WFH cannot overlap FULL_DAY leave or active WFH request for same user (409) | Application / Repo | `app/services/wfh_service.py` | `test_wfh_overlap_detection` |
| **WFH-04**  | `GET /wfh/me` returns caller's requests newest first, with status, from_date, to_date filters | Application / Repo | `app/api/v1/wfh.py`, `app/repositories/wfh_repo.py` | `test_get_my_wfh_filtering_and_sorting` |
| **WFH-05**  | `POST /wfh/{id}/cancel` owner-only, pending-only; 404 for other user; 409 if not pending | Application / Domain | `app/api/v1/wfh.py`, `app/domain/state_machine.py` | `test_cancel_wfh_permissions_and_state_rules` |
| **MGR-01**  | `GET /manager/requests` (manager only) returns direct reports' leaves and WFH; defaults to status=PENDING | Application / Repo | `app/api/v1/manager.py`, `app/repositories/` | `test_manager_queue_direct_reports_only` |
| **MGR-02**  | Manager filters by status, employee_id, from_date, to_date | Presentation / Repo | `app/api/v1/manager.py` | `test_manager_queue_filters` |
| **MGR-03**  | `POST /manager/leaves/{id}/approve` & `POST /manager/leaves/{id}/reject` | Application / Domain | `app/api/v1/manager.py`, `app/services/manager_service.py` | `test_manager_leave_decision` |
| **MGR-04**  | `POST /manager/wfh/{id}/approve` & `POST /manager/wfh/{id}/reject` | Application / Domain | `app/api/v1/manager.py`, `app/services/manager_service.py` | `test_manager_wfh_decision` |
| **MGR-05**  | Rejection requires comment (min 5 chars); approval accepts optional comment | Schema / Domain | `app/schemas/manager.py` | `test_manager_decision_comment_validation` |
| **MGR-06**  | Manager can only decide requests of direct reports; other requests return 403 | Application | `app/services/manager_service.py` | `test_manager_cannot_decide_other_team_403` |
| **MGR-07**  | Only PENDING requests can be decided; decided requests return 409 | Domain | `app/domain/state_machine.py` | `test_already_decided_returns_409` |
| **MGR-08**  | Every decision stores `decided_by`, `decided_at` (UTC timestamp), and `decision_comment` | Infrastructure / Model | `app/models/leave.py`, `app/models/wfh.py` | `test_decision_audit_trail_recorded` |
| **RPT-01**  | `GET /reports/leaves` returns CSV download (`text/csv`, attachment filename) | Presentation / App | `app/api/v1/reports.py` | `test_report_download_headers_and_content_type` |
| **RPT-02**  | Window is exactly last 6 calendar months up to and including today; computed on server | Domain / App | `app/services/report_service.py` | `test_report_six_month_date_window_calculation` |
| **RPT-03**  | CSV header: `date,request_type,leave_type,duration_type,half,hours,days_counted,status,reason,decided_by,decided_at` | Presentation / App | `app/services/report_service.py` | `test_report_csv_exact_header` |
| **RPT-04**  | Rows sorted by date, oldest first; WFH produces one row per working day | Domain / App | `app/services/report_service.py` | `test_report_sorting_and_wfh_expansion` |
| **RPT-05**  | Blank line and summary block: Total APPROVED leave days, total approved WFH days, PENDING & REJECTED counts | Application | `app/services/report_service.py` | `test_report_summary_calculations` |
| **RPT-06**  | Role access: employee downloads own; manager can pass `?employee_id` for direct report; other returns 403 | Application / Deps | `app/api/v1/reports.py` | `test_report_role_based_access_control` |
| **RPT-07**  | Empty window returns valid CSV with header and zero summary (never error) | Application | `app/services/report_service.py` | `test_report_empty_returns_valid_csv` |
| **HLTH-01** | `GET /health` returns `{"status": "ok"}` and validates DB connectivity | Presentation / Infra | `app/api/v1/health.py` | `test_health_check_db_connectivity` |
| **CONC-01** | Concurrency-safe overlap checking using user-level pessimistic locking (`FOR UPDATE`) | Infrastructure / App | `app/services/leave_service.py`, `app/services/wfh_service.py` | `test_concurrent_leave_overlap_prevention` |
| **DOC-01**  | Complete README, sample_report.csv, Dockerfile, docker-compose.yml | DevOps / Docs | Root project files | Verification of docker-compose build and fresh clone |
