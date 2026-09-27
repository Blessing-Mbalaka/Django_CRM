const configNode = document.getElementById('taskWorkspaceConfig');

export const config = configNode ? JSON.parse(configNode.textContent) : { user: {}, people: [], urls: {} };

function cookie(name) {
  return document.cookie.split(';').map(item => item.trim()).find(item => item.startsWith(`${name}=`))?.split('=').slice(1).join('=') || '';
}

function detail(payload, status) {
  if (payload?.detail) return payload.detail;
  if (payload && typeof payload === 'object') {
    return Object.entries(payload).map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(' ') : messages}`).join(' ');
  }
  return `Request failed (${status}).`;
}

export async function request(url, options = {}) {
  const method = (options.method || 'GET').toUpperCase();
  const headers = new Headers(options.headers || {});
  const isForm = options.body instanceof FormData;
  if (!isForm && options.body !== undefined) headers.set('Content-Type', 'application/json');
  headers.set('Accept', 'application/json');
  const token = decodeURIComponent(cookie('csrftoken'));
  if (token) headers.set('X-CSRFToken', token);
  const response = await fetch(url, {
    credentials: 'same-origin',
    ...options,
    method,
    headers,
    body: isForm || options.body === undefined ? options.body : JSON.stringify(options.body),
  });
  if (response.status === 204) return null;
  const type = response.headers.get('content-type') || '';
  const payload = type.includes('application/json') ? await response.json() : await response.text();
  if (!response.ok) throw new Error(detail(payload, response.status));
  return payload;
}

export const collection = payload => Array.isArray(payload) ? payload : (payload?.results || []);
const itemUrl = (base, id) => `${base}${encodeURIComponent(id)}/`;

export const api = {
  boards: () => request(config.urls.boards),
  board: id => request(itemUrl(config.urls.boards, id)),
  createBoard: body => request(config.urls.boards, { method: 'POST', body }),
  tasks: board => request(`${config.urls.tasks}?board=${encodeURIComponent(board)}`),
  createTask: body => request(config.urls.tasks, { method: 'POST', body }),
  updateTask: (id, body) => request(itemUrl(config.urls.tasks, id), { method: 'PATCH', body }),
  deleteTask: id => request(itemUrl(config.urls.tasks, id), { method: 'DELETE' }),
  moveTask: (id, column, position = 0) => request(`${itemUrl(config.urls.tasks, id)}move/`, { method: 'POST', body: { column, position } }),
  projects: board => request(`${config.urls.projects}?board=${encodeURIComponent(board)}`),
  createProject: body => request(config.urls.projects, { method: 'POST', body }),
  updateProject: (id, body) => request(itemUrl(config.urls.projects, id), { method: 'PATCH', body }),
  dashboard: () => request(config.urls.dashboard),
  calendar: (start, end) => request(`${config.urls.calendar}?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`),
  team: () => request(config.urls.team),
  attachments: task => request(`${config.urls.attachments}?task=${encodeURIComponent(task)}`),
  uploadAttachment(task, file) {
    const body = new FormData();
    body.append('task', task);
    body.append('file', file);
    return request(config.urls.attachments, { method: 'POST', body });
  },
  deleteAttachment: id => request(itemUrl(config.urls.attachments, id), { method: 'DELETE' }),
};
