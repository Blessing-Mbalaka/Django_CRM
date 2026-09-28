import { API } from './api.js';
import * as Views from './views.js';
import * as Forms from './forms.js';
import * as Charts from './charts.js';

const $ = selector => document.querySelector(selector);
const pages = {
  dashboard: 'Marketing & Advertising', campaigns: 'Campaigns', advertising: 'Advertising',
  content: 'Posters & Content', email: 'Email Marketing', calendar: 'Marketing Calendar',
  leads: 'Marketing Leads', analytics: 'Analytics', brand: 'Brand Kit', opportunities: 'Advertising Opportunities',
};
const primary = {
  dashboard: ['Create Campaign', 'campaign'], campaigns: ['New Campaign', 'campaign'],
  advertising: ['Create Advert', 'advert'], content: ['Upload Content', 'content'],
  email: ['Create Email', 'email'], calendar: ['Add Activity', 'activity'],
  leads: ['New Lead', 'lead'], analytics: ['Add Metric', 'metric'], brand: ['Edit Brand Kit', 'brand'],
};
const resources = { campaign: 'campaigns', advert: 'adverts', content: 'content', activity: 'activities', lead: 'leads', contact: 'contacts', metric: 'metrics', brand: 'brand-kit' };
const collections = { campaign: 'campaigns', advert: 'adverts', content: 'content', activity: 'activities', lead: 'leads', contact: 'contacts', metric: 'metrics' };
const state = { canManage: API.config.canManage, providers: {}, summary: {}, analytics: { available: false }, calendar: [], campaigns: [], adverts: [], content: [], contacts: [], leads: [], activities: [], metrics: [], messages: [], brand: {} };
let currentRoute = 'dashboard';
let dialogTrigger = null;

function toast(message, error = false) {
  const item = document.createElement('div');
  item.className = `toast${error ? ' error' : ''}`;
  item.textContent = message;
  $('#toasts').append(item);
  window.setTimeout(() => item.remove(), 4500);
}

function showDialog(title, body) {
  dialogTrigger = document.activeElement;
  $('#dialogTitle').textContent = title;
  $('#dialogBody').innerHTML = body;
  if (!$('#marketingDialog').open) $('#marketingDialog').showModal();
}

function closeDialog() {
  $('#marketingDialog').close();
  $('#dialogBody').replaceChildren();
  if (dialogTrigger?.isConnected) dialogTrigger.focus();
}

function providerStrip() {
  const labels = { twilio_email: 'Email', twilio_sms: 'SMS', meta_whatsapp: 'WhatsApp', meta_facebook: 'Facebook', meta_instagram: 'Instagram' };
  $('#providerStatus').innerHTML = Object.entries(state.providers).map(([name, value]) => `<span class="provider-status ${Views.esc(value.state)}" title="${Views.esc(value.message)}">${Views.esc(labels[name])}: ${Views.esc(value.state.replaceAll('_', ' '))}</span>`).join('');
}

async function loadState() {
  const [summary, analytics, calendar, providers, campaigns, adverts, content, contacts, leads, activities, metrics, messages, brands] = await Promise.all([
    API.summary(), API.analytics(), API.calendar(), API.providers(), API.list('campaigns'), API.list('adverts'),
    API.list('content'), API.list('contacts?include_inactive=1').catch(() => API.list('contacts')), API.list('leads'),
    API.list('activities'), API.list('metrics'), API.list('outbound-messages'), API.list('brand-kit'),
  ]);
  Object.assign(state, { summary, analytics, calendar: calendar.results || [], providers, campaigns, adverts, content, contacts, leads, activities, metrics, messages, brand: brands[0] || {} });
  providerStrip();
}

function render() {
  currentRoute = location.hash.slice(1) || 'dashboard';
  if (!pages[currentRoute]) currentRoute = 'dashboard';
  $('#pageTitle').textContent = pages[currentRoute];
  document.title = `${pages[currentRoute]} · SME Business Suite`;
  document.querySelectorAll('[data-route]').forEach(link => {
    const active = link.dataset.route === currentRoute || (currentRoute === 'opportunities' && link.dataset.route === 'advertising');
    link.classList.toggle('active', active);
    if (active) link.setAttribute('aria-current', 'page'); else link.removeAttribute('aria-current');
  });
  const button = $('#primaryAction');
  const configured = primary[currentRoute];
  button.hidden = !state.canManage || !configured;
  if (configured) { button.textContent = `＋ ${configured[0]}`; button.dataset.kind = configured[1]; }
  const renderer = Views[currentRoute] || Views.dashboard;
  $('#content').innerHTML = currentRoute === 'analytics' ? renderer(state, Charts) : renderer(state);
}

function findItem(kind, id) {
  if (kind === 'brand') return state.brand;
  return state[collections[kind]]?.find(item => String(item.id) === String(id)) || {};
}

