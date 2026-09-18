(function(A) {
  'use strict';
  const U = A.UI,
    D = A.Domain,
    $ = s => document.querySelector(s);
  const pages = {
    dashboard: 'Dashboard',
    products: 'Products',
    categories: 'Categories',
    in: 'Stock In',
    out: 'Stock Out',
    suppliers: 'Suppliers',
    history: 'Stock History',
    low: 'Low Stock',
    reports: 'Reports',
    settings: 'Settings'
  };
  A.filters = {
    products: {
      q: '',
      category: '',
      status: 'All statuses',
      sort: 'Newest first'
    },
    categories: {
      q: ''
    },
    suppliers: {
      q: ''
    },
    history: {
      q: '',
      product: '',
      type: 'All movements',
      from: '',
      to: '',
      reason: ''
    }
  };
  A.report = 'Current Stock Summary';

  function toast(message, error = false) {
    const div = document.createElement('div');
    div.className = 'toast' + (error ? ' error-toast' : '');
    div.textContent = message;
    $('#toasts').append(div);
    setTimeout(() => div.remove(), 4500);
  }

  function modal(title, html) {
    $('#modalTitle').textContent = title;
    $('#modalBody').innerHTML = html;
    if (!$('#modal').open) $('#modal').showModal();
    const form = $('#modal form[data-form="movement"]');
    if (form) updatePreview(form);
  }

  function closeModal() {
    $('#modal').close();
    $('#modalBody').innerHTML = '';
  }

  function confirmAction(title, description, callback) {
    modal(title, `<p style="line-height:1.7">${U.esc(description)}</p><div class="form-actions">${U.button('Cancel','close-modal')}<button class="btn danger" id="confirmAction">Confirm</button></div>`);
    $('#confirmAction').onclick = () => {
      try {
        callback();
        closeModal();
        render();
      } catch (e) {
        toast(e.message, true);
      }
    };
  }

  function render() {
    document.body.classList.toggle('dashboard-page', A.page === 'dashboard');
    const name = A.state.settings.businessName;
    $('#businessName').textContent = name;
    $('#businessInitials').textContent = name.split(/\s+/).slice(0, 2).map(s => s[0]).join('').toUpperCase();
    $('#pageTitle').textContent = pages[A.page];
    document.title = pages[A.page] + ' · EIEAAS Inventory';
    $('#navigation').innerHTML = Object.entries(pages).map(([id, label]) => `<button data-action="navigate" data-id="${id}" class="${A.page===id?'active':''}" ${A.page===id?'aria-current="page"':''} aria-label="${label}" title="${label}">${U.icon(id)}<span>${label}</span></button>`).join('');
    const views = {
      dashboard: U.dashboard,
      products: U.products,
      categories: U.categories,
      suppliers: U.suppliers,
      history: U.history,
      low: U.low,
      reports: A.Reports.render,
      settings: U.settings,
      in: () => U.movementPage('in'),
      out: () => U.movementPage('out')
    };
    $('#content').innerHTML = views[A.page]();
    const form = $('#content form[data-form="movement"]');
    if (form) updatePreview(form);
  }

  function navigate(page) {
    if (!pages[page]) page = 'dashboard';
    A.page = page;
    history.replaceState(null, '', '#' + page);
    $('#sidebar').classList.remove('open');
    $('#menuButton').setAttribute('aria-expanded', 'false');
    render();
  }

  function updatePreview(form) {
    const p = A.state.products.find(p => p.id === form.elements.product.value),
      direction = form.elements.direction.value,
      amount = Number(form.elements.quantity.value) || 0;
    const next = p ? Math.round((p.quantity + (direction === 'in' ? amount : -amount)) * 1000) / 1000 : 0;
    const preview = form.querySelector('#stockPreview');
    preview.innerHTML = `<div><span>Current Stock</span><strong>${p?U.qty(p.quantity)+' '+U.esc(p.unit):'—'}</strong></div><div><span>${direction==='in'?'Receiving':'Removing'}</span><strong>${U.qty(amount)}</strong></div><div><span>New Stock</span><strong class="${next<0?'invalid':''}">${p?U.qty(next)+' '+U.esc(p.unit):'—'}</strong></div>`;
    const quantity = form.elements.quantity;
    quantity.setCustomValidity(next < 0 ? 'Insufficient stock. Reduce the quantity.' : '');
    form.querySelector('#movementSupplier').hidden = direction === 'out';
  }
  document.addEventListener('click', event => {
    const target = event.target.closest('[data-action]');
    if (!target) return;
    const action = target.dataset.action,
      id = target.dataset.id;
    try {
      const p = () => A.state.products.find(p => p.id === id),
        s = () => A.state.suppliers.find(s => s.id === id),
        c = () => A.state.categories.find(c => c.id === id);
      switch (action) {
        case 'navigate':
          navigate(id);
          break;
        case 'sign-out':
          window.location.assign('../index.html');
          break;
        case 'close-modal':
          closeModal();
          break;
        case 'add-product':
          modal('Add Product', U.productForm());
          break;
        case 'edit-product':
          modal('Edit Product', U.productForm(p()));
          break;
        case 'view-product':
          modal('Product Details', U.viewProduct(p()));
          break;
        case 'archive-product':
          confirmAction('Archive product?', `Archive ${p().name}? It will be removed from active inventory and reports. Stock history is retained.`, () => {
            D.archiveProduct(id);
            toast('Product archived successfully');
          });
          break;
        case 'add-category':
          modal('Add Category', U.categoryForm());
          break;
        case 'edit-category':
          modal('Edit Category', U.categoryForm(c()));
          break;
        case 'delete-category':
          confirmAction('Delete category?', `Delete ${c().name}? Categories assigned to products cannot be deleted.`, () => {
            D.deleteCategory(id);
            toast('Category deleted');
          });
          break;
        case 'add-supplier':
          modal('Add Supplier', U.supplierForm());
          break;
        case 'edit-supplier':
          modal('Edit Supplier', U.supplierForm(s()));
          break;
        case 'view-supplier':
          modal('Supplier Details', U.viewSupplier(s()));
          break;
        case 'delete-supplier':
          confirmAction('Delete supplier?', `Delete ${s().name}? Associated products will be marked as not assigned. Previous stock history will retain the supplier name.`, () => {
            D.deleteSupplier(id);
            toast('Supplier deleted');
          });
          break;
        case 'adjust':
          modal('Adjust Stock · ' + p().name, U.movementForm('in', id, true));
          break;
        case 'add-stock':
          modal('Add Stock · ' + p().name, U.movementForm('in', id, false));
          break;
        case 'select-report':
          A.report = id;
          render();
          break;
        case 'export-report':
          A.Reports.export();
          toast('Report exported');
          break;
        case 'export-history':
          A.Reports.exportHistory();
          toast('History exported');
          break;
        case 'print-report':
          window.print();
          break;
        case 'backup':
          A.Reports.download('inventory-backup-' + new Date().toISOString().slice(0, 10) + '.json', JSON.stringify(A.state, null, 2), 'application/json');
          toast('Backup downloaded');
          break;
        case 'clear-data':
          confirmAction('Clear all inventory data?', 'This permanently removes all products, categories, suppliers and stock history, including any custom records. Download a backup first if you need a copy. Your business settings will be kept.', () => {
            D.clearData();
            toast('Inventory cleared. Your workspace is ready.');
          });
          break;
      }
    } catch (error) {
      toast(error.message, true);
    }
  });
  document.addEventListener('submit', event => {
    const form = event.target.closest('[data-form]');
    if (!form) return;
    event.preventDefault();
    if (!form.reportValidity()) return;
    const values = Object.fromEntries(new FormData(form)),
      id = form.dataset.id;
    try {
      const kind = form.dataset.form;
      if (kind === 'product') {
        D.saveProduct(values, id);
        toast(id ? 'Product updated successfully' : 'Product added successfully');
      }
      if (kind === 'category') {
        D.saveCategory(values, id);
        toast(id ? 'Category updated' : 'Category added');
      }
      if (kind === 'supplier') {
        D.saveSupplier(values, id);
        toast(id ? 'Supplier updated' : 'Supplier added');
      }
      if (kind === 'movement') {
        D.move({
          ...values,
          adjustment: form.dataset.adjustment === 'true'
        });
        toast('Stock updated successfully');
      }
      if (kind === 'settings') {
        D.saveSettings(values);
        toast('Settings saved');
      }
      if ($('#modal').open) closeModal();
      render();
    } catch (error) {
      form.querySelector('#formError').textContent = error.message;
      toast(error.message, true);
    }
  });

  function onFilter(event) {
    const input = event.target;
    if (!input.dataset.filter) return;
    const [page, key] = input.dataset.filter.split('.');
    A.filters[page][key] = input.value;
    const views = {
      products: U.productResults,
      categories: U.categoryResults,
      suppliers: U.supplierResults,
      history: () => U.table(U.historyHeaders, U.historyRows(U.filteredHistory()))
    };
    $('#' + page + 'Results').innerHTML = views[page]();
  }
  document.addEventListener('input', event => {
    onFilter(event);
    const form = event.target.closest('form[data-form="movement"]');
    if (form) updatePreview(form);
  });
  document.addEventListener('change', event => {
    if (event.target.tagName === 'SELECT') onFilter(event);
    const form = event.target.closest('form[data-form="movement"]');
    if (!form) return;
    if (event.target.name === 'product') {
      const p = A.state.products.find(p => p.id === event.target.value);
      form.elements.supplier.value = p?.supplier || '';
    }
    if (event.target.name === 'direction') {
      const incoming = event.target.value === 'in';
      form.elements.reason.innerHTML = U.options(incoming ? ['Purchase', 'Customer Return', 'Opening stock', 'Correction', 'Other'] : ['Sale', 'Internal Use', 'Damaged', 'Expired', 'Lost', 'Returned to Supplier', 'Correction', 'Other'], 'Correction');
    }
    updatePreview(form);
  });
  $('#sidebarToggle').onclick = () => {
    const expanded = document.body.classList.toggle('sidebar-expanded');
    $('#sidebarToggle').setAttribute('aria-expanded', String(expanded));
    $('#sidebarToggle').setAttribute('aria-label', expanded ? 'Collapse sidebar' : 'Expand sidebar');
    $('#sidebarToggle').title = expanded ? 'Collapse sidebar' : 'Expand sidebar';
  };
  $('#menuButton').onclick = () => {
    const open = $('#sidebar').classList.toggle('open');
    $('#menuButton').setAttribute('aria-expanded', String(open));
  };
  document.addEventListener('click', event => {
    if (!event.target.closest('#sidebar') && !event.target.closest('#menuButton')) {
      $('#sidebar').classList.remove('open');
      $('#menuButton').setAttribute('aria-expanded', 'false');
    }
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      $('#sidebar').classList.remove('open');
      $('#menuButton').setAttribute('aria-expanded', 'false');
    }
  });
  window.addEventListener('hashchange', () => navigate(location.hash.slice(1)));
  window.addEventListener('storage', event => {
    if (event.key === A.Storage.key) {
      try {
        A.state = A.Storage.load();
        if ($('#modal').open) closeModal();
        render();
        toast('Inventory updated from another tab');
      } catch (e) {
        toast(e.message, true);
      }
    }
  });
  try {
    A.state = A.Storage.load();
    navigate(location.hash.slice(1) || 'dashboard');
  } catch (error) {
    $('#content').innerHTML = '<section class="panel">' + U.empty('Inventory could not be opened', U.esc(error.message)) + '</section>';
    toast(error.message, true);
  }
  A.render = render;
  A.navigate = navigate;
})(window.InventoryApp);
