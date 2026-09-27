# Academy Canonical Landing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `/academy/` the sole authenticated landing page and redirect the legacy root dashboard to it.

**Architecture:** Keep the Academy view and its hash-routed dashboard unchanged as the canonical destination. Replace the root dashboard response with a named-URL redirect and update smoke/browser expectations so navigation has one source of truth.

**Tech Stack:** Django 6.0, Django TestCase, Playwright sync API

**Spec:** `docs/superpowers/specs/2026-09-27-academy-tasks-inventory-integration-design.md`

## Global Constraints

- `/academy/` is the sole canonical authenticated landing page.
- Authenticated `/` requests redirect to `/academy/`.
- `LOGIN_REDIRECT_URL` remains `/academy/`.
- Academy Business Tools continues to use named Django routes and `/academy/#tools` return URLs.
- Do not import prototype sample data or hardcode hosts, ports, user IDs, or CSRF tokens.

## Review Focus

- An anonymous `/` request must still follow Django's login boundary rather than exposing Academy content.
- A `next=/` login must resolve through the root redirect without creating a redirect loop.
- Existing code that reverses `core:dashboard` must receive a valid redirect response.
- Academy `#dashboard` must remain the default client route after the redirect.
- Browser smoke tests must not assume that root contains the removed legacy tile catalogue.

---

### Task 1: Redirect the root route to Academy

**Files:**
- Modify: `apps/core/views.py`
- Modify: `apps/core/tests.py`
- Modify: `tests/browser/test_dummy_users.py`

**Interfaces:**
- Consumes: named route `academy:index`
- Produces: `dashboard_view(request) -> HttpResponseRedirect` for authenticated requests

- [ ] **Step 1: Write the failing root redirect tests**

Add `CoreLandingTests.test_authenticated_root_redirects_to_academy`, `test_anonymous_root_redirects_to_login`, and `test_academy_remains_default_dashboard` in `apps/core/tests.py`. Assert authenticated `/` returns 302 with `/academy/`, anonymous `/` returns the login redirect, and `/academy/` contains `Academy Dashboard` configuration.

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `.venv\Scripts\python.exe manage.py test apps.core.tests.CoreLandingTests -v 2`

Expected: authenticated root assertion fails because the legacy dashboard returns 200.

- [ ] **Step 3: Implement the named redirect**

Change `dashboard_view(request)` in `apps/core/views.py` to return `redirect('academy:index')` after `login_required`. Remove its unused dashboard-service import. Keep `core:dashboard` and `core:dashboard_alt` route names for compatibility.

- [ ] **Step 4: Update root smoke expectations**

Change the existing root assertions in `apps/core/tests.py` and `tests/browser/test_dummy_users.py` to follow or explicitly assert the `/academy/` redirect. Keep all module-route and role checks against the Academy Business Tools route rather than the removed root catalogue.

- [ ] **Step 5: Run focused and browser-source tests**

Run: `.venv\Scripts\python.exe manage.py test apps.core.tests apps.academy.tests -v 2`

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add apps/core/views.py apps/core/tests.py tests/browser/test_dummy_users.py
git commit -m "feat: make academy the canonical landing page"
```

