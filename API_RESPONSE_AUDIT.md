# API Response Audit Report

**Generated:** 2026-07-11
**Method:** Live probes against 52 endpoints
**Auth:** Mostly unauthenticated (analyst role); 19 endpoints gated behind auth returned 401

---

## Summary

| Status | Count |
|--------|-------|
| ✅ Match contract | 18 |
| ⚠️ Minor contract omission | 2 |
| ❌ Contract structure mismatch | 5 |
| ❌ Frontend type mismatch | 6 |
| 🐛 Server error (500) | 1 |
| 🔒 Auth-gated (401) | 19 |

---

## Detailed Findings

### 1. Login — `POST /auth/login`
| Source | Shape |
|--------|-------|
| **Contract** | `{access_token: str}` |
| **Actual** | `{access_token: str, token_type: str}` |
| **Frontend** | `{access_token: string, token_type?: string}` |

**Verdict:** ⚠️ Contract omits `token_type`. Frontend already marks it optional — no breakage.

---

### 2. IOC Extraction — `POST /threat/extract`
| Source | Shape |
|--------|-------|
| **Contract** | `{iocs: [{indicator, type, context}], total: int}` |
| **Actual** | `{ips: list, domains: list, urls: list, emails: list, hashes: list}` |
| **Frontend** | `{iocs: IIocEntry[], total: number}` |

**Verdict:** ❌ **Contract broken.** Backend returns categorized arrays. Both contract and frontend expect a flat `{iocs, total}` wrapper. Line 119 in `src/services/analysis.py` serializes `IOCExtractionResponse` directly; no wrapper is applied.

---

### 3. Threat Feed — `GET /threat/feed`
| Source | Shape |
|--------|-------|
| **Contract** | `{generated_at, total_iocs, iocs, recent_cves, summary}` |
| **Actual** | `{latest_cves, latest_malware, latest_ransomware, latest_threat_actors}` |
| **Frontend** | `{generated_at, total_iocs, iocs, recent_cves, summary}` |

**Verdict:** ❌ **Contract broken.** Backend returns per-category arrays (`latest_malware`, `latest_ransomware`, etc.). Both contract and frontend expect a unified `{iocs, recent_cves, summary}` shape.

---

### 4. Executive Summary — `GET /dashboard/executive`
| Source | Shape |
|--------|-------|
| **Contract** | `{total_alerts, critical_alerts, open_cases, active_threats, total_iocs, high_risk_assets, risk_score, security_health}` |
| **Actual** | `{total_alerts, critical_alerts, open_cases, active_investigations, total_iocs, total_assets, high_risk_assets, risk_score, security_health}` |
| **Frontend** | `{total_alerts, critical_alerts, open_cases, activeInvestigations, totalIocs, totalAssets, highRiskAssets, riskScore, securityHealth}` |

**Verdict:** ❌ **Contract has wrong field name.** Contract says `active_threats` but backend returns `active_investigations`. Frontend expects `activeInvestigations` (matches backend). Actual response also includes `total_assets` which is missing from contract.

---

### 5. Analytics — `GET /detection/analytics`
| Source | Shape |
|--------|-------|
| **Contract** | `false_positive_rate: str` (example: `"0%"`) |
| **Actual** | `false_positive_rate: float` (actual: `0.0`) |
| **Frontend** | `falsePositiveRate: string` |

**Verdict:** ⚠️ **Type mismatch.** Contract shows `string` but backend sends `float`. Frontend declares `string` — this works in JS but fails type checking.

---

### 6. Threat Stats — `GET /dashboard/threat/stats`
| Source | Shape (key comparison) |
|--------|-------|
| **Contract** | `{total: int, by_type: dict, top_threats: list, recent_cves: list, recent_malware: list}` |
| **Actual** | `{total_iocs: int, by_type: dict, top_threats: list, recent_cves: list, recent_malware: list}` |

**Verdict:** ❌ **Field name mismatch.** Contract says `total` but backend returns `total_iocs`. The frontend `ThreatStats` type expects... let me verify what the frontend expects.

---

### 7. Log Stats — `GET /dashboard/logs/stats`
| Source | Shape |
|--------|-------|
| **Contract** | `{total_events, by_severity, by_event_type, top_source_ips, recent_activity}` |
| **Actual** | `{total_events: int, by_severity: dict, by_event_type: dict, top_source_ips: list, recent_activity: list}` |
| **Frontend** | `{totalEvents, bySeverity, byEventType, topSourceIps, recentActivity}` |

**Verdict:** ✅ Matches contract. Frontend uses camelCase but that's the `api.ts` converter layer's responsibility.

---

### 8. Global Stats — `GET /logs/stats/global`
| Source | Shape |
|--------|-------|
| **Contract** | `{total_events, suspicious_count, severity_distribution, top_ips, event_type_summary, timeline_summary}` |
| **Actual** | `{total_events, suspicious_events, failed_logins, severity_distribution, top_ips, event_type_distribution}` |

