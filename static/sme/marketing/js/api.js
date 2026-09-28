const config = JSON.parse(document.querySelector('#marketing-config').textContent);
const base = config.apiBase || '/api/v1/marketing/';

function csrfToken() {
  return document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1] || '';
}

async function request(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (!(options.body instanceof FormData) && options.body !== undefined) {
    headers.set('Content-Type', 'application/json');
    options.body = JSON.stringify(options.body);
  }
  if (options.method && options.method !== 'GET') headers.set('X-CSRFToken', csrfToken());
  headers.set('Accept', 'application/json');
  const response = await fetch(`${base}${path}`, { credentials: 'same-origin', ...options, headers });
  if (response.status === 204) return null;
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload.detail || Object.entries(payload).map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(' ') : value}`).join(' ');
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return payload;
}

export const API = {
  config,
  list: async resource => {
    const separator = resource.includes('?') ? resource.replace('?', '/?') : `${resource}/`;
    const data = await request(separator);
    return Array.isArray(data) ? data : data.results || [];
  },
  get: (resource, id) => request(`${resource}/${id}/`),
  create: (resource, body) => request(`${resource}/`, { method: 'POST', body }),
  update: (resource, id, body) => request(`${resource}/${id}/`, { method: 'PATCH', body }),
  remove: (resource, id) => request(`${resource}/${id}/`, { method: 'DELETE' }),
  action: (path, body = {}) => request(path, { method: 'POST', body }),
  summary: () => request('workspace/summary/'),
  calendar: () => request('workspace/calendar/'),
  analytics: () => request('workspace/analytics/'),
  providers: () => request('workspace/provider-status/'),
};

export { request };
