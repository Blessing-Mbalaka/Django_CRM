# Marketing and Communications Integration Design

**Date:** 28 September 2026  
**Status:** Approved design  
**Source prototype:** `SMEs (3)/SMEs/marketing-app/`  
**Canonical route:** `/growth/`

## 1. Objective

Replace the existing Growth & Marketing placeholder with the supplied Marketing & Advertising workspace, preserving its visual language and navigation while moving all operational state into Django. Add reusable, Marketing-owned provider adapters for Twilio Email, Twilio SMS, Meta WhatsApp Cloud API, Facebook Page publishing, and Instagram professional-account publishing.

The completed workspace must remain fully usable when no provider credentials are configured. A missing or failing provider disables only the affected delivery action and displays a clear status; it must not break campaigns, content creation, leads, analytics, calendar planning, or the rest of the CRM.

## 2. Scope and routes

`/growth/` becomes the only Marketing application. The current placeholder is removed, and any Academy or CRM link to Marketing resolves to this Django route rather than a prototype file.

The Django shell preserves these prototype routes:

- `#dashboard`
- `#campaigns`
- `#advertising`
- `#content`
- `#email`
- `#calendar`
- `#leads`
- `#analytics`
- `#brand`

Advertising opportunities may remain a nested view reached from Advertising rather than a tenth primary navigation item.

The implementation must not load prototype JavaScript data or read/write `localStorage`. Prototype sample metrics must not be imported as live operational facts.

## 3. Repository structure

Marketing remains isolated in the same pattern as Academy, Tasks, and Inventory:

```text
apps/marketing/
├── models.py
├── serializers.py
├── api_views.py
├── views.py
├── urls.py
├── admin.py
├── tests/
├── migrations/
└── management/commands/send_due_marketing.py

functionalities/marketing/
├── queries.py
├── analytics.py
├── dispatch.py
├── scheduling.py
├── webhooks.py
└── providers/
    ├── base.py
    ├── status.py
    ├── twilio_email.py
    ├── twilio_sms.py
    ├── meta_whatsapp.py
    ├── meta_facebook.py
    └── meta_instagram.py

templates/marketing/index.html

static/sme/marketing/
├── css/style.css
└── js/
    ├── api.js
    ├── views.js
    ├── forms.js
    ├── charts.js
    └── app.js
```

Provider adapters live under `functionalities/marketing/providers/`. They must not import templates or browser code and may therefore be reused by other Django applications later.

## 4. Domain model

### 4.1 MarketingCampaign

Stores name, objective, product/service, target audience, target location, selected channels, start/end dates, budget, status, description, owner, and timestamps. End date cannot precede start date.

Statuses are `draft`, `scheduled`, `active`, `paused`, `completed`, and `cancelled`.

### 4.2 MarketingAdvert

Stores campaign, name, advertised subject, advertising type, platform/publisher, audience, location, start/end dates, budget, actual spend, destination URL, status, and timestamps. Performance is not inferred from budget or status.

### 4.3 MarketingContent

Stores content kind (`poster`, `social`, or `email`), campaign, title/name, subject, heading, body/caption, call-to-action text and link, hashtags, platform, template, genuine uploaded image, scheduling time, lifecycle status, and timestamps. Email HTML is rendered from a controlled template and escaped/sanitized content rather than arbitrary executable markup.

Uploads accept only approved image MIME types and extensions, enforce a 5 MB limit, use generated storage names, and are served through configured media storage.

### 4.4 MarketingContact

Stores name, email address, mobile number, WhatsApp number, source, optional CRM Client relationship, per-channel consent flags, consent timestamps/source, opt-out timestamps, active state, and timestamps.

Outbound marketing delivery requires a usable destination and affirmative consent for the selected channel. An opted-out contact cannot be sent marketing content even if a stale consent flag remains true.

### 4.5 MarketingLead

