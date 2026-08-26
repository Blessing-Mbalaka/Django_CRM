import { collection } from '../../api/client.js';
import { createProduct, listProducts } from '../../api/products-api.js';
import { escapeHtml, formatMoney, setBusy, setFeedback } from '../ui.js';

const state = { products: [], type: '', query: '' };
const rows = document.getElementById('productRows');

function render() {
  const items = state.products.filter((item) => (!state.type || item.product_type === state.type) && `${item.sku} ${item.name}`.toLowerCase().includes(state.query));
  document.getElementById('productCount').textContent = state.products.length;
  document.getElementById('stockProductCount').textContent = state.products.filter((item) => item.product_type === 'stock').length;
  document.getElementById('serviceProductCount').textContent = state.products.filter((item) => item.product_type === 'service').length;
  if (!items.length) { rows.innerHTML = '<tr><td colspan="7" class="module-empty"><i class="bi bi-box-seam"></i><strong>No catalogue items</strong><span>Create a product or service to begin.</span></td></tr>'; return; }
  rows.innerHTML = items.map((item) => `<tr><td><code>${escapeHtml(item.sku)}</code></td><td><strong>${escapeHtml(item.name)}</strong>${item.description ? `<small class="d-block text-muted">${escapeHtml(item.description)}</small>` : ''}</td><td><span class="suite-status status-${item.product_type === 'stock' ? 'issued' : 'approved'}">${escapeHtml(item.product_type)}</span></td><td class="fw-700 text-uj">${formatMoney(item.sales_price)}</td><td>${formatMoney(item.cost_price)}</td><td>${escapeHtml(item.tax_rate)}%</td><td>${item.is_active ? '<span class="suite-status status-approved">Active</span>' : '<span class="suite-status status-draft">Inactive</span>'}</td></tr>`).join('');
}

async function load() { try { state.products = collection(await listProducts()); render(); } catch (error) { setFeedback(error.message, 'danger'); } }
document.getElementById('productSearch').addEventListener('input', (event) => { state.query = event.target.value.trim().toLowerCase(); render(); });
document.querySelectorAll('[data-product-type]').forEach((button) => button.addEventListener('click', () => { document.querySelectorAll('[data-product-type]').forEach((item) => item.classList.remove('active')); button.classList.add('active'); state.type = button.dataset.productType; render(); }));
document.getElementById('productForm').addEventListener('submit', async (event) => { event.preventDefault(); const button = document.getElementById('saveProductButton'); setBusy(button, true, 'Saving…'); try { await createProduct({ sku: document.getElementById('productSku').value.trim().toUpperCase(), name: document.getElementById('productName').value.trim(), product_type: document.getElementById('productType').value, tax_rate: document.getElementById('productTax').value, sales_price: document.getElementById('productSalesPrice').value, cost_price: document.getElementById('productCostPrice').value, description: document.getElementById('productDescription').value.trim(), is_active: true }); bootstrap.Modal.getOrCreateInstance(document.getElementById('productModal')).hide(); event.target.reset(); setFeedback('Catalogue item created.', 'success'); await load(); } catch (error) { setFeedback(error.message, 'danger'); } finally { setBusy(button, false); } });
load();

