# Sentinel — AI-Powered Security Operations Platform

Sentinel is an AI-assisted cybersecurity platform designed to help security analysts investigate incidents, analyze logs, enrich Indicators of Compromise (IOCs), manage investigations, and generate incident reports from a single interface.

The project combines FastAPI, React, Electron, AI-powered analysis, threat intelligence integrations, detection rules, and case management into a modern Security Operations Center (SOC) workflow.

---

## Features

### Authentication
- JWT Authentication
- Role-Based Access Control (RBAC)
- Multi-Factor Authentication (TOTP)
- Organization Support
- API Usage Tracking

### Log Analysis
Supports Windows Event Logs, Syslog, Apache Logs, Nginx Logs, JSON Logs, CSV Logs, XML Logs.

Capabilities: log parsing, event extraction, timeline generation, brute-force detection, suspicious PowerShell detection, privilege escalation indicators, attack chain reconstruction.

### Threat Intelligence
- IOC Extraction
- VirusTotal Integration
- AbuseIPDB Integration
- AlienVault OTX Integration
- NVD CVE Lookup
- CISA KEV Feed
- IOC Correlation
- Threat Feed Aggregation

### AI Investigation Assistant
- AI Chat
- Log Investigation
- Security Event Explanation
- Timeline Analysis
- Incident Recommendations
- Report Assistance
- Context-Aware Conversations

### Case Management
- Investigation Cases
- Evidence Management
- Comments & Notes
- Investigation Timeline
- Report Generation (PDF / HTML / JSON Export)

### Detection Engineering
- Sigma Rules
- YARA Rules
- Custom Detection Rules
- Threat Hunting
- Rule Testing
- Workflow Playbooks

### Dashboard
- Security Overview
- Alert Center
- Risk Score
- Asset Management
- Notifications
- Threat Statistics
- User Activity

### Enterprise Features
- SIEM Integrations
- EDR Integrations
- Cloud Integrations
- Backup & Restore
- API Metrics

---

## Technology Stack

| Layer | Technologies |
|-------|-------------|
| Backend | FastAPI, SQLAlchemy, SQLite, JWT, Pydantic |
| Frontend | React, TypeScript, Vite, Tailwind CSS, TanStack Query |
| Desktop | Electron, electron-builder |
| AI | OpenAI, Anthropic, Gemini, Ollama, LM Studio |
| Security | Sigma, YARA, VirusTotal, AbuseIPDB, AlienVault OTX, NVD, CISA KEV |
| DevOps | Docker, Docker Compose, GitHub Actions |

---

## Development Workflow

```
Develop
    ↓
Electron Dev Mode   ←  npm run dev
    ↓
Commit
    ↓
Package             ←  npm run package
    ↓
Test Installer
    ↓
Release
```

**Always develop in Electron Dev Mode.** Do not run the packaged installer during development. The dev mode gives you hot reload, live error feedback, and full console output.

---

## Quick Start

### Prerequisites
- **Node.js** 20+
- **Python** 3.12+ (with `.venv` virtual environment)
- **npm** dependencies installed

### One-Command Dev

```bash
npm run dev
```

This single command starts everything:

| Service    | Technology         | Hot Reload                |
|------------|--------------------|---------------------------|
| Backend    | FastAPI (uvicorn)  | `--reload` (save .py)     |
| Frontend   | React (Vite)       | HMR (save .tsx/.ts)       |
| Electron   | TSC watch + reload | Auto-restart (save .ts)   |

All output appears in **one terminal** with color-coded prefixes.

### Manual Dev (per-service)

```bash
# Backend only
python -m uvicorn src.api:app --reload --host 127.0.0.1 --port 8000

# Frontend only (another terminal)
cd frontend && npm run dev

# Electron only (after backend + frontend are running)
cd electron && npm run watch   # compile TypeScript
cd electron && npx electron .  # launch Electron
```

---

### Docker

```bash
docker compose up --build
```

---

### Packaging (for release)

