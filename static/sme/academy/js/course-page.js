(function (API) {
  const root = document.querySelector('#academyApp');
  const pageTitle = document.querySelector('#pageTitle');
  const sidebar = document.querySelector('#sidebar');
  const toolsData = document.querySelector('#academy-tools-data');
  const state = {
    paths: [], courses: [], tools: toolsData ? JSON.parse(toolsData.textContent) : [],
    selectedPath: 'all', selectedCategory: 'all', selectedLevel: 'all', query: '', enrollment: null
  };
  const esc = value => String(value ?? '').replace(/[&<>'"]/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
  })[character]);
  const endpoint = name => root.dataset[`${name}Url`];
  const results = payload => Array.isArray(payload) ? payload : payload.results;
  const paragraphs = value => esc(value).split(/\n{2,}/).map(text => `<p>${text.replaceAll('\n', '<br>')}</p>`).join('');
  const categoryName = item => item.category?.name || item.category_detail?.name || 'General';
  const toolIcon = path => `<svg class="tool-card-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="${esc(path)}"></path></svg>`;
  const manageButton = (entity, label = 'Add content') => window.AcademyAdmin?.canManage ? `<button class="btn secondary" data-admin-open="${entity}">${esc(label)}</button>` : '';

  async function enrollments() {
    return API.list(endpoint('enrollments'));
  }

  async function renderDashboard() {
    setRouteUi('dashboard', 'Academy Dashboard');
    const learnerCourses = await enrollments();
    const completed = learnerCourses.filter(item => item.status === 'completed').length;
    const certificates = learnerCourses.filter(item => item.certificate).length;
    root.innerHTML = `<div class="page-heading"><div><h2>Welcome to the SME Academy</h2><p>Your learning, business support and CRM tools are available from one workspace.</p></div></div>
      <div class="knowledge-grid academy-summary-grid">
        <article class="panel"><span class="badge">Learning catalogue</span><h2>${state.courses.length} courses</h2><p>${state.paths.length} administrator-configured learning paths.</p><a class="btn secondary small" href="#courses">Browse courses</a></article>
        <article class="panel"><span class="badge">My progress</span><h2>${learnerCourses.length} enrolled</h2><p>${completed} completed course${completed === 1 ? '' : 's'}.</p><a class="btn secondary small" href="#learning">Continue learning</a></article>
        <article class="panel"><span class="badge">Achievements</span><h2>${certificates} certificate${certificates === 1 ? '' : 's'}</h2><p>Certificates are issued automatically after a passing completion.</p><a class="btn secondary small" href="#certificates">View certificates</a></article>
        <article class="panel"><span class="badge">Business support</span><h2>${state.tools.length} tools</h2><p>Open the CRM applications available for your account.</p><a class="btn secondary small" href="#tools">Open business tools</a></article>
      </div>`;
  }

  async function renderLearning() {
    setRouteUi('learning', 'My Learning');
    const learnerCourses = await enrollments();
    root.innerHTML = `<div class="page-heading"><div><h2>My learning</h2><p>Continue enrolled courses and review your recorded progress.</p></div></div>
      <div class="knowledge-grid">${learnerCourses.length ? learnerCourses.map(item => `<article class="panel knowledge-card"><span class="badge">${esc(item.status.replaceAll('_', ' '))}</span><h2>${esc(item.course.title)}</h2><p>${esc(item.course.description || '')}</p><small>${item.final_grade === null ? 'Grade not yet recorded' : `${esc(item.final_grade)}% final grade`}</small><div class="card-actions"><a class="btn secondary small" href="#course/${encodeURIComponent(item.course.slug)}">${item.status === 'completed' ? 'Review course' : 'Continue course'}</a></div></article>`).join('') : '<section class="panel"><h2>No enrolled courses yet</h2><p>Choose a course to begin tracking your learning.</p><a class="btn" href="#courses">Browse courses</a></section>'}</div>`;
  }

  function renderPaths() {
    setRouteUi('paths', 'Learning Paths');
    root.innerHTML = `<div class="page-heading"><div><h2>Learning paths</h2><p>Follow administrator-configured pathways through the course catalogue.</p></div>${manageButton('paths', 'Add learning path')}</div>
      <div class="knowledge-grid">${state.paths.length ? state.paths.map(path => {
        const courses = state.courses.filter(course => course.path.slug === path.slug);
        return `<article class="panel knowledge-card"><span class="badge">${courses.length} course${courses.length === 1 ? '' : 's'}</span><h2>${esc(path.title)}</h2><p>${esc(path.description || '')}</p><div class="completed-list">${courses.map(course => `<div><strong>${esc(course.title)}</strong><span>${esc(course.level_label)} · ${course.duration_minutes} min</span></div>`).join('') || '<p>No published courses yet.</p>'}</div><a class="btn secondary small" href="#courses" data-select-path="${esc(path.slug)}">View path courses</a></article>`;
      }).join('') : '<section class="panel"><h2>No learning paths published yet</h2></section>'}</div>`;
    root.querySelectorAll('[data-select-path]').forEach(link => link.addEventListener('click', () => { state.selectedPath = link.dataset.selectPath; }));
  }

  function renderTools() {
    setRouteUi('tools', 'Business Tools');
    root.innerHTML = `<section class="banner sme-tools-banner"><div class="banner-copy"><span class="eyebrow">Your business, organised</span><h2>Run. Manage. Grow.</h2><p>Open the connected tools that help you manage customers, money, operations and growth from one SME workspace.</p><a class="btn shine" href="#dashboard">View Academy dashboard</a></div><img src="${esc(endpoint('toolsBanner'))}" alt="" aria-hidden="true"></section>
      <div class="page-heading"><div><h2>Business tools</h2><p>The same role-aware CRM applications shown on the main landing page, using canonical application routes.</p></div></div>
      <div class="knowledge-grid academy-tools-grid">${state.tools.length ? state.tools.map(item => `<article class="panel knowledge-card academy-tool-card">${toolIcon(item.svg_path)}<span class="badge">${esc(item.group)}</span><h2>${esc(item.label)}</h2><p>${esc(item.description)}</p>${item.coming_soon ? '<span class="badge">Coming soon</span>' : `<a class="btn secondary small" href="${esc(item.url)}">Open tool</a>`}</article>`).join('') : '<section class="panel"><h2>No business tools are available for this account</h2></section>'}</div>`;
  }

  async function renderGrowth() {
    setRouteUi('growth', 'Growth');
    const learnerCourses = await enrollments();
    const completed = learnerCourses.filter(item => item.status === 'completed');
    root.innerHTML = `<div class="page-heading"><div><h2>Growth</h2><p>Use your recorded learning progress and business diagnostic results to choose the next action.</p></div></div>
      <div class="knowledge-grid"><article class="panel"><span class="badge">Learning progress</span><h2>${completed.length} course${completed.length === 1 ? '' : 's'} completed</h2><p>Continue building capability through the Academy catalogue.</p><a class="btn secondary small" href="#learning">Review progress</a></article><article class="panel"><span class="badge">Business health</span><h2>Run a diagnostic</h2><p>Get scored recommendations from assessments configured by an administrator.</p><a class="btn secondary small" href="#diagnostics">Open diagnostics</a></article></div>`;
  }

  async function renderCertificates() {
    setRouteUi('certificates', 'Certificates');
    const learnerCourses = await enrollments();
    const certified = learnerCourses.filter(item => item.certificate);
    root.innerHTML = `<div class="page-heading"><div><h2>Certificates</h2><p>Certificates are generated when a course is completed at or above its configured passing grade.</p></div></div>
      <div class="knowledge-grid">${certified.length ? certified.map(item => `<article class="panel knowledge-card"><span class="badge">Completed</span><h2>${esc(item.course.title)}</h2><p>Final grade: ${esc(item.final_grade)}%</p><a class="btn secondary small" href="${esc(item.certificate.print_url)}">View certificate</a></article>`).join('') : '<section class="panel"><h2>No certificates yet</h2><p>Complete and pass a course to receive your first certificate.</p><a class="btn" href="#learning">My learning</a></section>'}</div>`;
  }

  function csrfError(error) {
    if (error.status === 401 || error.status === 403) {
      window.location.assign(`/accounts/login/?next=${encodeURIComponent(window.location.pathname + window.location.hash)}`);
      return true;
    }
    return false;
  }

  function showError(error, heading = 'This content could not be loaded') {
    if (csrfError(error)) return;
    root.innerHTML = `<section class="panel"><h2>${esc(heading)}</h2><p>${esc(error.message || 'Please try again.')}</p></section>`;
  }

  function setRouteUi(name, title) {
    pageTitle.textContent = title;
    document.querySelectorAll('[data-route]').forEach(button => {
      const active = button.dataset.route === name;
      button.classList.toggle('active', active);
      if (active) button.setAttribute('aria-current', 'page'); else button.removeAttribute('aria-current');
    });
  }

  function categoryOptions(items, selected) {
    const categories = new Map();
    items.forEach(item => {
      const category = item.category || item.category_detail;
      if (category) categories.set(category.slug, category.name);
    });
    return [...categories].map(([slug, name]) => `<option value="${esc(slug)}" ${slug === selected ? 'selected' : ''}>${esc(name)}</option>`).join('');
  }

  function courseCard(course) {
    const status = course.enrollment_status.replaceAll('_', ' ');
    return `<article class="panel knowledge-card course-card"><div class="course-card-body">
      <span class="badge">${esc(course.level_label)} · ${course.duration_minutes} min · ${esc(status)}</span>
      <h2>${esc(course.title)}</h2><p>${esc(course.description)}</p>
      <small>${esc(course.path.title)} · ${esc(course.instructor_name)}</small>
      <div class="card-actions"><a class="btn secondary small" href="#course/${encodeURIComponent(course.slug)}">Open course →</a></div>
    </div></article>`;
  }

  function renderCourses() {
    setRouteUi('courses', 'SME Academy Courses');
    const query = state.query.trim().toLowerCase();
    const courses = state.courses.filter(course => {
      const pathMatches = state.selectedPath === 'all' || course.path.slug === state.selectedPath;
      const categoryMatches = state.selectedCategory === 'all' || course.category?.slug === state.selectedCategory;
      const levelMatches = state.selectedLevel === 'all' || course.level_config?.slug === state.selectedLevel || course.level === state.selectedLevel;
      return pathMatches && categoryMatches && levelMatches && (!query || `${course.title} ${course.description} ${course.path.title}`.toLowerCase().includes(query));
    });
    const paths = state.paths.map(path => `<option value="${esc(path.slug)}" ${state.selectedPath === path.slug ? 'selected' : ''}>${esc(path.title)}</option>`).join('');
    const categories = [...new Map(state.courses.filter(course => course.category).map(course => [course.category.slug, course.category.name]))].map(([slug, name]) => `<option value="${esc(slug)}" ${state.selectedCategory === slug ? 'selected' : ''}>${esc(name)}</option>`).join('');
    const levels = [...new Map(state.courses.map(course => [course.level_config?.slug || course.level, course.level_label]))].map(([slug, name]) => `<option value="${esc(slug)}" ${state.selectedLevel === slug ? 'selected' : ''}>${esc(name)}</option>`).join('');
    root.innerHTML = `<div class="page-heading"><div><h2>Courses</h2><p>All paths, levels, durations, pass marks and lessons are configured by Academy administrators.</p></div>${manageButton('courses', 'Add course')}</div>
      <section class="panel"><div class="filters"><label>Search<input id="courseSearch" type="search" value="${esc(state.query)}" placeholder="Search courses…"></label>
      <label>Learning path<select id="pathFilter"><option value="all">All paths</option>${paths}</select></label>
      <label>Category<select id="courseCategoryFilter"><option value="all">All categories</option>${categories}</select></label>
      <label>Level<select id="courseLevelFilter"><option value="all">All levels</option>${levels}</select></label></div></section>
      <div class="knowledge-grid">${courses.length ? courses.map(courseCard).join('') : '<section class="panel"><h2>No courses found</h2></section>'}</div>`;
  }

  function moduleBody(module) {
    if (module.type === 'video' && module.video_embed_url.startsWith('https://www.youtube-nocookie.com/embed/')) {
      return `<div class="academy-video"><iframe src="${esc(module.video_embed_url)}" title="${esc(module.title)}" loading="lazy" sandbox="allow-scripts allow-same-origin allow-presentation" allowfullscreen></iframe></div>${paragraphs(module.body)}`;
    }
    if (module.type === 'quiz') {
      return `${paragraphs(module.body)}<form id="quizForm"><fieldset class="quiz-options"><legend>${esc(module.prompt)}</legend>${module.quiz_options.map((option, index) => `<label class="learning-check"><input required type="radio" name="selected" value="${index}"> ${esc(option)}</label>`).join('')}</fieldset><button class="btn" type="submit">Submit answer</button></form>`;
    }
    const resource = module.resource_url ? `<p><a class="btn secondary small" href="${esc(module.resource_url)}" target="_blank" rel="noopener noreferrer">Open resource ↗</a></p>` : '';
    return `${paragraphs(module.body)}${module.prompt ? `<div class="notice"><strong>Your prompt</strong><p>${esc(module.prompt)}</p></div>` : ''}${resource}<form id="completeForm"><label>Response (optional)<textarea name="response"></textarea></label><button class="btn" type="submit">Mark complete</button></form>`;
  }

  async function renderCourse(course, index = 0) {
    setRouteUi('courses', course.title);
    const enrollmentList = await API.list(endpoint('enrollments'));
    state.enrollment = enrollmentList.find(item => item.course.slug === course.slug) || null;
    const module = course.modules[index];
    if (!module) {
      root.innerHTML = `<a class="btn secondary small" href="#courses">← Courses</a><section class="panel"><h2>${esc(course.title)}</h2><p>No published modules are available.</p></section>`;
      return;
    }
    const lessons = course.modules.map((item, itemIndex) => `<button class="lesson-button ${itemIndex === index ? 'selected' : ''}" data-module-index="${itemIndex}"><span>${itemIndex + 1}</span>${esc(item.title)}</button>`).join('');
    const enrolment = state.enrollment
      ? `<span class="badge" id="courseStatus">${esc(state.enrollment.status.replaceAll('_', ' '))}${state.enrollment.final_grade !== null ? ` · ${state.enrollment.final_grade}%` : ''}</span>${state.enrollment.certificate ? `<a class="btn secondary small" href="${esc(state.enrollment.certificate.print_url)}">Print certificate</a>` : ''}`
      : '<button class="btn" id="enrolButton" type="button">Start course</button>';
    root.innerHTML = `<div class="back-row"><a class="btn secondary small" href="#courses">← Courses</a>${enrolment}</div>
      <div class="page-heading"><div><h2>${esc(course.title)}</h2><p>${esc(course.description)}</p><small>${course.duration_minutes} minutes · pass mark ${course.passing_grade}% · ${esc(course.instructor_name)}</small></div></div>
      <div class="course-layout"><aside class="panel lesson-list">${lessons}</aside><section class="panel lesson-content"><h2>${esc(module.title)}</h2>${state.enrollment ? moduleBody(module) : '<p>Start the course to record progress and earn a certificate.</p>'}</section></div>`;
    root.querySelectorAll('[data-module-index]').forEach(button => button.addEventListener('click', () => renderCourse(course, Number(button.dataset.moduleIndex))));
    document.querySelector('#enrolButton')?.addEventListener('click', async () => {
      state.enrollment = await API.post(`${endpoint('courses')}${encodeURIComponent(course.slug)}/enrol/`);
      renderCourse(course, index);
    });
    document.querySelector('#completeForm')?.addEventListener('submit', async event => {
      event.preventDefault();
      try {
        state.enrollment = await API.post(`${endpoint('enrollments')}${state.enrollment.id}/complete-module/`, { module: module.id, response: event.target.response.value });
        renderCourse(course, Math.min(index + 1, course.modules.length - 1));
      } catch (error) { showError(error, 'Progress could not be saved'); }
    });
    document.querySelector('#quizForm')?.addEventListener('submit', async event => {
      event.preventDefault();
      const selected = new FormData(event.target).get('selected');
      try {
        const result = await API.post(`${endpoint('enrollments')}${state.enrollment.id}/submit-quiz/`, { module: module.id, selected_option: Number(selected) });
        state.enrollment = result.enrollment;
        if (!result.is_correct) window.alert('That answer is not correct yet. Review the lesson and try again.');
        renderCourse(course, result.is_correct ? Math.min(index + 1, course.modules.length - 1) : index);
      } catch (error) { showError(error, 'Answer could not be submitted'); }
    });
  }

  async function renderCatalogue(name, title, intro, card) {
    setRouteUi(name, title);
    root.innerHTML = '<section class="panel"><h2>Loading…</h2></section>';
    const items = await API.list(endpoint(name));
    const managedEntity = { resources: 'resources', funding: 'funding', events: 'events' }[name];
    root.innerHTML = `<div class="page-heading"><div><h2>${esc(title)}</h2><p>${esc(intro)}</p></div>${managedEntity ? manageButton(managedEntity, `Add ${name === 'events' ? 'event' : name === 'funding' ? 'opportunity' : 'resource'}`) : ''}</div>
      <section class="panel"><div class="filters"><label>Search<input type="search" data-catalogue-search placeholder="Search…"></label><label>Category<select data-catalogue-category><option value="all">All categories</option>${categoryOptions(items, 'all')}</select></label></div></section>
      <div class="knowledge-grid" data-catalogue-results>${items.length ? items.map(card).join('') : '<section class="panel"><h2>Nothing published yet</h2><p>An administrator can add content in Django admin.</p></section>'}</div>`;
    const update = () => {
      const query = root.querySelector('[data-catalogue-search]').value.toLowerCase();
      const category = root.querySelector('[data-catalogue-category]').value;
      const filtered = items.filter(item => (category === 'all' || (item.category || item.category_detail)?.slug === category) && `${item.title} ${item.description || ''}`.toLowerCase().includes(query));
      root.querySelector('[data-catalogue-results]').innerHTML = filtered.length ? filtered.map(card).join('') : '<section class="panel"><h2>No matches</h2></section>';
    };
    root.querySelector('[data-catalogue-search]').addEventListener('input', update);
    root.querySelector('[data-catalogue-category]').addEventListener('change', update);
  }

  const resourceCard = item => `<article class="panel knowledge-card"><span class="badge">${esc(categoryName(item))}</span><h2>${esc(item.title)}</h2><p>${esc(item.description)}</p>${item.download_url || item.external_url ? `<a class="btn secondary small" href="${esc(item.download_url || item.external_url)}" target="_blank" rel="noopener noreferrer">Open resource ↗</a>` : ''}</article>`;
  const fundingCard = item => `<article class="panel knowledge-card"><span class="badge">${esc(categoryName(item))}</span><h2>${esc(item.title)}</h2><p><strong>${esc(item.provider)}</strong></p><p>${esc(item.description)}</p><small>Closes: ${esc(item.closes_on || 'Not specified')}</small>${item.application_url ? `<p><a class="btn secondary small" href="${esc(item.application_url)}" target="_blank" rel="noopener noreferrer">Apply ↗</a></p>` : ''}</article>`;
  const eventCard = item => `<article class="panel knowledge-card"><span class="badge">${esc(categoryName(item))}</span><h2>${esc(item.title)}</h2><p>${esc(item.description)}</p><small>${esc(new Date(item.starts_at).toLocaleString())} · ${esc(item.venue || 'Online')}</small><p><button class="btn secondary small" data-register-event="${esc(item.slug)}" ${item.is_registered ? 'disabled' : ''}>${item.is_registered ? 'Registered' : 'Register'}</button></p></article>`;

  async function renderEvents() {
    await renderCatalogue('events', 'Events & webinars', 'Register for administrator-configured sessions.', eventCard);
  }

  async function renderDiagnostics(slug) {
    setRouteUi('diagnostics', 'Business diagnostic');
    if (!slug) {
      const items = await API.list(endpoint('diagnostics'));
      root.innerHTML = `<div class="page-heading"><div><h2>Business diagnostics</h2><p>Assess your business using questions and scoring configured by administrators.</p></div>${manageButton('diagnostics', 'Add diagnostic')}</div><div class="knowledge-grid">${items.map(item => `<article class="panel"><h2>${esc(item.title)}</h2><p>Version ${item.version} · ${item.questions.length} questions</p><a class="btn" href="#diagnostic/${encodeURIComponent(item.slug)}">Start diagnostic</a></article>`).join('') || '<section class="panel"><h2>Nothing published yet</h2></section>'}</div>`;
      return;
    }
    const diagnostic = await API.get(`${endpoint('diagnostics')}${encodeURIComponent(slug)}/`);
    root.innerHTML = `<a class="btn secondary small" href="#diagnostics">← Diagnostics</a><form id="diagnosticForm" class="panel diagnostic-panel"><h2>${esc(diagnostic.title)}</h2>${diagnostic.questions.map((question, index) => `<fieldset><legend>${index + 1}. ${esc(question.prompt)}</legend>${question.options.map(option => `<label class="learning-check"><input required type="radio" name="question-${question.id}" value="${option.id}"> ${esc(option.label)}</label>`).join('')}</fieldset>`).join('')}<button class="btn" type="submit">Calculate result</button></form>`;
    root.querySelector('#diagnosticForm').addEventListener('submit', async event => {
      event.preventDefault(); const data = new FormData(event.target); const answers = {};
      diagnostic.questions.forEach(question => { answers[String(question.id)] = Number(data.get(`question-${question.id}`)); });
      const result = await API.post(`${endpoint('diagnostics')}${encodeURIComponent(slug)}/submit/`, { answers });
      root.innerHTML = `<section class="panel diagnostic-panel"><h2>Your result: ${esc(result.total_score)}%</h2><p>Your category scores and submission have been saved.</p>${Object.entries(result.category_scores).map(([name, score]) => `<p><strong>${esc(name)}</strong>: ${esc(score)}%</p>`).join('')}${result.recommendations.map(item => `<div class="notice"><strong>Recommended course: ${esc(item.course_title)}</strong><p>${esc(item.message)}</p><a class="btn secondary small" href="#course/${encodeURIComponent(item.course_slug)}">Open course</a></div>`).join('')}<a class="btn secondary" href="#diagnostics">All diagnostics</a></section>`;
    });
  }

  async function renderMentorship() {
    setRouteUi('mentorship', 'Mentorship');
    const [mentors, bookings, conversations] = await Promise.all([API.list(endpoint('mentors')), API.list(endpoint('bookings')), API.list(endpoint('conversations'))]);
    root.innerHTML = `<div class="page-heading"><div><h2>Mentorship</h2><p>Request a mentor and keep private messages in one authenticated conversation.</p></div>${manageButton('mentors', 'Add mentor')}</div>
      <div class="knowledge-grid">${mentors.map(mentor => `<article class="panel"><h2>${esc(mentor.name)}</h2><p>${esc(mentor.expertise)}</p><p>${esc(mentor.biography)}</p><form data-mentor-form="${mentor.id}"><label>What do you need help with?<textarea name="topic" required></textarea></label><button class="btn" type="submit">Request mentorship</button></form></article>`).join('') || '<section class="panel"><h2>No mentors available yet</h2></section>'}</div>
      <div class="page-heading"><div><h2>Requests</h2></div></div>${bookings.map(booking => `<section class="panel session-row"><strong>${esc(booking.learner_name)} · ${esc(booking.mentor_detail.name)}</strong><span>${esc(booking.topic)}</span><span class="badge">${esc(booking.status)}</span>${booking.can_respond ? `<button class="btn small" data-booking-action="accept" data-booking="${booking.id}">Accept</button><button class="btn secondary small" data-booking-action="decline" data-booking="${booking.id}">Decline</button>` : ''}</section>`).join('') || '<section class="panel"><p>No mentorship requests yet.</p></section>'}
      <div class="page-heading"><div><h2>My conversations</h2></div></div>${conversations.map(conversation => `<section class="panel"><div class="completed-list">${conversation.messages.map(message => `<div><strong>${esc(message.sender_name)}</strong><span>${esc(message.body)}</span></div>`).join('') || '<p>No messages yet.</p>'}</div><form data-message-form="${conversation.id}"><label>Message<input name="body" required></label><button class="btn small" type="submit">Send</button></form></section>`).join('')}`;
    root.querySelectorAll('[data-mentor-form]').forEach(form => form.addEventListener('submit', async event => {
      event.preventDefault(); await API.post(endpoint('bookings'), { mentor: Number(form.dataset.mentorForm), topic: event.target.topic.value }); renderMentorship();
    }));
    root.querySelectorAll('[data-message-form]').forEach(form => form.addEventListener('submit', async event => {
      event.preventDefault(); await API.post(endpoint('messages'), { conversation: Number(form.dataset.messageForm), body: event.target.body.value }); renderMentorship();
    }));
    root.querySelectorAll('[data-booking-action]').forEach(button => button.addEventListener('click', async () => {
      await API.post(`${endpoint('bookings')}${button.dataset.booking}/${button.dataset.bookingAction}/`); renderMentorship();
    }));
  }

  async function renderCommunity() {
    setRouteUi('community', 'Community forum');
    const [categories, posts] = await Promise.all([API.list(endpoint('forumCategories')), API.list(endpoint('forumPosts'))]);
    root.innerHTML = `<div class="page-heading"><div><h2>Community forum</h2><p>Posts are identified by the authenticated member and organised by administrator-created categories.</p></div>${manageButton('forumCategories', 'Manage categories')}</div>
      <section class="panel"><div class="filters"><label>Filter discussions<select id="communityCategory"><option value="all">All categories</option>${categories.map(category => `<option value="${esc(category.slug)}">${esc(category.name)}</option>`).join('')}</select></label></div><form id="postForm"><label>Category<select name="category" required><option value="">Choose</option>${categories.map(category => `<option value="${category.id}">${esc(category.name)}</option>`).join('')}</select></label><label>Title<input name="title" required></label><label>Post<textarea name="body" required></textarea></label><button class="btn" type="submit">Publish post</button></form></section>
      <div class="knowledge-grid">${posts.map(post => `<article class="panel" data-forum-category="${esc(post.category_detail?.slug || '')}"><span class="badge">${esc(categoryName(post))}</span><h2>${esc(post.title)}</h2><small>By ${esc(post.author_name)}</small><p>${esc(post.body)}</p>${post.replies.map(reply => `<div class="notice"><strong>${esc(reply.author_name)}</strong><p>${esc(reply.body)}</p></div>`).join('')}<form data-reply-form="${post.id}"><label>Reply<input name="body" required ${post.is_locked ? 'disabled' : ''}></label><button class="btn small" type="submit" ${post.is_locked ? 'disabled' : ''}>Reply</button></form></article>`).join('') || '<section class="panel"><h2>No discussions yet</h2></section>'}</div>`;
    root.querySelector('#communityCategory').addEventListener('change', event => {
      root.querySelectorAll('[data-forum-category]').forEach(post => { post.hidden = event.target.value !== 'all' && post.dataset.forumCategory !== event.target.value; });
    });
    root.querySelector('#postForm').addEventListener('submit', async event => {
      event.preventDefault(); const data = new FormData(event.target); await API.post(endpoint('forumPosts'), { category: Number(data.get('category')), title: data.get('title'), body: data.get('body') }); renderCommunity();
    });
    root.querySelectorAll('[data-reply-form]').forEach(form => form.addEventListener('submit', async event => {
      event.preventDefault(); await API.post(endpoint('forumReplies'), { post: Number(form.dataset.replyForm), body: event.target.body.value }); renderCommunity();
    }));
  }

  async function route() {
    const [page, slug] = (window.location.hash.slice(1) || 'dashboard').split('/');
    try {
      if (page === 'dashboard') return renderDashboard();
      if (page === 'learning') return renderLearning();
      if (page === 'paths') return renderPaths();
      if (page === 'course' && slug) return renderCourse(await API.getCourse(endpoint('courses'), slug));
      if (page === 'resources') return renderCatalogue('resources', 'Templates & resources', 'Download files and links published by Academy administrators.', resourceCard);
      if (page === 'tools') return renderTools();
      if (page === 'funding') return renderCatalogue('funding', 'Funding opportunities', 'Review eligibility and apply using verified administrator-configured links.', fundingCard);
      if (page === 'events') return renderEvents();
      if (page === 'diagnostics' || page === 'diagnostic') return renderDiagnostics(slug);
      if (page === 'mentorship') return renderMentorship();
      if (page === 'community') return renderCommunity();
      if (page === 'growth') return renderGrowth();
      if (page === 'certificates') return renderCertificates();
      if (page === 'manage' && window.AcademyAdmin?.canManage) return window.AcademyAdmin.render();
      renderCourses();
    } catch (error) { showError(error); }
  }

  document.addEventListener('input', event => {
    if (event.target.id === 'courseSearch') { state.query = event.target.value; renderCourses(); document.querySelector('#courseSearch').focus(); }
  });
  document.addEventListener('change', event => {
    if (event.target.id === 'pathFilter') { state.selectedPath = event.target.value; renderCourses(); }
    if (event.target.id === 'courseCategoryFilter') { state.selectedCategory = event.target.value; renderCourses(); }
    if (event.target.id === 'courseLevelFilter') { state.selectedLevel = event.target.value; renderCourses(); }
  });
  root.addEventListener('click', async event => {
    const manage = event.target.closest('[data-admin-open]');
    if (manage && window.AcademyAdmin?.canManage) { window.AcademyAdmin.open(manage.dataset.adminOpen); return; }
    const button = event.target.closest('[data-register-event]');
    if (!button || button.disabled) return;
    try {
      await API.post(`${endpoint('events')}${encodeURIComponent(button.dataset.registerEvent)}/register/`);
      button.textContent = 'Registered'; button.disabled = true;
    } catch (error) { showError(error, 'Event registration could not be saved'); }
  });
  document.querySelector('#sidebarToggle').addEventListener('click', event => event.currentTarget.setAttribute('aria-expanded', String(document.body.classList.toggle('sidebar-expanded'))));
  document.querySelector('#menuButton').addEventListener('click', event => event.currentTarget.setAttribute('aria-expanded', String(sidebar.classList.toggle('open'))));
  document.querySelectorAll('[data-href]').forEach(button => button.addEventListener('click', () => window.location.assign(button.dataset.href)));
  document.querySelectorAll('[data-route]').forEach(button => button.addEventListener('click', () => { window.location.hash = button.dataset.route; sidebar.classList.remove('open'); }));
  window.addEventListener('hashchange', route);
  Promise.all([API.listPaths(endpoint('paths')), API.listCourses(endpoint('courses'))])
    .then(([paths, courses]) => { state.paths = paths; state.courses = courses; route(); })
    .catch(showError);
})(window.AcademyAPI);
