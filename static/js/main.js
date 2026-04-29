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

// ── SIDEBAR TOGGLE (mobile) ───────────────────────────────────────
(function () {
  'use strict';

  const sidebar = document.getElementById('sidebar');
  const toggleBtn = document.getElementById('sidebarToggle');
  const overlay = document.getElementById('sidebarOverlay');

  function openSidebar() {
    sidebar?.classList.add('open');
    overlay?.classList.remove('d-none');
    document.body.style.overflow = 'hidden';
    toggleBtn?.setAttribute('aria-expanded', 'true');
  }

  function closeSidebar() {
    sidebar?.classList.remove('open');
    overlay?.classList.add('d-none');
    document.body.style.overflow = '';
    toggleBtn?.setAttribute('aria-expanded', 'false');
  }

  toggleBtn?.addEventListener('click', () => {
    sidebar?.classList.contains('open') ? closeSidebar() : openSidebar();
  });

  overlay?.addEventListener('click', closeSidebar);

  // Close sidebar on ESC key (accessibility)
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeSidebar();
  });
})();

// ── ACTIVE SIDEBAR NAV ────────────────────────────────────────────
(function () {
  'use strict';

  const links = document.querySelectorAll('.sidebar-nav a');
  const currentPath = window.location.pathname;

  links.forEach((link) => {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
      link.setAttribute('aria-current', 'page');
    }
  });
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
