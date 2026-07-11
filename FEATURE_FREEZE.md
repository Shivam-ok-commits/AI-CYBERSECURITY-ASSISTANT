# Feature Freeze Audit — Sentinel v1.1

This document catalogs every TODO, FIXME, HACK, disabled code path, feature flag, experimental component, temporary code, and dead code path discovered across the repository.

---

## 1. Feature Flags & Gated Features

| # | Location | Code | Status | Notes |
|---|----------|------|--------|-------|
| FF1 | `src/api.py:79` | `if os.getenv("ENABLE_RATE_LIMIT", "").lower() == "true":` | **Gated** | Rate limiting middleware is disabled by default. Must set `ENABLE_RATE_LIMIT=true` env var. Middleware is registered inside this conditional — without it, no rate limiting exists anywhere. |
| FF2 | `frontend/src/pages/AI/AIAssistant.tsx:33` | `useQuery({ ..., enabled: false })` | **Hard-disabled** | The AI recommendations query is hardcoded to `enabled: false`. Feature accepts input but never executes. Dead code. |
| FF3 | `frontend/src/pages/Settings.tsx:471-472` | HTTP/HTTPS Proxy settings with `onChange={() => {}}` and `helperText="Coming soon"` | **Placeholder** | Proxy settings accept no input and show "Coming soon". Inputs are non-functional. |

---

## 2. Disabled Code Paths

| # | Location | Line(s) | Issue |
|---|----------|---------|-------|
| DC1 | `src/services/ai_providers/__init__.py` | 32-34 | Dead code path: when a provider is created and `is_available()` returns `False`, the code imports `FALLBACK_RESPONSES` and `get_prompt` but does nothing with them. The `return _current_provider` at line 37 makes lines 33-34 unreachable. |
| DC2 | `src/services/dashboard.ts` (via frontend `api/dashboard.ts`) | 9-16 | `getLogStats()`, `getThreatStats()`, `getInvestigationStats()` are defined in both frontend API and backend but **never called** from any frontend page. Dashboard uses `getFullDashboard()` instead. |
| DC3 | `src/services/case_management.py:44-45` | `_dict_or_none()` | Defined but never called anywhere. Intended for case data conversion but unused. |
| DC4 | `src/services/detection_engine.py:25-26` | `_dict_or_none()` | Same unused helper duplicated in detection engine. |
| DC5 | `src/utils/` | Entire directory | `utils/__init__.py` exists but is empty. Never imported anywhere. |

---

## 3. Experimental Features

| # | Location | Code | Notes |
|---|----------|------|-------|
| EX1 | `src/schemas/detection.py:56` | `status: str = "experimental"` | Sigma/YARA detection rules have an `experimental` status tier. This is an intentional feature (matching the Sigma spec), not dead code. Used in `SIGMA_STATUSES = ("experimental", "stable", "deprecated", "unsupported")`. **Intentional.** |
| EX2 | `src/database.py:479` | `status TEXT NOT NULL DEFAULT 'experimental' CHECK(status IN ('experimental','stable','deprecated','unsupported'))` | Detection rules table stores status with the same four tiers. **Intentional.** |
| EX3 | `electron/src/window.ts:50` | `experimentalFeatures: false` | Electron `webPreferences.experimentalFeatures` explicitly disabled. This is a security hardening, not a toggle. **Intentional.** |

---

## 4. Stub / Placeholder Components

| # | Location | Lines | Issue |
|---|----------|-------|-------|
| S1 | `frontend/src/pages/Reports.tsx` | 1-38 | **Reports page is a stub.** Contains only an `EmptyState` component with "No reports generated yet" and an Electron "Open Reports Folder" button. No report listing, generation, preview, or export UI exists. Backend has `POST /cases/{id}/reports` but frontend never calls it. |
| S2 | `frontend/src/pages/Settings.tsx:471-472` | Proxy settings | Two `Input` components that accept no input (`onChange={() => {}}`), value hardcoded to `""`, helper text says "Coming soon". Non-functional UI. |

---

## 5. Temporary / Hardcoded Values

| # | Location | Line | Value | Issue |
|---|----------|------|-------|-------|
| T1 | `src/config.py:31` | `os.getenv("JWT_SECRET_KEY", "change-me-in-production")` | Hardcoded default JWT secret | If the env var is not set, the literal string `"change-me-in-production"` is used as the JWT signing key. Anyone who knows this default can forge tokens. |
| T2 | `src/api.py:58` | `allow_origins=["*"]` | CORS wildcard | Temporary CORS setting for development. Invalid when combined with `allow_credentials=True`. Will break in production with credentialed requests. |
| T3 | `frontend/src/pages/Settings.tsx:184-193` | API key field definitions | Provider-specific API key field metadata | These field definitions work correctly but embed provider-specific labels, types, and placeholders inline rather than in a config. Functional but not configurable. |
| T4 | `src/routers/logs.py:74` | `f"{user['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"` | Filename construction | Original filename is embedded in the saved path without sanitization. Path traversal risk. |

---

## 6. Unused Imports / Dead Code

| # | File | Line | Import / Code |
|---|------|------|---------------|
| U1 | `src/services/ioc_extractor.py` | 1 | `import hashlib` — never used. |
| U2 | `src/services/case_management.py` | 2 | `import uuid` — never used. |
| U3 | `src/services/log_parser.py` | 244-252 | `_xml_text()` function defined but never called. |
| U4 | `src/services/ai_explainer.py` | 261-266 | IP/domain extraction regex — duplicates logic from `ioc_extractor.py`. |
| U5 | `src/services/detection_engine.py` | 21 | `_ts()` helper — duplicate of identical `_ts()` in `dashboard.py:18`. |
| U6 | `src/services/dashboard.py` | 18 | `_ts()` helper — duplicate of identical `_ts()` in `detection_engine.py:21`. |

