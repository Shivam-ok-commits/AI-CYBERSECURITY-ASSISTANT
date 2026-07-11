# API Mismatch Report — Frontend vs. Contract

> Generated: 2026-07-11
>
> Comparing every frontend API request against `docs/API_CONTRACT.md`.
>
> `[FE]` = Frontend behavior &nbsp;|&nbsp; `[CX]` = Contract expectation &nbsp;|&nbsp; `[BE]` = Actual backend schema (when contract is wrong)

---

## Summary

| Category | Count |
|----------|-------|
| Total frontend API calls examined | 56 |
| Fully matching | 24 |
| With at least one mismatch | 32 |
| **Unique mismatches identified** | **26** |

---

## Severity Legend

| Severity | Meaning |
|----------|---------|
| 🔴 **CRITICAL** | Breaks functionality — response can't be consumed |
| 🟠 **HIGH** | Wrong data — wrong or missing information displayed |
| 🟡 **MEDIUM** | Incorrect but fallback or partial rendering works |
| 🔵 **LOW** | Minor — cosmetic, unused fields, contract error |

---

## 1. Authentication

---

### `POST /auth/register`

| Aspect | Status | Details |
|--------|--------|---------|
| HTTP method | ✅ | POST |
| URL | ✅ | `/auth/register` |
| Request body | 🟡 | `[FE]` sends `{ username, password }` (no `email`). `[CX]` `email` is optional — backend defaults to `""` then auto-generates one. Functional but surprising — user never controls their email. |
| Response shape | 🟡 | `[FE]` expects `AuthResponse { access_token: string; token_type: string }`. `[CX]` example shows only `{ "access_token" }`. `[BE]` actually returns `{ access_token, token_type: "bearer" }`. Frontend is **correct** for the real backend — contract example is incomplete. |
| Auth | ✅ | None required |

---

### `POST /auth/login`

| Aspect | Status | Details |
|--------|--------|---------|
| All | ✅ | Fully matches |

---

### `POST /auth/login/mfa`

| Aspect | Status | Details |
|--------|--------|---------|
| Usage | 🔵 | `[FE]` — function is **exported but never imported** anywhere in the frontend codebase. Orphaned code. |

---

### `GET /auth/me`

| Aspect | Status | Details |
|--------|--------|---------|
| Response properties | ✅ | `{ id, username, email, role, mfa_enabled }` — all match |

---

### `GET /auth/oauth/{provider}/url`

| Aspect | Status | Details |
|--------|--------|---------|
| Query param name | ✅ | `redirect_uri` matches |
| Response | ✅ | `{ authorization_url }` matches |

---

### `POST /auth/oauth/{provider}/callback`

| Aspect | Status | Details |
|--------|--------|---------|
| Request body | 🔵 | `[FE]` sends `{ provider, code, redirect_uri }`. Backend gets `provider` from both path param AND body — redundant but harmless. |

---

### `POST /auth/mfa/setup`

| Aspect | Status | Details |
|--------|--------|---------|
| Response property name | 🔴 | `[FE]` expects `data.qr_code`. `[CX]` example shows `"uri"`. `[BE]` schema `MfaSetupResponse` has `qr_code: str`. **Contract is wrong** — says `uri` but backend uses `qr_code`. Frontend matches the actual backend. |

---

### `POST /auth/mfa/verify`

| Aspect | Status | Details |
|--------|--------|---------|
| All | ✅ | Fully matches |

---

### `POST /auth/mfa/enable`

| Aspect | Status | Details |
|--------|--------|---------|
| All | ✅ | Fully matches |

---

### `POST /auth/mfa/disable`

| Aspect | Status | Details |
|--------|--------|---------|
| All | ✅ | Fully matches |

---

## 2. Dashboard

---

### `GET /dashboard/summary`

| Aspect | Status | Details |
|--------|--------|---------|
| URL | ✅ | `/dashboard/summary` |
| Auth | ✅ | Required |
| Response `executive` | ✅ | `total_iocs`, `critical_alerts`, `security_health` all match `ExecutiveSummary` schema |
| Response `log_stats` | ✅ | `total_events`, `recent_activity` both match `LogStats` schema |

