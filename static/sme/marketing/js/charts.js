import { esc, formatNumber, money } from './views.js';

export function funnel(totals) {
  const steps = [
    ['People reached', totals.reach], ['Responses', totals.responses],
    ['Enquiries', totals.enquiries], ['Leads', totals.leads], ['Customers', totals.customers],
  ];
  return `<div class="marketing-funnel">${steps.map(([label, value], index) => `<div style="width:${100 - index * 9}%"><span>${esc(label)}</span><strong>${formatNumber(value)}</strong></div>${index < steps.length - 1 ? '<span aria-hidden="true">↓</span>' : ''}`).join('')}</div>`;
}

export function channelBars(channels) {
  if (!channels.length) return '<p class="no-data">No channel measurements have been recorded yet.</p>';
  const max = Math.max(...channels.map(item => Number(item.revenue || 0)), 1);
  return `<div class="channel-bars">${channels.map(item => `<div class="bar-row"><span>${esc(item.channel)}</span><div class="bar-track"><i style="width:${Math.max(2, Number(item.revenue || 0) / max * 100)}%"></i></div><strong>${money(item.revenue)}</strong></div>`).join('')}</div>`;
}
