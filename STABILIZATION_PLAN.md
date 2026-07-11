# Stabilization Plan — Sentinel v1.1

---

## Summary

This report catalogs **all known stability issues** across the Sentinel codebase as of the `stabilization/v1.1` branch. No fixes have been applied. Each issue is ranked Critical, High, Medium, or Low.

| Severity | Backend | Frontend | Electron | Total |
|----------|---------|----------|----------|-------|
| **Critical** | 9 | 1 | 0 | 10 |
| **High** | 12 | 9 | 0 | 21 |
| **Medium** | 22 | 16 | 0 | 38 |
| **Low** | 15 | 14 | 0 | 29 |
| **Total** | 58 | 40 | 0 | **98** |

---

## 1. Critical Bugs

| # | Area | File | Line | Issue |
|---|------|------|------|-------|
| C1 | Backend | `src/services/dashboard.py` | 109-117 | `dict(conn.execute(...GROUP BY...).fetchall())` is called on a list of `Row` objects. This does NOT produce `{severity: count}` — it produces garbage. Affects `get_alert_stats`, `get_investigation_stats`, `get_threat_intel_stats`, `get_log_stats`, `get_severity_chart_data`, `get_threat_distribution`. **All dashboard stats are wrong.** |
| C2 | Backend | `src/database.py` | 407 vs 689 | The `notifications` table is created **twice** with different schemas. The first (line 407) has `title`, `message`, `type`, `is_read`, `user_id`. The second (line 689) has `channel`, `event`, `config`, `enabled`, `user_id`. The second `CREATE TABLE` fails silently. Enterprise notification inserts fail. |
| C3 | Backend | `src/services/case_management.py` | 134 | `DELETE FROM case_notes WHERE case_id = ?` — the `case_notes` table **does not exist** anywhere in `database.py`. Case deletion always crashes with `OperationalError`. |
| C4 | Backend | `src/routers/logs.py` | 139 vs 285 | Route ordering bug: `GET /logs/{log_id}` (line 139) is defined **before** `GET /logs/stats/global` (line 285). FastAPI resolves by definition order, so `/logs/stats/global` is captured by `/{log_id}` with `log_id = "stats"`, causing a DB lookup for integer ID — returns 404. **Log stats endpoint is unreachable.** |
| C5 | Backend | `src/schemas/case_management.py` | 46 | `is_archived: bool` but DB column is `INTEGER NOT NULL DEFAULT 0`. SQLite returns `0`/`1` as Python `int`. Pydantic v2 by default does **not** coerce `int` to `bool`. Reading any case with `is_archived` set will fail Pydantic validation. |
| C6 | Backend | Multiple routers | Various | **Many endpoints lack authentication.** Detection endpoints (rules CRUD, sigma, yara, hunts, analytics) — at least 20 endpoints. Enterprise endpoints (settings, logs, backups, billing, audit) — at least 15 endpoints. Dashboard endpoints (executive summary, alert stats, investigation stats, threat stats, log stats, charts) — at least 10 endpoints. All accessible without a token. |
| C7 | Backend | `src/config.py` | 31 | Default JWT secret is hardcoded: `os.getenv("JWT_SECRET_KEY", "change-me-in-production")`. If deployment forgets to set the env var, JWT tokens can be forged. The code itself warns about this but does not enforce. |
| C8 | Backend | `src/routers/auth.py` | 45-54 | **No rate limiting on login endpoint.** Brute-force attacks are possible. The middleware rate limiter in `api.py` is gated behind `ENABLE_RATE_LIMIT` env var which defaults to off. |
| C9 | Backend | `src/api.py` | 58 | CORS configured with `allow_origins=["*"]` and `allow_credentials=True`. Per CORS spec, `allow_credentials` cannot be used with wildcard origin. Browsers will ignore the wildcard, breaking credentialed requests. |
| C10 | Frontend | All pages | — | **No Error Boundary anywhere in the app.** Any unhandled render error (`.map` on undefined, null pointer, type error) unmounts the entire React tree. The Threat Intelligence blank page is a direct consequence — `feed.map()` throws because `feed` is an object, not an array. |

