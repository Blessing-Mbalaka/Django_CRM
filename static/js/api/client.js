const API_ROOT = '/api/v1';

function getCookie(name) {
  return document.cookie.split(';').map((item) => item.trim()).find((item) => item.startsWith(`${name}=`))?.split('=').slice(1).join('=') || '';
}

function normaliseError(payload, status) {
  if (typeof payload === 'string') {
    const plainText = payload.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
    return plainText.slice(0, 240) || `Request failed (${status}).`;
  }
  if (payload?.detail) return payload.detail;
  if (Array.isArray(payload)) return payload.join(' ');
  if (payload && typeof payload === 'object') {
    return Object.entries(payload).map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(' ') : messages}`).join(' ');
  }
  return `Request failed (${status}).`;
}

export class ApiError extends Error {
  constructor({ method, path, status, detail }) {
    super(`${method} /api/v1${path} failed (${status}): ${detail}`);
    this.name = 'ApiError';
    this.method = method;
    this.path = path;
    this.status = status;
    this.detail = detail;
  }
}

export async function apiRequest(path, options = {}) {
  const method = (options.method || 'GET').toUpperCase();
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
  if (response.redirected && !(response.headers.get('content-type') || '').includes('application/json')) {
    throw new ApiError({ method, path, status: 401, detail: 'Authentication may have expired. Reload the page and sign in again.' });
  }
  if (response.status === 204) return null;
  const contentType = response.headers.get('content-type') || '';
  const payload = contentType.includes('application/json') ? await response.json() : await response.text();
  if (!response.ok) throw new ApiError({ method, path, status: response.status, detail: normaliseError(payload, response.status) });
  return payload;
}

export function collection(payload) {
  return Array.isArray(payload) ? payload : (payload?.results || []);
}
