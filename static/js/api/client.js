const API_ROOT = '/api/v1';

function getCookie(name) {
  return document.cookie.split(';').map((item) => item.trim()).find((item) => item.startsWith(`${name}=`))?.split('=').slice(1).join('=') || '';
}

function normaliseError(payload, status) {
  if (typeof payload === 'string') return payload;
  if (payload?.detail) return payload.detail;
  if (Array.isArray(payload)) return payload.join(' ');
  if (payload && typeof payload === 'object') {
    return Object.entries(payload).map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(' ') : messages}`).join(' ');
  }
  return `Request failed (${status}).`;
}

export async function apiRequest(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const isFormData = options.body instanceof FormData;
  if (!isFormData && options.body !== undefined) headers.set('Content-Type', 'application/json');
  headers.set('Accept', 'application/json');
  const csrfToken = decodeURIComponent(getCookie('csrftoken'));
  if (csrfToken) headers.set('X-CSRFToken', csrfToken);

  const response = await fetch(`${API_ROOT}${path}`, {
    credentials: 'same-origin',
    ...options,
    headers,
    body: isFormData || options.body === undefined ? options.body : JSON.stringify(options.body),
  });
  if (response.status === 204) return null;
  const contentType = response.headers.get('content-type') || '';
  const payload = contentType.includes('application/json') ? await response.json() : await response.text();
  if (!response.ok) throw new Error(normaliseError(payload, response.status));
  return payload;
}

export function collection(payload) {
  return Array.isArray(payload) ? payload : (payload?.results || []);
}

