/* All mutations are local to this preview session. No data is sent or persisted. */
(function (A) {
  const S = A.state, U = A.U, V = A.V, $ = selector => document.querySelector(selector);
  const pages = { dashboard: 'Dashboard', learning: 'My Learning', paths: 'Learning Paths', courses: 'Courses', diagnostic: 'Business Diagnostic', resources: 'Templates & Resources', tools: 'Business Tools', mentorship: 'Mentorship', community: 'SME Community', funding: 'Funding & Opportunities', events: 'Events & Webinars', growth: 'My Business Growth', certificates: 'Certificates', profile: 'My Profile', settings: 'Settings' };
  let trigger, nextId = 1;
  function toast(message) { const e = document.createElement('div'); e.className = 'toast'; e.textContent = message; $('#toasts').append(e); setTimeout(() => e.remove(), 4000); }
  function closeSidebar() { $('#sidebar').classList.remove('open'); $('#menuButton').setAttribute('aria-expanded', 'false'); }
  function render() {
    document.body.classList.toggle('academy-dashboard', S.page === 'dashboard');
    $('#pageTitle').textContent = S.page === 'dashboard' ? 'SME Academy' : pages[S.page] || 'Course Details'; document.title = $('#pageTitle').textContent + ' · EIEAAS';
    $('#navigation').innerHTML = Object.entries(pages).map(([id, label]) => `<button data-action="navigate" data-id="${id}" aria-label="${label}" title="${label}" ${S.page === id || S.page === 'course' && id === 'courses' ? 'class="active" aria-current="page"' : ''}>${U.icon(id)}<span>${label}</span></button>`).join('');
    $('#content').innerHTML = V[S.page]();
    document.body.classList.toggle('compact-cards', S.settings.compact);
  }
  function navigate() {
    const [page, id] = location.hash.slice(1).split('/');
    S.page = pages[page] || page === 'course' ? page : 'dashboard';
    if (page === 'course') { S.courseId = id; const done = S.completed[id] || []; S.module = Array.from({ length: 9 }, (_, i) => i).find(i => !done.includes(i)) ?? 0; }
    closeSidebar(); render(); $('#content').focus({ preventScroll: true });
  }
  function modal(title, html) { trigger = document.activeElement; $('#modalTitle').textContent = title; $('#modalBody').innerHTML = html; $('#modal').showModal(); }
  function close() { $('#modal').close(); $('#modalBody').innerHTML = ''; if (trigger?.isConnected) trigger.focus(); }
  function certificate(id) {
    const c = A.courses.find(c => c.id === id);
    modal('Sample Certificate', `<div class="certificate"><span>EIEAAS · SME Academy</span><h2>Certificate of Completion</h2><p>Presented to ${U.esc(S.profile.name)}</p><h3>${U.esc(c.title)}</h3><p>Completed ${U.date(S.certificates[id])}</p><small>Front-end sample · Not an accredited qualification</small></div>`);
  }
  document.addEventListener('click', event => {
    const t = event.target.closest('[data-action]');
    if (t) {
      const { action, id } = t.dataset;
      if (action === 'navigate') location.hash = id;
      if (action === 'course') location.hash = `course/${id}`;
      if (action === 'close') close();
      if (action === 'path') { S.query = ''; S.filters = { path: id, level: 'All', duration: 'All', stage: 'All', status: 'All' }; location.hash = 'courses'; }
      if (action === 'module') { S.module = Math.max(0, Math.min(8, Number(id))); render(); }
      if (action === 'complete') {
        if (S.module === 5 && !S.quiz[id]?.correct && !S.completed[id]?.includes(5)) { toast('Answer the practice question correctly first.'); return; }
        if (S.module === 6 && !S.outputs[id]?.result?.trim() && !S.completed[id]?.includes(6)) { toast('Save your practical business task first.'); return; }
        const before = S.completed[id] || [], done = new Set(before); done.add(S.module); S.completed[id] = [...done];
        if (done.size > before.length) S.activity.unshift('Completed module: ' + A.courses.find(c => c.id === id).modules[S.module]);
        if (done.size === 9) S.certificates[id] = S.certificates[id] || A.day(0);
        render(); toast('Module completed');
      }
      if (action === 'diagnostic-back') { const checked = document.querySelector('input[name="answer"]:checked'); if (checked) S.diagnosticAnswers[S.diagnosticStep] = checked.value; S.diagnosticStep = Math.max(0, S.diagnosticStep - 1); render(); }
      if (action === 'diagnostic-review') { S.diagnosticFinished = false; S.diagnosticStep = 0; render(); }
      if (action === 'resource') {
        const r = A.resources.find(r => r.id === id);
        modal(r.name, `<span class="badge">${r.type} · Sample worksheet</span><div class="resource-sheet">${r.fields.map(field => `<div><strong>${field}</strong><span>Add your own business information</span></div>`).join('')}</div>${U.btn('Download (demo)', 'download', id)}<p class="muted">Preview only. No real file is generated.</p>`);
      }
      if (action === 'download' || action === 'certificate-download') toast('Download preview only — no file was generated.');
      if (action === 'certificate-share') toast('Share preview only — nothing was posted or sent.');
      if (action === 'certificate') certificate(id);
      if (action === 'crm-preview') modal('CRM tool preview', '<p>Your CRM module can be linked here when its entry point is available.</p><p>No CRM connection has been created in this front-end preview.</p>');
      if (action === 'book') {
        const m = A.mentors.find(m => m.id === id);
        modal('Book a sample session', `<p>${m.name} · ${m.expertise}</p>` + U.form('booking', U.field('date', 'Date', A.day(4), 'date', `required min="${A.day(1)}"`) + `<label class="field">Time (SAST)<select name="time">${U.options(['09:00', '10:00', '11:00', '14:00'], '10:00')}</select></label>` + U.area('topic', 'What would you like to discuss?') + '<p class="muted full">Demo booking only. No mentor is contacted.</p>', 'Book Session (demo)', id));
      }
      if (action === 'register') {
        if (S.registrations.has(id)) { toast('Already registered in this preview.'); return; }
        const e = A.events.find(e => e.id === id);
        modal('Event registration preview', `<h3>${e.title}</h3><p>${U.date(e.date)} · ${e.time} SAST · ${e.mode}</p>` + U.form('registration', U.field('name', 'Name', S.profile.name, 'text', 'required') + U.field('email', 'Email', S.profile.email, 'email', 'required') + '<p class="muted full">No registration is submitted to an organiser.</p>', 'Register (demo)', id));
      }
      if (action === 'opportunity') {
        const o = A.opportunities.find(o => o.id === id);
        modal(o.title, `<span class="badge">${o.type}</span><p>${o.provider}</p><p>Deadline: ${U.date(o.deadline)}</p><h3>Eligibility summary</h3><p>${o.eligibility}</p><p class="notice">Illustrative opportunity only. This is not an actual offer, verified eligibility assessment or funding application.</p>${U.btn('Explore Funding Readiness', 'course', 'funding-2')}`);
      }
      if (action === 'community-form') modal(id === 'Question' ? 'Ask a Question' : 'Share a Resource', U.form('post', U.field('title', 'Title', '', 'text', 'required maxlength="180"') + U.area('body', id === 'Question' ? 'Your question' : 'Describe the resource') + `<label class="field">Topic<select name="topic">${U.options(['Operations', 'Customer growth', 'Business resources'], 'Operations')}</select></label><input type="hidden" name="kind" value="${id}"><p class="muted full">Saved locally in this preview, not published to anyone.</p>`, 'Add to Preview'));
      if (action === 'help') modal('Help & Support', '<details open><summary>How do I start?</summary><p>Choose a learning path or take the Business Diagnostic, then open a course.</p></details><details><summary>Are changes saved?</summary><p>This front-end prototype keeps edits only until the page is refreshed.</p></details><details><summary>Are bookings and certificates real?</summary><p>No. They are demonstration screens. No booking, message, registration or certificate is sent.</p></details>');
    }
    if (!event.target.closest('#sidebar') && !event.target.closest('#menuButton')) closeSidebar();
  });
  document.addEventListener('input', event => { if (event.target.id === 'courseSearch') { S.query = event.target.value; $('#courseResults').innerHTML = V.courseResults(); } });
  document.addEventListener('change', event => {
    const t = event.target;
    if (t.dataset.filter) { S.filters[t.dataset.filter] = t.value; $('#courseResults').innerHTML = V.courseResults(); }
    if (t.id === 'resourceCategory') { S.resourceCategory = t.value; render(); }
    if (t.id === 'communityTopic') { S.communityTopic = t.value; render(); }
  });
  document.addEventListener('submit', event => {
    const form = event.target.closest('form[data-form]'); if (!form) return; event.preventDefault(); if (!form.reportValidity()) return;
    const data = new FormData(form), values = Object.fromEntries(data), kind = form.dataset.form, id = form.dataset.id;
    const error = text => { const box = form.querySelector('#formError'); if (box) box.textContent = text; else toast(text); };
    if (kind === 'diagnostic') { S.diagnosticAnswers[S.diagnosticStep] = values.answer; if (S.diagnosticStep === 12) S.diagnosticFinished = true; else S.diagnosticStep++; render(); return; }
    if (kind === 'quiz') { S.quiz[id] = { correct: values.answer === '0' }; render(); return; }
    if (kind === 'activity' || kind === 'output') {
      if (kind === 'output' && !values.result.trim()) { error('Describe your practical output before saving.'); return; }
      S.outputs[id] = { ...S.outputs[id], ...values, attachment: data.get('attachment')?.name || S.outputs[id]?.attachment || '' }; render(); toast('Saved for this preview.'); return;
    }
    if (kind === 'reflection') { S.reflections[id] = values.reflection; render(); toast('Reflection saved privately in this preview.'); return; }
    if (kind === 'booking') {
      if (values.date <= A.day(0)) { error('Choose a future date.'); return; }
      if (S.sessions.some(s => s.mentor === id && s.date === values.date && s.time === values.time)) { error('This sample session is already booked.'); return; }
      S.sessions.push({ mentor: id, ...values }); close(); render(); toast('Demo session added. No mentor was contacted.'); return;
    }
    if (kind === 'registration') { S.registrations.add(id); close(); render(); toast('Registered in this preview only.'); return; }
    if (kind === 'post') {
      if (!values.title.trim() || !values.body.trim()) { error('Enter a title and message.'); return; }
      S.posts.unshift({ ...values, id: `new-post-${nextId++}`, author: S.profile.name, replies: [] }); close(); render(); toast('Added locally. Nothing was published.'); return;
    }
    if (kind === 'reply') { if (!values.reply.trim()) { error('Write a reply first.'); return; } S.posts.find(p => p.id === id).replies.push(`${S.profile.name}: ${values.reply}`); render(); toast('Reply added to this preview.'); return; }
    if (kind === 'profile') { if (!values.name.trim() || !values.business.trim()) { error('Enter your name and business name.'); return; } Object.assign(S.profile, values); render(); toast('Profile updated for this preview.'); return; }
    if (kind === 'settings') { S.settings = { reminders: data.has('reminders'), digest: data.has('digest'), compact: data.has('compact') }; render(); toast('Preferences saved for this preview.'); }
  });
  $('#sidebarToggle').onclick = () => { const expanded = document.body.classList.toggle('sidebar-expanded'); $('#sidebarToggle').setAttribute('aria-expanded', String(expanded)); $('#sidebarToggle').setAttribute('aria-label', expanded ? 'Collapse sidebar' : 'Expand sidebar'); $('#sidebarToggle').title = expanded ? 'Collapse sidebar' : 'Expand sidebar'; };
  $('#menuButton').onclick = () => { const open = $('#sidebar').classList.toggle('open'); $('#menuButton').setAttribute('aria-expanded', String(open)); };
  $('#modal').addEventListener('cancel', event => { event.preventDefault(); close(); });
  document.addEventListener('keydown', event => { if (event.key === 'Escape') closeSidebar(); });
  window.addEventListener('hashchange', () => { if ($('#modal').open) close(); navigate(); }); navigate();
})(window.Academy);
