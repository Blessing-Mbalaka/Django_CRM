# JBS CRM — System Workflow & Architecture Guide

**University of Johannesburg · Business School**
**Phase 1 | Django 6 · DRF · SQLite**

---

## 1. Project Overview

The JBS CRM is a **modular, API-first Institutional Intelligence Platform** built on Django with Django REST Framework. It gives the CEO executive-level oversight of clients, engagements, finances, and risk — while enabling staff to manage their own portfolios.

---

## 2. Technology Stack

| Layer            | Technology                          |
|------------------|-------------------------------------|
| Backend          | Django 6.0 (Python 3.12)            |
| API              | Django REST Framework 3.17          |
| Database         | SQLite (Phase 1) → PostgreSQL later |
| Auth             | Django Auth + Role-Based Permissions|
| Frontend         | Django Templates + Bootstrap 5      |
| Styling          | UJ Design System (custom CSS)       |
| CORS             | django-cors-headers                 |
| Forms            | crispy-forms + crispy-bootstrap5    |

---

## 3. UJ Design System

### Colour Palette

| Token              | Hex       | Usage                              |
|--------------------|-----------|------------------------------------|
| `--uj-orange`      | `#F05A22` | Primary brand, buttons, accents    |
| `--uj-orange-dark` | `#C44B1B` | Hover states, active borders       |
| `--uj-orange-tint` | `#FEF3EE` | Card headers, table row highlights |
| `--uj-white`       | `#FFFFFF` | Backgrounds, cards                 |
| `--uj-text`        | `#1A1A2E` | Body text (high contrast WCAG AA)  |
| `--uj-sidebar`     | `#1E1E2E` | Sidebar background                 |

### Design Principles Applied

- **Affordance** — All interactive elements (buttons, links, table rows) signal clickability via hover colour shifts, cursor pointer, and orange border reveals.
- **Usability** — Consistent layout: sidebar + topbar shell, breadcrumbs, page titles, sticky topbar. Toast messages auto-dismiss but pause on hover.
- **Accessibility (WCAG 2.1 AA)** — Skip navigation link, `aria-label` on all interactive elements, `role` attributes on landmarks, `aria-current="page"` on active nav, focus-visible outlines, semantic HTML tables with `scope` and `aria-label`.

---

## 4. Modular App Architecture

Each major domain is its own Django app inside `apps/`:

```
apps/
├── accounts/       → Login, logout, custom User model, roles, profile
├── core/           → Dashboard (CEO view), home page
├── admin_panel/    → System administration, user management
├── staff/          → Staff directory, roles, department allocation
├── centres/        → Department profiles, KPIs, director assignment (legacy package name)
├── clients/        → Client & stakeholder register
├── engagements/    → Engagement lifecycle management
├── finance/        → Revenue, pipeline, financial records
├── alerts/         → Risk alerts, automated notifications
├── analytics/      → Reporting, forecasting (Phase 2 charts)
├── communication/  → Contact logs, relationship health
└── api/            → DRF API router — all endpoints
```

**Rule:** Views are thin. All business logic lives in `functionalities/`.

---

## 5. Strict Layering Rules

```
Request → urls.py → views.py → functionalities/*/services.py → models.py → DB
                                                             ↓
                                                       serializers.py → API
```

| Layer                 | Responsibility                                      |
|-----------------------|-----------------------------------------------------|
| `views.py`            | Auth check, call service, return response. Nothing else. |
| `functionalities/*/services.py` | All business logic (aggregations, rules)  |
| `models.py`           | Schema definition + simple computed properties      |
| `serializers.py`      | DRF serialization + field display names             |
| `forms.py`            | Input validation + widget styling                   |
| `urls.py`             | URL routing only                                    |

---

## 6. Business Logic Rules

### Engagement Rules
- Every engagement must have a **lead owner**
- No duplicate client engagements across departments (to prevent overlap)
- `last_contact` date tracked; `days_since_contact` auto-computed
- Lifecycle: `prospect → active → on_hold → closed / lost`

### Visibility Rules
| Level           | Access                              |
|-----------------|-------------------------------------|
| `private`       | Assigned staff only                 |
| `shared`        | All staff in the same department    |
| `institutional` | CEO-level access (all data)         |

### Alert Rules
- No contact > 30 days: `MEDIUM` alert
- No contact > 60 days: `HIGH` alert
- No contact > 90 days: `CRITICAL` alert
- Overdue payment: `HIGH` financial alert
- Engagement overlap on same client: `MEDIUM` overlap alert

---

## 7. System Workflow

### 7.1 Login Flow
```
GET /accounts/login/ → LoginForm rendered
POST credentials → Django authenticates → messages.success("Welcome back")
→ redirect to /dashboard/
Role-based dashboard:
  CEO      → Full institutional view (all clients, all departments)
  Director → Department-scoped view
  Staff    → Personal engagement portfolio
```

### 7.2 Dashboard Load
```
GET /dashboard/ → core.views.dashboard_view()
→ calls functionalities/crm_core/services.get_dashboard_context(user)
→ queries: Client.count(), Engagement.filter(active).count(),
           FinancialRecord.sum(pipeline), Alert.filter(unresolved).count()
→ renders core/dashboard.html with KPI stat cards + recent engagements + alerts
```

### 7.3 Client → Engagement Creation Flow
```
1. POST /clients/new/         → ClientForm → Client.save()  → toast: "Client created"
2. POST /engagements/new/     → EngagementForm (links client + staff + centre)
                              → Engagement.save() → toast: "Engagement created"
3. System auto-creates alert tracking for last_contact date
```

