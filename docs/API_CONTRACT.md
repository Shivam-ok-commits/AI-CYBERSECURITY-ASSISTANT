# API Contract — AI Cybersecurity Assistant

> Base URL: `/api/v1`
>
> Date: 2026-07-11
>
> This document defines the **expected** contract for every endpoint. Endpoints that deviate from the contract are flagged with ⚠ **CONTRACT VIOLATION**.

---

## Response Envelope

All responses follow one of two patterns:

| Type | Format |
|------|--------|
| **Success (single object)** | `{ ...fields }` |
| **Success (list)** | `[ { ... }, ... ]` |
| **Error** | `{ "detail": "<message>" }` |

> ⚠ **CONTRACT VIOLATION**: There is **no unified response wrapper**. Bare lists and bare objects are returned directly. No `data`, `total`, `page` envelope exists. This violates API consistency best practices.

---

## Error Response Format

```json
{
  "detail": "Human-readable error message"
}
```

| Status Code | Meaning |
|-------------|---------|
| 400 | Bad request (validation, missing field) |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (insufficient role, MFA required) |
| 404 | Resource not found |
| 409 | Conflict (duplicate field, e.g. username) |
| 422 | Validation error (Pydantic schema) |
| 429 | Rate limit exceeded |
| 500 | Internal server error |
| 501 | Not implemented |

> ⚠ **CONTRACT VIOLATION**: Some endpoints (e.g., `POST /detection/rules/{rule_id}/test`) return Pydantic `ValidationError` directly (422), while others raise `HTTPException` with `status_code`. The error response `detail` key comes from FastAPI's default — the format is correct but unstructured.

---

## Authentication

Most endpoints require a JWT Bearer token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Endpoints labeled **Auth: None** do not require authentication. All others require a valid token obtained from `/auth/login` or `/auth/register`.

> ⚠ **CONTRACT VIOLATION**: Several endpoints in `/detection`, `/enterprise`, and `/dashboard` inconsistently omit auth requirements (see per-endpoint notes).

---

## Endpoints

---

### 1. Health

---

#### `GET /health`

Method: `GET`
Route: `/api/v1/health`
Description: Returns service health status including database connectivity.
Authentication: None

**Request**: None

**Success Response** (200):
```json
{
  "status": "ok",
  "version": "0.1.0",
  "database": "ok"
}
```

| Field | Type | Description |
|-------|------|-------------|
| status | string | `"ok"` |
| version | string | Semver version |
| database | string | `"ok"` or `"error"` |

> ⚠ **CONTRACT VIOLATION**: `database` is a raw string (`"ok"`/`"error"`) instead of a structured object `{ "status": "ok", "type": "sqlite" }`.

**Error Responses**: None (returns 200 even on DB failure, just sets `database: "error"`).

---

### 2. Authentication

---

#### `POST /auth/register`

Method: `POST`
Route: `/api/v1/auth/register`
Description: Register a new user account.
Authentication: None

**Request — JSON Body**:
```json
{
  "username": "analyst1",
  "password": "securePass123!",
  "email": "analyst1@cybersec.local"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| username | string | Yes | Unique username |
| password | string | Yes | Plain-text password (hashed server-side) |
| email | string | No | Email (auto-generated if omitted) |

**Success Response** (201):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

| Field | Type | Description |
|-------|------|-------------|
| access_token | string | JWT Bearer token |

**Error Responses**: 409 Conflict (duplicate username/email).

---

#### `POST /auth/login`

Method: `POST`
Route: `/api/v1/auth/login`
Description: Authenticate with username/password and receive a JWT.
Authentication: None

**Request — JSON Body**:
```json
{
  "username": "analyst1",
  "password": "securePass123!"
}
```

**Success Response** (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Error Responses**: 401 (invalid credentials), 403 (MFA required).

---

#### `POST /auth/login/mfa`

Method: `POST`
Route: `/api/v1/auth/login/mfa`
Description: Authenticate with username/password and TOTP MFA code.
Authentication: None

**Request — JSON Body**:
```json
{
  "username": "analyst1",
  "password": "securePass123!",
  "mfa_code": "123456"
}
```

**Success Response** (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Error Responses**: 400 (MFA not enabled), 401 (invalid credentials/MFA code).

---

#### `GET /auth/me`

Method: `GET`
Route: `/api/v1/auth/me`
Description: Get the currently authenticated user's profile.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Success Response** (200):
```json
{
  "id": 1,
  "username": "analyst1",
  "email": "analyst1@cybersec.local",
  "role": "analyst",
  "mfa_enabled": false
}
```

**Error Responses**: 401 (invalid/expired token).

---

#### `GET /auth/admin-only`

Method: `GET`
Route: `/api/v1/auth/admin-only`
Description: Admin-only endpoint for testing role-based access.
Authentication: Required (role: admin)

**Request — Headers**: `Authorization: Bearer <token>`

**Success Response** (200):
```json
{
  "message": "Welcome admin",
  "user": "admin"
}
```

**Error Responses**: 403 (user is not admin).

---

#### `GET /auth/oauth/{provider}/url`

Method: `GET`
Route: `/api/v1/auth/oauth/{provider}/url`
Description: Get the OAuth 2.0 authorization URL for a provider.
Authentication: None

**Path Parameters**: `provider` (string) — e.g. `github`, `google`

**Query Parameters**: `redirect_uri` (string, optional)

**Success Response** (200):
```json
{
  "authorization_url": "https://github.com/login/oauth/authorize?..."
}
```

**Error Responses**: 501 (provider OAuth not configured).

---

#### `POST /auth/oauth/{provider}/callback`

Method: `POST`
Route: `/api/v1/auth/oauth/{provider}/callback`
Description: Handle OAuth 2.0 callback and exchange code for JWT.
Authentication: None

**Path Parameters**: `provider` (string)

**Request — JSON Body**:
```json
{
  "code": "abc123...",
  "redirect_uri": "http://localhost:5173/auth/github/callback"
}
```

**Success Response** (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Error Responses**: 501 (provider not configured).

---

#### `POST /auth/mfa/setup`

Method: `POST`
Route: `/api/v1/auth/mfa/setup`
Description: Generate TOTP secret and QR code URI for MFA setup.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Success Response** (200):
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "uri": "otpauth://totp/Cybersec%20Assistant:user?secret=..."
}
```

---

#### `POST /auth/mfa/verify`

Method: `POST`
Route: `/api/v1/auth/mfa/verify`
Description: Verify a TOTP code before enabling MFA.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Request — JSON Body**:
```json
{
  "code": "123456"
}
```

**Success Response** (200):
```json
{
  "verified": true
}
```

**Error Responses**: 400 (invalid code).

---

#### `POST /auth/mfa/enable`

Method: `POST`
Route: `/api/v1/auth/mfa/enable`
Description: Enable MFA after successful verification.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Request — JSON Body**:
```json
{
  "code": "123456"
}
```

**Success Response** (200):
```json
{
  "mfa_enabled": true
}
```

**Error Responses**: 400 (invalid code).

---

#### `POST /auth/mfa/disable`

Method: `POST`
Route: `/api/v1/auth/mfa/disable`
Description: Disable MFA for the current user.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Success Response** (200):
```json
{
  "mfa_enabled": false
}
```

---

#### `POST /auth/ldap/login`

Method: `POST`
Route: `/api/v1/auth/ldap/login`
Description: Authenticate via LDAP and receive a JWT.
Authentication: None

**Request — JSON Body**:
```json
{
  "server": "ldap.example.com",
  "base_dn": "dc=example,dc=com",
  "username": "analyst1",
  "password": "securePass123!",
  "user_filter": "(objectClass=person)",
  "bind_dn": "",
  "bind_password": "",
  "attribute_map": {}
}
```

