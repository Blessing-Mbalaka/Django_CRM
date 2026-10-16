(() => {
  const sidebar = document.querySelector('#crmSidebar');
  const desktopToggle = document.querySelector('#crmSidebarToggle');
  const mobileMenu = document.querySelector('#crmMobileMenu');
  if (!sidebar) return;

  const closeMobile = () => {
    sidebar.classList.remove('is-open');
    mobileMenu?.setAttribute('aria-expanded', 'false');
  };

  desktopToggle?.addEventListener('click', () => {
    const expanded = document.body.classList.toggle('crm-sidebar-expanded');
    desktopToggle.setAttribute('aria-expanded', String(expanded));
    desktopToggle.setAttribute('aria-label', expanded ? 'Collapse CRM navigation' : 'Expand CRM navigation');
  });

  mobileMenu?.addEventListener('click', () => {
    const open = sidebar.classList.toggle('is-open');
    mobileMenu.setAttribute('aria-expanded', String(open));
  });

  sidebar.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMobile));
  document.addEventListener('keydown', event => { if (event.key === 'Escape') closeMobile(); });
  document.addEventListener('click', event => {
    if (!sidebar.contains(event.target) && !mobileMenu?.contains(event.target)) closeMobile();
  });
})();