### 7.4 Engagement Lifecycle Updates
```
Prospect → Active:   staff updates engagement.status → Dashboard KPI updates
Active → On Hold:    risk check triggered → alert may be created
Active → Closed:     financial record marked is_paid → revenue updated
Any state:           last_contact updated → days_since_contact resets
```

### 7.5 Financial Tracking Flow
```
Engagement created → FinancialRecord(record_type='pipeline') added
Work confirmed    → record_type changed to 'revenue', is_paid=False
Payment received  → is_paid=True
Dashboard shows:
  pipeline_value = SUM(pipeline records)
  revenue = SUM(revenue records, is_paid=True)
```

### 7.6 Alert Generation
```
Scheduled task (Phase 2: Celery/Beat) OR manual check:
→ functionalities/alerts/services.py scans all active engagements
→ if days_since_contact > threshold: Alert.objects.create(...)
→ Alert appears in sidebar badge + /alerts/ list + dashboard widget
```

### 7.7 API Flow
```
GET /api/                → api_root view → JSON index of all endpoints
GET /api/clients/        → ClientViewSet.list() → paginated JSON
GET /api/clients/1/      → ClientViewSet.retrieve() → single record JSON
POST /api/clients/       → ClientSerializer.validate() → save()
→ Browsable API at /api/ (DRF BrowsableAPIRenderer enabled)
→ Token auth: Authorization: Token <token_key>
→ Session auth: cookies (for browser-based use)
```

---

## 8. REST API Reference

| Endpoint               | Method     | Description                        |
|------------------------|------------|------------------------------------|
| `/api/`                | GET        | API root — index of all endpoints  |
| `/api/clients/`        | GET, POST  | List/create clients                |
| `/api/clients/{id}/`   | GET, PUT, PATCH, DELETE | Client CRUD          |
| `/api/engagements/`    | GET, POST  | List/create engagements            |
| `/api/departments/`    | GET, POST  | List/create departments            |
| `/api/staff/`          | GET        | Staff directory                    |
| `/api/finance/`        | GET, POST  | Financial records                  |
| `/api/alerts/`         | GET, POST  | Alerts management                  |
| `/api/users/`          | GET        | User list (admin only)             |
| `/api-auth/login/`     | POST       | DRF session login                  |

**Authentication:**
```http
Authorization: Token <your_token>
```

---

## 9. Database Schema (Phase 1 — SQLite)

```
User ─────────────────── accounts_user
Centre ────────────────── centres_centre (→ director FK → User)
StaffProfile ──────────── staff_staffprofile (→ user FK → User, → centre FK)
Client ────────────────── clients_client (→ centre FK, → lead_owner FK → User)
Engagement ────────────── engagements_engagement (→ client FK, → centre FK, → lead_owner FK)
FinancialRecord ────────── finance_financialrecord (→ engagement FK)
Alert ──────────────────── alerts_alert (→ engagement FK, → client FK)
CommunicationLog ─────── communication_communicationlog (→ engagement FK, → logged_by FK)
```

---

## 10. Setup & Run (Phase 1)

```bash
# 1. Activate virtual environment
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply migrations
python manage.py migrate

# 4. Create superuser (CEO account)
python manage.py createsuperuser

# 5. Run development server
python manage.py runserver

# 6. Access the system
http://localhost:8000/            → Login page
http://localhost:8000/dashboard/  → CEO Dashboard
http://localhost:8000/api/        → Browsable REST API
http://localhost:8000/admin/      → Django Admin
```

---

## 11. Phase Roadmap

| Phase | Scope                                                                |
|-------|----------------------------------------------------------------------|
| **1** | ✅ Django project + modular apps + UJ design + SQLite + DRF         |
| **2** | PostgreSQL migration, Celery alert generation, Charts (Chart.js)    |
| **3** | Advanced analytics, AI-powered risk scoring, engagement predictions |
| **4** | Mobile-optimised views, PDF report export, email notifications      |

---

## 12. File Structure Reference

```
CRM/
├── .venv/                        ← Python virtual environment
├── jbs_crm/                      ← Django project package
│   ├── settings/
│   │   ├── base.py               ← All shared settings
│   │   └── development.py        ← Dev overrides
│   └── urls.py                   ← Root URL config
├── apps/                         ← All Django apps (one per domain)
│   ├── accounts/                 ← Auth, login, custom User
│   ├── core/                     ← Dashboard, home
│   ├── admin_panel/              ← System admin
│   ├── staff/                    ← People management
│   ├── centres/                  ← Department management (legacy package name)
│   ├── clients/                  ← Client register
│   ├── engagements/              ← Engagement lifecycle
│   ├── finance/                  ← Financial tracking
│   ├── alerts/                   ← Risk alerts
│   ├── analytics/                ← Reports
│   ├── communication/            ← Contact logs
│   └── api/                      ← DRF router
├── functionalities/              ← All business logic
│   └── crm_core/services.py      ← Dashboard aggregations
├── templates/                    ← All HTML templates
│   ├── base.html                 ← Shell: sidebar + topbar + toasts
│   ├── partials/
│   │   ├── _sidebar.html
│   │   ├── _navbar.html
│   │   └── _toasts.html          ← Django messages → UJ toast cards
│   ├── accounts/login.html
│   └── core/dashboard.html
├── static/
│   ├── css/uj_theme.css          ← UJ design system
│   ├── js/main.js                ← Toast JS, sidebar toggle
│   └── images/uj_logo.png
├── db.sqlite3                    ← SQLite database
├── manage.py
├── requirements.txt
└── workflow.md                   ← This file
```

---

*JBS Institutional CRM — University of Johannesburg · Phase 1 · April 2026*