---

## 7. Unreachable Endpoints

| # | Endpoint | Issue |
|---|----------|-------|
| R1 | `GET /api/v1/logs/stats/global` | Route ordering bug: `GET /logs/{log_id}` (line 139) is defined before `GET /logs/stats/global` (line 285). FastAPI resolves by definition order, so `/logs/stats/global` matches `/{log_id}` first. **Unreachable.** |
| R2 | `DELETE /api/v1/cases/{case_id}` | Calls `DELETE FROM case_notes WHERE case_id = ?` but `case_notes` table does not exist. **Always crashes.** |
| R3 | `POST /api/v1/cases/{case_id}/evidence` | Requires `evidence_type` field with no default, but frontend never sends it. **Always returns 422.** |
| R4 | `GET /api/v1/threat/feed` | Returns an object but frontend calls `.map()` on it. **Causes blank page crash.** |

---

## 8. Broken / Non-Functional Features

| # | Feature | Issue |
|---|---------|-------|
| B1 | **AI Recommendations** | Query hardcoded to `enabled: false`. Even if enabled, response shape mismatch would crash (frontend expects array, backend returns object). |
| B2 | **IOC Enrichment display** | Frontend reads `data.source`, `data.malicious` at top level. Backend nests them under `data.reputation.*`. All enrichment results show "N/A". |
| B3 | **Case Evidence display** | Backend `get_case()` returns only the `cases` table row without joining evidence or comments. Frontend reads `detail.evidence` and `detail.comments` which are always `undefined`. |
| B4 | **Case Evidence creation** | Frontend sends `{description, source, content}` but backend requires `evidence_type` (no default). Always fails with 422. |
| B5 | **Dashboard stats** | `dict(conn.execute(...GROUP BY...).fetchall())` produces wrong results for all stats aggregation. All dashboard numbers are incorrect. |
| B6 | **Electron log upload** | `atob()` in `useElectron.ts:90` corrupts binary data. Only text files upload correctly. |
| B7 | **AI Chat session switching** | Chat messages stored in local React state, not loaded from API. Switching sessions always shows empty chat. |

---

## 9. Unused API Endpoints (Defined in Backend, No Frontend Consumer)

| # | Endpoint | Backend File |
|---|----------|-------------|
| UE1 | `GET /api/v1/dashboard/alerts` | `src/routers/dashboard.py` (alert list) |
| UE2 | `GET /api/v1/dashboard/logs/stats` | `src/routers/dashboard.py` (log stats) |
| UE3 | `GET /api/v1/dashboard/threat/stats` | `src/routers/dashboard.py` (threat stats) |
| UE4 | `GET /api/v1/dashboard/investigations/stats` | `src/routers/dashboard.py` (investigation stats) |
| UE5 | `GET /api/v1/dashboard/severity-chart` | `src/routers/dashboard.py` (chart data) |
| UE6 | `GET /api/v1/dashboard/threat-distribution` | `src/routers/dashboard.py` (threat dist) |
| UE7 | `GET /api/v1/dashboard/summary/export` | `src/routers/dashboard.py` (export) |
| UE8 | `POST /api/v1/cases/{id}/reports` | `src/routers/case_management.py` (report gen) |
| UE9 | `GET /api/v1/cases/templates` | `src/routers/case_management.py` (report templates) |
| UE10 | `GET /api/v1/cases/search/find` | `src/routers/case_management.py` (search) |
| UE11 | `GET /api/v1/cases/archived/list` | `src/routers/case_management.py` (archived) |
| UE12 | `GET /api/v1/cases/audit/logs` | `src/routers/case_management.py` (audit) |
| UE13 | `GET /api/v1/ai/prompts` | `src/routers/ai.py` (prompt templates) |
| UE14 | `GET /api/v1/ai/providers/active` | `src/routers/ai.py` (active provider) |

---

## 10. Unauthenticated Endpoints (Missing `Depends(get_current_user)`)

| # | Router | Endpoints Without Auth |
|---|--------|----------------------|
| UH1 | `src/routers/detection.py` | 20+ endpoints: rules CRUD, sigma CRUD, yara CRUD, hunts CRUD, analytics, validate, test — **NO auth** |
| UH2 | `src/routers/enterprise.py` | 15+ endpoints: organizations, settings, logs, backups, billing, audit — **NO auth** (except `/backups`) |
| UH3 | `src/routers/dashboard.py` | 10+ endpoints: executive summary, alert stats, investigation stats, threat stats, log stats, charts — **NO auth** |
| UH4 | `src/routers/threat_intel.py` | `POST /threat/extract` — **NO auth** |

---

## Summary

| Category | Count |
|----------|-------|
| Feature Flags (gated/disabled) | 3 |
| Disabled Code Paths | 5 |
| Experimental Features (intentional) | 3 |
| Stub / Placeholder Components | 2 |
| Temporary / Hardcoded Values | 4 |
| Unused Imports / Dead Code | 6 |
| Unreachable Endpoints | 4 |
| Broken / Non-Functional Features | 7 |
| Unused API Endpoints | 14 |
| Unauthenticated Endpoints | ~50 |
| **Total** | **~98** |

All issues target the `stabilization/v1.1` branch. No code has been modified.
