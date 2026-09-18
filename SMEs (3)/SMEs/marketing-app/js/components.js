/* Reusable controls, charts and brand previews. */
(function (A) {
  const S = A.state;
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const money = value => new Intl.NumberFormat('en-ZA', { style: 'currency', currency: 'ZAR', maximumFractionDigits: 0 }).format(Number(value) || 0);
  const number = value => new Intl.NumberFormat('en-ZA').format(Number(value) || 0);
  const date = value => value ? new Date(`${value.slice(0, 10)}T12:00:00`).toLocaleDateString('en-ZA', { day: 'numeric', month: 'short' }) : 'Not set';
  const icons = {
    dashboard: 'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z',
    campaigns: 'M4 5h7l2 3h8v12H4z', advertising: 'M3 9h5l12-5v16L8 15H3zM8 15l2 6H6l-2-6',
    content: 'M4 3h16v18H4zM7 16l4-5 3 3 3-2M8 7h.01', email: 'M3 5h18v14H3zM3 5l9 8 9-8',
    calendar: 'M4 5h16v16H4zM4 10h16M8 3v4M16 3v4M8 14h2M14 14h2M8 18h2',
    leads: 'M9 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6M2 20v-2a7 5 0 0 1 14 0v2M17 5a3 3 0 0 1 0 6M18 14a5 4 0 0 1 4 4v2',
    analytics: 'M4 3v18h17M8 16v-5M13 16V6M18 16V9', brand: 'M12 3l9 5-9 5-9-5zM3 12l9 5 9-5M3 16l9 5 9-5'
  };
  const icon = name => `<svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="${icons[name] || icons.campaigns}"/></svg>`;
  const btn = (label, action, id = '', kind = '', style = 'secondary small') => `<button type="button" class="btn ${style}" data-action="${action}" data-id="${esc(id)}" data-kind="${kind}">${label}</button>`;
  const badge = status => `<span class="badge ${['Active', 'Live', 'Converted', 'Sent (sample)'].includes(status) ? 'deep' : ''}">${esc(status)}</span>`;
  const empty = message => `<div class="empty"><strong>${message}</strong><p>Try another filter or create your first item.</p></div>`;
  const panel = (title, subtitle, body, action = '') => `<section class="panel"><div class="panel-header"><div><h2>${title}</h2><p>${subtitle}</p></div>${action}</div>${body}</section>`;
  const intro = (text, action = '') => `<div class="module-intro"><p>${text}</p>${action}</div>`;
  const stats = items => `<div class="stats marketing-stats" style="--count:${items.length}">${items.map(([label, value, glyph]) => `<article class="stat"><div class="stat-label">${label}${icon(glyph || 'analytics')}</div><strong>${value}</strong><small>Sample workspace</small></article>`).join('')}</div>`;
  const table = (headers, rows) => rows.length ? `<div class="table-wrap"><table><thead><tr>${headers.map(h => `<th scope="col">${h}</th>`).join('')}</tr></thead><tbody>${rows.map(row => `<tr>${row.map(cell => `<td>${cell}</td>`).join('')}</tr>`).join('')}</tbody></table></div>` : empty('No matching items');
  const options = (items, selected, placeholder = '') => (placeholder ? `<option value="">${placeholder}</option>` : '') + items.map(item => `<option value="${esc(item)}" ${item === selected ? 'selected' : ''}>${esc(item)}</option>`).join('');
  const lookup = id => S.campaigns.find(c => c.id === id)?.name || 'No campaign';
  const tabs = (items, selected, action) => `<div class="report-tabs" role="group" aria-label="Choose view">${items.map(item => `<button type="button" class="btn secondary small ${item === selected ? 'active' : ''}" data-action="${action}" data-id="${esc(item)}" aria-pressed="${item === selected}">${esc(item)}</button>`).join('')}</div>`;
  const filter = page => S.filters[page] || { q: '', status: '', from: '', to: '' };
  function filters(page, statuses, dateFilter = false) {
    const f = filter(page);
    return `<div class="filters"><input type="search" placeholder="Search ${page}..." aria-label="Search ${page}" data-filter="q" value="${esc(f.q)}"><select aria-label="Filter ${page}" data-filter="status">${options(statuses, f.status, 'All')}</select>${dateFilter ? `<label>From<input type="date" data-filter="from" value="${f.from || ''}"></label><label>To<input type="date" data-filter="to" value="${f.to || ''}"></label>` : ''}</div>`;
  }
  function matches(item, page, statusKey = 'status', dateValue = '') {
    const f = filter(page);
    return (!f.q || JSON.stringify(item).toLowerCase().includes(f.q.toLowerCase())) && (!f.status || item[statusKey] === f.status) && (!f.from || dateValue >= f.from) && (!f.to || dateValue <= f.to);
  }
  function performance() {
    const totals = A.totals();
    const factor = { '7 Days': .24, '30 Days': 1, '3 Months': 2.7 }[S.period];
    const items = [['Enquiries', totals.enquiries], ['Customers', totals.customers]];
    const maximum = Math.max(...items.map(([, value]) => value), 1);
    return `${tabs(['7 Days', '30 Days', '3 Months'], S.period, 'period')}<div class="performance-bars">${items.map(([label, value], i) => `<div><span>${label}</span><strong>${number(Math.round(value * factor))}</strong><div class="performance-track"><span style="width:${value / maximum * 100}%;background:${['#79af91', '#c1dec4'][i]}"></span></div></div>`).join('')}</div><p class="muted small-copy">Illustrative ${S.period.toLowerCase()} results. Compare enquiries with customers acquired.</p>`;
  }
  function rose() {
    const colors = ['#175b46', '#35765b', '#59977a', '#7aaf91', '#a0cab0', '#c2dfc6', '#e0eddb'];
    const max = Math.max(...S.results.map(r => r.customers), 1);
    const step = Math.PI * 2 / S.results.length;
    const slices = S.results.map((row, i) => {
      const r = 118 * Math.sqrt(row.customers / max);
      const a = -Math.PI / 2 + i * step, b = a + step;
      const point = angle => `${140 + r * Math.cos(angle)} ${140 + r * Math.sin(angle)}`;
      return `<path d="M140 140 L${point(a)} A${r} ${r} 0 0 1 ${point(b)} Z" fill="${colors[i]}"><title>${esc(row.channel)}: ${row.customers} customers</title></path>`;
    }).join('');
    return `<div class="source-chart"><svg viewBox="0 0 280 280" role="img" aria-label="Customers by source: ${esc(S.results.map(r => `${r.channel} ${r.customers}`).join(', '))}">${[30, 60, 90, 118].map(r => `<circle cx="140" cy="140" r="${r}" fill="none" stroke="#eaf0e6"/>`).join('')}${slices}</svg><div class="legend">${S.results.map((r, i) => `<div><span class="dot" style="background:${colors[i]}"></span>${esc(r.channel)}<strong>${r.customers}</strong></div>`).join('')}</div></div>`;
  }
  const color = (value, fallback) => /^#[0-9a-f]{6}$/i.test(value) ? value : fallback;
  const fonts = ['Segoe UI', 'Arial', 'Georgia', 'Verdana', 'Tahoma'];
  const brandStyle = () => `--brand-primary:${color(S.brand.primary, '#175b46')};--brand-secondary:${color(S.brand.secondary, '#d9ebd8')};--brand-accent:${color(S.brand.accent, '#ef8d55')};--brand-heading:'${fonts.includes(S.brand.secondaryFont) ? S.brand.secondaryFont : 'Georgia'}';font-family:'${fonts.includes(S.brand.font) ? S.brand.font : 'Segoe UI'}',sans-serif`;
  const safeImage = value => typeof value === 'string' && (/^data:image\/(png|jpeg|webp|gif);base64,/i.test(value) || value.startsWith('blob:')) ? value : '';
  const image = (value, alt) => safeImage(value) ? `<img src="${esc(value)}" alt="${esc(alt)}">` : '';
  const brandLogo = () => S.brand.logo ? image(S.brand.logo, S.brand.name + ' logo') : `<span class="brand-monogram">${esc(S.brand.name.split(' ').map(w => w[0]).slice(0, 2).join(''))}</span>`;
  function poster(item) {
    const b = S.brand;
    return `<div class="poster template-${['1', '2', '3', '4'].includes(String(item.template)) ? item.template : '1'}" style="${brandStyle()}"><div class="poster-brand">${brandLogo()}<span>${esc(b.name)}</span></div><div class="poster-main"><span class="poster-kicker">${esc(item.product || b.slogan)}</span><h2>${esc(item.title || 'Your next local favourite')}</h2><p>${esc(item.message || item.caption || b.short)}</p>${image(item.image, item.title || 'Poster image')}${item.price ? `<strong class="poster-price">${esc(item.price)}</strong>` : ''}${item.promotion ? `<span class="poster-offer">${esc(item.promotion)}</span>` : ''}</div><div class="poster-contact"><strong>${esc(item.cta || 'Visit us today')}</strong><span>${esc(item.phone || b.phone)} · WhatsApp ${esc(item.whatsapp || b.whatsapp)}</span><span>${esc(item.website || b.website)}</span>${item.start ? `<span>${date(item.start)} – ${date(item.end || item.start)}</span>` : ''}</div></div>`;
  }
  function emailPreview(item) {
    return `<div class="email-preview" style="${brandStyle()}"><div class="email-brand">${brandLogo()}<strong>${esc(S.brand.name)}</strong></div><div class="email-copy"><small>${esc(item.subject)}</small><h2>${esc(item.heading || item.title)}</h2>${image(item.image, 'Email promotion')}<p>${esc(item.message)}</p><span class="preview-cta">${esc(item.cta || 'Find out more')}</span><small class="muted">${esc(item.link)}</small></div><div class="email-contact">${esc(S.brand.slogan)}<br>${esc(S.brand.phone)} · ${esc(S.brand.email)}<br>${esc(S.brand.location)}</div></div>`;
  }
  const details = entries => `<dl class="detail-grid">${entries.map(([label, value]) => `<div><dt>${label}</dt><dd>${esc(value)}</dd></div>`).join('')}</dl>`;
  A.C = { esc, money, number, date, icon, btn, badge, empty, panel, intro, stats, table, options, lookup, tabs, filter, filters, matches, performance, rose, brandStyle, brandLogo, image, poster, emailPreview, details, fonts };
})(window.Marketing);
