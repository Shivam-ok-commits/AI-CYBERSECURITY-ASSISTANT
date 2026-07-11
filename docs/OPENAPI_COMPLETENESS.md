# OpenAPI Schema — Completeness Report

> Generated: 2026-07-11
>
> Files: `openapi.json` (177 KB) and `openapi.yaml` in project root

---

## Overview

| Metric | Value |
|--------|-------|
| OpenAPI version | 3.1.0 |
| Total paths | 151 |
| Total operations | 187 |
| Component schemas | 105 |
| Tags (router-level) | 10 |

---

## Completeness by Required Field

| Field | Status | Coverage |
|-------|--------|----------|
| `operationId` | ✅ Auto-generated | 187/187 |
| `summary` | ⚠️ Auto-generated from function name | 187/187 (auto, not human-written) |
| `description` | ❌ **Missing on all endpoints** | 0/187 |
| `tags` | ⚠️ Router-level only | 187/187 (grouped, not per-endpoint) |
| `parameters` | ✅ Auto-inferred | 187/187 |
| `requestBody` | ⚠️ Missing on 6 endpoints | 181/187 |
| `response_model` | ⚠️ **Missing on 50 endpoints** | 124/187 with typed schema, 63 with empty `{}` |
| `status codes` | ✅ Present | 187/187 |
| `security` | ⚠️ **Not defined globally or per-endpoint** | 0/187 |

---

## Endpoints That Cannot Be Represented Correctly

### 1. POST endpoints with raw `str` query parameters (not request body)

These endpoints accept a bare string (`content: str` or `text: str`) as a function parameter. FastAPI treats these as **query parameters** in the OpenAPI schema, but the frontend may send them as a **raw body string**. The OpenAPI representation is incomplete.

| Endpoint | Parameter | Issue |
|----------|-----------|-------|
| `POST /detection/sigma/validate` | `content` (query) | Raw string input has no request body schema |
| `POST /detection/yara/validate` | `content` (query) | Same |
| `POST /detection/ai/generate-sigma` | `text` (query) | Same |
| `POST /detection/ai/generate-yara` | `text` (query) | Same |
| `POST /detection/ai/explain` | `content` (query) | Same |
| `POST /detection/ai/improve` | `content`, `suggestion` (query) | Same |

**Why it's wrong**: These are `POST` endpoints meant to receive data, but the OpenAPI schema shows no `requestBody` — only query parameters. A generated client would send `?content=...` instead of a JSON body `"...\""`.

---

### 2. POST endpoints with bare JSON array request bodies

These endpoints accept an untyped bare array (`list[str]` or `list[dict]`) as the body. The OpenAPI schema shows them as `type: array` with no wrapping object, which is valid OpenAPI but non-standard.

| Endpoint | Body type | Issue |
|----------|-----------|-------|
| `POST /detection/rules/{rule_id}/test` | `string[]` | Bare array, no named field |
| `POST /detection/sigma/{rule_id}/execute` | `object[]` | Bare array of objects, no named field |
| `POST /detection/yara/{rule_id}/scan` | `string[]` | Bare array, no named field |

**Why it's non-standard**: Most tools expect `{ "sample_data": [...] }` rather than `[...]` directly.

---

### 3. DELETE endpoints with 204 No Content (correct, but no schema)

These 12 endpoints return `204 No Content` with no response body. The OpenAPI correctly shows no `content`, which is proper for 204. However, the `response_model` is unset, so there's no type-level confirmation of the empty body.

| Endpoint |
|----------|
| `DELETE /cases/{case_id}` |
| `DELETE /cases/{case_id}/evidence/{evidence_id}` |
| `DELETE /dashboard/assets/{asset_id}` |
| `DELETE /detection/rules/{rule_id}` |
| `DELETE /detection/sigma/{rule_id}` |
| `DELETE /detection/yara/{rule_id}` |
| `DELETE /detection/hunts/{hunt_id}` |
| `DELETE /detection/jobs/{job_id}` |
| `DELETE /detection/automation/{rule_id}` |
| `DELETE /detection/playbooks/{playbook_id}` |
| `DELETE /enterprise/notifications/{notif_id}` |
| `DELETE /enterprise/integrations/{int_id}` |

---

### 4. Endpoints with empty response schemas (no `response_model`)

63 response schemas are `{}` (empty object) because the endpoint lacks `response_model` and either returns a bare dict or no type annotation. Generated clients cannot know the response shape.

**Breakdown by router:**

| Router | Empty response schemas | Examples |
|--------|-----------------------|----------|
| `dashboard.py` | 32 | Chart endpoints, stat endpoints, action endpoints |
| `detection.py` | 16 | Action POSTs, export, raw response endpoints |
| `enterprise.py` | 14 | Plans, metrics, org actions, integration actions |
| `plugins.py` | 7 | All plugin endpoints |
| `auth.py` | 3 | MFA verify/enable/disable |
| `case_management.py` | 3 | DELETE, render template, export report |
| `logs.py` | 3 | List logs, log detail, events.json, timeline, attack-chain |
| `ai.py` | 3 | Switch provider, get history, RAG search, RAG index |
| `threat_intel.py` | 1 | Correlate IOCs POST |

---

### 5. Endpoint that returns raw file download (not JSON)

| Endpoint | Response type | Issue |
|----------|---------------|-------|
| `GET /cases/{case_id}/reports/{report_id}/export` | Dynamic (`Response` object) | The response content type is dynamic (markdown, PDF, etc.) and cannot be statically represented in OpenAPI |

---

### 6. Missing security/authentication definition

The OpenAPI schema has **no `security` definitions** at either the global or per-endpoint level. All authenticated endpoints require `Authorization: Bearer <token>`, but this is not documented in the schema. Generated clients will not know to send auth headers.

---

## Summary of Defects

| Defect | Count | Severity |
|--------|-------|----------|
| Missing `description` on all endpoints | 187/187 | High |
| Missing `response_model` / empty response schema | 63 | High |
| No security scheme defined | 187/187 | High |
| Raw string as query param instead of body | 6 | Medium |
| Bare array request body (non-standard) | 3 | Low |
| Dynamic response type (not representable) | 1 | Low |
| `summary` auto-generated, not human-written | 187/187 | Low |
