# Academy Management Workspace Design

**Date:** 18 September 2026  
**Status:** Approved for implementation planning  
**Application:** JBS SME Ecosystem / SME Academy

## 1. Purpose

Add a protected, SME-branded management workspace inside `/academy/` so authorised Academy managers can configure the content currently maintained through Django Admin without leaving the Academy interface.

The workspace must provide explicit create, read, update and safe-delete/archive operations through supported APIs and modal forms. Django Admin remains available as a secondary operational interface, but it is no longer the only way to configure the Academy.

The Tasks application is not part of this delivery. It will be assessed after the Academy management workspace is complete.

## 2. Authorised users

Academy management access is granted when any of these conditions is true:

- `user.is_superuser`
- `user.is_staff`
- the application role is Administrator
- the application role is CEO/Dean (the existing compatibility role code `dean`)

All other authenticated users retain the existing learner experience. They must not see management navigation or controls and must receive HTTP 403 from management APIs.

The backend permission is authoritative. Hiding a button is not an access-control mechanism.

## 3. User experience

### 3.1 Navigation

Authorised users receive a `Manage Academy` item in the Academy sidebar. It routes to `#manage` inside the existing Academy shell.

Relevant learner-facing sections also display contextual controls to authorised users:

- Courses: `Add course`, `Manage paths`, `Manage categories`, `Manage levels`
- Templates & Resources: `Add resource`, `Manage categories`
- Business Diagnostic: `Add diagnostic`, `Manage categories`
- Funding: `Add opportunity`, `Import CSV`, `Manage categories`
- Events: `Add event`, `Manage categories`
- Mentorship: `Add mentor`
- Community: `Manage categories`, plus moderation actions on posts

All contextual buttons open the same management forms used by `#manage`; there are not separate implementations for each screen.

### 3.2 Management workspace

The management screen is grouped into:

1. Learning
2. Resources
3. Diagnostics
4. Funding
5. Events
6. Mentorship
7. Community

Each group contains entity tabs with:

- a concise explanation;
- search and status filtering;
- an `Add` button;
- a table/list showing active, draft and archived records;
- Edit, Publish/Unpublish and Archive/Delete actions;
- clear empty and error states.

The interface uses the existing SME green, sage, orange, rounded-card and modal styling. It remains usable at mobile widths.

### 3.3 Modal forms

Simple entities use one modal form. Relations are select fields populated from management APIs, including inactive records when editing an existing relationship.

Complex entities use a parent editor plus child managers:

- A course is saved first, then its modules are managed in an ordered list.
- Quiz modules expose answer-option inputs and the correct-option selector.
- A diagnostic is saved first, then questions are managed in order.
- Diagnostic questions expose ordered scored options.
- Diagnostic recommendations are managed from the diagnostic editor and link score ranges to published or draft courses.

This avoids a single oversized form while still keeping the complete workflow inside the Academy.

### 3.4 Feedback and errors

- Invalid fields display their server-provided errors next to the relevant control.
- Non-field errors appear at the top of the modal.
- Successful saves close the modal, show an accessible toast and refresh the affected list.
- Network errors retain entered form values and offer a retry.
- Conflict or protected-delete responses explain whether a record was archived instead.
- Submit controls are disabled while a request is pending to prevent duplicate writes.

## 4. Managed entity matrix

| Area | Managed entities | Important relationships and rules |
|---|---|---|
| Learning | Course categories, course levels, learning paths, courses, course modules | Course requires path; category and configured level follow current model constraints; modules retain position, type, prompt, video/resource URL, required and published state; course controls duration, passing grade and published state. |
| Resources | Resource categories, Academy resources | Resource requires a category and supports an uploaded file or validated HTTPS external URL; published state is manager-controlled. |
| Diagnostics | Diagnostic categories, diagnostics, questions, options, recommendations | Questions belong to a diagnostic and category; options carry scores and order; recommendations use valid non-overlapping score bounds and reference a course. |
| Funding | Opportunity categories, funding opportunities | Manual CRUD and current CSV template/preview/atomic import remain available; application links must pass existing URL validation. |
| Events | Event categories, Academy events/webinars | Dates, capacity, venue and meeting/registration URL use current model validation; registrations remain system records. |
| Mentorship | Mentor profiles | Manager selects an existing user and configures expertise, biography and active state; mentorship bookings and conversations remain system records. |
| Community | Forum categories and post moderation | Managers configure categories and may publish/hide, pin or lock posts; post authorship and replies remain user-generated records. |

The management workspace does not edit enrolments, module progress, quiz attempts, certificates, diagnostic submissions, event registrations, mentorship bookings, conversations or chat messages.

## 5. API architecture

### 5.1 Route boundary

Management endpoints live under:

`/api/v1/academy/manage/`

Learner-facing `/api/v1/academy/` endpoints retain their current behavior and permissions.

### 5.2 Explicit resources

Use explicit serializers and viewsets for each managed entity family. Do not expose a generic model-name endpoint and do not accept arbitrary fields.

Expected route families include:

- `course-categories/`
- `course-levels/`
- `paths/`
- `courses/`
- `modules/`
- `resource-categories/`
- `resources/`
- `diagnostic-categories/`
- `diagnostics/`
- `diagnostic-questions/`
- `diagnostic-options/`
- `diagnostic-recommendations/`
- `opportunity-categories/`
- `funding/`
- `events-categories/`
- `events/`
- `mentors/`
- `forum-categories/`
- `forum-posts/` for moderation fields only

