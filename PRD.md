# Sentinel — Product Requirements Document

**Status:** Draft v1.0
**Author:** Product Management
**Target Audience:** Engineering, Design, Investors

---

## 1. Product Vision

### What is Sentinel?

Sentinel is an AI-powered desktop Security Operations Center (SOC) platform for cybersecurity analysts, students, researchers, and small security teams. It combines log analysis, threat intelligence enrichment, AI-assisted investigation, case management, and incident reporting into a single offline-capable desktop application.

### Why does it exist?

Small-to-medium security teams and individual analysts face a brutal gap in the market. Enterprise SIEM/SOC platforms cost tens of thousands of dollars per seat, require dedicated infrastructure to deploy and maintain, generate steep learning curves that take months to climb, force analysts to juggle 8–12 disconnected tools for log analysis, IOC enrichment, and reporting, and are often impossible to use offline or on closed networks. The SMB market is systematically underserved. Sentinel exists to close that gap.

### How it differs from traditional SIEM/SOC products

Traditional SIEMs are built for large-scale ingestion, centralized log storage, and compliance monitoring. Sentinel is built for depth of investigation, not breadth of ingestion. Where Splunk asks "what is happening across 10,000 endpoints," Sentinel asks "what happened in this incident, and what do we do about it." It prioritizes analyst workflow over data pipeline, local-first operation over cloud dependency, and AI augmentation over manual correlation.

### Long-term vision

Sentinel becomes the defacto open-core platform for security investigation, analogous to what VS Code is for development or what Obsidian is for knowledge management — a free, extensible, local-first desktop tool that analysts configure for their workflow rather than being configured by a vendor. The platform evolves from standalone desktop app to extensible ecosystem with community plugins, AI agent workflows, and optional cloud synchronization for teams, while remaining free and offline-capable at its core.

---

## 2. Target Users

### SOC Analysts (Level 1–2)

**Goals:** Triage alerts quickly, enrich IOCs without switching tools, document findings in reports.

**Pain points:** Spending 60% of their time context-switching between VirusTotal, AbuseIPDB, email, ticketing systems, and log viewers. Manual copy-paste workflows that are error-prone and slow.

### Incident Responders

**Goals:** Rapidly analyze evidence, reconstruct attack timelines, produce executive summaries.

**Pain points:** Pressure to move fast while maintaining forensic accuracy. Disconnected data sources make timeline reconstruction tedious. Reporting is an afterthought done under time pressure.

### Cybersecurity Students

**Goals:** Learn investigation workflows, understand attack patterns, practice with real-world log analysis.

**Pain points:** No access to enterprise tools. Expensive licenses. No guided AI assistance to explain findings.

### Blue Teams

**Goals:** Run regular security exercises, document incidents, maintain investigation readiness.

**Pain points:** Budget-constrained. Cannot justify SIEM spend for low-volume environments. Need a tool that works when they need it, not one that requires always-on infrastructure.

### Small Security Teams (1–5 analysts)

**Goals:** Cover all security operations functions with minimal headcount.

**Pain points:** Every analyst is a generalist; they cannot afford specialists in log analysis, threat intel, and reporting. Need a force multiplier.

### Malware Analysts & Threat Hunters

**Goals:** Extract IOCs from samples and logs, cross-reference intelligence feeds, build investigation narratives.

**Pain points:** Existing tools are either enterprise-scale or single-purpose scripts. No middle ground exists.

### Researchers

**Goals:** Study attack patterns, publish findings, experiment with detection rules.

**Pain points:** Need a reproducible, documented investigation environment. Want AI assistance for exploring hypotheses.

---

## 3. Problem Statement

### Manual Log Investigation is Slow

Analysts spend hours scrolling through raw log files, filtering noise, and manually correlating events. Without automated parsing and timeline generation, critical indicators are missed and investigation time balloons.

### IOC Enrichment is Fragmented

Threat intelligence workflows require analysts to manually copy indicators into VirusTotal, AbuseIPDB, AlienVault OTX, and other services. Each context switch costs time and mental energy. Many teams skip enrichment entirely due to friction.

### Security Tools are Disconnected

Log analysis happens in one tool, IOC lookup in another, case management in a third, and reporting in a fourth. None of these tools share data. This fragmentation leads to lost context, duplicated effort, and incomplete investigations.

