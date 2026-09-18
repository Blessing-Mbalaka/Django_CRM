(function (API) {
  const root = document.querySelector('#academyApp');
  const pageTitle = document.querySelector('#pageTitle');
  const sidebar = document.querySelector('#sidebar');
  const state = { paths: [], courses: [], selectedPath: 'all', query: '' };

  const escapeHtml = value => String(value ?? '').replace(/[&<>'"]/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
  })[character]);

  function paragraphText(value) {
    return escapeHtml(value).split(/\n{2,}/).map(text => `<p>${text.replaceAll('\n', '<br>')}</p>`).join('');
  }

  function safeResourceUrl(value) {
    try {
      const url = new URL(value, window.location.origin);
      return ['http:', 'https:'].includes(url.protocol) ? url.href : '';
    } catch (_) {
      return '';
    }
  }

  function courseCard(course) {
    return `<article class="panel knowledge-card course-card">
      <div class="course-card-body">
        <span class="badge">${escapeHtml(course.level_label)} · ${course.duration_minutes} min</span>
        <h2>${escapeHtml(course.title)}</h2>
        <p>${escapeHtml(course.description)}</p>
        <small>${escapeHtml(course.path.title)} · ${escapeHtml(course.instructor_name)}</small>
        <div class="card-actions"><a class="btn secondary small" href="#course/${encodeURIComponent(course.slug)}">Open course →</a></div>
      </div>
    </article>`;
  }

  function renderList() {
    pageTitle.textContent = 'SME Academy Courses';
    const query = state.query.trim().toLowerCase();
    const courses = state.courses.filter(course => {
      const pathMatches = state.selectedPath === 'all' || course.path.slug === state.selectedPath;
      const textMatches = !query || `${course.title} ${course.description} ${course.path.title}`.toLowerCase().includes(query);
      return pathMatches && textMatches;
    });
    const pathOptions = state.paths.map(path => (
      `<option value="${escapeHtml(path.slug)}" ${state.selectedPath === path.slug ? 'selected' : ''}>${escapeHtml(path.title)}</option>`
    )).join('');
    root.innerHTML = `<div class="page-heading"><div><h2>Courses</h2><p>Choose practical learning configured by your Academy administrators.</p></div></div>
      <section class="panel"><div class="filters">
        <label>Search<input id="courseSearch" type="search" value="${escapeHtml(state.query)}" placeholder="Search courses…"></label>
        <label>Learning path<select id="pathFilter"><option value="all">All paths</option>${pathOptions}</select></label>
      </div></section>
      <div id="courseResults" class="knowledge-grid">${courses.length ? courses.map(courseCard).join('') : '<section class="panel"><h2>No courses found</h2><p>Try a different path or search phrase.</p></section>'}</div>`;
    root.focus({ preventScroll: true });
  }

  function videoModule(module) {
    const prefix = 'https://www.youtube-nocookie.com/embed/';
    if (!module.video_embed_url.startsWith(prefix)) {
      return '<p class="notice">This video URL is not available.</p>';
    }
    return `<div class="academy-video"><iframe
      src="${escapeHtml(module.video_embed_url)}"
      title="${escapeHtml(module.title)}"
      loading="lazy"
      referrerpolicy="strict-origin-when-cross-origin"
      sandbox="allow-scripts allow-same-origin allow-presentation"
      allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; web-share"
      allowfullscreen></iframe></div>${paragraphText(module.body)}`;
  }

  function moduleContent(module) {
    if (module.type === 'video') return videoModule(module);
    if (module.type === 'quiz') {
      const options = module.quiz_options.map((option, index) => (
        `<label class="learning-check"><input type="radio" name="quiz-option" value="${index}"> ${escapeHtml(option)}</label>`
      )).join('');
      return `${paragraphText(module.body)}<fieldset class="quiz-options"><legend>${escapeHtml(module.prompt)}</legend>${options}</fieldset>`;
    }
    const resourceUrl = safeResourceUrl(module.resource_url);
    const resource = resourceUrl ? `<p><a class="btn secondary small" href="${escapeHtml(resourceUrl)}" target="_blank" rel="noopener noreferrer">Open resource ↗</a></p>` : '';
    const prompt = module.prompt ? `<div class="notice"><strong>Your prompt</strong><p>${escapeHtml(module.prompt)}</p></div>` : '';
    return `${paragraphText(module.body)}${prompt}${resource}`;
  }

  function renderCourse(course, selectedIndex = 0) {
    const modules = course.modules || [];
    const module = modules[selectedIndex];
    pageTitle.textContent = course.title;
    if (!module) {
      root.innerHTML = `<a class="btn secondary small" href="#courses">← Courses</a><section class="panel"><h2>${escapeHtml(course.title)}</h2><p>No published modules are available yet.</p></section>`;
      return;
    }
    const lessons = modules.map((item, index) => (
      `<button class="lesson-button ${index === selectedIndex ? 'selected' : ''}" data-module-index="${index}" ${index === selectedIndex ? 'aria-current="step"' : ''}><span>${index + 1}</span>${escapeHtml(item.title)}</button>`
    )).join('');
    root.innerHTML = `<div class="back-row"><a class="btn secondary small" href="#courses">← Courses</a><span class="badge">${escapeHtml(course.level_label)}</span></div>
      <div class="page-heading"><div><h2>${escapeHtml(course.title)}</h2><p>${escapeHtml(course.description)}</p><small>${course.duration_minutes} minutes · ${escapeHtml(course.instructor_name)}</small></div></div>
      <div class="course-layout"><aside class="panel lesson-list">${lessons}</aside><section class="panel lesson-content"><h2>${escapeHtml(module.title)}</h2>${moduleContent(module)}</section></div>`;
    root.querySelectorAll('[data-module-index]').forEach(button => {
      button.addEventListener('click', () => renderCourse(course, Number(button.dataset.moduleIndex)));
    });
    root.focus({ preventScroll: true });
  }

  async function route() {
    const [page, slug] = window.location.hash.slice(1).split('/');
    if (page === 'course' && slug) {
      root.innerHTML = '<section class="panel"><h2>Loading course…</h2></section>';
      try {
        renderCourse(await API.getCourse(root.dataset.coursesUrl, slug));
      } catch (error) {
        renderError(error);
      }
      return;
    }
    renderList();
  }

  function renderError(error) {
    if (error.status === 401 || error.status === 403) {
      window.location.assign(`/accounts/login/?next=${encodeURIComponent(window.location.pathname + window.location.hash)}`);
      return;
    }
    root.innerHTML = '<section class="panel"><h2>Courses could not be loaded</h2><p>Please refresh the page or try again later.</p></section>';
  }

  async function start() {
    try {
      [state.paths, state.courses] = await Promise.all([
        API.listPaths(root.dataset.pathsUrl),
        API.listCourses(root.dataset.coursesUrl)
      ]);
      await route();
    } catch (error) {
      renderError(error);
    }
  }

  document.addEventListener('input', event => {
    if (event.target.id === 'courseSearch') {
      state.query = event.target.value;
      renderList();
      document.querySelector('#courseSearch').focus();
    }
  });
  document.addEventListener('change', event => {
    if (event.target.id === 'pathFilter') {
      state.selectedPath = event.target.value;
      renderList();
    }
  });
  document.querySelector('#sidebarToggle').addEventListener('click', event => {
    const expanded = document.body.classList.toggle('sidebar-expanded');
    event.currentTarget.setAttribute('aria-expanded', String(expanded));
  });
  document.querySelector('#menuButton').addEventListener('click', event => {
    const open = sidebar.classList.toggle('open');
    event.currentTarget.setAttribute('aria-expanded', String(open));
  });
  document.querySelectorAll('[data-href]').forEach(button => {
    button.addEventListener('click', () => window.location.assign(button.dataset.href));
  });
  window.addEventListener('hashchange', route);
  start();
})(window.AcademyAPI);