---

## 2. Runtime Errors

| # | Area | File | Line | Issue | Severity |
|---|------|------|------|-------|----------|
| R1 | Frontend | `frontend/src/pages/ThreatIntel/ThreatIntel.tsx` | 111 | `feed?.map(...)` — `feed` is an object `{latest_cves, latest_malware, ...}` from `GET /threat/feed`, not an array. `TypeError: feed.map is not a function` — **page crashes, blank screen.** | **Critical** |
| R2 | Frontend | `frontend/src/pages/AI/AIAssistant.tsx` | 33 | `recommendations` query hardcoded to `enabled: false`. **Feature never executes.** | **High** |
| R3 | Frontend | `frontend/src/pages/AI/AIAssistant.tsx` | 19 | Chat messages not restored when switching sessions. `chatMessages` is local React state, never loaded from API. Switching sessions always shows empty chat. | **High** |
| R4 | Frontend | `frontend/src/pages/Settings.tsx` | 117 | `if (!token) return null` — renders blank page if user navigates to settings before auth restores. | **Medium** |
| R5 | Frontend | `frontend/src/App.tsx` / `frontend/src/pages/Settings.tsx` | 30 / 44 | `/mfa` route renders `<Settings />` which always starts on "general" tab. User expects to see MFA settings. | **Medium** |
| R6 | Backend | `src/services/backup.py` | 31 | SQLite backup copies database file while app may have active connections, then opens a new connection to write backup record. Can cause `sqlite3.OperationalError: database is locked`. | **High** |
| R7 | Backend | `src/config.py` | 33 | `int(os.getenv(...))` called at class definition time. If env var is not a valid integer, the entire app crashes at import with `ValueError`. | **High** |
| R8 | Backend | `src/routers/threat_intel.py` | 59-63 | `body.get("text") or text` — if `body` is `None` (the default), this raises `AttributeError` before reaching the `or` fallback. | **High** |
| R9 | Backend | `src/services/threat_intel.py` | 44 | `result["threat_score"]` accessed without `.get()` — `KeyError` if called with partial result from any code path that doesn't set `threat_score`. | **Medium** |

---

## 3. API Contract Mismatches

| # | Endpoint | Frontend Call | Backend Reality | Severity |
|---|----------|---------------|-----------------|----------|
| M1 | `GET /threat/feed` | Expects `Array<{indicator, type, risk, source, updated}>` — calls `.map()` on response | Returns `{latest_cves: [], latest_malware: [], ...}` (object, not array) | **Critical** |
| M2 | `POST /cases/{id}/evidence` | Sends `{description, source, content}` — no `evidence_type` | Requires `evidence_type: str` with no default — **422 error every time** | **Critical** |
| M3 | `GET /cases/{id}` | Reads `detail.evidence`, `detail.comments`, `detail.attack_stage`, `detail.assignee` | Returns `CaseResponse` which has **none** of these fields. Evidence and comments are never joined. | **Critical** |
| M4 | `GET /threat/lookup` | Reads `data.source`, `data.malicious`, `data.risk`, `data.country`, `data.tags` at top level | Backend nests these under `data.reputation.*` — all frontend reads return `undefined` | **High** |
| M5 | `POST /ai/investigate` | Reads `data.analysis \|\| data.response \|\| JSON.stringify(data)` | Backend returns `{summary, suspicious_patterns, ...}` — `analysis` and `response` don't exist | **Medium** |
| M6 | `POST /ai/recommendations` | Frontend treats response as array (`.map`, `.length`) | Backend returns object `{next_steps, containment, recovery, patching, detection_improvements}` | **High** |
| M7 | `GET /logs/{id}` | Reads `total_events`, `suspicious_count`, `format`, `filepath`, `event_types` | No `response_model` defined — shape is undocumented, may change | **Medium** |
| M8 | `GET /logs/{id}/timeline` | Expects flat list with `timestamp`, `event_type`, `source_ip`, `severity`, `details` | No `response_model` — `TimelineBlock` schema exists but isn't used | **Medium** |
| M9 | `GET /dashboard/summary` | Accesses `executive.total_iocs`, `executive.critical_alerts`, `log_stats.total_events` | No `response_model` — all untyped | **High** |
| M10 | `POST /detection/rules/{id}/test` | Sends `{sample_data: [...]}` | `sample_data: list[str]` — no max length enforced | **Medium** |