### Enterprise SIEMs are Inaccessible

Splunk, Elastic, and Microsoft Sentinel require significant infrastructure, licensing budgets, and dedicated engineering support. Small teams, students, and individual researchers cannot access these platforms, yet they face the same security threats.

### No AI Assistance in Existing Workflows

Modern SOC analysts could benefit enormously from AI assistance — explaining suspicious events, suggesting investigation paths, drafting incident reports — but existing tools lack native AI integration. Analysts resort to copying data into ChatGPT, breaking security boundaries.

### Reporting is an Afterthought

Incident reports are typically written manually after the investigation is complete. They are inconsistent, time-consuming to produce, and often omit critical details. No tool integrates investigation data directly into report generation.

---

## 4. Product Goals

**Goal 1:** Reduce average investigation time by 50% compared to manual tool-switching workflows.

**Goal 2:** Eliminate context-switching by providing log analysis, IOC enrichment, AI investigation, case management, and reporting in a single application.

**Goal 3:** Achieve 95%+ accuracy on supported log format parsing (Windows Event Logs, Syslog, Apache, Nginx, JSON, CSV, XML).

**Goal 4:** Enable full offline operation for all core features, with online-only features clearly labeled.

**Goal 5:** Deliver a first-class Electron desktop experience with sub-5-second cold startup and native Windows integration.

**Goal 6:** Process a complete investigation — from log upload to report export — in under 30 minutes for standard incident types.

**Goal 7:** Provide AI assistance that is explainable, citeable, and auditable — never a black box.

---

## 5. Core Features

### Must Have (Version 1)

| Feature | Description |
|---------|-------------|
| Authentication | JWT-based local authentication with role-based access control (Admin, Analyst, Viewer). MFA support via TOTP. |
| Dashboard | Security overview widget showing recent logs, open cases, threat intelligence summary, and system health. |
| Log Upload | Drag-and-drop file upload supporting multiple log formats. Client-side validation before upload. |
| Log Parsing | Automatic format detection and parsing for Windows EVTX, Syslog, Apache, Nginx, JSON, CSV, XML. |
| IOC Extraction | Regex and pattern-based extraction of IPs, domains, hashes, URLs, email addresses from parsed events. |
| Threat Intelligence | One-click IOC enrichment via VirusTotal, AbuseIPDB, AlienVault OTX. Cached results to avoid API rate limits. |
| AI Copilot | Chat-based AI assistant with context-aware investigation support. Supports OpenAI, Gemini, Ollama providers. |
| Case Management | Create, update, close investigation cases. Attach evidence, add comments, link to logs and IOCs. |
| Reports | Generate PDF, HTML, and JSON incident reports from case data. Export full investigation narratives. |
| Settings | Configure AI providers, threat intelligence API keys, notification preferences, and application theme. |
| SQLite Storage | All data persisted locally in SQLite. No external database dependency. |
| Electron Desktop | Native Windows desktop application with system tray, auto-updater, splash screen, and single-instance lock. |
| Local Evidence Storage | Uploaded logs, reports, and case evidence stored on local filesystem. |

### Should Have (Version 2)

| Feature | Description |
|---------|-------------|
| Timeline View | Linear visualization of events reconstructed from parsed log data with attack chain highlighting. |
| MITRE ATT&CK Mapping | Automatic mapping of detected events to MITRE ATT&CK techniques and tactics. |
| Sigma Rule Viewer | Browse, search, and apply Sigma detection rules against parsed events. |
| YARA Rule Viewer | Browse, search, and apply YARA rules against extracted file IOCs. |
| Notification Center | In-app notification system for investigation updates, threat intel matches, and system events. |
| Advanced Search | Full-text search across logs, cases, IOCs, and reports with filtering and saved searches. |
| Tagging | User-defined tags for logs, cases, IOCs, and reports with color coding and filterable tag lists. |
| Dashboard Customization | Configurable dashboard widgets, layouts, and saved dashboard presets. |
| Dark Theme Refinements | Polished dark theme with proper contrast ratios, reduced eye strain, and consistent styling. |

### Nice to Have (Future)

