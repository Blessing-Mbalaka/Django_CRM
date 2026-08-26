import { getBalanceSheet, getIncomeStatement, getTrialBalance } from '../../api/accounting-api.js';
import { escapeHtml, formatMoney, setBusy, setFeedback } from '../ui.js';

const startInput = document.getElementById('reportStart');
const endInput = document.getElementById('reportEnd');
const runButton = document.getElementById('runReportsButton');

function reportRows(rows, amountKey = 'amount') {
  return rows.length ? rows.map((row) => `<div class="report-line"><span>${row.code ? `<code>${escapeHtml(row.code)}</code> ` : ''}${escapeHtml(row.name)}</span><strong>${formatMoney(row[amountKey])}</strong></div>`).join('') : '<div class="report-empty">No activity in this period.</div>';
}

function totalRow(label, amount) { return `<div class="report-line report-total"><span>${escapeHtml(label)}</span><strong>${formatMoney(amount)}</strong></div>`; }

function renderIncome(report) {
  document.getElementById('reportRevenue').textContent = formatMoney(report.total_revenue);
  document.getElementById('reportExpenses').textContent = formatMoney(report.total_expenses);
  document.getElementById('reportProfit').textContent = formatMoney(report.net_profit);
  document.getElementById('incomeStatement').innerHTML = '<h3>Revenue</h3>' + reportRows(report.revenue) + totalRow('Total revenue', report.total_revenue) + '<h3>Expenses</h3>' + reportRows(report.expenses) + totalRow('Total expenses', report.total_expenses) + totalRow('Net profit', report.net_profit);
}

function renderBalance(report) {
  document.getElementById('balanceStatus').innerHTML = report.is_balanced ? '<span class="suite-status status-approved">Balanced</span>' : '<span class="suite-status status-rejected">Out of balance</span>';
  document.getElementById('balanceSheet').innerHTML = '<h3>Assets</h3>' + reportRows(report.assets) + totalRow('Total assets', report.total_assets) + '<h3>Liabilities</h3>' + reportRows(report.liabilities) + totalRow('Total liabilities', report.total_liabilities) + '<h3>Equity</h3>' + reportRows(report.equity) + totalRow('Total equity', report.total_equity);
}

function renderTrial(report) {
  document.getElementById('trialStatus').innerHTML = report.is_balanced ? '<span class="suite-status status-approved">Balanced</span>' : '<span class="suite-status status-rejected">Out of balance</span>';
  document.getElementById('trialBalance').innerHTML = report.rows.length ? report.rows.map((row) => `<div class="report-line"><span><code>${escapeHtml(row.code)}</code> ${escapeHtml(row.name)}</span><span class="trial-amounts"><strong>${formatMoney(row.debit)}</strong><strong>${formatMoney(row.credit)}</strong></span></div>`).join('') + `<div class="report-line report-total"><span>Total</span><span class="trial-amounts"><strong>${formatMoney(report.total_debit)}</strong><strong>${formatMoney(report.total_credit)}</strong></span></div>` : '<div class="report-empty">No posted ledger activity.</div>';
}

async function loadReports() {
  setBusy(runButton, true, 'Running...');
  try {
    const [trial, income, balance] = await Promise.all([getTrialBalance(endInput.value), getIncomeStatement(startInput.value, endInput.value), getBalanceSheet(endInput.value)]);
    renderTrial(trial); renderIncome(income); renderBalance(balance);
  } catch (error) { setFeedback(error.message, 'danger'); }
  finally { setBusy(runButton, false); }
}

const today = new Date();
endInput.value = today.toISOString().slice(0, 10);
startInput.value = `${today.getFullYear()}-01-01`;
runButton.addEventListener('click', loadReports);
loadReports();
