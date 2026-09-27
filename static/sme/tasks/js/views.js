export const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
export const dateText = value => value ? new Date(`${value}T12:00:00`).toLocaleDateString('en-ZA', { day: 'numeric', month: 'short', year: 'numeric' }) : 'No due date';
const pill = value => `<span class="badge status-${esc(String(value).toLowerCase().replaceAll(' ', '-'))}">${esc(value)}</span>`;
const progress = value => `<div class="learning-progress" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${value}"><span style="width:${value}%"></span></div>`;
const heading = (title, subtitle) => `<div class="page-heading"><div><h2>${title}</h2><p>${subtitle}</p></div></div>`;
const empty = text => `<div class="empty"><strong>${esc(text)}</strong><p>Create or assign work to see it here.</p></div>`;

function projectProgress(project) {
  const tasks = project.subtask_details || [];
  if (!tasks.length) return project.column_name === 'Completed' ? 100 : 0;
  return Math.round(tasks.filter(task => task.column_name === 'Completed').length / tasks.length * 100);
}

function taskStatus(task, today) {
  if (task.column_name !== 'Completed' && task.due_date && task.due_date < today) return 'Overdue';
  return task.column_name;
}

function taskTable(tasks, today) {
  if (!tasks.length) return empty('No tasks match this view');
  return `<div class="table-scroll"><table><thead><tr><th>Task</th><th>Project</th><th>Assigned to</th><th>Due date</th><th>Priority</th><th>Status</th><th></th></tr></thead><tbody>${tasks.map(task => `<tr><td><button class="task-name" data-action="edit-task" data-id="${task.id}">${esc(task.title)}</button></td><td>${esc(task.project_name || 'General work')}</td><td>${esc(task.assignee_name || 'Unassigned')}</td><td class="${taskStatus(task, today) === 'Overdue' ? 'overdue-date' : ''}">${dateText(task.due_date)}</td><td>${pill(task.priority)}</td><td>${pill(taskStatus(task, today))}</td><td><button class="icon-button" data-action="edit-task" data-id="${task.id}" aria-label="Edit ${esc(task.title)}">•••</button></td></tr>`).join('')}</tbody></table></div>`;
}

export function dashboard(state) {
  const metrics = [
    ['Active Projects', state.summary.active_projects || 0, 'Work moving forward'],
    ['Tasks Due Today', state.summary.due_today || 0, 'Your team’s focus today'],
    ['Completed Tasks', state.summary.completed || 0, 'Progress worth celebrating'],
    ['Overdue Tasks', state.summary.overdue || 0, 'Ready for a follow-up'],
  ];
  const active = state.projects.filter(project => project.status === 'active').slice(0, 3);
  const counts = state.summary.status_counts || {};
  return `<section class="banner"><div class="banner-copy"><span class="eyebrow">YOUR TEAM. ALL IN ONE PLACE.</span><h2>Welcome back, ${esc(state.user.name)}</h2><p>Plan work, manage projects and keep your team on track.</p><button class="btn shine" data-action="new-task">＋ New Task</button></div><img src="${esc(state.banner)}" alt="Business owner organising their workspace"></section>
    <div class="stats task-stats">${metrics.map(([label, value, note]) => `<article class="stat"><div class="stat-label">${label}</div><strong>${value}</strong><small>${note}</small></article>`).join('')}</div>
    <div class="task-dashboard-grid"><section class="panel"><div class="panel-header"><div><h2>Project progress</h2><p>A little progress, every day</p></div><button class="btn secondary small" data-action="navigate" data-id="projects">All projects →</button></div>${active.length ? active.map(project => { const value = projectProgress(project); return `<button class="progress-project" data-action="project" data-id="${project.id}"><span><strong>${esc(project.name)}</strong><small>Due ${dateText(project.due_date)}</small></span><b>${value}%</b>${progress(value)}</button>`; }).join('') : empty('No active projects')}</section>
    <section class="panel"><div class="panel-header"><div><h2>Task status</h2><p>A snapshot of your team’s work</p></div><span class="badge">${state.summary.total_tasks || 0} tasks</span></div><div class="legend">${[['To Do', counts.to_do], ['In Progress', counts.in_progress], ['Completed', counts.completed], ['Overdue', counts.overdue]].map(([label, value], index) => `<div><span class="dot dot-${index}"></span>${label}<strong>${value || 0}</strong></div>`).join('')}</div></section></div>`;
}