---

### `GET /dashboard/alerts`

| Aspect | Status | Details |
|--------|--------|---------|
| Usage | 🔵 | `[FE]` — function is **exported but never imported** anywhere. Orphaned code. |

---

### `GET /dashboard/logs/stats`

| Aspect | Status | Details |
|--------|--------|---------|
| Usage | 🔵 | Orphaned — never imported. |

---

### `GET /dashboard/threat/stats`

| Aspect | Status | Details |
|--------|--------|---------|
| Usage | 🔵 | Orphaned. |

---

### `GET /dashboard/investigations/stats`

| Aspect | Status | Details |
|--------|--------|---------|
| Usage | 🔵 | Orphaned. |

---

## 3. Detection

---

### `GET /detection/rules`

| Aspect | Status | Details |
|--------|--------|---------|
| Response properties | ✅ | `id`, `name`, `rule_type`, `category`, `severity`, `hit_count` — all exist in `DetectionRuleResponse` |

---

### `POST /detection/rules`

| Aspect | Status | Details |
|--------|--------|---------|
| Usage | 🔵 | Response data **never read** — only cache invalidation |

---

### `GET /detection/rules/{id}`

| Aspect | Status | Details |
|--------|--------|---------|
| Usage | 🔵 | Orphaned — never imported. |

---

### `PUT /detection/rules/{id}`

| Aspect | Status | Details |
|--------|--------|---------|
| Usage | 🔵 | Orphaned. |

---

### `DELETE /detection/rules/{id}`

| Aspect | Status | Details |
|--------|--------|---------|
| Response handling | 🟡 | `[FE]` does **not** call `.then(r => r.data)` — returns full Axios response object. Contract assumes bare JSON response. Consumer treats response as `void` (never reads it), so it works — but inconsistent with all other API calls. |

---

### `POST /detection/rules/{id}/test`

| Aspect | Status | Details |
|--------|--------|---------|
| HTTP method | ✅ | POST |
| URL | ✅ | `/detection/rules/{id}/test` |
| Request body | ✅ | Sends bare `string[]` — contract notes this as a violation but frontend matches the actual backend API |
| Response `matched` | ✅ | `RuleTestResult.matched` is a `bool` ✓ |

---

### `GET /detection/sigma`

| Aspect | Status | Details |
|--------|--------|---------|
| Response property `log_source` | 🔴 | `[FE]` accesses `r.log_source`. `[BE]` `SigmaRuleResponse` has `logsource_category`, `logsource_product`, `logsource_service` — **no field named `log_source`**. Undefined in rendered UI. |

---

### `POST /detection/sigma`

| Aspect | Status | Details |
|--------|--------|---------|
| Usage | 🔵 | Response data never read. |

---

### `GET /detection/yara`

| Aspect | Status | Details |
|--------|--------|---------|
| Response properties | ✅ | `id`, `name`, `description` all match `YARARuleResponse` |

---

### `POST /detection/yara`

| Aspect | Status | Details |
|--------|--------|---------|
| Usage | 🔵 | Response data never read. |

---

### `GET /detection/hunts`

| Aspect | Status | Details |
|--------|--------|---------|
| Response properties | ✅ | `id`, `name`, `hunt_type`, `created_at` — all match `SavedHuntResponse` |

---

### `POST /detection/hunts`

| Aspect | Status | Details |
|--------|--------|---------|
| Usage | 🔵 | Response data never read. |

---

### `POST /detection/hunts/{id}/execute`

| Aspect | Status | Details |
|--------|--------|---------|
| Usage | 🔵 | Response data never read. |

---

### `GET /detection/hunts/results`

| Aspect | Status | Details |
|--------|--------|---------|
| Response properties | ✅ | `id`, `hunt_type`, `match_type`, `match_value`, `severity`, `created_at` — all match `HuntResultResponse` |

---

### `GET /detection/analytics`

