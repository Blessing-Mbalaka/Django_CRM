import { collection } from '../../api/client.js';
import { createBankStatement, listAccounts, listBankStatements, listReconciliationCandidates, reconcileBankLine, unreconcileBankLine } from '../../api/accounting-api.js';
import { escapeHtml, formatDate, formatMoney, setBusy, setFeedback } from '../ui.js';

const state = { accounts: [], statements: [], selectedId: null, candidates: new Map() };
const statementRows = document.getElementById('statementRows');
const lineRows = document.getElementById('statementLineRows');

function selectedStatement() { return state.statements.find((item) => item.id === state.selectedId); }

function renderStatements() {
  statementRows.innerHTML = state.statements.length ? state.statements.map((item) => `<tr class="clickable-row${item.id === state.selectedId ? ' is-selected' : ''}" data-statement-id="${item.id}"><td><strong>${escapeHtml(item.reference)}</strong></td><td>${escapeHtml(item.bank_account_name)}</td><td>${formatDate(item.start_date)} - ${formatDate(item.end_date)}</td><td>${formatMoney(item.closing_balance)}</td><td>${item.reconciled_count}/${item.statement_lines.length}</td><td><span class="suite-status status-${item.status === 'reconciled' ? 'approved' : 'draft'}">${escapeHtml(item.status)}</span></td></tr>`).join('') : '<tr><td colspan="6" class="module-empty"><i class="bi bi-bank"></i><strong>No bank statements</strong><span>Import a statement to begin reconciliation.</span></td></tr>';
}

function renderLines() {
  const statement = selectedStatement();
  const card = document.getElementById('statementLineCard');
  card.hidden = !statement;
  if (!statement) return;
  document.getElementById('statementLineTitle').textContent = `${statement.reference} transactions`;
  lineRows.innerHTML = statement.statement_lines.map((line) => {
    const candidate = state.candidates.get(line.id)?.[0];
    const match = line.is_reconciled ? `${formatDate(line.journal_date)} · ${escapeHtml(line.journal_reference || `Journal line #${line.matched_journal_line}`)}` : candidate ? `${formatDate(candidate.date)} · ${escapeHtml(candidate.reference || candidate.description)}` : '<span class="text-muted">No exact candidate</span>';
    const action = line.is_reconciled ? `<button class="table-action" data-unmatch-line="${line.id}"><i class="bi bi-x-circle"></i> Undo</button>` : candidate ? `<button class="table-action" data-match-line="${line.id}" data-journal-line="${candidate.id}"><i class="bi bi-link-45deg"></i> Match</button>` : '';
    return `<tr><td>${formatDate(line.transaction_date)}</td><td>${escapeHtml(line.description)}</td><td>${escapeHtml(line.reference || '-')}</td><td class="${Number(line.amount) < 0 ? 'text-danger' : 'text-success'} fw-700">${formatMoney(line.amount)}</td><td>${match}</td><td class="text-end">${action}</td></tr>`;
  }).join('');
}

async function loadCandidates(statement) {
  const unmatched = statement.statement_lines.filter((line) => !line.is_reconciled);
  const results = await Promise.all(unmatched.map(async (line) => [line.id, collection(await listReconciliationCandidates(line.id))]));
  state.candidates = new Map(results);
}

async function selectStatement(id) {
  state.selectedId = id;
  renderStatements();
  const statement = selectedStatement();
  await loadCandidates(statement);
  renderLines();
}

async function loadStatements(keepSelection = true) {
  state.statements = collection(await listBankStatements());
  if (!keepSelection || !state.statements.some((item) => item.id === state.selectedId)) state.selectedId = state.statements[0]?.id || null;
  renderStatements();
  if (selectedStatement()) await loadCandidates(selectedStatement());
  renderLines();
}

