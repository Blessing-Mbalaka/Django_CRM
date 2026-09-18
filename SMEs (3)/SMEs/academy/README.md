# SME Academy

## Django integration (18 September 2026)

The live Academy course catalogue is now served by Django at `/academy/`. The original files in this folder remain the visual/content reference; Django does not load this folder's `js/data.js` at runtime.

Administrators manage learning paths, courses, and ordered typed modules at `/admin/academy/`. A module may contain article text, an activity prompt, a quiz, a practical task, a resource link, a reflection prompt, or a YouTube video. Enter a normal HTTPS YouTube watch, share, Shorts, live, or embed URL. Django validates the provider and video ID and produces a `youtube-nocookie.com` iframe URL for learners; do not paste iframe HTML.

The authenticated frontend reads published content from:

- `/api/v1/academy/paths/`
- `/api/v1/academy/courses/`
- `/api/v1/academy/courses/<slug>/`

Seed the editable sample catalogue once with:

```powershell
.\.venv\Scripts\python.exe manage.py seed_academy
```

The command is idempotent and does not overwrite later administrator edits. The database is authoritative after seeding.

Open `index.html` in a modern browser, or use VS Code Live Server from the parent folder. No install or build is required. Hash routes support the 15 sidebar pages and `#course/<id>` detail pages.

## Scope

This is a front-end prototype. It has 8 learning paths and 72 sample course records. Course modules demonstrate video, reading, activity, quiz, practical output, worksheet and reflection interactions. The content is illustrative, not a complete accredited curriculum.

All progress, profile changes, notes, bookings, registrations and community posts reset on refresh. Nothing is sent to another user or service. File selection stores only a filename in memory. Downloads, sharing and certificates are mock previews. No backend, authentication, APIs, payments, file storage or notification service is implemented.

## Files and reuse

- `index.html`: platform shell and script entry points.
- `../inventory/css/style.css`: shared Inventory design system, unchanged.
- `../knowledge-hub/css/style.css`: reusable learning cards, progress bars and reading layouts.
- `css/style.css`: Academy-specific layouts and responsive refinements.
- `js/data.js`: mock records and session state. Replace with an API adapter later.
- `js/ui.js`: reusable cards, controls and rendering helpers.
- `js/views.js`: page templates and the course player.
- `js/app.js`: routes, validation and local interactions.

Keep these sibling modules together so relative links and styles resolve. Do not run a JavaScript formatter that rewrites literal HTML inside template strings.

## Demo behaviour

- Course progress comes from completed modules. The quiz must be answered correctly before that module is marked complete; the practical business task must have a saved output.
- A sample certificate appears after all nine modules are completed. Certificate dates and completed modules are seeded for the seven sample completed courses.
- Learning hours are estimated from course duration and completion, not tracked viewing time.
- The learning journey reflects the Business Stage chosen in My Profile. Upcoming stages are shown as a roadmap; courses remain available.
- The diagnostic uses 13 self-reported confidence answers. Scores map answers to 25–100% and recommendations prioritise the lowest-scoring areas. This is not AI or a verified business assessment.
- Business Growth is explicitly labelled historical sample data, separate from learning progress.
- Mentors, funding programmes and events are fictional examples. Bookings and registrations are local demonstrations only.
- CRM is a placeholder because no existing CRM entry point was found. Other Business Tools link to the local modules.

## Validation

JavaScript syntax and generated HTML were checked for all pages and nine module types. Interaction checks covered diagnostic completion, quiz/task completion gates, bookings, duplicate booking prevention, registration, community text escaping, filters and settings. Inventory, Marketing and Tasks were verified unchanged. No visual browser test was performed.