| Aspect | Status | Details |
|--------|--------|---------|
| Response `total_rules` | ✅ | Matches |
| Response `enabled_rules` | ✅ | Matches |
| Response `total_hits` | ✅ | Matches |
| Response `false_positive_rate` | 🟠 | `[FE]` treats as **string** (`"0%"` default). `[BE]` `AnalyticsResponse.false_positive_rate` is **`float`** (e.g. `0.05`). Display renders incorrect value. |
| Response `by_category` | ✅ | `dict` — matches |

---

## 4. Logs

---

### `POST /logs/upload`

| Aspect | Status | Details |
|--------|--------|---------|
| Upload format | ✅ | `FormData` with `file` field. Both axios (web) and raw `fetch()` (Electron) use correct format. |
| Response | 🔵 | Response data never read. |

---

### `GET /logs`

| Aspect | Status | Details |
|--------|--------|---------|
| URL | ✅ | `/logs` |
| Response properties | ✅ | `id`, `filename`, `created_at`, `total_events` (alias), `suspicious_count` — all present |

---

### `GET /logs/{id}`

| Aspect | Status | Details |
|--------|--------|---------|
| Response properties | ✅ | `filename`, `filepath`, `format`, `total_events`, `suspicious_count`, `event_types` — all present |

---

### `GET /logs/{id}/timeline`

| Aspect | Status | Details |
|--------|--------|---------|
| Response properties | ✅ | `timestamp`, `event_type`, `source_ip`, `severity`, `details` — all match |

---

### `GET /logs/stats/global`

| Aspect | Status | Details |
|--------|--------|---------|
| Usage | 🔵 | Orphaned — never imported. |

---

## 5. Cases

---

### `POST /cases` (create)

| Aspect | Status | Details |
|--------|--------|---------|
| HTTP method | ✅ | POST |
| URL | ✅ | `/cases` |
| Request field `assignee` | 🔴 | `[FE]` sends `assignee`. `[BE]` expects `assigned_analyst`. Pydantic silently drops `assignee`. **The case is created without an assignee.** |
| Request field `attack_stage` | 🟠 | `[FE]` sends `attack_stage`. `[BE]` has no such field — silently dropped. |
| Request field `tags` | 🟡 | `[FE]` sends `tags` (string array). `[BE]` has no such field — silently dropped. |
| Request field `case_type` | 🟠 | `[FE]` does **not** send `case_type`. `[BE]` `CaseCreate` defaults to `"incident"`, so it works — but frontend never controls case type. |
| Request field `assigned_analyst` | 🔴 | `[FE]` does **not** send `assigned_analyst`. Backend defaults to `""`. |

---

### `GET /cases`

| Aspect | Status | Details |
|--------|--------|---------|
| Response properties | ✅ | `id`, `title`, `severity`, `status`, `created_at` — all match `CaseListResponse` |

---

### `GET /cases/{id}`

| Aspect | Status | Details |
|--------|--------|---------|
| Response `assignee` | 🔴 | `[FE]` accesses `detail.assignee`. `[BE]` `CaseResponse` has `assigned_analyst`. **Undefined** in UI. |
| Response `attack_stage` | 🔴 | `[FE]` accesses `detail.attack_stage`. `[BE]` `CaseResponse` has **no such field**. Always shows `"—"`. |
| Response `evidence` | 🔴 | `[FE]` accesses `detail.evidence` (array). `[BE]` `CaseResponse` has **no `evidence` field**. Never renders evidence. |
| Response `evidence[].type` | 🟠 | `[FE]` accesses `e.type`. `[BE]` `EvidenceResponse` has `evidence_type` — would be **wrong property name** if evidence were returned. |
| Response `comments` | 🔴 | `[FE]` accesses `detail.comments` (array). `[BE]` `CaseResponse` has **no `comments` field**. Never renders comments. |
| Response `comments[].user` | 🟠 | `[FE]` accesses `c.user`. `[BE]` `CommentResponse` has `username` — would be **wrong property name** if comments were returned. |

---

### `PUT /cases/{id}`

| Aspect | Status | Details |
|--------|--------|---------|
| Usage | 🔵 | Orphaned — never imported. |

---

### `POST /cases/{id}/archive`

| Aspect | Status | Details |
|--------|--------|---------|
| Usage | 🔵 | Orphaned. |

