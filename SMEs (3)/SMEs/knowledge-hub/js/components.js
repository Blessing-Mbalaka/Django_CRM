(function (A) {
  const S = A.state;
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const paths = {
    dashboard: 'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z',
    explore: 'M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14M15 15l6 6',
    courses: 'M3 4h7l2 2 2-2h7v16h-7l-2 2-2-2H3zM12 6v16',
    videos: 'M4 4h16v16H4zM10 8l6 4-6 4z', guides: 'M5 3h10l4 4v14H5zM9 11h6M9 15h6',
    templates: 'M4 3h16v18H4zM4 9h16M10 9v12', funding: 'M3 8l9-5 9 5H3zM5 10v8M12 10v8M19 10v8M3 21h18',
    compliance: 'M12 3l8 3v6c0 5-8 9-8 9s-8-4-8-9V6zM8 12l3 3 5-6',
    bookmarks: 'M6 3h12v18l-6-4-6 4z', learning: 'M3 12l6 6L21 5',
    start: 'M12 3l7 8h-4v10H9V11H5z', finance: 'M3 5h18v14H3zM12 8a3 3 0 1 0 0 6 3 3 0 0 0 0-6',
    marketing: 'M3 9h5l12-5v16L8 15H3z', operations: 'M4 5h16v15H4zM8 9h8M8 13h8M8 17h4',
    people: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8M4 21v-3a8 5 0 0 1 16 0v3', technology: 'M3 4h18v13H3zM8 21h8M12 17v4'
  };
  const icon = name => `<svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="${paths[name] || paths.courses}"/></svg>`;
  const btn = (label, action, id = '', style = 'secondary small') => `<button type="button" class="btn ${style}" data-action="${action}" data-id="${esc(id)}">${label}</button>`;
  const progress = value => `<div class="learning-progress" role="progressbar" aria-label="Learning progress" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${value}"><span style="width:${value}%"></span></div>`;
  const bookmark = id => `<button class="icon-button save-button ${S.bookmarks.has(id) ? 'saved' : ''}" data-action="bookmark" data-id="${id}" aria-label="${S.bookmarks.has(id) ? 'Remove bookmark' : 'Bookmark'} ${esc(A.find(id).title)}" aria-pressed="${S.bookmarks.has(id)}">${icon('bookmarks')}</button>`;
  const empty = text => `<div class="empty"><strong>${text}</strong><p>Try another topic or search.</p></div>`;
  const panel = (title, body, action = '') => `<section class="panel"><div class="panel-header"><h2>${title}</h2>${action}</div>${body}</section>`;
  const title = (heading, subtitle) => `<div class="page-heading"><div><h2>${heading}</h2><p>${subtitle}</p></div></div>`;
  const tabs = (items, selected, action) => `<div class="report-tabs" role="group" aria-label="Choose content">${items.map(item => `<button class="btn secondary small ${item === selected ? 'active' : ''}" data-action="${action}" data-id="${esc(item)}" aria-pressed="${item === selected}">${esc(item)}</button>`).join('')}</div>`;
  function card(item) {
    const typeIcon = { Guide: 'guides', Course: 'courses', Video: 'videos', Template: 'templates' }[item.type];
    const thumbnail = item.type === 'Video' ? `<button class="video-thumb" data-action="open" data-id="${item.id}" aria-label="Preview ${esc(item.title)}"><span>▶</span><small>${item.time} min · Video preview</small></button>` : '';
    const value = item.type === 'Course' ? A.progress(item.id) : 0;
    return `<article class="panel knowledge-card">${thumbnail}<div class="card-top"><span class="badge">${esc(item.category)}</span>${bookmark(item.id)}</div><h2>${esc(item.title)}</h2><p>${esc(item.description)}</p><div class="resource-meta">${icon(typeIcon)}<span>${item.type}${item.fileType ? ' · ' + item.fileType : ''}</span><span>${item.time} min${item.type === 'Guide' ? ' read' : ''}</span><span>${item.difficulty}</span></div>${item.type === 'Course' ? `<div class="progress-label"><span>5 lessons</span><strong>${value}% complete</strong></div>${progress(value)}` : ''}<div class="card-actions">${btn(item.type === 'Course' ? value ? 'Continue' : 'Start Course' : item.type === 'Guide' ? 'Read Guide' : 'Preview', 'open', item.id)}${item.type === 'Template' ? btn('Download', 'download', item.id) : ''}</div></article>`;
  }
  const grid = items => items.length ? `<div class="knowledge-grid">${items.map(card).join('')}</div>` : empty('No matching resources');
  const options = (items, value) => items.map(item => `<option ${value === item ? 'selected' : ''} value="${esc(item)}">${esc(item)}</option>`).join('');
  const search = (dashboard = false) => `<form class="knowledge-search" data-form="search"><label for="knowledgeSearch">${dashboard ? 'What would you like to learn?' : 'Search business topics'}</label><div><input id="knowledgeSearch" name="query" type="search" value="${esc(S.query)}" placeholder="${dashboard ? 'How do I price my services?' : 'Search business topics...'}"><button class="btn" type="submit">Search</button></div></form>`;
  function matches(item) {
    const normalize = value => value.toLowerCase().replace(/pricing/g, 'price').replace(/finances/g, 'finance').replace(/[^a-z0-9 ]/g, ' ').replace(/\b(how|do|i|my|the|a|an|to|for|of)\b/g, '').split(/\s+/).filter(Boolean);
    const text = `${item.title} ${item.description} ${item.category} ${item.type} ${item.category === 'Compliance' ? 'tax register registration sars' : ''}`.toLowerCase().replace(/pricing/g, 'price');
    return normalize(S.query).every(word => text.includes(word)) && (S.category === 'All' || item.category === S.category) && (S.type === 'All' || (['Funding', 'Compliance'].includes(S.type) ? item.category === S.type : item.type === S.type.replace(/s$/, '')));
  }
  A.C = { esc, icon, btn, progress, bookmark, empty, panel, title, tabs, card, grid, options, search, matches };
})(window.Knowledge);