| Feature | Description |
|---------|-------------|
| Multi-User Collaboration | Shared cases, comments, and evidence across team members with sync layer. |
| Live Log Monitoring | File system watcher for real-time log ingestion from configured directories. |
| Plugin System | Community-contributed parsers, enrichment providers, export formats, and AI tools. |
| Cloud Synchronization | Optional encrypted sync of cases and findings across devices. |
| AI Automation Workflows | Configurable AI agent pipelines: auto-enrich, auto-classify, auto-report. |
| Scheduled Scans | Periodic log directory scans, threat intel lookups, and report generation. |
| Asset Inventory | Track IP addresses, hostnames, and software versions extracted from logs. |

---

## 6. User Journey

```
Launch Sentinel
    │
    ▼
Splash Screen (app initializing)
    │
    ▼
Authentication (login / register)
    │
    ▼
Dashboard (overview of recent activity)
    │
    ▼
Upload Log Files (drag-and-drop)
    │
    ▼
Automatic Parsing & Format Detection (progress indicator)
    │
    ▼
IOC Extraction (auto-extracted indicators shown inline)
    │
    ▼
Threat Intelligence Enrichment (one-click per IOC)
    │
    ▼
AI Investigation (ask questions about events, get explanations)
    │
    ▼
Case Creation (capture findings, attach evidence)
    │
    ▼
Report Generation (auto-populated from case data)
    │
    ▼
Export (PDF / HTML / JSON to local filesystem)
    │
    ▼
Close Investigation (case resolved, artifacts archived)
```

### Alternative paths

- **Quick triage:** Upload → Parse → AI ask → export findings as notes. Skip case creation and formal reporting.
- **Deep dive:** Upload → Parse → Extract IOCs → Enrich all → Map to MITRE ATT&CK → Build timeline → Create case → Write report.
- **Training mode:** Upload sample logs → AI explains each suspicious event → Student documents analysis → Export report as learning exercise.

---

## 7. Functional Requirements

### 7.1 Authentication

- JWT-based token authentication with configurable expiry (default 24 hours).
- Local user registration with password hashing (bcrypt).
- Role-based access control: Admin, Analyst, Viewer.
- Admin role: full system access, user management, settings configuration.
- Analyst role: create/edit cases, upload logs, run investigations.
- Viewer role: read-only access to cases, logs, reports.
- TOTP-based multi-factor authentication (optional, per-user toggle).
- Session management: login, logout, token refresh, session timeout.
- First-run setup wizard: create admin account on initial launch.

### 7.2 Dashboard

- Widget-based layout showing:
  - Recent cases (last 7 days) with status badges.
  - Recent log uploads with format, size, and timestamp.
  - Threat intelligence summary (total IOCs enriched, suspicious findings).
  - System health (backend status, database size, storage usage).
- Quick-action buttons: Upload Logs, New Case, Open AI Copilot.
- Auto-refresh with configurable interval (default 30 seconds).

### 7.3 Log Analysis

- File upload via drag-and-drop or file picker. Maximum file size: 500 MB.
- Server-side format detection via file signature and content inspection.
- Supported formats: Windows EVTX, Syslog (RFC 3164, RFC 5424), Apache access/error, Nginx access/error, JSON array/NDJSON, CSV with header detection, XML structured logs.
- Parsing engine extracts: timestamps, event types, source/destination IPs, usernames, process names, severity levels, raw message content.
- Detection capabilities: brute-force attempts (multiple failed logins), suspicious PowerShell execution, privilege escalation indicators (SID history, token manipulation), malware persistence mechanisms (registry run keys, scheduled tasks).
- Timeline generation: parsed events sorted and grouped by time with manual inspection view.
- Event filtering: filter by type, severity, time range, source IP.
- Search: full-text search across all parsed events with highlighted results.

### 7.4 Threat Intelligence

- IOC extraction using regex patterns for: IPv4, IPv6, domains, FQDNs, URLs, MD5/SHA1/SHA256 hashes, email addresses, file paths.
- Integration adapters for: VirusTotal (file hash, IP, domain, URL lookup), AbuseIPDB (IP reputation, country, ISP, reports), AlienVault OTX (pulse lookup, IOC correlation).
- API key management: configure per-service keys with test-connection button.
- Caching: enrichment results cached locally to avoid duplicate API calls and respect rate limits.
- Confidence scoring: aggregate signals from multiple sources into a single confidence rating.
- Batch enrichment: select multiple IOCs for simultaneous lookup.