---

## 4. Frontend Issues

| # | File | Line | Issue | Severity |
|---|------|------|-------|----------|
| F1 | All pages | — | No Error Boundary — any runtime error crashes entire app | **Critical** |
| F2 | `frontend/src/pages/Dashboard.tsx` | 24-31 | Heavy use of `as Record<string, unknown>` — completely bypasses type safety | **High** |
| F3 | `frontend/src/api/*.ts` | All | 0 typed API response interfaces across 7 API modules. All return raw `any`. | **High** |
| F4 | `frontend/src/pages/Settings.tsx` | 56-81 | `loadSettings()` has no try/catch — perpetual loading if Electron IPC fails | **Medium** |
| F5 | `frontend/src/pages/Dashboard.tsx` | 21-22 | No `isLoading` check — stat cards show zeros until data arrives | **Medium** |
| F6 | `frontend/src/pages/Detection/Detection.tsx` | All | No loading states for any of 6 queries | **Medium** |
| F7 | `frontend/src/pages/Cases/Cases.tsx` | 18-19 | No loading states for cases/detail queries | **Medium** |
| F8 | `frontend/src/pages/ThreatIntel/ThreatIntel.tsx` | 16 | No loading state for feed query | **Medium** |
| F9 | `frontend/src/pages/Logs/LogAnalysis.tsx` | 16-26 | No loading states for analyses/detail/timeline | **Medium** |
| F10 | `frontend/src/pages/Plugins.tsx` | 3,49,54,63 | Direct `api` import bypasses typed API layer | **Medium** |
| F11 | `frontend/src/pages/AI/AIAssistant.tsx` | 26,88,119 | Fallback chains `data.response \|\| data.reply \|\| data.message` indicate unknown API contract | **Medium** |
| F12 | `frontend/src/pages/Settings.tsx` | 89-94 | `updateSetting` fires IPC on every keystroke — no debounce | **Medium** |
| F13 | `frontend/src/pages/Settings.tsx` | 63-67,91-93 | Settings not persisted in browser mode (only Electron) | **Medium** |
| F14 | `frontend/src/pages/Settings.tsx` | 1-560 | Single file at 560 lines with 5 sub-components | **Medium** |
| F15 | `frontend/src/pages/Reports.tsx` | 1-38 | Report page is a stub — EmptyState only, no generation, no listing, no export | **Medium** |
| F16 | `frontend/src/pages/Logs/LogAnalysis.tsx` | 149 | Inconsistent null handling: `detail.total_events` without `??` vs other fields with `??` | **Low** |
| F17 | `frontend/src/pages/Logs/LogAnalysis.tsx` | 52-54 | Browser upload via axios may fail silently in error handler (generic toast only) | **Medium** |
| F18 | `frontend/src/components/Toast.tsx` | 24 | `setTimeout` not cleared on unmount — minor memory leak | **Low** |
| F19 | `frontend/src/pages/Detection/Detection.tsx` | Various | No `isPending` on mutation buttons — duplicate submissions possible | **Low** |
| F20 | `frontend/src/pages/Logs/LogAnalysis.tsx` | 83 | File input not reset after upload — cannot re-upload same file | **Low** |
| F21 | `frontend/src/context/AuthContext.tsx` | 72 | `catch (err: any)` — type-erased error | **Low** |
| F22 | `frontend/src/pages/Dashboard.tsx` | 45 | `as string \|\| "OK"` — type assertion lie on possibly undefined value | **Low** |

---

## 5. Backend Issues