function parseTransactions(value) {
  const rows = value.split(/\r?\n/).filter((line) => line.trim());
  if (rows[0] && /^(transaction_)?date\s*,/i.test(rows[0].trim())) rows.shift();
  if (!rows.length) throw new Error('Choose a CSV statement file or paste at least one transaction.');
  return rows.map((line, index) => {
    const parts = []; let valuePart = ''; let quoted = false;
    for (let position = 0; position < line.length; position += 1) { const character = line[position]; if (character === '"' && line[position + 1] === '"' && quoted) { valuePart += '"'; position += 1; } else if (character === '"') quoted = !quoted; else if (character === ',' && !quoted) { parts.push(valuePart.trim()); valuePart = ''; } else valuePart += character; }
    parts.push(valuePart.trim());
    if (parts.length !== 4 || !parts[0] || !parts[1] || !parts[3]) throw new Error(`Transaction line ${index + 1} must contain date, description, reference and amount.`);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(parts[0])) throw new Error(`Transaction line ${index + 1} must use a YYYY-MM-DD date.`);
    if (Number.isNaN(Number(parts[3]))) throw new Error(`Transaction line ${index + 1} has an invalid amount.`);
    return { transaction_date: parts[0], description: parts[1], reference: parts[2], amount: parts[3] };
  });
}

statementRows.addEventListener('click', (event) => { const row = event.target.closest('[data-statement-id]'); if (row) selectStatement(Number(row.dataset.statementId)).catch((error) => setFeedback(error.message, 'danger')); });
lineRows.addEventListener('click', async (event) => { const match = event.target.closest('[data-match-line]'); const unmatch = event.target.closest('[data-unmatch-line]'); try { if (match) { await reconcileBankLine(match.dataset.matchLine, match.dataset.journalLine); setFeedback('Bank transaction reconciled.', 'success'); } else if (unmatch) { await unreconcileBankLine(unmatch.dataset.unmatchLine); setFeedback('Reconciliation removed.', 'success'); } else return; await loadStatements(); } catch (error) { setFeedback(error.message, 'danger'); } });

document.getElementById('statementForm').addEventListener('submit', async (event) => {
  event.preventDefault(); const button = document.getElementById('saveStatementButton'); setBusy(button, true, 'Importing...');
  try {
    const statement = await createBankStatement({ bank_account: Number(document.getElementById('statementAccount').value), reference: document.getElementById('statementReference').value.trim(), start_date: document.getElementById('statementStart').value, end_date: document.getElementById('statementEnd').value, opening_balance: document.getElementById('statementOpening').value, closing_balance: document.getElementById('statementClosing').value, lines: parseTransactions(document.getElementById('statementTransactions').value) });
    state.selectedId = statement.id; bootstrap.Modal.getOrCreateInstance(document.getElementById('statementModal')).hide(); event.target.reset(); setStatementDates(); setFeedback('Bank statement imported.', 'success'); await loadStatements();
  } catch (error) { setFeedback(error.message, 'danger'); } finally { setBusy(button, false); }
});
document.getElementById('statementFile').addEventListener('change', async (event) => { const file = event.target.files[0]; if (!file) return; try { document.getElementById('statementTransactions').value = await file.text(); setFeedback('CSV loaded. Review the preview and balances before importing.', 'success'); } catch (error) { setFeedback(`Unable to read CSV: ${error.message}`, 'danger'); } });

function setStatementDates() { const today = new Date(); const month = String(today.getMonth() + 1).padStart(2, '0'); document.getElementById('statementEnd').value = today.toISOString().slice(0, 10); document.getElementById('statementStart').value = `${today.getFullYear()}-${month}-01`; document.getElementById('statementOpening').value = '0.00'; }

async function initialise() {
  try { state.accounts = collection(await listAccounts()); const bankAccounts = state.accounts.filter((item) => item.is_active && item.system_role === 'bank'); document.getElementById('statementAccount').innerHTML = '<option value="">Choose bank account</option>' + bankAccounts.map((item) => `<option value="${item.id}">${escapeHtml(item.code)} - ${escapeHtml(item.name)}</option>`).join(''); document.getElementById('statementSetupWarning').hidden = bankAccounts.length > 0; document.getElementById('saveStatementButton').disabled = bankAccounts.length === 0; await loadStatements(false); } catch (error) { setFeedback(error.message, 'danger'); }
}

setStatementDates(); initialise();
