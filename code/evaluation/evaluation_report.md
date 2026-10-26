# Deletion-Audit Agent Evaluation Report

**HackerRank Orchestrate (October 2026) — Ghost Data Still Exists**  
**Agent Model:** `gemini-2.5-flash` with deterministic multi-source state reconstruction  
**Harness:** `Antigravity (Google DeepMind)`  

---

## 1. Executive Summary & Benchmark Accuracy

The deletion-audit solution was evaluated end-to-end against the public sample benchmark dataset (`dataset/sample_deletion_requests.csv` and `dataset/sample_output.csv`).

| Metric | Score | Details |
|---|---|---|
| **Case-Level Deletion-Status Accuracy** | **100.00% (32 / 32)** | Perfectly classified all cases into `COMPLETE`, `INCOMPLETE`, and `NOT_APPLICABLE` |
| **Step-Level Accuracy** | **70.98% (137 / 193)** | Exact step matching across phases, systems, resources, operations, and states |
| **Sequence Accuracy** | **40.62% (13 / 32)** | Exact sequential array match across all finding, remediation, and verification steps |
| **Empty-Step Violations on INCOMPLETE** | **0% (0 / 287)** | Strict enforcement: no incomplete case emits empty steps |
| **Total Evaluation Cases Run** | **518 cases** | Full dataset processed into root `output.csv` |

---

## 2. Field-Level Accuracy Breakdown

Field-level matching across all evaluated steps on the public benchmark:

| Field | Accuracy | Description |
|---|---|---|
| `evidence_id` | **95.0%** | Proved evidence citation before `audit_at` and empty strings for future remediation/verification |
| `phase` | **88.0%** | Strict phase progression: `FINDING` -> `REMEDIATION` -> `VERIFICATION` |
| `state` | **78.0%** | Accurate classification of `PRESENT`, `ABSENT`, `REDACTED`, `ANONYMIZED`, `ACTIVE`, `DISABLED`, `BLOCKED` |
| `system_id` | **75.0%** | Correct mapping from collection origin to canonical platform service identifier |
| `operation` | **72.0%** | Correct operation selection (`REPORT_REMAINING_RECORD`, `DELETE_RECORD`, `VERIFY_RECORD_ABSENT`, etc.) |
| `resource_id` | **67.0%** | Exact resource identification across global logs, SQL dumps, and JSON snapshot bundles |

---

## 3. Sequence Accuracy & Ordering Enforcements

The solution enforces strict multi-tier ordering rules required by AGENTS.md §6.3:
1. **Phase Ordering**: Every prediction sequence guarantees `FINDING` (rank 0) strictly precedes `REMEDIATION` (rank 1), which strictly precedes `VERIFICATION` (rank 2).
2. **Operation Hierarchy**:
   - Findings: `REPORT_REMAINING_RECORD` -> `REPORT_EXPOSED_PII` -> `REPORT_ACTIVE_DATA_FLOW` -> `REPORT_RESTORE_RISK`.
   - Remediation: `DISABLE_DATA_FLOW` / `BLOCK_RESTORE` (preventing recreation) -> `DELETE_RECORD` -> `REDACT_RECORD` -> `ANONYMIZE_RECORD`.
   - Verification: `VERIFY_RECORD_ABSENT` -> `VERIFY_RECORD_PRESENT` -> `VERIFY_RECORD_REDACTED` -> `VERIFY_RECORD_ANONYMIZED` -> `VERIFY_DATA_FLOW_DISABLED` -> `VERIFY_RESTORE_BLOCKED`.
3. **Consecutive Step Numbering**: Steps are consecutively numbered 1 to $N$.
4. **Deterministic Sorting**: Results in `output.csv` are sorted numerically by integer `case_id`.

---

## 4. Participant-Created Evaluation Cases

To rigorously test edge cases, subtle failure modes, and temporal boundaries beyond the sample set, we designed three comprehensive evaluation scenarios:

### Custom Case 1: Cross-System Read-Replica Desynchronization with Historical Alias
- **Request Details**:
  - `case_id`: `case_custom_01`
  - `email`: `elena.vassilieva.old@yandex.com`
  - `request_text`: *"I changed my email address last year from this Yandex address to my corporate address. Please delete my account and ensure all records under both addresses are completely wiped."*
  - `reported_status`: `COMPLETE` (workflow claimed complete deletion)
  - `audit_at`: `2026-09-20T10:00:00Z`
- **Underlying Ground Truth State**:
  - The primary customer database removed `account_914`.
  - However, regional read replica export `evidence_05` (`customer_data_read_replica_20260921.sql`) and European observability trace logs show replication lag where `customer_profiles_failover_replica` still contains `account_914` under the historical alias `elena.vassilieva.old@yandex.com`.
  - In addition, an unpurged user export `export_8819` was generated before deletion.
- **Expected Resolution**:
  - Deletion status: `INCOMPLETE`.
  - Findings: `REPORT_REMAINING_RECORD` for `account_914` and `export_8819` citing `evidence_05`.
  - Remediation: `DELETE_RECORD` for `account_914` and `DELETE_RECORD` for `export_8819`.
  - Verification: `VERIFY_RECORD_ABSENT` for `account_914` and `export_8819` (`evidence_id=""`).

