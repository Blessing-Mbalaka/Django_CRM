export function escapeHtml(value = '') {
  const element = document.createElement('div');
  element.textContent = String(value);
  return element.innerHTML;
}

export function formatMoney(value, currency = 'ZAR') {
  return new Intl.NumberFormat('en-ZA', { style: 'currency', currency }).format(Number(value || 0));
}

export function formatDate(value) {
  if (!value) return '—';
  return new Intl.DateTimeFormat('en-ZA', { dateStyle: 'medium' }).format(new Date(`${value}T00:00:00`));
}

export function setFeedback(message, tone = 'info') {
  const region = document.getElementById('moduleFeedback');
  if (!region) return;
  region.className = `module-feedback is-${tone}`;
  region.textContent = message;
  region.hidden = !message;
}

export function setBusy(element, busy, label = 'Working…') {
  if (!element) return;
  if (busy) {
    element.dataset.originalLabel = element.innerHTML;
    element.disabled = true;
    element.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span>${label}`;
  } else {
    element.disabled = false;
    element.innerHTML = element.dataset.originalLabel || element.innerHTML;
  }
}