Stores optional contact, campaign, acquisition source, received date, status, estimated value, notes, owner, and optional CRM Client relationship. Statuses are `new`, `contacted`, `interested`, `converted`, and `not_interested`. Sending a lead to CRM links or creates the appropriate Client through an explicit manager action; it never silently duplicates a Client.

### 4.6 MarketingActivity

Stores a calendar activity name, type, date/time, description, and optional campaign, advert, or content relationship. Campaign starts, advert starts, and scheduled content are also projected into calendar query results without duplicating their source rows.

### 4.7 MarketingMetric

Stores campaign, optional advert, channel, reporting date/period, spend, reach, responses, enquiries, leads, customers, and attributed revenue. Dashboard and Analytics calculate from these rows plus current operational lead counts. No sample values are displayed as real metrics.

### 4.8 BrandKit

A singleton containing business name, slogan, approved logo upload, colours, fonts, descriptions, phone, WhatsApp, email, website, physical location, and social profile URLs. Brand data is reused in poster and email previews.

### 4.9 OutboundMessage

Stores channel, optional campaign/content/contact relationships, immutable destination and content snapshots, scheduled time, current delivery status, provider name, provider message or operation identifier, accepted/sent/delivered/read/failed timestamps, attempt count, last sanitized error, creator, and timestamps.

Statuses are `draft`, `scheduled`, `processing`, `accepted`, `sent`, `delivered`, `read`, `failed`, `cancelled`, and `unavailable`. A provider acceptance response is never represented as delivered.

### 4.10 DeliveryAttempt and ProviderWebhookEvent

`DeliveryAttempt` stores an attempt number, start/end times, outcome, HTTP/provider status, retry eligibility, and sanitized error/response metadata. It must not store credentials, authorization headers, or full secrets returned in diagnostic data.

`ProviderWebhookEvent` stores provider, external event identifier or deterministic digest, event type, received/processed timestamps, linked message, and a safely bounded payload. A unique provider/event constraint makes webhook processing idempotent.

## 5. Provider interface

The shared interface exposes:

- `provider_status() -> dict[str, ProviderStatus]`
- `send_email(message: OutboundMessage) -> ProviderResult`
- `send_sms(message: OutboundMessage) -> ProviderResult`
- `send_whatsapp(message: OutboundMessage) -> ProviderResult`
- `publish_facebook_post(message: OutboundMessage) -> ProviderResult`
- `publish_instagram_media(message: OutboundMessage) -> ProviderResult`
- `dispatch_message(message_id: int) -> OutboundMessage`
- `dispatch_due_marketing(*, limit: int) -> DispatchSummary`

`ProviderStatus` reports `available`, `not_configured`, `unavailable`, or `temporarily_failing`, plus a safe human-readable explanation and missing environment-variable names. It never returns secret values.

`ProviderResult` provides provider ID, normalized initial status, sanitized metadata, and retry guidance.

## 6. Provider contracts

### 6.1 Twilio Email

Send through `POST https://comms.twilio.com/v1/Emails` using HTTP Basic authentication with an API Key SID and API Key Secret. The sender must be a verified address/domain. A successful `202 Accepted` response stores the returned `operationId` and `operationLocation`; it does not mark the email delivered.

Email status synchronization uses the Twilio operation/email endpoints where configured. Because Twilio Email documents seven-day resource retention, local delivery history is authoritative for long-term CRM reporting.

Official references:

- https://www.twilio.com/docs/email/api/getting-started
- https://www.twilio.com/docs/email/api/mail-send
- https://www.twilio.com/docs/email/api/operations-and-email-tracking

### 6.2 Twilio SMS

Use the official Python helper library. Production authentication uses Account SID plus an API Key SID/Secret. `TWILIO_AUTH_TOKEN` remains required for validating signed Twilio callbacks and may support local/test authentication. Sending uses either a configured Messaging Service SID or Twilio sender number, never both in the same request.

Recipients use validated E.164 numbers. Each send includes a public HTTPS status callback when configured. The returned Message SID and initial status are persisted.

Official references:

- https://www.twilio.com/docs/messaging/api/message-resource
- https://www.twilio.com/docs/messaging/guides/track-outbound-message-status
- https://www.twilio.com/docs/usage/webhooks/webhooks-security

### 6.3 Meta WhatsApp

Use the configured Graph API version and `/{phone-number-id}/messages` endpoint with a bearer token. Store the returned WhatsApp message ID and correlate webhook status updates by that ID. The adapter supports approved templates and any free-form messaging permitted by the active conversation/service rules; it must not attempt to bypass Meta template or consent requirements.

Official reference:

- https://www.postman.com/meta/whatsapp-business-platform/

### 6.4 Facebook Page publishing

Publish only to the configured Facebook Page through the versioned Graph API using a Page access token with the required approved permissions. The app does not publish to personal profiles or buy/manage paid advertising. Provider configuration and permission failures are shown as unavailable rather than treated as successful posts.

Official reference:

- https://developers.facebook.com/docs/pages-api/posts/

### 6.5 Instagram publishing

Publish only for a configured Instagram Professional account with the required content-publishing permissions. Media publishing follows the container creation and publish lifecycle. Provider-accessible media URLs are required; a local-only development media URL therefore makes live Instagram publishing unavailable while previews remain functional.

Official references:

- https://developers.facebook.com/docs/instagram-platform/content-publishing/
- https://www.postman.com/meta/instagram/

## 7. Environment configuration

`.env.example` must contain commented groups for every provider. Comments explain where to obtain each value, acceptable alternatives, sender verification, token longevity, callback requirements, and official documentation links.

Required names:

```text
TWILIO_EMAIL_API_KEY
TWILIO_EMAIL_API_SECRET
TWILIO_EMAIL_FROM_ADDRESS
TWILIO_EMAIL_FROM_NAME

TWILIO_ACCOUNT_SID
TWILIO_API_KEY
TWILIO_API_SECRET
TWILIO_AUTH_TOKEN
TWILIO_SMS_FROM_NUMBER
TWILIO_MESSAGING_SERVICE_SID
TWILIO_STATUS_CALLBACK_URL

META_GRAPH_API_VERSION
META_ACCESS_TOKEN
META_APP_SECRET
META_WEBHOOK_VERIFY_TOKEN
META_WHATSAPP_PHONE_NUMBER_ID
META_WHATSAPP_BUSINESS_ACCOUNT_ID
META_FACEBOOK_PAGE_ID
META_FACEBOOK_PAGE_ACCESS_TOKEN
META_INSTAGRAM_USER_ID
META_INSTAGRAM_ACCESS_TOKEN

MARKETING_PUBLIC_BASE_URL
```

The application reads optional provider variables with safe empty defaults. Credentials are never required to boot Django, run migrations, render Marketing, or run tests.

## 8. Delivery and scheduling lifecycle

1. A permitted manager creates content or requests a send/publish.
2. Django validates permissions, channel availability, destination, consent, content, dates, and provider-specific prerequisites.
3. An `OutboundMessage` content/destination snapshot is committed before external I/O.
4. The message is claimed transactionally and set to `processing`.
5. The provider adapter performs the request with explicit connect/read timeouts.
6. The provider result and `DeliveryAttempt` are saved atomically.
7. Signed webhooks or explicit status synchronization update later lifecycle states.

Immediate and scheduled delivery call the same `dispatch_message` service. The `send_due_marketing` management command claims due scheduled messages deterministically and supports a bounded batch limit. Concurrent command executions must not send one message twice.

Network errors, timeouts, rate limits, and documented temporary provider failures may retry with capped backoff. Authentication, missing configuration, invalid destinations, denied permissions, opted-out contacts, and malformed content do not retry automatically. Managers can retry eligible failures explicitly.

## 9. Webhooks

Webhook endpoints do not require session authentication, but they require provider verification:

