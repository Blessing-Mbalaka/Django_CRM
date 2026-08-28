/**
 * JBS CRM — Main JavaScript
 * Toast auto-dismiss · Sidebar toggle · Active nav detection
 */

// ── TOAST SYSTEM ──────────────────────────────────────────────────
(function () {
  'use strict';

  const TOAST_DURATION = 5000; // ms before auto-dismiss

  function dismissToast(toast) {
    toast.style.animation = 'toastFadeOut 0.3s ease-in forwards';
    setTimeout(() => toast.remove(), 320);
  }

  function initToasts() {
    const toasts = document.querySelectorAll('.uj-toast');
    toasts.forEach((toast) => {
      // Auto-dismiss
      const timer = setTimeout(() => dismissToast(toast), TOAST_DURATION);

      // Manual close button
      const closeBtn = toast.querySelector('.toast-close');
      if (closeBtn) {
        closeBtn.addEventListener('click', () => {
          clearTimeout(timer);
          dismissToast(toast);
        });
      }

      // Pause timer on hover (usability — user can read without it disappearing)
      let remaining = TOAST_DURATION;
      let start = Date.now();
      let timeoutId = timer;

      toast.addEventListener('mouseenter', () => {
        clearTimeout(timeoutId);
        remaining -= Date.now() - start;
      });

      toast.addEventListener('mouseleave', () => {
        start = Date.now();
        timeoutId = setTimeout(() => dismissToast(toast), remaining);
      });
    });
  }

  document.addEventListener('DOMContentLoaded', initToasts);
})();

// ── CONFIRM DIALOGS (affordance for destructive actions) ──────────
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-confirm]').forEach((el) => {
    el.addEventListener('click', (e) => {
      if (!window.confirm(el.dataset.confirm)) {
        e.preventDefault();
        e.stopImmediatePropagation();
      }
    });
  });
});

// Runtime toasts for API-driven modules. Server-side Django messages use the
// same visual component and are initialised above.
(function () {
  'use strict';

  const ICONS = {
    success: 'bi-check-circle-fill',
    warning: 'bi-exclamation-triangle-fill',
    danger: 'bi-x-circle-fill',
    info: 'bi-info-circle-fill',
  };

  function show(message, tone = 'info', options = {}) {
    if (!message) return null;
    let container = document.querySelector('.toast-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container';
      container.setAttribute('role', 'region');
      container.setAttribute('aria-live', 'polite');
      container.setAttribute('aria-label', 'Notifications');
      document.body.appendChild(container);
    }
    const safeTone = Object.prototype.hasOwnProperty.call(ICONS, tone) ? tone : 'info';
    const toast = document.createElement('div');
    toast.className = `uj-toast toast-${safeTone}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-atomic', 'true');

    const icon = document.createElement('span');
    icon.className = `toast-icon text-${safeTone}`;
    icon.innerHTML = `<i class="bi ${ICONS[safeTone]}"></i>`;
    const body = document.createElement('div');
    body.className = 'toast-body';
    body.textContent = String(message);
    const close = document.createElement('button');
    close.className = 'toast-close';
    close.type = 'button';
    close.setAttribute('aria-label', 'Dismiss notification');
    close.textContent = '×';
    toast.append(icon, body, close);
    container.appendChild(toast);

    const dismiss = () => {
      toast.style.animation = 'toastFadeOut 0.3s ease-in forwards';
      setTimeout(() => toast.remove(), 320);
    };
    const timer = setTimeout(dismiss, options.duration || (safeTone === 'danger' ? 9000 : 5000));
    close.addEventListener('click', () => { clearTimeout(timer); dismiss(); });
    return toast;
  }

  window.JBSToast = { show };
  document.addEventListener('DOMContentLoaded', () => {
    if (!window.bootstrap?.Modal && document.querySelector('[data-bs-toggle="modal"]')) {
      show('Interface library failed to load. Modal buttons are unavailable; hard-refresh the page and check network access.', 'danger', { duration: 15000 });
    }
  });
  window.addEventListener('error', (event) => {
    if (!event.error) return;
    console.error('Interface error', event.error);
    show(`Interface error: ${event.error.message || 'Unknown JavaScript error'}`, 'danger');
  });
  window.addEventListener('unhandledrejection', (event) => {
    const reason = event.reason instanceof Error ? event.reason.message : String(event.reason || 'Unknown request error');
    console.error('Unhandled request error', event.reason);
    show(`Request error: ${reason}`, 'danger');
  });
})();
