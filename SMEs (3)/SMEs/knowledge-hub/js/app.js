(function (A) {
  const S = A.state, C = A.C, V = A.V, $ = selector => document.querySelector(selector);
  const pages = { dashboard: 'Dashboard', explore: 'Explore Knowledge', courses: 'Courses', videos: 'Videos', guides: 'Guides & Articles', templates: 'Templates & Resources', funding: 'Funding', compliance: 'Compliance', bookmarks: 'Bookmarks', learning: 'My Learning' };
  let trigger;
  function toast(text) { const e = document.createElement('div'); e.className = 'toast'; e.textContent = text; $('#toasts').append(e); setTimeout(() => e.remove(), 3500); }
  function activity(text) { S.activity.unshift({ text }); }
  function closeSidebar() { $('#sidebar').classList.remove('open'); $('#menuButton').setAttribute('aria-expanded', 'false'); }
  function render() {
    $('#pageTitle').textContent = S.page === 'dashboard' ? 'Business Knowledge Hub' : pages[S.page] || (S.page === 'course' ? 'Course Details' : 'Guide');
    document.title = $('#pageTitle').textContent + ' · EIEAAS';
    $('#navigation').innerHTML = Object.entries(pages).map(([id, name]) => `<button data-action="navigate" data-id="${id}" aria-label="${name}" title="${name}" ${S.page === id ? 'class="active" aria-current="page"' : ''}>${C.icon(id)}<span>${name}</span></button>`).join('');
    $('#content').innerHTML = ['explore', 'courses', 'videos', 'guides', 'templates', 'bookmarks'].includes(S.page) ? V.library(S.page) : V[S.page]();
  }
  function navigate() {
    const [page, id] = location.hash.slice(1).split('/');
    S.page = pages[page] || ['course', 'guide'].includes(page) ? page : 'dashboard'; S.itemId = id || '';
    if (S.page === 'course') S.lesson = Array.from({ length: 5 }, (_, i) => i).find(i => !(S.completed[id] || []).includes(i)) ?? 0;
    closeSidebar(); render(); $('#content').focus({ preventScroll: true });
  }
  function modal(title, html) { trigger = document.activeElement; $('#modalTitle').textContent = title; $('#modalBody').innerHTML = html; $('#modal').showModal(); }
  function close() { $('#modal').close(); $('#modalBody').innerHTML = ''; if (trigger?.isConnected) trigger.focus(); }
  function open(id) {
    const item = A.find(id); if (!item) return;
    if (item.type === 'Course' || item.type === 'Guide') { location.hash = `${item.type.toLowerCase()}/${id}`; return; }
    if (item.type === 'Video') modal(item.title, `<div class="video-placeholder"><span>▶</span><strong>${C.esc(item.title)}</strong><small>Video preview · No streaming in this demo</small></div><h3>What this video covers</h3><p>${C.esc(item.transcript)}</p>${C.btn(S.watched.has(id) ? 'Preview watched ✓' : 'Mark preview watched', 'watched', id)}`);
    else modal(item.title, `<p>${C.esc(item.description)}</p><span class="badge">${item.fileType} · Sample layout</span><div class="resource-sheet">${item.columns.map(label => `<div><strong>${C.esc(label)}</strong><span>Write your business information here</span></div>`).join('')}</div>${C.btn('Download (demo)', 'download', id)}<p class="muted">Preview only. No file is stored or downloaded.</p>`);
  }
  document.addEventListener('click', event => {
    const t = event.target.closest('[data-action]');
    if (t) {
      const { action, id } = t.dataset;
      if (action === 'navigate') { S.query = ''; S.type = 'All'; S.category = 'All'; location.hash = id; if (S.page === id) render(); }
      if (action === 'open') open(id);
      if (action === 'close') close();
      if (action === 'bookmark') { S.bookmarks.has(id) ? S.bookmarks.delete(id) : S.bookmarks.add(id); render(); toast(S.bookmarks.has(id) ? 'Resource saved' : 'Bookmark removed'); }
      if (action === 'category') { S.query = ''; S.type = 'All'; S.category = id; location.hash = 'explore'; }
      if (action === 'type') { S.type = id; render(); }
      if (action === 'saved-type') { S.savedType = id; render(); }
      if (action === 'learning-tab') { S.learningTab = id; render(); }
      if (action === 'lesson') { S.lesson = Math.max(0, Math.min(4, Number(id))); render(); }
      if (action === 'complete-guide') { if (!S.completedGuides.has(id)) activity('Completed: ' + A.find(id).title); S.completedGuides.add(id); render(); toast('Guide completed'); }
      if (action === 'download') { activity('Download preview: ' + A.find(id).title); toast('Download preview only — no file was downloaded.'); }
      if (action === 'watched') { S.watched.add(id); activity('Watched preview: ' + A.find(id).title); close(); toast('Preview marked as watched'); }
      if (action === 'restart-quiz') { S.quiz[id] = { index: 0, answers: [], feedback: null }; render(); }
      if (action === 'quiz-retry') { const q = S.quiz[id]; if (q) { q.feedback = null; render(); } }
      if (action === 'quiz-next') { const q = S.quiz[id]; if (q?.feedback !== null && q) { q.index++; q.feedback = null; if (q.index === 5) S.scores[id] = q.answers.filter(Boolean).length; render(); } }
      if (action === 'complete-lesson') {
        if (S.lesson === 4 && S.quiz[id]?.index !== 5 && !S.completed[id]?.includes(4)) { toast('Finish the quiz first.'); return; }
        const completed = new Set(S.completed[id] || []); const before = completed.size; completed.add(S.lesson); S.completed[id] = [...completed];
        if (completed.size !== before) activity(`Completed lesson: ${A.find(id).lessons[S.lesson]} · ${A.find(id).title}`);
        if (completed.size === 5) S.certificates[id] = new Date().toISOString().slice(0, 10);
        render(); toast('Lesson completed');
      }
      if (action === 'certificate') modal('Sample Certificate', `<div class="certificate"><span>EIEAAS · Business Knowledge Hub</span><h2>Certificate of Completion</h2><p>Sample learner</p><h3>${C.esc(A.find(id).title)}</h3><p>Completed ${S.certificates[id]}</p><small>Front-end preview only · Not an accredited qualification</small></div>`);
    }
    if (!event.target.closest('#sidebar') && !event.target.closest('#menuButton')) closeSidebar();
  });
  document.addEventListener('submit', event => {
    const form = event.target.closest('form'); if (!form) return; event.preventDefault();
    if (form.dataset.form === 'search') { S.query = new FormData(form).get('query').trim(); S.type = 'All'; S.category = 'All'; if (S.page === 'explore') render(); else location.hash = 'explore'; }
    if (form.dataset.form === 'quiz' && form.reportValidity()) {
      const q = S.quiz[S.itemId] || (S.quiz[S.itemId] = { index: 0, answers: [], feedback: null });
      if (q.feedback !== null || q.index >= 5) return;
      q.feedback = Number(new FormData(form).get('answer')) === A.quizzes[q.index].answer; if (typeof q.answers[q.index] !== 'boolean') q.answers[q.index] = q.feedback; render();
    }
  });
  document.addEventListener('input', event => { if (event.target.id === 'glossarySearch') { S.glossaryQuery = event.target.value; $('#glossaryResults').innerHTML = V.glossaryResults(); } });
  document.addEventListener('change', event => { if (event.target.id === 'categoryFilter') { S.category = event.target.value; $('#results').innerHTML = V.results(); } if (event.target.dataset.readiness) S.readiness[Number(event.target.dataset.readiness)] = event.target.value; });
  $('#sidebarToggle').onclick = () => { const expanded = document.body.classList.toggle('sidebar-expanded'); $('#sidebarToggle').setAttribute('aria-expanded', String(expanded)); $('#sidebarToggle').setAttribute('aria-label', expanded ? 'Collapse sidebar' : 'Expand sidebar'); };
  $('#menuButton').onclick = () => { const open = $('#sidebar').classList.toggle('open'); $('#menuButton').setAttribute('aria-expanded', String(open)); };
  $('#modal').addEventListener('cancel', event => { event.preventDefault(); close(); });
  document.addEventListener('keydown', event => { if (event.key === 'Escape') closeSidebar(); });
  window.addEventListener('hashchange', navigate); navigate();
})(window.Knowledge);