Funding CSV endpoints remain explicit actions in the funding management boundary.

### 5.3 Permission

Create `IsAcademyManager`, a DRF permission class implementing the approved staff/superuser/Administrator/CEO-Dean rule. Every management viewset and action uses it.

Serializers must not permit clients to set learner ownership, authorship, certificate identifiers or other system-controlled values.

### 5.4 Query behavior

Management querysets include active, inactive, published, unpublished and archived records. They support concise search and status filters needed by the workspace.

Learner querysets continue to return only active/published records.

### 5.5 Transactions

Operations that update a parent and ordered child collection execute in `transaction.atomic()`. Validation occurs before destructive replacement of child records. A failed child leaves the previous valid configuration intact.

## 6. Safe deletion and archival

`DELETE` means “remove safely,” with the server deciding the allowed operation:

1. If the record has no protected references or learner history, it may be permanently deleted.
2. If it is referenced, it is archived using the model’s existing `is_active` or `is_published` field.
3. Where no suitable state exists and history requires preservation, an additive nullable `archived_at` field may be introduced through a migration.

The response identifies `deleted` or `archived` and returns the resulting record state when archived.

Archiving a parent makes it unavailable to learners without deleting historical enrolments, submissions, registrations, messages or certificates. Managers may restore archived records when model constraints still pass.

Hard deletion must never cascade into learner history.

## 7. Frontend architecture

Add a focused management JavaScript module rather than growing `course-page.js` indefinitely:

- `academy-admin-api.js`: authenticated management requests, multipart support and normalized validation errors.
- `academy-admin.js`: route rendering, entity lists, modal lifecycle, form serialization and refresh behavior.
- `academy-admin-schema.js`: declarative field/list configuration for simple entities only.

Complex course and diagnostic child editors remain explicit code because their validation and relationships are not generic CRUD.

The Django view safely injects:

- `can_manage_academy`;
- named management endpoint URLs;
- funding CSV template/preview/import URLs;
- choice metadata that cannot be obtained from entity lists.

No host, port, CSRF token or endpoint path is hardcoded in frontend JavaScript.

The modal uses a native `<dialog>` or an existing locally styled modal implementation so management does not depend on the optional Bootstrap CDN.

## 8. Validation and security

- All write validation is server-side and reuses model/service validation where available.
- Slugs may be suggested from titles but uniqueness is enforced server-side.
- URLs follow existing HTTPS/origin rules.
- Uploaded files use the project’s current storage and type/size constraints.
- Funding CSV import stays atomic: any invalid row prevents writes.
- Forum moderation permits only the approved status, pin and lock fields.
- Mentor selection cannot silently change existing booking participants.
- CSRF protection applies to session-authenticated writes.
- Management actions produce ordinary Django/DRF auditability through timestamps and authenticated request ownership; a new general audit-log subsystem is outside this scope.

## 9. Testing strategy

### 9.1 Permission tests

For every management API family:

- unauthenticated request returns 401/403 according to the configured authentication boundary;
- ordinary authenticated user receives 403;
- staff, superuser, Administrator and CEO/Dean-role users can access it;
- management navigation and controls are absent for ordinary learners.

### 9.2 CRUD tests

Each entity family covers create, list/retrieve, update, validation failure and safe removal. Tests assert persisted model state rather than serializer internals.

### 9.3 Archival tests

- Unused records can be deleted where safe.
- Referenced records are archived rather than deleted.
- Learner history survives parent archival.
- Archived records disappear from learner APIs and remain visible to management APIs.
- Restoring a record re-exposes it only when all parent dependencies are active/published.

### 9.4 Nested transaction tests

- Valid course modules and diagnostic children persist in order.
- One invalid child rolls back the complete submitted change.
- Quiz correct-option and diagnostic score-bound validation are enforced.

### 9.5 Browser tests

Using an authorised demo account:

- open Manage Academy;
- create and edit representative taxonomy and content records;
- verify the learner section refreshes from the API;
- archive the representative content and verify its learner visibility changes;
- exercise the funding CSV modal;
- confirm modal validation, mobile layout and canonical URLs;
- confirm ordinary staff cannot see or open management controls.

Browser-created fixtures use unique test prefixes and are removed or archived at the end of the journey.

## 10. Delivery boundaries

This delivery includes the management workspace, protected APIs, necessary additive migrations, SME-styled modals, contextual controls, tests and Master Plan updates.

It does not redesign Django Admin, edit learner history, add bulk import beyond the existing funding CSV workflow, introduce a general workflow engine, implement outbound notifications, or change the Tasks application.

After acceptance, the next activity is a separate inspection and plan for Tasks.

## 11. Acceptance criteria

The feature is accepted when:

- authorised managers can configure every entity in the managed matrix without opening Django Admin;
- ordinary users cannot see or call management functionality;
- learner pages display newly published configuration after API refresh;
- related historical data is preserved by safe archival;
- funding manual and CSV workflows are both available;
- all management modals match SME branding and work without relying on Bootstrap CDN behavior;
- targeted, full Django and Playwright suites pass with no unhandled browser errors;
- no runtime endpoint contains a hardcoded localhost host or port.
