# Marketing and Communications Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the `/growth/` placeholder with the complete database-backed Marketing workspace and real, environment-configured Twilio and Meta delivery adapters.

**Architecture:** Add an isolated `apps.marketing` Django domain and a `functionalities.marketing` service package. Persist planning, contacts, consent, content, metrics, delivery attempts, and webhook events locally; route all external operations through provider adapters and one transactional dispatcher used by both immediate and scheduled sends.

**Tech Stack:** Python 3.12, Django 6.0.4, Django REST Framework 3.17.1, requests 2.34.2, Twilio Python 9.11.1, vanilla ES modules, native `<dialog>`, Django TestCase/APITestCase, Playwright

**Spec:** `docs/superpowers/specs/2026-09-28-marketing-communications-integration-design.md`

## Global Constraints

- `/growth/` is the only Marketing application route; remove the existing placeholder and every prototype-file link.
- Keep implementation files inside `apps/marketing`, `functionalities/marketing`, `templates/marketing`, and `static/sme/marketing` except required project registration, dependency, environment-example, Academy-link, and documentation edits.
- Do not load `SMEs (3)/SMEs/marketing-app/js/data.js`, use `localStorage`, or import prototype sample metrics.
- Provider credentials come only from environment variables and must never reach browser JSON, database rows, logs, fixtures, or test output.
- Missing credentials must not prevent Django startup, migrations, tests, or Marketing read/planning features.
- External calls require explicit connect/read timeouts and mocked tests; automated tests never perform real sends or publishing.
- Marketing writes and every send, schedule, retry, cancel, Brand Kit change, and CRM lead conversion require CEO, Director, or System Administrator permissions.
- Outbound marketing requires an affirmative per-channel consent state and must reject opted-out contacts.
- Provider acceptance is not delivery; only verified provider events/status responses advance delivery states.
- Use `requests==2.34.2` and `twilio==9.11.1`, current verified releases as of 28 September 2026.
- Preserve unrelated working-tree changes, including existing `docs/uat/` and any pre-existing documentation/template edits; stage only plan-scoped files.

## Review Focus

- A single missing variable must mark only that provider `not_configured`, without exposing other configured secret values or disabling planning features.
- A scheduler crash or concurrent scheduler process must not send the same `OutboundMessage` twice.
- Opted-out, malformed, or channel-incompatible contacts must fail before any provider call.
- Duplicate or out-of-order webhook events must be idempotent and must not regress a terminal delivery status.
- Instagram/Facebook media whose URL is not publicly reachable over HTTPS must remain previewable but must not be published.

---

### Task 1: Add the isolated Marketing app and durable domain schema

**Files:**
- Create: `apps/marketing/__init__.py`
- Create: `apps/marketing/apps.py`
- Create: `apps/marketing/models.py`
- Create: `apps/marketing/admin.py`
- Create: `apps/marketing/views.py`
- Create: `apps/marketing/urls.py`
- Create: `apps/marketing/migrations/0001_initial.py`
- Create: `apps/marketing/tests/__init__.py`
- Create: `apps/marketing/tests/test_models.py`
- Modify: `jbs_crm/settings/base.py`
- Modify: `jbs_crm/urls.py`
- Modify: `apps/core/urls.py`
- Modify: `apps/core/views.py`

**Interfaces:**
- Produces models: `MarketingCampaign`, `MarketingAdvert`, `MarketingContent`, `MarketingContact`, `MarketingLead`, `MarketingActivity`, `MarketingMetric`, `BrandKit`, `OutboundMessage`, `DeliveryAttempt`, `ProviderWebhookEvent`
- Produces route namespace: `marketing`, mounted at `/growth/`
- Produces upload paths: `marketing/content/YYYY/MM/` and `marketing/brand/`

- [ ] **Step 1: Write failing model tests**

