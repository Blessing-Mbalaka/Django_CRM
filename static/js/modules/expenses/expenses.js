import { collection } from '../../api/client.js';
import { approveExpense, createCategory, createExpense, listCategories, listExpenses, rejectExpense, submitExpense } from '../../api/expenses-api.js';
import { escapeHtml, formatDate, formatMoney, setBusy, setFeedback } from '../ui.js';

const state = { expenses: [], categories: [], status: '' };
const rows = document.getElementById('expenseRows');

function badge(status) { return `<span class="suite-status status-${status}">${escapeHtml(status)}</span>`; }

function render() {
  document.getElementById('expenseTotal').textContent = `${formatMoney(state.expenses.reduce((sum, item) => sum + Number(item.amount), 0))} total`;
  if (!state.expenses.length) { rows.innerHTML = '<tr><td colspan="8" class="module-empty"><i class="bi bi-wallet2"></i><strong>No expenses found</strong><span>Capture a business cost or choose another status.</span></td></tr>'; return; }
  rows.innerHTML = state.expenses.map((item) => {
    const submit = ['draft', 'rejected'].includes(item.status) ? `<button class="table-action" data-submit="${item.id}"><i class="bi bi-send"></i> Submit</button>` : '';
    const decision = item.status === 'submitted' ? `<button class="icon-button text-success" data-approve="${item.id}" title="Approve"><i class="bi bi-check-lg"></i></button><button class="icon-button text-danger" data-reject="${item.id}" title="Reject"><i class="bi bi-x-lg"></i></button>` : '';
    return `<tr><td><strong>${escapeHtml(item.description)}</strong>${item.notes ? `<small class="d-block text-muted">${escapeHtml(item.notes)}</small>` : ''}</td><td>${escapeHtml(item.category_name)}</td><td>${formatDate(item.incurred_on)}</td><td class="fw-700 text-uj">${formatMoney(item.amount)}</td><td>${formatMoney(item.vat_amount)}</td><td class="text-capitalize">${escapeHtml(item.payment_method)}</td><td>${badge(item.status)}</td><td class="text-end text-nowrap">${submit}${decision}</td></tr>`;
  }).join('');
}

async function load() { try { state.expenses = collection(await listExpenses(state.status)); render(); } catch (error) { rows.innerHTML = '<tr><td colspan="8" class="module-empty text-danger">Unable to load expenses.</td></tr>'; setFeedback(error.message, 'danger'); } }
async function loadCategories() { try { state.categories = collection(await listCategories()); document.getElementById('expenseCategory').innerHTML = '<option value="">Choose a category</option>' + state.categories.filter((item) => item.is_active).map((item) => `<option value="${item.id}">${escapeHtml(item.name)}</option>`).join(''); } catch (error) { setFeedback(error.message, 'danger'); } }

document.querySelectorAll('[data-expense-status]').forEach((button) => button.addEventListener('click', async () => { document.querySelectorAll('[data-expense-status]').forEach((item) => item.classList.remove('active')); button.classList.add('active'); state.status = button.dataset.expenseStatus; await load(); }));
document.getElementById('newCategoryButton').addEventListener('click', async () => { const name = window.prompt('New expense category name'); if (!name?.trim()) return; try { await createCategory(name.trim()); await loadCategories(); setFeedback('Expense category created.', 'success'); } catch (error) { setFeedback(error.message, 'danger'); } });

document.getElementById('expenseForm').addEventListener('submit', async (event) => {
  event.preventDefault(); const button = document.getElementById('saveExpenseButton'); setBusy(button, true, 'Saving…');
  try { await createExpense({ description: document.getElementById('expenseDescription').value.trim(), category: Number(document.getElementById('expenseCategory').value), amount: document.getElementById('expenseAmount').value, vat_amount: document.getElementById('expenseVat').value, incurred_on: document.getElementById('expenseDate').value, payment_method: document.getElementById('expenseMethod').value, notes: document.getElementById('expenseNotes').value.trim() }); bootstrap.Modal.getOrCreateInstance(document.getElementById('expenseModal')).hide(); event.target.reset(); setDefaultDate(); setFeedback('Expense saved as draft.', 'success'); await load(); } catch (error) { setFeedback(error.message, 'danger'); } finally { setBusy(button, false); }
});

rows.addEventListener('click', async (event) => {
  const submit = event.target.closest('[data-submit]'); const approve = event.target.closest('[data-approve]'); const reject = event.target.closest('[data-reject]');
  try {
    if (submit) { await submitExpense(submit.dataset.submit); setFeedback('Expense submitted for approval.', 'success'); }
    else if (approve) { await approveExpense(approve.dataset.approve, 'Approved from expense register'); setFeedback('Expense approved.', 'success'); }
    else if (reject) { const reason = window.prompt('Reason for rejection'); if (reason === null) return; await rejectExpense(reject.dataset.reject, reason); setFeedback('Expense rejected.', 'success'); }
    else return;
    await load();
  } catch (error) { setFeedback(error.message, 'danger'); }
});

function setDefaultDate() { document.getElementById('expenseDate').value = new Date().toISOString().slice(0, 10); }
setDefaultDate(); loadCategories(); load();
