export const esc = value => String(value ?? '').replace(/[&<>'"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[char]);
export const money = value => new Intl.NumberFormat('en-ZA', { style: 'currency', currency: 'ZAR', maximumFractionDigits: 2 }).format(Number(value || 0));
export const formatNumber = value => new Intl.NumberFormat('en-ZA').format(Number(value || 0));
const date = value => value ? new Intl.DateTimeFormat('en-ZA', { dateStyle: 'medium' }).format(new Date(value)) : 'Not set';
const badge = value => `<span class="badge">${esc(String(value || 'draft').replaceAll('_', ' '))}</span>`;
const empty = message => `<section class="panel empty-state"><h2>No data yet</h2><p>${esc(message)}</p></section>`;
const panel = (title, subtitle, content) => `<section class="panel"><div class="section-heading"><div><h2>${esc(title)}</h2><p class="muted">${esc(subtitle)}</p></div></div>${content}</section>`;
const stats = rows => `<div class="stats marketing-stats" style="--count:${Math.min(rows.length, 5)}">${rows.map(([label, value]) => `<article class="stat"><span>${esc(label)}</span><strong>${esc(value)}</strong></article>`).join('')}</div>`;
const action = (label, name, id = '', tone = 'secondary') => `<button type="button" class="btn ${tone} small" data-action="${name}" data-id="${esc(id)}">${esc(label)}</button>`;

function table(headers, rows) {
  if (!rows.length) return '<p class="no-data">Nothing has been recorded in this view yet.</p>';
  return `<div class="table-wrap"><table><thead><tr>${headers.map(item => `<th>${esc(item)}</th>`).join('')}</tr></thead><tbody>${rows.map(row => `<tr>${row.map(cell => `<td>${cell}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
}

export function dashboard(state) {
  const c = state.summary.campaigns || {};
  const l = state.summary.leads || {};
  const d = state.summary.delivery || {};
  return `<section class="banner"><div class="banner-copy"><span class="eyebrow">YOUR BRAND. YOUR COMMUNITY.</span><h2>${esc(state.brand.business_name || 'Build your marketing workspace')}</h2><p>Manage your brand, campaigns, advertising and customer reach using live CRM data.</p><div class="marketing-banner-actions">${state.canManage ? action('＋ Create Campaign', 'create', 'campaign', 'shine') + action('＋ Create Advert', 'create', 'advert') : ''}</div></div><img src="/static/sme/assets/inventory-banner.png" alt=""></section>${stats([['Active Campaigns', c.active || 0], ['Adverts', state.summary.adverts || 0], ['Marketing Leads', l.total || 0], ['Messages Delivered', d.delivered || 0]])}<div class="marketing-grid">${panel('Marketing performance', 'Measured from saved activity', state.analytics.available ? `<p><strong>${formatNumber(state.analytics.totals.reach)}</strong> people reached</p><p><strong>${money(state.analytics.totals.revenue)}</strong> attributed revenue</p>` : '<p class="no-data">No performance measurements have been recorded yet.</p>')}${panel('Provider readiness', 'External services are independently configurable', document.querySelector('#providerStatus').innerHTML || '<p>Checking services…</p>')}</div>`;
}

export function campaigns(state) {
  const rows = state.campaigns.map(item => [`<strong>${esc(item.name)}</strong>`, esc(item.objective || '—'), esc((item.channels || []).join(', ') || '—'), money(item.budget), `${date(item.start_date)} – ${date(item.end_date)}`, badge(item.status), state.canManage ? `<div class="data-actions">${action('Edit', 'edit', `campaign:${item.id}`)}${action('Delete', 'delete', `campaign:${item.id}`)}</div>` : '<span class="muted">Read only</span>']);
  return panel('Your campaigns', 'A clear plan for every promotion', table(['Campaign', 'Objective', 'Channels', 'Budget', 'Dates', 'Status', 'Actions'], rows));
}

export function advertising(state) {
  const rows = state.adverts.map(item => [`<strong>${esc(item.name)}</strong>`, esc(item.platform || item.advertising_type || '—'), esc(item.location || '—'), `${money(item.actual_spend)} / ${money(item.budget)}`, badge(item.status), state.canManage ? `<div class="data-actions">${action('Edit', 'edit', `advert:${item.id}`)}${action('Delete', 'delete', `advert:${item.id}`)}</div>` : '<span class="muted">Read only</span>']);
  return `<div class="module-intro"><p>Manage where your business advertises and track what works.</p>${action('Advertising Opportunities', 'opportunities')}</div>${panel('Your adverts', 'Online, on air, or around the neighbourhood', table(['Advert', 'Platform', 'Location', 'Spent / Budget', 'Status', 'Actions'], rows))}`;
}

export function opportunities() {
  const items = [['Facebook & Instagram', 'Reach local audiences through your connected Meta business assets.'], ['WhatsApp', 'Use consented customer conversations and approved templates.'], ['Community & events', 'Record local radio, print, directory, outdoor and sponsorship plans.']];
  return `<div class="module-intro"><p>Plan channel opportunities; rates and bookings must be confirmed directly with publishers.</p>${action('← Advertising', 'navigate', 'advertising')}</div><div class="three-grid">${items.map(([name, copy]) => `<article class="panel opportunity-card"><span class="badge">Channel</span><h2>${esc(name)}</h2><p>${esc(copy)}</p></article>`).join('')}</div>`;
}

export function content(state) {
  if (!state.content.length) return empty('Upload your first genuine poster or social image.');
  return `<div class="content-grid">${state.content.map(item => `<article class="panel library-card"><div class="library-preview">${item.image ? `<img src="${esc(item.image)}" alt="">` : '<div class="empty-state">No image</div>'}</div><div class="library-caption"><div><strong>${esc(item.title)}</strong><small>${esc(item.kind)} · ${esc(item.status)}</small></div>${state.canManage ? `<div class="data-actions">${action('Edit', 'edit', `content:${item.id}`)}${action('Delete', 'delete', `content:${item.id}`)}</div>` : ''}</div></article>`).join('')}</div>`;
}

export function email(state) {
  const emails = state.messages.filter(item => item.channel === 'email');
  return `<div class="module-intro"><p>Send only to contacts with affirmative email consent.</p>${state.canManage ? action('Add Contact', 'create', 'contact') : ''}</div>${panel('Email campaigns', 'Twilio Email delivery and status tracking', table(['Subject', 'Recipient', 'Scheduled', 'Status', 'Attempts', 'Actions'], emails.map(item => [esc(item.subject_snapshot || 'Untitled email'), esc(item.destination), date(item.scheduled_at || item.created_at), badge(item.status), esc(item.attempt_count), state.canManage ? `<div class="data-actions">${['failed', 'unavailable'].includes(item.status) ? action('Retry', 'retry', item.id) : ''}${['draft', 'scheduled', 'failed', 'unavailable'].includes(item.status) ? action('Cancel', 'cancel', item.id) : ''}</div>` : '<span class="muted">Read only</span>'])))}`;
}

export function calendar(state) {
  return panel('Marketing calendar', 'Campaigns, adverts, scheduled content and activities', table(['Date', 'Item', 'Source', 'Status'], state.calendar.map(item => [date(item.starts_at), `<strong>${esc(item.title)}</strong>`, esc(item.source), badge(item.status || item.type)])));
}

export function leads(state) {
  return `${stats([['New Leads', state.leads.filter(item => item.status === 'new').length], ['Interested', state.leads.filter(item => item.status === 'interested').length], ['Converted', state.leads.filter(item => item.status === 'converted').length]])}${panel('Marketing leads', 'Follow up and transfer qualified interest to CRM', table(['Contact', 'Source', 'Received', 'Status', 'Value', 'Actions'], state.leads.map(item => [esc(state.contacts.find(contact => contact.id === item.contact)?.name || `Lead ${item.id}`), esc(item.acquisition_source || '—'), date(item.received_date), badge(item.status), money(item.estimated_value), state.canManage ? `<div class="data-actions">${action('Edit', 'edit', `lead:${item.id}`)}${!item.client ? action('Send to CRM', 'convert', item.id) : '<span class="badge">In CRM</span>'}</div>` : '<span class="muted">Read only</span>'])) )}`;
}

export function analytics(state, charts) {
  if (!state.analytics.available) return empty('Add Marketing Metrics to see reach, enquiries, customers, spend and return.');
  const t = state.analytics.totals;
  return `${stats([['Marketing Spend', money(t.spend)], ['Total Reach', formatNumber(t.reach)], ['Enquiries', formatNumber(t.enquiries)], ['Customers', formatNumber(t.customers)], ['Attributed Revenue', money(t.revenue)]])}<div class="marketing-grid">${panel('From attention to customers', 'The measured marketing journey', charts.funnel(t))}${panel('Attributed revenue by channel', 'Based only on recorded metrics', charts.channelBars(state.analytics.channels))}</div><p class="notice">${state.analytics.roas === null ? 'ROAS is unavailable until spend is recorded.' : `Recorded return on advertising spend: ${state.analytics.roas}×.`}</p>`;
}

export function brand(state) {
  const b = state.brand;
  return `<div class="marketing-grid">${panel('Your business identity', 'Logo, colours and contact details together', `${b.logo ? `<img class="brand-logo" src="${esc(b.logo)}" alt="${esc(b.business_name)} logo">` : ''}<h2>${esc(b.business_name || 'Business name not added')}</h2><p>${esc(b.slogan || 'Add your slogan')}</p><div class="brand-swatches">${[b.primary_colour, b.secondary_colour, b.accent_colour].filter(Boolean).map(value => `<div><span style="background:${esc(value)}"></span><small>${esc(value)}</small></div>`).join('')}</div>`)}${panel('Ready to reuse', 'Saved contact and profile information', `<p>${esc(b.short_description || 'Add a short business description.')}</p><p>${esc(b.phone || 'No phone')} · ${esc(b.email || 'No email')}</p><p>${esc(b.website || 'No website')}</p><p>${esc(b.physical_location || 'No location')}</p>`)}</div>`;
}

export { action, badge, empty, panel, stats, table };