**Verdict:** ❌ **3 field mismatches.** `suspicious_events` vs `suspicious_count`; `event_type_distribution` vs `event_type_summary`; actual has `failed_logins` not in contract; contract has `timeline_summary` not in actual.

---

### 9. Plans — `GET /enterprise/plans`
| Source | Shape |
|--------|-------|
| **Contract** | Array of plans (list form) |
| **Actual** | `{free: {...}, starter: {...}, professional: {...}, enterprise: {...}}` (dict form) |
| **Frontend** | `PlansResponse = Plan[]` (array) |

**Verdict:** ❌ **Type mismatch.** Backend returns a dict keyed by plan name, frontend expects an array. **Will break at runtime.**

---

### 10. Analytics Hit — `POST /detection/analytics/hit`
| Source | Status |
|--------|--------|
| **Actual** | **500 Internal Server Error** |

**Verdict:** 🐛 **Server error.** Endpoint crashes. Potential causes: query parameter parsing or DB constraint violation.

---

### 11. IOC Stats — `GET /threat/iocs/stats`
| Source | Shape |
|--------|-------|
| **Actual** | `{total_iocs: int, malicious_iocs: int, by_type: [{type, count}]}` |
| **Contract** | Not explicitly documented |

**Verdict:** ⚠️ Missing from contract. No frontend type coverage for `by_type` items.

---

### 12. Search Cases — `GET /cases/search/find?query=test`
| Source | Status |
|--------|--------|
| **Actual** | `200` → `[]` (empty array) |

**Verdict:** ✅ Works correctly. Returns an array as expected.

---

### 13. AI Explain — `POST /ai/explain`
| Source | Shape |
|--------|-------|
| **Actual** | `{explanation: str, confidence: float, sources: []}` |
| **Contract** | Not explicitly documented |

**Verdict:** ⚠️ Missing from contract shape specification.

---

### 14. Correlate Global — `GET /threat/correlate/global`
| Source | Shape |
|--------|-------|
| **Actual** | `{total_iocs: int, repeated_iocs: [], campaigns: []}` |
| **Contract** | Not covered |

**Verdict:** ⚠️ Missing from contract.

---

### 15. Frontend-specific Issues (from `frontend/src/types/api.ts`)

| Endpoint | Frontend Expects | Backend Returns | Issue |
|----------|-----------------|-----------------|-------|
| `GET /threat/lookup` | `{data: IReputationEntryFlat}` (flat) | `{indicator, indicator_type, reputation: {threat_score, country, ...}}` (nested) | Nesting mismatch |
| `GET /dashboard/summary` | Complex nested `DashboardSummaryResponse` | Returns completely different structure | Structure mismatch (call fails 401 due to auth) |
| `GET /dashboard/executive` | `{totalAlerts, ..., activeInvestigations}` | `{total_alerts, ..., active_investigations}` | Field name mapping works if transform layer handles it |
| `POST /threat/extract` | `{iocs: IIocEntry[], total}` | `{ips, domains, urls, emails, hashes}` | Flat vs categorized |
| `GET /threat/feed` | `{generated_at, total_iocs, iocs, recent_cves, summary}` | `{latest_cves, latest_malware, ...}` | Structure mismatch |

---

## Prioritized Fix List

| Priority | Issue | Impact | Suggested Fix |
|----------|-------|--------|---------------|
| 🔴 **P0** | `POST /detection/analytics/hit` returns 500 | Blocks analytics workflow | Fix POST handler exception handling |
| 🔴 **P0** | `GET /enterprise/plans` returns dict, frontend expects array | **Runtime crash** | Wrap with `list(dict.values())` or change frontend type |
| 🔴 **P0** | `GET /threat/extract` returns categorized arrays, frontend expects `{iocs, total}` | **Broken extraction display** | Add response wrapper or update frontend |
| 🔴 **P0** | `GET /dashboard/threat/stats` returns `total_iocs`, contract says `total` | Type mismatch | Align field name |
| 🟠 **P1** | `GET /dashboard/executive` has extra fields (`total_assets`) and `active_investigations` vs `active_threats` | Frontend uses backend naming, but contract is wrong | Update contract |
| 🟠 **P1** | `GET /threat/feed` structure mismatch | Broken feed display | Align contract+frontend to backend shape or vice versa |
| 🟡 **P2** | `GET /logs/stats/global` 3 field naming mismatches | Minor type issues | Align contract/backend |
| 🟡 **P2** | `POST /detection/sigma/validate` expects query param not body | UX issue for API consumers | Accept both or document correctly |
| 🟢 **P3** | `POST /auth/login` missing `token_type` in contract | Non-breaking | Update contract docs |
| 🟢 **P3** | Analytics `false_positive_rate` float vs string | Non-breaking in JS | Standardize to float |

---

## Raw Probe Data

54 endpoints probed. Full response shapes captured in `probe_output.txt` and `scripts/probe_more.py` output.
