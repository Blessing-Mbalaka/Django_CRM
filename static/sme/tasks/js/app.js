import { api, collection, config } from './api.js';
import * as View from './views.js';

const $ = selector => document.querySelector(selector);
const pages = { dashboard: 'Task & Project Management', projects: 'Projects', tasks: 'Tasks', my: 'My Tasks', calendar: 'Calendar', team: 'Team' };
const state = {
  user: config.user,
  people: config.people,
  banner: document.body.dataset.banner,
  boards: [], board: null, tasks: [], projects: [], summary: {}, team: [], calendar: { tasks: [], projects: [] },
  page: 'dashboard', projectId: '', search: '', filter: 'All', taskView: 'list', personalTab: 'Today',
  month: new Date(new Date().getFullYear(), new Date().getMonth(), 1),
  today: new Date().toLocaleDateString('en-CA'),
};
let modalTrigger = null;

function notify(message, error = false) {
  const item = document.createElement('div');
  item.className = `toast${error ? ' error-toast' : ''}`;
  item.textContent = message;
  $('#toasts').append(item);
  setTimeout(() => item.remove(), 4500);
}

function status(message = '', error = false) {
  const root = $('#workspaceStatus');
  root.hidden = !message;
  root.classList.toggle('error', error);
  root.textContent = message;
}

function showModal(title, html) {
  modalTrigger = document.activeElement;
  $('#modalTitle').textContent = title;
  $('#modalBody').innerHTML = html;
  if (!$('#modal').open) $('#modal').showModal();
  $('#modal input:not([type="hidden"]), #modal select, #modal textarea')?.focus();
}

function closeModal() {
  $('#modal').close();
  $('#modalBody').innerHTML = '';
  modalTrigger?.focus?.();
}

function canManageBoard() {
  return state.board && state.board.owner === state.user.id;
}

function column(name) {
  return state.board?.columns.find(item => item.name === name);
}

function routeParts() {
  const [candidate, id] = (location.hash.slice(1) || 'dashboard').split('/');
  if (candidate === 'project' && id) return ['project', id];
  return [pages[candidate] ? candidate : 'dashboard', ''];
}

async function loadBoard(id) {
  state.board = await api.board(id);
  const [tasks, projects] = await Promise.all([api.tasks(id), api.projects(id)]);
  state.tasks = collection(tasks);
  state.projects = collection(projects);
  $('#boardSelect').value = String(id);
}

async function refresh() {
  const [summary, team] = await Promise.all([api.dashboard(), api.team()]);
  state.summary = summary;
  state.team = team;
  if (state.board) await loadBoard(state.board.id);
}

function calendarRange() {
  const start = new Date(state.month.getFullYear(), state.month.getMonth(), 1);
  start.setDate(start.getDate() - ((start.getDay() + 6) % 7));
  const end = new Date(start); end.setDate(end.getDate() + 41);
  const key = date => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
  return [key(start), key(end)];
}

async function loadCalendar() {
  const [start, end] = calendarRange();
  state.calendar = await api.calendar(start, end);
}

function render() {
  const [page, id] = routeParts();
  state.page = page;
  state.projectId = id;
  document.body.classList.toggle('dashboard-page', page === 'dashboard');
  $('#pageTitle').textContent = page === 'project' ? 'Project Details' : pages[page];
  document.title = `${$('#pageTitle').textContent} · EIEAAS`;
  document.querySelectorAll('[data-route]').forEach(button => {
    const active = button.dataset.route === page || (page === 'project' && button.dataset.route === 'projects');
    button.classList.toggle('active', active);
    if (active) button.setAttribute('aria-current', 'page'); else button.removeAttribute('aria-current');
  });
  const primary = $('#primaryAction');
  primary.hidden = page === 'team' || !canManageBoard();
  primary.textContent = page === 'projects' ? '＋ New Project' : '＋ New Task';
  primary.dataset.action = page === 'projects' ? 'new-project' : 'new-task';
  primary.dataset.id = page === 'project' ? id : '';
  const views = {
    dashboard: () => View.dashboard(state),
    projects: () => View.projects(state),
    project: () => View.projectDetail(state, id),
    tasks: () => View.tasks(state),
    my: () => View.myTasks(state),
    calendar: () => View.calendar(state),
    team: () => View.team(state),
  };
  $('#content').innerHTML = views[page]();
}

async function navigate() {
  try {
    const [page] = routeParts();
    if (page === 'calendar') await loadCalendar();
    render();
    $('#sidebar').classList.remove('open');
    $('#menuButton').setAttribute('aria-expanded', 'false');
    $('#content').focus({ preventScroll: true });
  } catch (error) {
    status(error.message, true);
  }
}

async function openTask(id = '', projectId = '') {
  const task = id ? state.tasks.find(item => item.id === Number(id)) : {};
  if (id && !task) return notify('Task could not be found.', true);
  showModal(task?.id ? 'Edit Task' : 'New Task', View.taskForm(state, task, projectId));
  if (task?.id) {
    try {
      const attachments = collection(await api.attachments(task.id));
      if (attachments.length) {
        const list = document.createElement('div');
        list.className = 'attachment-list';
        list.innerHTML = `<h3>Attachments</h3>${attachments.map(item => `<div><a href="${View.esc(item.download_url)}">${View.esc(item.original_name)}</a><button type="button" class="btn secondary small" data-action="delete-attachment" data-id="${item.id}">Remove</button></div>`).join('')}`;
        $('#modalBody form').insertAdjacentElement('beforeend', list);
      }
    } catch (error) { notify(error.message, true); }
  }
}

