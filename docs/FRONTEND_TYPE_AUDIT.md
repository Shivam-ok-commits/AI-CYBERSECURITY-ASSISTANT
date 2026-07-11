# Frontend Type Audit

**Date:** 2026-07-11
**Scope:** All `.ts`/`.tsx` files under `frontend/src/` vs `frontend/src/types/api.ts`
**Method:** Manual code review against type definitions and live-probed backend responses

---

## P0 — Orphaned Type Definition File

`frontend/src/types/api.ts` (1180 lines, 90+ exported types) is **never imported** by any file in the project. The entire file is dead code.

All consumers define their own local types, duplicating subsets of these definitions in 5 locations:

| File | Duplicated Type | api.ts Equivalent |
|------|----------------|-------------------|
| `api/auth.ts:3-6` | `LoginRequest` | Line 40 — `LoginRequest` |
| `api/auth.ts:8-11` | `AuthResponse` | Line 100 — `AuthResponse` |
| `api/ai.ts:23-27` | `AIProviderInfo` | Line 318 — `AIProviderInfo` |
| `context/AuthContext.tsx:4-10` | `User` | Line 56 — `UserResponse` |
| `pages/Plugins.tsx:13-23` | `PluginInfo` | Line 1088 — `PluginInfo` |
| `api/cases.ts:3-11` | `CaseData` (divergent) | Line 405 — `CaseCreate` |

None of these local types are themselves imported by other files, so each API file is the sole consumer of its own type definitions.

---

## P0 — 43 API Functions Return `any`

Every API function that omits a response generic parameter returns `any`, flowing unchecked into all consumers:

| File | Lines | Functions | Count |
|------|-------|-----------|-------|
| `api/ai.ts` | 3–19 | `createSession`, `listSessions`, `chat`, `investigate`, `getRecommendations`, `explainLog` | 6 |
| `api/cases.ts` | 13–35 | `listCases`, `getCase`, `createCase`, `updateCase`, `archiveCase`, `addEvidence`, `addComment`, `generateReport` | 8 |
| `api/dashboard.ts` | 3–16 | `getFullDashboard`, `getAlerts`, `getLogStats`, `getThreatStats`, `getInvestigationStats` | 5 |
| `api/detection.ts` | 3–46 | `listRules`, `createRule`, `getRule`, `updateRule`, `testRule`, `listSigmaRules`, `createSigmaRule`, `listYaraRules`, `createYaraRule`, `listHunts`, `createHunt`, `executeHunt`, `getHuntResults`, `getAnalytics` (14) | 14 |
| `api/logs.ts` | 3–16 | `uploadLog`, `getAnalyses`, `getAnalysis`, `getTimeline`, `getGlobalStats` | 5 |
| `api/threatIntel.ts` | 3–13 | `extractIocs`, `enrichIoc`, `correlateIocs`, `getThreatFeed` | 4 |
| `api/auth.ts` | 19–20 | `register` | 1 |
| **Total** | | | **43** |

Only `api/auth.ts` (login, getProfile, oauth, mfa, etc.) correctly types its response generics.

---

## P1 — Wrong Field Names (Runtime Data Access)

### IOC Enrichment — `pages/ThreatIntel/ThreatIntel.tsx:63-79`

Accesses these fields on the `enrichIoc` response, but **none exist at the top level** of the actual backend response `{indicator, indicator_type, reputation: {...}}`:

| Accessed Field | Backend Location | Issue |
|---|---|---|
| `.source` (line 65) | `reputation.sources` (array) | Wrong path + wrong type |
| `.malicious` (line 67) | Does not exist | **Will be `undefined`** |
| `.risk` (line 68) | `reputation.threat_score` | Wrong name + wrong path |
| `.country` (line 71) | `reputation.country` | Wrong path |
| `.tags` (line 72) | Does not exist | **Will be `undefined`** |

### Case Detail — `pages/Cases/Cases.tsx:111-171`

Accesses these fields on the `getCase` response, but the backend `CaseResponse` has none of them:

| Accessed Field | Backend Actual Field | Issue |
|---|---|---|
| `.attack_stage` (line 121) | `case_type` | Wrong name |
| `.assignee` (line 122) | `assigned_analyst` | Wrong name |
| `.evidence` (line 123, 127-131) | Separate endpoint `/cases/{id}/evidence` | **Not in response** |
| `.comments` (line 161) | Separate endpoint `/cases/{id}/comments` | **Not in response** |

The evidence sub-object also accesses `.type` (line 135) which should be `evidence_type`.

### Threat Feed — `pages/ThreatIntel/ThreatIntel.tsx:111-116`

Treats the feed response as `Array<{indicator, type, risk, source, updated}>`, but the backend returns `{latest_cves, latest_malware, latest_ransomware, latest_threat_actors}`.

```typescript
feed?.map((f: { indicator: string; type: string; risk: string; ... }) => ...)
```

`feed` is a `dict → object`, not an array. **Calling `.map()` on an object will throw a runtime TypeError.**

### Dashboard — `pages/Dashboard.tsx:24-33`

Uses brute-force casts to access nested properties:

```typescript
const exec = (dashboard as Record<string, unknown>)?.executive as Record<string, unknown> | undefined;
const logStats = (dashboard as Record<string, unknown>)?.log_stats as Record<string, unknown> | undefined;
```

If the backend shape ever changes, these silently return `undefined`. No type checking.

### Sigma Rule — `pages/Detection/Detection.tsx:222`

Accesses `.log_source` on sigma rules, but the backend `SigmaRuleResponse` uses three separate fields: `logsource_category`, `logsource_product`, `logsource_service`.

