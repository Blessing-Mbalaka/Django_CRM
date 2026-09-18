/* In-memory interactions. No external service is contacted. */
(function (A) {
  'use strict';
  const S = A.state, C = A.C, V = A.V, F = A.F;
  const $ = selector => document.querySelector(selector);
  const pages = { dashboard: 'Marketing & Advertising', campaigns: 'Campaigns', advertising: 'Advertising', content: 'Posters & Content', email: 'Email Marketing', calendar: 'Marketing Calendar', leads: 'Marketing Leads', analytics: 'Analytics', brand: 'Brand Kit' };
  const actions = { dashboard: ['Create Campaign', 'campaign'], campaigns: ['New Campaign', 'campaign'], advertising: ['Create Advert', 'advert'], opportunities: ['Create Advert', 'advert'], content: ['Create Poster', 'poster'], email: ['Create Email', 'email'], calendar: ['Add Marketing Activity', 'activity'], brand: ['Edit Brand Kit', 'brand'] };
  const collections = { campaign: 'campaigns', advert: 'ads', opportunity: 'opportunities', poster: 'content', social: 'content', content: 'content', email: 'emails', activity: 'activities' };
  let counter = 1;
  let modalTrigger;
  let formInitial = {};
  function toast(message) {
    const item = document.createElement('div'); item.className = 'toast'; item.textContent = message;
    $('#toasts').append(item); setTimeout(() => item.remove(), 4500);
  }
  function closeSidebar() { $('#sidebar').classList.remove('open'); $('#menuButton').setAttribute('aria-expanded', 'false'); }
  function render() {
    const title = pages[S.page] || 'Advertising Opportunities';
    $('#pageTitle').textContent = title; document.title = `${title} · EIEAAS`;
    $('#navigation').innerHTML = Object.entries(pages).map(([id, label]) => {
      const text = id === 'dashboard' ? 'Dashboard' : id === 'leads' ? 'Leads' : label;
      const active = S.page === id || S.page === 'opportunities' && id === 'advertising';
      return `<button data-action="navigate" data-id="${id}" aria-label="${text}" title="${text}" ${active ? 'class="active" aria-current="page"' : ''}>${C.icon(id)}<span>${text}</span></button>`;
    }).join('');
    const primary = $('#primaryAction'), action = actions[S.page];
    primary.hidden = !action;
    if (action) { primary.textContent = (action[1] === 'brand' ? '' : '＋ ') + action[0]; primary.dataset.kind = action[1]; }
    $('#content').innerHTML = V[S.page]();
  }
  function navigate() {
    const route = location.hash.slice(1) || 'dashboard';
    S.page = pages[route] || route === 'opportunities' ? route : 'dashboard';
    closeSidebar(); render(); $('#content').focus({ preventScroll: true });
  }
  function modal(title, html) {
    if (!$('#modal').open) modalTrigger = document.activeElement;
    $('#modalTitle').textContent = title; $('#modalBody').innerHTML = html;
    if (!$('#modal').open) $('#modal').showModal();
  }
  function close() {
    $('#modal').close(); $('#modalBody').innerHTML = '';
    if (modalTrigger?.isConnected) modalTrigger.focus();
  }
  function create(kind, initial = {}) {
    if (kind === 'brand') initial = { ...S.brand };
    if (kind === 'email' && !initial.id) {
      const [subject, heading, message] = F.templateText.Promotion;
      initial = { subject, heading, message, cta: 'Find out more', link: S.brand.website, ...initial };
    }
    formInitial = initial;
    const titles = { campaign: 'Campaign', advert: 'Advert', poster: 'Poster', social: 'Social Post', email: 'Email', activity: 'Marketing Activity', brand: 'Brand Kit' };
    modal(`${initial.id || kind === 'brand' ? 'Edit' : 'Create'} ${titles[kind]}`, F.render(kind, initial));
  }
  function preview(kind, id) {
    const item = S[collections[kind]].find(row => row.id === id);
    if (!item) return;
    const html = kind === 'email' ? C.emailPreview(item) : C.poster(item);
    modal(kind === 'email' ? 'Email preview' : 'Content preview', html + `<div class="form-actions">${C.btn('Edit', 'edit', id, kind === 'content' ? item.kind : kind)}${kind === 'email' ? '' : C.btn('Download (demo)', 'demo-download') + C.btn('Share (demo)', 'demo-share')}</div><p class="small-copy muted">Preview only. No content is sent or published.</p>`);
  }
  document.addEventListener('click', event => {
    const target = event.target.closest('[data-action]');
    if (target) {
      const { action, id, kind } = target.dataset;
      if (action === 'navigate') location.hash = id;
      if (action === 'create') create(kind);
      if (action === 'close') close();
      if (action === 'edit') {
        const item = S[collections[kind]].find(row => row.id === id); if (item) create(kind, item);
      }
      if (action === 'detail') {
        if (kind === 'content' || kind === 'email') preview(kind, id);
        else modal('Details', V.detail(kind, id));
      }
      if (action === 'preview') preview(kind, id);
      if (action === 'period') { S.period = id; render(); }
      if (action === 'month') {
        S.month = id === 'today' ? new Date(new Date().getFullYear(), new Date().getMonth(), 1) : new Date(S.month.getFullYear(), S.month.getMonth() + Number(id), 1); render();
      }
      if (action === 'crm') toast('CRM preview only — no lead was transferred.');
      if (action === 'demo-download') toast('Download preview only — no file was generated.');
      if (action === 'demo-share') toast('Share preview only — nothing was published or sent.');
      if (action === 'opportunity-ad') {
        const o = S.opportunities.find(item => item.id === id);
        const type = { Websites: 'Website', 'Mobile Apps': 'Mobile App', 'Social Media': 'Facebook', 'Local Business Directories': 'Local Business Directory', 'Community Radio': 'Community Radio', Newspapers: 'Newspaper/Magazine', Magazines: 'Newspaper/Magazine', Events: 'Event/Sponsorship', 'Outdoor Advertising': 'Billboard' }[o.type];
        create('advert', { publisher: o.publisher, location: o.location, audience: o.audience, type, budget: o.price, name: `Advert with ${o.publisher}` });
      }
      if (action === 'brand-example') {
        const item = { title: id === 'Posters' ? 'A little local inspiration' : id, heading: 'A little local inspiration', message: S.brand.short, subject: 'News from your local business', cta: 'Visit us', template: '1' };
        const html = id === 'Emails' ? C.emailPreview(item) : ['Invoices', 'Quotations', 'Business Profile'].includes(id) ? `<div class="document-preview" style="${C.brandStyle()}">${C.brandLogo()}<h2>${C.esc(S.brand.name)}</h2><p>${C.esc(S.brand.slogan)}</p><h3>${id} · Sample preview</h3><p>${C.esc(S.brand.long)}</p><hr><p>${C.esc(S.brand.phone)} · ${C.esc(S.brand.email)}</p><p>${C.esc(S.brand.location)}</p></div>` : C.poster(item);
        modal(`${id} with your branding`, html + '<p class="notice">This is a visual preview. No existing documents or other platform modules have been changed.</p>');
      }
    }
    if (!event.target.closest('#sidebar') && !event.target.closest('#menuButton')) closeSidebar();
  });
  function filter(event) {
    const input = event.target;
    if (!input.dataset.filter) return;
    S.filters[S.page] = { ...C.filter(S.page), [input.dataset.filter]: input.value };
    $('#results').innerHTML = V.results[S.page]();
  }
  document.addEventListener('input', event => { if (event.target.tagName !== 'SELECT') filter(event); });
  document.addEventListener('change', event => {
    const input = event.target;
    if (input.tagName === 'SELECT') filter(event);
    if (input.dataset.lead) {
      const lead = S.leads.find(l => l.id === input.dataset.lead);
      lead.status = input.value; render(); toast('Lead status updated in this preview.');
    }
    if (input.id === 'emailTemplate') {
      const [subject, heading, message] = F.templateText[input.value];
      const form = input.closest('form');
      form.elements.subject.value = subject; form.elements.heading.value = heading; form.elements.message.value = message;
    }
  });
  async function localImage(file) {
    if (!file || !file.size) return '';
    if (!['image/png', 'image/jpeg', 'image/webp', 'image/gif'].includes(file.type)) throw new Error('Please select a PNG, JPG, WebP or GIF image.');
    if (file.size > 5 * 1024 * 1024) throw new Error('Please use an image smaller than 5 MB.');
    return new Promise((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(reader.result); reader.onerror = () => reject(new Error('The image could not be read.')); reader.readAsDataURL(file); });
  }
  document.addEventListener('submit', async event => {
    const form = event.target.closest('form[data-form]'); if (!form) return;
    event.preventDefault(); if (!form.reportValidity()) return;
    if (form.dataset.busy === 'true') return;
    form.dataset.busy = 'true';
    try {
      const kind = form.dataset.form, intent = event.submitter?.value || 'save';
      const data = new FormData(form), values = Object.fromEntries(data);
      if (values.name !== undefined) values.name = values.name.trim();
      if (values.title !== undefined) values.title = values.title.trim();
      if (values.name === '' || values.title === '') throw new Error('Please enter a name or title.');
      if (values.start && values.end && values.end < values.start) throw new Error('End date must be on or after the start date.');
      if (kind === 'campaign') { values.channels = data.getAll('channels'); if (!values.channels.length) throw new Error('Choose at least one marketing channel.'); }
      for (const name of ['budget', 'spent']) if (name in values) { values[name] = Number(values[name]); if (!Number.isFinite(values[name]) || values[name] < 0) throw new Error('Amounts must be zero or greater.'); }
      for (const name of ['image', 'logo']) if (name in values) values[name] = await localImage(data.get(name)) || formInitial[name] || '';
      if (kind === 'social' && intent === 'schedule' || kind === 'email' && intent === 'schedule') {
        const value = kind === 'email' ? values.sendAt : values.schedule;
        if (!value || new Date(value).getTime() <= Date.now()) throw new Error('Choose a future date and time to schedule this item.');
      }
      if (['preview', 'download', 'share'].includes(intent)) {
        $('#formPreview').innerHTML = `<h3>Preview with your Brand Kit</h3>${kind === 'email' ? C.emailPreview(values) : C.poster(values)}`;
        if (intent !== 'preview') toast(intent === 'download' ? 'Download preview only — no file was generated.' : 'Share preview only — nothing was sent.');
        return;
      }
      if (kind === 'brand') Object.assign(S.brand, values);
      else {
        const existing = S[collections[kind]].find(item => item.id === form.dataset.id);
        let defaults = {};
        if (kind === 'campaign') defaults = { reach: 0 };
        if (kind === 'advert') defaults = { reach: 0, responses: 0, enquiries: 0, customers: 0, sales: 0 };
        if (kind === 'poster' || kind === 'social') {
          values.kind = kind; values.category = kind === 'poster' ? 'Posters' : 'Social Posts'; values.status = intent === 'schedule' ? 'Scheduled' : 'Draft';
          if (intent !== 'schedule') values.schedule = '';
        }
        if (kind === 'email') {
          values.status = intent === 'schedule' ? 'Scheduled' : intent === 'send' ? 'Send preview' : 'Draft';
          defaults = { sent: 0, delivered: 0, opened: 0, clicked: 0, enquiries: 0, customers: 0 };
        }
        if (existing) Object.assign(existing, values);
        else S[collections[kind]].push({ ...defaults, ...values, id: `new-${kind}-${counter++}` });
      }
      close(); render();
      toast(intent === 'send' ? 'Send preview saved. No email was sent.' : intent === 'schedule' ? 'Scheduled in this preview only. No message will be sent.' : 'Saved for this preview.');
    } catch (error) { $('#formError').textContent = error.message; }
    finally { form.dataset.busy = 'false'; }
  });
  $('#sidebarToggle').addEventListener('click', () => {
    const open = document.body.classList.toggle('sidebar-expanded');
    $('#sidebarToggle').setAttribute('aria-expanded', String(open)); $('#sidebarToggle').setAttribute('aria-label', open ? 'Collapse sidebar' : 'Expand sidebar'); $('#sidebarToggle').title = open ? 'Collapse sidebar' : 'Expand sidebar';
  });
  $('#menuButton').addEventListener('click', () => { const open = $('#sidebar').classList.toggle('open'); $('#menuButton').setAttribute('aria-expanded', String(open)); });
  $('#modal').addEventListener('cancel', event => { event.preventDefault(); close(); });
  document.addEventListener('keydown', event => { if (event.key === 'Escape') closeSidebar(); });
  window.addEventListener('hashchange', navigate);
  navigate();
})(window.Marketing);
