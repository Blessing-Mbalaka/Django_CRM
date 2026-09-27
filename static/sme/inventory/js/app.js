import * as API from './api.js';
import * as View from './views.js';
import {reportNames, reportView} from './reports.js';

const {config} = API;
const routes = ['dashboard','products','categories','in','out','suppliers','history','low','reports','settings'];
const titles = {dashboard:'Dashboard',products:'Products',categories:'Categories',in:'Stock In',out:'Stock Out',suppliers:'Suppliers',history:'Stock History',low:'Low Stock',reports:'Reports',settings:'Settings'};
const state = {canManage: config.user.can_manage, banner: '/static/sme/assets/inventory-banner.png', summary: null, products: [], records: [], categories: [], suppliers: [], locations: [], movements: [], settings: {}, reportName: reportNames[0], report: null};
const content = document.getElementById('content');
const modal = document.getElementById('modal');
const modalTitle = document.getElementById('modalTitle');
const modalBody = document.getElementById('modalBody');
const statusBox = document.getElementById('workspaceStatus');

function route() { const value = location.hash.slice(1).split('/')[0]; return routes.includes(value) ? value : 'dashboard'; }
function detail(message, fallback = 'Something went wrong.') { return message?.data ? Object.values(message.data).flat().join(' ') : message?.message || fallback; }
function notify(message, error = false) { statusBox.textContent = message; statusBox.classList.toggle('error', error); statusBox.hidden = false; clearTimeout(notify.timer); notify.timer = setTimeout(() => { statusBox.hidden = true; }, 5000); }
function openModal(title, html) { modalTitle.textContent = title; modalBody.innerHTML = html; modal.showModal(); modalBody.querySelector('input,select,textarea')?.focus(); }
function closeModal() { modal.close(); modalBody.innerHTML = ''; }
function formData(form) { const data = Object.fromEntries(new FormData(form)); for (const key of ['category','preferred_supplier','location']) if (data[key] === '') data[key] = null; return data; }
function formError(form, error) { const box = form.querySelector('.error'); box.textContent = detail(error); box.scrollIntoView({behavior:'smooth', block:'nearest'}); }

async function load() {
  const [summary, products, records, categories, suppliers, locations, movements, settings] = await Promise.all([
    API.request(config.urls.summary), API.request(config.urls.stock_rows), API.get(config.urls.products), API.get(config.urls.categories),
    API.get(config.urls.suppliers), API.get(config.urls.locations), API.get(config.urls.movements), API.get(config.urls.settings),
  ]);
  Object.assign(state, {summary, products, records, categories, suppliers, locations, movements, settings: settings[0]});
  document.getElementById('businessName').textContent = state.settings.business_name;
  document.getElementById('businessInitials').textContent = state.settings.business_name.split(/\s+/).slice(0,2).map(word => word[0]).join('').toUpperCase();
}

async function refresh(message = '') {
  await load();
  await render();
  if (message) notify(message);
}

function topAction(current) {
  if (!state.canManage) return '';
  const actions = {products:['＋ Add Product','add-product'], categories:['＋ Add Category','add-category'], suppliers:['＋ Add Supplier','add-supplier'], dashboard:['＋ Add Product','add-product']};
  const action = actions[current];
  return action ? `<button class="btn" data-action="${action[1]}">${action[0]}</button>` : '';
}

async function render() {
  const current = route();
  document.body.classList.toggle('dashboard-page', current === 'dashboard');
  document.getElementById('pageTitle').textContent = titles[current];
  document.getElementById('pageActions').innerHTML = topAction(current);
  document.querySelectorAll('[data-route]').forEach(button => button.classList.toggle('active', button.dataset.route === current));
  if (current === 'dashboard') content.innerHTML = View.dashboard(state);
  if (current === 'products') content.innerHTML = View.products(state);
  if (current === 'categories') content.innerHTML = View.categories(state);
  if (current === 'in' || current === 'out') content.innerHTML = View.movementPage(state, current);
  if (current === 'suppliers') content.innerHTML = View.suppliers(state);
  if (current === 'history') content.innerHTML = View.history(state);
  if (current === 'low') content.innerHTML = View.lowStock(state);
  if (current === 'settings') content.innerHTML = View.settings(state);
  if (current === 'reports') {
    state.report = await API.request(`${config.urls.reports}?name=${encodeURIComponent(state.reportName)}`);
    content.innerHTML = reportView(state.report, state.reportName, state.settings.currency);
  }
  content.focus({preventScroll:true});
}

function recordById(records, id) { return records.find(record => String(record.id) === String(id)); }
function showProduct(id) {
  const product = recordById(state.products, id);
  openModal(product.name, `<div class="detail-grid"><div><span>SKU</span><strong>${View.esc(product.sku)}</strong></div><div><span>Stock</span><strong>${View.qty(product.quantity)} ${View.esc(product.unit)}</strong></div><div><span>Status</span><strong>${View.esc(product.status)}</strong></div><div><span>Supplier</span><strong>${View.esc(product.supplier_name)}</strong></div></div>`);
}

