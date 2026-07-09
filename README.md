# Sentinel

> AI-Powered Security Operations Platform

Sentinel is an AI-assisted cybersecurity platform designed to help security analysts investigate incidents, analyze logs, enrich Indicators of Compromise (IOCs), manage investigations, and generate incident reports from a single interface.

The project combines FastAPI, React, AI-powered analysis, threat intelligence integrations, detection rules, and case management into a modern Security Operations Center (SOC) workflow.

---

## Version

Current Release: **Sentinel v1.0**

Status:

- Backend: Stable
- Frontend: In Development
- Desktop Version: Planned (Version 2)

---

# Features

## Authentication

- JWT Authentication
- Role-Based Access Control (RBAC)
- Multi-Factor Authentication (TOTP)
- Organization Support
- API Usage Tracking

---

## Log Analysis

Supports:

- Windows Event Logs
- Syslog
- Apache Logs
- Nginx Logs
- JSON Logs
- CSV Logs
- XML Logs

Capabilities:

- Log parsing
- Event extraction
- Timeline generation
- Brute-force detection
- Suspicious PowerShell detection
- Privilege escalation indicators
- Attack chain reconstruction

---

## Threat Intelligence

- IOC Extraction
- VirusTotal Integration
- AbuseIPDB Integration
- AlienVault OTX Integration
- NVD CVE Lookup
- CISA KEV Feed
- IOC Correlation
- Threat Feed Aggregation

---

## AI Investigation Assistant

- AI Chat
- Log Investigation
- Security Event Explanation
- Timeline Analysis
- Incident Recommendations
- Report Assistance
- Context-Aware Conversations

---

## Case Management

- Investigation Cases
- Evidence Management
- Comments & Notes
- Investigation Timeline
- Report Generation
- PDF / HTML / JSON Export

---

## Detection Engineering

- Sigma Rules
- YARA Rules
- Custom Detection Rules
- Threat Hunting
- Rule Testing
- Workflow Playbooks

---

## Dashboard

- Security Overview
- Alert Center
- Risk Score
- Asset Management
- Notifications
- Threat Statistics
- User Activity

---

## Enterprise Features

- SIEM Integrations
- EDR Integrations
- Cloud Integrations
- Backup & Restore
- API Metrics

---

# Technology Stack

## Backend

- FastAPI
- SQLAlchemy
- SQLite
- JWT Authentication
- Pydantic

## Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- TanStack Query

## AI

- OpenAI
- Local AI Fallback

## Security

- Sigma
- YARA
- VirusTotal
- AbuseIPDB
- AlienVault OTX
- NVD
- CISA KEV

## DevOps

- Docker
- Docker Compose
- GitHub Actions

---

# Project Structure

```
Sentinel/

├── frontend/
├── src/
├── tests/
├── deploy/
├── docs/
├── data/
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

# Quick Start

## Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/Sentinel.git

cd Sentinel
```

---

## Backend

```bash
python -m venv .venv

source .venv/bin/activate
# Windows
.venv\Scripts\activate

python -m pip install -r requirements.txt

uvicorn src.api:app --reload
```

---

## Frontend

```bash
cd frontend

npm install

npm run dev
```

---

## Run Tests

```bash
pytest
```

---

## Docker

```bash
docker compose up --build
```

---

# Roadmap

## Version 1

- Authentication
- Log Analysis
- Threat Intelligence
- AI Investigation
- Case Management
- Detection Rules
- Dashboard
- Reports

---

## Version 2

- Professional SOC Interface
- Desktop Application (Electron)
- Native File Explorer Integration
- SQLite Local Storage
- MITRE ATT&CK Explorer
- Interactive IOC Graph
- Enhanced AI Copilot

---

## Version 3

- PCAP Analysis
- Malware Static Analysis
- Memory Forensics
- Local AI Models
- Plugin Marketplace
- Detection Coverage Analytics

---

# Screenshots

Coming Soon

- Dashboard
- Log Analysis
- Threat Intelligence
- AI Investigation
- Case Management

---

# License

MIT License

---

# Author

**Shivam Singh**

---

# Disclaimer

Sentinel is intended for cybersecurity research, education, and defensive security operations. Users are responsible for complying with all applicable laws and regulations when using external threat intelligence services or analyzing security data.