**Success Response** (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Error Responses**: 401 (LDAP auth failed).

---

### 3. Logs

---

#### `POST /logs/upload`

Method: `POST`
Route: `/api/v1/logs/upload`
Description: Upload a log file for parsing and analysis.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`, `Content-Type: multipart/form-data`

**Request — Body**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | UploadFile | Yes | Log file (text-based, e.g. .log, .txt, .csv) |

**Success Response** (201):
```json
{
  "id": 1,
  "filename": "auth.log",
  "size_bytes": 102400,
  "source_type": "linux_auth",
  "status": "parsed",
  "event_count": 50
}
```

| Field | Type | Description |
|-------|------|-------------|
| id | int | Log record ID |
| filename | string | Original filename |
| size_bytes | int | File size in bytes |
| source_type | string | Detected log source type |
| status | string | `"parsed"` |
| event_count | int | Number of parsed events |

**Error Responses**: 400 (invalid file/validation error).

---

#### `GET /logs/`

Method: `GET`
Route: `/api/v1/logs/`
Description: List all uploaded logs for the current user with detection summary.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Query Parameters**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| limit | int | 50 | Max results (1–200) |
| offset | int | 0 | Pagination offset |

**Success Response** (200):
```json
[
  {
    "id": 1,
    "filename": "auth.log",
    "source_type": "linux_auth",
    "format": "linux_auth",
    "status": "parsed",
    "size_bytes": 102400,
    "event_count": 50,
    "total_events": 50,
    "suspicious_count": 3,
    "created_at": "2026-07-11T10:00:00"
  }
]
```

| Field | Type | Description |
|-------|------|-------------|
| id | int | Log record ID |
| filename | string | Original filename |
| source_type | string | Detected log source type |
| format | string | ⚠ **DUPLICATE** of `source_type` |
| status | string | `"parsed"` |
| size_bytes | int | File size |
| event_count | int | Number of events |
| total_events | int | ⚠ **DUPLICATE** of `event_count` |
| suspicious_count | int | Number of suspicious findings |
| created_at | string | ISO 8601 timestamp |

> ⚠ **CONTRACT VIOLATION**: `format` is an undocumented alias for `source_type` (same value). `total_events` is an undocumented alias for `event_count` (same value). Duplicate fields should be removed.

> ⚠ **CONTRACT VIOLATION**: Returns a bare list with no envelope (`total` count, `page`, etc.), making pagination tracking impossible client-side.

---

#### `GET /logs/{log_id}`

Method: `GET`
Route: `/api/v1/logs/{log_id}`
Description: Get detailed information about a specific log.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Path Parameters**: `log_id` (int)

**Success Response** (200):
```json
{
  "id": 1,
  "filename": "auth.log",
  "source_type": "linux_auth",
  "format": "linux_auth",
  "status": "parsed",
  "size_bytes": 102400,
  "event_count": 50,
  "total_events": 50,
  "filepath": "",
  "created_at": "2026-07-11T10:00:00",
  "suspicious_count": 3,
  "event_types": ["Authentication Failure", "User Login"]
}
```

> ⚠ **CONTRACT VIOLATION**: `format` duplicates `source_type`. `total_events` duplicates `event_count`.

**Error Responses**: 404 (log not found).

---

#### `GET /logs/{log_id}/events`

Method: `GET`
Route: `/api/v1/logs/{log_id}/events`
Description: Get raw parsed events from a log (typed model).
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Path Parameters**: `log_id` (int)

**Query Parameters**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| limit | int | 500 | Max rows (1–5000) |
| offset | int | 0 | Pagination offset |

**Success Response** (200):
```json
[
  {
    "id": 1,
    "log_id": 1,
    "line_number": 1,
    "timestamp": "2026-07-10T08:00:00",
    "source_ip": "192.168.1.100",
    "event_type": "authentication_failure",
    "severity": "high",
    "raw": "Failed password for root from 192.168.1.100 port 22 ssh2",
    "parsed_json": "{...}",
    "created_at": "2026-07-11T10:00:00"
  }
]
```

**Error Responses**: 404 (log not found).

---

#### `GET /logs/{log_id}/events.json`

Method: `GET`
Route: `/api/v1/logs/{log_id}/events.json`
Description: Get raw parsed events (raw dicts, no model serialization).
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Path Parameters**: `log_id` (int)

**Query Parameters**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| limit | int | 500 | Max rows (1–5000) |
| offset | int | 0 | Pagination offset |

**Success Response** (200):
```json
[
  { "id": 1, "log_id": 1, "line_number": 1, "timestamp": "...", ... }
]
```

> ⚠ **CONTRACT VIOLATION**: This endpoint is functionally identical to `GET /logs/{log_id}/events` but returns raw `dict` objects instead of `LogEntry` models. The response shape is undocumented and any schema changes in the DB propagate directly to the API. Either remove this endpoint or align it with the typed response.

**Error Responses**: 404 (log not found).

---

#### `GET /logs/{log_id}/extracted`

Method: `GET`
Route: `/api/v1/logs/{log_id}/extracted`
Description: Get extracted/normalized events from a log.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Path Parameters**: `log_id` (int)

**Success Response** (200):
```json
[
  {
    "timestamp": "2026-07-10T08:00:00",
    "source_ip": "192.168.1.100",
    "event_name": "Authentication Failure",
    "event_category": "authentication",
    "severity": "high",
    "raw": "Failed password for root..."
  }
]
```

**Error Responses**: 404 (log not found).

---

#### `GET /logs/{log_id}/suspicious`

Method: `GET`
Route: `/api/v1/logs/{log_id}/suspicious`
Description: Get suspicious findings and brute-force detections for a log.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Path Parameters**: `log_id` (int)

**Query Parameters**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| bf-threshold | int | 5 | Brute-force threshold (failed attempts) |
| bf-window | int | 5 | Brute-force time window (minutes) |

**Success Response** (200):
```json
[
  {
    "type": "brute_force",
    "severity": "critical",
    "source_ip": "192.168.1.100",
    "event_count": 10,
    "time_range": { "start": "...", "end": "..." },
    "description": "Possible brute-force attack from 192.168.1.100"
  }
]
```

**Error Responses**: 404 (log not found).

---

#### `GET /logs/{log_id}/timeline`

Method: `GET`
Route: `/api/v1/logs/{log_id}/timeline`
Description: Get a chronological timeline of events grouped by time.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Path Parameters**: `log_id` (int)

**Success Response** (200):
```json
[
  {
    "timestamp": "2026-07-10T08:00:00",
    "event_type": "Authentication Failure",
    "source_ip": "192.168.1.100",
    "severity": "high",
    "details": "Failed password for root from 192.168.1.100 port 22 ssh2"
  }
]
```

**Error Responses**: 404 (log not found).

---

#### `GET /logs/{log_id}/attack-chain`

Method: `GET`
Route: `/api/v1/logs/{log_id}/attack-chain`
Description: Get an attack chain derived from the log events.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Path Parameters**: `log_id` (int)

**Success Response** (200):
```json
{
  "attack_chain": [
    { "phase": "reconnaissance", "events": [...], "summary": "..." }
  ]
}
```

**Error Responses**: 404 (log not found).

---

#### `GET /logs/{log_id}/statistics`

Method: `GET`
Route: `/api/v1/logs/{log_id}/statistics`
Description: Get computed statistics for a specific log.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Path Parameters**: `log_id` (int)

**Query Parameters**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| bf-threshold | int | 5 | Brute-force threshold |
| bf-window | int | 5 | Brute-force time window (minutes) |

**Success Response** (200):
```json
{
  "total_events": 50,
  "suspicious_count": 3,
  "severity_distribution": { "low": 10, "medium": 30, "high": 8, "critical": 2 },
  "top_ips": ["192.168.1.100", "10.0.0.1"],
  "event_type_summary": { "authentication_failure": 20, "user_login": 30 },
  "timeline_summary": { "first_event": "...", "last_event": "...", "duration_minutes": 60 }
}
```

**Error Responses**: 404 (log not found).

---

#### `GET /logs/stats/global`

Method: `GET`
Route: `/api/v1/logs/stats/global`
Description: Get global statistics across all of the user's uploaded logs.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Query Parameters**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| limit | int | 10000 | Max events to analyze (1–100000) |
| bf-threshold | int | 5 | Brute-force threshold |
| bf-window | int | 5 | Brute-force time window (minutes) |

**Success Response** (200): Same shape as `/logs/{log_id}/statistics`.

> ⚠ **CONTRACT VIOLATION**: Route `/logs/stats/global` is defined after `/{log_id}` routes. FastAPI matches routes in definition order, so this works because it comes later — but this is fragile. A future reorder could break routing.

---

### 4. Threat Intelligence

---

#### `POST /threat/extract`

Method: `POST`
Route: `/api/v1/threat/extract`
Description: Extract Indicators of Compromise (IOCs) from raw text.
Authentication: None

**Request — Query OR JSON Body**:
```
POST /api/v1/threat/extract?text=1.2.3.4+malware.exe+evil.com
```

```json
{
  "text": "Connection from 1.2.3.4 downloading malware.exe from evil.com"
}
```

**Success Response** (200):
```json
{
  "iocs": [
    { "indicator": "1.2.3.4", "type": "ip", "context": "..." },
    { "indicator": "evil.com", "type": "domain", "context": "..." },
    { "indicator": "malware.exe", "type": "file", "context": "..." }
  ],
  "total": 3
}
```

> ⚠ **CONTRACT VIOLATION**: Accepts both a query parameter `text` AND a JSON body field `text` — dual input methods are confusing and non-standard. Pick one.

> ⚠ **CONTRACT VIOLATION**: No authentication required despite being an analysis feature. Potential abuse vector.

**Error Responses**: 400 (empty text).

---

#### `GET /threat/extract/{log_id}`

Method: `GET`
Route: `/api/v1/threat/extract/{log_id}`
Description: Extract IOCs from a previously uploaded log and persist them.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Path Parameters**: `log_id` (int)

**Success Response** (200):
```json
[
  {
    "indicator": "1.2.3.4",
    "indicator_type": "ip",
    "log_id": 1,
    "event_line": 42,
    "context": "Connection from 1.2.3.4 on port 22"
  }
]
```

**Error Responses**: 404 (log not found).

---

#### `GET /threat/lookup`

Method: `GET`
Route: `/api/v1/threat/lookup`
Description: Look up reputation data for a single IOC.
Authentication: None

**Query Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| indicator | string | Yes | The IOC value (IP, domain, hash, etc.) |
| type | string | Yes | IOC type: `ip`, `domain`, `url`, `md5`, `sha1`, `sha256`, `email` |

**Success Response** (200):
```json
{
  "indicator": "1.2.3.4",
  "indicator_type": "ip",
  "reputation": {
    "indicator": "1.2.3.4",
    "indicator_type": "ip",
    "threat_score": 85,
    "country": "RU",
    "asn": "AS12345",
    "malware_associations": ["trickbot", "emotet"],
    "threat_actor_associations": ["TA505"],
    "detection_ratio": "15/20",
    "sources": ["abuseipdb", "virustotal"]
  }
}
```

> ⚠ **CONTRACT VIOLATION**: `indicator` should be a **path parameter** (`/threat/lookup/{indicator}`), not a query parameter. Using a query parameter for a required resource identifier breaks REST conventions and disables URL-based caching.

**Error Responses**: 400 (invalid type).

---

#### `GET /threat/cisa-kev`

Method: `GET`
Route: `/api/v1/threat/cisa-kev`
Description: Fetch the CISA Known Exploited Vulnerabilities catalog.
Authentication: None

**Success Response** (200):
```json
[
  {
    "cve_id": "CVE-2024-12345",
    "vendor": "Microsoft",
    "product": "Exchange Server",
    "vulnerability_name": "Microsoft Exchange Remote Code Execution",
    "date_added": "2026-01-15",
    "due_date": "2026-07-15",
    "required_action": "Apply updates per vendor instructions"
  }
]
```

---

#### `GET /threat/cve/{cve_id}`

Method: `GET`
Route: `/api/v1/threat/cve/{cve_id}`
Description: Look up CVE details from the NVD database.
Authentication: None

**Path Parameters**: `cve_id` (string, e.g. `CVE-2024-12345`)

**Success Response** (200):
```json
{
  "cve_id": "CVE-2024-12345",
  "description": "...",
  "cvss_score": 9.8,
  "cvss_severity": "CRITICAL",
  "affected_products": ["..."],
  "references": ["..."]
}
```

**Error Responses**: 404 (CVE not found).

---

#### `GET /threat/nvd/search`

Method: `GET`
Route: `/api/v1/threat/nvd/search`
Description: Search CVEs in the NVD database.
Authentication: None

**Query Parameters**: `q` (string, search query)

**Success Response** (200):
```json
[
  { "cve_id": "CVE-2024-12345", "description": "...", "cvss_score": 9.8 }
]
```

---

#### `GET /threat/iocs`

Method: `GET`
Route: `/api/v1/threat/iocs`
Description: List cached IOC reputation entries with filtering.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Query Parameters**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| q | string | "" | Search by indicator value |
| type | string | "" | Filter by IOC type |
| min-score | float | 0 | Minimum threat score |
| max-score | float | 10 | Maximum threat score |
| skip | int | 0 | ⚠ **NON-STANDARD**: should be `offset` |
| limit | int | 50 | Max results |

**Success Response** (200):
```json
[
  {
    "id": 1,
    "indicator": "1.2.3.4",
    "indicator_type": "ip",
    "threat_score": 85,
    "source": "abuseipdb",
    "created_at": "2026-07-11T10:00:00"
  }
]
```

> ⚠ **CONTRACT VIOLATION**: Uses `skip` for pagination instead of `offset` (used by all other endpoints). Inconsistent pagination parameter naming.

---

#### `GET /threat/iocs/stats`

Method: `GET`
Route: `/api/v1/threat/iocs/stats`
Description: Get aggregate statistics about cached IOCs.
Authentication: None

**Success Response** (200):
```json
{
  "total_iocs": 150,
  "by_type": { "ip": 80, "domain": 40, "url": 20, "hash": 10 },
  "avg_threat_score": 45.2,
  "top_sources": ["abuseipdb", "virustotal"]
}
```

---

#### `GET /threat/iocs/{indicator}`

Method: `GET`
Route: `/api/v1/threat/iocs/{indicator}`
Description: Get detailed information about a specific cached IOC.
Authentication: None

**Path Parameters**: `indicator` (string)

**Success Response** (200):
```json
{
  "indicator": "1.2.3.4",
  "indicator_type": "ip",
  "threat_score": 85,
  "source": "abuseipdb",
  "country": "RU",
  "asn": "AS12345",
  "malware_associations": ["trickbot"],
  "threat_actor_associations": ["TA505"],
  "detection_ratio": "15/20",
  "first_seen": "...",
  "last_seen": "...",
  "created_at": "..."
}
```

**Error Responses**: 404 (IOC not found).

---

#### `GET /threat/correlate/global`

Method: `GET`
Route: `/api/v1/threat/correlate/global`
Description: Correlate all IOCs extracted from the user's logs.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Success Response** (200):
```json
{
  "total_iocs": 50,
  "repeated_iocs": [
    { "indicator": "1.2.3.4", "count": 5, "logs": [1, 2, 3] }
  ],
  "campaigns": [
    { "name": "Campaign 1", "iocs": ["1.2.3.4"], "log_ids": [1, 2] }
  ]
}
```

---

#### `POST /threat/correlate`

Method: `POST`
Route: `/api/v1/threat/correlate`
Description: Correlate a custom list of IOC values.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Request — JSON Body**:
```json
{
  "iocs": ["1.2.3.4", "evil.com", "d41d8cd98f00b204e9800998ecf8427e"]
}
```

**Success Response** (200):
```json
{
  "groups": [
    { "name": "1.2.3.4", "type": "ip", "iocs": ["1.2.3.4"], "reputation": "unknown" }
  ],
  "total": 1
}
```

---

#### `GET /threat/correlate/{log_id}`

Method: `GET`
Route: `/api/v1/threat/correlate/{log_id}`
Description: Correlate IOCs extracted from a specific log.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Path Parameters**: `log_id` (int)

**Success Response** (200): Same shape as `/threat/correlate/global`.

**Error Responses**: 404 (log not found / no IOCs extracted).

---

#### `GET /threat/feed`

Method: `GET`
Route: `/api/v1/threat/feed`
Description: Generate a consolidated threat intelligence feed.
Authentication: None

**Success Response** (200):
```json
{
  "generated_at": "2026-07-11T12:00:00",
  "total_iocs": 100,
  "iocs": [...],
  "recent_cves": [...],
  "summary": "..."
}
```

---

#### `GET /threat/feed/daily`

Method: `GET`
Route: `/api/v1/threat/feed/daily`
Description: Get a daily threat intelligence summary.
Authentication: None

**Success Response** (200):
```json
{
  "date": "2026-07-11",
  "new_iocs": 15,
  "new_cves": 5,
  "top_threats": [...],
  "summary": "..."
}
```

---

### 5. AI

---

#### `GET /ai/providers`

Method: `GET`
Route: `/api/v1/ai/providers`
Description: List available AI providers.
Authentication: None

**Success Response** (200):
```json
[
  { "name": "openai", "available": true, "requires_api_key": true }
]
```

---

#### `GET /ai/providers/active`

Method: `GET`
Route: `/api/v1/ai/providers/active`
Description: Get the currently active AI provider.
Authentication: None

**Success Response** (200):
```json
{
  "name": "openai",
  "available": true,
  "requires_api_key": true
}
```

---

#### `POST /ai/providers/switch`

Method: `POST`
Route: `/api/v1/ai/providers/switch`
Description: Switch the active AI provider.
Authentication: None

**Request — JSON Body**:
```json
{
  "provider": "anthropic"
}
```

**Success Response** (200): Same shape as `/ai/providers/active`.

**Error Responses**: 400 (unknown provider).

---

#### `POST /ai/sessions`

Method: `POST`
Route: `/api/v1/ai/sessions`
Description: Create a new AI chat session.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Request — JSON Body**:
```json
{
  "title": "Investigation 1",
  "context_type": "log",
  "context_id": 1
}
```

**Success Response** (201):
```json
{
  "id": 1,
  "user_id": 1,
  "title": "Investigation 1",
  "context_type": "log",
  "context_id": 1,
  "created_at": "...",
  "updated_at": "..."
}
```

---

#### `GET /ai/sessions`

Method: `GET`
Route: `/api/v1/ai/sessions`
Description: List all chat sessions for the current user.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Success Response** (200): Array of session objects.

---

#### `GET /ai/sessions/{session_id}`

Method: `GET`
Route: `/api/v1/ai/sessions/{session_id}`
Description: Get a specific chat session.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Path Parameters**: `session_id` (int)

**Success Response** (200): Single session object.

**Error Responses**: 404 (session not found).

---

#### `GET /ai/sessions/{session_id}/history`

Method: `GET`
Route: `/api/v1/ai/sessions/{session_id}/history`
Description: Get message history for a chat session.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Success Response** (200):
```json
[
  { "role": "user", "content": "Analyze this log", "timestamp": "..." },
  { "role": "assistant", "content": "...", "timestamp": "..." }
]
```

**Error Responses**: 404 (session not found).

---

#### `POST /ai/chat`

Method: `POST`
Route: `/api/v1/ai/chat`
Description: Send a chat message and get an AI response.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Request — JSON Body**:
```json
{
  "session_id": 1,
  "message": "Analyze this log for threats"
}
```

**Success Response** (200):
```json
{
  "response": "I found 3 suspicious events...",
  "session_id": 1
}
```

**Error Responses**: 404 (session not found).

---

#### `POST /ai/explain`

Method: `POST`
Route: `/api/v1/ai/explain`
Description: Get AI explanation of a security term or concept.
Authentication: None

**Request — JSON Body**:
```json
{
  "text": "What is pass-the-hash?"
}
```

**Success Response** (200):
```json
{
  "explanation": "Pass-the-hash is an attack technique where...",
  "confidence": 0.7
}
```

---

#### `POST /ai/investigate`

Method: `POST`
Route: `/api/v1/ai/investigate`
Description: Perform AI-powered log investigation.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Request — JSON Body**:
```json
{
  "log_id": 1,
  "evidence": ""
}
```

**Success Response** (200):
```json
{
  "summary": "...",
  "suspicious_patterns": [...],
  "critical_events": [...],
  "attack_chain": [...],
  "priorities": [...],
  "recommendations": [...],
  "confidence": 0.85
}
```

**Error Responses**: 400 (must provide log_id or evidence), 404 (log not found).

---

#### `POST /ai/recommendations`

Method: `POST`
Route: `/api/v1/ai/recommendations`
Description: Generate remediation recommendations for a log.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Request — JSON Body**: Same shape as `/ai/investigate`.

**Success Response** (200):
```json
{
  "next_steps": [...],
  "containment": [...],
  "recovery": [...],
  "patching": [...],
  "detection_improvements": [...]
}
```

---

#### `POST /ai/timeline`

Method: `POST`
Route: `/api/v1/ai/timeline`
Description: AI-powered timeline analysis of log events.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Request — JSON Body**: Same shape as `/ai/investigate`.

**Success Response** (200):
```json
{
  "phases": [...],
  "attack_vector": "...",
  "recommendations": [...]
}
```

---

#### `POST /ai/ask`

Method: `POST`
Route: `/api/v1/ai/ask`
Description: Interactive Q&A within a chat session (alias for `/ai/chat`).
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Request → Response**: Identical to `POST /ai/chat`.

> ⚠ **CONTRACT VIOLATION**: `/ai/ask` is functionally identical to `/ai/chat`. Duplicate endpoints should be consolidated.

---

#### `GET /ai/prompts`

Method: `GET`
Route: `/api/v1/ai/prompts`
Description: List available prompt templates.
Authentication: None

**Success Response** (200):
```json
[
  { "name": "log-analysis", "category": "general", "content": "Analyze the following log..." }
]
```

---

#### `GET /ai/prompts/{name}`

Method: `GET`
Route: `/api/v1/ai/prompts/{name}`
Description: Get a specific prompt template by name.
Authentication: None

**Path Parameters**: `name` (string)

**Success Response** (200): Single prompt object.

---

#### `POST /ai/rag/search`

Method: `POST`
Route: `/api/v1/ai/rag/search`
Description: Search indexed RAG documents.
Authentication: None

**Query Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| query | string | Yes | Search query |
| source_type | string | No | Filter by source type |

**Success Response** (200):
```json
{
  "results": [{ "content": "...", "score": 0.95, "source": "..." }],
  "total": 10
}
```

---

#### `POST /ai/rag/index/log/{log_id}`

Method: `POST`
Route: `/api/v1/ai/rag/index/log/{log_id}`
Description: Index a log's events into the RAG system.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Path Parameters**: `log_id` (int)

**Success Response** (200):
```json
{
  "indexed": true,
  "chunks": 50
}
```

**Error Responses**: 404 (log not found / no events).

---

### 6. Case Management

---

#### `GET /cases/templates`

Method: `GET`
Route: `/api/v1/cases/templates`
Description: List report templates.
Authentication: None

**Success Response** (200):
```json
[
  { "id": 1, "name": "Incident Report", "content": "...", "category": "incident", "is_default": true }
]
```

---

#### `GET /cases/templates/{template_id}`

Method: `GET`
Route: `/api/v1/cases/templates/{template_id}`
Description: Get a specific report template.
Authentication: None

**Path Parameters**: `template_id` (int)

**Success Response** (200): Single template object.

**Error Responses**: 404 (template not found).

---

#### `POST /cases/templates`

Method: `POST`
Route: `/api/v1/cases/templates`
Description: Create a new report template.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Request — JSON Body**:
```json
{
  "name": "Incident Report",
  "content": "# Incident Report\n\n## Summary\n{{summary}}",
  "category": "incident",
  "is_default": false
}
```

**Success Response** (201): Single template object.

---

#### `POST /cases/templates/{template_id}/render`

Method: `POST`
Route: `/api/v1/cases/templates/{template_id}/render`
Description: Render a template with variable substitution.
Authentication: None

**Path Parameters**: `template_id` (int)

**Request — JSON Body**: A flat JSON object of template variables.

```json
{
  "summary": "Ransomware attack detected",
  "severity": "critical"
}
```

**Success Response** (200):
```json
{
  "content": "# Incident Report\n\n## Summary\nRansomware attack detected"
}
```

**Error Responses**: 404 (template not found).

---

#### `GET /cases/search/find`

Method: `GET`
Route: `/api/v1/cases/search/find`
Description: Search cases with filters.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Query Parameters**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| query | string | "" | Text search |
| status | string | "" | Filter by status |
| severity | string | "" | Filter by severity |
| case_type | string | "" | Filter by type |
| assigned_analyst | string | "" | Filter by analyst |
| date_from | string | "" | Date range start |
| date_to | string | "" | Date range end |
| is_archived | bool | null | Archived filter |
| limit | int | 50 | Max results |
| offset | int | 0 | Pagination offset |

**Success Response** (200):
```json
[
  { "id": 1, "title": "Phishing Campaign", "status": "open", "severity": "high", ... }
]
```

---

#### `GET /cases/archived/list`

Method: `GET`
Route: `/api/v1/cases/archived/list`
Description: List archived cases.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Success Response** (200): Array of archived case summaries.

---

#### `GET /cases/audit/logs`

Method: `GET`
Route: `/api/v1/cases/audit/logs`
Description: Get audit log entries for case management.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Query Parameters**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| entity_type | string | "" | Filter by entity type |
| entity_id | string | "" | Filter by entity ID |
| limit | int | 100 | Max results |
| offset | int | 0 | Pagination offset |

**Success Response** (200): Array of audit log entries.

---

#### `POST /cases`

Method: `POST`
Route: `/api/v1/cases`
Description: Create a new security case.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Request — JSON Body**:
```json
{
  "title": "Phishing Campaign - Q3",
  "description": "Ongoing phishing campaign targeting finance",
  "case_type": "phishing",
  "severity": "high",
  "assigned_analyst": "analyst1"
}
```

**Success Response** (201):
```json
{
  "id": 1,
  "title": "Phishing Campaign - Q3",
  "status": "open",
  "severity": "high",
  "case_type": "phishing",
  "created_at": "...",
  "assigned_analyst": "analyst1",
  ...
}
```

---

#### `GET /cases`

Method: `GET`
Route: `/api/v1/cases`
Description: List all cases for the current user.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Query Parameters**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| archived | bool | false | Include archived |
| limit | int | 50 | Max results (1–200) |
| offset | int | 0 | Pagination offset |

**Success Response** (200): Array of case summaries.

> ⚠ **CONTRACT VIOLATION**: `POST /cases` and `GET /cases` use an empty string suffix instead of `/cases/`. While this works in FastAPI, it is inconsistent with the pattern used by other routes.

---

#### `GET /cases/{case_id}`

Method: `GET`
Route: `/api/v1/cases/{case_id}`
Description: Get case details.
Authentication: Required

**Path Parameters**: `case_id` (int)

**Request — Headers**: `Authorization: Bearer <token>`

**Success Response** (200): Full case object.

**Error Responses**: 404 (case not found).

---

#### `PUT /cases/{case_id}`

Method: `PUT`
Route: `/api/v1/cases/{case_id}`
Description: Update a case.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Path Parameters**: `case_id` (int)

**Request — JSON Body** (partial update):
```json
{
  "title": "Updated Title",
  "severity": "critical"
}
```

**Success Response** (200): Updated case object.

**Error Responses**: 404 (case not found).

---

#### `DELETE /cases/{case_id}`

Method: `DELETE`
Route: `/api/v1/cases/{case_id}`
Description: Delete a case.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Path Parameters**: `case_id` (int)

**Success Response**: 204 No Content.

**Error Responses**: 404 (case not found).

---

#### `POST /cases/{case_id}/archive`

Method: `POST`
Route: `/api/v1/cases/{case_id}/archive`
Description: Archive a case.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Path Parameters**: `case_id` (int)

**Success Response** (200): Updated case object.

**Error Responses**: 404 (case not found).

---

#### `POST /cases/{case_id}/restore`

Method: `POST`
Route: `/api/v1/cases/{case_id}/restore`
Description: Restore an archived case.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Path Parameters**: `case_id` (int)

**Success Response** (200): Updated case object.

**Error Responses**: 404 (case not found).

---

#### `POST /cases/{case_id}/notes`

Method: `POST`
Route: `/api/v1/cases/{case_id}/notes`
Description: Add an internal note to a case.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Path Parameters**: `case_id` (int)

**Request — JSON Body**:
```json
{
  "content": "Suspicious IP identified: 1.2.3.4"
}
```

**Success Response** (201): Comment/note object.

**Error Responses**: 404 (case not found).

---

#### `GET /cases/{case_id}/notes`

Method: `GET`
Route: `/api/v1/cases/{case_id}/notes`
Description: List internal notes for a case.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Path Parameters**: `case_id` (int)

**Success Response** (200): Array of comment objects.

---

#### `POST /cases/{case_id}/evidence`

Method: `POST`
Route: `/api/v1/cases/{case_id}/evidence`
Description: Add evidence to a case.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Path Parameters**: `case_id` (int)

**Request — JSON Body**:
```json
{
  "evidence_type": "log_file",
  "file_name": "auth.log",
  "file_path": "/uploads/1_auth.log",
  "description": "Authentication log showing brute force",
  "source": "syslog"
}
```

**Success Response** (201): Evidence object.

**Error Responses**: 404 (case not found).

---

#### `GET /cases/{case_id}/evidence`

Method: `GET`
Route: `/api/v1/cases/{case_id}/evidence`
Description: List evidence for a case.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Path Parameters**: `case_id` (int)

**Query Parameters**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| limit | int | 50 | Max results (1–200) |
| offset | int | 0 | Pagination offset |

**Success Response** (200): Array of evidence objects.

---

#### `DELETE /cases/{case_id}/evidence/{evidence_id}`

Method: `DELETE`
Route: `/api/v1/cases/{case_id}/evidence/{evidence_id}`
Description: Remove evidence from a case.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Path Parameters**: `case_id` (int), `evidence_id` (int)

**Success Response**: 204 No Content.

**Error Responses**: 404 (evidence not found).

---

#### `POST /cases/{case_id}/reports`

Method: `POST`
Route: `/api/v1/cases/{case_id}/reports`
Description: Generate a report for a case.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Path Parameters**: `case_id` (int)

**Request — JSON Body**:
```json
{
  "template_id": 1,
  "title": "Incident Report - Phishing Campaign",
  "format": "markdown",
  "sections": ["summary", "timeline", "evidence", "recommendations"]
}
```

**Success Response** (201): Report object.

**Error Responses**: 404 (case not found).

---

#### `GET /cases/{case_id}/reports`

Method: `GET`
Route: `/api/v1/cases/{case_id}/reports`
Description: List reports for a case.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Path Parameters**: `case_id` (int)

**Query Parameters**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| limit | int | 50 | Max results (1–200) |
| offset | int | 0 | Pagination offset |

**Success Response** (200): Array of report objects.

---

#### `GET /cases/{case_id}/reports/{report_id}/export`

Method: `GET`
Route: `/api/v1/cases/{case_id}/reports/{report_id}/export`
Description: Export a report as a downloadable file.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Path Parameters**: `case_id` (int), `report_id` (int)

**Query Parameters**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| fmt | string | "markdown" | Export format |

**Success Response** (200): File download with `Content-Disposition: attachment`.

**Error Responses**: 404 (report not found).

---

#### `GET /cases/{case_id}/timeline`

Method: `GET`
Route: `/api/v1/cases/{case_id}/timeline`
Description: Get a timeline of case investigation activity.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Path Parameters**: `case_id` (int)

**Success Response** (200):
```json
{
  "events": [
    { "timestamp": "...", "type": "evidence_added", "description": "..." }
  ]
}
```

**Error Responses**: 404 (case not found).

---

#### `POST /cases/{case_id}/comments`

Method: `POST`
Route: `/api/v1/cases/{case_id}/comments`
Description: Add a comment to a case.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Path Parameters**: `case_id` (int)

**Request — JSON Body**:
```json
{
  "content": "Shared findings with the team",
  "is_internal": false
}
```

**Success Response** (201): Comment object.

**Error Responses**: 404 (case not found).

---

#### `GET /cases/{case_id}/comments`

Method: `GET`
Route: `/api/v1/cases/{case_id}/comments`
Description: List comments for a case.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Path Parameters**: `case_id` (int)

**Query Parameters**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| internal | bool | false | Include internal comments |

**Success Response** (200): Array of comment objects.

---

#### `GET /cases/{case_id}/activity`

Method: `GET`
Route: `/api/v1/cases/{case_id}/activity`
Description: Get all activity for a case.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Path Parameters**: `case_id` (int)

**Success Response** (200): Array of activity entries.

**Error Responses**: 404 (case not found).

---

### 7. Dashboard

---

#### `GET /dashboard/executive`

Method: `GET`
Route: `/api/v1/dashboard/executive`
Description: Get executive summary data for the security dashboard.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required despite exposing potentially sensitive summary data.

**Success Response** (200):
```json
{
  "total_alerts": 150,
  "critical_alerts": 12,
  "open_cases": 8,
  "active_threats": 5,
  ...
}
```

---

#### `GET /dashboard/summary`

Method: `GET`
Route: `/api/v1/dashboard/summary`
Description: Get full dashboard summary for authenticated user.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Success Response** (200):
```json
{
  "alerts": { "total": 150, "critical": 12 },
  "cases": { "open": 8, "total": 20 },
  "iocs": { "total": 300 },
  "recent_activity": [...]
}
```

---

#### `POST /dashboard/alerts`

Method: `POST`
Route: `/api/v1/dashboard/alerts`
Description: Create a new security alert.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Request — JSON Body**:
```json
{
  "title": "Suspicious Login Detected",
  "severity": "high",
  "alert_type": "login_anomaly",
  "source": "auth.log",
  "description": "..."
}
```

**Success Response** (201): Alert object.

---

#### `GET /dashboard/alerts`

Method: `GET`
Route: `/api/v1/dashboard/alerts`
Description: List alerts with filtering.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required, allowing unauthenticated access to all alerts.

**Query Parameters**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| status | string | "" | Filter by status |
| severity | string | "" | Filter by severity |
| alert_type | string | "" | Filter by type |
| assigned_to | string | "" | Filter by assignee |
| query | string | "" | Text search |
| limit | int | 50 | Max results |
| offset | int | 0 | Pagination offset |

**Success Response** (200): Array of alert objects.

---

#### `GET /dashboard/alerts/stats`

Method: `GET`
Route: `/api/v1/dashboard/alerts/stats`
Description: Get alert statistics.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

**Success Response** (200):
```json
{
  "total": 150,
  "by_severity": { "low": 50, "medium": 60, "high": 30, "critical": 10 },
  "by_status": { "open": 80, "investigating": 40, "resolved": 30 }
}
```

---

#### `GET /dashboard/alerts/{alert_id}`

Method: `GET`
Route: `/api/v1/dashboard/alerts/{alert_id}`
Description: Get a specific alert.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

**Path Parameters**: `alert_id` (int)

**Success Response** (200): Alert object.

**Error Responses**: 404 (alert not found).

---

#### `PUT /dashboard/alerts/{alert_id}`

Method: `PUT`
Route: `/api/v1/dashboard/alerts/{alert_id}`
Description: Update an alert.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Path Parameters**: `alert_id` (int)

**Request — JSON Body** (partial):
```json
{
  "status": "investigating",
  "assigned_to": "analyst1"
}
```

**Success Response** (200): Updated alert object.

**Error Responses**: 404 (alert not found).

---

#### `POST /dashboard/assets`

Method: `POST`
Route: `/api/v1/dashboard/assets`
Description: Register a new asset.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

**Request — JSON Body**:
```json
{
  "name": "web-server-01",
  "asset_type": "server",
  "ip_address": "10.0.0.1",
  "criticality": "high",
  "os": "Linux Ubuntu 22.04"
}
```

**Success Response** (201): Asset object.

---

#### `GET /dashboard/assets`

Method: `GET`
Route: `/api/v1/dashboard/assets`
Description: List assets with filtering.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

**Query Parameters**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| asset_type | string | "" | Filter by type |
| criticality | string | "" | Filter by criticality |
| is_active | bool | null | Active filter |
| query | string | "" | Text search |
| limit | int | 100 | Max results |
| offset | int | 0 | Pagination offset |

**Success Response** (200): Array of asset objects.

---

#### `GET /dashboard/assets/{asset_id}`

Method: `GET`
Route: `/api/v1/dashboard/assets/{asset_id}`
Description: Get a specific asset.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

**Success Response** (200): Asset object.

**Error Responses**: 404 (asset not found).

---

#### `PUT /dashboard/assets/{asset_id}`

Method: `PUT`
Route: `/api/v1/dashboard/assets/{asset_id}`
Description: Update an asset.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

**Request — JSON Body** (partial):
```json
{ "criticality": "critical", "is_active": true }
```

**Success Response** (200): Updated asset object.

**Error Responses**: 404 (asset not found).

---

#### `DELETE /dashboard/assets/{asset_id}`

Method: `DELETE`
Route: `/api/v1/dashboard/assets/{asset_id}`
Description: Delete an asset.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required — anyone can delete assets.

**Success Response**: 204 No Content.

**Error Responses**: 404 (asset not found).

---

#### `GET /dashboard/investigations/stats`

Method: `GET`
Route: `/api/v1/dashboard/investigations/stats`
Description: Get investigation statistics.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

---

#### `GET /dashboard/threat/stats`

Method: `GET`
Route: `/api/v1/dashboard/threat/stats`
Description: Get threat intelligence statistics.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

---

#### `GET /dashboard/logs/stats`

Method: `GET`
Route: `/api/v1/dashboard/logs/stats`
Description: Get log monitoring statistics.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

---

#### `GET /dashboard/charts/severity`

Method: `GET`
Route: `/api/v1/dashboard/charts/severity`
Description: Get severity distribution chart data.
Authentication: None

---

#### `GET /dashboard/charts/attack-timeline`

Method: `GET`
Route: `/api/v1/dashboard/charts/attack-timeline`
Description: Get attack timeline chart data.
Authentication: None

**Query Parameters**: `days` (int, default 7)

---

#### `GET /dashboard/charts/threat-distribution`

Method: `GET`
Route: `/api/v1/dashboard/charts/threat-distribution`
Description: Get threat distribution chart data.
Authentication: None

---

#### `GET /dashboard/charts/ioc-trend`

Method: `GET`
Route: `/api/v1/dashboard/charts/ioc-trend`
Description: Get IOC trend chart data.
Authentication: None

**Query Parameters**: `days` (int, default 30)

---

#### `GET /dashboard/charts/cve-trend`

Method: `GET`
Route: `/api/v1/dashboard/charts/cve-trend`
Description: Get CVE trend chart data.
Authentication: None

**Query Parameters**: `days` (int, default 30)

---

#### `GET /dashboard/charts/event-types`

Method: `GET`
Route: `/api/v1/dashboard/charts/event-types`
Description: Get event type distribution chart data.
Authentication: None

---

#### `POST /dashboard/notifications`

Method: `POST`
Route: `/api/v1/dashboard/notifications`
Description: Create a notification.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Request — JSON Body**:
```json
{
  "type": "alert",
  "title": "New critical alert",
  "message": "..."
}
```

**Success Response** (201): Notification object.

---

#### `GET /dashboard/notifications`

Method: `GET`
Route: `/api/v1/dashboard/notifications`
Description: List notifications.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Query Parameters**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| unread_only | bool | false | Only unread |
| notif_type | string | "" | Filter by type |
| limit | int | 50 | Max results |
| offset | int | 0 | Pagination offset |

**Success Response** (200): Array of notification objects.

---

#### `GET /dashboard/notifications/unread-count`

Method: `GET`
Route: `/api/v1/dashboard/notifications/unread-count`
Description: Get count of unread notifications.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Success Response** (200):
```json
{ "count": 5 }
```

---

#### `POST /dashboard/notifications/{notif_id}/read`

Method: `POST`
Route: `/api/v1/dashboard/notifications/{notif_id}/read`
Description: Mark a notification as read.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Path Parameters**: `notif_id` (int)

**Success Response** (200):
```json
{ "ok": true }
```

**Error Responses**: 404 (notification not found).

---

#### `POST /dashboard/notifications/read-all`

Method: `POST`
Route: `/api/v1/dashboard/notifications/read-all`
Description: Mark all notifications as read.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Success Response** (200):
```json
{ "ok": true, "marked": 5 }
```

---

#### `GET /dashboard/settings`

Method: `GET`
Route: `/api/v1/dashboard/settings`
Description: Get user settings.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Success Response** (200):
```json
{
  "theme": "dark",
  "notifications_enabled": true,
  "default_view": "dashboard"
}
```

---

#### `PUT /dashboard/settings`

Method: `PUT`
Route: `/api/v1/dashboard/settings`
Description: Update user settings.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Request — JSON Body** (partial):
```json
{
  "theme": "light"
}
```

**Success Response** (200): Updated settings object.

---

#### `GET /dashboard/users/analysts`

Method: `GET`
Route: `/api/v1/dashboard/users/analysts`
Description: List all analysts/users.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

> ⚠ **CONTRACT VIOLATION**: Returns all users (including their emails and roles) with no role-based filtering. Any authenticated user can enumerate the full user list.

**Success Response** (200):
```json
[
  { "id": 1, "username": "admin", "email": "admin@sentinel.local", "role": "admin", "created_at": "..." }
]
```

---

#### `GET /dashboard/users/activity`

Method: `GET`
Route: `/api/v1/dashboard/users/activity`
Description: Get user activity audit log.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Query Parameters**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| limit | int | 50 | Max results |
| offset | int | 0 | Pagination offset |

> ⚠ **CONTRACT VIOLATION**: The `limit` parameter is silently capped at 500 server-side but the contract specifies the user's input is accepted.

**Success Response** (200): Array of audit log entries with usernames.

---

### 8. Detection

---

#### `POST /detection/rules`

Method: `POST`
Route: `/api/v1/detection/rules`
Description: Create a custom detection rule.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Request — JSON Body**:
```json
{
  "name": "Brute Force Detection",
  "description": "Detect multiple failed logins",
  "rule_type": "frequency",
  "severity": "high",
  "category": "authentication",
  "conditions": { "field": "event_type", "operator": "eq", "value": "authentication_failure" },
  "threshold": 5,
  "window_minutes": 5
}
```

**Success Response** (201): Rule object.

---

#### `GET /detection/rules`

Method: `GET`
Route: `/api/v1/detection/rules`
Description: List detection rules.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

**Query Parameters**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| category | string | "" | Filter by category |
| rule_type | string | "" | Filter by type |
| severity | string | "" | Filter by severity |
| enabled_only | bool | false | Only enabled rules |
| query | string | "" | Text search |
| limit | int | 100 | Max results |
| offset | int | 0 | Pagination offset |

**Success Response** (200): Array of rule objects.

---

#### `GET /detection/rules/{rule_id}`

Method: `GET`
Route: `/api/v1/detection/rules/{rule_id}`
Description: Get a specific detection rule.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

**Success Response** (200): Rule object.

**Error Responses**: 404 (rule not found).

---

#### `PUT /detection/rules/{rule_id}`

Method: `PUT`
Route: `/api/v1/detection/rules/{rule_id}`
Description: Update a detection rule.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Path Parameters**: `rule_id` (int)

**Request — JSON Body** (partial):
```json
{ "enabled": false }
```

**Success Response** (200): Updated rule object.

**Error Responses**: 404 (rule not found).

---

#### `DELETE /detection/rules/{rule_id}`

Method: `DELETE`
Route: `/api/v1/detection/rules/{rule_id}`
Description: Delete a detection rule.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required — anyone can delete rules.

**Success Response**: 204 No Content.

**Error Responses**: 404 (rule not found).

---

#### `POST /detection/rules/{rule_id}/test`

Method: `POST`
Route: `/api/v1/detection/rules/{rule_id}/test`
Description: Test a detection rule against sample data.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

**Path Parameters**: `rule_id` (int)

**Request — JSON Body**: A bare array of strings (not a named field):
```json
[
  "Failed password for root from 1.2.3.4 port 22",
  "Accepted password for admin from 10.0.0.1 port 22"
]
```

> ⚠ **CONTRACT VIOLATION**: Accepts a bare JSON array as body instead of a wrapped object `{ "sample_data": [...] }`.

**Success Response** (200):
```json
{
  "matched": 1,
  "total": 2,
  "results": [...]
}
```

---

#### `POST /detection/sigma`

Method: `POST`
Route: `/api/v1/detection/sigma`
Description: Create a Sigma rule.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

**Request — JSON Body**:
```json
{
  "title": "Suspicious RDP Connection",
  "logsource": { "category": "network_connection", "product": "windows" },
  "detection": { "selection": { "EventID": 4624 } },
  "condition": "selection"
}
```

**Success Response** (201): Sigma rule object.

---

#### `GET /detection/sigma`

Method: `GET`
Route: `/api/v1/detection/sigma`
Description: List Sigma rules.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

**Query Parameters**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| level | string | "" | Filter by level |
| status | string | "" | Filter by status |
| query | string | "" | Text search |
| limit | int | 100 | Max results |
| offset | int | 0 | Pagination offset |

---

#### `GET /detection/sigma/{rule_id}`

Method: `GET`
Route: `/api/v1/detection/sigma/{rule_id}`
Description: Get a specific Sigma rule.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

---

#### `DELETE /detection/sigma/{rule_id}`

Method: `DELETE`
Route: `/api/v1/detection/sigma/{rule_id}`
Description: Delete a Sigma rule.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

---

#### `POST /detection/sigma/validate`

Method: `POST`
Route: `/api/v1/detection/sigma/validate`
Description: Validate a Sigma rule YAML content.
Authentication: None

**Request — JSON Body**: A raw string (not wrapped in an object):
```json
"title: Test\ndetection:\n  selection:\n    EventID: 4624\n  condition: selection"
```

> ⚠ **CONTRACT VIOLATION**: Accepts a raw string as body instead of `{ "content": "..." }`.

**Success Response** (200):
```json
{
  "valid": true,
  "errors": []
}
```

---

#### `POST /detection/sigma/{rule_id}/execute`

Method: `POST`
Route: `/api/v1/detection/sigma/{rule_id}/execute`
Description: Execute a Sigma rule against events.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

**Request — JSON Body**: A bare array:
```json
[ { "EventID": 4624, "TargetUserName": "admin" } ]
```

**Success Response** (200):
```json
{
  "matched": true,
  "results": [...]
}
```

---

#### `GET /detection/sigma/{rule_id}/export`

Method: `GET`
Route: `/api/v1/detection/sigma/{rule_id}/export`
Description: Export a Sigma rule in YAML format.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

**Success Response** (200): Raw YAML string.

---

#### `POST /detection/yara`

Method: `POST`
Route: `/api/v1/detection/yara`
Description: Create a YARA rule.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

**Request — JSON Body**:
```json
{
  "name": "MalwareDetect",
  "description": "Detects known malware pattern",
  "rule_content": "rule MalwareDetect { strings: $a = \"malware\" condition: $a }",
  "tags": ["malware", "trojan"]
}
```

---

#### `GET /detection/yara`

Method: `GET`
Route: `/api/v1/detection/yara`
Description: List YARA rules.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

---

#### `GET /detection/yara/{rule_id}`

Method: `GET`
Route: `/api/v1/detection/yara/{rule_id}`
Description: Get a specific YARA rule.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

---

#### `DELETE /detection/yara/{rule_id}`

Method: `DELETE`
Route: `/api/v1/detection/yara/{rule_id}`
Description: Delete a YARA rule.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

---

#### `POST /detection/yara/validate`

Method: `POST`
Route: `/api/v1/detection/yara/validate`
Description: Validate YARA rule content.
Authentication: None

**Request — JSON Body**: Raw string.

> ⚠ **CONTRACT VIOLATION**: Same bare-string body pattern as `/detection/sigma/validate`.

**Success Response** (200):
```json
{ "valid": true, "errors": [] }
```

---

#### `POST /detection/yara/{rule_id}/scan`

Method: `POST`
Route: `/api/v1/detection/yara/{rule_id}/scan`
Description: Scan file contents against a YARA rule.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

**Request — JSON Body**: Bare array of strings.

---

#### `GET /detection/hunts/results`

Method: `GET`
Route: `/api/v1/detection/hunts/results`
Description: List threat hunting results.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

> ⚠ **CONTRACT VIOLATION**: Static route `/hunts/results` must be registered before parameterized routes to avoid being matched as `/hunts/{hunt_id}`.

---

#### `POST /detection/hunts`

Method: `POST`
Route: `/api/v1/detection/hunts`
Description: Create a saved hunt.
Authentication: Required

---

#### `GET /detection/hunts`

Method: `GET`
Route: `/api/v1/detection/hunts`
Description: List saved hunts.
Authentication: Required

---

#### `GET /detection/hunts/{hunt_id}`

Method: `GET`
Route: `/api/v1/detection/hunts/{hunt_id}`
Description: Get a saved hunt.
Authentication: Required

---

#### `DELETE /detection/hunts/{hunt_id}`

Method: `DELETE`
Route: `/api/v1/detection/hunts/{hunt_id}`
Description: Delete a saved hunt.
Authentication: Required

---

#### `POST /detection/hunts/{hunt_id}/execute`

Method: `POST`
Route: `/api/v1/detection/hunts/{hunt_id}/execute`
Description: Execute a saved hunt.
Authentication: Required

---

#### `POST /detection/jobs`

Method: `POST`
Route: `/api/v1/detection/jobs`
Description: Create a scheduled scan job.
Authentication: Required

---

#### `GET /detection/jobs`

Method: `GET`
Route: `/api/v1/detection/jobs`
Description: List scheduled jobs.
Authentication: Required

---

#### `PUT /detection/jobs/{job_id}`

Method: `PUT`
Route: `/api/v1/detection/jobs/{job_id}`
Description: Update a scheduled job.
Authentication: Required

---

#### `DELETE /detection/jobs/{job_id}`

Method: `DELETE`
Route: `/api/v1/detection/jobs/{job_id}`
Description: Delete a scheduled job.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

---

#### `POST /detection/jobs/{job_id}/run`

Method: `POST`
Route: `/api/v1/detection/jobs/{job_id}/run`
Description: Execute a scheduled job immediately.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

---

#### `POST /detection/automation`

Method: `POST`
Route: `/api/v1/detection/automation`
Description: Create an alert automation rule.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

---

#### `GET /detection/automation`

Method: `GET`
Route: `/api/v1/detection/automation`
Description: List alert automation rules.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

---

#### `PUT /detection/automation/{rule_id}`

Method: `PUT`
Route: `/api/v1/detection/automation/{rule_id}`
Description: Update an automation rule.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

---

#### `DELETE /detection/automation/{rule_id}`

Method: `DELETE`
Route: `/api/v1/detection/automation/{rule_id}`
Description: Delete an automation rule.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

---

#### `POST /detection/ai/generate-sigma`

Method: `POST`
Route: `/api/v1/detection/ai/generate-sigma`
Description: Generate a Sigma rule from natural language.
Authentication: None

**Request — JSON Body**: Raw string.

> ⚠ **CONTRACT VIOLATION**: Accepts raw string body instead of `{ "text": "..." }`.

**Success Response** (200):
```json
{ "content": "title: Generated Rule\n..." }
```

---

#### `POST /detection/ai/generate-yara`

Method: `POST`
Route: `/api/v1/detection/ai/generate-yara`
Description: Generate a YARA rule from a description.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: Same bare-string pattern.

---

#### `POST /detection/ai/explain`

Method: `POST`
Route: `/api/v1/detection/ai/explain`
Description: Explain a detection rule.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: Same bare-string pattern.

---

#### `POST /detection/ai/improve`

Method: `POST`
Route: `/api/v1/detection/ai/improve`
Description: Improve a detection rule with AI suggestions.
Authentication: None

**Query Parameters**: `suggestion` (string, optional)

**Request — JSON Body**: Raw string.

> ⚠ **CONTRACT VIOLATION**: Same bare-string pattern.

---

#### `POST /detection/playbooks`

Method: `POST`
Route: `/api/v1/detection/playbooks`
Description: Create a workflow playbook.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

---

#### `GET /detection/playbooks`

Method: `GET`
Route: `/api/v1/detection/playbooks`
Description: List workflow playbooks.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

---

#### `GET /detection/playbooks/{playbook_id}`

Method: `GET`
Route: `/api/v1/detection/playbooks/{playbook_id}`
Description: Get a specific playbook.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

---

#### `DELETE /detection/playbooks/{playbook_id}`

Method: `DELETE`
Route: `/api/v1/detection/playbooks/{playbook_id}`
Description: Delete a playbook.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

---

#### `POST /detection/reports`

Method: `POST`
Route: `/api/v1/detection/reports`
Description: Create a hunting report.
Authentication: Required

---

#### `GET /detection/reports`

Method: `GET`
Route: `/api/v1/detection/reports`
Description: List hunting reports.
Authentication: Required

---

#### `GET /detection/analytics`

Method: `GET`
Route: `/api/v1/detection/analytics`
Description: Get detection analytics and metrics.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

---

#### `POST /detection/analytics/hit`

Method: `POST`
Route: `/api/v1/detection/analytics/hit`
Description: Record a rule hit for analytics.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

> ⚠ **CONTRACT VIOLATION**: This is a POST endpoint but uses individual **query parameters** (`rule_type`, `rule_id`, `event_source`, `match_detail`, `severity`) instead of a JSON body.

**Success Response** (200):
```json
{ "ok": true }
```

---

### 9. Enterprise

---

#### `GET /enterprise/notifications`

Method: `GET`
Route: `/api/v1/enterprise/notifications`
Description: List notification configurations.
Authentication: Required

---

#### `POST /enterprise/notifications`

Method: `POST`
Route: `/api/v1/enterprise/notifications`
Description: Create a notification configuration.
Authentication: Required

---

#### `DELETE /enterprise/notifications/{notif_id}`

Method: `DELETE`
Route: `/api/v1/enterprise/notifications/{notif_id}`
Description: Delete a notification configuration.
Authentication: Required

---

#### `POST /enterprise/notifications/send`

Method: `POST`
Route: `/api/v1/enterprise/notifications/send`
Description: Send a notification immediately.
Authentication: Required

**Request — JSON Body**:
```json
{
  "event": "alert.critical",
  "data": { "title": "...", "message": "..." }
}
```

---

#### `POST /enterprise/orgs`

Method: `POST`
Route: `/api/v1/enterprise/orgs`
Description: Create an organization.
Authentication: Required

---

#### `GET /enterprise/orgs`

Method: `GET`
Route: `/api/v1/enterprise/orgs`
Description: List user's organizations.
Authentication: Required

---

#### `GET /enterprise/orgs/{org_id}`

Method: `GET`
Route: `/api/v1/enterprise/orgs/{org_id}`
Description: Get organization details.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required — org details are public.

---

#### `POST /enterprise/orgs/{org_id}/members`

Method: `POST`
Route: `/api/v1/enterprise/orgs/{org_id}/members`
Description: Add a member to an organization.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required — anyone can add members.

---

#### `DELETE /enterprise/orgs/{org_id}/members/{user_id}`

Method: `DELETE`
Route: `/api/v1/enterprise/orgs/{org_id}/members/{user_id}`
Description: Remove a member from an organization.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required — anyone can remove members.

---

#### `GET /enterprise/plans`

Method: `GET`
Route: `/api/v1/enterprise/plans`
Description: List available billing plans.
Authentication: None

---

#### `GET /enterprise/subscriptions/{org_id}`

Method: `GET`
Route: `/api/v1/enterprise/subscriptions/{org_id}`
Description: Get subscription details.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

---

#### `POST /enterprise/subscriptions/{org_id}/change`

Method: `POST`
Route: `/api/v1/enterprise/subscriptions/{org_id}/change`
Description: Change subscription plan.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

---

#### `GET /enterprise/subscriptions/{org_id}/check-limit`

Method: `GET`
Route: `/api/v1/enterprise/subscriptions/{org_id}/check-limit`
Description: Check if the API usage is within plan limits.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

---

#### `GET /enterprise/integrations`

Method: `GET`
Route: `/api/v1/enterprise/integrations`
Description: List integrations for an organization.
Authentication: None

**Query Parameters**: `org_id` (int, required)

> ⚠ **CONTRACT VIOLATION**: No authentication required — integrations and their configs are exposed.

---

#### `POST /enterprise/integrations`

Method: `POST`
Route: `/api/v1/enterprise/integrations`
Description: Create a new integration.
Authentication: None

**Query Parameters**: `org_id` (int, required)

> ⚠ **CONTRACT VIOLATION**: No authentication required.

---

#### `DELETE /enterprise/integrations/{int_id}`

Method: `DELETE`
Route: `/api/v1/enterprise/integrations/{int_id}`
Description: Delete an integration.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

---

#### `POST /enterprise/integrations/{int_id}/test`

Method: `POST`
Route: `/api/v1/enterprise/integrations/{int_id}/test`
Description: Test an integration connection.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

---

#### `POST /enterprise/integrations/{int_id}/send`

Method: `POST`
Route: `/api/v1/enterprise/integrations/{int_id}/send`
Description: Send an event via an integration.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

---

#### `POST /enterprise/backups`

Method: `POST`
Route: `/api/v1/enterprise/backups`
Description: Create a manual backup.
Authentication: Required

---

#### `GET /enterprise/backups`

Method: `GET`
Route: `/api/v1/enterprise/backups`
Description: List backups.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required — backup listing is unauthenticated.

---

#### `POST /enterprise/backups/{backup_id}/restore`

Method: `POST`
Route: `/api/v1/enterprise/backups/{backup_id}/restore`
Description: Restore from a backup.
Authentication: Required (role: admin)

---

#### `GET /enterprise/metrics`

Method: `GET`
Route: `/api/v1/enterprise/metrics`
Description: Get API performance metrics.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required — internal performance data is exposed.

**Query Parameters**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| endpoint | string | "" | Filter by endpoint |
| limit | int | 100 | Max results |
| offset | int | 0 | Pagination offset |

---

#### `GET /enterprise/metrics/stats`

Method: `GET`
Route: `/api/v1/enterprise/metrics/stats`
Description: Get aggregated API metric statistics.
Authentication: None

> ⚠ **CONTRACT VIOLATION**: No authentication required.

**Success Response** (200):
```json
{
  "total_requests": 10000,
  "avg_duration_ms": 45.2,
  "top_endpoints": [
    { "endpoint": "/api/v1/logs/", "hits": 500, "avg_dur": 30.1 }
  ]
}
```

---

### 10. Plugins

---

#### `GET /plugins/`

Method: `GET`
Route: `/api/v1/plugins/`
Description: List registered plugins.
Authentication: Required

**Request — Headers**: `Authorization: Bearer <token>`

**Query Parameters**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| type | string | "" | Filter by plugin type |

---

#### `GET /plugins/{plugin_id}`

Method: `GET`
Route: `/api/v1/plugins/{plugin_id}`
Description: Get a specific plugin's details.
Authentication: Required

---

#### `POST /plugins/{plugin_id}/enable`

Method: `POST`
Route: `/api/v1/plugins/{plugin_id}/enable`
Description: Enable a plugin.
Authentication: Required

---

#### `POST /plugins/{plugin_id}/disable`

Method: `POST`
Route: `/api/v1/plugins/{plugin_id}/disable`
Description: Disable a plugin.
Authentication: Required

---

#### `PUT /plugins/{plugin_id}/config`

Method: `PUT`
Route: `/api/v1/plugins/{plugin_id}/config`
Description: Update a plugin's configuration.
Authentication: Required

**Request — JSON Body**:
```json
{
  "config": { "api_key": "...", "endpoint": "https://..." }
}
```

---

#### `POST /plugins/discover`

Method: `POST`
Route: `/api/v1/plugins/discover`
Description: Discover and register new plugins from a directory.
Authentication: Required

**Query Parameters**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| dir | string | "" | Plugin directory path |

---

#### `POST /plugins/reload`

Method: `POST`
Route: `/api/v1/plugins/reload`
Description: Reload bundled plugins from the filesystem.
Authentication: Required

---

## Summary of Contract Violations

| # | Endpoint | Violation | Severity |
|---|----------|-----------|----------|
| 1 | `GET /logs/`, `GET /logs/{log_id}` | Duplicate fields: `format`/`source_type`, `total_events`/`event_count` | Medium |
| 2 | `GET /logs/{log_id}/events.json` | Raw dict response instead of typed model (identical to `/events`) | Medium |
| 3 | `GET /threat/iocs` | Uses `skip` instead of `offset` (pagination inconsistency) | Low |
| 4 | `GET /threat/lookup` | `indicator` as query param instead of path param | Medium |
| 5 | `POST /threat/extract` | Dual input method (query param + JSON body) | Medium |
| 6 | `POST /threat/extract` | No authentication | High |
| 7 | `/detection/*` (many) | Inconsistent auth — most GET/DELETE/POST have no auth | **Critical** |
| 8 | `/dashboard/*` (many) | Inconsistent auth — several endpoints lack auth | **Critical** |
| 9 | `/enterprise/*` (many) | Inconsistent auth — orgs, subscriptions, integrations, backups all unauthenticated | **Critical** |
| 10 | `POST /detection/rules/{rule_id}/test` | Bare array request body instead of wrapped object | Low |
| 11 | `POST /detection/sigma/validate` | Raw string request body instead of wrapped object | Low |
| 12 | `POST /detection/ai/*` | Raw string request body instead of wrapped object | Low |
| 13 | `POST /detection/analytics/hit` | POST uses query params instead of JSON body | Medium |
| 14 | `POST /ai/ask` | Duplicate endpoint — same functionality as `/ai/chat` | Low |
| 15 | `GET /dashboard/users/analysts` | User enumeration — any authenticated user can list all users | Medium |
| 16 | All endpoints | No unified response envelope (`data`, `total`, `page`) | Medium |
| 17 | All endpoints | No structured error model (bare `{"detail": "..."}`) | Low |
| 18 | `GET /health` | `database` field is a string instead of a structured object | Low |
| 19 | `POST /cases`, `GET /cases` | Empty string suffix instead of `/` | Low |
| 20 | `GET /logs/stats/global` | Fragile route placement after `/{log_id}` | Low |
