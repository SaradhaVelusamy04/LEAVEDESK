# LeaveDesk — System Assumptions & Design Decisions

This document explicitly captures all technical interpretations, domain boundary assumptions, and edge-case resolutions in accordance with Section 8, Section 18, and Section 6.4 of the brief.

---

## 1. Working-Day & Calendar Policy (WFH Management)

* **Context:**
  Section 8 specifies: *"Do not silently invent a holiday calendar or weekend policy. Document the working-day interpretation and any other unresolved assumptions."*
* **Decision:**
  * **Working Days:** Defined strictly as Monday through Friday (Python `datetime.date.weekday() < 5`, where 0=Monday, 4=Friday).
  * **Weekends:** Saturday (5) and Sunday (6) are non-working days.
  * **Public Holidays:** No static or country-specific holiday calendar is assumed.
  * **Multi-Day Spans:** A WFH request spanning Friday to Monday encompasses 2 working days (Friday and Monday), which is valid under the 2-working-day limit.
  * **Zero Working Days:** A WFH request spanning only non-working days (e.g. Saturday to Sunday) contains 0 working days and will be rejected with HTTP 422 because a WFH request must cover at least 1 working day.
  * **Maximum Working Days:** Any request spanning more than 2 working days (e.g. Monday to Wednesday = 3 working days) is rejected with HTTP 422.

---

## 2. Leave Duration & Overlap Mechanics

* **Context:**
  Section 2.2 and Section 7 of the brief define:
  * `FULL_DAY`: 1.0 day.
  * `HALF_DAY`: Requires `half` (`FIRST_HALF` or `SECOND_HALF`), 0.5 day.
  * `HOURS`: Requires `hours` in `{1, 2, 3}`, days counted = `hours / 8`.
* **Conflict Matrix:**
  * Active requests are defined as those with status `PENDING` or `APPROVED`.
  * `CANCELLED` and `REJECTED` requests do **not** block new requests.
  * A `FULL_DAY` leave blocks **any** other leave or WFH request on that date for the same user (HTTP 409).
  * Two `HALF_DAY` requests for the same date may coexist **only if** one is `FIRST_HALF` and the other is `SECOND_HALF`.
  * Two identical half-day requests (e.g. two `FIRST_HALF` on the same date) conflict (HTTP 409).
  * A `HALF_DAY` and a `FULL_DAY` conflict (HTTP 409).
  * `HOURS` requests:
    * Since `HOURS` leaves do not specify a time-of-day half, an `HOURS` leave cannot coexist with a `FULL_DAY` leave.
    * Cumulative leave on a single calendar day cannot exceed 1.0 day (`days_counted <= 1.0`).
    * An `HOURS` request cannot overlap another `HOURS` request on the same date to avoid ambiguous partial time slots.

---

## 3. Manager Roles & Request Lifecycles

* **Context:**
  Managers can submit their own leave and WFH requests.
* **Hierarchy:**
  * Every employee points to a manager via `reports_to_id`.
  * Top-level managers (e.g., Priya Manager in `seed.py`) have `reports_to_id = NULL`.
  * Only a request's designated direct manager (`creator.reports_to_id == manager.id`) is authorized to approve or reject requests.
  * If a top-level manager submits a request, it remains in `PENDING` status unless a higher-level supervisor is assigned.
  * Managers cannot approve or reject their own requests (prevents self-approval loop).

---

## 4. Reporting Date Windows & Arithmetic

* **Context:**
  Section 4.2: *"The window is the last 6 calendar months up to and including today: from the same day 6 months ago (use `dateutil.relativedelta` or equivalent) to today. Compute it on the server; do not trust dates from the client."*
* **Date Window Calculation:**
  * `to_date = datetime.date.today()`
  * `from_date = to_date - relativedelta(months=6)`
  * Both dates are inclusive.
  * If the starting day does not exist in the target month (e.g. August 31 minus 6 months = February 28/29), standard `relativedelta` month truncation semantics are applied.
* **WFH Multi-Day Row Expansion:**
  * A WFH request spanning multiple working days generates **one CSV row per working day** within the reporting window.
  * Each working day row lists `request_type = WFH`, `days_counted = 1.0`, with leave-specific columns (`leave_type`, `duration_type`, `half`, `hours`) left empty.
  * Non-working weekend days within a multi-day WFH span are excluded from report rows.

---

## 5. CSV Reporting Output Format

* **Header:**
  Must strictly match:
  `date,request_type,leave_type,duration_type,half,hours,days_counted,status,reason,decided_by,decided_at`
* **Audit Fields in CSV:**
  * `decided_by`: Formatted as the deciding manager's email (or empty string if not decided).
  * `decided_at`: Formatted as ISO 8601 UTC timestamp string `YYYY-MM-DDTHH:MM:SSZ` (or empty string if not decided).
* **Summary Block:**
  Appended after a blank line following the data rows:
  ```csv
  SUMMARY
  Total Approved Leave Days,<sum_leave_days_to_2_decimals>
  Total Approved WFH Days,<sum_wfh_days>
  Pending Requests Count,<count_pending>
  Rejected Requests Count,<count_rejected>
  ```
  *(Formatted to be cleanly parsed and human-readable).*
* **Zero Requests Case:**
  If a user has 0 requests in the 6-month window, returns the header row, a blank line, and the summary block with all zeros.

---

## 6. Security, Authentication & Token Management

* **Token Scheme:** Bearer authentication with JWT (`sub` payload set to user's `id` as string).
* **Token Expiration:** Default 60 minutes, configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`.
* **Password Hashing:** `bcrypt` with automated salt generation.
* **Resource Privacy:** Attempting to access or cancel another user's request via `/leaves/{id}/cancel` returns **404 Not Found** instead of 403, preventing attackers from probing for valid request IDs.
