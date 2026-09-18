(function (global) {
  async function request(url) {
    const response = await fetch(url, {
      credentials: 'same-origin',
      headers: { Accept: 'application/json' }
    });
    if (!response.ok) {
      const error = new Error(`Academy request failed with status ${response.status}.`);
      error.status = response.status;
      throw error;
    }
    return response.json();
  }

  async function listAll(url) {
    const records = [];
    let next = url;
    while (next) {
      const page = await request(next);
      records.push(...page.results);
      next = page.next;
    }
    return records;
  }

  global.AcademyAPI = {
    listPaths(url) {
      return listAll(url);
    },
    listCourses(url) {
      return listAll(url);
    },
    getCourse(coursesUrl, slug) {
      return request(`${coursesUrl}${encodeURIComponent(slug)}/`);
    }
  };
})(window);

