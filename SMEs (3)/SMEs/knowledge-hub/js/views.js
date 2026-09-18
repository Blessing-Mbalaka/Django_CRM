(function (A) {
  const S = A.state, C = A.C;
  const { esc, btn, panel, grid, title } = C;
  const statCards = rows => `<div class="stats hub-stats">${rows.map(([label, value]) => `<article class="stat"><div class="stat-label">${label}</div><strong>${value}</strong><small>Your learning so far</small></article>`).join('')}</div>`;
  function dashboard() {
    const sum = A.summary();
    const popular = `<div class="topic-grid">${A.categories.map(c => `<button class="panel topic-card" data-action="category" data-id="${c.id}">${C.icon(c.icon)}<strong>${c.title}</strong><span>${c.description}</span></button>`).join('')}</div>`;
    const connections = [['Inventory', 'Running low on stock?', 'stock'], ['Invoicing', 'Customers paying late?', 'late-payments'], ['Marketing', 'Not getting enough leads?', 'marketing-plan'], ['CRM', 'Losing repeat customers?', 'retention'], ['Project Management', 'Tasks always overdue?', 'project-plan']];
    return `<p class="intro">Learn practical skills to start, manage and grow your business.</p>${C.search(true)}` + statCards([['Learning Progress', sum.progress + '%'], ['Saved Resources', sum.saved], ['Completed Guides', sum.guides], ['Courses in Progress', sum.active]]) + title('Continue learning', 'One practical step at a time.') + grid(A.courses.filter(c => A.progress(c.id) > 0 && A.progress(c.id) < 100).slice(0, 3)) + title('Recommended for you', 'Useful starting points for everyday business questions.') + grid(['pricing', 'late-payments', 'marketing-template', 'funding-course'].map(A.find)) + title('Popular topics', 'Find the area you want to work on.') + popular + title('Learn While You Work', 'Practical support for the rest of your business tools.') + `<div class="topic-grid">${connections.map(([app, question, id]) => `<button class="panel topic-card" data-action="open" data-id="${id}"><span class="badge">${app}</span><strong>${question}</strong><span>Learn: ${A.find(id).title} ↗</span></button>`).join('')}</div>`;
  }
  function results(page = S.page) {
    const types = { courses: 'Course', videos: 'Video', guides: 'Guide', templates: 'Template' };
    let items = A.items.filter(C.matches);
    if (types[page]) items = items.filter(i => i.type === types[page]);
    if (page === 'bookmarks') items = items.filter(i => S.bookmarks.has(i.id) && (S.savedType === 'All' || i.type === S.savedType.replace(/s$/, '')));
    if (page === 'explore' && S.query) return ['Course', 'Video', 'Guide', 'Template'].map(type => { const group = items.filter(i => i.type === type); return group.length ? title(type + 's', `${group.length} results`) + grid(group) : ''; }).join('') || C.empty('No matching resources');
    return grid(items);
  }
  function library(page) {
    const copy = { explore: ['Explore Knowledge', 'Find practical answers for your next business decision.'], courses: ['Short Business Courses', 'Practical learning you can complete at your own pace.'], videos: ['Business Videos', 'Short previews with useful ideas to try.'], guides: ['Guides & Articles', 'Clear steps for everyday business questions.'], templates: ['Templates & Resources', 'Practical tools you can use in your business.'], bookmarks: ['Saved Resources', 'Everything you have bookmarked, together.'] }[page];
    const allCategories = page === 'templates' ? ['Finance', 'Marketing', 'HR', 'Operations', 'Funding', 'Compliance', 'Business Planning'] : A.categories.map(c => c.id);
    return title(...copy) + C.search() + (page === 'explore' ? C.tabs(['All', 'Courses', 'Videos', 'Guides', 'Templates', 'Funding', 'Compliance'], S.type, 'type') : page === 'bookmarks' ? C.tabs(['All', 'Courses', 'Videos', 'Guides', 'Templates'], S.savedType, 'saved-type') : '') + `<div class="filters"><select id="categoryFilter" aria-label="Filter category">${C.options(['All', ...allCategories], S.category)}</select></div><div id="results">${results(page)}</div>` + (page === 'explore' ? glossary() : '');
  }
  function glossaryResults() {
    const rows = A.glossary.filter(([term, description]) => `${term} ${description}`.toLowerCase().includes(S.glossaryQuery.toLowerCase()));
    return rows.map(([term, description]) => `<details class="glossary-item"><summary>${term}</summary><p>${description}</p></details>`).join('') || C.empty('No matching terms');
  }
  function glossary() { return panel('Business Glossary', `<input id="glossarySearch" type="search" aria-label="Search business terms" placeholder="Search business terms..." value="${esc(S.glossaryQuery)}"><div id="glossaryResults">${glossaryResults()}</div>`); }
  function guide() {
    const item = A.find(S.itemId); if (!item || item.type !== 'Guide') return C.empty('Guide not found');
    const section = (heading, body) => `<section><h2>${heading}</h2>${body}</section>`;
    return `<div class="back-row">${btn('← Guides & Articles', 'navigate', 'guides')}${C.bookmark(item.id)}</div><article class="panel guide-article"><span class="badge">${item.category} · ${item.time} min read</span><h2 class="article-title">${esc(item.title)}</h2>${item.category === 'Compliance' || item.category === 'Funding' ? '<p class="notice">Educational introduction only, not legal, tax or financial advice. Check current requirements with the relevant authority or provider.</p>' : ''}${section('Overview', `<p>${esc(item.description)}</p>`)}${section('Why It Matters', `<p>${esc(item.why)}</p>`)}${section('Step-by-Step Guide', `<ol>${item.steps.map(step => `<li>${esc(step)}</li>`).join('')}</ol>`)}${section('Example', `<p class="notice">${esc(item.example)}</p>`)}${section('Checklist', item.checklist.map(text => `<label class="learning-check"><input type="checkbox">${esc(text)}</label>`).join(''))}${section('Key Takeaways', `<p>${esc(item.takeaway)}</p>`)}${item.source ? `<p><a href="${item.source[1]}" target="_blank" rel="noopener noreferrer">${item.source[0]} ↗</a></p>` : ''}${btn(S.completedGuides.has(item.id) ? 'Guide completed ✓' : 'Mark guide complete', 'complete-guide', item.id, '')}</article>`;
  }
  function quiz(course) {
    const q = S.quiz[course.id] || { index: 0, answers: [], feedback: null };
    if (q.index === A.quizzes.length) return `<h3>Your score: ${q.answers.filter(Boolean).length}/${A.quizzes.length}</h3><p>You have reached the end of this practice quiz.</p>${btn('Complete Lesson', 'complete-lesson', course.id, '')}${btn('Try quiz again', 'restart-quiz', course.id)}`;
    const item = A.quizzes[q.index];
    const feedback = q.feedback === null ? '' : `<div class="notice" role="status"><strong>${q.feedback ? 'Correct' : 'Try Again'}</strong><p>${item.explanation}</p></div>`;
    return `<form data-form="quiz"><fieldset class="quiz-options"><legend>Question ${q.index + 1} of 5: ${item.question}</legend>${item.options.map((text, i) => `<label><input type="radio" name="answer" value="${i}" required>${text}</label>`).join('')}</fieldset><button class="btn" type="submit" ${q.feedback !== null ? 'disabled' : ''}>Submit</button></form>${feedback}${q.feedback === false ? btn('Try Again', 'quiz-retry', course.id) : ''}${q.feedback !== null ? btn(q.index === 4 ? 'See Score' : 'Next Question', 'quiz-next', course.id) : ''}`;
  }
  function course() {
    const item = A.find(S.itemId); if (!item || item.type !== 'Course') return C.empty('Course not found');
    const article = A.find(item.guide), lesson = S.lesson;
    const bodies = [`<p>${esc(item.description)}</p><p>Choose one thing you would like to improve in your business as you work through this course.</p>`, `<h3>Keep it practical</h3><ul>${article.steps.map(step => `<li>${esc(step)}</li>`).join('')}</ul>`, `<h3>A local business example</h3><p class="notice">${esc(article.example)}</p>`, article.checklist.map(text => `<label class="learning-check"><input type="checkbox">${esc(text)}</label>`).join(''), quiz(item)];
    const lessons = item.lessons.map((name, i) => `<button class="lesson-button ${i === lesson ? 'selected' : ''}" data-action="lesson" data-id="${i}" ${i === lesson ? 'aria-current="step"' : ''}><span>${S.completed[item.id]?.includes(i) ? '✓' : i + 1}</span>${name}</button>`).join('');
    const controls = lesson < 4 ? `<div class="form-actions"><button class="btn secondary" data-action="lesson" data-id="${lesson - 1}" ${lesson === 0 ? 'disabled' : ''}>Previous</button>${btn(S.completed[item.id]?.includes(lesson) ? 'Completed ✓' : 'Mark Complete', 'complete-lesson', item.id, '')}${btn('Next', 'lesson', String(lesson + 1))}</div>` : '';
    return `<div class="back-row">${btn('← Courses', 'navigate', 'courses')}${C.bookmark(item.id)}</div>${title(esc(item.title), `${item.time} minutes · ${item.category}`)}<p>${esc(item.description)}</p><div class="progress-label"><strong>${A.progress(item.id)}% complete</strong></div>${C.progress(A.progress(item.id))}<div class="course-layout"><aside class="panel lesson-list">${lessons}</aside><section class="panel lesson-content"><h2>${item.lessons[lesson]}</h2>${item.category === 'Compliance' ? '<p class="notice">Educational overview only. Check current official information for your circumstances.</p>' : ''}${bodies[lesson]}${article.source && lesson !== 4 ? `<a href="${article.source[1]}" target="_blank" rel="noopener noreferrer">${article.source[0]} ↗</a>` : ''}${controls}</section></div>`;
  }
  function funding() {
    const topics = ['Types of Funding', 'Funding Readiness', 'Business Plans', 'Pitch Decks', 'Financial Documents', 'Grants', 'Loans', 'Investors', 'Incubators'];
    const readiness = ['Business Registration', 'Business Plan', 'Financial Records', 'Bank Statements', 'Pitch Deck', 'Proof of Sales', 'Tax Documentation'];
    return title('Funding & Growth', 'Understand your options and prepare useful questions. This is not a funding application.') + panel('Explore funding topics', `<div class="topic-links">${topics.map((t, i) => btn(t, 'open', ['funding-prepare', 'funding-course', 'business-plan', 'pitch-course', 'cash-template', 'grants', 'loans', 'investors-video', 'funding-prepare'][i])).join('')}</div>`) + panel('Funding readiness', '<p class="muted">Practice checklist only. These statuses do not establish eligibility for funding.</p>' + readiness.map((name, i) => `<label class="readiness-row"><span>${name}</span><select data-readiness="${i}" aria-label="${name} status">${C.options(['Complete', 'Missing', 'In Progress'], S.readiness[i])}</select></label>`).join('')) + grid(A.items.filter(i => i.category === 'Funding'));
  }
  function compliance() {
    const topics = ['CIPC', 'SARS', 'VAT', 'PAYE', 'B-BBEE', 'POPIA', 'COID', 'Business Licences', 'Record Keeping'];
    return title('Business Compliance', 'Understand important requirements for running your business.') + '<p class="notice">Learn about common business compliance requirements. This sample content is educational, not legal or tax advice. It does not determine which obligations apply to you.</p>' + `<div class="topic-links">${topics.map((t, i) => btn(t, 'open', ['cipc', 'tax', 'vat', 'paye', 'bbbee', 'popia', 'coid', 'licences', 'records'][i])).join('')}</div>` + grid(A.items.filter(i => i.category === 'Compliance'));
  }
  function learning() {
    const sum = A.summary();
    const activity = S.activity.map(a => `<li>${esc(a.text)}</li>`).join('');
    const certificates = Object.keys(S.certificates).map(id => `<article class="panel"><span class="badge">Sample certificate</span><h2>Certificate of Completion</h2><p>${esc(A.find(id).title)}</p><small>Completed ${S.certificates[id]}</small><div class="card-actions">${btn('View Certificate', 'certificate', id)}</div></article>`).join('');
    return title('My Learning', 'Small steps add up to useful business skills.') + statCards([['Courses in Progress', sum.active], ['Completed Courses', sum.finished], ['Completed Guides', sum.guides], ['Saved Resources', sum.saved]]) + C.tabs(['Overview', 'Quiz Results', 'Certificates'], S.learningTab, 'learning-tab') + (S.learningTab === 'Certificates' ? `<div class="knowledge-grid">${certificates || C.empty('Complete a course to see a sample certificate')}</div>` : S.learningTab === 'Quiz Results' ? panel('Quiz Results', Object.entries(S.scores).map(([id, score]) => `<div class="readiness-row"><span>${esc(A.find(id).title)}</span><strong>${score}/5</strong></div>`).join('') || C.empty('No quiz results yet')) : grid(A.courses.filter(c => A.progress(c.id) > 0)) + panel('Recent Activity', `<ul class="activity-list">${activity}</ul>`));
  }
  A.V = { dashboard, library, results, glossaryResults, guide, course, funding, compliance, learning };
})(window.Knowledge);