### YARA Rule Creation — `pages/Detection/Detection.tsx:69`

Sends `rule_text` as the field name, but the backend `YARARuleCreate` schema expects `content`.

---

## P1 — `as unknown as Record<string, unknown>` Bypasses Type Checking

Four mutations in `pages/Detection/Detection.tsx` throw away all type safety:

| Line | Expression | Behaves as |
|------|-----------|------------|
| 34 | `newRule as unknown as Record<string, unknown>` | Accepts any shape |
| 51 | `newHunt as unknown as Record<string, unknown>` | Accepts any shape |
| 63 | `newSigma as unknown as Record<string, unknown>` | Accepts any shape |
| 69 | `newYara as unknown as Record<string, unknown>` | Accepts any shape |

These suppress TS errors but pass potentially wrong data to the backend. The `newYara` shape has `rule_text` while backend expects `content`; `newSigma` has `log_source` while backend expects `logsource_category`/`logsource_product`/`logsource_service`.

---

## P2 — Nullability Mismatches

| Location | Declared As | Actual Backend | Risk |
|----------|------------|----------------|------|
| `api/auth.ts:23` — `getProfile` return | `mfa_enabled: boolean` (required) | Can be `null` | `null` assigned to `boolean` at runtime |
| `pages/Cases/Cases.tsx:118` — `detail.description` | Assumed present | `CaseResponse.description` is `Optional[str]` | May be `undefined` |
| `api/threatIntel.ts:3` — `extractIocs` param | `text: string` | Backend expects `text: str` | Correct for sending |

---

## P2 — Incorrect Array Assumptions

| File | Code | Problem |
|------|------|---------|
| `pages/ThreatIntel/ThreatIntel.tsx:111` | `feed?.map(...)` | `feed` is a dict, not array — **runtime crash** |
| `pages/Detection/Detection.tsx:301` | `huntResults?.map(...)` | Untyped — assumed array, backend returns `array` ✅ but no type guard |
| `pages/AI/AIAssistant.tsx:71` | `sessions?.map(...)` | Untyped — assumed array ✅ but no type guard |

---

## P2 — Unused Enum/String Literal Types

`api.ts` defines 6 string union types and 4 const arrays that are never imported or referenced:

| Type | api.ts Line | Used Anywhere? |
|------|-------------|----------------|
| `Severity` | 34 | No |
| `Status` | 35 | No |
| `Role` | 36 | No |
| `SeverityLevel` | 1163 | No |
| `CaseStatus` | 1166 | No |
| `IOCType` | 1169 | No |
| `AlertStatus` | 1172 | No |
| `SourceType` | 1178 | No |

Pages use plain strings (`"medium"`, `"open"`, etc.) without type enforcement.

---

## P3 — AI Chat Response Fallback Pattern

`pages/AI/AIAssistant.tsx:26`:

```typescript
data.response || data.reply || data.message
```

The `ChatResponse` type in `api.ts:345` uses `reply` as the field name. The fallback chain reveals uncertainty about which field the backend returns. Live probe confirms the backend `POST /ai/chat` response shape was never verified.

**`posts/sessions`** also uses a fallback — line 19: `data.id` — assumes the create session response has an `id` field. The backend `ChatSessionResponse` does have `id`, but this is never type-checked.

---

## P3 — Missing Generic Constraints

Several request-type parameters use `Record<string, string>` or `Record<string, unknown>` when specific interfaces exist in `api.ts`:

| File | Param Type | api.ts Interface |
|------|-----------|------------------|
| `api/cases.ts:13` | `params?: Record<string, string>` | `PaginationParams` (line 8) |
| `api/detection.ts:6` | `data: Record<string, unknown>` | `DetectionRuleCreate` (line 754) |
| `api/detection.ts:24` | `data: Record<string, unknown>` | `SigmaRuleCreate` (line 801) |
| `api/detection.ts:30` | `data: Record<string, unknown>` | `YARARuleCreate` (line 840) |
| `api/detection.ts:36` | `data: Record<string, unknown>` | `SavedHuntCreate` (line 868) |
| `api/cases.ts:28` | `{ description, source, content, evidence_type? }` | `EvidenceCreate` (line 483) |

---

## P3 — Cascade Effects from Untyped API Layer

Since 43/50 API functions return `any`, all consumer components access data without any compilation safety. A single backend field rename silently breaks:

- 5 dashboard cards in `Dashboard.tsx`
- All 4 threat-intel panels in `ThreatIntel.tsx`
- Case detail rendering in `Cases.tsx`
- Chat, investigate, explain panels in `AIAssistant.tsx`
- All detection tabs in `Detection.tsx`
- Log analysis detail in `LogAnalysis.tsx`

---

## Summary

| Category | Count | Severity |
|----------|-------|----------|
| Orphaned type file (1180 lines, 90+ types, 0 imports) | 1 | P0 |
| API functions returning `any` | 43 | P0 |
| Wrong field names (runtime `undefined` / crashes) | 14 | P1 |
| `as unknown` bypass | 4 | P1 |
| Nullability mismatches | 2 | P2 |
| Array vs object assumption | 1 | P2 |
| Unused enum/union types | 8 | P2 |
| Response shape uncertainty (fallback chains) | 2 | P3 |
| Missing specific request generics (`Record<string, X>`) | 6 | P3 |

**Root cause:** `api.ts` was generated as a standalone OpenAPI reference but never wired into the service layer. Each `api/*.ts` file defines its own inline response types (or omits them entirely), and those inline types are never enforced against consumer usage.