Add distinct tests for campaign date ordering, non-negative budgets/metrics, Brand Kit singleton loading, five-megabyte/type-checked uploads, opted-out contact semantics, unique webhook event identity, immutable outbound destination/content snapshots after creation, and delivery status choices.

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `.venv\Scripts\python.exe manage.py test apps.marketing.tests.test_models -v 2`

Expected: FAIL because `apps.marketing` and its models do not exist.

- [ ] **Step 3: Implement and register the models**

Implement the fields and constraints from spec section 4. Add `MarketingConfig`, register `apps.marketing`, create admin registrations with safe list/search fields, and generate the initial migration. Model `clean()` methods own cross-field date, opt-out, and relationship validation; database constraints own non-negative numeric values and webhook uniqueness.

- [ ] **Step 4: Move canonical routing ownership to Marketing**

Mount `apps.marketing.urls` at `/growth/`, remove the `growth_marketing_view` and route from Core, and leave the Marketing page view login-protected. Do not delete or replace the final template until Task 7.

- [ ] **Step 5: Run model and migration checks**

Run: `.venv\Scripts\python.exe manage.py test apps.marketing.tests.test_models -v 2`

Run: `.venv\Scripts\python.exe manage.py makemigrations --check --dry-run`

Expected: model tests PASS and no model changes remain pending.

- [ ] **Step 6: Commit**

```powershell
git add apps/marketing jbs_crm/settings/base.py jbs_crm/urls.py apps/core/urls.py apps/core/views.py
git commit -m "feat: add marketing domain models"
```

### Task 2: Add provider configuration, safe status reporting, dependencies, and environment guidance

**Files:**
- Create: `functionalities/marketing/__init__.py`
- Create: `functionalities/marketing/providers/__init__.py`
- Create: `functionalities/marketing/providers/base.py`
- Create: `functionalities/marketing/providers/status.py`
- Create: `apps/marketing/tests/test_provider_status.py`
- Modify: `jbs_crm/settings/base.py`
- Modify: `.env.example`
- Modify: `requirements.txt`

**Interfaces:**
- Produces: `ProviderState(str, Enum)` with `available`, `not_configured`, `unavailable`, `temporarily_failing`
- Produces: `ProviderStatus(provider: str, state: ProviderState, message: str, missing: tuple[str, ...])`
- Produces: `ProviderResult(provider_id: str, status: str, metadata: dict, retryable: bool)`
- Produces: `ProviderError(message, *, retryable: bool, status_code: int | None = None, safe_details: dict | None = None)`
- Produces: `provider_status(*, probe: bool = False) -> dict[str, ProviderStatus]`

- [ ] **Step 1: Write failing configuration/status tests**

Test a fully empty environment, each complete provider configuration, one missing variable at a time, SMS sender-number versus Messaging-Service alternatives, redaction of credential values, and a failing optional capability probe. Assert other providers remain independently usable.

- [ ] **Step 2: Run the tests and verify RED**

Run: `.venv\Scripts\python.exe manage.py test apps.marketing.tests.test_provider_status -v 2`

Expected: FAIL because provider interfaces do not exist.

- [ ] **Step 3: Add optional settings and provider primitives**

Read every spec section 7 variable with an empty/default-safe `django-environ` value. Implement immutable provider result/status types, required-variable groups, alternative-variable rules, safe status messages, and a default `probe=False` path that performs no external I/O.

- [ ] **Step 4: Document environment setup explicitly**

Append the exact grouped `.env.example` sections from the spec, including comments explaining where each key is created, sender/domain prerequisites, permanent versus short-lived Meta tokens, callback/public HTTPS requirements, and official documentation links. Do not add real-looking secret examples.

- [ ] **Step 5: Pin provider dependencies**

Add `requests==2.34.2` and `twilio==9.11.1` to `requirements.txt`, install them in the project virtual environment, and verify imports.

- [ ] **Step 6: Run focused tests**

Run: `.venv\Scripts\python.exe manage.py test apps.marketing.tests.test_provider_status -v 2`

Expected: PASS with no network access.

- [ ] **Step 7: Commit**

