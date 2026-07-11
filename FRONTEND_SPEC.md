# Sentinel — Frontend Specification Document

**Version:** 1.0
**Author:** Design System & Frontend Architecture
**Target Audience:** Designers, Frontend Engineers, AI Coding Tools

---

## 1. Design Philosophy

### Product Personality

Sentinel is precise, powerful, and trustworthy. It communicates competence without noise. Every visual element serves the analyst's goal: understanding an incident and acting on it. The personality is:

- **Professional** — enterprise-grade fit and finish
- **Calm under pressure** — information-dense without visual clutter
- **Authoritative** — clear hierarchy, confident color use
- **Assistive** — AI features feel helpful, not intrusive

### Visual Style

The design follows a **functional cyberpunk** aesthetic — dark-first, high-contrast, with subtle glow accents on interactive elements. Think Bloomberg Terminal meets modern SaaS:

- Dark backgrounds with controlled color accents
- Glass morphism for overlays and dialogs (subtle backdrop blur)
- Monochromatic base with strategic color for meaning only
- Flat surfaces with very subtle elevation via outer shadows
- No skeuomorphism, no gradients for decoration

### UX Principles

| Principle | Description |
|-----------|-------------|
| **Progressive disclosure** | Show the essential, reveal complexity on demand |
| **Direct manipulation** | Drag-and-drop upload, click-to-enrich, inline editing |
| **Keyboard-first** | Every action reachable without a mouse |
| **State visibility** | Clear loading, empty, error, and success states for every operation |
| **Forgiving input** | Accept logs in any reasonable format; autocorrect where possible |
| **Undo-friendly** | Bulk actions require confirmation; deleted items go to trash (V2) |

### Design Goals

- Analyst can triage an incident within 60 seconds of opening the app
- Critical information (severity, status, timestamps) is scannable at a glance
- Complex workflows (upload → parse → enrich → report) are 3 clicks or fewer
- Every interactive element has a clear affordance

### Accessibility Goals

- WCAG 2.2 AA compliance minimum
- WCAG 2.2 AAA for text contrast (7:1 for body text)
- Full keyboard navigation with visible focus rings
- Screen reader announcements for dynamic content changes
- Color is never the sole differentiator

### Desktop-First Approach

- Minimum window size: 1024×768
- Target window size: 1440×900
- Designed for mouse + keyboard input
- Touch support for trackpad gestures (scroll, pinch zoom on charts)
- No mobile-first considerations beyond Electron window resizing

### Dark Mode Philosophy

Dark mode is the **default and primary theme**. Light mode is a secondary consideration (no warm tones, cool grays only):

