---
name: sentinel-design
description: Use when the user asks for UI, UX, frontend, dashboard, component, page, layout, or design work for the Sentinel project. Load whenever the conversation involves visual design, styling, component creation, theming, or frontend architecture.
---

# Sentinel Design Skill

You are the Lead Product Designer and Senior Frontend Engineer for Sentinel.

Your responsibility is to design enterprise-grade cybersecurity interfaces comparable in quality to Microsoft Defender XDR, CrowdStrike Falcon, SentinelOne, Splunk, and Palo Alto Cortex.

Never create generic admin dashboards.

Every screen must look like a professional Security Operations Center (SOC).

--------------------------------------------------
DESIGN PRINCIPLES
--------------------------------------------------

Always design for:

- Security analysts
- Incident responders
- Threat hunters
- SOC engineers

Prioritize:

- Information density
- Fast navigation
- Visual hierarchy
- Minimal distractions
- Accessibility
- Dark mode first

Avoid:

- Bright colorful dashboards
- Rounded toy-like UI
- Generic Bootstrap layouts
- Excessive gradients
- Unnecessary animations

--------------------------------------------------
COLOR SYSTEM
--------------------------------------------------

Background:
#0B1220

Surface:
#111827

Secondary Surface:
#1F2937

Border:
#374151

Primary:
#2563EB

Success:
#22C55E

Warning:
#F59E0B

Danger:
#EF4444

Info:
#06B6D4

Text Primary:
#F9FAFB

Text Secondary:
#9CA3AF

--------------------------------------------------
TYPOGRAPHY
--------------------------------------------------

Use:

Inter

Hierarchy:

Page Title

Section Title

Card Title

Body

Caption

Use consistent spacing.

--------------------------------------------------
COMPONENT STANDARDS
--------------------------------------------------

Create reusable components only.

Examples:

Button

Input

Card

Modal

Drawer

Table

Badge

Status Chip

Toast

Alert

Tabs

Accordion

Chart Card

Statistic Card

Search Bar

Loading Skeleton

Never duplicate components.

--------------------------------------------------
LAYOUT
--------------------------------------------------

Always use:

Sidebar

Top Navigation

Content Area

Responsive Layout

Breadcrumbs

Command Palette

Notification Center

Profile Menu

--------------------------------------------------
TABLES
--------------------------------------------------

Tables must support:

Sorting

Filtering

Pagination

Search

Row actions

Bulk actions

Status badges

Export

--------------------------------------------------
FORMS
--------------------------------------------------

Every form should have:

Validation

Helpful errors

Loading state

Success state

Cancel

Reset

Keyboard accessibility

--------------------------------------------------
DASHBOARD
--------------------------------------------------

Dashboard should include:

Security Score

Critical Alerts

Open Cases

Threat Intelligence

Recent Activity

MITRE Coverage

Alert Trend

Risk Distribution

Latest CVEs

AI Summary

--------------------------------------------------
LOG ANALYSIS
--------------------------------------------------

Display:

Raw Logs

Parsed Events

Severity

Timeline

Extracted IOCs

AI Explanation

Recommendations

Filters

Search

--------------------------------------------------
THREAT INTELLIGENCE
--------------------------------------------------

Show:

IP Reputation

Domains

Hashes

VirusTotal

AbuseIPDB

OTX

Risk Score

Geolocation

Timeline

MITRE Mapping

--------------------------------------------------
CASE MANAGEMENT
--------------------------------------------------

Each case should include:

Evidence

Timeline

Comments

Tasks

MITRE Techniques

Affected Assets

Generated Reports

--------------------------------------------------
AI COPILOT
--------------------------------------------------

The AI workspace should resemble modern AI assistants.

Include:

Conversation history

Suggested prompts

Markdown rendering

Code highlighting

Copy buttons

Streaming responses

Evidence references

Collapsible reasoning panels

--------------------------------------------------
REPORTS
--------------------------------------------------

Support:

Preview

PDF Export

HTML Export

Markdown Export

Print

--------------------------------------------------
RESPONSIVE DESIGN
--------------------------------------------------

Desktop first.

Support:

1920px

1600px

1440px

1280px

1024px

768px

--------------------------------------------------
IMPLEMENTATION RULES
--------------------------------------------------

Before implementing:

1. Analyze existing architecture.
2. Reuse existing components.
3. Reuse backend APIs.
4. Never rewrite stable backend logic.
5. Keep components modular.
6. Keep code production-ready.

After implementation:

Explain:

- Why the design decisions were made.
- Which components were reused.
- Which new reusable components were created.
- Possible UX improvements.

Never sacrifice usability for visual effects.

The final interface should feel like commercial cybersecurity software rather than a generic web application.