async function saveTask(form) {
  const id = form.dataset.id;
  const project = state.projects.find(item => item.id === Number(form.elements.project.value));
  const payload = {
    title: form.elements.title.value.trim(),
    description: form.elements.description.value.trim(),
    priority: form.elements.priority.value,
    assignee: form.elements.assignee.value ? Number(form.elements.assignee.value) : null,
    due_date: form.elements.due_date.value || null,
  };
  let task;
  if (id) {
    task = await api.updateTask(id, payload);
  } else {
    payload.board = state.board.id;
    payload.column = column('To Do').id;
    if (project?.kanban_task) payload.parent_task = project.kanban_task;
    task = await api.createTask(payload);
  }
  const destination = column(form.elements.status.value);
  if (destination && task.column !== destination.id) await api.moveTask(task.id, destination.id, 0);
  const file = form.elements.attachment.files[0];
  if (file) await api.uploadAttachment(task.id, file);
  closeModal();
  await refresh();
  render();
  notify(id ? 'Task updated.' : 'Task created.');
}

async function saveProject(form) {
  const assignees = [...form.querySelectorAll('[name="assignees"]:checked')].map(input => Number(input.value));
  const payload = {
    board: state.board.id,
    name: form.elements.name.value.trim(),
    description: form.elements.description.value.trim(),
    start_date: form.elements.start_date.value,
    due_date: form.elements.due_date.value || null,
    status: form.elements.status.value,
    assignees,
  };
  await api.createProject(payload);
  closeModal();
  await refresh();
  render();
  notify('Project created and assigned.');
}

document.addEventListener('click', async event => {
  const target = event.target.closest('[data-action], [data-route]');
  if (!target) return;
  const action = target.dataset.action;
  const id = target.dataset.id || '';
  try {
    if (target.dataset.route) { location.hash = target.dataset.route; return; }
    if (action === 'navigate') location.hash = id;
    if (action === 'project') location.hash = `project/${id}`;
    if (action === 'new-task') await openTask('', id);
    if (action === 'edit-task') await openTask(id);
    if (action === 'new-project') showModal('New Project', View.projectForm(state));
    if (action === 'close-modal') closeModal();
    if (action === 'view') { state.taskView = id; render(); }
    if (action === 'filter') { state.filter = id; render(); }
    if (action === 'personal-tab') { state.personalTab = id; render(); }
    if (action === 'month') {
      state.month = id === 'today' ? new Date(new Date().getFullYear(), new Date().getMonth(), 1) : new Date(state.month.getFullYear(), state.month.getMonth() + Number(id), 1);
      await loadCalendar(); render();
    }
    if (action === 'delete-attachment') {
      await api.deleteAttachment(id);
      target.closest('div').remove();
      notify('Attachment removed.');
    }
  } catch (error) { notify(error.message, true); }
});

document.addEventListener('change', async event => {
  if (event.target.matches('[data-task-status]')) {
    const task = state.tasks.find(item => item.id === Number(event.target.dataset.taskStatus));
    const destination = column(event.target.value);
    try { await api.moveTask(task.id, destination.id, 0); await refresh(); render(); notify('Task status updated.'); } catch (error) { notify(error.message, true); }
  }
  if (event.target.matches('[data-complete]')) {
    const destination = column(event.target.checked ? 'Completed' : 'To Do');
    try { await api.moveTask(event.target.dataset.complete, destination.id, 0); await refresh(); render(); } catch (error) { notify(error.message, true); }
  }
});

document.addEventListener('input', event => {
  if (event.target.id === 'taskSearch') { state.search = event.target.value; $('#taskResults').innerHTML = View.tasks(state).match(/<div id="taskResults">([\s\S]*)<\/div><\/section>$/)?.[1] || ''; }
});

$('#modalBody').addEventListener('submit', async event => {
  event.preventDefault();
  const form = event.target;
  const submit = form.querySelector('[type="submit"]');
  submit.disabled = true;
  try {
    if (form.dataset.form === 'task') await saveTask(form);
    if (form.dataset.form === 'project') await saveProject(form);
  } catch (error) {
    form.querySelector('#formError').textContent = error.message;
    submit.disabled = false;
  }
});

$('#primaryAction').addEventListener('click', event => event.target.dataset.action === 'new-project' ? showModal('New Project', View.projectForm(state)) : openTask('', event.target.dataset.id));
$('#boardSelect').addEventListener('change', async event => { try { await loadBoard(event.target.value); render(); } catch (error) { status(error.message, true); } });
$('#sidebarToggle').addEventListener('click', () => { const expanded = document.body.classList.toggle('sidebar-expanded'); $('#sidebarToggle').setAttribute('aria-expanded', String(expanded)); });
$('#menuButton').addEventListener('click', () => { const open = $('#sidebar').classList.toggle('open'); $('#menuButton').setAttribute('aria-expanded', String(open)); });
window.addEventListener('hashchange', navigate);

async function start() {
  try {
    state.boards = collection(await api.boards());
    if (!state.boards.length) state.boards = [await api.createBoard({ name: 'My Work', description: 'Daily SME operations' })];
    $('#boardSelect').innerHTML = state.boards.map(board => `<option value="${board.id}">${View.esc(board.name)}</option>`).join('');
    const requested = Number(new URLSearchParams(location.search).get('board'));
    const initial = state.boards.find(board => board.id === requested) || state.boards[0];
    await loadBoard(initial.id);
    await refresh();
    await navigate();
  } catch (error) {
    status(error.message, true);
    $('#content').innerHTML = '<section class="panel"><div class="empty"><strong>Task workspace could not be opened</strong><p>Reload the page or contact an administrator.</p></div></section>';
  }
}

start();