```powershell
git add functionalities/marketing jbs_crm/settings/base.py .env.example requirements.txt apps/marketing/tests/test_provider_status.py
git commit -m "feat: configure marketing providers"
```

### Task 3: Implement Twilio Email and SMS adapters

**Files:**
- Create: `functionalities/marketing/providers/twilio_email.py`
- Create: `functionalities/marketing/providers/twilio_sms.py`
- Create: `apps/marketing/tests/test_twilio_providers.py`

**Interfaces:**
- Consumes: `ProviderResult`, `ProviderError`, Django Twilio settings, and an `OutboundMessage` snapshot
- Produces: `send_email(message: OutboundMessage) -> ProviderResult`
- Produces: `fetch_email_operation(operation_id: str) -> ProviderResult`
- Produces: `send_sms(message: OutboundMessage) -> ProviderResult`
- Produces: `validate_twilio_request(*, url: str, params: dict, signature: str) -> bool`

- [ ] **Step 1: Write failing Twilio Email tests**

Mock `requests.post` and assert the exact `https://comms.twilio.com/v1/Emails` endpoint, API-key Basic Auth, sender/recipient/content structure, timeout tuple, optional scheduling/tags, `202` operation persistence shape, `400` non-retryability, `429` retryability, `503` retryability, timeout retryability, malformed JSON handling, and no credentials in exceptions.

- [ ] **Step 2: Write failing Twilio SMS tests**

Mock the Twilio client and assert API-key client construction with Account SID, E.164 destination validation, sender-number and Messaging-Service alternatives, callback URL, message SID/status normalization, missing sender rejection before SDK calls, trial/provider errors, and retry classification.

- [ ] **Step 3: Run the tests and verify RED**

Run: `.venv\Scripts\python.exe manage.py test apps.marketing.tests.test_twilio_providers -v 2`

Expected: FAIL on missing adapters.

- [ ] **Step 4: Implement Twilio Email**

Use `requests` with Basic Auth, JSON payloads, and `(5, 30)` connect/read timeouts. Accept only `202`; normalize validation/auth/rate/server/network errors according to the spec. Include a plain-text alternative and marketing campaign tag where available.

- [ ] **Step 5: Implement Twilio SMS and signature validation**

Use `twilio.rest.Client(api_key, api_secret, account_sid=account_sid)` for production sending. Pass exactly one of `from_` or `messaging_service_sid`. Use `twilio.request_validator.RequestValidator` for webhook signatures rather than a custom signature algorithm.

- [ ] **Step 6: Run focused tests**

Run: `.venv\Scripts\python.exe manage.py test apps.marketing.tests.test_twilio_providers -v 2`

Expected: PASS with zero external requests.

- [ ] **Step 7: Commit**

```powershell
git add functionalities/marketing/providers apps/marketing/tests/test_twilio_providers.py
git commit -m "feat: add Twilio marketing providers"
```

### Task 4: Implement Meta WhatsApp, Facebook, and Instagram adapters

**Files:**
- Create: `functionalities/marketing/providers/meta_common.py`
- Create: `functionalities/marketing/providers/meta_whatsapp.py`
- Create: `functionalities/marketing/providers/meta_facebook.py`
- Create: `functionalities/marketing/providers/meta_instagram.py`
- Create: `apps/marketing/tests/test_meta_providers.py`

**Interfaces:**
- Consumes: `ProviderResult`, `ProviderError`, Meta settings, and `OutboundMessage`
- Produces: `send_whatsapp(message: OutboundMessage) -> ProviderResult`
- Produces: `publish_facebook_post(message: OutboundMessage) -> ProviderResult`
- Produces: `create_instagram_container(message: OutboundMessage) -> ProviderResult`
- Produces: `publish_instagram_media(container_id: str) -> ProviderResult`
- Produces: `validate_meta_signature(*, raw_body: bytes, signature_header: str) -> bool`

- [ ] **Step 1: Write failing Meta adapter tests**

