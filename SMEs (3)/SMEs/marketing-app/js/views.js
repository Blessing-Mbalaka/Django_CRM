/* Pages are small templates composed from shared Inventory-style controls. */
(function (A) {
  const S = A.state, C = A.C;
  const { esc, money, number, date, btn, badge, panel, intro, stats, table } = C;
  const campaignCounts = id => ({ leads: S.leads.filter(l => l.campaign === id).length, customers: S.leads.filter(l => l.campaign === id && l.status === 'Converted').length });

  function campaignCard(c) {
    const counts = campaignCounts(c.id);
    return `<article class="panel campaign-card"><div class="panel-header">${C.icon('campaigns')}${badge(c.status)}</div><h2>${esc(c.name)}</h2><p>${esc(c.channels.join(' + '))}</p><div class="card-metrics"><div><strong>${money(c.budget)}</strong><small>Budget</small></div><div><strong>${number(c.reach)}</strong><small>Reached</small></div><div><strong>${counts.leads}</strong><small>Leads</small></div></div>${btn('View campaign →', 'detail', c.id, 'campaign')}</article>`;
  }
  function dashboard() {
    const total = A.totals();
    return `<section class="banner"><div class="banner-copy"><span class="eyebrow">YOUR BRAND. YOUR COMMUNITY.</span><h2>Welcome back, ${esc(S.brand.name)}</h2><p>Manage your brand, campaigns, advertising and customer reach.</p><div class="marketing-banner-actions">${btn('＋ Create Campaign', 'create', '', 'campaign', 'shine')} ${btn('＋ Create Advert', 'create', '', 'advert', 'secondary')}</div></div><img src="../assets/inventory-banner.png" alt="Business owner organising their workspace"></section>` + stats([
      ['Active Campaigns', S.campaigns.filter(c => c.status === 'Active').length, 'campaigns'], ['Active Adverts', S.ads.filter(a => a.status === 'Live').length, 'advertising'], ['Marketing Spend', money(total.spent)]
    ]) + `<div class="marketing-grid marketing-dashboard-panels">${panel('Marketing performance', 'From being seen to bringing customers through the door', C.performance())}${panel('Upcoming marketing', 'A simple plan for the days ahead', upcoming(), btn('Calendar ↗', 'navigate', 'calendar'))}</div>`;
  }
  function campaignRows() {
    return table(['Campaign', 'Objective', 'Channels', 'Budget', 'Dates', 'Leads', 'Customers', 'Status', 'Action'], S.campaigns.filter(c => C.matches(c, 'campaigns', 'status', c.start)).map(c => {
      const counts = campaignCounts(c.id);
      return [`<strong>${esc(c.name)}</strong>`, esc(c.objective), esc(c.channels.join(', ')), money(c.budget), `${date(c.start)} – ${date(c.end)}`, counts.leads, counts.customers, badge(c.status), btn('View', 'detail', c.id, 'campaign')];
    }));
  }
  function campaigns() {
    return intro('Plan what you are promoting, who it is for, and where to share it.') + panel('Your campaigns', 'A clear plan for every promotion', C.filters('campaigns', ['Draft', 'Scheduled', 'Active', 'Completed', 'Paused'], true) + `<div id="results">${campaignRows()}</div>`);
  }
  function advertisingRows() {
    return table(['Advert', 'Where it runs', 'Location', 'Spent / Budget', 'Reach', 'Enquiries', 'Customers', 'Status', 'Action'], S.ads.filter(a => C.matches(a, 'advertising', 'status', a.start)).map(a => [`<strong>${esc(a.name)}</strong>`, `${esc(a.publisher)}<small>${esc(a.type)}</small>`, esc(a.location), `${money(a.spent)} / ${money(a.budget)}`, number(a.reach), a.enquiries, a.customers, badge(a.status), btn('Performance', 'detail', a.id, 'advert')]));
  }
  function advertising() {
    const sum = field => S.ads.reduce((total, a) => total + Number(a[field] || 0), 0);
    return intro('Manage where your business advertises and track what works.', btn('Find Advertising Opportunities', 'navigate', 'opportunities')) + stats([['Active Adverts', S.ads.filter(a => a.status === 'Live').length, 'advertising'], ['Advertising Spend', money(sum('spent'))], ['Total Reach', number(sum('reach'))], ['Enquiries', sum('enquiries'), 'leads'], ['Customers Generated', sum('customers'), 'leads']]) + panel('Your adverts', 'Online, on air, or around the neighbourhood', C.filters('advertising', ['Draft', 'Scheduled', 'Live', 'Paused', 'Ended'], true) + `<div id="results">${advertisingRows()}</div>`);
  }
  function opportunityRows() {
    const items = S.opportunities.filter(o => C.matches(o, 'opportunities', 'type'));
    return items.length ? `<div class="three-grid">${items.map(o => `<article class="panel opportunity-card">${badge(o.type)}<h2>${esc(o.publisher)}</h2><p>${esc(o.description)}</p><dl><dt>Location / Audience</dt><dd>${esc(o.location)} · ${esc(o.audience)}</dd><dt>Estimated reach</dt><dd>${number(o.reach)} people</dd><dt>Starting price</dt><dd>${money(o.price)}${o.id === 'op0' ? '/month' : ''}</dd></dl>${btn('View Opportunity', 'detail', o.id, 'opportunity')}</article>`).join('')}</div>` : C.empty('No matching opportunities');
  }
  function opportunities() {
    return intro('Explore sample places to advertise locally. Prices and reach are illustrative.', btn('← Advertising', 'navigate', 'advertising')) + C.filters('opportunities', S.opportunities.map(o => o.type)) + `<div id="results">${opportunityRows()}</div>`;
  }
  function contentRows() {
    const items = S.content.filter(c => C.matches(c, 'content', 'category'));
    return items.length ? `<div class="content-grid">${items.map(item => `<article class="panel library-card"><div class="library-preview">${C.poster(item)}</div><div class="library-caption"><div><strong>${esc(item.title)}</strong><small>${esc(item.category)} · ${esc(item.status)}</small></div>${btn('Preview', 'preview', item.id, 'content')}</div></article>`).join('')}</div>` : C.empty('No content in this view');
  }
  function content() {
    return intro('Create simple promotional material for your business.', btn('＋ Create Social Post', 'create', '', 'social')) + C.filters('content', ['Posters', 'Social Posts', 'Promotions', 'Images']) + `<div id="results">${contentRows()}</div>`;
  }
  function emailRows() {
    return table(['Campaign', 'Audience', 'Send date', 'Sent', 'Delivered', 'Opened', 'Clicked', 'Enquiries', 'Customers', 'Status', 'Action'], S.emails.filter(e => C.matches(e, 'email', 'status', e.sendAt.slice(0, 10))).map(e => [`<strong>${esc(e.name)}</strong><small>${esc(e.subject)}</small>`, esc(e.audience), date(e.sendAt), e.sent, e.delivered, e.opened, e.clicked, e.enquiries, e.customers, badge(e.status), btn('Preview', 'preview', e.id, 'email')]));
  }
  function email() {
    const sum = name => S.emails.reduce((total, item) => total + Number(item[name] || 0), 0);
    return intro('Send promotions and updates to your customers. This preview does not send email.') + stats([['Emails Sent', sum('sent'), 'email'], ['Delivered', sum('delivered'), 'email'], ['Opened', sum('opened'), 'email'], ['Clicked', sum('clicked')], ['Enquiries', sum('enquiries'), 'leads']]) + panel('Email campaigns', 'Simple messages, with your branding already in place', C.filters('email', ['Draft', 'Scheduled', 'Sent (sample)', 'Send preview'], true) + `<div id="results">${emailRows()}</div>`);
  }
  function calendarItems() {
    return [
      ...S.campaigns.map(c => ({ name: c.name, date: c.start, type: 'Campaign', id: c.id, kind: 'campaign' })),
      ...S.ads.map(a => ({ name: a.name, date: a.start, type: 'Advert', id: a.id, kind: 'advert' })),
      ...S.emails.filter(e => e.status !== 'Draft' && e.sendAt).map(e => ({ name: e.name, date: e.sendAt.slice(0, 10), type: 'Email', id: e.id, kind: 'email' })),
      ...S.content.filter(c => c.schedule).map(c => ({ name: c.title, date: c.schedule.slice(0, 10), type: 'Social Post', id: c.id, kind: 'content' })),
      ...S.activities.map(a => ({ ...a, kind: 'activity' }))
    ];
  }
  function upcoming() {
    const items = calendarItems().filter(i => i.date >= A.today).sort((a, b) => a.date.localeCompare(b.date)).slice(0, 2);
    return items.length ? items.map(i => `<button class="upcoming-row" data-action="detail" data-kind="${i.kind}" data-id="${i.id}"><span>${date(i.date)}</span><div><strong>${esc(i.name)}</strong><small>${esc(i.type)}</small></div><b>↗</b></button>`).join('') : C.empty('Nothing scheduled yet');
  }
  function calendar() {
    const start = new Date(S.month.getFullYear(), S.month.getMonth(), 1);
    start.setDate(start.getDate() - (start.getDay() + 6) % 7);
    const types = ['Campaign', 'Advert', 'Email', 'Social Post', 'Promotion', 'Event'];
    const events = calendarItems();
    const days = Array.from({ length: 42 }, (_, i) => {
      const d = new Date(start); d.setDate(d.getDate() + i); const key = A.key(d);
      const labels = events.filter(event => event.date === key).map(event => `<button class="calendar-event tone-${Math.max(0, types.indexOf(event.type))}" title="${esc(event.name)}" data-action="detail" data-id="${event.id}" data-kind="${event.kind}">${esc(event.name)}</button>`).join('');
      return `<div class="calendar-day ${d.getMonth() !== S.month.getMonth() ? 'outside' : ''}"><time class="${key === A.today ? 'is-today' : ''}" datetime="${key}">${d.getDate()}</time>${labels}</div>`;
    }).join('');
    const header = `<div class="actions"><button class="btn secondary small" data-action="month" data-id="-1" aria-label="Previous month">←</button>${btn('Today', 'month', 'today')}<button class="btn secondary small" data-action="month" data-id="1" aria-label="Next month">→</button></div>`;
    const legend = `<div class="calendar-legend">${types.map((type, i) => `<span class="tone-${i}">${type}</span>`).join('')}</div>`;
    const weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(day => `<div class="weekday">${day}</div>`).join('');
    return intro('See the plan for your next promotion at a glance.') + panel(S.month.toLocaleDateString('en-ZA', { month: 'long', year: 'numeric' }), 'Your marketing schedule', legend + `<div class="calendar-scroll"><div class="calendar-grid">${weekdays}${days}</div></div>`, header);
  }
  function leadRows() {
    return table(['Name', 'Contact', 'Campaign', 'Source', 'Date', 'Status', 'Value', 'Action'], S.leads.filter(l => C.matches(l, 'leads', 'status', l.date)).map(l => [`<strong>${esc(l.name)}</strong>`, esc(l.contact), esc(C.lookup(l.campaign)), esc(l.source), date(l.date), `<select class="inline-select" aria-label="Status for ${esc(l.name)}" data-lead="${l.id}">${C.options(['New', 'Contacted', 'Interested', 'Converted', 'Not Interested'], l.status)}</select>`, money(l.value), btn('Send to CRM', 'crm', l.id)]));
  }
  function leads() {
    return intro('Follow up with people who found you through your marketing.') + `<div id="leadStats">${stats(['New', 'Contacted', 'Interested', 'Converted'].map(status => [status === 'New' ? 'New Leads' : status, S.leads.filter(l => l.status === status).length, 'leads']))}</div>` + panel('Marketing leads', 'Only enquiries from your marketing activity', C.filters('leads', ['New', 'Contacted', 'Interested', 'Converted', 'Not Interested'], true) + `<div id="results">${leadRows()}</div>`);
  }
  function analytics() {
    const t = A.totals();
    const steps = [['People reached', number(t.reach)], ['Enquiries', t.enquiries], ['Leads', t.leads], ['Customers', t.customers], ['Sales', money(t.sales)]];
    const funnel = `<div class="marketing-funnel">${steps.map(([label, value], i) => `<div style="width:${100 - i * 9}%"><span>${label}</span><strong>${value}</strong></div>${i < 4 ? '<span aria-hidden="true">↓</span>' : ''}`).join('')}</div>`;
    return intro('See where your money goes and what it brings back. Sample results for the last 30 days.') + stats([['Total Marketing Spend', money(t.spent)], ['Total Reach', number(t.reach)], ['Enquiries Generated', t.enquiries, 'leads'], ['Customers Acquired', t.customers, 'leads'], ['Revenue Generated', money(t.sales)]]) + `<div class="marketing-grid">${panel('From attention to sales', 'A simple view of your marketing journey', funnel)}${panel('Where customers found you', 'Rose chart · sector area represents customer count', C.rose())}</div>` + panel('Where your marketing money worked', 'Compare spending with leads, customers and sales', table(['Channel', 'Spent', 'Leads', 'Customers', 'Sales'], S.results.map(r => [esc(r.channel), money(r.spent), r.leads, r.customers, money(r.sales)]))) + `<p class="notice">You spent ${money(t.spent)} and generated ${money(t.sales)} in sample sales. That is ${Number(t.sales / t.spent).toFixed(2)} rand in sales for every rand spent. Sales are revenue, not profit.</p>`;
  }
  function brand() {
    const b = S.brand;
    const preview = `<div class="brand-preview" style="${C.brandStyle()}"><div class="brand-lockup">${C.brandLogo()}<div><h2>${esc(b.name)}</h2><p>${esc(b.slogan)}</p></div></div><p>${esc(b.short)}</p><div class="brand-swatches">${[b.primary, b.secondary, b.accent].map(value => `<div><span style="background:${/^#[0-9a-f]{6}$/i.test(value) ? value : '#175b46'}"></span><small>${esc(value)}</small></div>`).join('')}</div><p>${esc(b.font)} · ${esc(b.secondaryFont)}</p><div class="brand-contact">${esc(b.phone)} · ${esc(b.email)}<br>${esc(b.website)}<br>${esc(b.location)}</div></div>`;
    const reuse = `<div class="brand-uses">${['Posters', 'Emails', 'Campaigns', 'Adverts', 'Invoices', 'Quotations', 'Business Profile'].map(item => btn(item + ' ↗', 'brand-example', item)).join('')}</div><p class="muted small-copy">Posters and emails use your saved Brand Kit in this demo. Business documents below are previews; existing platform documents are unchanged.</p>`;
    return intro('Keep your business identity consistent everywhere.') + `<div class="marketing-grid">${panel('Your business identity', 'Logo, colours and contact details, together', preview)}${panel('Ready to use everywhere', 'One brand across your marketing and business documents', reuse + C.details([['Short description', b.short], ['Facebook', b.facebook || 'Not added'], ['Instagram', b.instagram || 'Not added'], ['TikTok', b.tiktok || 'Not added'], ['LinkedIn', b.linkedin || 'Not added']]))}</div>`;
  }
  function detail(kind, id) {
    if (kind === 'campaign') {
      const c = S.campaigns.find(c => c.id === id); if (!c) return C.empty('Campaign not found');
      const counts = campaignCounts(id);
      return `<div class="brand-mini">${esc(S.brand.name)} · ${esc(S.brand.slogan)}</div>` + C.details([['Campaign', c.name], ['Objective', c.objective], ['Product / Service', c.product], ['Audience', c.audience], ['Location', c.location], ['Channels', c.channels.join(', ')], ['Dates', `${date(c.start)} – ${date(c.end)}`], ['Budget', money(c.budget)], ['Leads / Customers', `${counts.leads} / ${counts.customers}`], ['Status', c.status], ['Description', c.description]]) + btn('Edit Campaign', 'edit', id, kind);
    }
    if (kind === 'advert') {
      const a = S.ads.find(a => a.id === id); if (!a) return C.empty('Advert not found');
      const cpl = a.enquiries ? money(a.spent / a.enquiries) : 'No enquiries yet';
      const roas = a.spent ? (a.sales / a.spent).toFixed(2) + '×' : 'No spend yet';
      return `<div class="brand-mini">${esc(S.brand.name)}</div>` + C.details([['Advert', a.name], ['Advertising', a.what], ['Platform / Type', `${a.publisher} · ${a.type}`], ['Audience', a.audience], ['Location', a.location], ['Dates', `${date(a.start)} – ${date(a.end)}`], ['Campaign', C.lookup(a.campaign)], ['Budget', money(a.budget)], ['Amount spent', money(a.spent)], ['People reached', number(a.reach)], ['Clicks / Responses', a.responses], ['Enquiries', a.enquiries], ['Customers', a.customers], ['Sales generated', money(a.sales)], ['Cost per lead (enquiry)', cpl], ['Return on advertising spend', roas], ['Advert link', a.link || 'Not added'], ['Status', a.status]]) + `<p class="notice">You spent ${money(a.spent)} and generated ${money(a.sales)} in sample sales. Cost per lead is spending divided by enquiries; sales are not profit.</p>` + btn('Edit Advert', 'edit', id, kind);
    }
    if (kind === 'opportunity') {
      const o = S.opportunities.find(o => o.id === id);
      return C.details([['Publisher', o.publisher], ['Type', o.type], ['Location', o.location], ['Audience', o.audience], ['Estimated reach', number(o.reach)], ['Starting price', money(o.price)], ['Description', o.description]]) + '<p class="notice">Illustrative opportunity only. This is not a live listing, booking or verified quote.</p>' + btn('Plan an advert here', 'opportunity-ad', id, '', '');
    }
    if (kind === 'email') return C.emailPreview(S.emails.find(e => e.id === id));
    if (kind === 'content') return C.poster(S.content.find(c => c.id === id));
    const activity = S.activities.find(a => a.id === id);
    return activity ? C.details([['Activity', activity.name], ['Type', activity.type], ['Date', date(activity.date)], ['Description', activity.description]]) : C.empty('Activity not found');
  }
  A.V = { dashboard, campaigns, advertising, opportunities, content, email, calendar, leads, analytics, brand, detail, calendarItems, results: { campaigns: campaignRows, advertising: advertisingRows, opportunities: opportunityRows, content: contentRows, email: emailRows, leads: leadRows } };
})(window.Marketing);