export function projects(state) {
  return heading('A clear view of every project', 'Keep the details simple and the work moving.') + (state.projects.length ? `<div class="project-grid">${state.projects.map(project => { const value = projectProgress(project); return `<article class="panel project-card"><div class="panel-header">${pill(project.status.replaceAll('_', ' '))}</div><h2><button class="task-name" data-action="project" data-id="${project.id}">${esc(project.name)}</button></h2><p>${esc(project.description || 'No description yet.')}</p><dl class="project-meta"><div><dt>Start date</dt><dd>${dateText(project.start_date)}</dd></div><div><dt>Due date</dt><dd>${dateText(project.due_date)}</dd></div></dl><div class="progress-caption"><span>${(project.subtask_details || []).length} tasks</span><strong>${value}% complete</strong></div>${progress(value)}<div class="card-bottom"><button class="btn secondary small" data-action="project" data-id="${project.id}">View project →</button></div></article>`; }).join('')}</div>` : empty('No projects yet'));
}

export function projectDetail(state, id) {
  const project = state.projects.find(item => item.id === Number(id));
  if (!project) return empty('Project not found');
  const tasks = state.tasks.filter(task => task.project === project.id && !task.is_project_card);
  const value = projectProgress(project);
  return `<div class="back-link"><button class="btn secondary small" data-action="navigate" data-id="projects">← All projects</button></div><section class="panel">${heading(esc(project.name), esc(project.description || ''), '')}<dl class="project-meta detail-meta"><div><dt>Start date</dt><dd>${dateText(project.start_date)}</dd></div><div><dt>Due date</dt><dd>${dateText(project.due_date)}</dd></div><div><dt>Project owner</dt><dd>${esc(project.created_by_name || state.user.name)}</dd></div><div><dt>Team members</dt><dd>${esc((project.assignee_details || []).map(person => person.name).join(', '))}</dd></div></dl><div class="progress-caption"><span>Overall progress</span><strong>${value}% complete</strong></div>${progress(value)}</section><section class="panel"><div class="panel-header"><h2>Project tasks</h2><button class="btn" data-action="new-task" data-id="${project.id}">＋ Add Task</button></div>${taskTable(tasks, state.today)}</section>`;
}

function board(tasks, state) {
  return `<div class="task-board">${['To Do', 'In Progress', 'Completed'].map(status => { const items = tasks.filter(task => task.column_name === status); return `<section class="board-column"><h2>${status}<span>${items.length}</span></h2>${items.map(task => `<article class="board-card"><button class="task-name" data-action="edit-task" data-id="${task.id}">${esc(task.title)}</button><p>${esc(task.project_name || 'General work')}</p><div class="board-meta"><span>${esc(task.assignee_name || 'Unassigned')}</span>${pill(task.priority)}</div><small class="${taskStatus(task, state.today) === 'Overdue' ? 'overdue-date' : ''}">${dateText(task.due_date)}</small><select data-task-status="${task.id}" aria-label="Status for ${esc(task.title)}">${['To Do', 'In Progress', 'Completed'].map(value => `<option ${value === status ? 'selected' : ''}>${value}</option>`).join('')}</select></article>`).join('') || '<p class="column-empty">No tasks here yet</p>'}</section>`; }).join('')}</div>`;
}

