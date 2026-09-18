# Full Academy Functionality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the Django Academy with persistent learning/certificates, admin-driven taxonomies/resources/diagnostics, funding CSV import, events, mentor messaging, and a moderated forum.

**Architecture:** Extend `apps.academy` as the bounded domain. Admin owns catalogue configuration; authenticated DRF endpoints own learner actions; service functions calculate grades/certificates and import CSV atomically. The existing Academy shell renders API data and never trusts client-supplied user identifiers or completion status.

**Tech Stack:** Django 6.0.4, DRF 3.17.1, Django admin, SQLite development migrations, vanilla JavaScript.

**Spec:** `Master Plan.md` section 21

## Global Constraints

- Work in the current `main` workspace as explicitly approved.
- Use test-first development and additive migrations.
- Marketing is out of scope.
- All writes require authentication and CSRF/session or token authentication.
- Forum/message authors are always assigned from `request.user`.
- CSV imports validate every row before writing any row.
- Certificates are server-generated and unique per passed enrolment.

---

### Task 1: Learning completion and certificates

**Status: implemented.**

Create admin taxonomies, enrolments, progress, quiz attempts, certificates, service rules, migrations, admin screens, APIs, and tests. Completion requires all published required modules; required quiz-module scores must meet the course passing grade.

### Task 2: Resources and diagnostics

**Status: implemented.**

Create admin-owned resource categories/resources and versioned diagnostic categories/questions/options/submissions. Add published read APIs, authenticated submission APIs, filtering, and tests.

### Task 3: Funding CSV and events

**Status: implemented.**

Create opportunity/event taxonomies and records, atomic CSV validation/import with admin preview and template download, event registrations, APIs, and tests.

### Task 4: Mentorship and messaging

**Status: implemented.**

Create mentor profiles, bookings, private conversations/messages, participant-only query rules, admin management, APIs, and tests.

### Task 5: Community forum

**Status: implemented.**

Create admin categories, posts/replies, authenticated identity assignment, filters, ownership/moderation rules, APIs, and tests.

### Task 6: Academy frontend and verification

**Status: implemented and automated verification complete; interactive browser smoke testing remains environment-dependent.**

Make each Academy hash page fetch its API, implement functional forms/filters/error states, update documentation, apply migrations, run the full test suite, and perform browser smoke testing when available.
