(function () {
  'use strict';
  const form = document.getElementById('businessActivityFilters');
  const chart = document.getElementById('businessActivityChart');
  const status = document.getElementById('activityChartStatus');
  const summary = document.getElementById('activitySummary');
  if (!form || !chart) return;

  const money = new Intl.NumberFormat('en-ZA', { style: 'currency', currency: 'ZAR', maximumFractionDigits: 0 });
  const number = new Intl.NumberFormat('en-ZA', { maximumFractionDigits: 3 });
  const today = new Date();
  const oneYearAgo = new Date(today);
  oneYearAgo.setFullYear(today.getFullYear() - 1);
  const iso = (value) => value.toISOString().slice(0, 10);
  form.elements.end_date.value = iso(today);
  form.elements.start_date.value = iso(oneYearAgo);

  function summaryCard(icon, label, value) {
    return `<div><i class="bi ${icon}"></i><span>${label}</span><strong>${value}</strong></div>`;
  }

  function renderSummary(data) {
    const item = data.summary;
    summary.innerHTML = [
      summaryCard('bi-graph-up-arrow', 'Revenue', money.format(item.revenue)),
      summaryCard('bi-graph-down-arrow', 'Expenses', money.format(item.expenses)),
      summaryCard('bi-calculator', 'Net profit', money.format(item.net_profit)),
      summaryCard('bi-boxes', 'Stock on hand', number.format(item.inventory_level)),
      summaryCard('bi-box-seam', 'Inventory value', money.format(item.inventory_value)),
      summaryCard('bi-cart-check', 'Purchasing', money.format(item.purchasing)),
    ].join('');
  }

  function currencyTrace(name, values, colour, type = 'scatter', visible = true) {
    return { x: currentLabels, y: values, name, type, mode: type === 'scatter' ? 'lines+markers' : undefined, marker: { color: colour }, line: { color: colour, width: 3 }, yaxis: 'y', visible };
  }

  let currentLabels = [];
  async function loadActivity() {
    status.hidden = false;
    status.textContent = 'Loading business activity…';
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    try {
      const query = new URLSearchParams(new FormData(form));
      [...query.entries()].forEach(([key, value]) => { if (!value) query.delete(key); });
      const response = await fetch(`${form.dataset.endpoint}?${query.toString()}`, { credentials: 'same-origin', headers: { Accept: 'application/json' } });
      if (!response.ok) throw new Error(`Activity request failed (${response.status})`);
      const data = await response.json();
      currentLabels = data.labels;
      renderSummary(data);
      if (!window.Plotly) throw new Error('Plotly could not be loaded. Check the network connection and refresh.');
      const traces = [
        currencyTrace('Revenue', data.currency.revenue, '#16a34a', 'bar'),
        currencyTrace('Expenses', data.currency.expenses, '#ef4444', 'bar'),
        currencyTrace('Purchasing', data.currency.purchasing, '#f59e0b'),
        currencyTrace('Inventory value', data.currency.inventory_value, '#7c3aed'),
        currencyTrace('Cash received', data.currency.cash_in, '#0284c7', 'scatter', 'legendonly'),
        currencyTrace('Cash paid', data.currency.cash_out, '#db2777', 'scatter', 'legendonly'),
        { x: currentLabels, y: data.quantity.inventory_level, name: 'Inventory level', type: 'scatter', mode: 'lines+markers', yaxis: 'y2', line: { color: '#4338ca', width: 3, dash: 'dot' }, marker: { color: '#4338ca' } },
        { x: currentLabels, y: data.quantity.purchase_receipts, name: 'Quantity received', type: 'bar', yaxis: 'y2', marker: { color: 'rgba(14,116,144,.35)' } },
      ];
      await window.Plotly.react(chart, traces, {
        barmode: 'group', hovermode: 'x unified', margin: { l: 70, r: 70, t: 25, b: 55 },
        paper_bgcolor: 'transparent', plot_bgcolor: '#fff',
        legend: { orientation: 'h', y: -0.2 },
        xaxis: { title: '', gridcolor: '#eeeef3' },
        yaxis: { title: 'Value (ZAR)', tickprefix: 'R ', gridcolor: '#eeeef3', zerolinecolor: '#d9d9e2' },
        yaxis2: { title: 'Quantity', overlaying: 'y', side: 'right', showgrid: false, zeroline: false },
        font: { family: 'Segoe UI, system-ui, sans-serif', color: '#1a1a2e', size: 11 },
      }, { responsive: true, displaylogo: false, modeBarButtonsToRemove: ['lasso2d', 'select2d'] });
      status.hidden = true;
    } catch (error) {
      status.hidden = false;
      status.textContent = error.message;
      window.JBSToast?.show(error.message, 'danger');
    } finally {
      button.disabled = false;
    }
  }

  form.addEventListener('submit', (event) => { event.preventDefault(); loadActivity(); });
  loadActivity();
})();