export function tasks(state) {
  const visible = state.tasks.filter(task => !task.is_project_card).filter(task => `${task.title} ${task.project_name} ${task.assignee_name}`.toLowerCase().includes(state.search.toLowerCase())).filter(task => state.filter === 'All' || taskStatus(task, state.today) === state.filter);
  return `<section class="panel"><div class="tasks-toolbar"><input id="taskSearch" type="search" placeholder="Search tasks..." aria-label="Search tasks" value="${esc(state.search)}"><div class="view-switch">${['list', 'board'].map(view => `<button class="btn secondary small ${state.taskView === view ? 'selected' : ''}" data-action="view" data-id="${view}">${view === 'list' ? 'List' : 'Board'}</button>`).join('')}</div></div><div class="report-tabs">${['All', 'To Do', 'In Progress', 'Completed', 'Overdue'].map(value => `<button class="btn secondary small ${state.filter === value ? 'active' : ''}" data-action="filter" data-id="${value}">${value}</button>`).join('')}</div><div id="taskResults">${state.taskView === 'board' ? board(visible, state) : taskTable(visible, state.today)}</div></section>`;
}

export function myTasks(state) {
  const monday = new Date(`${state.today}T12:00:00`);
  monday.setDate(monday.getDate() - ((monday.getDay() + 6) % 7));
  const sunday = new Date(monday); sunday.setDate(sunday.getDate() + 6);
  const key = date => date.toISOString().slice(0, 10);
  const mine = state.tasks.filter(task => !task.is_project_card && task.assignee === state.user.id).filter(task => {
    const status = taskStatus(task, state.today);
    if (state.personalTab === 'Completed') return status === 'Completed';
    if (state.personalTab === 'Overdue') return status === 'Overdue';
    if (state.personalTab === 'Today') return task.due_date === state.today && status !== 'Completed';
    return task.due_date >= key(monday) && task.due_date <= key(sunday) && status !== 'Completed';
  });
  return heading('Your work, in one place', `Tasks assigned to ${esc(state.user.name)}`) + `<div class="report-tabs">${['Today', 'This Week', 'Overdue', 'Completed'].map(tab => `<button class="btn secondary small ${state.personalTab === tab ? 'active' : ''}" data-action="personal-tab" data-id="${tab}">${tab}</button>`).join('')}</div><section class="personal-list">${mine.length ? mine.map(task => `<article class="panel personal-task"><input type="checkbox" data-complete="${task.id}" aria-label="Complete ${esc(task.title)}" ${task.column_name === 'Completed' ? 'checked' : ''}><div><button class="task-name" data-action="edit-task" data-id="${task.id}">${esc(task.title)}</button><p>${esc(task.project_name || 'General work')} · Due ${dateText(task.due_date)}</p></div>${pill(task.priority)}${pill(taskStatus(task, state.today))}</article>`).join('') : empty('You’re all caught up in this view')}</section>`;
}

export function calendar(state) {
  const month = state.month;
  const start = new Date(month.getFullYear(), month.getMonth(), 1);
  start.setDate(start.getDate() - ((start.getDay() + 6) % 7));
  const weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(day => `<div class="weekday">${day}</div>`).join('');
  const days = Array.from({ length: 42 }, (_, index) => {
    const day = new Date(start); day.setDate(start.getDate() + index);
    const key = `${day.getFullYear()}-${String(day.getMonth() + 1).padStart(2, '0')}-${String(day.getDate()).padStart(2, '0')}`;
    const tasks = (state.calendar.tasks || []).filter(item => item.due_date === key).map(item => `<button class="calendar-event ${item.overdue ? 'late' : ''}" data-action="edit-task" data-id="${item.id}">${item.overdue ? '! ' : '• '}${esc(item.title)}</button>`).join('');
    const projects = (state.calendar.projects || []).filter(item => item.due_date === key).map(item => `<button class="calendar-event project-event" data-action="project" data-id="${item.id}">◆ ${esc(item.name)}</button>`).join('');
    return `<div class="calendar-day ${day.getMonth() !== month.getMonth() ? 'outside-month' : ''} ${key === state.today ? 'today' : ''}"><time datetime="${key}">${day.getDate()}</time>${tasks}${projects}</div>`;
  }).join('');
  return `<section class="panel"><div class="panel-header"><h2>${month.toLocaleDateString('en-ZA', { month: 'long', year: 'numeric' })}</h2><div class="actions"><button class="btn secondary small" data-action="month" data-id="-1">←</button><button class="btn secondary small" data-action="month" data-id="today">Today</button><button class="btn secondary small" data-action="month" data-id="1">→</button></div></div><div class="calendar-key"><span>• Task deadline</span><span>◆ Project deadline</span><span class="overdue-date">! Overdue work</span></div><div class="calendar-scroll"><div class="calendar-grid">${weekdays}${days}</div></div></section>`;
}

