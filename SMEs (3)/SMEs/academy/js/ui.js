/* Small presentation helpers; shared layout and controls come from Inventory. */
(function (A) {
  const S = A.state;
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const paths = {
    dashboard: 'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z',
    learning: 'M3 12l6 6L21 5', paths: 'M5 3v18M5 5h10l-2 3 2 3H5M5 15h15',
    courses: 'M3 4h7l2 2 2-2h7v16h-7l-2 2-2-2H3zM12 6v16',
    diagnostic: 'M4 3h16v18H4zM8 8h8M8 12h8M8 16h4', resources: 'M4 3h16v18H4zM4 9h16M10 9v12',
    tools: 'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z',
    mentorship: 'M8 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6M2 21v-4a6 4 0 0 1 12 0v4M17 6h5v8h-3l-2 3z',
    community: 'M3 4h18v13H9l-5 4v-4H3zM7 8h10M7 12h7',
    funding: 'M3 8l9-5 9 5H3zM5 10v8M12 10v8M19 10v8M3 21h18',
    events: 'M4 5h16v16H4zM4 10h16M8 3v4M16 3v4', growth: 'M4 3v18h17M8 16v-5M13 16V6M18 16V9',
    certificates: 'M12 3a6 6 0 1 0 0 12 6 6 0 0 0 0-12M8 14l-2 7 6-3 6 3-2-7',
    profile: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8M4 21v-3a8 5 0 0 1 16 0v3',
    settings: 'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M5 19l2-2M17 7l2-2'
  };
  const icon = name => `<svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="${paths[name] || paths.courses}"/></svg>`;
  const btn = (label, action, id = '', style = 'secondary small') => `<button type="button" class="btn ${style}" data-action="${action}" data-id="${esc(id)}">${label}</button>`;
  const panel = (title, body, action = '') => `<section class="panel"><div class="panel-header"><h2>${title}</h2>${action}</div>${body}</section>`;
  const title = (text, subtitle) => `<div class="page-heading"><div><h2>${text}</h2><p>${subtitle}</p></div></div>`;
  const progress = value => `<div class="learning-progress" role="progressbar" aria-label="Progress" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${value}"><span style="width:${value}%"></span></div>`;
  const empty = text => `<div class="empty"><strong>${text}</strong><p>Try another filter or explore a learning path.</p></div>`;
  const stats = rows => `<div class="stats academy-stats">${rows.map(([label, value, glyph]) => `<article class="stat"><div class="stat-label"><span>${label}</span>${glyph ? icon(glyph) : ''}</div><strong>${value}</strong><small>Sample workspace</small></article>`).join('')}</div>`;
  const options = (items, value) => items.map(item => `<option value="${esc(item)}" ${item === value ? 'selected' : ''}>${esc(item)}</option>`).join('');
  const field = (name, label, value = '', type = 'text', extra = '') => `<label class="field">${label}<input name="${name}" type="${type}" value="${esc(value)}" ${extra}></label>`;
  const area = (name, label, value = '') => `<label class="field full">${label}<textarea name="${name}" maxlength="4000">${esc(value)}</textarea></label>`;
  const form = (kind, body, label = 'Save', id = '') => `<form data-form="${kind}" data-id="${esc(id)}"><div class="error" id="formError" role="alert"></div><div class="form-grid">${body}</div><div class="form-actions"><button class="btn" type="submit">${label}</button></div></form>`;
  const date = value => new Date(`${value}T12:00:00`).toLocaleDateString('en-ZA', { day: 'numeric', month: 'short', year: 'numeric' });
  function courseCard(course) {
    const value = A.progress(course.id);
    return `<article class="panel academy-course"><div class="course-art art-${course.path}">${icon('courses')}<span>${esc(course.stage)}</span></div><div class="course-card-body"><span class="badge">${esc(course.category)}</span><h2>${esc(course.title)}</h2><p>${esc(course.description)}</p><div class="resource-meta"><span>${course.duration} min</span><span>${course.level}</span></div><div class="progress-label"><span>9 modules</span><strong>${value}%</strong></div>${progress(value)}<div class="card-actions">${btn(value ? value === 100 ? 'Review Course' : 'Continue' : 'Start Course', 'course', course.id)}</div></div></article>`;
  }
  const grid = items => items.length ? `<div class="knowledge-grid">${items.map(courseCard).join('')}</div>` : empty('No matching courses');
  function matches(course) {
    const f = S.filters, value = A.progress(course.id);
    const status = value === 100 ? 'Completed' : value > 0 ? 'In Progress' : 'Not Started';
    return `${course.title} ${course.description} ${course.category}`.toLowerCase().includes(S.query.toLowerCase()) && (f.path === 'All' || course.path === f.path) && (f.level === 'All' || course.level === f.level) && (f.stage === 'All' || course.stage === f.stage) && (f.status === 'All' || status === f.status) && (f.duration === 'All' || (f.duration === 'Up to 60 min' ? course.duration <= 60 : course.duration > 60));
  }
  function journey() {
    const stages = ['Foundations', 'Validate', 'Build', 'Grow', 'Scale', 'Investment Ready'];
    const active = Math.max(0, stages.indexOf(S.profile.stage));
    return `<ol class="journey">${stages.map((stage, i) => `<li class="${i < active ? 'done' : i === active ? 'current' : 'upcoming'}" ${i === active ? 'aria-current="step"' : ''}><b>${i < active ? '✓' : i + 1}</b><strong>${stage}</strong><small>${i < active ? 'Completed' : i === active ? 'Current focus' : 'Upcoming'}</small></li>`).join('')}</ol>`;
  }
  A.U = { esc, icon, btn, panel, title, progress, empty, stats, options, field, area, form, date, courseCard, grid, matches, journey };
})(window.Academy);