Assert versioned Graph URLs, bearer authentication, `(5, 30)` timeouts, WhatsApp phone-number ID/message payloads and returned `wamid`, template versus text validation, Facebook Page feed publishing, Instagram container then publish order, publicly reachable HTTPS media validation, token/permission errors, rate limiting, timeouts, and secret redaction.

- [ ] **Step 2: Write failing signature tests**

Assert valid/invalid/missing `X-Hub-Signature-256`, constant-time comparison, and empty-app-secret rejection.

- [ ] **Step 3: Run the tests and verify RED**

Run: `.venv\Scripts\python.exe manage.py test apps.marketing.tests.test_meta_providers -v 2`

Expected: FAIL because Meta adapters do not exist.

- [ ] **Step 4: Implement shared Meta request handling and WhatsApp**

Centralize the Graph base URL, authorization header, timeout, JSON parsing, and normalized error mapping in `meta_common.py`. Implement WhatsApp text/template payload validation without weakening provider requirements.

- [ ] **Step 5: Implement Facebook and Instagram publishing**

Facebook publishes only to the configured Page. Instagram rejects local/private/non-HTTPS media URLs before making a provider request, creates a container, verifies creation response, and then publishes it.

- [ ] **Step 6: Implement Meta signature validation**

Validate the `sha256=` signature over the raw body with `META_APP_SECRET` using HMAC-SHA256 and `hmac.compare_digest`.

- [ ] **Step 7: Run focused tests**

Run: `.venv\Scripts\python.exe manage.py test apps.marketing.tests.test_meta_providers -v 2`

Expected: PASS.

- [ ] **Step 8: Commit**

```powershell
git add functionalities/marketing/providers apps/marketing/tests/test_meta_providers.py
git commit -m "feat: add Meta marketing providers"
```

### Task 5: Add transactional dispatch, scheduling, status synchronization, and signed webhooks

**Files:**
- Create: `functionalities/marketing/dispatch.py`
- Create: `functionalities/marketing/scheduling.py`
- Create: `functionalities/marketing/webhooks.py`
- Create: `apps/marketing/webhook_views.py`
- Create: `apps/marketing/management/__init__.py`
- Create: `apps/marketing/management/commands/__init__.py`
- Create: `apps/marketing/management/commands/send_due_marketing.py`
- Create: `apps/marketing/tests/test_dispatch.py`
- Create: `apps/marketing/tests/test_webhooks.py`
- Modify: `apps/marketing/urls.py`

**Interfaces:**
- Consumes: provider functions from Tasks 3–4 and delivery models from Task 1
- Produces: `queue_message(...) -> OutboundMessage`
- Produces: `dispatch_message(message_id: int) -> OutboundMessage`
- Produces: `dispatch_due_marketing(*, limit: int = 100) -> DispatchSummary`
- Produces: `retry_message(*, message: OutboundMessage, actor) -> OutboundMessage`
- Produces: `cancel_message(*, message: OutboundMessage, actor) -> OutboundMessage`
- Produces webhook routes: `marketing:twilio-status-webhook` and `marketing:meta-webhook`

- [ ] **Step 1: Write failing dispatcher and consent tests**

Cover each channel adapter selection, persisted snapshot before adapter invocation, opted-out and malformed destination rejection before provider calls, accepted versus delivered distinction, attempt creation, sanitized errors, retryable versus terminal failure, maximum attempts, cancellation, and management actor requirements.

- [ ] **Step 2: Write failing scheduler concurrency tests**

Cover due/future/cancelled selection, deterministic ordering, batch limit, processing claims, a simulated adapter crash, recovery of stale processing claims, and two dispatch calls not sending one row twice. Use `TransactionTestCase` for locking-sensitive behavior and document SQLite serialization versus production row locks.

- [ ] **Step 3: Write failing webhook tests**

Cover Twilio valid/invalid signatures, Meta verification challenge, Meta valid/invalid signatures, duplicate event digests, unknown provider IDs, out-of-order events, terminal-state non-regression, and bounded payload storage.