Build the production installer:

```bash
npm run package
```

This runs the full pipeline:
1. **Clean** — removes all previous build artifacts
2. **Frontend** — builds React + Vite into `frontend/dist/`
3. **Electron** — compiles TypeScript into `electron/dist/`
4. **Backend** — bundles Python into a standalone EXE (PyInstaller)
5. **electron-builder** — creates `Sentinel Setup.exe` and `Sentinel Portable.exe`

Output: `electron/release/`

---

## Project Structure

```
sentinel/
├── frontend/           # React + Vite (UI)
│   ├── src/
│   │   ├── api/        # API client (centralized base URL)
│   │   ├── components/ # Shared UI components
│   │   ├── pages/      # Route pages
│   │   └── hooks/      # React hooks (useElectron, etc.)
│   └── vite.config.ts
├── electron/           # Electron shell (desktop wrapper)
│   ├── src/
│   │   ├── main.ts     # App entry point + IPC handlers
│   │   ├── startup.ts  # Startup orchestration (splash → backend → frontend)
│   │   ├── backend.ts  # Backend process manager
│   │   ├── window.ts   # Window creation + lifecycle
│   │   ├── tray.ts     # System tray
│   │   └── updater.ts  # Auto-updater
│   └── package.json    # electron-builder config
├── src/                # Python FastAPI backend
│   ├── api.py          # FastAPI app
│   ├── config.py       # Settings
│   ├── database.py     # SQLite
│   ├── routers/        # API routes
│   └── services/       # Business logic
├── scripts/
│   ├── dev.js          # One-command dev orchestrator
│   ├── dev.ps1         # PowerShell dev (legacy)
│   └── package.ps1     # Packaging pipeline
└── package.json        # Root scripts
```

---

## Scripts Reference

| Command              | Description                                   |
|----------------------|-----------------------------------------------|
| `npm run dev`        | Start all services in dev mode (one terminal) |
| `npm run dev:legacy` | Start dev mode via PowerShell (separate windows) |
| `npm run build`      | Build frontend + Electron TypeScript          |
| `npm run build:backend` | Build backend PyInstaller EXE              |
| `npm run package`    | Full production packaging pipeline            |
| `npm run clean`      | Remove all build artifacts                    |

---

## Architecture Notes

### Single Instance
Sentinel uses `app.requestSingleInstanceLock()`. Launching a second instance focuses the existing window.

### Startup Sequence
1. Splash screen displayed immediately
2. Backend process started (with retries)
3. Health check (`/api/v1/health`) confirms backend is ready
4. React frontend loaded into the window
5. System tray created

If the backend fails to start after 3 attempts, an error screen is displayed and the app exits.

### API URL
All frontend API requests use a centralized `API_BASE_URL` from `frontend/src/api/config.ts`. It auto-detects:
- **Electron (file://)**: `http://127.0.0.1:8000/api/v1`
- **Browser (Vite/nginx)**: `/api/v1` (relative — proxy handles routing)

### Database
SQLite is used for all persistence. The backend uses 1 worker (SQLite cannot handle concurrent writes from multiple processes).

---

## Roadmap

### Version 1
- Authentication
- Log Analysis
- Threat Intelligence
- AI Investigation
- Case Management
- Detection Rules
- Dashboard
- Reports

### Version 2
- Professional SOC Interface
- Desktop Application (Electron)
- Native File Explorer Integration
- SQLite Local Storage
- MITRE ATT&CK Explorer
- Interactive IOC Graph
- Enhanced AI Copilot

### Version 3
- PCAP Analysis
- Malware Static Analysis
- Memory Forensics
- Local AI Models
- Plugin Marketplace
- Detection Coverage Analytics

---

## License

MIT License

---

## Author

**Shivam Singh**

---

## Disclaimer

Sentinel is intended for cybersecurity research, education, and defensive security operations. Users are responsible for complying with all applicable laws and regulations when using external threat intelligence services or analyzing security data.
