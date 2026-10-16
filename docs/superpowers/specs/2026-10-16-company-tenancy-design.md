# Company Tenancy Design

**Date:** 2026-10-16  
**Status:** Approved for planning

## Purpose

Convert the application from a single-organization system into a row-level multi-tenant platform. Each normal user belongs to one company and may only read or change that company's data. Django superusers may access data across companies so the platform can measure and report on the wider business ecosystem.

The migration must preserve all existing data by assigning it to one generated default company.

## Scope

Tenant isolation applies to every company-owned workflow, including CRM, invoicing, inventory, project management, marketing, documents, accounting, payroll, purchasing, sales, expenses, alerts, communications, analytics, and company-specific settings.

Academy catalogue content may remain platform-wide where it is intentionally shared. User-specific Academy activity, such as enrollments, submissions, registrations, bookings, conversations, and certificates, remains isolated through the user's company. A later feature may add company-private Academy content; it is not part of this change.

Self-service company registration, company switching, subscription billing, and delegated company-administrator tooling are out of scope. Company records and user assignments will initially be managed in Django Admin.

## Tenant Model

Create a `Company` model as the tenant root with:

- `name` and unique `slug`
- optional legal name, registration number, tax number, email, phone, and address fields
- `is_active`
- created and updated timestamps

Add a nullable `company` foreign key to the custom user model. It is nullable at the database level so platform superusers can exist without a tenant, but application validation and admin forms must require a company for every non-superuser.

Add a required `company` foreign key to `Centre`. A centre is a department within exactly one company. Centre codes and names that are currently globally unique must become unique per company where applicable.

## Ownership Rules

Every top-level company-owned aggregate receives an indexed, required `company` foreign key. This includes root records whose data may be queried or summarized without joining through another tenant-owned record, such as clients, engagements, campaigns, contacts, products, stock locations, suppliers, projects, boards, documents, invoices, sales orders, purchase orders, expenses, pay runs, accounting accounts and periods, and singleton/settings records.

Dependent records inherit their company from a required parent rather than duplicating the field when ownership is unambiguous. Examples include invoice lines through invoices, task comments through tasks, campaign metrics through campaigns, and delivery attempts through outbound messages.

Models that can exist independently or have optional parent relationships receive their own `company` field. This prevents records with a temporarily null parent from becoming unscoped.

All relationships between tenant-owned objects must refer to objects in the same company. Validation is required at serializer/form boundaries and in service functions that construct or connect records. Database uniqueness constraints must include `company` whenever the value only needs to be unique within a tenant.

## Request Scoping

A shared tenancy module will expose the current company and reusable queryset helpers or viewset mixins.

For normal authenticated users:

- the current tenant is always `request.user.company`;
- list and detail querysets are filtered by that company before other filters are applied;
- create operations assign the company server-side;
- client-provided company values are ignored or rejected;
- a missing or inactive company results in a clear authorization denial;
- direct requests for another company's object return not found, avoiding disclosure that the object exists.

For superusers:

- unfiltered cross-company access is permitted in Django Admin and explicit platform-level reporting code;
- ordinary API endpoints may accept an explicit company filter for investigation;
- records created through tenant APIs require an explicit valid company when no current company is assigned.

Related-object choices in serializers and forms must be restricted to the effective company. A user cannot connect their record to another company's client, staff member, product, campaign, project, document, or other related object by submitting an identifier manually.

## Non-API Paths

Isolation must cover more than REST viewsets. HTML views, dashboard services, analytics, exports, searches, autocomplete endpoints, context processors, management workflows, and file/document lookups must all use the effective company.

Background work must carry an explicit company or start from a tenant-owned record. Scheduled marketing dispatch, notification generation, recurring jobs, and management commands must never depend on ambient request state.

Inbound provider webhooks may locate records by a provider identifier, but updates must remain tied to the matched tenant-owned outbound record. Webhook responses must not expose company data.

Uploaded documents and generated exports must use company-specific storage paths to reduce accidental name collisions and simplify future per-company retention or export.

## Ecosystem Analytics

Normal company users only receive metrics calculated from their company rows. Platform-wide ecosystem analytics are restricted to superusers and deliberately query across companies.

The explicit `company_id` fields on root records provide an efficient grouping dimension for counts, financial totals, operational trends, adoption metrics, and other cross-company aggregates. Platform analytics must keep company-level grouping available and must not expose raw records through a tenant-facing endpoint.

No separate analytics warehouse is introduced in this phase. The transactional database remains the source for initial ecosystem reporting.

## Migration Strategy

The schema and data transition is staged to preserve existing installations:

1. Create the `Company` table and add nullable company relationships.
2. Create one default company with a deterministic slug and a name configurable through migration-safe settings or a fixed neutral fallback.
3. Assign all existing users, centres, settings, and top-level business records to that company. Infer child ownership from their parents where applicable.
4. Validate that every tenant-owned row has one company and that related rows do not cross companies.
5. Make tenant relationships required and replace global uniqueness constraints with company-scoped constraints.

Migration code must use historical Django models and must be reversible where practical. It must not read runtime service code.

New local and test databases receive the same default company through the data migration; deployment does not require a manual pre-migration step.

## Administration

Django Admin will provide company creation and editing. User administration will expose company assignment and validate that non-superusers have a company. Tenant-owned admin querysets and foreign-key choices will be scoped for non-superuser staff; platform superusers retain cross-company administration.

The application navigation may display the current company name, but a company switcher will not be added because normal users belong to exactly one company.

## Security and Failure Behaviour

Tenant identity is derived from the authenticated user, never from an untrusted header, query parameter, form value, or request body for normal users.

Requests without authentication retain the existing public-access policy but cannot access tenant business data. Normal authenticated users without an active company are denied. Cross-company object identifiers behave as missing objects. Cross-company writes fail validation without changing data.

Application code must not silently fall back to an unrestricted queryset when tenant resolution fails.

## Testing

Tests will create at least two companies and prove:

- list endpoints, detail endpoints, HTML pages, dashboards, searches, and exports exclude the other company's records;
- create operations assign the current company and reject submitted cross-company ownership;
- related fields and form choices only contain same-company objects;
- direct object identifiers cannot read, update, delete, or associate another company's data;
- services and analytics calculate tenant totals independently;
- marketing scheduling, dispatch, retries, and webhooks update the correct tenant-owned message;
- documents and generated files use company-specific paths;
- normal users without a company are denied;
- inactive companies cannot use tenant workflows;
- superusers can inspect all companies and run ecosystem aggregates;
- the data migration assigns legacy records to the default company without loss.

Existing application tests must continue to pass after their fixtures are made company-aware. The complete Django test suite and relevant browser acceptance suites are required before completion.

## Rollout

The migration and application code ship together. Before production migration, take a database backup. After migration, verify the default company, user assignments, tenant row counts, relationship consistency, and representative module pages before creating additional companies.

Provider credentials remain deployment-level in this phase. This means email, SMS, WhatsApp, Facebook, and Instagram API credentials are shared by the platform. Per-company provider credentials can be added later as encrypted company-owned configuration without weakening the tenant model described here.