| # | File | Line | Issue | Severity |
|---|------|------|-------|----------|
| B1 | `src/services/case_management.py` | 134 | Delete on non-existent `case_notes` table crashes case deletion | **Critical** |
| B2 | `src/routers/logs.py` | 54, 74-77 | Upload reads entire file into memory then validates size. OOM possible. No try/except on file write. | **High** |
| B3 | `src/routers/logs.py` | 74 | File path traversal: `file.filename` embedded in destination path without sanitization. `os.path.join` with `../` escapes uploads dir. | **High** |
| B4 | `src/routers/logs.py` | 70 | `parse_log(text, source_type)` called without try/except — any parser exception returns 500 | **Medium** |
| B5 | `src/services/backup.py` | 21 | `shutil.copy2` without SQLite exclusive lock — backup may be corrupted if writes happen during copy | **High** |
| B6 | `src/services/detection_engine.py` | 341-397 | `execute_hunt()` is 57 lines with 4 levels of nesting, 5 hunt types in if/elif chains | **Medium** |
| B7 | `src/services/dashboard.py` | All | All stat aggregation uses `dict()` on `Row` list — produces wrong results (see C1) | **Critical** |
| B8 | `src/utils/` | — | `utils/` directory exists but is empty — dead code | **Low** |
| B9 | `src/services/log_parser.py` | 244-252 | `_xml_text()` defined but never called | **Low** |
| B10 | `src/services/ioc_extractor.py` | 1 | `import hashlib` unused | **Low** |
| B11 | `src/services/case_management.py` | 2 | `import uuid` unused | **Low** |
| B12 | `src/services/case_management.py` | 44-45 | `_dict_or_none()` defined but never called | **Low** |
| B13 | `src/services/detection_engine.py` | 25-26 | `_dict_or_none()` defined but never called | **Low** |
| B14 | `src/services/ai_explainer.py` | 261-266 | IP/domain extraction regex duplicates `ioc_extractor.py` logic | **Low** |
| B15 | `src/services/detection_engine.py` / `src/services/dashboard.py` | 21 / 18 | Duplicate `_ts()` helper in both files | **Low** |

---

## 6. Electron Issues

| # | File | Line | Issue | Severity |
|---|------|------|-------|----------|
| E1 | `frontend/src/hooks/useElectron.ts` | 88-96 | `uploadFileViaBackend` uses raw `fetch()` with `atob()` to decode base64 from `file.readBuffer()`. `atob()` corrupts binary data — works only for text files. Binary files (.evtx, .zip) get corrupted on upload. | **High** |
| E2 | `frontend/src/hooks/useElectron.ts` | 99 | `uploadFileViaBackend` returns `void` — caller in `LogAnalysis.tsx` uses `await` on a void promise, masking silent failures | **Medium** |
| E3 | `frontend/src/pages/Reports.tsx` | 10 | `handleOpenFolder` has no try/catch for `api.app.getPath()` IPC call | **Low** |
| E4 | `frontend/src/pages/Cases/Cases.tsx` | 41 | `handleOpenEvidenceFolder` has no try/catch for IPC call | **Low** |

---

## 7. Security Risks

| # | File | Line | Issue | Severity |
|---|------|------|-------|----------|
| S1 | `src/config.py` | 31 | Default JWT secret `"change-me-in-production"` — token forgery if not overridden | **Critical** |
| S2 | `src/routers/auth.py` | 45-54 | **No rate limiting on login** — brute-force attacks possible | **Critical** |
| S3 | Multiple routers | Various | **20+ detection endpoints, 15+ enterprise endpoints, 10+ dashboard endpoints have no authentication** | **Critical** |
| S4 | `src/api.py` | 58 | Invalid CORS: `allow_origins=["*"]` with `allow_credentials=True` — browser ignores wildcard, breaks credentialed requests | **Critical** |
| S5 | `src/routers/auth.py` | 22-42 | No password complexity requirements — empty or trivial passwords accepted | **High** |
| S6 | `src/routers/logs.py` | 54-61 | File read into memory before size validation — OOM from malicious large file | **High** |
| S7 | `src/routers/logs.py` | 74 | Upload path traversal via `file.filename` containing `../` | **High** |
| S8 | `src/routers/threat_intel.py` | 58-64 | `POST /threat/extract` has no auth dependency | **High** |
| S9 | `frontend/src/context/AuthContext.tsx` | 9 | JWT stored in `localStorage` — accessible to any JavaScript in the renderer process | **Medium** |
| S10 | Frontend | All | No CSP enforcement beyond meta tag in dev mode | **Medium** |

