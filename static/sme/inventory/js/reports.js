import {esc, table, money, qty} from './views.js';

export const reportNames = ['Current Stock Summary', 'Inventory Value', 'Low Stock Report', 'Out of Stock Report', 'Stock Movement Summary', 'Products by Category'];

export function reportView(dataset, selected, currency) {
  if (!dataset) return '<section class="panel"><p>Loading report…</p></section>';
  const tabs = reportNames.map(name => `<button class="btn secondary small ${name === selected ? 'active' : ''}" data-action="select-report" data-name="${esc(name)}">${esc(name)}</button>`).join('');
  const rows = dataset.rows.map(row => `<tr>${row.map(value => `<td>${esc(value)}</td>`).join('')}</tr>`).join('');
  const s = dataset.summary;
  return `<div class="page-heading"><div><h2>Inventory reports</h2><p>Live database reports in ${esc(currency)}.</p></div><div class="actions"><button class="btn secondary" data-action="export-report">Export CSV</button><button class="btn" data-action="print-report">Print Report</button></div></div>
    <div class="report-tabs no-print">${tabs}</div>
    <div class="stats"><article class="stat"><div class="stat-label">Active Products</div><strong>${qty(s.products)}</strong></article><article class="stat"><div class="stat-label">Aggregate Quantity</div><strong>${qty(s.aggregate_quantity)}</strong></article><article class="stat"><div class="stat-label">Inventory Value</div><strong>${money(s.inventory_value, currency)}</strong></article><article class="stat"><div class="stat-label">Low / Out</div><strong>${s.low_stock} / ${s.out_of_stock}</strong></article></div>
    <section class="panel"><div class="panel-header"><h2>${esc(dataset.name)}</h2></div>${table(dataset.headers, rows)}</section>`;
}