- Background: near-black (#0D1117) to deep gray (#161B22)
- Surfaces: layered dark grays to create depth without shadows
- Text: bright white (#F0F6FC) for primary, muted gray (#8B949E) for secondary
- Accents: saturated colors that glow subtly against dark backgrounds
- Consistency: no light-mode-only features; light theme is a palette swap

---

## 2. Design System

### Color Palette

#### Primary — Cyber Blue

| Token | HEX | Usage |
|-------|-----|-------|
| `--color-primary-50` | `#EBF5FF` | Background tint |
| `--color-primary-100` | `#C7E2FF` | Hover background |
| `--color-primary-200` | `#94C5FF` | Active background |
| `--color-primary-300` | `#5BA0FF` | Link text, icon |
| `--color-primary-400` | `#3580F0` | Button default |
| `--color-primary-500` | `#1F6FEB` | Primary brand color |
| `--color-primary-600` | `#1558C7` | Button hover |
| `--color-primary-700` | `#0D4196` | Button pressed |
| `--color-primary-800` | `#0A2D6B` | Disabled button bg |
| `--color-primary-900` | `#051B40` | Subtle background |

#### Secondary — Emerald

| Token | HEX | Usage |
|-------|-----|-------|
| `--color-secondary-50` | `#E6F9EE` | Success badge bg |
| `--color-secondary-400` | `#3FB950` | Success text, online status |
| `--color-secondary-500` | `#2EA043` | Success border |
| `--color-secondary-600` | `#238636` | Success button |

#### Accent — Amber

| Token | HEX | Usage |
|-------|-----|-------|
| `--color-accent-50` | `#FFF8EB` | Warning badge bg |
| `--color-accent-400` | `#D29922` | Warning text |
| `--color-accent-500` | `#BB8009` | Warning border |
| `--color-accent-600` | `#9E6A03` | Warning button |

#### Danger — Red

| Token | HEX | Usage |
|-------|-----|-------|
| `--color-danger-50` | `#FFEBED` | Critical badge bg |
| `--color-danger-400` | `#F85149` | Danger text, error icon |
| `--color-danger-500` | `#DA3633` | Danger border |
| `--color-danger-600` | `#B6231C` | Danger button |

#### Info — Purple

| Token | HEX | Usage |
|-------|-----|-------|
| `--color-info-50` | `#F0E8FF` | Info badge bg |
| `--color-info-400` | `#A371F7` | Info text |
| `--color-info-500` | `#8957E5` | Info border |
| `--color-info-600` | `#6E40C9` | Info accent |

#### Backgrounds (Dark Theme — Default)

| Token | HEX | Usage |
|-------|-----|-------|
| `--bg-primary` | `#0D1117` | Main application background |
| `--bg-secondary` | `#161B22` | Sidebar, cards, panels |
| `--bg-tertiary` | `#21262D` | Input fields, hover rows |
| `--bg-elevated` | `#1C2128` | Modals, dialogs, dropdowns |
| `--bg-overlay` | `rgba(1,4,9,0.8)` | Modal backdrop |

#### Backgrounds (Light Theme)

| Token | HEX | Usage |
|-------|-----|-------|
| `--bg-primary` | `#FFFFFF` | Main application background |
| `--bg-secondary` | `#F6F8FA` | Sidebar, cards, panels |
| `--bg-tertiary` | `#EDEFF2` | Input fields, hover rows |
| `--bg-elevated` | `#FFFFFF` | Modals, dialogs, dropdowns |
| `--bg-overlay` | `rgba(27,31,36,0.5)` | Modal backdrop |

#### Surfaces

| Token | HEX | Usage |
|-------|-----|-------|
| `--surface-card` | `#161B22` | Card background |
| `--surface-card-hover` | `#1C2128` | Card hover state |
| `--surface-modal` | `#1C2128` | Modal/sheet background |
| `--surface-tooltip` | `#21262D` | Tooltip background |
| `--surface-code` | `#0D1117` | Code block background |

#### Borders

| Token | HEX | Usage |
|-------|-----|-------|
| `--border-default` | `#30363D` | Default border |
| `--border-muted` | `#21262D` | Subtle divider |
| `--border-accent` | `#1F6FEB` | Focus ring, active tab |
| `--border-danger` | `#DA3633` | Error border |

#### Text

| Token | HEX | Usage |
|-------|-----|-------|
| `--text-primary` | `#F0F6FC` | Primary body text |
| `--text-secondary` | `#8B949E` | Secondary / caption text |
| `--text-tertiary` | `#6E7681` | Placeholder, disabled |
| `--text-link` | `#58A6FF` | Hyperlinks |
| `--text-inverse` | `#0D1117` | Text on brand backgrounds |
| `--text-danger` | `#F85149` | Error messages |
| `--text-success` | `#3FB950` | Success messages |

### Interactive States

| State | Pattern |
|-------|---------|
| **Default** | Base color per component |
| **Hover** | `filter: brightness(1.15)` for dark, `brightness(0.92)` for light |
| **Active/Pressed** | `filter: brightness(0.85)` for dark, `brightness(0.85)` for light |
| **Disabled** | Opacity 0.4, cursor not-allowed |
| **Focus** | `box-shadow: 0 0 0 3px var(--color-primary-500)` with `outline: none` |
| **Selected** | Background tint + accent border left (sidebar items) |

---

## 3. Typography

### Font Family

```css
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'Consolas', monospace;
```

### Type Scale

| Token | Size | Weight | Line Height | Letter Spacing | Usage |
|-------|------|--------|-------------|----------------|-------|
| `--text-display` | 32px / 2rem | 700 | 1.2 | -0.02em | Page titles |
| `--text-h1` | 24px / 1.5rem | 600 | 1.3 | -0.015em | Section headers |
| `--text-h2` | 20px / 1.25rem | 600 | 1.35 | -0.01em | Card/panel titles |
| `--text-h3` | 16px / 1rem | 600 | 1.4 | 0 | Subsection titles |
| `--text-body` | 14px / 0.875rem | 400 | 1.5 | 0 | Body text |
| `--text-body-bold` | 14px / 0.875rem | 600 | 1.5 | 0 | Emphasized body |
| `--text-small` | 12px / 0.75rem | 400 | 1.5 | 0.01em | Captions, timestamps |
| `--text-small-bold` | 12px / 0.75rem | 600 | 1.5 | 0.01em | Labels, badges |
| `--text-micro` | 11px / 0.6875rem | 500 | 1.4 | 0.02em | Data in tables, KPI values |
| `--text-code` | 13px / 0.8125rem | 400 | 1.6 | 0 | Monospace code |
| `--text-button` | 14px / 0.875rem | 500 | 1 | 0.01em | Button labels |
| `--text-input` | 14px / 0.875rem | 400 | 1.5 | 0 | Form inputs |

### Typography Rules

- Maximum line length for body text: 80 characters
- Monospace: all log output, IOC values, code blocks, table data cells
- No text size under 11px (accessibility minimum)
- Headings use tighter letter-spacing for density
- Monospace uses default letter-spacing (0)

---

## 4. Iconography

### Library

**Phosphor Icons** (duotone variant) — chosen for consistent stroke weight, semantic weights (regular/bold/fill), and security-appropriate aesthetic. Fallback: Lucide Icons for any missing icons.

### Icon Sizes

| Token | Size | Usage |
|-------|------|-------|
| `--icon-micro` | 12px | Inline with small text, badges |
| `--icon-small` | 16px | Inline with body text, table cells |
| `--icon-medium` | 20px | Buttons, navigation items |
| `--icon-large` | 24px | Section headers, empty states |
| `--icon-xlarge` | 32px | Feature icons, status illustrations |
| `--icon-xxlarge` | 48px | Empty state hero images |

### Icon Rules

| Category | Style | Color |
|----------|-------|-------|
| **Navigation** | Outline, regular weight | `--text-secondary`, active: `--text-primary` |
| **Status** (passive) | Outline | Semantic color (success/warning/danger/info) |
| **Status** (active) | Fill | Semantic color |
| **Threat severity** | Fill | Critical: danger, High: accent, Medium: warning, Low: secondary |
| **File type** | Outline | `--text-secondary` |
| **MITRE tactics** | Outline | `--text-secondary` |
| **Actions** (clickable) | Outline, regular weight | `--text-secondary`, hover: `--text-primary` |
| **AI / Copilot** | Duotone | Primary + secondary color |

---

## 5. Spacing System

Base unit: 4px

| Token | Value | Usage |
|-------|-------|-------|
| `--space-1` | 4px | Tight icon padding, gap between label and value |
| `--space-2` | 8px | Inline element gaps, icon-right padding |
| `--space-3` | 12px | Input padding, small card padding |
| `--space-4` | 16px | Standard padding (cards, panels, sections) |
| `--space-5` | 20px | Button horizontal padding |
| `--space-6` | 24px | Section spacing, card groups |
| `--space-8` | 32px | Major section spacing, modal padding |
| `--space-10` | 40px | Page section separation |
| `--space-12` | 48px | Page margins, sidebar width |
| `--space-16` | 64px | Large page sections |

### Spacing Rules

- **Card padding:** 16px (--space-4)
- **Page margin:** 24px (--space-6) from window edges
- **Section gap:** 24px (--space-6) between page sections
- **Component gap:** 8px (--space-2) between related form elements
- **Table cell padding:** 8px 12px (--space-2 --space-3)
- **List item spacing:** 4px (--space-1) between dense items, 8px between standard items

---

## 6. Layout System

### Application Shell

```
┌─────────────────────────────────────────────────────┐
│  Title Bar (Electron frameless)                      │
├──────────┬──────────────────────────────────────────┤
│          │  Top Bar                                  │
│  Sidebar │  Breadcrumbs  Search  Notifications  User │
│          ├──────────────────────────────────────────┤
│          │                                          │
│   Nav    │                                          │
│   Items  │         Content Area                      │
│          │         (Scrollable)                      │
│          │                                          │
│          │                                          │
│          │                                          │
├──────────┴──────────────────────────────────────────┤
│  Status Bar (backend health, version, network status) │
└─────────────────────────────────────────────────────┘
```

### Sidebar

| Property | Value |
|----------|-------|
| **Width** | 240px collapsed, 280px expanded |
| **Background** | `--bg-secondary` |
| **Border-right** | `1px solid --border-default` |
| **Collapsible** | Yes (toggle to icon-only, 64px) |

Navigation items:

| Icon | Label | Route | Badge |
|------|-------|-------|-------|
| Gauge | Dashboard | `/dashboard` | — |
| Terminal | Log Analysis | `/logs` | Count pending |
| Shield | Threat Intelligence | `/threat-intel` | Alert count |
| Robot | AI Copilot | `/ai-copilot` | — |
| Folder | Cases | `/cases` | Open case count |
| MagnifyingGlass | Detection Rules | `/detection` | — |
| FileText | Reports | `/reports` | — |
| Gear | Settings | `/settings` | — |

### Top Bar

| Property | Value |
|----------|-------|
| **Height** | 48px |
| **Background** | `--bg-secondary` |
| **Border-bottom** | `1px solid --border-default` |

Left: Breadcrumbs (e.g., Log Analysis > Windows Event Log > Case #1024)
Right: Search (Ctrl+K), Notifications (bell icon + count badge), User avatar + dropdown

### Layout Grid

```
Page Content:
┌──────────────────────────────────────────────────────┐
│  Page Header (title + actions)                       │
│  ─────────────────────────────────────────────────── │
│                                                       │
│  ┌──────┬──────┬──────┬──────┐                       │
│  │ Card │ Card │ Card │ Card │  Statistic row        │
│  └──────┴──────┴──────┴──────┘                       │
│                                                       │
│  ┌────────────────────────────────────────────┐       │
│  │               Main Panel                    │       │
│  │              (Table / Content)              │       │
│  └────────────────────────────────────────────┘       │
│                                                       │
│  ┌──────────────┬─────────────────────────────┐       │
│  │ Side Panel   │ Detail Panel                 │       │
│  │ (Filters)    │ (Item detail)                │       │
│  └──────────────┴─────────────────────────────┘       │
└──────────────────────────────────────────────────────┘
```

### Breakpoints

| Breakpoint | Width | Layout |
|------------|-------|--------|
| Desktop small | 1024×768 | Minimum supported |
| Desktop medium | 1280×800 | Standard laptop |
| Desktop large | 1440×900 | Target design size |
| Desktop xlarge | 1600×900 | Large monitors |
| Desktop xxlarge | 1920×1080 | Full HD+ |
| Electron min | 1024×768 | Minimum window size |

---

## 7. Component Library

### 7.1 Buttons

| Variant | Purpose | Visual |
|---------|---------|--------|
| **Primary** | Main action (Upload, Save, Create) | `--color-primary-500` bg, white text |
| **Secondary** | Alternative action | Transparent bg, `--border-default` border |
| **Ghost** | Low emphasis action (Cancel, Dismiss) | Transparent, text only |
| **Danger** | Destructive action (Delete, Remove) | `--color-danger-500` bg or outline |
| **Icon** | Single-icon action | Square, 32×32, ghost variant |
| **Link** | Inline navigation | Text colored as `--text-link` |

Sizes: Small (28px), Default (32px), Large (40px)
States: Default, Hover, Active, Disabled, Loading (show spinner icon)
Accessibility: Focus ring visible, aria-label for icon-only buttons

### 7.2 Inputs

| Variant | Usage |
|---------|-------|
| **Text** | Single-line text entry |
| **Password** | Password with show/hide toggle |
| **Search** | Search with magnifying glass icon, clear button |
| **Textarea** | Multi-line text (notes, report body) |
| **Number** | Numeric input with increment/decrement |

States: Default, Hover, Focus, Filled, Error (with message), Disabled
Height: 32px default, 28px compact
Accessibility: label for every input, aria-describedby for error messages

### 7.3 Search Bar

- Integrated in top bar (Ctrl+K shortcut)
- Command palette overlay on focus (like VS Code)
- Searches across: cases, logs, IOCs, reports, settings
- Recent searches shown
- Keyboard navigation (arrow keys, enter to select)

### 7.4 Dropdowns & Selects

- Custom rendered (not native `<select>`)
- Options list with scroll (max 8 visible)
- Search filtering for options > 5
- Multi-select with checkboxes and chip display

### 7.5 Checkboxes & Radio Buttons

- Custom styled, minimum 16×16 hit area
- Indeterminate state for checkboxes (partial selection)
- Group orientation: vertical (default) or horizontal

### 7.6 Tables & Data Grids

Specified in Section 10.

### 7.7 Cards

| Variant | Content |
|---------|---------|
| **Statistic** | Icon, label, value, trend arrow |
| **Chart** | Title, chart element, optional legend |
| **Summary** | Thumbnail + title + description + metadata |
| **Log Entry** | Timestamp + severity badge + source + truncated message |

Card elevation: `--surface-card` bg, `1px solid --border-default` border, no shadow.

### 7.8 Badges & Status Chips

| Variant | Example |
|---------|---------|
| **Severity** | Critical, High, Medium, Low, Info |
| **Status** | Open, In Progress, Resolved, Closed |
| **Format** | EVTX, Syslog, JSON, CSV |
| **Source** | VirusTotal, AbuseIPDB, AI |

Colors: semantic (danger for critical, warning for medium, etc.)

### 7.9 Modals

| Variant | Width | Usage |
|---------|-------|-------|
| **Small** | 400px | Confirmations, brief forms |
| **Medium** | 560px | Standard forms |
| **Large** | 720px | Detail views, report preview |
| **Full** | 90vw | Log viewer, AI conversation |

Backdrop: `--bg-overlay` with `backdrop-filter: blur(4px)`
Animation: fade in + scale from 0.95

### 7.10 Drawers

- Slide from right: 400px default, up to 600px
- Used for: case details, IOC details, filter panels
- Backdrop optional (click-outside to close)

### 7.11 Tabs

- Underline-style (active tab has `--border-accent` bottom border)
- Variants: Pill tabs for filter bars
- Wrapped tabs: scrollable if overflow

### 7.12 Toasts

| Variant | Icon | Auto-dismiss |
|---------|------|-------------|
| **Success** | CheckCircle | 4s |
| **Error** | XCircle | 8s |
| **Warning** | Warning | 6s |
| **Info** | Info | 4s |

Position: bottom-right, stacked
Animation: slide in from right

### 7.13 Alerts

- Inline banners, not overlay
- Variants: Success, Warning, Error, Info
- Dismissible (X button)
- Optional action button

### 7.14 Pagination

- Previous / Next buttons
- Page number display ("Page 3 of 12")
- Page size selector (10, 25, 50, 100)
- Total item count

### 7.15 Skeleton Loaders

- Animated shimmer effect (gradient sweep)
- Match exact shape of content being loaded
- Card skeleton: rectangle + 2 lines
- Table skeleton: header row + 5 body rows
- Chart skeleton: rectangle with chart-shaped fill

### 7.16 Empty States

- Illustration (48px icon)
- Title ("No logs uploaded")
- Description ("Upload a log file to begin analysis.")
- CTA button ("Upload Log")
- Optional: link to documentation

### 7.17 Loading Indicators

- **Button:** Inline spinner icon, text remains visible
- **Page:** Full-page centered spinner for initial load
- **Section:** Section-level spinner overlay
- **Inline:** Small spinner for individual item loading

### 7.18 Tooltips

- Show on hover (300ms delay) or focus
- Position: top (default), bottom, left, right
- Max width: 280px
- Rich content support (text + optional icon)

### 7.19 Progress Bars

- Determinate: shows percentage
- Indeterminate: animated stripe for unknown duration
- Variants: Default, Success (green), Error (red)
- Height: 4px (thin), 8px (standard)

---

## 8. Page Specifications

### 8.1 Login Page

```
┌─────────────────────────────────┐
│                                 │
│         [Logo / Sentinel]        │
│                                 │
│         Welcome back             │
│                                 │
│  ┌─────────────────────────┐    │
│  │ Email / Username         │    │
│  ├─────────────────────────┤    │
│  │ Password                 │    │
│  └─────────────────────────┘    │
│                                 │
│  [✓] Remember me                │
│                                 │
│  ┌─────────────────────────┐    │
│  │     Sign In              │    │
│  └─────────────────────────┘    │
│                                 │
│  Need an account? Register      │
│                                 │
│  ────── Or continue with ────── │
│                                 │
│  [Local Account]                │
│                                 │
│  Version 1.0.0                  │
└─────────────────────────────────┘
```

- Centered card on `--bg-primary`, max width 400px
- On first run: redirect to setup wizard (create admin account)
- Error states: invalid credentials shake animation
- MFA: if enabled, second step with TOTP input appears

### 8.2 Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  Dashboard                                     [+ New Case]  │
├──────────────────────────────────────────────────────────────┤
│ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐                │
│ │Open    │ │Logs    │ │IOCs    │ │Alerts  │  Stat cards     │
│ │Cases: 8│ │Today: 3│ │Found:47│ │Active:2│                │
│ │↑ 12%   │ │↓ 5%    │ │↑ 23%   │ │—       │                │
│ └────────┘ └────────┘ └────────┘ └────────┘                │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐    │
│ │  Recent Cases                    [View All →]         │    │
│ │  ┌──────┬──────┬──────┬──────┬──────────┬─────────┐  │    │
│ │  │Case  │Severi│Status│Assign│  Updated │ IOCs    │  │    │
│ │  ├──────┼──────┼──────┼──────┼──────────┼─────────┤  │    │
│ │  │#1024 │HIGH  │Open  │jsmith│ 2m ago   │ 12      │  │    │
│ │  │#1023 │CRIT  │In Pr │adoe  │ 15m ago  │ 8       │  │    │
│ │  │#1022 │MEDIUM│Resolv│jsmith│ 1h ago   │ 4       │  │    │
│ │  └──────┴──────┴──────┴──────┴──────────┴─────────┘  │    │
│ └──────────────────────────────────────────────────────┘    │
│                                                              │
│ ┌────────────────────┐ ┌──────────────────────────────────┐ │
│ │  Threat Summary    │ │  Activity Timeline                │ │
│ │                    │ │                                  │ │
│ │  Malicious: 12     │ │  ⬤ Upload — case #1024 — 2m ago │ │
│ │  Suspicious: 35    │ │  ⬤ AI Analysis — #1023 — 15m    │ │
│ │  Clean: 128        │ │  ⬤ IOC Enrich — #1022 — 1h     │ │
│ │                    │ │  ⬤ Report — #1021 — 3h          │ │
│ └────────────────────┘ └──────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 8.3 Log Analysis

```
┌─────────────────────────────────────────────────────────────┐
│  Log Analysis                                [Upload Logs ▲] │
├──────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────────┐│
│ │  Upload Zone (drag & drop or click to browse)             ││
│ │  Supported: .evtx .log .txt .json .csv .xml .gz          ││
│ │  Max file size: 500 MB                                    ││
│ └──────────────────────────────────────────────────────────┘│
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐│
│ │  Upload History                  [Filter ▼]  [Search]    ││
│ │  ┌───┬──────┬──────┬────┬──────┬──────┬──────┬────────┐ ││
│ │  │  #│ File │Format│Size│Events│ IOCs │Status│ Upload │ ││
│ │  ├───┼──────┼──────┼────┼──────┼──────┼──────┼────────┤ ││
│ │  │ 1 │sec...│EVTX  │12MB│ 3,420│ 47   │Done  │10:32AM │ ││
│ │  │ 2 │sys...│Syslog│2MB │ 180  │ 8    │Parsed│09:15AM │ ││
│ │  │ 3 │apa...│Apache│5MB │ 890  │ 12   │Error │08:00AM │ ││
│ │  └───┴──────┴──────┴────┴──────┴──────┴──────┴────────┘ ││
│ └──────────────────────────────────────────────────────────┘│
│                                                              │
│ Clicking a row opens detail view:                            │
│ ┌──────────────────────────────────────────────────────────┐│
│ │  Log Detail: security.evtx      [Analyze] [Create Case]  ││
│ │  ┌────────────┬───────────────────────────────────────┐  ││
│ │  │ Timeline   │ Event List                             │  ││
│ │  │            │ ┌──────┬──────┬─────────┬──────────┐  │  ││
│ │  │  ═══ Event │ │ Time │ Type │ Source  │ Message  │  │  ││
│ │  │  ═══ burst │ ├──────┼──────┼─────────┼──────────┤  │  ││
│ │  │    │       │ │10:32 │4624  │192.168.1│An acc... │  │  ││
│ │  │    │       │ │10:32 │4624  │192.168.1│An acc... │  │  ││
│ │  │    │       │ │10:33 │4625  │10.0.0.5 │An acc... │  │  ││
│ │  │    ▼       │ └──────┴──────┴─────────┴──────────┘  │  ││
│ │  └────────────┴───────────────────────────────────────┘  ││
│ └──────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 8.4 Threat Intelligence

```
┌─────────────────────────────────────────────────────────────┐
│  Threat Intelligence                        [Add API Key ▲]  │
├──────────────────────────────────────────────────────────────┤
│ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐                │
│ │IOCs    │ │Malicio│ │Clean  │ │Uncheck│                │
│ │Total:47│ │12     │ │30     │ │5      │                │
│ └────────┘ └────────┘ └────────┘ └────────┘                │
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐│
│ │  IOCs                              [Batch Enrich ▼] [↻] ││
│ │  ┌───┬──────────┬──────┬──────┬──────┬────────┬───────┐ ││
│ │  │  #│ Value    │ Type │ Source│Confid│ Last   │ Status│ ││
│ │  ├───┼──────────┼──────┼──────┼──────┼────────┼───────┤ ││
│ │  │ 1 │185.220.1│ IP   │ EVTX │ 85%  │ 2m ago │Done   │ ││
│ │  │ 2 │eicar.or│Domain│ EVTX │ 92%  │ 5m ago │Done   │ ││
│ │  │ 3 │d41d8cd9│MD5   │ Syslg│ —    │ —     │Pending│ ││
│ │  └───┴──────────┴──────┴──────┴──────┴────────┴───────┘ ││
│ └──────────────────────────────────────────────────────────┘│
│                                                              │
│ Clicking IOC opens detail panel:                             │
│ ┌──────────────────────────────────────────────────────────┐│
│ │  185.220.101.168          [Copy] [Case #1024]  [Enrich]  ││
│ │  Type: IPv4 | Source: security.evtx | Case: #1024         ││
│ │                                                           ││
│ │  ┌────────────┬──────────────────────────────────────┐    ││
│ │  │ VirusTotal │ 0/91 detections (clean)              │    ││
│ │  │            │ Last analyzed: 2026-07-10             │    ││
│ │  ├────────────┼──────────────────────────────────────┤    ││
│ │  │ AbuseIPDB  │ ISP: OVH SAS | Country: FR           │    ││
│ │  │            │ Abuse reports: 3 | Confidence: 12%   │    ││
│ │  ├────────────┼──────────────────────────────────────┤    ││
│ │  │ OTX        │ Found in 2 pulses                    │    ││
│ │  └────────────┴──────────────────────────────────────┘    ││
│ └──────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 8.5 AI Copilot

```
┌─────────────────────────────────────────────────────────────┐
│  AI Copilot                                                   │
├──────────────────────────────────────────────────────────────┤
│ ┌────────────┬─────────────────────────────────────────────┐│
│ │            │                                             ││
│ │ History    │  ┌─────────────────────────────────────┐    ││
│ │ (sessions) │  │ AI Assistant                        │    ││
│ │            │  │                                     │    ││
│ │  Today     │  │ Hello! I'm your Sentinel AI         │    ││
│ │  • Case    │  │ assistant. I can help you analyze   │    ││
│ │    #1024   │  │ logs, explain security events,      │    ││
│ │  • Case    │  │ suggest investigation steps, and    │    ││
│ │    #1021   │  │ draft incident reports.             │    ││
│ │            │  │                                     │    ││
│ │  Yesterday │  │ Upload a log file or open an        │    ││
│ │  • Gen     │  │ existing case to get started.       │    ││
│ │    query   │  └─────────────────────────────────────┘    ││
│ │            │                                             ││
│ │            │  ┌─────────────────────────────────────┐    ││
│ │            │  │ Analyze this PowerShell event:     │    ││
│ │            │  │ "powershell -enc SQBFAFgAIAAo..." │    ││
│ │            │  └─────────────────────────────────────┘    ││
│ │            │                                             ││
│ │            │  ┌─────────────────────────────────────┐    ││
│ │            │  │ AI: This is a base64-encoded        │    ││
│ │            │  │ PowerShell command. Decoded:       │    ││
│ │            │  │ IEX (New-Object Net.WebClient)     │    ││
│ │            │  │ .DownloadString('http://...')      │    ││
│ │            │  │ This is commonly used for...       │    ││
│ │            │  │ [Save to Case] [Copy] [Explain More]│    ││
│ │            │  └─────────────────────────────────────┘    ││
│ │            │                                             ││
│ └────────────┴─────────────────────────────────────────────┘│
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Type your question... (Ctrl+Enter to send)    [Send]   ││
│  │  [Attach Context: None ▼]  Provider: GPT-4o ●          ││
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 8.6 Case Management

```
┌─────────────────────────────────────────────────────────────┐
│  Cases                                        [+ New Case ▲] │
├──────────────────────────────────────────────────────────────┤
│ ┌──────┬──────┬──────┬──────┬──────┬──────┐                │
│ │Open  │In Pro│Resolv│Closed│Draft │ALL   │  Filter pills   │
│ └──────┴──────┴──────┴──────┴──────┴──────┘                │
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐│
│ │  Search cases...                          [Filter ▼]     ││
│ │  ┌───┬──────┬──────┬──────┬────┬──────┬──────┬─────────┐││
│ │  │  #│ Title│Severi│Status│IOCs│ Assgn│Updated│ Tags   │││
│ │  ├───┼──────┼──────┼──────┼────┼──────┼──────┼─────────┤││
│ │  │102│Ranse│CRIT │Open  │ 12 │ jsm. │ 2m   │ ransom..│││
│ │  │102│Phish│HIGH │In Pr │ 8  │ adoe │ 15m  │ phish.. │││
│ │  └───┴──────┴──────┴──────┴────┴──────┴──────┴─────────┘││
│ └──────────────────────────────────────────────────────────┘│
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐│
│ │  Case #1024: Ransomware Investigation                    ││
│ │  ┌──────┬──────┬──────┬──────┬───────┬────────────┐    ││
│ │  │Overvi│Timeli│Eviden│IOCs  │AI     │ Report     │    ││
│ │  ├──────┴──────┴──────┴──────┴───────┴────────────┤    ││
│ │  │ Description: ...                                │    ││
│ │  │ Severity: Critical    Status: Open              │    ││
│ │  │ Created: 2026-07-10 10:30  By: jsmith           │    ││
│ │  │ Tags: [ransomware] [powershell] [lateral]       │    ││
│ │  │                                                  │    ││
│ │  │ ┌────────────┬───────────────────────────────┐  │    ││
│ │  │ │ Evidence   │ Add Evidence [+]               │  │    ││
│ │  │ │ 📄 securit│                                 │  │    ││
│ │  │ │ 💬 AI Anal│                                 │  │    ││
│ │  │ └────────────┴───────────────────────────────┘  │    ││
│ │  └──────────────────────────────────────────────────┘    ││
│ └──────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 8.7 Detection Rules (Sigma / YARA)

```
┌─────────────────────────────────────────────────────────────┐
│  Detection Rules                         [Browse Rules ▲]   │
├──────────────────────────────────────────────────────────────┤
│ ┌──────────┬──────────┐                                     │
│ │  Sigma   │  YARA    │  Tabs                                 │
│ └──────────┴──────────┘                                     │
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐│
│ │  Search rules...                          [Filter ▼]     ││
│ │  ┌───┬──────────┬──────┬──────┬──────┬──────┬──────────┐││
│ │  │  #│ Rule     │ Tactic│ Tech │ Level│ Status│ LogSrc │││
│ │  ├───┼──────────┼──────┼──────┼──────┼──────┼──────────┤││
│ │  │ 1 │PowerSplo│Execu │T1059 │high  │Match │ Sysmon  │││
│ │  │ 2 │Susp.Log│Persi │T1078 │criti.│NoMatc│ EVTX    │││
│ │  └───┴──────────┴──────┴──────┴──────┴──────┴──────────┘││
│ └──────────────────────────────────────────────────────────┘│
│                                                              │
│ Click to expand rule YAML in modal:                          │
│ ┌──────────────────────────────────────────────────────────┐│
│ │  Powershell Suspicious Encoding                          ││
│ │  ┌─────────────────────────────────────────────────────┐ ││
│ │  │ title: Powershell Suspicious Encoding                │ ││
│ │  │ id: 7f4b3c8a-9e12-4b3c-8a9e-124b3c8a9e12           │ ││
│ │  │ status: experimental                                 │ ││
│ │  │ logsource:                                           │ ││
│ │  │   product: windows                                   │ ││
│ │  │   service: powershell                                │ ││
│ │  │ detection:                                           │ ││
│ │  │   selection:                                         │ ││
│ │  │     EventID: 4104                                    │ ││
│ │  │     ScriptBlockText|contains: '-EncodedCommand'     │ ││
│ │  └─────────────────────────────────────────────────────┘ ││
│ │  [Run Against Current Logs] [Copy] [Download]            ││
│ └──────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 8.8 Reports

```
┌─────────────────────────────────────────────────────────────┐
│  Reports                                     [+ New Report ▲]│
├──────────────────────────────────────────────────────────────┤
│ ┌──────────┬──────────┬──────────┐                          │
│ │Incident  │Summary   │IOC Report│  Report type tabs         │
│ └──────────┴──────────┴──────────┘                          │
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐│
│ │  Reports                             [Search]            ││
│ │  ┌───┬──────┬──────┬──────┬──────┬──────┬──────┬──────┐ ││
│ │  │  #│ Title│ Type │ Case │Pages│Format│Genera│ Downl│ ││
│ │  ├───┼──────┼──────┼──────┼──────┼──────┼──────┼──────┤ ││
│ │  │ 1 │Ranso│Inci..│#1024 │ 4    │ PDF  │ 2m   │ [DL] │ ││
│ │  │ 2 │Phish│Inci..│#1021 │ 3    │ HTML │ 1h   │ [DL] │ ││
│ │  └───┴──────┴──────┴──────┴──────┴──────┴──────┴──────┘ ││
│ └──────────────────────────────────────────────────────────┘│
│                                                              │
│ Report preview (modal or drawer):                            │
│ ┌──────────────────────────────────────────────────────────┐│
│ │  Incident Report: Ransomware Investigation               ││
│ │  ─────────────────────────────────────────────────────── ││
│ │                                                           ││
│ │  Incident Summary                                        ││
│ │  On July 10, 2026...                                      ││
│ │                                                           ││
│ │  Timeline of Events                                       ││
│ │  10:30:00 — Initial compromise via...                     ││
│ │  10:32:15 — PowerShell encoded command execution          ││
│ │  10:35:00 — C2 beacon detected to 185.220.101.168        ││
│ │                                                           ││
│ │  IOCs Identified                                          ││
│ │  - 185.220.101.168 (C2, VirusTotal: 0/91)                ││
│ │  - eicar.zip (Malware, MD5: d41d8cd9...)                  ││
│ │                                                           ││
│ │  [Export PDF] [Export HTML] [Export JSON] [Edit]         ││
│ └──────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 8.9 Settings

```
┌─────────────────────────────────────────────────────────────┐
│  Settings                                                     │
├──────────┬──────────────────────────────────────────────────┤
│          │                                                   │
│  General │  General                                          │
│  AI      │  ┌─────────────────────────────────────────────┐ │
│  Threat  │  │ Theme: [Dark ▼]                              │ │
│  Intel   │  │ Language: [English ▼]                        │ │
│  Security│  │ Date Format: [YYYY-MM-DD ▼]                  │ │
│  Storage │  │ Auto-save interval: [30] seconds             │ │
│  About   │  │ Log retention: [90 days ▼]                   │ │
│          │  └─────────────────────────────────────────────┘ │
│          │                                                   │
│          │  AI Providers                                     │
│          │  ┌─────────────────────────────────────────────┐ │
│          │  │ Provider    │ Model       │ Status   │ [⚙] │ │
│          │  │────────────┼─────────────┼──────────┼─────┤ │ │
│          │  │ OpenAI      │ GPT-4o      │ ● Active │ Edit│ │
│          │  │ Gemini      │ Gemini Pro  │ ○ Disab  │ Edit│ │
│          │  │ Ollama      │ llama3:70b  │ ● Active │ Edit│ │
│          │  │ [+ Add Provider]          │          │     │ │
│          │  └─────────────────────────────────────────────┘ │
│          │                                                   │
│          │  Threat Intelligence                              │
│          │  ┌─────────────────────────────────────────────┐ │
│          │  │ Service         │ Key Status     │ [⚙]      │ │
│          │  │─────────────────┼────────────────┼───────── │ │
│          │  │ VirusTotal      │ ● Configured   │ [Edit]   │ │
│          │  │ AbuseIPDB       │ ● Configured   │ [Edit]   │ │
│          │  │ AlienVault OTX  │ ○ Not set      │ [Edit]   │ │
│          │  └─────────────────────────────────────────────┘ │
│          │                                                   │
│          │  Storage: DB Size: 24.5 MB | Cached: 12 MB       │
│          │  [Clear Cache] [Export Database] [Backup]         │
│          │                                                   │
│          │  Sentinel v1.0.0 (Build 20260710)                 │
│          │  [Check for Updates] [About]                      │
├──────────┴──────────────────────────────────────────────────┤
└─────────────────────────────────────────────────────────────┘
```

### 8.10 Error Pages

**404:** Illustration + "Page not found" + "The page you're looking for doesn't exist." + [Back to Dashboard]

**500:** Illustration + "Something went wrong" + "An unexpected error occurred. Please try again." + [Reload] [Go to Dashboard]

**Offline:** Illustration + "No connection" + "Some features (AI, Threat Intel) require internet access." + "Local features are available."

---

## 9. Charts & Data Visualization

### Library

**Recharts** (React-native, composable, SVG-based, tree-shakeable).

### Bar Charts

- Usage: IOCs by type, Events by severity, Cases by status
- Single series, horizontal bars preferred for label readability
- Bar color maps to semantic meaning (danger=critical, amber=high, etc.)
- Tooltip on hover with exact value

### Line Charts

- Usage: Activity over time (cases per day, log uploads, enrichment count)
- Single or multi-series (toggleable legends)
- Area fill with gradient (low opacity)
- Time-based X axis with smart date formatting

### Pie / Donut Charts

- Usage: Event type distribution, source distribution
- Donut variant (center shows total count)
- Max 8 slices; "Other" group for remainder
- Stroke on hover to highlight

### Heatmaps

- Usage: Event frequency by hour/weekday (login attempts, brute force patterns)
- Color intensity from low (cool blue) to high (hot red)
- X axis: hour of day, Y axis: day of week

### Timelines

- Usage: Attack chain reconstruction, case activity log
- Vertical timeline with dot markers
- Color-coded by event type
- Connecting lines between related events

### Threat Relationship Graph

- Usage: IOC relationships (IP → domain → hash)
- Force-directed graph (vis-network or cytoscape.js)
- Nodes sized by confidence, colored by type
- Edge labels for relationship type

### MITRE Coverage Matrix

- Usage: MITRE ATT&CK coverage visualization
- Standard MITRE matrix layout (tactics columns, techniques rows)
- Color coding: detected (green), partial (amber), not detected (gray)
- Click cell to see matching detections

### Risk Score Visualization

- Gauge-style radial chart or segmented bar
- Score 0–100 with color zones: 0–30 (green), 31–60 (amber), 61–100 (red)
- Animated fill on load

---

## 10. Table Design

### Enterprise Data Table Specification

```
┌──────────────────────────────────────────────────────────────────┐
│  Title                                             [Actions ▼]   │
├──────────────────────────────────────────────────────────────────┤
│  Search...            [Filter ▼]  [Columns ▼]    [Export ▼]      │
│                                                      ↕ Export DL │
│ ┌──┬────────┬──────┬──────┬─────────┬────────┬────────┬──────┐  │
│ │☐ │ Case # │Severi│Status│ Assigned│Updated │ IOCs   │  ⚡  │  │
│ ├──┼────────┼──────┼──────┼─────────┼────────┼────────┼──────┤  │
│ │☐ │ #1024  │CRIT  │Open  │ jsmith  │ 2m ago │ 12     │  →   │  │
│ │☐ │ #1023  │HIGH  │In Pr │ adoe    │ 15m ago│ 8      │  →   │  │
│ │☐ │ #1022  │MED   │Resolv│ jsmith  │ 1h ago │ 4      │  →   │  │
│ │☐ │ #1021  │LOW   │Closed│ bjones  │ 3h ago │ 2      │  →   │  │
│ └──┴────────┴──────┴──────┴─────────┴────────┴────────┴──────┘  │
│   ☐ Select all   4 items          Page 1 of 1     [10 ▼] per pg │
└──────────────────────────────────────────────────────────────────┘
```

### Table Properties

| Feature | Implementation |
|---------|---------------|
| **Sorting** | Click column header to sort ASC/DESC. Active column shows arrow indicator. Multi-sort: Shift+click. |
| **Filtering** | Filter dropdown per column (text contains, exact match, range). Global search across all visible columns. |
| **Pagination** | Bottom bar: page number, page size selector (10/25/50/100), total count. |
| **Bulk actions** | Checkbox column. Actions appear in top bar when items selected. |
| **Export** | Export visible rows or all filtered rows as CSV or JSON. |
| **Sticky headers** | Column headers and first column (checkbox) stay visible on scroll. |
| **Resizable columns** | Drag column header borders to resize. Min width: 60px. Max width: 500px. |
| **Row click** | Click row to navigate to detail view or open action menu. |
| **Row hover** | Background changes to `--bg-tertiary`. |
| **Alternating rows** | Optional (not recommended for security data; use row hover instead). |
| **Empty state** | Illustration + "No data" + CTA button. |
| **Loading state** | Skeleton rows (5 shimmer rows matching column layout). |

### Table Density

| Mode | Row Height | Usage |
|------|-----------|-------|
| **Compact** | 32px | Tables with 50+ rows (upload history, IOCs) |
| **Standard** | 40px | Default for most tables |
| **Comfortable** | 48px | Tables with inline actions or previews |

---

## 11. Responsive Behavior

Sentinel is desktop-only. "Responsive" refers to Electron window resizing:

| Window Width | Layout Behavior |
|-------------|----------------|
| ≥ 1440px | Full layout with sidebar expanded |
| 1024–1439px | Sidebar collapses to icon-only (64px), some panels stack |
| < 1024px | Minimum enforced by Electron (resize disabled below 1024×768) |

### Specific Behaviors

- **Sidebar:** Auto-collapses below 1280px, toggleable via hamburger menu
- **Tables:** Horizontal scroll within table container if columns exceed width
- **Cards:** Switch from 4-column to 2-column grid below 1280px
- **Detail panels:** Side-by-side at ≥ 1280px, stacked at < 1280px
- **Modals:** Full-width below 1024px (90vw)

---

## 12. Animations

### Durations

| Token | Duration | Usage |
|-------|----------|-------|
| `--anim-fast` | 150ms | Hover, button press, small transitions |
| `--anim-normal` | 200ms | Standard transitions |
| `--anim-slow` | 300ms | Dialog open/close, panel slide |
| `--anim-xslow` | 500ms | Page transitions, background loading |

### Easing

```css
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
```

### Animation Specifications

| Element | Animation | Duration | Easing |
|---------|-----------|----------|--------|
| **Page transition** | Fade in + slight translateY(8px → 0) | 200ms | ease-out |
| **Modal open** | Backdrop fade + scale(0.95 → 1) | 200ms | ease-out |
| **Modal close** | Fade out + scale(1 → 0.95) | 150ms | ease-in |
| **Drawer slide** | TranslateX(100% → 0) | 200ms | ease-out |
| **Toast enter** | TranslateX(100% → 0) + fade | 300ms | ease-out |
| **Toast exit** | TranslateX(0 → 100%) + fade | 200ms | ease-in |
| **Tooltip** | Fade in | 150ms | ease-out |
| **Skeleton shimmer** | Gradient sweep (infinite) | 1500ms | linear |
| **Tab switch** | Fade content | 150ms | ease-out |
| **Spinner rotation** | 360° rotate (infinite) | 800ms | linear |
| **Progress bar** | Width transition | 300ms | ease-out |
| **Button loading** | Fade icon in, pulse text | 200ms | ease-out |

---

## 13. Accessibility

### Compliance Target

WCAG 2.2 Level AA minimum, AAA for color contrast.

### Keyboard Navigation

| Key | Action |
|-----|--------|
| **Tab** | Move focus forward through interactive elements |
| **Shift+Tab** | Move focus backward |
| **Enter / Space** | Activate focused element |
| **Escape** | Close modal, drawer, dropdown, dismiss toast |
| **Arrow keys** | Navigate within listbox, table, tab list, dropdown |
| **Ctrl+K** | Open command palette |
| **Ctrl+/** | Show keyboard shortcuts |
| **Ctrl+N** | New case (global) |
| **Ctrl+U** | Upload logs (global) |

### Focus Management

- Visible focus ring (`2px solid --border-accent` with `3px` offset) on all interactive elements
- Focus order follows visual order (left-to-right, top-to-bottom)
- Modal/drawer open: trap focus within component, close on Escape
- Modal/drawer close: return focus to triggering element
- Page navigation: focus heading of new page

### ARIA Usage

| Pattern | ARIA Attributes |
|---------|----------------|
| **Navigation** | `role="navigation"`, `aria-label`, `aria-current="page"` |
| **Tabs** | `role="tablist"`, `role="tab"`, `role="tabpanel"`, `aria-selected`, `aria-controls` |
| **Modals** | `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, `aria-describedby` |
| **Alerts** | `role="alert"` |
| **Progress** | `role="progressbar"`, `aria-valuenow`, `aria-valuemin`, `aria-valuemax` |
| **Tables** | `<table>`, `<th>` with `scope`, `aria-sort` on sortable headers |
| **Status** | `role="status"`, `aria-live="polite"` for dynamic updates |
| **Errors** | `aria-invalid`, `aria-describedby` linking to error message |

### Screen Reader Support

- All icons hidden by default (`aria-hidden="true"`) unless they are the sole content of an interactive element
- Loading states announced via `aria-live="polite"` region
- Dynamic content changes announced (e.g., "Case #1024 updated", "3 IOCs enriched")
- Images (icons, avatars) have `alt` text when meaningful
- Skip-to-content link at app root

---

## 14. Electron UX

### Native File Picker

```typescript
// Triggered by Upload button or drag-and-drop
dialog.showOpenDialog({
  title: 'Select Log Files',
  filters: [
    { name: 'Log Files', extensions: ['evtx', 'log', 'txt', 'json', 'csv', 'xml', 'gz'] },
    { name: 'All Files', extensions: ['*'] }
  ],
  properties: ['openFile', 'multiSelections']
})
```

### Drag-and-Drop

- Full-page drop zone overlay (semi-transparent with dashed border)
- Accepted file types shown
- Reject invalid files with visual feedback (shake + error toast)
- Progress indicator during upload (percentage + estimated time)

### Native Notifications

```typescript
// Triggered by: enrichment complete, AI analysis done, long operation finished
new Notification('Sentinel', {
  body: 'IOC enrichment complete for Case #1024 (12 IOCs analyzed)',
  icon: path.join(__dirname, '../assets/icon.ico')
})
```

### Context Menus

- Right-click on table rows: Edit, Delete, Open in New Tab, Copy Value
- Right-click on IOCs: Copy Value, Enrich, Open in Browser (for URLs)
- Right-click on file entries: Open File Location, Reveal in Explorer

### File System Operations

```typescript
// Open report folder in Explorer
shell.openPath(reportDir)

// Open evidence folder
shell.openPath(evidencePath)

// Save file dialog
dialog.showSaveDialog({
  title: 'Export Report',
  defaultPath: `incident-report-${caseNumber}.pdf`,
  filters: [
    { name: 'PDF', extensions: ['pdf'] },
    { name: 'HTML', extensions: ['html'] },
    { name: 'JSON', extensions: ['json'] }
  ]
})
```

### Window Management

| Feature | Implementation |
|---------|---------------|
| **Minimum size** | 1024×768 |
| **Default size** | 1440×900 |
| **Remember position** | Save window bounds to config, restore on launch |
| **Frameless** | Custom title bar (drag region: -webkit-app-region: drag) |
| **System tray** | Minimize to tray. Double-click tray icon to restore |
| **Single instance** | Second launch focuses existing window |

---

## 15. API Specification

### 15.1 Authentication

#### POST /api/v1/auth/register

- **Purpose:** Create new user account
- **Auth:** None
- **Headers:** `Content-Type: application/json`
- **Body:** `{ "email": "string", "password": "string", "name": "string" }`
- **Response 201:** `{ "id": "uuid", "email": "string", "name": "string", "created_at": "iso8601" }`
- **Response 409:** `{ "detail": "Email already registered" }`
- **Frontend:** Login/Register page

#### POST /api/v1/auth/login

- **Purpose:** Authenticate and receive JWT
- **Auth:** None
- **Headers:** `Content-Type: application/json`
- **Body:** `{ "email": "string", "password": "string" }`
- **Response 200:** `{ "access_token": "jwt", "token_type": "bearer", "user": { "id", "email", "name", "role" } }`
- **Response 401:** `{ "detail": "Invalid credentials" }`
- **Frontend:** Login page

#### POST /api/v1/auth/mfa/setup

- **Purpose:** Generate TOTP secret and QR code URL
- **Auth:** Bearer token
- **Response 200:** `{ "secret": "base32", "qr_code": "data:image/png;base64,..." }`
- **Frontend:** Settings > Security > MFA Setup

#### POST /api/v1/auth/mfa/verify

- **Purpose:** Verify TOTP code during setup
- **Body:** `{ "code": "string" }`
- **Response 200:** `{ "enabled": true }`
- **Frontend:** Settings > Security > MFA Setup

#### POST /api/v1/auth/mfa/validate

- **Purpose:** Validate TOTP code during login (step 2)
- **Body:** `{ "email": "string", "code": "string", "temp_token": "string" }`
- **Response 200:** `{ "access_token": "jwt", "token_type": "bearer" }`
- **Frontend:** Login page (MFA step)

### 15.2 Dashboard

#### GET /api/v1/dashboard/stats

- **Purpose:** Fetch dashboard statistics
- **Auth:** Bearer token
- **Response 200:** `{ "open_cases": 8, "logs_today": 3, "total_iocs": 47, "active_alerts": 2, "cases_trend": 12, "logs_trend": -5, "iocs_trend": 23 }`
- **Frontend:** Dashboard stat cards

#### GET /api/v1/dashboard/recent-cases

- **Purpose:** Recent cases for dashboard
- **Query:** `?limit=5`
- **Response 200:** `[{ "id": "uuid", "case_number": 1024, "title": "string", "severity": "CRITICAL", "status": "OPEN", "assigned_to": { "name": "string" }, "updated_at": "iso8601", "ioc_count": 12 }]`
- **Frontend:** Dashboard recent cases table

#### GET /api/v1/dashboard/activity

- **Purpose:** Recent activity timeline
- **Query:** `?limit=10`
- **Response 200:** `[{ "type": "upload|ai|enrich|report|case", "description": "string", "timestamp": "iso8601", "link": { "path": "string" } }]`
- **Frontend:** Dashboard activity timeline

### 15.3 Logs

#### POST /api/v1/logs/upload

- **Purpose:** Upload log file
- **Auth:** Bearer token
- **Headers:** `Content-Type: multipart/form-data`
- **Body:** FormData with `file` (binary)
- **Response 201:** `{ "id": "uuid", "filename": "string", "format": "EVTX|SYSLOG|APACHE|NGINX|JSON|CSV|XML", "size": 12345678, "status": "UPLOADED", "created_at": "iso8601" }`
- **Response 413:** `{ "detail": "File too large" }`
- **Frontend:** Log Analysis > Upload zone

#### GET /api/v1/logs

- **Purpose:** List uploaded logs
- **Query:** `?page=1&per_page=20&search=string&format=EVTX&status=string`
- **Response 200:** `{ "items": [{ "id", "filename", "format", "size", "event_count", "ioc_count", "status", "created_at" }], "total": 50, "page": 1, "per_page": 20 }`
- **Frontend:** Log Analysis > Upload history table

#### GET /api/v1/logs/{id}

- **Purpose:** Get log detail with metadata
- **Response 200:** `{ "id", "filename", "format", "size", "total_events", "suspicious_count", "event_types": { "4624": 120, "4625": 15 }, "filepath": "string", "status", "created_at", "parsed_at" }`
- **Frontend:** Log Analysis > Detail view

#### GET /api/v1/logs/{id}/events

- **Purpose:** Get parsed events for a log
- **Query:** `?page=1&per_page=50&search=string&type=4624&severity=HIGH&time_from=iso8601&time_to=iso8601`
- **Response 200:** `{ "items": [{ "id", "timestamp", "event_type", "severity", "source_ip", "destination_ip", "username", "process_name", "message", "raw" }], "total": 3420, "page": 1, "per_page": 50 }`
- **Frontend:** Log Analysis > Event list with pagination

#### GET /api/v1/logs/{id}/timeline

- **Purpose:** Get timeline view of events
- **Response 200:** `[{ "id", "timestamp", "event_type", "severity", "message", "source_ip", "destination_ip" }]`
- **Frontend:** Log Analysis > Timeline view

#### GET /api/v1/logs/{id}/iocs

- **Purpose:** Get extracted IOCs for a log
- **Response 200:** `[{ "id", "value", "type": "IP|DOMAIN|URL|MD5|SHA1|SHA256|EMAIL", "count": 3, "first_seen": "iso8601", "last_seen": "iso8601", "confidence": null }]`
- **Frontend:** Log Analysis > IOCs tab

### 15.4 Threat Intelligence

#### GET /api/v1/threat-intel/iocs

- **Purpose:** List all IOCs across all logs
- **Query:** `?page=1&per_page=20&type=IP&status=ENRICHED&search=string`
- **Response 200:** `{ "items": [{ "id", "value", "type", "source_log": "string", "confidence": 85, "last_enriched": "iso8601", "enrichment_status": "PENDING|ENRICHED|ERROR", "malicious": true|false|null }], "total": 47 }`
- **Frontend:** Threat Intelligence > IOC table

#### POST /api/v1/threat-intel/enrich

- **Purpose:** Enrich specific IOC
- **Body:** `{ "ioc_ids": ["uuid1", "uuid2"] }`
- **Response 202:** `{ "task_id": "uuid", "status": "PROCESSING" }`
- **Frontend:** Threat Intelligence > Batch enrich

#### GET /api/v1/threat-intel/iocs/{id}/enrichment

- **Purpose:** Get enrichment results for IOC
- **Response 200:** `{ "ioc_id": "uuid", "value": "185.220.101.168", "results": { "virustotal": { "detections": 0, "total": 91, "last_analyzed": "iso8601" }, "abuseipdb": { "isp": "OVH SAS", "country": "FR", "abuse_reports": 3, "confidence": 12 }, "otx": { "pulses": 2 } }, "overall_confidence": 85 }`
- **Frontend:** Threat Intelligence > IOC detail panel

### 15.5 AI

#### POST /api/v1/ai/chat

- **Purpose:** Send message to AI assistant
- **Auth:** Bearer token
- **Body:** `{ "message": "string", "context": { "case_id": "uuid|null", "log_id": "uuid|null", "event_ids": ["uuid"] }, "provider": "openai|gemini|ollama", "stream": true }`
- **Response 200 (non-streaming):** `{ "reply": "string", "sources": ["string"], "tokens_used": 1500 }`
- **Response 200 (streaming):** Server-Sent Events `data: {"type": "token", "content": "string"}\n\ndata: {"type": "done", "usage": { "tokens": 1500 }}\n\n`
- **Frontend:** AI Copilot

#### POST /api/v1/ai/summarize

- **Purpose:** Generate AI summary of log or case
- **Body:** `{ "type": "log|case", "id": "uuid", "provider": "string" }`
- **Response 200:** `{ "summary": "string", "key_findings": ["string"], "recommendations": ["string"] }`
- **Frontend:** AI Copilot > Summarize action

#### GET /api/v1/ai/conversations

- **Purpose:** List AI conversation history
- **Response 200:** `[{ "id": "uuid", "title": "string", "case_id": "uuid|null", "message_count": 12, "provider": "string", "created_at": "iso8601", "updated_at": "iso8601" }]`
- **Frontend:** AI Copilot > History sidebar

#### GET /api/v1/ai/conversations/{id}

- **Purpose:** Get full conversation
- **Response 200:** `{ "id": "uuid", "title": "string", "messages": [{ "role": "user|assistant", "content": "string", "timestamp": "iso8601" }], "context": { "case_id", "log_id" }, "provider": "string" }`
- **Frontend:** AI Copilot > Load conversation

### 15.6 Cases

#### GET /api/v1/cases

- **Purpose:** List cases
- **Query:** `?page=1&per_page=20&status=OPEN&severity=CRITICAL&search=string&assigned_to=uuid`
- **Response 200:** `{ "items": [{ "id", "case_number", "title", "severity", "status", "assigned_to": { "id", "name" }, "ioc_count", "evidence_count", "updated_at", "tags": ["string"] }], "total": 50, "page": 1, "per_page": 20 }`
- **Frontend:** Cases > Case list table

#### POST /api/v1/cases

- **Purpose:** Create new case
- **Headers:** `Content-Type: application/json`
- **Body:** `{ "title": "string", "description": "string", "severity": "CRITICAL|HIGH|MEDIUM|LOW", "tags": ["string"], "log_ids": ["uuid"], "ioc_ids": ["uuid"] }`
- **Response 201:** `{ "id": "uuid", "case_number": 1025, "title": "string", ... }`
- **Frontend:** Cases > New Case dialog

#### GET /api/v1/cases/{id}

- **Purpose:** Get case detail
- **Response 200:** `{ "id", "case_number", "title", "description", "severity", "status", "assigned_to": { "id", "name", "email" }, "created_at", "updated_at", "resolved_at", "closed_at", "tags": ["string"], "iocs": [...], "evidence": [...], "comments": [...], "logs": [...], "timeline": [...] }`
- **Frontend:** Cases > Detail view

#### PATCH /api/v1/cases/{id}

- **Purpose:** Update case
- **Body:** `{ "title": "string", "description": "string", "severity": "string", "status": "string", "tags": ["string"] }`
- **Response 200:** Updated case object
- **Frontend:** Cases > Detail > Edit

#### POST /api/v1/cases/{id}/evidence

- **Purpose:** Add evidence to case
- **Headers:** `Content-Type: multipart/form-data`
- **Body:** FormData with `file` + `description: string`
- **Response 201:** `{ "id": "uuid", "filename": "string", "description": "string", "filepath": "string", "size": 1234, "created_at": "iso8601" }`
- **Frontend:** Cases > Detail > Evidence tab

#### POST /api/v1/cases/{id}/comments

- **Purpose:** Add comment to case
- **Body:** `{ "content": "string", "parent_id": "uuid|null" }`
- **Response 201:** `{ "id": "uuid", "content": "string", "author": { "id", "name" }, "created_at": "iso8601", "parent_id": "uuid|null" }`
- **Frontend:** Cases > Detail > Comments

### 15.7 Reports

#### GET /api/v1/reports

- **Purpose:** List reports
- **Query:** `?page=1&per_page=20&type=INCIDENT|SUMMARY|IOC&search=string`
- **Response 200:** `{ "items": [{ "id", "title", "type", "case_id", "case_number", "format": "PDF|HTML|JSON", "page_count": 4, "generated_at", "filepath" }], "total": 10 }`
- **Frontend:** Reports > Report list

#### POST /api/v1/reports/generate

- **Purpose:** Generate report from case
- **Body:** `{ "case_id": "uuid", "type": "INCIDENT|SUMMARY|IOC", "format": "PDF|HTML|JSON", "template_id": "uuid|null" }`
- **Response 201:** `{ "id": "uuid", "title": "string", "type": "string", "format": "string", "status": "GENERATING", "filepath": "string" }`
- **Frontend:** Reports > Generate button

#### GET /api/v1/reports/{id}/download

- **Purpose:** Download report file
- **Response 200:** Binary file stream with `Content-Disposition: attachment`
- **Frontend:** Reports > Download button

### 15.8 Settings

#### GET /api/v1/settings

- **Purpose:** Get all settings
- **Response 200:** `{ "theme": "dark|light", "language": "en", "date_format": "YYYY-MM-DD", "log_retention_days": 90, "ai_providers": [{ "id", "name", "provider_type", "model", "enabled", "configured": true }], "threat_intel": { "virustotal": { "configured": true }, "abuseipdb": { "configured": true }, "otx": { "configured": false } } }`
- **Frontend:** Settings > All tabs

#### PATCH /api/v1/settings

- **Purpose:** Update settings
- **Body:** Partial settings object
- **Response 200:** Updated settings
- **Frontend:** Settings > Save

#### POST /api/v1/settings/ai/test

- **Purpose:** Test AI provider connection
- **Body:** `{ "provider_id": "uuid" }`
- **Response 200:** `{ "success": true, "latency_ms": 1200, "model": "gpt-4o" }`
- **Response 200 (failure):** `{ "success": false, "error": "Connection timeout" }`
- **Frontend:** Settings > AI Providers > Test

#### POST /api/v1/settings/threat-intel/test

- **Purpose:** Test threat intel API key
- **Body:** `{ "service": "virustotal|abuseipdb|otx" }`
- **Response 200:** `{ "success": true, "message": "API key valid" }`
- **Frontend:** Settings > Threat Intel > Test

### 15.9 Detection

#### GET /api/v1/detection/sigma

- **Purpose:** List Sigma rules
- **Query:** `?page=1&per_page=20&search=string&tactic=string&level=string`
- **Response 200:** `{ "items": [{ "id", "title", "rule_id", "tactic", "technique", "level", "status": "MATCH|NO_MATCH|NOT_RUN", "log_source": "string" }], "total": 50 }`
- **Frontend:** Detection > Sigma tab

#### GET /api/v1/detection/yara

- **Purpose:** List YARA rules
- **Response 200:** `{ "items": [{ "id", "title", "rule_id", "author", "status", "matches" }] }`
- **Frontend:** Detection > YARA tab

#### POST /api/v1/detection/sigma/run

- **Purpose:** Run Sigma rule against log
- **Body:** `{ "rule_id": "uuid", "log_id": "uuid" }`
- **Response 200:** `{ "match": true, "events_matched": 3, "matching_events": [{ "id", "timestamp", "message" }] }`
- **Frontend:** Detection > Run button

### 15.10 Health

#### GET /api/v1/health

- **Purpose:** Backend health check
- **Auth:** None
- **Response 200:** `{ "status": "healthy", "version": "1.0.0", "uptime_seconds": 3600, "database": { "size_mb": 24.5, "connections": 1 }, "storage": { "used_mb": 156, "free_mb": 45600 } }`
- **Frontend:** Electron startup health check, Status bar

---

## 16. Third-Party Integrations

### 16.1 OpenAI

| Property | Specification |
|----------|---------------|
| **Purpose** | AI chat, analysis, summarization |
| **Auth** | API key (sk-...) |
| **API Base** | `https://api.openai.com/v1` |
| **Models** | `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `gpt-3.5-turbo` |
| **Rate Limits** | Tier-based (default: 500 RPM for GPT-4o) |
| **Retry** | Exponential backoff (3 attempts), 429/503 retry |
| **Error** | `{ "error": { "message": "...", "type": "...", "code": 429 } }` |
| **Cache** | Identical prompts within 5 min return cached (configurable) |
| **Endpoint** | `POST /v1/chat/completions` |

Request:
```json
{
  "model": "gpt-4o",
  "messages": [{ "role": "system", "content": "You are a SOC analyst assistant..." }, { "role": "user", "content": "Analyze this event..." }],
  "temperature": 0.3,
  "max_tokens": 4096,
  "stream": true
}
```

### 16.2 Google Gemini

| Property | Specification |
|----------|---------------|
| **Purpose** | AI chat, analysis (fallback/secondary provider) |
| **Auth** | API key |
| **API Base** | `https://generativelanguage.googleapis.com/v1beta` |
| **Models** | `gemini-2.0-flash`, `gemini-2.0-pro` |
| **Rate Limits** | 60 RPM (free tier), 2000 RPM (paid) |
| **Retry** | Exponential backoff (3 attempts) |
| **Endpoint** | `POST /models/{model}:generateContent` |

### 16.3 Ollama

| Property | Specification |
|----------|---------------|
| **Purpose** | Local AI (fully offline) |
| **Auth** | None (localhost only) |
| **API Base** | User-configured (default: `http://localhost:11434`) |
| **Models** | User-installed (recommended: `llama3.1:70b`, `mixtral:8x7b`) |
| **Rate Limits** | Local hardware dependent |
| **Retry** | 3 attempts with 2s delay |
| **Endpoint** | `POST /api/chat` |

### 16.4 VirusTotal

| Property | Specification |
|----------|---------------|
| **Purpose** | File hash, IP, domain, URL reputation lookup |
| **Auth** | API key |
| **API Base** | `https://www.virustotal.com/api/v3` |
| **Rate Limits** | 4 requests/min (free), 10/min (standard), 60/min (premium) |
| **Retry** | 3 attempts, 429: wait `Retry-After` header |
| **Cache TTL** | 24 hours |
| **Endpoints** | `GET /ip_addresses/{ip}`, `GET /domains/{domain}`, `GET /urls/{url}`, `GET /files/{hash}` |

### 16.5 AbuseIPDB

| Property | Specification |
|----------|---------------|
| **Purpose** | IP address reputation |
| **Auth** | API key |
| **API Base** | `https://api.abuseipdb.com/api/v2` |
| **Rate Limits** | 1000 requests/day (free) |
| **Retry** | 3 attempts, daily limit exceeded: return cached if available |
| **Cache TTL** | 6 hours |
| **Endpoint** | `GET /check?ipAddress={ip}&maxAgeInDays=90` |

### 16.6 AlienVault OTX

| Property | Specification |
|----------|---------------|
| **Purpose** | IOC pulse lookup, threat correlation |
| **Auth** | API key |
| **API Base** | `https://otx.alienvault.com/api/v1` |
| **Rate Limits** | 10 requests/min (free) |
| **Retry** | 3 attempts |
| **Cache TTL** | 12 hours |
| **Endpoint** | `GET /indicators/{type}/{value}/general` |

### 16.7 NVD

| Property | Specification |
|----------|---------------|
| **Purpose** | CVE lookup and vulnerability details |
| **Auth** | None (rate-limited public API) |
| **API Base** | `https://services.nvd.nist.gov/rest/json/cves/2.0` |
| **Rate Limits** | 5 requests per 30 seconds (unauthenticated) |
| **Retry** | 3 attempts |
| **Cache TTL** | 24 hours |
| **Endpoint** | `GET ?cveId=CVE-2024-12345` |

### 16.8 CISA KEV

| Property | Specification |
|----------|---------------|
| **Purpose** | Check if CVE is in Known Exploited Vulnerabilities catalog |
| **Auth** | None |
| **API Base** | `https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json` |
| **Cache TTL** | 6 hours |
| **Endpoint** | Single JSON feed |

### 16.9 MITRE ATT&CK

| Property | Specification |
|----------|---------------|
| **Purpose** | Tactic/technique mapping and matrix visualization |
| **Auth** | None |
| **API Base** | `https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json` |
| **Cache TTL** | 24 hours (updated infrequently) |
| **Storage** | Local JSON in app data directory for offline use |

---

## 17. Security Requirements

### JWT Handling

- Store JWT in memory only (never localStorage or sessionStorage)
- Use refresh token flow: short-lived access token (15 min) + long-lived refresh token (7 days)
- Refresh token stored in Electron's `safeStorage` (encrypted)
- On app quit: clear tokens from memory
- On token expiry: auto-refresh if refresh token available; otherwise redirect to login
- All API requests include `Authorization: Bearer <token>` header via Axios interceptor

### Secure Storage (Electron)

```typescript
import { safeStorage } from 'electron'

// Encrypt sensitive data (API keys, tokens)
const encrypted = safeStorage.encryptString(plaintext)
const decrypted = safeStorage.decryptString(encrypted)
```

Data stored with `safeStorage`:
- AI provider API keys
- Threat intelligence API keys
- JWT refresh token
- Database encryption key (V2)

### CSP

```html
<meta http-equiv="Content-Security-Policy" content="
  default-src 'self';
  script-src 'self';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: blob:;
  connect-src 'self' http://127.0.0.1:8000 http://localhost:* ws://localhost:*;
  font-src 'self';
  frame-src 'none';
  object-src 'none';
  base-uri 'self';
">
```

### Electron IPC

- Context isolation enabled
- Node integration disabled in renderer
- `preload.ts` exposes limited API via `contextBridge`
- All IPC messages validated with Zod schema before processing
- Channel whitelist:

```typescript
contextBridge.exposeInMainWorld('electronAPI', {
  platform: () => process.platform,
  openFileDialog: (options) => ipcRenderer.invoke('dialog:openFile', options),
  saveFileDialog: (options) => ipcRenderer.invoke('dialog:saveFile', options),
  showNotification: (title, body) => ipcRenderer.invoke('notification:show', title, body),
  openPath: (path) => ipcRenderer.invoke('shell:openPath', path),
  getAppVersion: () => ipcRenderer.invoke('app:getVersion'),
  onMenuAction: (callback) => ipcRenderer.on('menu:action', (_, action) => callback(action))
})
```

### XSS Protection

- React default escaping (curly braces)
- No `dangerouslySetInnerHTML` except for report preview (sanitized with DOMPurify)
- CSP restricts script execution to `'self'`
- Input validation on all user text inputs

### CSRF

- No CSRF needed (Electron same-origin, no cookie-based auth)
- JWT in Authorization header, not cookies
- State-changing endpoints require Authorization header

### File Upload Validation

```typescript
// Frontend validation before upload
const VALID_EXTENSIONS = ['evtx', 'log', 'txt', 'json', 'csv', 'xml', 'gz']
const MAX_FILE_SIZE = 500 * 1024 * 1024 // 500 MB

function validateFile(file: File): { valid: boolean; error?: string } {
  const ext = file.name.split('.').pop()?.toLowerCase()
  if (!ext || !VALID_EXTENSIONS.includes(ext)) return { valid: false, error: 'Unsupported file type' }
  if (file.size > MAX_FILE_SIZE) return { valid: false, error: 'File exceeds 500 MB limit' }
  if (file.size === 0) return { valid: false, error: 'File is empty' }
  return { valid: true }
}
```

---

## 18. Performance Requirements

### Startup Time

| Phase | Target |
|-------|--------|
| Electron process launch | < 500ms |
| Renderer process (React load) | < 1s |
| API health check (electron startup) | < 2s |
| Full app interactive | < 5s |

### Code Splitting

```typescript
// Route-level lazy loading
const LogAnalysis = lazy(() => import('@pages/Logs/LogAnalysis'))
const ThreatIntel = lazy(() => import('@pages/ThreatIntel/ThreatIntel'))
const AICopilot = lazy(() => import('@pages/AICopilot/AICopilot'))
const Cases = lazy(() => import('@pages/Cases/Cases'))
const Reports = lazy(() => import('@pages/Reports/Reports'))
const Settings = lazy(() => import('@pages/Settings/Settings'))
```

### Virtualized Tables

- Use `@tanstack/react-virtual` for tables with > 100 rows
- Window height + overscan (5 rows) for smooth scrolling
- Estimated row height 40px (standard), 32px (compact)

### Image Optimization

- All icons as SVGs (inlined or sprite sheet)
- Splash screen image as preloaded base64
- No raster images in UI

### Caching Strategy

| Data | Strategy | TTL |
|------|----------|-----|
| Dashboard stats | Poll every 30s | 30s |
| Case list | Cache + background refetch | 60s |
| Log event list | Cache per log + pagination | 5 min |
| Threat intel results | SQLite cache | Per-service TTL |
| AI conversations | Load on demand | Session |
| Settings | Load once | Session |
| MITRE data | Local JSON | 24h |
| Sigma/YARA rules | Load on tab visit | Session |

### Memory Budget

| Category | Limit |
|----------|-------|
| JS heap (renderer) | < 200 MB |
| Virtual table memory | < 50 MB (10k rows) |
| AI conversation history | < 20 MB (100 sessions) |
| Total renderer | < 350 MB |

---

## 19. Frontend Architecture

### Folder Structure

```
frontend/
├── public/
│   └── electron.html            # Electron entry HTML
│
├── src/
│   ├── main.tsx                 # React entry point
│   ├── App.tsx                  # Root component + router
│   ├── vite-env.d.ts
│   │
│   ├── api/
│   │   ├── client.ts            # Axios instance, interceptors, token management
│   │   ├── auth.ts              # Auth API calls
│   │   ├── logs.ts              # Log API calls
│   │   ├── threat-intel.ts      # Threat intel API calls
│   │   ├── ai.ts                # AI API calls
│   │   ├── cases.ts             # Case API calls
│   │   ├── reports.ts           # Report API calls
│   │   ├── settings.ts          # Settings API calls
│   │   ├── detection.ts         # Detection API calls
│   │   └── dashboard.ts         # Dashboard API calls
│   │
│   ├── components/
│   │   ├── ui/                  # Design system primitives
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Dropdown.tsx
│   │   │   ├── Checkbox.tsx
│   │   │   ├── Radio.tsx
│   │   │   ├── Tabs.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Drawer.tsx
│   │   │   ├── Toast.tsx
│   │   │   ├── Alert.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── Tooltip.tsx
│   │   │   ├── Skeleton.tsx
│   │   │   ├── EmptyState.tsx
│   │   │   ├── Spinner.tsx
│   │   │   ├── ProgressBar.tsx
│   │   │   ├── Pagination.tsx
│   │   │   └── index.ts
│   │   │
│   │   ├── data-table/          # Enterprise data table
│   │   │   ├── DataTable.tsx
│   │   │   ├── DataTableHeader.tsx
│   │   │   ├── DataTableRow.tsx
│   │   │   ├── DataTablePagination.tsx
│   │   │   ├── DataTableFilter.tsx
│   │   │   └── hooks.ts
│   │   │
│   │   ├── layout/
│   │   │   ├── AppShell.tsx     # Main layout wrapper
│   │   │   ├── Sidebar.tsx
│   │   │   ├── TopBar.tsx
│   │   │   ├── StatusBar.tsx
│   │   │   ├── Breadcrumbs.tsx
│   │   │   └── PageHeader.tsx
│   │   │
│   │   ├── charts/
│   │   │   ├── BarChart.tsx
│   │   │   ├── LineChart.tsx
│   │   │   ├── PieChart.tsx
│   │   │   ├── TimelineChart.tsx
│   │   │   ├── RiskGauge.tsx
│   │   │   └── mitre/
│   │   │       ├── MitreMatrix.tsx
│   │   │       └── MitreCell.tsx
│   │   │
│   │   └── common/
│   │       ├── UploadZone.tsx
│   │       ├── CommandPalette.tsx
│   │       ├── NotificationCenter.tsx
│   │       ├── SearchInput.tsx
│   │       ├── CopyButton.tsx
│   │       ├── UserMenu.tsx
│   │       └── ThemeToggle.tsx
│   │
│   ├── pages/
│   │   ├── Login/
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx
│   │   │   ├── MFASetup.tsx
│   │   │   └── MFALogin.tsx
│   │   ├── Dashboard/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── StatCard.tsx
│   │   │   ├── RecentCasesWidget.tsx
│   │   │   └── ActivityWidget.tsx
│   │   ├── Logs/
│   │   │   ├── LogAnalysis.tsx
│   │   │   ├── UploadZone.tsx
│   │   │   ├── UploadHistory.tsx
│   │   │   ├── LogDetail.tsx
│   │   │   ├── EventTable.tsx
│   │   │   ├── TimelineView.tsx
│   │   │   └── EventDetail.tsx
│   │   ├── ThreatIntel/
│   │   │   ├── ThreatIntel.tsx
│   │   │   ├── IOCTable.tsx
│   │   │   ├── IOCDetail.tsx
│   │   │   └── EnrichmentPanel.tsx
│   │   ├── AICopilot/
│   │   │   ├── AICopilot.tsx
│   │   │   ├── ChatHistory.tsx
│   │   │   ├── ChatMessages.tsx
│   │   │   └── ChatInput.tsx
│   │   ├── Cases/
│   │   │   ├── CaseList.tsx
│   │   │   ├── CaseDetail.tsx
│   │   │   ├── CaseOverview.tsx
│   │   │   ├── CaseTimeline.tsx
│   │   │   ├── CaseEvidence.tsx
│   │   │   ├── CaseComments.tsx
│   │   │   └── CaseIOCs.tsx
│   │   ├── Detection/
│   │   │   ├── Detection.tsx
│   │   │   ├── SigmaRules.tsx
│   │   │   ├── SigmaRuleDetail.tsx
│   │   │   ├── YaraRules.tsx
│   │   │   └── YaraRuleDetail.tsx
│   │   ├── Reports/
│   │   │   ├── ReportList.tsx
│   │   │   ├── ReportGenerate.tsx
│   │   │   └── ReportPreview.tsx
│   │   ├── Settings/
│   │   │   ├── Settings.tsx
│   │   │   ├── GeneralSettings.tsx
│   │   │   ├── AISettings.tsx
│   │   │   ├── ThreatIntelSettings.tsx
│   │   │   ├── SecuritySettings.tsx
│   │   │   └── StorageSettings.tsx
│   │   ├── About/
│   │   │   └── About.tsx
│   │   └── NotFound/
│   │       └── NotFound.tsx
│   │
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useLogs.ts
│   │   ├── useCases.ts
│   │   ├── useIOCs.ts
│   │   ├── useAI.ts
│   │   ├── useSettings.ts
│   │   ├── useNotifications.ts
│   │   ├── useTheme.ts
│   │   ├── useDebounce.ts
│   │   └── useElectron.ts
│   │
│   ├── context/
│   │   ├── AuthContext.tsx
│   │   ├── ThemeContext.tsx
│   │   └── NotificationContext.tsx
│   │
│   ├── types/
│   │   ├── api.ts              # API response types
│   │   ├── auth.ts
│   │   ├── log.ts
│   │   ├── ioc.ts
│   │   ├── case.ts
│   │   ├── report.ts
│   │   ├── ai.ts
│   │   ├── detection.ts
│   │   └── electron.d.ts
│   │
│   ├── lib/
│   │   ├── utils.ts            # Formatting, date, string helpers
│   │   ├── constants.ts        # App-wide constants
│   │   └── validators.ts       # Zod schemas for forms
│   │
│   └── styles/
│       ├── tokens.css           # CSS custom properties (design tokens)
│       ├── base.css             # Reset, base element styles
│       ├── components.css       # Shared component styles
│       └── animations.css       # Keyframes and transitions
│
├── index.html
├── vite.config.ts
├── tsconfig.json
├── tsconfig.node.json
└── package.json
```

### State Management

- **Server state:** TanStack Query (React Query) — all API data caching, refetching, optimistic updates
- **UI state:** React context for global UI state (theme, notifications, sidebar state)
- **Form state:** React Hook Form + Zod validation
- **Auth state:** AuthContext (user, token, login/logout actions)

### API Client Architecture

```typescript
// api/client.ts
import axios from 'axios'
import { useAuthStore } from './auth'

const API_BASE = window.electronAPI ? 'http://127.0.0.1:8000/api/v1' : '/api/v1'

const client = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' }
  // Note: Content-Type removed for multipart uploads (dropzone overrides per-request)
})

// Request interceptor: attach JWT
client.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Response interceptor: handle 401 → refresh token or logout
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshed = await tryRefreshToken()
      if (refreshed) return client.request(error.config)
      useAuthStore.getState().logout()
    }
    return Promise.reject(error)
  }
)
```

### Routing

```typescript
// react-router-dom v6
const router = createBrowserRouter([
  { path: '/login', element: <Login /> },
  { path: '/register', element: <Register /> },
  {
    path: '/',
    element: <ProtectedRoute><AppShell /></ProtectedRoute>,
    children: [
      { index: true, redirect: '/dashboard' },
      { path: 'dashboard', element: <Dashboard /> },
      { path: 'logs', element: <LogAnalysis /> },
      { path: 'logs/:id', element: <LogDetail /> },
      { path: 'threat-intel', element: <ThreatIntel /> },
      { path: 'ai-copilot', element: <AICopilot /> },
      { path: 'cases', element: <CaseList /> },
      { path: 'cases/:id', element: <CaseDetail /> },
      { path: 'detection', element: <Detection /> },
      { path: 'reports', element: <ReportList /> },
      { path: 'reports/generate/:caseId', element: <ReportGenerate /> },
      { path: 'reports/:id', element: <ReportPreview /> },
      { path: 'settings', element: <Settings /> },
      { path: 'about', element: <About /> },
      { path: '*', element: <NotFound /> }
    ]
  }
])
```

### Error Boundaries

```tsx
// App-level error boundary catches render errors, shows crash screen
// Per-page error boundaries for isolated failures
// API query errors handled by TanStack Query's onError + toast
// Network errors: retry button, offline banner
```

### Theme System

```css
/* styles/tokens.css */
:root {
  /* Dark theme (default) */
  --bg-primary: #0D1117;
  --bg-secondary: #161B22;
  --text-primary: #F0F6FC;
  /* ... all tokens ... */
}

[data-theme="light"] {
  --bg-primary: #FFFFFF;
  --bg-secondary: #F6F8FA;
  --text-primary: #1F2328;
  /* ... all tokens ... */
}
```

---

## 20. Implementation Roadmap

### Phase 1 — Application Shell

- Set up Vite + React + TypeScript + Tailwind
- Folder structure (20.1)
- Router setup with react-router-dom v6
- Theme system (CSS custom properties, dark/light toggle)
- AppShell layout: Sidebar, TopBar, Content area, StatusBar
- Empty state for every page route

### Phase 2 — Design System

- Build all UI primitives: Button, Input, Dropdown, Checkbox, Radio, Tabs, Modal, Drawer, Toast, Alert, Badge, Tooltip, Skeleton, EmptyState, Spinner, ProgressBar, Pagination
- DataTable component with sorting, filtering, pagination, bulk actions, virtual scrolling
- Build layout components: PageHeader, Breadcrumbs, SearchInput
- Build common components: UploadZone, CommandPalette, NotificationCenter, UserMenu, CopyButton

### Phase 3 — Authentication

- Login page with form validation
- Registration page
- MFA setup + MFA login step
- AuthContext + auth store
- API client with JWT interceptor + refresh
- ProtectedRoute component
- First-run setup flow

### Phase 4 — Dashboard

- Dashboard page layout
- StatCard component (4 cards)
- RecentCasesWidget with mini data table
- ActivityWidget with timeline
- Dashboard API hooks + polling

### Phase 5 — Log Analysis

- UploadZone with drag-and-drop
- UploadHistory data table
- LogDetail page with tabs: Events, Timeline, IOCs
- EventTable (virtualized) + filtering
- TimelineView (vertical timeline)
- EventDetail modal/panel
- Log analysis API hooks

### Phase 6 — Threat Intelligence

- ThreatIntel page with IOC table
- IOCDetail panel (enrichment results)
- Batch enrich workflow
- Threat intel API hooks + polling for enrichment status

### Phase 7 — AI Copilot

- AICopilot chat interface
- ChatHistory sidebar (session list)
- ChatMessages (streaming response display)
- ChatInput (provider selector, context attachment, send)
- SSE / streaming integration with AI API
- Save conversations, load history

### Phase 8 — Case Management

- CaseList table
- CaseDetail page with tabs: Overview, Timeline, Evidence, IOCs, Comments
- Evidence upload (drag-and-drop + file picker)
- Comments (threaded, @-mentions)
- Case creation dialog
- Case API hooks

### Phase 9 — Reports

- ReportList table
- ReportGenerate dialog (type, format, template)
- ReportPreview modal/drawer
- Download report (triggers Electron save dialog)
- Report API hooks

### Phase 10 — Settings

- Settings page with sidebar tabs: General, AI, Threat Intel, Security, Storage, About
- AI provider CRUD (add/edit/delete/test)
- Threat intel API key management + test
- Security settings (password, MFA setup/disable)
- Storage stats + cache clearance + backup
- Theme toggle, language, date format preferences

---

## Appendix A — Design Token Reference

```css
/* Complete CSS custom properties for the design system */

:root {
  /* Colors - Primary */
  --color-primary-50: #EBF5FF;
  --color-primary-100: #C7E2FF;
  --color-primary-200: #94C5FF;
  --color-primary-300: #5BA0FF;
  --color-primary-400: #3580F0;
  --color-primary-500: #1F6FEB;
  --color-primary-600: #1558C7;
  --color-primary-700: #0D4196;
  --color-primary-800: #0A2D6B;
  --color-primary-900: #051B40;

  /* Colors - Secondary */
  --color-secondary-50: #E6F9EE;
  --color-secondary-400: #3FB950;
  --color-secondary-500: #2EA043;
  --color-secondary-600: #238636;

  /* Colors - Accent */
  --color-accent-50: #FFF8EB;
  --color-accent-400: #D29922;
  --color-accent-500: #BB8009;
  --color-accent-600: #9E6A03;

  /* Colors - Danger */
  --color-danger-50: #FFEBED;
  --color-danger-400: #F85149;
  --color-danger-500: #DA3633;
  --color-danger-600: #B6231C;

  /* Colors - Info */
  --color-info-50: #F0E8FF;
  --color-info-400: #A371F7;
  --color-info-500: #8957E5;
  --color-info-600: #6E40C9;

  /* Backgrounds */
  --bg-primary: #0D1117;
  --bg-secondary: #161B22;
  --bg-tertiary: #21262D;
  --bg-elevated: #1C2128;
  --bg-overlay: rgba(1, 4, 9, 0.8);

  /* Surfaces */
  --surface-card: #161B22;
  --surface-card-hover: #1C2128;
  --surface-modal: #1C2128;
  --surface-tooltip: #21262D;
  --surface-code: #0D1117;

  /* Borders */
  --border-default: #30363D;
  --border-muted: #21262D;
  --border-accent: #1F6FEB;
  --border-danger: #DA3633;

  /* Text */
  --text-primary: #F0F6FC;
  --text-secondary: #8B949E;
  --text-tertiary: #6E7681;
  --text-link: #58A6FF;
  --text-inverse: #0D1117;
  --text-danger: #F85149;
  --text-success: #3FB950;

  /* Typography */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'Consolas', monospace;

  --text-display: 32px;
  --text-h1: 24px;
  --text-h2: 20px;
  --text-h3: 16px;
  --text-body: 14px;
  --text-body-bold: 14px;
  --text-small: 12px;
  --text-small-bold: 12px;
  --text-micro: 11px;
  --text-code: 13px;
  --text-button: 14px;
  --text-input: 14px;

  /* Spacing */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;

  /* Icons */
  --icon-micro: 12px;
  --icon-small: 16px;
  --icon-medium: 20px;
  --icon-large: 24px;
  --icon-xlarge: 32px;
  --icon-xxlarge: 48px;

  /* Animation */
  --anim-fast: 150ms;
  --anim-normal: 200ms;
  --anim-slow: 300ms;
  --anim-xslow: 500ms;
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
}
```

---

## Appendix B — Consistency Rules

1. **All spacing must use the 4px grid.** Never use arbitrary pixel values.
2. **No color values outside the design token system.** Every color must be a CSS variable.
3. **All interactive elements must have hover, focus, active, and disabled states.**
4. **Every API call must have loading, success, error, and empty state handling.**
5. **No inline styles.** All styles via CSS modules, Tailwind utility classes, or CSS variables.
6. **No `<div>` for buttons.** Use semantic `<button>` or `<a>` with proper ARIA.
7. **All text nodes must use typography tokens.** No ad-hoc font-size declarations.
8. **Icons must be 12/16/20/24/32/48px.** No custom icon sizes.
9. **Tables must use DataTable component.** No ad-hoc table markup.
10. **Modals must trap focus, close on Escape, and return focus on close.**
11. **Every page must have a PageHeader with title + optional actions.**
12. **Loading states must use Skeleton components, not spinner overlays.**
13. **Empty states must include illustration + message + optional CTA.**
14. **Error messages must be user-facing, not technical.**
15. **All forms must use React Hook Form + Zod validation.**
16. **Route transitions must use fade animation (200ms).**
17. **Hover delay for tooltips: 300ms.**
18. **Toast duration: 4s (info/success), 6s (warning), 8s (error).**
19. **File upload: validate extension + size + empty before sending.**
20. **Keyboard shortcuts listed in help modal (Ctrl+/).**
