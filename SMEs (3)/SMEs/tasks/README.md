# Task & Project Management

Open `index.html` in a modern browser, or serve the parent marketing folder with VS Code Live Server. No install or build step is required.

This is a front-end prototype. All edits live in memory and reset on refresh. Attachments retain only the selected filename; nothing is uploaded. There is no backend, authentication, API, database, or persistence.

## Files

- `index.html`: the shared platform shell, header, sidebar, and modal.
- `../inventory/css/style.css`: existing platform components, loaded without modification.
- `css/style.css`: task-module layouts and responsive additions.
- `js/data.js`: sample projects, team and tasks; dates are relative to today.
- `js/ui.js`: page templates, rose chart, reusable controls and forms.
- `js/app.js`: navigation, filters, task completion, modal submission and calendar controls.

## Behaviour

The dashboard counts and project completion percentages are calculated from tasks. Overdue means an unfinished task with a due date before today; it is not a fourth board column. My Tasks shows Thando's work, with a Monday–Sunday week. Calendar arrows move one month at a time. Selecting a project opens its details. Task names and action menus open editable task details.

Projects and tasks can be created for the current session. The task board has exactly three columns and a status dropdown on each card. New project owners are also included in the project's team. Due dates cannot precede project start dates.

The sidebar uses Inventory's styles and icons. Inventory files are not modified. Keep both folders together so the shared stylesheet resolves.
