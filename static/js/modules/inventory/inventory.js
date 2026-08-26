import { collection } from '../../api/client.js';
import { listProducts } from '../../api/products-api.js';
import { createLocation, createMovement, listLocations, listMovements } from '../../api/inventory-api.js';
import { escapeHtml, formatDate, formatMoney, setBusy, setFeedback } from '../ui.js';

const state = { products: [], locations: [], movements: [] };
const rows = document.getElementById('movementRows');
const productFilter = document.getElementById('inventoryProductFilter');
const locationFilter = document.getElementById('inventoryLocationFilter');

function render() {
  document.getElementById('locationCount').textContent = state.locations.length;
  document.getElementById('movementCount').textContent = state.movements.length;
  document.getElementById('stockUnitBalance').textContent = state.movements.reduce((sum, item) => sum + Number(item.signed_quantity), 0).toFixed(3).replace(/\.000$/, '');
  document.getElementById('inventoryRecordCount').textContent = `${state.movements.length} records`;
  if (!state.movements.length) { rows.innerHTML = '<tr><td colspan="7" class="module-empty"><i class="bi bi-boxes"></i><strong>No stock movements</strong><span>Record an opening receipt or adjustment.</span></td></tr>'; return; }
  rows.innerHTML = state.movements.map((item) => `<tr><td>${formatDate(item.occurred_on)}</td><td><strong>${escapeHtml(item.product_name)}</strong></td><td>${escapeHtml(item.location_name)}</td><td><span class="movement-type movement-${item.movement_type}">${escapeHtml(item.movement_type.replace('_', ' '))}</span></td><td class="fw-700 ${Number(item.signed_quantity) < 0 ? 'text-danger' : 'text-success'}">${Number(item.signed_quantity) > 0 ? '+' : ''}${escapeHtml(item.signed_quantity)}</td><td>${formatMoney(item.unit_cost)}</td><td>${escapeHtml(item.reference || '—')}</td></tr>`).join('');
}

function setOptions() {
  const products = state.products.filter((item) => item.product_type === 'stock');
  const productOptions = products.map((item) => `<option value="${item.id}">${escapeHtml(item.sku)} · ${escapeHtml(item.name)}</option>`).join('');
  const locationOptions = state.locations.map((item) => `<option value="${item.id}">${escapeHtml(item.name)}</option>`).join('');
  document.getElementById('movementProduct').innerHTML = `<option value="">Choose product</option>${productOptions}`;
  document.getElementById('movementLocation').innerHTML = `<option value="">Choose location</option>${locationOptions}`;
  productFilter.innerHTML = `<option value="">All products</option>${productOptions}`;
  locationFilter.innerHTML = `<option value="">All locations</option>${locationOptions}`;
}

async function loadReferenceData() { const [products, locations] = await Promise.all([listProducts('stock'), listLocations()]); state.products = collection(products); state.locations = collection(locations); setOptions(); }
async function loadMovements() { try { state.movements = collection(await listMovements({ product: productFilter.value, location: locationFilter.value })); render(); } catch (error) { setFeedback(error.message, 'danger'); } }
productFilter.addEventListener('change', loadMovements); locationFilter.addEventListener('change', loadMovements);
document.getElementById('newLocationButton').addEventListener('click', async () => { const name = window.prompt('Location name'); if (!name?.trim()) return; const code = window.prompt('Short location code', name.trim().slice(0, 6).toUpperCase()); if (!code?.trim()) return; try { await createLocation({ name: name.trim(), code: code.trim().toUpperCase(), is_active: true }); await loadReferenceData(); setFeedback('Stock location created.', 'success'); } catch (error) { setFeedback(error.message, 'danger'); } });
document.getElementById('movementForm').addEventListener('submit', async (event) => { event.preventDefault(); const button = document.getElementById('saveMovementButton'); setBusy(button, true, 'Recording…'); try { await createMovement({ product: Number(document.getElementById('movementProduct').value), location: Number(document.getElementById('movementLocation').value), movement_type: document.getElementById('movementType').value, quantity: document.getElementById('movementQuantity').value, occurred_on: document.getElementById('movementDate').value, unit_cost: document.getElementById('movementCost').value, reference: document.getElementById('movementReference').value.trim() }); bootstrap.Modal.getOrCreateInstance(document.getElementById('movementModal')).hide(); event.target.reset(); setToday(); setFeedback('Stock movement recorded.', 'success'); await loadMovements(); } catch (error) { setFeedback(error.message, 'danger'); } finally { setBusy(button, false); } });
function setToday() { document.getElementById('movementDate').value = new Date().toISOString().slice(0, 10); }
setToday();
try { await loadReferenceData(); await loadMovements(); } catch (error) { setFeedback(error.message, 'danger'); }