function openForm(kind, item = {}) {
  if (!state.canManage) return;
  const renderer = Forms[kind];
  if (!renderer) return;
  const names = { campaign: 'Campaign', advert: 'Advert', content: 'Content', email: 'Email', activity: 'Marketing Activity', lead: 'Lead', contact: 'Contact', metric: 'Marketing Metric', brand: 'Brand Kit' };
  showDialog(`${item.id ? 'Edit' : 'Create'} ${names[kind]}`, renderer(item, state));
}

function normalizeForm(form) {
  const formData = new FormData(form);
  if (form.dataset.form === 'content' || form.dataset.form === 'brand') {
    for (const [key, value] of [...formData.entries()]) if (value === '' || (value instanceof File && value.size === 0)) formData.delete(key);
    return formData;
  }
  const values = Object.fromEntries(formData.entries());
  for (const name of ['campaign', 'contact', 'advert', 'content', 'ends_at']) if (values[name] === '') values[name] = null;
  if (form.dataset.form === 'campaign') values.channels = formData.getAll('channels');
  if (form.dataset.form === 'contact') {
    for (const name of ['email_consent', 'sms_consent', 'whatsapp_consent']) values[name] = formData.has(name);
  }
  return values;
}

async function refresh(message = '') {
  $('#saveState').textContent = '· Refreshing data…';
  await loadState();
  render();
  $('#saveState').textContent = '· Connected to CRM data';
  if (message) toast(message);
}

document.addEventListener('click', async event => {
  const close = event.target.closest('[data-close-dialog]');
  if (close) { closeDialog(); return; }
  const target = event.target.closest('[data-action]');
  if (!target) return;
  const { action, id } = target.dataset;
  try {
    if (action === 'create') openForm(id || target.dataset.kind);
    if (action === 'navigate') location.hash = id;
    if (action === 'opportunities') location.hash = 'opportunities';
    if (action === 'edit') { const [kind, itemId] = id.split(':'); openForm(kind, findItem(kind, itemId)); }
    if (action === 'delete') {
      const [kind, itemId] = id.split(':');
      if (window.confirm('Delete this record? This cannot be undone.')) { await API.remove(resources[kind], itemId); await refresh('Record deleted.'); }
    }
    if (action === 'convert') { await API.action(`leads/${id}/convert-to-client/`); await refresh('Lead sent to CRM.'); }
    if (action === 'retry') { await API.action(`outbound-messages/${id}/retry/`); await refresh('Delivery retry requested.'); }
    if (action === 'cancel') { await API.action(`outbound-messages/${id}/cancel/`); await refresh('Scheduled delivery cancelled.'); }
  } catch (error) { toast(error.message, true); }
});

document.addEventListener('submit', async event => {
  const form = event.target.closest('form[data-form]');
  if (!form) return;
  event.preventDefault();
  const errorNode = form.querySelector('#formError');
  errorNode.textContent = '';
  if (!form.reportValidity()) return;
  try {
    const kind = form.dataset.form;
    const values = normalizeForm(form);
    if (kind === 'email') {
      const intent = event.submitter?.value || 'send';
      if (intent === 'schedule') {
        if (!values.scheduled_at) throw new Error('Choose a future date and time.');
        await API.action('workspace/schedule/', values);
      } else {
        delete values.scheduled_at;
        await API.action('workspace/send/', values);
      }
    } else {
      const resource = resources[kind];
      if (form.dataset.id) await API.update(resource, form.dataset.id, values);
      else await API.create(resource, values);
    }
    closeDialog();
    await refresh(kind === 'email' ? 'Email request saved.' : 'Changes saved.');
  } catch (error) { errorNode.textContent = error.message; }
});

document.addEventListener('click', event => {
  if (!event.target.closest('[data-preview-email]')) return;
  const form = event.target.closest('form');
  const data = Object.fromEntries(new FormData(form));
  showDialog('Email preview', `<article class="document-preview"><h2>${Views.esc(data.subject)}</h2><p>${Views.esc(data.body)}</p></article>`);
});

$('#primaryAction').addEventListener('click', event => openForm(event.currentTarget.dataset.kind));
$('#sidebarToggle').addEventListener('click', () => {
  const expanded = document.body.classList.toggle('sidebar-expanded');
  $('#sidebarToggle').setAttribute('aria-expanded', String(expanded));
});
$('#menuButton').addEventListener('click', () => {
  const open = $('#sidebar').classList.toggle('open');
  $('#menuButton').setAttribute('aria-expanded', String(open));
});
$('#marketingDialog').addEventListener('cancel', event => { event.preventDefault(); closeDialog(); });
window.addEventListener('hashchange', render);

loadState().then(render).catch(error => {
  $('#content').innerHTML = `<section class="panel error-state"><h2>Marketing data could not be loaded</h2><p>${Views.esc(error.message)}</p><button class="btn" onclick="location.reload()">Try again</button></section>`;
});