---

### `POST /cases/{id}/evidence`

| Aspect | Status | Details |
|--------|--------|---------|
| Request field `content` | 🟠 | `[FE]` sends `content` (string). `[BE]` `EvidenceCreate` has **no `content` field** — silently dropped. |
| Request field `evidence_type` | 🟡 | `[FE]` sends `evidence_type?` — valid but optional in backend. |
| Request field `source` | ✅ | Matches |
| Request field `description` | ✅ | Matches |
| Response | 🔵 | Response data never read. |

---

### `POST /cases/{id}/comments`

| Aspect | Status | Details |
|--------|--------|---------|
| Request field name | 🟡 | `[FE]` sends `{ content, internal? }`. `[BE]` expects `{ content, is_internal }`. The field `internal` is silently dropped; the default `is_internal = False` is used. |

---

### `POST /cases/{id}/reports`

| Aspect | Status | Details |
|--------|--------|---------|
| Request body | 🟡 | `[FE]` sends `{ format }`. `[BE]` `ReportGenerateRequest` expects `title`, `executive_summary`, etc. — `format` is not a field. The backend initializes with defaults. |
| Usage | 🔵 | Orphaned — never imported/used. |

---

## 6. AI

---

### `POST /ai/sessions`

| Aspect | Status | Details |
|--------|--------|---------|
| Request body | ✅ | `{ title }` — backend defaults `context_type` and `context_id` |
| Response `id` | ✅ | `ChatSessionResponse.id` matches |

---

### `GET /ai/sessions`

| Aspect | Status | Details |
|--------|--------|---------|
| Response properties | ✅ | `id`, `title` — both match `ChatSessionResponse` |

---

### `POST /ai/chat`

| Aspect | Status | Details |
|--------|--------|---------|
| Request body | ✅ | `{ session_id, message }` — matches `ChatRequest` |
| Response `response` | 🟠 | `[FE]` accesses `data.response || data.reply || data.message` (fallback chain). `[BE]` `ChatResponse` has `reply`. The first fallback `response` is **undefined**, the second `reply` **works**. `message` is also undefined. The fallback chain is fragile — only `reply` exists. |

---

### `POST /ai/investigate`

| Aspect | Status | Details |
|--------|--------|---------|
| Request `log_id` | 🔴 | `[FE]` never sends `log_id`. Only sends `{ evidence }`. Backend falls through to the simple `explain_general()` path. The AI-powered event-based investigation is **never triggered**. |
| Response `analysis` | 🔴 | `[FE]` accesses `data.analysis || data.response || JSON.stringify(data)`. `[BE]` `InvestigationResponse` has `summary`. Neither `analysis` nor `response` exists in the real response. The fallback `JSON.stringify(data)` renders raw JSON to the user. **Data is never correctly displayed.** |

---

### `POST /ai/recommendations`

| Aspect | Status | Details |
|--------|--------|---------|
| Hardcoded logId | 🔴 | `[FE]` calls `getRecommendations(0)` — hardcoded `logId = 0`. Backend looks for log with id 0 (never exists), always returns empty arrays. **Functionally broken.** |
| Response shape assumption | 🔴 | `[FE]` treats response as **array** (`recommendations?.length > 0`, `.map()`). `[BE]` `RecommendationResponse` returns a **single object** `{ next_steps, containment, recovery, patching, detection_improvements }`. Never enters the `.map()` branch. |

---

### `POST /ai/explain`

| Aspect | Status | Details |
|--------|--------|---------|
| URL | ✅ | `/ai/explain` |
| Request | ✅ | `{ text }` matches `ExplainRequest` |
| Response `explanation` | ✅ | Falls back through `data.explanation || data.response || JSON.stringify(data)`. First branch `explanation` exists in `ExplainResponse`. ✓ |

---

### `GET /ai/providers`

| Aspect | Status | Details |
|--------|--------|---------|
| All | ✅ | Fully matches |

---

### `GET /ai/providers/active`

| Aspect | Status | Details |
|--------|--------|---------|
| Usage | 🔵 | Orphaned — never imported. |

---

### `POST /ai/providers/switch`