### 7.5 AI Assistant

- Chat interface with conversation history and per-session context.
- Context-aware: automatically includes current case and log data in conversation context.
- Multiple provider support: OpenAI (GPT-4, GPT-4o, GPT-3.5-turbo), Google Gemini (Pro, Ultra), Ollama (local, fully offline).
- Provider configuration: API key, model selection, base URL (for Ollama), timeout, max tokens, temperature.
- Capabilities: explain suspicious events, suggest investigation steps, draft incident report text, summarize log findings, answer security domain questions, generate remediation recommendations.
- Conversation export: save AI conversation as part of case evidence.
- Privacy: no log or case data sent to AI providers when using Ollama.

### 7.6 Case Management

- Case lifecycle: Draft → Open → In Investigation → Resolved → Closed.
- Case fields: title, description, severity (Low/Medium/High/Critical), status, assigned analyst, tags, timestamps (created, updated, resolved, closed).
- Evidence management: attach files (logs, screenshots, notes), link IOCs, link AI conversations.
- Comments: threaded comments with @-mentions and timestamps.
- Case timeline: chronological log of all case activity (uploads, comments, status changes).
- Case search: search by title, description, tags, severity, status.
- Case list: sortable, filterable table view with bulk actions.

### 7.7 Reports

- Report types: Incident Report, Investigation Summary, IOC Report, Executive Summary.
- Report structure for Incident Report: title, incident summary, timeline of events, IOCs identified, threat intelligence findings, AI analysis, remediation recommendations, appendices.
- Auto-population: reports pull data from associated case, logs, IOCs, and AI conversations.
- Manual editing: rich text editor for custom report content.
- Export formats: PDF (with formatting, tables, headers), HTML (self-contained, styled), JSON (structured data for programmatic use).
- Report templates: save and reuse custom report templates.

### 7.8 Settings

- General: application theme (light/dark), language, date/time format, log retention policy.
- AI Providers: add/remove/edit provider configurations.
- Threat Intelligence: API key management with test-connection for each service.
- Notifications: configure in-app notification preferences.
- Security: password change, MFA setup, session management.
- Storage: database size display, cache clearance, data export/backup.
- About: version information, license, update channel (stable/beta).

### 7.9 Electron Desktop

- Single-instance lock: launching second instance focuses first.
- Splash screen: branded splash shown during backend startup.
- Startup sequence: launch Python backend process (with retries), health check, load React frontend, create tray icon.
- System tray: minimize to tray, tray notifications, context menu (Show, Quit).
- Window management: configurable window size (default 1280×800), remember position, DevTools docked bottom in dev mode.
- Auto-updater: check for updates on startup, download and install with progress.
- File associations: register `.evtx` file association for "Open with Sentinel."
- Protocol handler: `sentinel://` deep links for future integrations.

### 7.10 Database

- SQLite via SQLAlchemy ORM.
- Single file database stored in user data directory.
- Migration system (Alembic) for schema versioning.
- Tables: users, cases, case_evidence, case_comments, logs, parsed_events, iocs, threat_intel_cache, ai_conversations, settings, notifications.
- Foreign key relationships: logs → parsed_events, cases → evidence/comments/IOCs, IOCs → threat_intel_cache.
- Indexes on: user email (unique), case status, log upload timestamp, event timestamp, IOC value, threat_intel_cache query.

### 7.11 Notifications

- In-app notification center with unread badge count.
- Notification triggers: case assigned, comment added, IOC match found, threat intel enrichment complete, AI analysis done, report generated.
- Notification types: info, success, warning, error.
- Mark as read, mark all read, dismiss individual notifications.
- Configurable notification preferences per trigger type.

---

## 8. Non-Functional Requirements

### Performance

- Cold startup (backend + frontend load): under 5 seconds on modern hardware.
- Log parsing: process 100 MB of logs in under 30 seconds.
- Timeline generation for 10,000+ events: under 2 seconds.
- Search across 50,000+ events: under 1 second.
- PDF report generation: under 5 seconds for standard reports.
- UI responsiveness: 60 FPS for all standard interactions; no frame drops on scroll or navigation.

