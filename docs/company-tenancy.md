# Companies and personal learning

Companies register at `/accounts/register/`, choose a unique company code, and create their first administrator. Sign in with that code, username (or email), and password. Usernames are unique within each company. Existing accounts use company code `original` and retain their passwords.

Company administrators use the **Team** / **Company team** link or `/accounts/team/` to create members. These accounts have ordinary application roles; registration and team creation never grant Django staff or superuser privileges. Users cannot move records to another company or switch companies by submitting a company identifier.

## Ownership and queries

The shared database remains in place. Company-owned models inherit `CompanyOwnedModel`: a required company foreign key, company-aware querysets, write validation, and cross-company relationship checks. The authenticated user's company is resolved before business views and services execute. REST tokens derive the company from their authenticated user as well. Inactive companies are denied. Company-specific identifiers, number sequences, settings, brand kits, and uniqueness constraints are independent.

Class-level querysets and form choices are scoped when cloned and evaluated. `all_companies` and Django's base manager intentionally remain available for trusted platform code, migration validation and signed provider callback resolution. Never use them in company-facing views or serializers. Workers must enter `company_context(company)` explicitly. Existing management jobs default to the original company; use `python manage.py company_command COMPANY_CODE send_due_marketing --limit 100` or `python manage.py company_command COMPANY_CODE bootstrap_accounts` to target another company.

## Shared learning, private progress

Learning paths, courses, published modules, resource catalogues, events, and other catalogue content remain shared. Academy content management remains restricted to the original platform company's existing Academy managers; registering a company does not grant that permission.

Enrolments, completed modules, responses, quiz attempts, certificates and other private activity have company ownership, and learner APIs additionally filter by the current user. Colleagues in the same company do not share personal progress. The course interface loads real published modules, enrols the learner, saves completions and responses, grades quizzes on the server, and restores progress after reload or a later sign-in. Certificates shown in the interface come from server-issued records.

## Files and provider callbacks

New authenticated uploads use `media/companies/<company-id>/...`. All `/media/` requests must reach Django's protected media view; do not configure a public static alias for this directory in production. Legacy uploads remain available to the original company. Published Academy resource files remain available to all signed-in learners.

Provider credentials remain deployment settings. Signed Twilio and Meta callbacks resolve a unique provider message and update its owning company's record inside that company's context. An optional `?company=COMPANY_CODE` callback parameter further restricts resolution. Scheduling only selects messages from its explicit company context.

## Migration and backup

The company migration reserves ID 1 and code `original` for the original company. Business migrations add company ownership to existing records with that value and preserve existing row counts, users, shared courses and file names. Run all migrations together with `python manage.py migrate`; no separate company databases are created.

The initial installation creates a timestamped `.company-backups/` folder containing the original database, original versions of changed files, and a manifest of new files. Keep this backup until the rollout is accepted. Stop the app before restoring both source files and database together. New companies and writes created after that backup would need to be exported before a restore.

Verification covers two-company read/write isolation, related identifiers and form choices, company settings, tokens, registration, team accounts, shared courses, personal progress, quiz grading, files, background scheduling, signed callbacks and legacy migration behavior.