| Aspect | Status | Details |
|--------|--------|---------|
| Usage | 🔵 | Orphaned. |

---

## 7. Threat Intelligence

---

### `POST /threat/extract`

| Aspect | Status | Details |
|--------|--------|---------|
| HTTP method | ✅ | POST |
| URL | ✅ | `/threat/extract` |
| Auth | 🟠 | `[CX]` flags no-auth as violation. `[FE]` sends auth because axios interceptor adds the token automatically. **Frontend implicitly sends auth; backend ignores it.** Works but inconsistent. |
| Request body | ✅ | `{ text }` — matches |
| Response `ips`, `domains`, `urls`, `emails` | ✅ | All match `IOCExtractionResponse` |
| Response `hashes` type | 🟠 | `[BE]` `IOCExtractionResponse.hashes` is `list[dict]` — each item is `{ value: string, type: string }`. `[FE]` treats all IOC types as `string[]` and renders with `.map((item: string) => ...)`. For hashes, this renders `[object Object]` instead of the actual value. |

---

### `GET /threat/lookup`

| Aspect | Status | Details |
|--------|--------|---------|
| HTTP method | ✅ | GET |
| URL | ✅ | `/threat/lookup` |
| Query param `indicator` | ✅ | Matches |
| Response nesting | 🔴 | `[FE]` accesses properties **flat** on the response root (`data.source`, `data.malicious`, etc.). `[BE]` returns `{ indicator, indicator_type, reputation: { threat_score, country, ... } }`. The actual data is nested under `data.reputation.*`. **No frontend property access resolves correctly.** |
| Response `source` | 🔴 | `[FE]` expects `data.source` (string). `[BE]` has `data.reputation.sources` (array of strings). **Wrong nesting + wrong type.** |
| Response `malicious` | 🔴 | `[FE]` expects `data.malicious` (boolean). `[BE]` has no such field. Closest is `data.reputation.threat_score`. |
| Response `risk` | 🔴 | `[FE]` expects `data.risk` (string). `[BE]` has no such field. |
| Response `country` | 🔴 | `[FE]` expects `data.country`. `[BE]` has `data.reputation.country`. **Wrong nesting.** |
| Response `tags` | 🔴 | `[FE]` expects `data.tags` (string array). `[BE]` has no `tags` field. Closest are `reputation.malware_associations` or `reputation.threat_actor_associations`. |

---

### `POST /threat/correlate`

| Aspect | Status | Details |
|--------|--------|---------|
| Request body | ✅ | `{ iocs: string[] }` — matches |
| Response `groups` | ✅ | `{ groups: [{ name, type, iocs }], total }` — all match |

---

### `GET /threat/feed`

| Aspect | Status | Details |
|--------|--------|---------|
| Response shape | 🔴 | `[FE]` treats response as a **bare array** (`feed?.map(...)`). `[BE]` `ThreatFeedResponse` returns a **single object**: `{ latest_cves: [], latest_malware: [], latest_ransomware: [], latest_threat_actors: [] }`. `.map` on an object is **undefined** — nothing renders. |
| Response property `indicator` | 🔴 | Assumes array items have `indicator`. Backend object has no such field. |
| Response property `type` | 🔴 | No such field at top level. |
| Response property `risk` | 🔴 | No such field. |
| Response property `source` | 🔴 | No such field. |
| Response property `updated` | 🔴 | No such field. |

---

## 8. Plugins

---

### `GET /plugins/`

| Aspect | Status | Details |
|--------|--------|---------|
| All | ✅ | Fully matches |

---

### `POST /plugins/{id}/enable`

| Aspect | Status | Details |
|--------|--------|---------|
| Response | 🔵 | Response data never read — only toast on success |

---

### `POST /plugins/{id}/disable`

| Aspect | Status | Details |
|--------|--------|---------|
| Response | 🔵 | Response data never read |

---

### `POST /plugins/reload`

| Aspect | Status | Details |
|--------|--------|---------|
| All | ✅ | Fully matches (response not read) |

---

## 9. Orphaned API Functions

These functions are defined in the API layer but **never imported or used** anywhere in the frontend:

| API File | Orphaned Functions |
|----------|-------------------|
| `api/auth.ts` | `loginMfa`, `register`, `getOAuthUrl`, `oauthCallback`, `verifyMfa` |
| `api/dashboard.ts` | `getAlerts`, `getLogStats`, `getThreatStats`, `getInvestigationStats` |
| `api/detection.ts` | `getRule`, `updateRule` |
| `api/logs.ts` | `getGlobalStats` |
| `api/cases.ts` | `updateCase`, `archiveCase`, `generateReport` |
| `api/ai.ts` | `getActiveProvider`, `switchProvider` |

> These represent **dead code** and a coverage gap — the frontend cannot access these backend endpoints at all.

---

## 10. Cross-Cutting Issues

| # | Issue | Affected Endpoints | Severity |
|---|-------|-------------------|----------|
| 1 | **Wrong nesting** — frontend accesses flat properties, backend nests under sub-object | `GET /threat/lookup` (`reputation.*`) | 🔴 |
| 2 | **Wrong property names** — frontend uses one name, backend uses another | `assignee` ↔ `assigned_analyst`, `internal` ↔ `is_internal`, `log_source` ↔ `logsource_*`, `type` ↔ `evidence_type`, `user` ↔ `username`, `analysis` ↔ `summary`, `response` ↔ `reply` | 🔴/🟠 |
| 3 | **Complete structure mismatch** — frontend expects array, backend returns object | `GET /threat/feed`, `POST /ai/recommendations` | 🔴 |
| 4 | **Missing request fields** — frontend omits fields the backend needs | `POST /cases` (no `case_type`, no `assigned_analyst`), `POST /ai/investigate` (no `log_id`) | 🟠 |
| 5 | **Extra request fields** — frontend sends fields backend ignores | `POST /cases` (`attack_stage`, `tags`, `assignee`), `POST /cases/{id}/evidence` (`content`) | 🟡 |
| 6 | **Wrong type assumption** — frontend expects string, backend returns float | `GET /detection/analytics` (`false_positive_rate`) | 🟠 |
| 7 | **IOC hashes type** — frontend treats as strings, backend returns objects | `POST /threat/extract` | 🟠 |
| 8 | **Hardcoded broken parameter** — frontend always passes `0` | `POST /ai/recommendations` (always gets empty results) | 🔴 |
| 9 | **Response data never read** — mutations only invalidate cache | 13+ mutation endpoints | 🔵 |
| 10 | **Contract errors** — contract example differs from backend schema | `POST /auth/mfa/setup` (`uri` vs `qr_code`), `POST /auth/register` (missing `token_type`) | 🟡 |

---

## 11. Mismatch Heatmap by Endpoint

| Endpoint | Method | Status | Issues |
|----------|--------|--------|--------|
| `/auth/register` | POST | 🟡 | Missing `email` in FE; contract missing `token_type` |
| `/auth/mfa/setup` | POST | 🟡 | Contract says `uri`, backend says `qr_code` |
| `/detection/sigma` | GET | 🔴 | `log_source` doesn't exist in response |
| `/detection/analytics` | GET | 🟠 | `false_positive_rate` type mismatch (string vs float) |
| `/cases` | POST | 🔴 | 3 wrong field names + 2 missing fields |
| `/cases/{id}` | GET | 🔴 | 4 wrong/missing response properties |
| `/cases/{id}/evidence` | POST | 🟠 | `content` field silently dropped |
| `/cases/{id}/comments` | POST | 🟡 | `internal` vs `is_internal` |
| `/ai/chat` | POST | 🟠 | `response`/`message` fallback undefined; only `reply` works |
| `/ai/investigate` | POST | 🔴 | Never sends `log_id`; wrong response property names |
| `/ai/recommendations` | POST | 🔴 | Hardcoded `logId=0`; array vs object mismatch |
| `/threat/lookup` | GET | 🔴 | Complete nesting + property name mismatch |
| `/threat/extract` | POST | 🟠 | `hashes` type mismatch (objects vs strings) |
| `/threat/feed` | GET | 🔴 | Array vs object structure mismatch |
