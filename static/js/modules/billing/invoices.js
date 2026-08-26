import { collection } from '../../api/client.js';
import { addInvoiceLine, createInvoice, issueInvoice, listClients, listInvoices, recordPayment } from '../../api/billing-api.js';
import { escapeHtml, formatDate, formatMoney, setBusy, setFeedback } from '../ui.js';

const state = { invoices: [], clients: [], query: '' };
const rows = document.getElementById('invoiceRows');

function statusBadge(status) {
  const labels = { draft: 'Draft', issued: 'Issued', part_paid: 'Part paid', paid: 'Paid', void: 'Void' };
  return `<span class="suite-status status-${status}">${labels[status] || escapeHtml(status)}</span>`;
}

function render() {
  const items = state.invoices.filter((item) => `${item.number || ''} ${item.client_name}`.toLowerCase().includes(state.query));
  document.getElementById('invoiceCount').textContent = `${items.length} ${items.length === 1 ? 'record' : 'records'}`;
  document.getElementById('invoiceTotalCount').textContent = state.invoices.length;
  document.getElementById('invoiceOutstanding').textContent = formatMoney(state.invoices.reduce((sum, item) => sum + Number(item.balance_due), 0));
  document.getElementById('invoicePaid').textContent = formatMoney(state.invoices.reduce((sum, item) => sum + Number(item.amount_paid), 0));
  document.getElementById('invoiceDrafts').textContent = state.invoices.filter((item) => item.status === 'draft').length;
  if (!items.length) { rows.innerHTML = '<tr><td colspan="8" class="module-empty"><i class="bi bi-receipt"></i><strong>No invoices found</strong><span>Create a draft invoice to begin billing.</span></td></tr>'; return; }
  rows.innerHTML = items.map((item) => {
    const issueButton = item.status === 'draft' ? `<button class="table-action" data-issue="${item.id}"><i class="bi bi-send"></i> Issue</button>` : '';
    const paymentButton = ['issued', 'part_paid'].includes(item.status) ? `<button class="table-action" data-payment="${item.id}"><i class="bi bi-cash"></i> Payment</button>` : '';
    return `<tr><td><strong>${escapeHtml(item.number || `Draft #${item.id}`)}</strong></td><td>${escapeHtml(item.client_name)}</td><td>${formatDate(item.issue_date)}</td><td>${formatDate(item.due_date)}</td><td class="fw-700">${formatMoney(item.total, item.currency)}</td><td class="fw-700 text-uj">${formatMoney(item.balance_due, item.currency)}</td><td>${statusBadge(item.status)}</td><td class="text-end text-nowrap">${issueButton}${paymentButton}</td></tr>`;
  }).join('');
}

async function load() {
  try { state.invoices = collection(await listInvoices()); render(); } catch (error) { rows.innerHTML = '<tr><td colspan="8" class="module-empty text-danger">Unable to load invoices.</td></tr>'; setFeedback(error.message, 'danger'); }
}

async function loadClients() {
  try { state.clients = collection(await listClients()); document.getElementById('invoiceClient').innerHTML = '<option value="">Choose a customer</option>' + state.clients.map((client) => `<option value="${client.id}">${escapeHtml(client.name)}</option>`).join(''); } catch (error) { setFeedback(`Customers: ${error.message}`, 'danger'); }
}

document.getElementById('invoiceSearch').addEventListener('input', (event) => { state.query = event.target.value.trim().toLowerCase(); render(); });
document.getElementById('invoiceForm').addEventListener('submit', async (event) => {
  event.preventDefault(); const button = document.getElementById('saveInvoiceButton'); setBusy(button, true, 'Saving…');
  try {
    const invoice = await createInvoice({ client: Number(document.getElementById('invoiceClient').value), due_date: document.getElementById('invoiceDueDate').value, notes: document.getElementById('invoiceNotes').value.trim() });
    await addInvoiceLine({ invoice: invoice.id, description: document.getElementById('lineDescription').value.trim(), quantity: document.getElementById('lineQuantity').value, unit_price: document.getElementById('linePrice').value, tax_rate: document.getElementById('lineTax').value });
    bootstrap.Modal.getOrCreateInstance(document.getElementById('invoiceModal')).hide(); event.target.reset(); setDefaultDates(); setFeedback('Draft invoice created.', 'success'); await load();
  } catch (error) { setFeedback(error.message, 'danger'); } finally { setBusy(button, false); }
});

rows.addEventListener('click', async (event) => {
  const issueButton = event.target.closest('[data-issue]'); const paymentButton = event.target.closest('[data-payment]');
  if (issueButton) {
    try { await issueInvoice(issueButton.dataset.issue); setFeedback('Invoice issued and number allocated.', 'success'); await load(); } catch (error) { setFeedback(error.message, 'danger'); }
  }
  if (paymentButton) {
    const invoice = state.invoices.find((item) => item.id === Number(paymentButton.dataset.payment));
    document.getElementById('paymentInvoice').value = invoice.id; document.getElementById('paymentAmount').value = invoice.balance_due; document.getElementById('paymentAmount').max = invoice.balance_due; document.getElementById('paymentContext').textContent = `${invoice.number} · ${invoice.client_name} · ${formatMoney(invoice.balance_due)} outstanding`;
    bootstrap.Modal.getOrCreateInstance(document.getElementById('paymentModal')).show();
  }
});

document.getElementById('paymentForm').addEventListener('submit', async (event) => {
  event.preventDefault(); const button = document.getElementById('recordPaymentButton'); setBusy(button, true, 'Recording…');
  try { await recordPayment({ invoice: Number(document.getElementById('paymentInvoice').value), amount: document.getElementById('paymentAmount').value, paid_on: document.getElementById('paymentDate').value, reference: document.getElementById('paymentReference').value.trim() }); bootstrap.Modal.getOrCreateInstance(document.getElementById('paymentModal')).hide(); event.target.reset(); setDefaultDates(); setFeedback('Payment recorded.', 'success'); await load(); } catch (error) { setFeedback(error.message, 'danger'); } finally { setBusy(button, false); }
});

function setDefaultDates() { const today = new Date(); const due = new Date(); due.setDate(today.getDate() + 14); document.getElementById('invoiceDueDate').value = due.toISOString().slice(0, 10); document.getElementById('paymentDate').value = today.toISOString().slice(0, 10); }
setDefaultDates(); loadClients(); load();