### Security

- All passwords hashed with bcrypt (cost factor 12).
- JWT tokens signed with HS256, minimum 256-bit secret.
- Session tokens invalidated on logout and password change.
- API key storage: encrypted at rest using AES-256-GCM.
- SQLite database file: stored with restricted file permissions (owner-only).
- Uploaded files: scanned for malicious content, stored outside web root.
- CORS policies: restricted to localhost origins only.
- Rate limiting on authentication endpoints (5 attempts per minute).
- No hardcoded secrets in source code; all credentials via `.env` or settings UI.

### Reliability

- Graceful handling of AI provider timeouts and failures (fallback messaging).
- SQLite WAL mode for concurrent read access during writes.
- Auto-save case data every 30 seconds to prevent data loss.
- Crash recovery: database integrity check on startup.
- Backend process health monitoring with automatic restart (up to 3 attempts).
- Log rotation for application logs to prevent disk exhaustion.

### Scalability

- Architecture supports up to 5 concurrent users via local network (future).
- SQLite suitable for databases up to 10 GB (estimated 10,000+ cases).
- File storage: designed for hundreds of uploaded log files totaling tens of GB.

### Maintainability

- Modular architecture: routers, services, schemas clearly separated.
- SQLAlchemy ORM for database agnosticism (future PostgreSQL support).
- Alembic migrations for schema evolution.
- Type hints throughout Python and TypeScript codebases.
- Comprehensive error handling with structured logging.
- Single `npm run dev` command for development.

### Accessibility

- Keyboard navigable UI with visible focus indicators.
- WCAG 2.1 AA contrast ratios for all text.
- Screen reader compatible semantic HTML.
- Resizable text without breaking layouts.
- Color-blind safe palette for severity indicators.

### Offline Support

- All core features (log parsing, local case management, IOC extraction, report generation, Ollama AI) work with zero network connectivity.
- External features (VirusTotal, AbuseIPDB, OpenAI, Gemini) clearly marked as online-only.
- Graceful degradation when external services unavailable.
- Cached threat intelligence data available offline.
- Queue enrichment requests for automatic processing when connectivity returns.

### Cross-Platform Readiness

- Backend: cross-platform Python (Windows, macOS, Linux).
- Frontend: cross-platform React (browser-compatible for development).
- Desktop: Electron supports Windows, macOS, Linux.
- Version 1 targets Windows (primary), with macOS and Linux builds planned for Version 2.

---

## 9. MVP Scope (Version 1)

Version 1 delivers a stable, single-user desktop SOC platform for individual analysts running on Windows. It includes all Must-Have features (Section 5.1), in a fully offline-capable configuration. The MVP is production-ready for: individual SOC analysts conducting investigations, cybersecurity students learning investigation workflows, blue team exercises and incident documentation, and threat researchers analyzing log files.

### In scope for V1

- Local authentication with JWT and optional MFA.
- Dashboard with core widgets.
- Log upload and parsing for 7 formats.
- IOC extraction and one-click enrichment.
- AI Copilot with OpenAI, Gemini, and Ollama.
- Case management with evidence and comments.
- Report generation (PDF, HTML, JSON).
- Electron desktop with tray, splash, auto-updater.
- SQLite persistence.
- Local file-based evidence storage.
- Settings UI for all configurable features.
- Dark and light themes.
- First-run setup wizard.

### V1 KPIs

- Startup time < 5 seconds.
- Parse accuracy > 95% on target formats.
- AI response time < 10 seconds for standard queries.
- Empty state handling for every view.
- 100% offline capability for core features.

---

## 10. Out of Scope (Version 1)

The following are intentionally excluded from Version 1, either as future enhancements or because they fall outside Sentinel's product scope:

- **Cloud SIEM / centralized log ingestion** — Sentinel is an investigation tool, not a log aggregation platform.
- **Multi-tenancy / organizational accounts** — Version 1 is single-user; team features deferred to Version 2.
- **Enterprise SSO / SAML / LDAP / OIDC** — Local authentication only in V1.
- **Kubernetes / Docker orchestration deployment** — Desktop-first; container deployment is a future consideration for server editions.
- **Real-time distributed agents / endpoint sensors** — Sentinel analyzes existing log files; it does not generate them.
- **Mobile companion application** — No mobile client planned until platform is mature.
- **Real-time alerting / email/SMS/pager integration** — In-app notifications only in V1.
- **RBAC policy engine / granular permissions beyond Admin/Analyst/Viewer** — Simplified role model in V1.
- **Multi-language / localization** — English only in V1.
- **Public API for external integrations** — Internal API only; public SDK deferred.
- **Plugin marketplace and community registry** — Plugin architecture is planned but V1 does not include full plugin lifecycle management.
- **Automated detection rule execution / alert generation from rules** — Sigma/YARA browsing only in V1; auto-detection deferred.
- **Custom log format parser creation UI** — Users may request format support; custom parser builder deferred.
- **Performance benchmarking / load testing suite** — Not user-facing.
- **Penetration testing / security audit certification** — Deferred to pre-V2 security review.

---

## 11. Success Metrics

### Adoption Metrics

- **Daily Active Users (DAU):** 30% of registered users active daily.
- **Weekly Active Users (WAU):** 60% of registered users active weekly.
- **Case completion rate:** 70% of created cases reach Resolved or Closed status.
- **User retention (30-day):** 50% of new users return within 30 days.

### Performance Metrics

- **P95 startup time:** Under 5 seconds cold start.
- **Log parse success rate:** > 99% of uploads complete parsing without error.
- **Parse accuracy:** > 95% true positive rate for event extraction on supported formats.
- **AI response P95 latency:** Under 10 seconds for standard queries.
- **Report generation P95:** Under 5 seconds for PDF export.
- **Crash-free rate:** > 99.5% of sessions.

### Quality Metrics

- **Upload success rate:** > 98% of uploads succeed without user-facing error.
- **IOC extraction precision:** > 90% of extracted IOCs are valid indicators.
- **AI response relevance:** > 80% user satisfaction rating on AI responses (surveyed).
- **Report completeness:** user-rated completeness score > 4/5.

### Business Metrics

- **Open source adoption:** 1,000+ GitHub stars in first 6 months.
- **Community contributions:** 10+ external contributors within first year.
- **Issue resolution time:** Median time to close community issues under 7 days.

---

## 12. Risks

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Python backend bundling (PyInstaller) fails on complex dependency trees | Delayed Windows releases | Test PyInstaller build in CI; maintain fallback as Python-only execution path |
| Electron app size ballooning with bundled Python runtime | Poor user download experience | Compress Python runtime; offer slim and full download variants |
| Cross-platform Python library compatibility (aiohttp, uvloop on Windows) | Platform-specific bugs | Automated testing on all target platforms; platform-specific code paths |

### Security Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| AI API key leakage via logs or crash reports | Credential exposure | Never log API keys; encrypt at rest; clear on settings export |
| Malicious log file exploits (zip bombs, parser vulnerabilities) | Denial of service, RCE | File size limits, parse timeout, sandboxed parsing in subprocess |
| Local SQLite injection | Data exfiltration | Parameterized queries exclusively; no raw SQL construction |
| Electron Chromium vulnerabilities | Full system compromise via renderer | Auto-update Electron; CSP headers; context isolation; node integration off |

### Performance Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Large log files (>500 MB) cause memory exhaustion | App crash | Stream processing for parsing; memory-mapped file I/O; clear size warnings |
| SQLite write contention with concurrent reads | UI blocking for case operations | WAL mode; dedicated write queue; background indexing |
| AI model inference on local hardware (Ollama) | Unacceptable response times | Async streaming responses; show progress indicators; recommend model tier |

### API Dependency Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| VirusTotal/AbuseIPDB rate limits | Blocked enrichment during heavy use | Local caching with TTL; batch with spacing; clear rate-limit warnings |
| AI provider API changes | Broken AI features | Provider abstraction layer; version-pinned API clients; graceful degradation |
| Third-party API downtime | Degraded but non-blocking UX | Cached enrichment results available offline; clear online-only feature labeling |

### Electron Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Auto-updater failure or corrupt update | Users stuck on old versions | Staged rollouts; checksum verification; manual update fallback |
| Backend process not terminating on app quit | Orphan Python processes | Process tree termination; PID file cleanup; watchdog monitoring |
| Native module compilation failures | Broken system tray, notifications, auto-updater | Fallback implementations; graceful degradation; pre-built binaries |