export function team(state) {
  return heading('Small team. Shared progress.', 'See who is working on what at a glance.') + `<div class="team-grid">${state.team.map(person => `<article class="panel team-card"><div class="team-avatar">${esc(person.initials)}</div><h2>${esc(person.name)}</h2><p>${esc(person.role)}</p><dl class="team-counts"><div><dd>${person.active_tasks}</dd><dt>Active tasks</dt></div><div><dd>${person.completed_tasks}</dd><dt>Completed</dt></div><div><dd>${person.due_today}</dd><dt>Due today</dt></div></dl></article>`).join('') || empty('No team activity yet')}</div>`;
}

const options = (items, selected, value = item => item.id, label = item => item.name) => items.map(item => `<option value="${esc(value(item))}" ${String(value(item)) === String(selected) ? 'selected' : ''}>${esc(label(item))}</option>`).join('');

export function taskForm(state, task = {}, projectId = '') {
  const projects = state.projects;
  return `<form data-form="task" data-id="${task.id || ''}"><div class="error" id="formError" role="alert"></div><div class="form-grid"><label class="field">Task Name *<input name="title" value="${esc(task.title)}" required maxlength="255"></label><label class="field">Project<select name="project"><option value="">General work</option>${options(projects, task.project || projectId)}</select></label><label class="field full">Description<textarea name="description">${esc(task.description)}</textarea></label><label class="field">Assigned To<select name="assignee"><option value="">Unassigned</option>${options(state.people, task.assignee)}</select></label><label class="field">Due Date<input name="due_date" type="date" value="${esc(task.due_date)}"></label><label class="field">Priority<select name="priority">${['low', 'medium', 'high', 'urgent'].map(value => `<option value="${value}" ${value === (task.priority || 'medium') ? 'selected' : ''}>${value}</option>`).join('')}</select></label><label class="field">Status<select name="status">${['To Do', 'In Progress', 'Completed'].map(value => `<option ${value === (task.column_name || 'To Do') ? 'selected' : ''}>${value}</option>`).join('')}</select></label><label class="field full">Attachment<input type="file" name="attachment" accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.txt"><small>PDF, Word, Excel, JPEG, PNG or text · maximum 25 MB.</small></label></div><div class="form-actions"><button class="btn secondary" type="button" data-action="close-modal">Cancel</button><button class="btn" type="submit">${task.id ? 'Save Changes' : 'Create Task'}</button></div></form>`;
}

export function projectForm(state) {
  return `<form data-form="project"><div class="error" id="formError" role="alert"></div><div class="form-grid"><label class="field">Project Name *<input name="name" required maxlength="255"></label><label class="field">Status<select name="status"><option value="planning">Planning</option><option value="active">Active</option><option value="on_hold">On Hold</option><option value="completed">Completed</option></select></label><label class="field full">Description<textarea name="description"></textarea></label><label class="field">Start Date *<input name="start_date" type="date" value="${state.today}" required></label><label class="field">Due Date<input name="due_date" type="date"></label><fieldset class="team-picker full"><legend>Team Members *</legend>${state.people.map(person => `<label><input type="checkbox" name="assignees" value="${person.id}" ${person.id === state.user.id ? 'checked' : ''}> ${esc(person.name)}</label>`).join('')}</fieldset></div><div class="form-actions"><button class="btn secondary" type="button" data-action="close-modal">Cancel</button><button class="btn" type="submit">Create Project</button></div></form>`;
}
