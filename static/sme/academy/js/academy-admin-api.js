(function (global) {
  const token = () => (document.cookie.split('; ').find(value => value.startsWith('csrftoken=')) || '').split('=').slice(1).join('=');
  async function request(url, options = {}) {
    const method = (options.method || 'GET').toUpperCase();
    const headers = { Accept: 'application/json', ...(options.headers || {}) };
    if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) headers['X-CSRFToken'] = decodeURIComponent(token());
    if (options.body && !(options.body instanceof FormData)) headers['Content-Type'] = 'application/json';
    const response = await fetch(url, { credentials: 'same-origin', ...options, method, headers });
    let payload = null;
    try { payload = await response.json(); } catch (_) { payload = null; }
    if (!response.ok) {
      const error = new Error(payload?.detail || `Request failed (${response.status}).`);
      error.status = response.status; error.fields = payload || {};
      throw error;
    }
    return payload;
  }
  global.AcademyAdminAPI = {
    request,
    list: url => request(url).then(data => Array.isArray(data) ? data : data.results),
    save: (url, value, id) => request(id ? `${url}${id}/` : url, { method: id ? 'PATCH' : 'POST', body: value instanceof FormData ? value : JSON.stringify(value) }),
    remove: (url, id) => request(`${url}${id}/`, { method: 'DELETE' }),
  };
})(window);
