(function (global) {
  function csrfToken() {
    const match = document.cookie.split('; ').find(item => item.startsWith('csrftoken='));
    return match ? decodeURIComponent(match.split('=').slice(1).join('=')) : '';
  }

  async function request(url, options = {}) {
    const method = (options.method || 'GET').toUpperCase();
    const headers = { Accept: 'application/json', ...(options.headers || {}) };
    if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) headers['X-CSRFToken'] = csrfToken();
    if (options.body && !(options.body instanceof FormData)) headers['Content-Type'] = 'application/json';
    const response = await fetch(url, { credentials: 'same-origin', ...options, method, headers });
    let payload = null;
    try { payload = await response.json(); } catch (_) { payload = null; }
    if (!response.ok) {
      const error = new Error(payload?.detail || `Academy request failed with status ${response.status}.`);
      error.status = response.status;
      error.payload = payload;
      throw error;
    }
    return payload;
  }

  async function listAll(url) {
    const records = [];
    let next = url;
    while (next) {
      const page = await request(next);
      if (Array.isArray(page)) return page;
      records.push(...page.results);
      next = page.next;
    }
    return records;
  }

  global.AcademyAPI = {
    request,
    list: listAll,
    get(url) { return request(url); },
    post(url, body = {}) { return request(url, { method: 'POST', body: JSON.stringify(body) }); },
    listPaths: listAll,
    listCourses: listAll,
    getCourse(coursesUrl, slug) { return request(`${coursesUrl}${encodeURIComponent(slug)}/`); }
  };
})(window);