- Twilio requests validate `X-Twilio-Signature` with the official SDK and `TWILIO_AUTH_TOKEN`, using the externally visible callback URL.
- Meta GET verification validates `hub.verify_token` and returns `hub.challenge` only on a match.
- Meta POST events validate `X-Hub-Signature-256` using `META_APP_SECRET` before parsing or persisting changes.

Invalid signatures return an error without updating any Marketing record. Event processing is idempotent and tolerant of out-of-order status callbacks; terminal states cannot regress to earlier transient states.

## 10. API and permissions

Authenticated users may read marketing data allowed by existing CRM visibility rules. CEO, Director, and System Administrator roles may create/edit campaigns, adverts, content, contacts, leads, activities, metrics, and Brand Kit data, and may send, schedule, publish, retry, or cancel outbound work.

The API includes explicit resources plus actions for dashboard summaries, calendar aggregation, analytics, provider status, preview, immediate send, scheduling, retry, and cancellation. The UI receives named Django URLs and a management-permission flag through safely serialized configuration.

Provider-status responses expose only state, missing variable names, and safe guidance. They never expose credential values or raw authorization errors.

## 11. User interface

The supplied sidebar, icons, cards, forms, tables, calendar, responsive rules, poster/email previews, charts, and Brand Kit styling are ported into maintained static files. The shell includes `/academy/#tools`, authenticated sign-out, keyboard focus handling, accessible dialogs, status messaging, and role-conditional actions.

Each provider is represented by a status card:

- `Available`
- `Not configured`
- `Unavailable`
- `Temporarily failing`

Unavailable send/publish controls remain discoverable but disabled with a clear explanation. The UI never claims a message was sent unless the provider accepted it, and never claims delivery until confirmed by a provider status.

Analytics are derived from persisted `MarketingMetric`, lead, and delivery records. Where a provider does not expose a metric or credentials are absent, the UI displays `Unavailable` or `No data`, not zero presented as a measured result.

## 12. Error handling and observability

All external calls use timeouts and normalized exceptions. User-visible errors are concise and actionable; detailed provider responses are sanitized before storage or logs. Credentials, authorization headers, access tokens, full webhook secrets, and sensitive message content are excluded from error logging.

The dashboard reports failed/retryable delivery counts. Django logging records provider, local message ID, provider ID when available, attempt number, normalized status, and elapsed time.

## 13. Testing

Automated tests mock all provider HTTP and SDK calls. Tests never send real email, SMS, WhatsApp, Facebook, or Instagram content.

Coverage includes:

- model validation and data preservation;
- every missing-provider-variable combination;
- provider status without secret leakage;
- correct Twilio Email request/authentication and `202` operation handling;
- Twilio SMS sender versus Messaging Service selection;
- Meta endpoint, version, token, container, and publishing flows;
- successful, rejected, rate-limited, timed-out, and server-error responses;
- retry classification and attempt limits;
- consent, opt-out, destination, upload, and date validation;
- duplicate scheduler prevention;
- valid/invalid webhook signatures, duplicate events, and out-of-order states;
- permissions for reads, writes, and sends;
- all nine hash routes, disabled provider controls, CRUD, genuine uploads, responsive navigation, and browser errors;
- whole-application regression, including canonical `/academy/` landing behaviour.

## 14. Documentation and operations

Add a Marketing setup guide covering:

- every environment variable and official provider link;
- verified sender/domain and sender-number prerequisites;
- Meta app, account, permission, and token prerequisites;
- public HTTPS callback/media URL requirements;
- `python manage.py send_due_marketing --limit N`;
- recommended Windows Task Scheduler, cron, or hosting-scheduler invocation;
- safe provider test mode and webhook verification;
- backup, deployment, and rollback considerations.

## 15. Explicit non-goals

- Buying or managing paid Meta, Google, TikTok, radio, print, or billboard advertising.
- Publishing to personal Facebook or consumer Instagram accounts.
- Scraping audiences or importing contacts without an explicit source and consent state.
- Pretending prototype sample results are live analytics.
- Storing provider secrets in the database or exposing them to the browser.
- Adding Celery, Redis, or another worker service in this version.
