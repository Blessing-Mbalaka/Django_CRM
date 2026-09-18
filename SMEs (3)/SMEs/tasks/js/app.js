/* Navigation and interactions. No network requests or browser storage. */
(function(A) {
  'use strict';
  const S = A.state;
  const U = A.UI;
  const $ = selector => document.querySelector(selector);
  const pages = {
    dashboard: 'Dashboard',
    projects: 'Projects',
    tasks: 'Tasks',
    my: 'My Tasks',
    calendar: 'Calendar',
    team: 'Team'
  };
  let nextId = 1;
  let modalTrigger;

  function toast(message) {
    const element = document.createElement('div');
    element.className = 'toast';
    element.textContent = message;
    $('#toasts').append(element);
    setTimeout(() => element.remove(), 3500);
  }

  function closeSidebar() {
    $('#sidebar').classList.remove('open');
    $('#menuButton').setAttribute('aria-expanded', 'false');
  }

  function render() {
    const title = S.page === 'dashboard' ? 'Task & Project Management' : S.page === 'project' ? 'Project Details' : pages[S.page];
    $('#pageTitle').textContent = title;
    document.title = `${title} · EIEAAS`;
    $('#navigation').innerHTML = Object.entries(pages).map(([id, label]) => {
      const active = S.page === id || (id === 'projects' && S.page === 'project');
      return `<button data-action="navigate" data-id="${id}" class="${active ? 'active' : ''}" ${active ? 'aria-current="page"' : ''} aria-label="${label}" title="${label}">${U.icon(id)}<span>${label}</span></button>`;
    }).join('');
    const primary = $('#primaryAction');
    primary.textContent = S.page === 'projects' ? '＋ New Project' : '＋ New Task';
    primary.dataset.action = S.page === 'projects' ? 'new-project' : 'new-task';
    primary.dataset.id = S.page === 'project' ? S.projectId : '';
    const views = {
      dashboard: U.dashboard,
      projects: U.projects,
      project: U.projectDetail,
      tasks: U.tasks,
      my: U.myTasks,
      calendar: U.calendar,
      team: U.team
    };
    $('#content').innerHTML = views[S.page]();
  }

  function navigate(route) {
    const [page, id] = route.split('/');
    S.page = pages[page] || page === 'project' ? page : 'dashboard';
    S.projectId = page === 'project' ? id : '';
    closeSidebar();
    render();
    $('#content').focus({
      preventScroll: true
    });
  }

  function openModal(title, html) {
    modalTrigger = document.activeElement;
    $('#modalTitle').textContent = title;
    $('#modalBody').innerHTML = html;
    $('#modal').showModal();
    const input = $('#modal input');
    if (input) input.focus();
  }

  function closeModal() {
    $('#modal').close();
    $('#modalBody').innerHTML = '';
    if (modalTrigger?.isConnected) modalTrigger.focus();
  }

  function complete(id) {
    const task = S.tasks.find(item => item.id === id);
    if (!task) return;
    task.status = task.status === 'Completed' ? 'To Do' : 'Completed';
    render();
    toast(task.status === 'Completed' ? 'Task completed' : 'Task reopened');
  }

  document.addEventListener('click', event => {
    document.querySelectorAll('.task-menu[open]').forEach(menu => {
      if (!menu.contains(event.target)) menu.open = false;
    });
    const target = event.target.closest('[data-action]');
    if (target) {
      const {
        action,
        id
      } = target.dataset;
      switch (action) {
        case 'navigate':
          location.hash = id;
          break;
        case 'project':
          location.hash = `project/${id}`;
          break;
        case 'new-task':
          openModal('New Task', U.taskForm({}, id));
          break;
        case 'new-project':
          openModal('New Project', U.projectForm());
          break;
        case 'edit-task': {
          const task = S.tasks.find(item => item.id === id);
          if (task) openModal('Task Details', U.taskForm(task));
          break;
        }
        case 'close-modal':
          closeModal();
          break;
        case 'complete':
          complete(id);
          break;
        case 'filter':
          S.filter = id;
          render();
          break;
        case 'view':
          S.view = id;
          render();
          break;
        case 'personal-tab':
          S.personalTab = id;
          render();
          break;
        case 'month':
          S.month = id === 'today' ? new Date(new Date().getFullYear(), new Date().getMonth(), 1) : new Date(S.month.getFullYear(), S.month.getMonth() + Number(id), 1);
          render();
          break;
      }
    }
    if (!event.target.closest('#sidebar') && !event.target.closest('#menuButton')) closeSidebar();
  });

  document.addEventListener('input', event => {
    if (event.target.id === 'taskSearch') {
      S.search = event.target.value;
      $('#taskResults').innerHTML = U.taskResults();
    }
  });

  document.addEventListener('change', event => {
    const target = event.target;
    if (target.dataset.complete) complete(target.dataset.complete);
    if (target.dataset.taskStatus) {
      const task = S.tasks.find(item => item.id === target.dataset.taskStatus);
      if (task) task.status = target.value;
      render();
      toast('Task status updated');
    }
  });

  document.addEventListener('submit', event => {
    const form = event.target.closest('form[data-form]');
    if (!form) return;
    event.preventDefault();
    if (!form.reportValidity()) return;
    const data = new FormData(form);
    const values = Object.fromEntries(data);
    if (!values.name.trim()) {
      $('#formError').textContent = 'Please enter a name.';
      return;
    }
    values.name = values.name.trim();
    if (form.dataset.form === 'project') {
      if (values.due < values.start) {
        $('#formError').textContent = 'The due date must be on or after the start date.';
        return;
      }
      const created = {
        ...values,
        id: `new-project-${nextId++}`,
        members: [...new Set([values.owner, ...data.getAll('members')])]
      };
      S.projects.push(created);
      closeModal();
      location.hash = `project/${created.id}`;
      toast('Project created');
    } else {
      const existing = S.tasks.find(item => item.id === form.dataset.id);
      values.attachment = data.get('attachment')?.name || existing?.attachment || '';
      if (existing) Object.assign(existing, values);
      else S.tasks.push({
        ...values,
        id: `new-task-${nextId++}`
      });
      closeModal();
      render();
      toast(existing ? 'Task updated' : 'Task created');
    }
  });

  $('#sidebarToggle').addEventListener('click', () => {
    const expanded = document.body.classList.toggle('sidebar-expanded');
    $('#sidebarToggle').setAttribute('aria-expanded', String(expanded));
    $('#sidebarToggle').setAttribute('aria-label', expanded ? 'Collapse sidebar' : 'Expand sidebar');
    $('#sidebarToggle').title = expanded ? 'Collapse sidebar' : 'Expand sidebar';
  });
  $('#menuButton').addEventListener('click', () => {
    const open = $('#sidebar').classList.toggle('open');
    $('#menuButton').setAttribute('aria-expanded', String(open));
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      closeSidebar();
      document.querySelectorAll('.task-menu[open]').forEach(menu => menu.open = false);
    }
  });
  $('#modal').addEventListener('cancel', event => {
    event.preventDefault();
    closeModal();
  });
  window.addEventListener('hashchange', () => navigate(location.hash.slice(1)));
  navigate(location.hash.slice(1) || 'dashboard');
})(window.TaskApp);