---

## 8. Performance Issues

| # | File | Line | Issue | Severity |
|---|------|------|-------|----------|
| P1 | All frontend pages | — | No code splitting (lazy loading). Entire app loaded in single bundle. | **Medium** |
| P2 | `frontend/src/pages/Settings.tsx` | 89-94 | IPC call on every keystroke — no debounce on settings input | **Medium** |
| P3 | Backend `src/routers/logs.py` | 54 | Entire uploaded file read into memory — no streaming | **High** |
| P4 | All frontend components | — | No `React.memo` used — unnecessary re-renders | **Low** |
| P5 | `frontend/src/pages/Cases/Cases.tsx` | 92 | Case list not virtualized — DOM degradation with 1000+ cases | **Low** |
| P6 | `frontend/src/pages/Detection/Detection.tsx` | Various | No `isPending` on mutation buttons — duplicate API calls possible | **Low** |

---

## 9. Code Smells

| # | File | Line | Issue | Severity |
|---|------|------|-------|----------|
| CS1 | `frontend/src/pages/Settings.tsx` | 1-560 | Single file at 560 lines with 5 sub-components | **Medium** |
| CS2 | `frontend/src/pages/Detection/Detection.tsx` | 1-337 | Single file with 5 tabs and duplicated form patterns | **Low** |
| CS3 | `frontend/src/pages/AI/AIAssistant.tsx` | 10 | Chat state split between React state and react-query cache | **Medium** |
| CS4 | `frontend/src/api/dashboard.ts` | 9-16 | `getLogStats`, `getThreatStats`, `getInvestigationStats` defined but never called | **Low** |
| CS5 | `frontend/src/pages/Dashboard.tsx` | 42-47 | `StatCard` `color` prop is raw string (no type safety on Tailwind class) | **Low** |
| CS6 | `frontend/src/pages/Plugins.tsx` | 33-40 | `as const` type-erased by `Record<string, string>` | **Low** |
| CS7 | `frontend/src/pages/Settings.tsx` | 140-168 | 13 props drilled to `SecuritySection` | **Low** |
| CS8 | `src/services/ai_providers/__init__.py` | 32-34 | Dead code path — imports `FALLBACK_RESPONSES` and `get_prompt` but never uses them | **Low** |
| CS9 | `src/services/detection_engine.py` | 341-397 | `execute_hunt()` too complex (57 lines, 4 nesting levels) | **Medium** |
| CS10 | `src/utils/` | — | Empty directory | **Low** |

---

## 10. Missing Tests

| # | Module | Status | Severity |
|---|--------|--------|----------|
| T1 | All frontend (`frontend/src/`, 33 files) | **0 test files exist** | **Medium** |
| T2 | `src/routers/enterprise.py` | No test file | **Medium** |
| T3 | `src/routers/plugins.py` | No test file | **Medium** |
| T4 | `src/services/log_parser.py` | No test file | **High** |
| T5 | `src/services/detector.py` | No test file | **High** |
| T6 | `src/services/ioc_extractor.py` | No test file | **High** |
| T7 | `src/services/ioc_correlation.py` | No test file | **Medium** |
| T8 | `src/services/threat_intel.py` | No test file | **High** |
| T9 | `src/services/threat_feed.py` | No test file | **Medium** |
| T10 | `src/services/ai_chat.py` | No test file | **High** |
| T11 | `src/services/ai_explainer.py` | No test file | **Medium** |
| T12 | `src/services/ai_memory.py` | No test file | **Medium** |
| T13 | `src/services/ai_rag.py` | No test file | **Medium** |
| T14 | `src/services/dashboard.py` | No test file | **Critical** (all stats are broken) |
| T15 | `src/services/case_management.py` | No test file | **High** |
| T16 | `src/services/detection_engine.py` | No test file | **High** |
| T17 | `src/services/notifications.py` | No test file | **Medium** |
| T18 | `src/services/security.py` | No test file | **Medium** |
| T19 | `src/services/backup.py` | No test file | **Medium** |
| T20 | `src/services/multi_tenant.py` | No test file | **Low** |
| T21 | `src/services/integrations.py` | No test file | **Low** |
| T22 | `src/services/billing.py` | No test file | **Low** |
| T23 | `src/services/workers.py` | No test file | **Low** |
| T24 | All AI provider implementations | No test files | **Medium** |
| T25 | All plugin implementations | No test files | **Low** |