- [ ] **Step 4: Run the tests and verify RED**

Run: `.venv\Scripts\python.exe manage.py test apps.marketing.tests.test_dispatch apps.marketing.tests.test_webhooks -v 2`

Expected: FAIL on missing dispatch and webhook interfaces.

- [ ] **Step 5: Implement queueing and dispatch**

Create immutable snapshots, claim messages inside `transaction.atomic()`, create an attempt before provider I/O, and finalize result/error state in a second atomic update. Use compare-and-update state guards so a second worker cannot claim an already-processing record.

- [ ] **Step 6: Implement scheduling and the management command**

Implement bounded due-message dispatch and stale-claim recovery. Add `--limit`, a non-negative validation, per-message error isolation, and a deterministic summary printed by `send_due_marketing`.

- [ ] **Step 7: Implement signed, idempotent webhooks**

Use CSRF exemption only on the two provider endpoints. Verify signatures before parsing/updating, hash events without stable IDs, persist deduplication records, and apply monotonic status transitions.

- [ ] **Step 8: Run focused tests**

Run: `.venv\Scripts\python.exe manage.py test apps.marketing.tests.test_dispatch apps.marketing.tests.test_webhooks -v 2`

Expected: PASS.

- [ ] **Step 9: Commit**

```powershell
git add functionalities/marketing apps/marketing/webhook_views.py apps/marketing/urls.py apps/marketing/management apps/marketing/tests/test_dispatch.py apps/marketing/tests/test_webhooks.py
git commit -m "feat: dispatch and track marketing delivery"
```

### Task 6: Expose Marketing CRUD, dashboard, analytics, calendar, provider, and delivery APIs

**Files:**
- Create: `apps/marketing/serializers.py`
- Create: `apps/marketing/api_views.py`
- Create: `functionalities/marketing/queries.py`
- Create: `functionalities/marketing/analytics.py`
- Create: `apps/marketing/tests/test_api.py`
- Modify: `apps/api/urls.py`

**Interfaces:**
- Consumes: models, `provider_status`, dispatch/retry/cancel, and Marketing permission policy
- Produces viewsets: `MarketingCampaignViewSet`, `MarketingAdvertViewSet`, `MarketingContentViewSet`, `MarketingContactViewSet`, `MarketingLeadViewSet`, `MarketingActivityViewSet`, `MarketingMetricViewSet`, `BrandKitViewSet`, `OutboundMessageViewSet`, `MarketingWorkspaceViewSet`
- Produces actions: `summary`, `calendar`, `analytics`, `provider-status`, `preview`, `send`, `schedule`, `retry`, `cancel`, and `convert-to-client`

- [ ] **Step 1: Write failing CRUD and validation API tests**

Cover every model resource, genuine multipart images, invalid image/type/size, date ordering, negative values, contact consent/opt-out, lead status, singleton Brand Kit, reader GET access, denied reader writes, manager writes, pagination, filters, and archived/inactive behavior.

- [ ] **Step 2: Write failing workspace action tests**

Cover database-derived summary/calendar/analytics with zero/no-data semantics, provider status without secrets, preview without sending, immediate send, future scheduling, past scheduling validation, retry eligibility, cancel restrictions, CRM conversion without duplicate clients, and provider-disabled responses.

- [ ] **Step 3: Run the API tests and verify RED**

Run: `.venv\Scripts\python.exe manage.py test apps.marketing.tests.test_api -v 2`

Expected: FAIL because API interfaces do not exist.

- [ ] **Step 4: Implement serializers and permissions**

Expose explicit fields only. Derive sender/owner fields from the request, validate uploads and consent at the API boundary, and never serialize raw provider metadata containing unreviewed fields.

- [ ] **Step 5: Implement query and analytics services**

Build dashboard counts, upcoming activity, campaign/advert rows, calendar projections, funnel/channel metrics, cost per enquiry, and ROAS from persisted records. Return `null`/`available: false` for unavailable measurements instead of fabricated zero results.

