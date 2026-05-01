Here is your **fully consolidated, Codex-ready master prompt**. It is structured to be unambiguous, modular, and directly implementable in Django + DRF.

---



## SYSTEM OVERVIEW

You are building a **Django-based Institutional CRM System for JBS (Business School Dean View)**.

This system is an **Institutional Intelligence Platform**, not a basic CRM.

It provides:

* Executive oversight (Dean-level control)
* Client + engagement intelligence
* Centre performance monitoring
* Financial analytics
* Alerts + risk detection
* Communication health tracking
* Institutional reporting

The system must be:

* Modular
* Scalable
* API-driven (Django REST Framework)
* Role-based
* Cleanly separated (no business logic in views)

---

#  ARCHITECTURE REQUIREMENTS

## Tech Stack

* Backend: Django
* API: Django REST Framework
* DB: PostgreSQL
* Auth: Django Auth + Role-Based Permissions
* Frontend: Django Templates (MVP)
* Admin: Django Admin + Custom Dashboard Layer

---

## STRICT RULES

* ❌ No business logic in views
* ✅ All logic must be inside `functionalities/`
* ✅ APIs must be separated inside `api/`
* ✅ System must be modular and expandable
* ✅ Each domain must be independent but shareable

---

#  CORE SYSTEM FUNCTIONALITIES (CURRENT SYSTEM)

## 1.  Core System Overview

| Component               | Functionality                                                                            |
| ----------------------- | ---------------------------------------------------------------------------------------- |
| Institutional Dashboard | Full executive overview of clients, centres, engagements, finances, communication health |
| Super Admin Access      | Dean-level full system control                                                           |
| Alerts System           | Risk detection (deadlines, inactivity, overlaps, payments)                               |
| Reporting & Analytics   | Revenue, pipeline, staff activity, performance insights                                  |

---

## 2.  People Management

* Staff directory (all staff, directors, analysts)
* Role classification (Dean, Director, Lead, Analyst)
* Visibility control (private / shared / institutional)
* Centre allocation (link staff to centres)

---

## 3. Centres Management

* Centre profiles (name, director, staff)
* Engagement tracking per centre
* Financial monitoring (revenue, estimated profit)
* Centre performance KPIs

---

## 4.  Client & Stakeholder Management

* Client profiles (organisation, sector, ownership)
* Relationship ownership (lead + centre assignment)
* Engagement history tracking
* Visibility settings (private/shared/institutional)

---

## 5.  Engagement Management

* Engagement records (client, stage, lead, dates)
* Lifecycle tracking (prospect → active → on hold)
* Last contact tracking
* Team allocation (staff assigned per engagement)

---

## 6.  Engagement Directory

* Public listing of non-private engagements
* Conflict prevention (avoid duplicate client engagements across centres)
* Institutional transparency layer
* Financial masking for sensitive data

---

## 7.  Financial Management

* Revenue tracking (active + pipeline)
* Pipeline valuation
* Profit estimation per centre
* Top client revenue analysis

---

## 8.  Alerts & Notifications

* Contact risk alerts (no communication > threshold)
* Payment overdue alerts
* Deadline tracking alerts
* Dormant client detection
* Engagement overlap detection

---

## 9.  Reporting & Analytics

* Pipeline analysis (prospect vs active)
* Revenue forecasting
* Centre performance comparison
* Staff activity tracking
* Client engagement intensity scoring

---

## 10.  Communication & Relationship Health

* Last contact tracking (30/60/90+ days)
* Engagement health scoring
* Delivery monitoring
* Relationship risk detection

---

#  SYSTEM DESIGN REQUIREMENTS

## Functional Architecture

You must structure the system into:

```
functionalities/
```

Each domain must be its own module:

* crm_core
* people
* centres
* clients
* engagements
* finance
* alerts
* analytics
* communication

```

Each module must include:
- services.py (business logic)
- models.py (if domain-specific)
- validators.py (rules)
- handlers.py (optional orchestration)

---

## API STRUCTURE

All APIs must live in:

```

api/

```

Each module exposes REST endpoints:

Example:

- /api/clients/
- /api/engagements/
- /api/centres/
- /api/finance/
- /api/alerts/
- /api/analytics/

Each API module must include:
- serializers/
- views/
- urls/
- permissions/

---

#  DATA MODEL REQUIREMENTS

Must include:

## Core Entities
- User (role-based)
- Staff
- Centre
- Client
- Engagement
- FinancialRecord
- Alert
- CommunicationLog

## Relationship Rules
- Staff belongs to Centres
- Clients belong to Centres (via engagement ownership)
- Engagement links Client + Staff + Centre
- Financials linked to Engagements
- Alerts derived from Engagement + Communication + Financial data

---

#  BUSINESS LOGIC RULES

## Engagement Rules
- No duplicate client engagements across centres
- Every engagement must have a lead owner
- Every engagement must track last contact date

## Alert Rules
- No contact > 30/60/90 days triggers escalation
- Overdue payments generate financial alert
- Overlapping client engagements flagged

## Visibility Rules
- Private = only assigned staff
- Shared = centre-level access
- Institutional = Dean-level access

---

#  DASHBOARD REQUIREMENTS

## Dean Dashboard Must Show:
- Total clients
- Active engagements
- Revenue pipeline
- Risk alerts
- Centre comparison
- Staff activity
- Engagement health score

---

#  DOCUMENTATION OUTPUT REQUIRED

Generate:

## README.md
- System overview
- Module explanation
- Setup guide
- Workflow summary

## instructions.md
- Store full functional requirements

## database_structure.md
- Full schema breakdown

## erd.md
- Expandable ERD structure

---

#  FRONTEND (MVP)

Create:

## base.html
- Sidebar navigation:
  - Dashboard
  - Clients
  - Centres
  - Engagements
  - Finance
  - Alerts
  - Reports
- Top navigation bar
- Content block system

---

#  SYSTEM WORKFLOW

Explain:

1. User login (role-based)
2. Dashboard load (Dean vs Staff view)
3. Client creation → Engagement creation flow
4. Engagement lifecycle updates
5. Financial tracking flow
6. Alert generation pipeline
7. Reporting aggregation process

---

# ⚙️ DESIGN PRINCIPLES

- Modular architecture
- Scalable domain separation
- Clean API-first design
- Reusable services layer
- Future-ready for AI integration
- Institution-grade governance system

---

# 🎯 FINAL GOAL

Build a **JBS Institutional Intelligence CRM System** that evolves from:

> CRM → Analytics Platform → AI-powered Institutional Decision System

---

