(function(A) {
  'use strict';
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  } [c]));
  const money = n => new Intl.NumberFormat('en-ZA', {
    style: 'currency',
    currency: A.state.settings.currency
  }).format(n);
  const qty = n => new Intl.NumberFormat('en-ZA', {
    maximumFractionDigits: 3
  }).format(n);
  const category = id => A.state.categories.find(c => c.id === id)?.name || 'Uncategorised';
  const supplier = id => A.state.suppliers.find(s => s.id === id)?.name || 'Not assigned';
  const paths = {
    dashboard: 'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z',
    products: 'm3 7 9-4 9 4v10l-9 4-9-4zM3 7l9 4 9-4M12 11v10',
    categories: 'M3 5h7l2 3h9v12H3z',
    in: 'M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5',
    out: 'M12 16V4m-5 5 5-5 5 5M4 16v5h16v-5',
    suppliers: 'M3 5h12v13H3zM15 10h4l3 4v4h-7M5 18a2 2 0 1 0 4 0M16 18a2 2 0 1 0 4 0',
    history: 'M3 10a9 9 0 1 1 0 5M3 4v6h6M12 7v5l3 2',
    low: 'm12 3 10 18H2zM12 9v5M12 17h.01',
    reports: 'M4 3v18h17M8 16v-5M13 16V6M18 16V9',
    settings: 'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M5 19l2-2M17 7l2-2'
  };
  const icon = name => `<svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="${paths[name]||paths.products}"/></svg>`;
  const button = (label, action, id = '', kind = 'secondary small') => `<button class="btn ${kind}" data-action="${action}" ${id?`data-id="${esc(id)}"`:''}>${label}</button>`;
  const badge = p => `<span class="badge ${p.quantity===0?'out':p.quantity<=p.minimum?'low':''}">${A.Domain.status(p)}</span>`;
  const empty = (title, body, action = '') => `<div class="empty"><div class="empty-icon">${icon('products')}</div><strong>${title}</strong><p>${body}</p>${action}</div>`;
  const table = (heads, rows) => `<div class="table-wrap"><table><thead><tr>${heads.map(h=>`<th>${h}</th>`).join('')}</tr></thead><tbody>${rows||`<tr><td colspan="${heads.length}">${empty('No results found','Try another filter or add your first record.')}</td></tr>`}</tbody></table></div>`;
  const selectOptions = (items, value = '', placeholder = 'Select…') => `<option value="">${placeholder}</option>` + items.map(i => `<option value="${esc(i.id)}" ${i.id===value?'selected':''}>${esc(i.name)}</option>`).join('');
  const options = (items, value) => items.map(i => `<option value="${esc(i)}" ${i===value?'selected':''}>${esc(i)}</option>`).join('');
  const units = ['Item', 'Piece', 'Box', 'Pack', 'Kg', 'Gram', 'Litre', 'Millilitre', 'Metre', 'Other'];
  const field = (label, name, value = '', type = 'text', extra = '') => `<label class="field">${label}<input name="${name}" type="${type}" value="${esc(value)}" ${extra}></label>`;
  const numeric = (label, name, value = 0) => field(label, name, value, 'number', 'min="0" max="1000000000000" step="0.001" required');
  const area = (label, name, value = '') => `<label class="field full">${label}<textarea name="${name}">${esc(value)}</textarea></label>`;
  const formActions = label => `<div class="form-actions full">${button('Cancel','close-modal')}<button class="btn" type="submit">${label}</button></div>`;
  const errorBox = '<div class="error" role="alert" id="formError"></div>';
  const matches = (value, q) => String(value).toLowerCase().includes((q || '').toLowerCase());

  function productRows(products, compact = false) {
    return products.map(p => `<tr><td><strong>${esc(p.name)}</strong>${compact?`<small>${esc(p.sku)}</small>`:''}</td>${compact?'':`<td>${esc(p.sku)}</td><td>${esc(category(p.category))}</td><td>${money(p.cost)}</td><td>${money(p.price)}</td>`}<td>${qty(p.quantity)}${compact?' '+esc(p.unit):''}</td>${compact?'':`<td>${esc(p.unit)}</td>`}<td>${badge(p)}</td>${compact?'':`<td>${esc(supplier(p.supplier))}</td>`}<td><div class="actions">${button('View','view-product',p.id)}${compact?'':button('Edit','edit-product',p.id)+button('Adjust Stock','adjust',p.id)+button('Archive','archive-product',p.id,'danger small')}</div></td></tr>`).join('');
  }

  function historyRows(items) {
    return items.map(t => `<tr><td>${esc(new Date(t.date).toLocaleString('en-ZA'))}</td><td>${esc(t.productName)}</td><td>${esc(t.sku)}</td><td><span class="badge ${t.type==='Adjustment'?'neutral':t.direction==='out'?'low':''}">${esc(t.type)}</span></td><td>${t.direction==='out'?'−':'+'}${qty(t.quantity)}</td><td>${qty(t.previous)}</td><td>${qty(t.next)}</td><td>${esc(t.reason)}</td><td>${esc(t.reference||'—')}</td><td>${esc(t.supplierName||'—')}</td><td>${esc(t.notes||'—')}</td></tr>`).join('');
  }
  const historyHeaders = ['Date / Time', 'Product', 'SKU', 'Movement', 'Quantity', 'Previous Stock', 'New Stock', 'Reason', 'Reference', 'Supplier', 'Notes'];

  function alertRows(products) {
    return products.map(p => `<tr><td><strong>${esc(p.name)}</strong></td><td>${esc(p.sku)}</td><td>${qty(p.quantity)} ${esc(p.unit)}</td><td>${qty(p.minimum)}</td><td>${esc(supplier(p.supplier))}</td><td>${badge(p)}</td><td>${button('＋ Add Stock','add-stock',p.id)}</td></tr>`).join('');
  }
  const alertTable = ps => table(['Product', 'SKU', 'Current Quantity', 'Minimum Level', 'Supplier', 'Status', 'Action'], alertRows(ps));

  function stockRose(products) {
    const totals = new Map();
    products.forEach(p => {
      if (p.quantity > 0) {
        const name = category(p.category);
        totals.set(name, (totals.get(name) || 0) + p.quantity);
      }
    });
    let entries = [...totals].sort((a, b) => b[1] - a[1]);
    if (entries.length > 3) entries = [...entries.slice(0, 2), ['Other categories', entries.slice(2).reduce((sum, e) => sum + e[1], 0)]];
    const total = entries.reduce((sum, e) => sum + e[1], 0);
    if (!total) return empty('No stock to display', 'Receive stock to see your inventory by category.');
    const colors = ['#175b4b', '#2e725e', '#438c75', '#75b49a', '#91c5a6', '#afd7b8', '#c3e3c9', '#def0df'];
    const max = Math.max(...entries.map(e => e[1])),
      step = 2 * Math.PI / entries.length;
    const point = (r, a) => [160 + r * Math.cos(a), 160 + r * Math.sin(a)];
    const sectors = entries.map(([name, value], i) => {
      const r = 140 * Math.sqrt(value / max),
        a = -Math.PI / 2 + i * step,
        b = a + step,
        mid = (a + b) / 2;
      const first = point(r, a),
        last = point(r, b),
        label = point(r * .66, mid),
        percentage = 100 * value / total;
      const title = esc(name) + ': ' + qty(value) + ' units (' + percentage.toFixed(1) + '%)';
      const shape = entries.length === 1 ? `<circle cx="160" cy="160" r="${r}" fill="${colors[i]}"><title>${title}</title></circle>` : `<path d="M160 160 L${first.join(' ')} A${r} ${r} 0 ${step>Math.PI?1:0} 1 ${last.join(' ')} Z" fill="${colors[i]}" stroke="white" stroke-width="1.5"><title>${title}</title></path>`;
      return shape + (percentage >= 3 ? `<text x="${label[0]}" y="${label[1]}" text-anchor="middle" dominant-baseline="middle" fill="${i<3?'#fff':'#175b4b'}">${Math.round(percentage)}%</text>` : '');
    }).join('');
    return `<div class="rose-overview"><svg class="stock-rose" viewBox="0 0 320 320" role="img" aria-label="Stock by category. Sector area represents the share of total stock.">${[35,70,105,140].map(r=>`<circle cx="160" cy="160" r="${r}" fill="none" stroke="#e8eee7"/>`).join('')}${sectors}</svg><div class="rose-legend">${entries.map(([name,value],i)=>`<div><span class="dot" style="background:${colors[i]}"></span><span>${esc(name)}<small>${qty(value)} units</small></span><strong>${(100*value/total).toFixed(1)}%</strong></div>`).join('')}</div></div>`;
  }

  function dashboard() {
    const s = A.Domain.summary(),
      products = A.Domain.active(),
      low = products.filter(p => p.quantity <= p.minimum).sort((a, b) => a.quantity - b.quantity);
    const metrics = [
      ['Total Products', qty(s.products), 'Active products', 'products', ''],
      ['Units in Stock', qty(s.units), 'Across all units of measure', 'in', ''],
      ['Low Stock Items', qty(s.low), 'At or below minimum', 'low', 'alert'],
      ['Out of Stock', qty(s.out), 'Ready to replenish', 'out', 'empty-stock']
    ];
    return `<section class="banner"><div class="banner-copy"><span class="eyebrow">EVERY ITEM. ALL IN ONE PLACE.</span><h2>Welcome back, ${esc(A.state.settings.businessName)}</h2><p>A clear view of your stock, so you can focus on what’s next for your business.</p>${button('＋ Add a Product','add-product','','shine')}</div><img src="../assets/inventory-banner.png" alt="Business owner organising their workspace"></section>
    <div class="stats inventory-summary">${metrics.map(m=>`<article class="stat ${m[4]}"><div class="stat-label">${m[0]}${icon(m[3])}</div><strong>${m[1]}</strong><small>${m[2]}</small></article>`).join('')}</div>
    <div class="dashboard-grid"><section class="panel"><div class="panel-header"><div><h2>Stock Overview</h2><p>Stock by category ? Percentage of total units</p></div>${button('Reports ↗','navigate','reports')}</div>${stockRose(products)}</section>
    <section class="panel"><div class="panel-header"><div><h2>Low Stock Alerts</h2><p>A little attention keeps business moving</p></div>${button('View All','navigate','low')}</div>${!A.state.settings.alerts?empty('Alerts are paused','Turn on low-stock alerts in Settings.',button('Open Settings','navigate','settings')):low.length?low.slice(0,3).map(p=>`<div class="alert-row"><div class="product-icon">${icon('products')}</div><div class="product-info"><strong>${esc(p.name)}</strong><small>Minimum required: ${qty(p.minimum)} ${esc(p.unit)}</small></div><div class="stock-count">${qty(p.quantity)} remaining</div>${button('＋','add-stock',p.id)}</div>`).join(''):empty('Stock is looking healthy','No products are below their minimum stock level.')}</section></div>`;
  }

  function products() {
    const f = A.filters.products;
    return `<div class="page-heading"><div><h2>Your product catalogue</h2><p>Keep every product, price and stock level in one place.</p></div>${button('＋ Add Product','add-product','','')}</div><section class="panel"><div class="filters"><input aria-label="Search products" placeholder="Search product name or SKU…" data-filter="products.q" value="${esc(f.q)}"><select aria-label="Filter category" data-filter="products.category">${selectOptions(A.state.categories,f.category,'All categories')}</select><select aria-label="Filter stock status" data-filter="products.status">${options(['All statuses','In Stock','Low Stock','Out of Stock'],f.status)}</select><select aria-label="Sort products" data-filter="products.sort">${options(['Newest first','Name A–Z','Quantity low–high','Value high–low'],f.sort)}</select></div><div id="productsResults">${productResults()}</div></section>`;
  }

  function filteredProducts() {
    const f = A.filters.products;
    let ps = A.Domain.active().filter(p => matches(p.name + ' ' + p.sku, f.q) && (!f.category || p.category === f.category) && (f.status === 'All statuses' || A.Domain.status(p) === f.status));
    return ps.sort((a, b) => f.sort === 'Name A–Z' ? a.name.localeCompare(b.name) : f.sort === 'Quantity low–high' ? a.quantity - b.quantity : f.sort === 'Value high–low' ? b.quantity * b.cost - a.quantity * a.cost : b.createdAt.localeCompare(a.createdAt));
  }

  function productResults() {
    return table(['Product', 'SKU', 'Category', 'Cost Price', 'Selling Price', 'Quantity', 'Unit', 'Stock Status', 'Supplier', 'Actions'], productRows(filteredProducts()));
  }

  function categories() {
    return `<section class="panel categories-panel"><div class="category-toolbar"><input aria-label="Search categories" placeholder="Search categories…" data-filter="categories.q" value="${esc(A.filters.categories.q)}">${button('＋ Add Category','add-category','','')}</div><div id="categoriesResults">${categoryResults()}</div></section>`;
  }

  function categoryResults() {
    const items = A.state.categories.filter(c => matches(c.name + ' ' + c.description, A.filters.categories.q));
    return items.length ? table(['Category', 'Products', ''], items.map(c => `<tr><td><div class="category-name"><span class="product-icon">${icon('categories')}</span><div><strong>${esc(c.name)}</strong>${c.description?`<small class="category-description" title="${esc(c.description)}">${esc(c.description)}</small>`:''}</div></div></td><td><span class="category-count">${A.Domain.active().filter(p=>p.category===c.id).length}</span></td><td><div class="actions category-actions"><button class="icon-button" data-action="edit-category" data-id="${esc(c.id)}" aria-label="Edit ${esc(c.name)}" title="Edit"><svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="m15 4 5 5M4 20l5-1L21 7l-5-5L4 14z"/></svg></button><button class="icon-button" data-action="delete-category" data-id="${esc(c.id)}" aria-label="Delete ${esc(c.name)}" title="Delete"><svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M9 6V3h6v3M6 6l1 15h10l1-15M10 10v7M14 10v7"/></svg></button></div></td></tr>`).join('')) : empty('No categories found', '', button('＋ Add Category', 'add-category', '', ''));
  }

  function suppliers() {
    return `<div class="page-heading"><div><h2>Your suppliers</h2><p>Good relationships start with the details.</p></div>${button('＋ Add Supplier','add-supplier','','')}</div><section class="panel"><div class="filters"><input aria-label="Search suppliers" placeholder="Search name, contact, email or phone…" data-filter="suppliers.q" value="${esc(A.filters.suppliers.q)}"></div><div id="suppliersResults">${supplierResults()}</div></section>`;
  }

  function supplierResults() {
    return table(['Supplier', 'Contact Person', 'Phone', 'Email', 'Products Supplied', 'Actions'], A.state.suppliers.filter(s => matches(s.name + ' ' + s.contact + ' ' + s.email + ' ' + s.phone, A.filters.suppliers.q)).map(s => `<tr><td><strong>${esc(s.name)}</strong></td><td>${esc(s.contact||'—')}</td><td>${esc(s.phone||'—')}</td><td>${esc(s.email||'—')}</td><td>${A.Domain.active().filter(p=>p.supplier===s.id).length}</td><td><div class="actions">${button('View','view-supplier',s.id)}${button('Edit','edit-supplier',s.id)}${button('Delete','delete-supplier',s.id,'danger small')}</div></td></tr>`).join(''));
  }

  function filteredHistory() {
    const f = A.filters.history;
    return [...A.state.stockTransactions].filter(t => (!f.product || t.productId === f.product) && (f.type === 'All movements' || t.type === f.type) && (!f.from || t.date.slice(0, 10) >= f.from) && (!f.to || t.date.slice(0, 10) <= f.to) && matches(t.reason, f.reason) && matches([t.productName, t.sku, t.reason, t.reference, t.supplierName, t.notes].join(' '), f.q)).sort((a, b) => b.date.localeCompare(a.date));
  }

  function history() {
    const f = A.filters.history;
    return `<div class="page-heading"><div><h2>Stock History</h2><p>A complete record of every inventory movement.</p></div>${button('Export CSV','export-history')}</div><section class="panel"><div class="filters"><input aria-label="Search history" placeholder="Search history…" data-filter="history.q" value="${esc(f.q)}"><select aria-label="Filter product" data-filter="history.product">${selectOptions(A.state.products,f.product,'All products')}</select><select aria-label="Filter movement" data-filter="history.type">${options(['All movements','Stock In','Stock Out','Adjustment'],f.type)}</select><label>From<input type="date" data-filter="history.from" value="${esc(f.from)}"></label><label>To<input type="date" data-filter="history.to" value="${esc(f.to)}"></label><input aria-label="Filter reason" placeholder="Filter by reason…" data-filter="history.reason" value="${esc(f.reason)}"></div><div id="historyResults">${table(historyHeaders,historyRows(filteredHistory()))}</div></section>`;
  }

  function low() {
    const ps = A.Domain.active();
    return `<div class="page-heading"><div><h2>Stock that needs attention</h2><p>Receive stock directly from an alert to keep quantities up to date.</p></div></div><section class="panel"><div class="panel-header"><h2>Low Stock</h2></div>${alertTable(ps.filter(p=>A.Domain.status(p)==='Low Stock'))}</section><section class="panel"><div class="panel-header"><h2>Out of Stock</h2></div>${alertTable(ps.filter(p=>p.quantity===0))}</section>`;
  }

  function productForm(p) {
    const editing = !!p;
    p = p || {
      unit: A.state.settings.defaultUnit,
      minimum: A.state.settings.minimum,
      quantity: 0,
      cost: 0,
      price: 0
    };
    return `<form data-form="product" data-id="${esc(p.id||'')}">${errorBox}<div class="form-grid"><div class="form-section">BASIC INFORMATION</div>${field('Product Name *','name',p.name,'text','required maxlength="150"')}${field('SKU / Product Code *','sku',p.sku,'text','required maxlength="60"')}<label class="field full">Category *<select name="category" required>${selectOptions(A.state.categories,p.category)}</select><small>Create categories from the Categories page.</small></label>${area('Description','description',p.description)}<div class="form-section">PRICING</div>${numeric('Cost Price *','cost',p.cost)}${numeric('Selling Price *','price',p.price)}<div class="form-section">INVENTORY</div>${editing?`<div class="notice">Current quantity: <b>${qty(p.quantity)} ${esc(p.unit)}</b><br>Use Adjust Stock to change quantities and keep a complete history.</div>`:numeric('Opening Quantity *','quantity',p.quantity)}${numeric('Minimum Stock Level *','minimum',p.minimum)}<label class="field">Unit of Measure *<select name="unit" required>${options(units,p.unit)}</select></label><div class="form-section">SUPPLIER</div><label class="field">Supplier<select name="supplier">${selectOptions(A.state.suppliers,p.supplier,'Not assigned')}</select></label>${field('Supplier Reference Code','reference',p.reference)}${formActions(editing?'Save Changes':'Add Product')}</div></form>`;
  }

  function categoryForm(c = {}) {
    return `<form data-form="category" data-id="${esc(c.id||'')}">${errorBox}<div class="form-grid">${field('Category Name *','name',c.name,'text','required maxlength="100"')}${area('Description','description',c.description)}${formActions(c.id?'Save Changes':'Add Category')}</div></form>`;
  }

  function supplierForm(s = {}) {
    return `<form data-form="supplier" data-id="${esc(s.id||'')}">${errorBox}<div class="form-grid">${field('Supplier Name *','name',s.name,'text','required maxlength="150"')}${field('Contact Person','contact',s.contact)}${field('Phone','phone',s.phone,'tel')}${field('Email','email',s.email,'email')}${area('Address','address',s.address)}${area('Notes','notes',s.notes)}<div class="notice full">Products supplied are linked automatically when you select this supplier on a product.</div>${formActions(s.id?'Save Changes':'Add Supplier')}</div></form>`;
  }

  function movementForm(direction = 'in', productId = '', adjustment = false) {
    const products = A.Domain.active(),
      p = products.find(p => p.id === productId),
      date = new Date();
    date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
    return `<form data-form="movement" data-adjustment="${adjustment}">${errorBox}<div class="form-grid"><label class="field full">Product *<select name="product" required>${selectOptions(products,productId)}</select></label>${adjustment?`<label class="field">Movement *<select name="direction">${options(['in','out'],direction).replace('>in<','>Stock In<').replace('>out<','>Stock Out<')}</select></label>`:`<input type="hidden" name="direction" value="${direction}">`}${field(direction==='in'?'Quantity Received *':'Quantity Removed *','quantity','','number','min="0.001" max="1000000000000" step="0.001" required')}${field('Date / Time *','date',date.toISOString().slice(0,16),'datetime-local','required')}<label class="field" id="movementSupplier">Supplier<select name="supplier">${selectOptions(A.state.suppliers,p?.supplier,'Not assigned')}</select></label><label class="field">Reason *<select name="reason" required>${options(direction==='in'?['Purchase','Customer Return','Opening stock','Correction','Other']:['Sale','Internal Use','Damaged','Expired','Lost','Returned to Supplier','Correction','Other'],adjustment?'Correction':direction==='in'?'Purchase':'Sale')}</select></label>${field('Reference Number','reference')}${area('Notes','notes')}<div class="stock-preview full" id="stockPreview"><div><span>Current Stock</span><strong>—</strong></div><div><span>New Stock</span><strong>—</strong></div></div><div class="form-actions full">${adjustment?button('Cancel','close-modal'):''}<button class="btn" type="submit">${adjustment?'Confirm Adjustment':direction==='in'?'Receive Stock':'Remove Stock'}</button></div></div></form>`;
  }

  function movementPage(direction) {
    return `<div class="page-heading"><div><h2>${direction==='in'?'Receive stock':'Record stock out'}</h2><p>${direction==='in'?'Add incoming inventory and keep a record of each delivery.':'Track sales, usage, returns and other stock removals.'}</p></div></div><section class="panel form-panel movement-panel">${A.Domain.active().length?movementForm(direction):empty('Add a product first','Create a product before recording stock movements.',button('＋ Add Product','add-product','',''))}</section>`;
  }

  function details(entries) {
    return `<dl class="detail-grid">${entries.map(([k,v])=>`<div><dt>${k}</dt><dd>${esc(v||'—')}</dd></div>`).join('')}</dl>`;
  }

  function viewProduct(p) {
    return details([
      ['Product', p.name],
      ['SKU', p.sku],
      ['Category', category(p.category)],
      ['Description', p.description],
      ['Cost Price', money(p.cost)],
      ['Selling Price', money(p.price)],
      ['Quantity', qty(p.quantity) + ' ' + p.unit],
      ['Minimum Stock', qty(p.minimum)],
      ['Stock Status', A.Domain.status(p)],
      ['Supplier', supplier(p.supplier)],
      ['Supplier Reference', p.reference],
      ['Added', new Date(p.createdAt).toLocaleDateString('en-ZA')]
    ]) + `<div class="form-actions">${button('Edit Product','edit-product',p.id)}${button('Adjust Stock','adjust',p.id,'')}</div>`;
  }

  function viewSupplier(s) {
    return details([
      ['Supplier', s.name],
      ['Contact Person', s.contact],
      ['Phone', s.phone],
      ['Email', s.email],
      ['Address', s.address],
      ['Notes', s.notes]
    ]) + '<h3>Products Supplied</h3>' + table(['Product', 'Quantity', 'Stock Status', 'Action'], productRows(A.Domain.active().filter(p => p.supplier === s.id), true));
  }

  function settings() {
    const s = A.state.settings;
    return `<div class="page-heading"><div><h2>Workspace settings</h2><p>Make inventory work for your business.</p></div></div><section class="panel form-panel"><form data-form="settings">${errorBox}<div class="form-grid"><div class="form-section">BUSINESS INFORMATION</div>${field('Business Name *','businessName',s.businessName,'text','required maxlength="100"')}<label class="field">Currency<select name="currency">${options(['ZAR','USD','EUR','GBP','BWP','NAD','KES','NGN','INR','AUD'],s.currency)}</select><small>Changes the display currency. Existing prices are not converted.</small></label><div class="form-section">INVENTORY DEFAULTS</div><label class="field">Default Unit<select name="defaultUnit">${options(units,s.defaultUnit)}</select></label>${numeric('Default Minimum Stock Level','minimum',s.minimum)}<label class="full"><input type="checkbox" name="alerts" ${s.alerts?'checked':''}> Show low-stock alerts on the dashboard</label><div class="form-actions full"><button class="btn" type="submit">Save Settings</button></div></div></form></section><section class="panel form-panel"><h2>Inventory data</h2><p class="notice">Your inventory is saved in this browser. Export a backup to keep a copy of all products, suppliers, categories, settings and stock history.</p><div class="actions">${button('Download Backup','backup')}${button('Clear Inventory Data','clear-data','','danger small')}</div><p style="color:var(--muted);font-size:11px">Clearing removes all sample and custom inventory records. Business settings are kept.</p></section>`;
  }
  A.UI = {
    esc,
    money,
    qty,
    category,
    supplier,
    icon,
    button,
    badge,
    empty,
    table,
    options,
    selectOptions,
    units,
    details,
    dashboard,
    products,
    productResults,
    categories,
    categoryResults,
    suppliers,
    supplierResults,
    history,
    filteredHistory,
    historyRows,
    historyHeaders,
    low,
    productForm,
    categoryForm,
    supplierForm,
    movementForm,
    movementPage,
    viewProduct,
    viewSupplier,
    settings
  };
})(window.InventoryApp);