Existing tests that DO exist (and should be verified for accuracy):
- `tests/test_api.py` — health check + 404 (2 tests)
- `tests/test_database.py` — database init
- `tests/test_auth.py` — auth endpoints
- `tests/test_logs.py` — log endpoints
- `tests/test_threat_intel.py` — threat intel endpoints
- `tests/test_dashboard.py` — dashboard endpoints
- `tests/test_case_management.py` — case endpoints
- `tests/test_detection.py` — detection endpoints
- `tests/test_ai.py` — AI endpoints

---

## 11. Missing Error Handling

| # | File | Line | Issue | Severity |
|---|------|------|-------|----------|
| EH1 | All frontend pages | — | No React Error Boundary | **Critical** |
| EH2 | `frontend/src/pages/Settings.tsx` | 56-81 | `loadSettings()` no try/catch | **Medium** |
| EH3 | `frontend/src/pages/Settings.tsx` | 83-87 | `loadBackupStatus()` no try/catch | **Medium** |
| EH4 | `frontend/src/hooks/useElectron.ts` | 88-96 | `uploadFileViaBackend` no error handling in binary decode | **High** |
| EH5 | `src/routers/logs.py` | 54, 74-77 | File read/write no try/except | **High** |
| EH6 | `src/routers/logs.py` | 70 | `parse_log()` no try/except | **Medium** |
| EH7 | `src/services/backup.py` | 21 | `shutil.copy2` no exclusive lock — silent corruption | **High** |
| EH8 | `src/services/threat_intel.py` | 35-111 | All external API calls (VT, AbuseIPDB, OTX) silently swallow exceptions | **Medium** |
| EH9 | `src/services/integrations.py` | 29-155 | All 10+ integration API calls swallow exceptions, return `False` silently | **High** |
| EH10 | `src/services/notifications.py` | 34-58 | All notification send failures silently return `False` | **Medium** |
| EH11 | `src/services/security.py` | 22-28 | Rate limit exceeded returns 429 but event is not logged | **Medium** |

---

## 12. Missing Logging

| # | File | Line | Issue | Severity |
|---|------|------|-------|----------|
| L1 | `src/services/auth.py` | 39-43 | Failed token decode — no log | **High** |
| L2 | `src/routers/auth.py` | 49-50 | Login failure — no log | **High** |
| L3 | `src/services/threat_intel.py` | 35-111 | All external API calls fail silently — no log | **Medium** |
| L4 | `src/services/integrations.py` | 29-155 | All integration calls fail silently — no log | **High** |
| L5 | `src/services/notifications.py` | 34-58 | Notification send failures — no log | **Medium** |
| L6 | `src/services/backup.py` | 11-64 | Backup operations — no log at all | **Medium** |
| L7 | `src/services/security.py` | 22-28 | Rate limit hits — no log | **Medium** |
| L8 | `src/database.py` | 28-756 | Database initialization — no log of table creation, migrations, errors | **Medium** |
| L9 | `src/config.py` | 41 | Settings loaded — no log of config state | **Low** |

---

## 13. Broken User Flows