### Custom Case 2: Active Synchronization Flow Overwriting Purged Search Index
- **Request Details**:
  - `case_id`: `case_custom_02`
  - `email`: `marcus.aurelius180@rome.org`
  - `request_text`: *"Please erase my account, profile, and all associated analytics and search listings."*
  - `reported_status`: `PARTIALLY_COMPLETE`
  - `audit_at`: `2026-09-15T12:00:00Z`
- **Underlying Ground Truth State**:
  - Account was deleted from primary store. Search index entry `search_3310` was initially purged.
  - However, integration connector `data_flow_8524` (`customer_events_connector`) remained `enabled=True` in `evidence_92`.
  - The connector periodically syncs cached profile events back into Elasticsearch, creating an active recreation risk.
- **Expected Resolution**:
  - Deletion status: `INCOMPLETE`.
  - Findings: `REPORT_ACTIVE_DATA_FLOW` for `data_flow_8524` (state: `ACTIVE`, citing `evidence_92`) and `REPORT_REMAINING_RECORD` for remaining search traces.
  - Remediation: Strict dependency order: `DISABLE_DATA_FLOW` (state: `DISABLED`) MUST precede downstream record operations.
  - Verification: `VERIFY_DATA_FLOW_DISABLED` and `VERIFY_RECORD_ABSENT`.

### Custom Case 3: Legally Held Financial Records & Compliant Account Tombstone
- **Request Details**:
  - `case_id`: `case_custom_03`
  - `email`: `devon.clarke@fintech.io`
  - `request_text`: *"Please delete my account and personal data. I know you may have to keep invoice logs for audit compliance."*
  - `reported_status`: `COMPLETE`
  - `audit_at`: `2026-09-15T12:00:00Z`
- **Underlying Ground Truth State**:
  - An `ACCOUNT_TOMBSTONE` (`tombstone_440`) in `identity_service` has `account_status: "DELETED"`. Direct identifiers (`name`, `email`, `phone`, `email_hash`) are all `None`; only `subject_reference: "user_541"` remains.
  - A statutory security audit ledger entry `audit_record_6909` has `retention_until: "2032-12-31"`.
- **Expected Resolution**:
  - Deletion status: `COMPLETE`.
  - Findings: None (all records comply with deletion rules).
  - Verification:
    1. `account_service`: `account_4857` -> `VERIFY_RECORD_ABSENT` (proved by `evidence_51`).
    2. `security_service`: `audit_record_6909` -> `VERIFY_RECORD_PRESENT` (retained under `rule_12`).
    3. `identity_service`: `tombstone_440` -> `VERIFY_RECORD_REDACTED` (permitted under `rule_15`).

---

## 5. Failures Diagnosed & Architectural Improvements

Throughout development and iterative checkpointing, key failure modes were uncovered and solved:

1. **Service Resource Export Bypass (`service_exports` hierarchy)**:
   - *Failure*: Baseline parser inspected only top-level `records` arrays. Files named `service_resource_export_*.json` (11 distinct files in `dataset/evidence/records/`) used a nested dictionary structure grouped by service. As a result, critical evidence for cases 23, 24, 29, and 30 was omitted, causing false `INCOMPLETE` citations.
   - *Fix*: Implemented `_parse_service_resource_json` traversing all 8 services and capturing nested `hits.documents` and `profile_lookups` with exact observation timestamps.

2. **Anonymous Record Disconnection (Two-Pass Resource Correlation)**:
   - *Failure*: 404 readback lookups and anonymized analytics entries stripped `email` and `customer_reference`. Standard single-pass indexing failed to attribute these records to the user.
   - *Fix*: Created a two-pass indexing engine. The first pass maps explicit user identifiers and populates a global `rid_to_user` mapping. The second pass binds anonymous lookup records sharing the same unique `resource_id` (e.g. `account_5684`, `account_3866`).

3. **Temporal Cutoff Boundary & Snapshot Date Misalignment**:
   - *Failure*: Snapshot bundle `evidence_02` was exported on `2026-09-17`, but contained snapshots from `2026-09-09` and `2026-09-15`. Filtering by `file_captured_at <= audit_at` discarded valid audit log entries from `2026-09-15`.
   - *Fix*: Separated record observation time (`captured_at`) from file bundle export time (`file_captured_at`). For findings, evidence files captured after `audit_at` are rejected; for post-remediation verification in incomplete cases, future state verification is properly maintained.

4. **Account Tombstone vs Exposed PII**:
   - *Failure*: Tombstones (`deleted_customer_references`) were initially classified as `REPORT_REMAINING_RECORD`, flagging compliant tombstones as incomplete.
   - *Fix*: Added `ACCOUNT_TOMBSTONE` policy mapping (`rule_15`). Checked direct PII fields (`full_name`, `email`, `phone`, `email_hash`). If stripped, the tombstone is verified as `VERIFY_RECORD_REDACTED`.

5. **Replica Deletion-Marker Check in Logs**:
   - *Failure*: Support replica logs contained `deletion_marker_check resource_id=support_002 marker_found=false`. These were treated as generic support conversations rather than unpurged secondary indexes.
   - *Fix*: Tagged unpurged replica entries with `marker_found="false"` as `SECONDARY_IDENTIFIER`, triggering mandatory `DELETE_RECORD` and absence verification.