- [ ] **Step 6: Implement viewsets and router registration**

Register all resources under `/api/v1/marketing/...` and legacy `/api/marketing/...`. Send actions call the dispatcher; they do not import provider modules directly.

- [ ] **Step 7: Run Marketing API tests**

Run: `.venv\Scripts\python.exe manage.py test apps.marketing.tests.test_api -v 2`

Expected: PASS.

- [ ] **Step 8: Commit**

```powershell
git add apps/marketing/serializers.py apps/marketing/api_views.py apps/marketing/tests/test_api.py apps/api/urls.py functionalities/marketing/queries.py functionalities/marketing/analytics.py
git commit -m "feat: expose marketing workspace APIs"
```

### Task 7: Replace the placeholder with the prototype-matched Marketing shell

**Files:**
- Create: `templates/marketing/index.html`
- Create: `static/sme/marketing/css/style.css`
- Create: `static/sme/marketing/js/api.js`
- Create: `static/sme/marketing/js/views.js`
- Create: `static/sme/marketing/js/forms.js`
- Create: `static/sme/marketing/js/charts.js`
- Create: `static/sme/marketing/js/app.js`
- Create: `apps/marketing/tests/test_views.py`
- Modify: `apps/marketing/views.py`
- Modify: `templates/academy/index.html`
- Delete: `templates/core/growth_marketing.html`
- Modify: `apps/core/tests.py`

**Interfaces:**
- Consumes: named Marketing API endpoints, authenticated user/permission state, provider statuses, and Django static/media URLs
- Produces hash routes: `dashboard`, `campaigns`, `advertising`, `content`, `email`, `calendar`, `leads`, `analytics`, `brand`

- [ ] **Step 1: Write failing shell tests**

Assert `/growth/` contains nine prototype-labelled navigation controls and unique icons, Marketing business identity, `/academy/#tools`, sign-out form, native dialog, safe JSON configuration, management flag, provider-status region, maintained static assets, and no generic CRM topbar/placeholder markers.

- [ ] **Step 2: Write failing route-link regression tests**

Assert Academy course/tool links and suite navigation use `/growth/`, the old `../marketing-app/index.html` string is absent, and the deleted Core placeholder is not referenced.

- [ ] **Step 3: Run the view tests and verify RED**

Run: `.venv\Scripts\python.exe manage.py test apps.marketing.tests.test_views apps.core.tests -v 2`

Expected: FAIL against the placeholder and prototype link.

- [ ] **Step 4: Port the shell and visual system**

Port the prototype CSS and relevant shared inventory visual primitives into `static/sme/marketing`, preserving sidebar sizes, icons, cards, tables, poster/email previews, calendar, charts, responsive breakpoints, print styles, and accessible focus states. Reference Django static/media URLs only.

- [ ] **Step 5: Implement the API adapter and all nine renderers**

Render exclusively from APIs. Escape all user-controlled values. Keep Advertising Opportunities as a nested route/view. Display provider availability cards and `No data` analytics states accurately.

- [ ] **Step 6: Implement forms and interactions**

Support CRUD, filters, previews, genuine multipart uploads, lead status/CRM conversion, calendar navigation, immediate send, scheduling, retry/cancel, provider-disabled explanations, responsive sidebar, and failed-form state preservation. Never place credentials or direct provider calls in JavaScript.

- [ ] **Step 7: Update Academy link and remove the placeholder**

Carefully merge the existing dirty `templates/academy/index.html` rather than overwriting unrelated user changes. Replace the prototype Marketing link with the named `/growth/` Django destination and remove `templates/core/growth_marketing.html`.

- [ ] **Step 8: Run view, Core, and JavaScript checks**

Run: `.venv\Scripts\python.exe manage.py test apps.marketing.tests.test_views apps.core.tests -v 2`

Run: `node --check static\sme\marketing\js\api.js` and repeat for `views.js`, `forms.js`, `charts.js`, and `app.js`.