### SQLite Limitations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Concurrent write contention | Slow case/evidence writes under heavy use | WAL mode; queued writes; single-worker backend |
| 10+ GB database performance degradation | Slow search and report generation | Database maintenance tool; archive old cases; export/import for archival |
| No built-in replication | Single point of failure for data | Backup/restore UI; manual database export; documentation on file-based backup |

---

## 13. Future Roadmap

### Version 2 — Team & Depth

**Focus:** Multi-user collaboration, deeper analysis, and macOS/Linux support.

- Multi-user case collaboration with sync layer.
- macOS native build (Apple Silicon + Intel).
- Linux build (.deb, .rpm, AppImage).
- MITRE ATT&CK mapping engine.
- Timeline visualization with attack path highlighting.
- Sigma and YARA rule browsing and application.
- Notification center with in-app and optional desktop notifications.
- Advanced search with saved searches and filters.
- Tagging system across all entities.
- Dashboard customization with configurable widgets.
- Public API (REST) for external integrations.
- Database maintenance tools (archive, export, compact).

### Version 3 — Extensibility & Intelligence

**Focus:** Plugin ecosystem, AI automation, and community platform.

- Plugin system with SDK for community parsers, enrichment providers, and export formats.
- AI automation workflows: configure pipelines (upload → parse → enrich → notify).
- Plugin marketplace in-app browsing and installation.
- Scheduled scans for directories and periodic enrichment.
- AI agent mode: autonomous investigation with human-in-the-loop approval.
- Asset inventory extracted from logs.
- Custom report template builder.
- Advanced analytics: detection coverage metrics, investigation trends.
- Integration marketplace: first-party and community connector library.

### Enterprise Edition

**Focus:** Organizations needing compliance, audit, and centralized management.

- PostgreSQL database support (replaces SQLite).
- Centralized user management with LDAP/SAML/OIDC SSO.
- Audit logging for all user actions.
- Role-based access control with granular permissions.
- Encrypted database at rest.
- Compliance report templates (NIST, ISO 27001, PCI DSS, GDPR).
- Air-gapped deployment support with manual intelligence updates.
- Dedicated support and SLA.
- On-premise deployment without Electron (browser-only frontend).

### Cloud Edition

**Focus:** Teams that want managed infrastructure.

- Managed cloud backend with team workspaces.
- Optional encrypted cloud sync for cases.
- Shared threat intelligence cache across team.
- Web-based frontend (no Electron required).
- Usage-based pricing for AI and threat intel features.
- SOC-as-a-Service optional offering with managed analysts.

### Community Edition

**Focus:** Free, open-core, forever.

- All Version 1 features permanently free.
- Community plugin access (subject to compatibility).
- Basic AI support (Ollama always free, external providers require own keys).
- Community support via GitHub Discussions.
- MIT licensed core.

---

## 14. Competitive Positioning

| Feature | Sentinel | Splunk | Elastic Security | Wazuh | Security Onion | CrowdStrike Falcon | Microsoft Defender XDR |
|---------|----------|--------|-----------------|-------|----------------|-------------------|----------------------|
| **Pricing** | Free / Open Core | $$$$ per GB ingested | $$ per GB + subscription | Free | Free | $$$$ per endpoint | $$$ bundled with E5 |
| **Deployment** | Desktop app | Server cluster | Server cluster | Server | Server / Appliance | Cloud SaaS | Cloud SaaS |
| **Offline Capable** | Full core | No | No | Partial | No | No | No |
| **Log Analysis** | Investigation depth | Ingestion breadth | Ingestion + detection | File integrity + SIEM | Full detection pipeline | Endpoint only | Endpoint + identity |
| **AI Assistant** | Native, multi-provider | AI add-on ($$$) | AI add-on ($$$) | None | None | Charlotte AI ($$$) | Copilot for Security ($$$) |
| **Threat Intel** | Built-in enrichment | TA add-on ($$$) | Built-in ($$) | Built-in | Built-in | Built-in | Built-in |
| **Case Management** | Built-in | Add-on ($$$) | Cases ($$$) | Add-on | Add-on | Built-in | Built-in |
| **Reporting** | Built-in, multi-format | Add-on ($$$) | Built-in ($$) | Built-in | Built-in | Built-in | Built-in |
| **Learning Curve** | Low (desktop app) | High (SPL, infra) | Medium (ES query) | Medium | High | Medium | Medium |
| **Install Time** | Minutes | Hours to days | Hours | Hours | Hours | Instant (cloud) | Instant (cloud) |
| **Multi-User** | V2 (planned) | Yes | Yes | Yes | Yes | Yes | Yes |
| **Windows Focus** | Primary | Cross-platform | Cross-platform | Cross-platform | Linux-focused | Cross-platform | Windows-preferred |