document.addEventListener('click', async event => {
  const nav = event.target.closest('[data-route]');
  if (nav) { location.hash = nav.dataset.route; document.getElementById('sidebar').classList.remove('mobile-open'); return; }
  const button = event.target.closest('[data-action]');
  if (!button) return;
  const {action, id} = button.dataset;
  try {
    if (action === 'close-modal') return closeModal();
    if (action === 'add-product') return openModal('Add Product', View.productForm(state));
    if (action === 'edit-product') return openModal('Edit Product', View.productForm(state, recordById(state.records, id)));
    if (action === 'view-product') return showProduct(id);
    if (action === 'add-category') return openModal('Add Category', View.categoryForm());
    if (action === 'edit-category') return openModal('Edit Category', View.categoryForm(recordById(state.categories, id)));
    if (action === 'add-supplier') return openModal('Add Supplier', View.supplierForm());
    if (action === 'edit-supplier') return openModal('Edit Supplier', View.supplierForm(recordById(state.suppliers, id)));
    if (action === 'stock-in' || action === 'adjust') return openModal(action === 'stock-in' ? 'Receive Stock' : 'Adjust Stock', View.movementForm(state, 'in', id));
    if (action === 'archive-product' && confirm('Archive this product? Its movement history will remain available.')) { await API.create(API.itemUrl(config.urls.products, id, 'archive/'), {}); return refresh('Product archived.'); }
    if (action === 'delete-category' && confirm('Remove this category? Assigned categories will be deactivated.')) { await API.remove(API.itemUrl(config.urls.categories, id)); return refresh('Category updated.'); }
    if (action === 'delete-supplier' && confirm('Deactivate this supplier?')) { await API.update(API.itemUrl(config.urls.suppliers, id), {is_active:false}); return refresh('Supplier deactivated.'); }
    if (action === 'select-report') { state.reportName = button.dataset.name; return render(); }
    if (action === 'print-report') return window.print();
    if (action === 'export-report') return API.download(`${config.urls.report_csv}?name=${encodeURIComponent(state.reportName)}`, 'inventory-report.csv');
    if (action === 'backup') { await API.download(config.urls.backup, 'inventory-backup.json'); return notify('Backup downloaded.'); }
    if (action === 'clear-data') {
      const confirmation = prompt('Type CLEAR INVENTORY DATA to remove inventory movements, rules, profiles and categories.');
      if (confirmation === null) return;
      await API.create(config.urls.clear_data, {confirmation});
      location.hash = 'dashboard'; return refresh('Inventory data cleared. Shared products and purchasing records were preserved.');
    }
  } catch (error) { notify(detail(error), true); }
});

document.addEventListener('submit', async event => {
  const form = event.target.closest('[data-form]');
  if (!form) return;
  event.preventDefault();
  const data = formData(form);
  try {
    if (form.dataset.form === 'product') {
      const id = form.dataset.id;
      if (!Number(data.opening_quantity || 0)) { delete data.opening_quantity; delete data.location; }
      await (id ? API.update(API.itemUrl(config.urls.products, id), data) : API.create(config.urls.products, data));
      closeModal(); return refresh(id ? 'Product updated.' : 'Product added.');
    }
    if (form.dataset.form === 'category') {
      const id = form.dataset.id;
      await (id ? API.update(API.itemUrl(config.urls.categories, id), data) : API.create(config.urls.categories, data));
      closeModal(); return refresh(id ? 'Category updated.' : 'Category added.');
    }
    if (form.dataset.form === 'supplier') {
      const id = form.dataset.id;
      await (id ? API.update(API.itemUrl(config.urls.suppliers, id), data) : API.create(config.urls.suppliers, data));
      closeModal(); return refresh(id ? 'Supplier updated.' : 'Supplier added.');
    }
    if (form.dataset.form === 'movement') {
      await API.create(config.urls.movements, data);
      if (modal.open) closeModal();
      return refresh(data.movement_type === 'receipt' ? 'Stock received.' : 'Stock removed.');
    }
    if (form.dataset.form === 'settings') {
      data.low_stock_alerts = form.elements.low_stock_alerts.checked;
      state.settings = await API.update(API.itemUrl(config.urls.settings, state.settings.id), data);
      return refresh('Settings saved.');
    }
  } catch (error) { formError(form, error); }
});

document.addEventListener('input', event => {
  if (event.target.id === 'productSearch') {
    const query = event.target.value.toLowerCase();
    document.querySelectorAll('#productResults tbody tr').forEach(row => { row.hidden = !row.textContent.toLowerCase().includes(query); });
  }
  if (event.target.id === 'historySearch') {
    const query = event.target.value.toLowerCase();
    document.querySelectorAll('#historyResults tbody tr').forEach(row => { row.hidden = !row.textContent.toLowerCase().includes(query); });
  }
});

document.addEventListener('change', async event => {
  if (event.target.id === 'historyType') {
    const query = event.target.value ? `?movement_type=${encodeURIComponent(event.target.value)}` : '';
    state.movements = await API.get(config.urls.movements + query);
    await render();
  }
});

document.getElementById('sidebarToggle').addEventListener('click', () => {
  const sidebar = document.getElementById('sidebar');
  sidebar.classList.toggle('expanded');
  document.getElementById('sidebarToggle').setAttribute('aria-expanded', sidebar.classList.contains('expanded'));
});
document.getElementById('menuButton').addEventListener('click', () => document.getElementById('sidebar').classList.toggle('mobile-open'));
window.addEventListener('hashchange', render);

(async () => {
  try { await load(); if (!location.hash) location.hash = 'dashboard'; else await render(); }
  catch (error) { content.innerHTML = `<section class="panel"><div class="empty"><strong>Inventory could not be loaded</strong><p>${View.esc(detail(error))}</p><button class="btn" onclick="location.reload()">Try again</button></div></section>`; }
})();