| # | Flow | Step That Breaks | Root Cause | Impact | Severity |
|---|------|------------------|------------|--------|----------|
| UF1 | **Upload log (Electron)** | Binary file encode/decode | `atob()` in `useElectron.ts:90` corrupts binary data | Uploaded files are corrupt | **High** |
| UF2 | **View threat intelligence** | Page render | `feed.map()` crash (M1) | Blank page | **Critical** |
| UF3 | **Enrich an IOC** | Display enrichment results | Field name mismatch (M4) | All values show "N/A" | **High** |
| UF4 | **View case detail** | Load evidence/comments | Backend doesn't return them (M3) | Evidence/comments sections always empty | **Critical** |
| UF5 | **Add evidence to case** | Submit evidence form | Missing required `evidence_type` field (M2) | 422 error every time | **Critical** |
| UF6 | **Delete a case** | Confirm deletion | `case_notes` table doesn't exist (C3) | 500 error | **Critical** |
| UF7 | **View log stats** | Navigate to stats | Route ordering bug (C4) | 404 or wrong data | **Critical** |
| UF8 | **View dashboard** | Load stats | `dict()` on Row list (C1) | All wrong numbers | **Critical** |
| UF9 | **Get AI recommendations** | Query execution | `enabled: false` (R2) | Never loads | **High** |
| UF10 | **Switch AI chat session** | Load previous messages | Chat messages not persisted per session (R3) | Always starts empty | **High** |
| UF11 | **Generate incident report** | Click generate | Reports page is a stub | Nothing happens | **Medium** |
| UF12 | **Configure settings in browser** | Save settings | Settings not persisted in browser mode (F13) | Lost on refresh | **Medium** |
| UF13 | **Open MFA settings** | Navigate to `/mfa` | Wrong default tab (R5) | Shows General, not Security | **Medium** |
| UF14 | **Login (brute force)** | Repeated attempts | No rate limiting (S2) | Vulnerable to brute force | **Critical** |
| UF15 | **NVD CVE lookup** | Query CVE | No auth on detection endpoints (S3) | Anonymous API usage | **High** |

---

## Severity Distribution

```
Critical:  ████████████████▌  10
High:      █████████████████████████████████▌  21
Medium:    █████████████████████████████████████████████████████████████▌  38
Low:       █████████████████████████████████████████████████           29
```

## Recommended Fix Order

### Round 1 — Crash Prevention & Data Integrity (Critical only)
1. Add Error Boundary to frontend (`C10`)
2. Fix Threat Intel feed crash — change frontend to handle object response (`C1 / M1 / R1`)
3. Fix dashboard stats — replace `dict()` on Row list with correct aggregation (`C1 / B7`)
4. Fix route ordering — move `GET /logs/stats/global` before `GET /logs/{log_id}` (`C4`)
5. Remove duplicate `notifications` table — consolidate to single schema (`C2`)
6. Add `evidence_type` to frontend evidence submission (`M2 / UF5`)
7. Fix `get_case()` to join evidence and comments (`M3 / UF4`)
8. Remove `DELETE FROM case_notes` or create the table (`C3 / B1 / UF6`)
9. Fix `is_archived` bool/int mismatch in schema (`C5`)
10. Add auth dependencies to unprotected endpoints (`C6 / S3`)

### Round 2 — Security & Correctness (High)
11. Add login rate limiting (`C8 / S2 / UF14`)
12. Fix CORS configuration (`C9 / S4`)
13. Enforce JWT secret override at startup (`C7 / S1`)
14. Fix Electron binary upload (`E1 / UF1`)
15. Fix IOC enrichment field display (`M4 / UF3`)
16. Add password complexity requirements (`S5`)
17. Fix path traversal in log upload (`S7 / B3`)
18. Stream file upload instead of reading into memory (`S6 / B2 / P3`)
19. Add try/except on file operations in upload (`EH5 / B2`)
20. Add try/except on external API calls (`EH8 / EH9`)

### Round 3 — Completeness (Medium)
21. Add page-level loading states
22. Add API response TypeScript interfaces
23. Implement Reports page
24. Fix AI assistant chat persistence
25. Add logging to auth failures, external API calls, backup operations
26. Debounce settings IPC calls
27. Add try/catch to Settings load functions

### Round 4 — Polish (Low)
28. Remove dead code (unused functions, empty directories)
29. Consolidate duplicate helpers
30. Add React.memo on list components
31. Fix file input reset in LogAnalysis
32. Add test files for critical services
