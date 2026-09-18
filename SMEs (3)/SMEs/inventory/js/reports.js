(function(A) {
  'use strict';
  const names = ['Current Stock Summary', 'Inventory Value', 'Low Stock Report', 'Out of Stock Report', 'Stock Movement Summary', 'Products by Category'];

  function data(name) {
    const ps = A.Domain.active(),
      U = A.UI;
    if (name === 'Stock Movement Summary') return {
      headers: ['Movement', 'Transactions', 'Units In', 'Units Out'],
      rows: ['Stock In', 'Stock Out', 'Adjustment'].map(type => {
        const ts = A.state.stockTransactions.filter(t => t.type === type);
        return [type, ts.length, ts.filter(t => t.direction === 'in').reduce((n, t) => n + t.quantity, 0), ts.filter(t => t.direction === 'out').reduce((n, t) => n + t.quantity, 0)];
      })
    };
    if (name === 'Products by Category') return {
      headers: ['Category', 'Products', 'Units', 'Value (' + A.state.settings.currency + ')'],
      rows: A.state.categories.map(c => {
        const items = ps.filter(p => p.category === c.id);
        return [c.name, items.length, items.reduce((n, p) => n + p.quantity, 0), items.reduce((n, p) => n + p.quantity * p.cost, 0).toFixed(2)];
      })
    };
    const filtered = name === 'Low Stock Report' ? ps.filter(p => A.Domain.status(p) === 'Low Stock') : name === 'Out of Stock Report' ? ps.filter(p => p.quantity === 0) : ps;
    return {
      headers: ['Product', 'SKU', 'Category', 'Quantity', 'Unit', 'Minimum', 'Status', 'Cost (' + A.state.settings.currency + ')', 'Inventory Value (' + A.state.settings.currency + ')', 'Supplier'],
      rows: filtered.map(p => [p.name, p.sku, U.category(p.category), p.quantity, p.unit, p.minimum, A.Domain.status(p), p.cost.toFixed(2), (p.quantity * p.cost).toFixed(2), U.supplier(p.supplier)])
    };
  }

  function render() {
    const U = A.UI,
      report = A.report,
      s = A.Domain.summary(),
      d = data(report);
    const cats = data('Products by Category'),
      max = Math.max(1, ...cats.rows.map(r => r[1]));
    return `<div class="page-heading"><div><h2>Inventory reports</h2><p>${U.esc(A.state.settings.businessName)} · ${U.esc(new Date().toLocaleDateString('en-ZA'))}</p></div><div class="actions">${U.button('Export CSV','export-report')}${U.button('Print Report','print-report')}</div></div><div class="report-tabs no-print">${names.map(n=>U.button(n,'select-report',n,'secondary small '+(n===report?'active':''))).join('')}</div><div class="stats"><article class="stat"><div class="stat-label">Active Products</div><strong>${U.qty(s.products)}</strong></article><article class="stat"><div class="stat-label">Units in Stock</div><strong>${U.qty(s.units)}</strong></article><article class="stat"><div class="stat-label">Inventory Value</div><strong>${U.money(s.value)}</strong></article><article class="stat"><div class="stat-label">Low Stock</div><strong>${s.low}</strong></article><article class="stat"><div class="stat-label">Out of Stock</div><strong>${s.out}</strong></article></div><section class="panel"><div class="panel-header"><h2>${U.esc(report)}</h2></div>${report==='Products by Category'?cats.rows.map(r=>`<div class="bar-row"><span>${U.esc(r[0])}</span><div class="bar-track"><div class="bar-fill" style="width:${r[1]/max*100}%"></div></div><strong>${r[1]}</strong></div>`).join(''):''}${U.table(d.headers,d.rows.map(row=>'<tr>'+row.map(v=>'<td>'+U.esc(v)+'</td>').join('')+'</tr>').join(''))}</section><p style="font-size:11px;color:var(--muted)">Current reports exclude archived products. Movement history retains all recorded transactions. Unit totals combine different units of measure.</p>`;
  }

  function download(filename, content, type) {
    const url = URL.createObjectURL(new Blob([content], {
      type
    }));
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function csvCell(value) {
    let s = String(value ?? '');
    if (/^[\s]*[=+@-]/.test(s)) s = "'" + s;
    return '"' + s.replace(/"/g, '""') + '"';
  }

  function csv(filename, headers, rows) {
    download(filename, '\uFEFF' + [headers, ...rows].map(row => row.map(csvCell).join(',')).join('\r\n'), 'text/csv;charset=utf-8');
  }
  A.Reports = {
    names,
    data,
    render,
    download,
    csv,
    export () {
      const d = data(A.report);
      csv('inventory-' + A.report.toLowerCase().replaceAll(' ', '-') + '.csv', d.headers, d.rows);
    },
    exportHistory() {
      csv('stock-history.csv', A.UI.historyHeaders, A.UI.filteredHistory().map(t => [t.date, t.productName, t.sku, t.type, (t.direction === 'out' ? '-' : '+') + t.quantity, t.previous, t.next, t.reason, t.reference, t.supplierName, t.notes]));
    }
  };
})(window.InventoryApp);
