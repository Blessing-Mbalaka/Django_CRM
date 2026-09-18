/* Shared presentation helpers and page templates. All user text is escaped. */
(function(A) {
    const S = A.state;
    const esc = value => String(value ?? '').replace(/[&<>"']/g, character => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    } [character]));
    const paths = {
      dashboard: 'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z',
      projects: 'M3 5h7l2 3h9v12H3z',
      tasks: 'M9 5h12M9 12h12M9 19h12M3 5l1 1 2-3M3 12l1 1 2-3M3 19l1 1 2-3',
      my: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8M4 21v-2a8 6 0 0 1 16 0v2',
      calendar: 'M4 5h16v16H4zM4 10h16M8 3v4M16 3v4M8 14h2M14 14h2M8 18h2',
      team: 'M9 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6M2 20v-2a7 5 0 0 1 14 0v2M17 5a3 3 0 0 1 0 6M18 14a5 4 0 0 1 4 4v2'
    };
    const icon = name => `<svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="${paths[name] || paths.tasks}"/></svg>`;
    const button = (label, action, id = '', style = 'secondary small') => `<button class="btn ${style}" data-action="${action}" data-id="${esc(id)}">${label}</button>`;
    const project = id => S.projects.find(item => item.id === id);
    const member = id => S.team.find(item => item.id === id);
    const date = value => new Date(`${value}T12:00:00`).toLocaleDateString('en-ZA', {
      day: 'numeric',
      month: 'short'
    });
    const pill = text => `<span class="badge status-${text.toLowerCase().replaceAll(' ', '-')}">${esc(text)}</span>`;
    const progress = value => `<div class="project-progress" role="progressbar" aria-label="Project completion" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${value}"><span style="width:${value}%"></span></div>`;
    const empty = message => `<div class="empty"><strong>${message}</strong><p>Try another view or create a new task.</p></div>`;
    const heading = (title, subtitle, action = '') => `<div class="page-heading"><div><h2>${title}</h2><p>${subtitle}</p></div>${action}</div>`;

    function taskTable(items, actions = true) {
      if (!items.length) return empty('No tasks in this view');
      return `<div class="table-wrap"><table><thead><tr>${['Task', 'Project', 'Assigned To', 'Due Date', 'Priority', 'Status', ...(actions ? ['Actions'] : [])].map(name => `<th scope="col">${name}</th>`).join('')}</tr></thead><tbody>${items.map(task => `<tr>
      <td><button class="task-name" data-action="edit-task" data-id="${task.id}">${esc(task.name)}</button></td>
      <td>${esc(project(task.project)?.name || 'No project')}</td>
      <td><span class="person"><span class="mini-avatar">${esc(member(task.assignee)?.initials || '—')}</span>${esc(member(task.assignee)?.name || 'Unassigned')}</span></td>
      <td><span class="${A.overdue(task) ? 'overdue-date' : ''}">${date(task.due)}</span></td>
      <td>${pill(task.priority)}</td><td>${pill(A.status(task))}</td>
      ${actions ? `<td><details class="task-menu"><summary aria-label="Actions for ${esc(task.name)}">•••</summary><div>${button('Edit task', 'edit-task', task.id)}${button(task.status === 'Completed' ? 'Reopen task' : 'Mark completed', 'complete', task.id)}</div></details></td>` : ''}
    </tr>`).join('')}</tbody></table></div>`;
    }

    function rose() {
      const labels = ['To Do', 'In Progress', 'Completed', 'Overdue'];
      const colors = ['#b6d9be', '#71aa8f', '#185b46', '#dcebdd'];
      const counts = labels.map(label => S.tasks.filter(task => A.status(task) === label).length);
      const maximum = Math.max(...counts, 1);
      const segments = counts.map((count, i) => {
        if (!count) return '';
        const radius = 112 * Math.sqrt(count / maximum);
        const start = -Math.PI / 2 + i * Math.PI / 2;
        const end = start + Math.PI / 2;
        const point = angle => `${130 + radius * Math.cos(angle)} ${130 + radius * Math.sin(angle)}`;
        const middle = start + Math.PI / 4;
        return `<path d="M130 130 L${point(start)} A${radius} ${radius} 0 0 1 ${point(end)} Z" fill="${colors[i]}"><title>${labels[i]}: ${count}</title></path><text x="${130 + radius * .64 * Math.cos(middle)}" y="${130 + radius * .64 * Math.sin(middle)}" fill="${i === 2 ? '#fff' : '#174d39'}">${count}</text>`;
      }).join('');
      return `<div class="task-chart"><svg viewBox="0 0 260 260" role="img" aria-label="Task status chart: ${labels.map((label, i) => `${label} ${counts[i]}`).join(', ')}">${[28, 56, 84, 112].map(radius => `<circle cx="130" cy="130" r="${radius}" fill="none" stroke="#edf1eb"/>`).join('')}${segments}</svg><div class="legend">${labels.map((label, i) => `<div><span class="dot" style="background:${colors[i]}"></span>${label}<strong>${counts[i]}</strong></div>`).join('')}</div></div>`;
    }

    function dashboard() {
      const metrics = [
        ['Active Projects', S.projects.filter(p => p.status === 'Active').length, 'Work moving forward', 'projects'],
        ['Tasks Due Today', S.tasks.filter(t => t.due === A.today && t.status !== 'Completed').length, 'Your team’s focus today', 'calendar'],
        ['Completed Tasks', S.tasks.filter(t => t.status === 'Completed').length, 'Progress worth celebrating', 'tasks'],
        ['Overdue Tasks', S.tasks.filter(A.overdue).length, 'Ready for a follow-up', 'my']
      ];
      return `<section class="banner"><div class="banner-copy"><span class="eyebrow">YOUR TEAM. ALL IN ONE PLACE.</span><h2>Welcome back, ${esc(member(S.currentUser).name)}</h2><p>Plan work, manage projects and keep your team on track.</p>${button('? New Task', 'new-task', '', 'shine')}</div><img src="../assets/inventory-banner.png" alt="Business owner organising their workspace"></section>
      <div class="stats task-stats">${metrics.map(([label, value, note, glyph]) => `<article class="stat"><div class="stat-label">${label}${icon(glyph)}</div><strong>${value}</strong><small>${note}</small></article>`).join('')}</div>
      <div class="task-dashboard-grid"><section class="panel"><div class="panel-header"><div><h2>Project progress</h2><p>A little progress, every day</p></div>${button('All projects ↗', 'navigate', 'projects')}</div>${S.projects.filter(p => p.status === 'Active').slice(0, 3).map(p => `<button class="progress-project" data-action="project" data-id="${p.id}"><span><strong>${esc(p.name)}</strong><small>Due ${date(p.due)}</small></span><b>${A.progress(p.id)}%</b>${progress(A.progress(p.id))}</button>`).join('')}</section>
      <section class="panel"><div class="panel-header"><div><h2>Task status</h2><p>A snapshot of your team’s work</p></div><span class="badge">${S.tasks.length} tasks</span></div>${rose()}</section></div>
      `;
    }

    function projects() {
      return heading('A clear view of every project', 'Keep the details simple and the work moving.') + `<div class="project-grid">${S.projects.map(p => `<article class="panel project-card"><div class="panel-header">${icon('projects')}${pill(p.status)}</div><h2><button class="task-name" data-action="project" data-id="${p.id}">${esc(p.name)}</button></h2><p>${esc(p.description)}</p><dl class="project-meta"><div><dt>Due date</dt><dd>${date(p.due)}</dd></div><div><dt>Owner</dt><dd>${esc(member(p.owner)?.name)}</dd></div></dl><div class="progress-caption"><span>${A.projectTasks(p.id).length} tasks</span><strong>${A.progress(p.id)}% complete</strong></div>${progress(A.progress(p.id))}<div class="card-bottom">${button('View project →', 'project', p.id)}</div></article>`).join('')}</div>`;
    }

    function projectDetail() {
      const p = project(S.projectId);
      if (!p) return empty('Project not found');
      return `<div class="back-link">${button('← All projects', 'navigate', 'projects')}</div><section class="panel">${heading(esc(p.name), esc(p.description), pill(p.status))}<dl class="project-meta detail-meta">${[['Start date', date(p.start)], ['Due date', date(p.due)], ['Project owner', member(p.owner)?.name], ['Team members', p.members.map(id => member(id)?.name).join(', ')]].map(([label, value]) => `<div><dt>${label}</dt><dd>${esc(value)}</dd></div>`).join('')}</dl><div class="progress-caption"><span>Overall progress</span><strong>${A.progress(p.id)}% complete</strong></div>${progress(A.progress(p.id))}</section><section class="panel"><div class="panel-header"><h2>Project tasks</h2>${button('＋ Add Task', 'new-task', p.id, '')}</div>${taskTable(A.projectTasks(p.id))}</section>`;
    }

    function filteredTasks() {
      return S.tasks.filter(task => (S.filter === 'All' || A.status(task) === S.filter) && `${task.name} ${project(task.project)?.name} ${member(task.assignee)?.name}`.toLowerCase().includes(S.search.toLowerCase()));
    }

    function board(items) {
      return `<div class="task-board">${['To Do', 'In Progress', 'Completed'].map(status => `<section class="board-column"><h2>${status}<span>${items.filter(t => t.status === status).length}</span></h2>${items.filter(t => t.status === status).map(t => `<article class="board-card"><button class="task-name" data-action="edit-task" data-id="${t.id}">${esc(t.name)}</button><p>${esc(project(t.project)?.name)}</p><div class="board-meta"><span>${esc(member(t.assignee)?.name)}</span>${pill(t.priority)}</div><small class="${A.overdue(t) ? 'overdue-date' : ''}">${A.overdue(t) ? 'Overdue · ' : ''}${date(t.due)}</small><select aria-label="Status for ${esc(t.name)}" data-task-status="${t.id}">${options(['To Do', 'In Progress', 'Completed'], t.status)}</select></article>`).join('') || '<p class="column-empty">No tasks here yet</p>'}</section>`).join('')}</div>`;
    }

    function tasks() {
      return `<section class="panel"><div class="tasks-toolbar"><input id="taskSearch" type="search" placeholder="Search tasks..." aria-label="Search tasks" value="${esc(S.search)}"><div class="view-switch" role="group" aria-label="Task view">${['list', 'board'].map(view => `<button class="btn secondary small ${S.view === view ? 'selected' : ''}" data-action="view" data-id="${view}" aria-pressed="${S.view === view}">${view === 'list' ? 'List' : 'Board'}</button>`).join('')}</div></div><div class="report-tabs" role="group" aria-label="Filter task status">${['All', 'To Do', 'In Progress', 'Completed', 'Overdue'].map(status => `<button class="btn secondary small ${S.filter === status ? 'active' : ''}" data-action="filter" data-id="${status}" aria-pressed="${S.filter === status}">${status}</button>`).join('')}</div><div id="taskResults">${taskResults()}</div></section>`;
    }
    const taskResults = () => S.view === 'board' ? board(filteredTasks()) : taskTable(filteredTasks());

    function myTasks() {
      const day = new Date(`${A.today}T12:00:00`).getDay();
      const weekStart = A.relativeDate(-((day + 6) % 7));
      const weekEnd = A.relativeDate(6 - ((day + 6) % 7));
      const items = S.tasks.filter(t => t.assignee === S.currentUser).filter(t => S.personalTab === 'Completed' ? t.status === 'Completed' : t.status !== 'Completed' && (S.personalTab === 'Overdue' ? A.overdue(t) : S.personalTab === 'Today' ? t.due === A.today : t.due >= weekStart && t.due <= weekEnd));
      return heading('Your work, in one place', `Tasks assigned to ${member(S.currentUser).name}`) + `<div class="report-tabs" role="group" aria-label="My task period">${['Today', 'This Week', 'Overdue', 'Completed'].map(tab => `<button class="btn secondary small ${S.personalTab === tab ? 'active' : ''}" data-action="personal-tab" data-id="${tab}" aria-pressed="${S.personalTab === tab}">${tab}</button>`).join('')}</div><section class="personal-list">${items.map(t => `<article class="panel personal-task"><input type="checkbox" aria-label="Complete ${esc(t.name)}" data-complete="${t.id}" ${t.status === 'Completed' ? 'checked' : ''}><div><button class="task-name" data-action="edit-task" data-id="${t.id}">${esc(t.name)}</button><p>${esc(project(t.project)?.name)} · Due ${date(t.due)}</p></div>${pill(t.priority)}${pill(A.status(t))}</article>`).join('') || empty('You’re all caught up in this view')}</section>`;
    }

    function calendar() {
      const month = S.month;
      const start = new Date(month.getFullYear(), month.getMonth(), 1);
      start.setDate(start.getDate() - (start.getDay() + 6) % 7);
      const weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        .map(day => `<div class="weekday">${day}</div>`).join('');
      const days = Array.from({ length: 42 }, (_, i) => {
        const d = new Date(start);
        d.setDate(start.getDate() + i);
        const key = A.dateKey(d);
        const tasks = S.tasks.filter(t => t.due === key).map(t =>
          `<button class="calendar-event ${A.overdue(t) ? 'late' : ''}" title="${esc(t.name)} ? ${esc(A.status(t))}" data-action="edit-task" data-id="${t.id}">${A.overdue(t) ? '! ' : '? '}${esc(t.name)}</button>`
        ).join('');
        const projects = S.projects.filter(p => p.due === key).map(p =>
          `<button class="calendar-event project-event" data-action="project" data-id="${p.id}">? ${esc(p.name)}</button>`
        ).join('');
        return `<div class="calendar-day ${d.getMonth() !== month.getMonth() ? 'outside-month' : ''} ${key === A.today ? 'today' : ''}"><time datetime="${key}">${d.getDate()}</time>${tasks}${projects}</div>`;
      }).join('');
      return `<section class="panel"><div class="panel-header"><h2>${month.toLocaleDateString('en-ZA', { month: 'long', year: 'numeric' })}</h2><div class="actions">${button('?', 'month', '-1')}${button('Today', 'month', 'today')}${button('?', 'month', '1')}</div></div><div class="calendar-key"><span>? Task deadline</span><span>? Project deadline</span><span class="overdue-date">! Overdue work</span></div><div class="calendar-scroll"><div class="calendar-grid">${weekdays}${days}</div></div></section>`;
    }

function team() {
  return heading('Small team. Shared progress.', 'See who is working on what at a glance.') + `<div class="team-grid">${S.team.map(person => {
      const tasks = S.tasks.filter(t => t.assignee === person.id);
      return `<article class="panel team-card"><div class="team-avatar">${person.initials}</div><h2>${person.name}</h2><p>${person.role}</p><dl class="team-counts">${[['Active tasks', tasks.filter(t => t.status !== 'Completed').length], ['Completed', tasks.filter(t => t.status === 'Completed').length], ['Due today', tasks.filter(t => t.due === A.today && t.status !== 'Completed').length]].map(([label, count]) => `<div><dd>${count}</dd><dt>${label}</dt></div>`).join('')}</dl></article>`;
    }).join('')}</div>`;
}

const options = (items, selected) => items.map(item => `<option value="${esc(item)}" ${item === selected ? 'selected' : ''}>${esc(item)}</option>`).join('');
const entityOptions = (items, selected) => items.map(item => `<option value="${item.id}" ${item.id === selected ? 'selected' : ''}>${esc(item.name)}</option>`).join('');
const field = (label, name, value = '', type = 'text', extra = '') => `<label class="field">${label}<input name="${name}" type="${type}" value="${esc(value)}" ${extra}></label>`;
const area = (label, name, value = '') => `<label class="field full">${label}<textarea name="${name}">${esc(value)}</textarea></label>`;

function taskForm(task = {}, projectId = '') {
  return `<form data-form="task" data-id="${task.id || ''}"><div class="error" role="alert" id="formError"></div><div class="form-grid">${field('Task Name *', 'name', task.name, 'text', 'required maxlength="150"')}
      <label class="field">Project *<select name="project" required>${entityOptions(S.projects, task.project || projectId)}</select></label>
      ${area('Description', 'description', task.description)}
      <label class="field">Assigned To *<select name="assignee" required>${entityOptions(S.team, task.assignee || S.currentUser)}</select></label>
      ${field('Due Date *', 'due', task.due || A.today, 'date', 'required')}
      <label class="field">Priority<select name="priority">${options(['Low', 'Medium', 'High'], task.priority || 'Medium')}</select></label>
      <label class="field">Status<select name="status">${options(['To Do', 'In Progress', 'Completed'], task.status || 'To Do')}</select></label>
      <label class="field full">Attachment<input type="file" name="attachment"><small>${task.attachment ? `Selected: ${esc(task.attachment)}. ` : ''}Preview only; files are not uploaded.</small></label>${area('Notes', 'notes', task.notes)}</div>
      <div class="form-actions">${button('Cancel', 'close-modal')}<button class="btn" type="submit">${task.id ? 'Save Changes' : 'Create Task'}</button></div></form>`;
}

function projectForm() {
  return `<form data-form="project"><div class="error" role="alert" id="formError"></div><div class="form-grid">${field('Project Name *', 'name', '', 'text', 'required maxlength="150"')}
      <label class="field">Project Owner *<select name="owner" required>${entityOptions(S.team, S.currentUser)}</select></label>${area('Description', 'description')}
      ${field('Start Date *', 'start', A.today, 'date', 'required')}${field('Due Date *', 'due', A.relativeDate(14), 'date', 'required')}
      <label class="field">Status<select name="status">${options(['Planning', 'Active', 'On Hold', 'Completed'], 'Planning')}</select></label>
      <fieldset class="team-picker full"><legend>Team Members</legend>${S.team.map(person => `<label><input type="checkbox" name="members" value="${person.id}"> ${person.name}</label>`).join('')}</fieldset></div>
      <div class="form-actions">${button('Cancel', 'close-modal')}<button class="btn" type="submit">Create Project</button></div></form>`;
}
A.UI = {
esc,
icon,
dashboard,
projects,
projectDetail,
tasks,
taskResults,
myTasks,
calendar,
team,
taskForm,
projectForm
};
})(window.TaskApp);
