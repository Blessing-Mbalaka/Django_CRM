const config = JSON.parse(document.getElementById('inventoryWorkspaceConfig').textContent);

function csrfToken() {
  return document.cookie.split(';').map(value => value.trim()).find(value => value.startsWith('csrftoken='))?.split('=')[1] || '';
}

export async function request(url, options = {}) {
  const headers = {Accept: 'application/json', ...(options.headers || {})};
  if (options.body && !(options.body instanceof FormData)) headers['Content-Type'] = 'application/json';
  if (!['GET', 'HEAD'].includes((options.method || 'GET').toUpperCase())) headers['X-CSRFToken'] = csrfToken();
  const response = await fetch(url, {...options, headers, credentials: 'same-origin'});
  if (!response.ok) {
    let detail;
    try { detail = await response.json(); } catch { detail = {detail: `Request failed (${response.status}).`}; }
    const error = new Error(typeof detail === 'string' ? detail : detail.detail || Object.values(detail).flat().join(' '));
    error.data = detail;
    throw error;
  }
  if (response.status === 204) return null;
  return response.json();
}

export const unwrap = payload => payload?.results || payload || [];
export const get = url => request(url).then(unwrap);
export const create = (url, data) => request(url, {method: 'POST', body: JSON.stringify(data)});
export const update = (url, data) => request(url, {method: 'PATCH', body: JSON.stringify(data)});
export const remove = url => request(url, {method: 'DELETE'});

export function itemUrl(base, id, suffix = '') {
  return `${base}${id}/${suffix}`;
}

export function download(url, filename) {
  return fetch(url, {credentials: 'same-origin'}).then(async response => {
    if (!response.ok) throw new Error(`Download failed (${response.status}).`);
    const anchor = document.createElement('a');
    anchor.href = URL.createObjectURL(await response.blob());
    anchor.download = filename;
    document.body.append(anchor); anchor.click(); anchor.remove();
    setTimeout(() => URL.revokeObjectURL(anchor.href), 1000);
  });
}

export {config};