### Where Sentinel Wins

- **Zero cost barrier.** A student or solo consultant can run the same tool as a five-person team without licensing negotiations.
- **True offline capability.** Sentinel works on a plane, in a SCIF, or on a compromised network where outbound connections are blocked. No other platform offers this.
- **Minute-to-value.** Install to first IOC enrichment in under 5 minutes. No cluster setup, no data pipeline configuration, no index tuning.
- **AI-native architecture.** AI is not a bolt-on upsell. It is built into every investigation workflow from day one.
- **Desktop experience.** Analysts work on laptops. Sentinel is designed for a laptop-first workflow with native file system access, system tray integration, and offline resilience.

### Where Sentinel is Intentionally Simpler

- **No agent management.** Sentinel does not deploy and manage 10,000 endpoint sensors. If you need EDR, pair it with CrowdStrike and import the logs.
- **No real-time alerting pipeline.** Sentinel is for investigation, not triage. It reconciles what happened and what to do about it. Pair it with Wazuh or Elastic for alert generation and import findings for deep investigation.
- **No compliance data lake.** Sentinel stores evidence, not every packet and event. If you need 12-month retention of all network flows for PCI DSS, keep your Splunk cluster. Export relevant findings to Sentinel for investigation.
- **No multi-tenant SaaS.** Version 1 is single-user local. Teams should use V2 or Enterprise Edition.

---

## 15. Product Summary

### Executive Summary

Sentinel is a free, open-core, AI-powered desktop SOC platform purpose-built for cybersecurity analysts who need enterprise-grade investigation capabilities without enterprise cost or complexity.

The cybersecurity industry has a gap. At the top, Splunk, CrowdStrike, and Microsoft offer powerful platforms that require six-figure budgets, dedicated infrastructure, and specialized engineering support. At the bottom, analysts use a patchwork of free tools, browser tabs, and manual processes that are slow, error-prone, and exhausting.

Sentinel fills the middle — a professional investigation platform that runs on a laptop, works offline, costs nothing, and delivers AI-assisted analysis, threat intelligence enrichment, case management, and report generation in a single desktop application.

### Target Audience

- Individual SOC analysts who want a dedicated investigation tool.
- Students learning cybersecurity who cannot access enterprise platforms.
- Blue teams who need investigation documentation without infrastructure overhead.
- Small security teams who need a force multiplier.
- Researchers and threat hunters who want reproducible investigation workflows.

### Value Proposition

**For analysts:** One tool for log analysis, IOC enrichment, AI investigation, case management, and reporting. Stop context-switching. Finish investigations in half the time.

**For teams:** Enterprise-grade investigation capabilities at zero licensing cost. Deploy in minutes, not days. No infrastructure to manage.

**For students:** A real SOC platform to learn investigation workflows. AI assistance that explains findings and teaches as you work.

### Long-Term Vision

Sentinel evolves from a powerful desktop tool into an extensible investigation ecosystem. Community plugins, AI agent workflows, and optional cloud sync for teams extend the platform without compromising its core principle: a free, local-first, privacy-respecting SOC platform that belongs to the analyst, not the vendor.

Version 1 delivers the foundation — a stable, feature-rich desktop application that transforms how individual analysts investigate security incidents. Version 2 adds team collaboration and deeper analysis. Version 3 unlocks the community ecosystem. The enterprise edition serves organizations that need compliance, audit, and centralized management.

Sentinel will not become a cloud platform that holds your data hostage. It will not add agents to your endpoints. It will not charge per GB of logs ingested. It will always be free to download, run offline, and use for real investigations.

**Sentinel: The SOC platform that works where you work.**
