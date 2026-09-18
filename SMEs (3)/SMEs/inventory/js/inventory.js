/* Domain operations: validation, stock arithmetic and atomic persistence. */
(function(A) {
  'use strict';
  const id = () => crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36) + Math.random().toString(36).slice(2);
  const round = n => Math.round((n + Number.EPSILON) * 1000) / 1000;
  const text = value => String(value ?? '').trim();

  function number(value, label) {
    const n = Number(value);
    if (value === '' || !Number.isFinite(n) || n < 0 || n > 1e12) throw new Error(label + ' must be a valid non-negative number.');
    return round(n);
  }

  function commit(change) {
    const draft = JSON.parse(JSON.stringify(A.state));
    const result = change(draft);
    A.Storage.save(draft);
    A.state = draft;
    return result;
  }

  function getProduct(state, productId) {
    const p = state.products.find(p => p.id === productId);
    if (!p || p.archived) throw new Error('This product is no longer active.');
    return p;
  }

  function transaction(state, p, data) {
    const amount = number(data.quantity, 'Quantity');
    if (amount <= 0) throw new Error('Quantity must be greater than zero.');
    if (!['in', 'out'].includes(data.direction)) throw new Error('Select Stock In or Stock Out.');
    if (!text(data.reason)) throw new Error('Enter a reason for this movement.');
    if (data.direction === 'out' && amount > p.quantity) throw new Error('Insufficient stock. Only ' + p.quantity + ' ' + p.unit + ' available.');
    const date = new Date(data.date || Date.now());
    if (!Number.isFinite(date.getTime())) throw new Error('Enter a valid date.');
    const previous = p.quantity,
      next = round(previous + (data.direction === 'in' ? amount : -amount));
    if (next > 1e12) throw new Error('Resulting stock quantity is too large.');
    const supplier = state.suppliers.find(s => s.id === data.supplier);
    state.stockTransactions.push({
      id: id(),
      productId: p.id,
      productName: p.name,
      sku: p.sku,
      type: data.adjustment ? 'Adjustment' : data.direction === 'in' ? 'Stock In' : 'Stock Out',
      direction: data.direction,
      quantity: amount,
      previous,
      next,
      date: date.toISOString(),
      reason: text(data.reason),
      reference: text(data.reference),
      supplierId: supplier?.id || '',
      supplierName: supplier?.name || '',
      notes: text(data.notes)
    });
    p.quantity = next;
  }
  A.Domain = {
    active: () => A.state.products.filter(p => !p.archived),
    status: p => p.quantity === 0 ? 'Out of Stock' : p.quantity <= p.minimum ? 'Low Stock' : 'In Stock',
    summary() {
      const ps = this.active();
      return {
        products: ps.length,
        units: round(ps.reduce((n, p) => n + p.quantity, 0)),
        value: ps.reduce((n, p) => n + p.quantity * p.cost, 0),
        low: ps.filter(p => this.status(p) === 'Low Stock').length,
        out: ps.filter(p => p.quantity === 0).length,
        inStock: ps.filter(p => this.status(p) === 'In Stock').length
      };
    },
    saveProduct(data, productId) {
      return commit(state => {
        const name = text(data.name),
          sku = text(data.sku);
        if (!name || !sku) throw new Error('Product name and SKU are required.');
        if (state.products.some(p => p.id !== productId && p.sku.toLowerCase() === sku.toLowerCase())) throw new Error('SKU already exists, including archived products.');
        if (!state.categories.some(c => c.id === data.category)) throw new Error('Choose a category. Create one on the Categories page first.');
        if (data.supplier && !state.suppliers.some(s => s.id === data.supplier)) throw new Error('Choose an existing supplier.');
        const values = {
          name,
          sku,
          category: data.category,
          description: text(data.description),
          cost: number(data.cost, 'Cost price'),
          price: number(data.price, 'Selling price'),
          minimum: number(data.minimum, 'Minimum stock level'),
          unit: text(data.unit),
          supplier: data.supplier || '',
          reference: text(data.reference)
        };
        if (!values.unit) throw new Error('Select a unit of measure.');
        if (productId) {
          Object.assign(getProduct(state, productId), values);
          return productId;
        }
        const p = {
          ...values,
          id: id(),
          quantity: 0,
          createdAt: new Date().toISOString(),
          archived: false
        };
        state.products.push(p);
        const opening = number(data.quantity, 'Opening quantity');
        if (opening > 0) transaction(state, p, {
          direction: 'in',
          quantity: opening,
          reason: 'Opening stock',
          supplier: p.supplier
        });
        return p.id;
      });
    },
    archiveProduct(productId) {
      commit(state => {
        getProduct(state, productId).archived = true;
      });
    },
    move(data) {
      commit(state => transaction(state, getProduct(state, data.product), data));
    },
    saveCategory(data, categoryId) {
      commit(state => {
        const name = text(data.name);
        if (!name) throw new Error('Category name is required.');
        if (state.categories.some(c => c.id !== categoryId && c.name.toLowerCase() === name.toLowerCase())) throw new Error('Category already exists.');
        if (categoryId) {
          const c = state.categories.find(c => c.id === categoryId);
          if (!c) throw new Error('Category not found.');
          Object.assign(c, {
            name,
            description: text(data.description)
          });
        } else state.categories.push({
          id: id(),
          name,
          description: text(data.description)
        });
      });
    },
    deleteCategory(categoryId) {
      commit(state => {
        if (state.products.some(p => p.category === categoryId)) throw new Error('This category is assigned to products. Reassign them before deleting it.');
        state.categories = state.categories.filter(c => c.id !== categoryId);
      });
    },
    saveSupplier(data, supplierId) {
      commit(state => {
        const name = text(data.name);
        if (!name) throw new Error('Supplier name is required.');
        if (data.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) throw new Error('Enter a valid email address.');
        const values = {
          name,
          contact: text(data.contact),
          phone: text(data.phone),
          email: text(data.email),
          address: text(data.address),
          notes: text(data.notes)
        };
        if (supplierId) {
          const s = state.suppliers.find(s => s.id === supplierId);
          if (!s) throw new Error('Supplier not found.');
          Object.assign(s, values);
        } else state.suppliers.push({
          ...values,
          id: id()
        });
      });
    },
    deleteSupplier(supplierId) {
      commit(state => {
        state.suppliers = state.suppliers.filter(s => s.id !== supplierId);
        state.products.forEach(p => {
          if (p.supplier === supplierId) p.supplier = '';
        });
      });
    },
    saveSettings(data) {
      commit(state => {
        if (!text(data.businessName)) throw new Error('Business name is required.');
        if (!['ZAR', 'USD', 'EUR', 'GBP', 'BWP', 'NAD', 'KES', 'NGN', 'INR', 'AUD'].includes(data.currency)) throw new Error('Select a supported currency.');
        state.settings = {
          businessName: text(data.businessName),
          currency: data.currency,
          defaultUnit: data.defaultUnit,
          minimum: number(data.minimum, 'Default minimum level'),
          alerts: data.alerts === 'on'
        };
      });
    },
    clearData() {
      commit(state => {
        state.products = [];
        state.categories = [];
        state.suppliers = [];
        state.stockTransactions = [];
        state.demo = false;
      });
    }
  };
})(window.InventoryApp);