Expected: PASS with no JavaScript syntax errors.

- [ ] **Step 9: Commit**

```powershell
git add templates/marketing static/sme/marketing apps/marketing/views.py apps/marketing/tests/test_views.py templates/academy/index.html apps/core/tests.py
git add -u templates/core/growth_marketing.html
git commit -m "feat: build complete marketing workspace"
```

### Task 8: Add live browser acceptance, setup documentation, and whole-application regression

**Files:**
- Create: `tests/browser/test_marketing_workspace.py`
- Create: `docs/marketing-provider-setup.md`
- Modify: `docs/release-checklist.md`
- Modify: `Master Plan.md`
- Modify: `ReadME`
- Modify: `tests/browser/test_dummy_users.py`

**Interfaces:**
- Consumes: migrated development database, demo users, mocked Django tests, and a live local server
- Produces: reproducible provider setup/scheduler documentation and Marketing browser acceptance coverage

- [ ] **Step 1: Write the browser journey**

Cover login, nine hash routes, desktop/mobile sidebar, campaign/advert/content/email/contact/lead/activity/metric/Brand Kit CRUD, genuine image upload, preview, provider `Not configured` controls, reader-hidden writes, calendar, no-data and recorded-data analytics, CRM lead conversion, and absence of browser errors/HTTP 500 responses. Do not perform a live provider send.

- [ ] **Step 2: Run the browser journey against the development server**

Run server: `.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8023 --noreload`

Run: `.venv\Scripts\python.exe tests/browser/test_marketing_workspace.py`

Expected: PASS after fixing any browser-discovered defect through a focused failing assertion.

- [ ] **Step 3: Write the provider setup guide**

Document every environment variable, official provider-console/documentation link, verified-sender requirements, Meta account/permission prerequisites, webhook routes and signature requirements, public HTTPS/media constraints, safe test procedure, and `send_due_marketing --limit N` setup for Windows Task Scheduler, cron, and hosting schedulers.

- [ ] **Step 4: Update release and project documentation**

Document `/growth/`, Marketing permissions, provider status behavior, consent boundary, delivery semantics, scheduler command, webhook security, and the browser-test command. Merge rather than overwrite pre-existing dirty documentation changes.

- [ ] **Step 5: Run Django checks and all Marketing suites**

Run: `.venv\Scripts\python.exe manage.py check`

Run: `.venv\Scripts\python.exe manage.py makemigrations --check --dry-run`

Run: `.venv\Scripts\python.exe manage.py test apps.marketing.tests -v 2`

Expected: no system issues, no pending migrations, all Marketing tests PASS.

- [ ] **Step 6: Run the complete Django regression suite**

Run: `.venv\Scripts\python.exe manage.py test -v 2`

Expected: PASS. Update stale expectations for intentionally replaced Tasks, Inventory, root landing, and Marketing shells; do not weaken unrelated behavior assertions.

- [ ] **Step 7: Run authenticated browser regression**

Run:

```powershell
.venv\Scripts\python.exe tests/browser/test_dummy_users.py
.venv\Scripts\python.exe tests/browser/test_academy_management.py
.venv\Scripts\python.exe tests/browser/test_task_workspace.py
.venv\Scripts\python.exe tests/browser/test_inventory_workspace.py
.venv\Scripts\python.exe tests/browser/test_marketing_workspace.py
```

Expected: all journeys PASS with no page errors or HTTP 500 responses.

- [ ] **Step 8: Verify no secret or prototype-state leakage**

Run targeted searches for real credential prefixes, Authorization headers in fixtures/output, `localStorage`, prototype `data.js`, and `../marketing-app/index.html`. Confirm `.env` remains ignored and only `.env.example` is staged.

- [ ] **Step 9: Commit**

```powershell
git add tests/browser/test_marketing_workspace.py tests/browser/test_dummy_users.py docs/marketing-provider-setup.md docs/release-checklist.md "Master Plan.md" ReadME
git commit -m "docs: verify integrated marketing workspace"
```
