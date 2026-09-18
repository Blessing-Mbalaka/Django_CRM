/* The only persistence adapter. Replace load/save when connecting a backend. */
window.InventoryApp = window.InventoryApp || {};
(function(A) {
  'use strict';
  const KEY = 'eieaas_inventory_v1';
  const defaults = {
    businessName: 'My Business',
    currency: 'ZAR',
    defaultUnit: 'Item',
    alerts: true,
    minimum: 5
  };

  function seed() {
    const now = Date.now();
    const categories = [{
      id: 'c1',
      name: 'General supplies',
      description: 'Everyday business essentials'
    }, {
      id: 'c2',
      name: 'Equipment',
      description: 'Tools and reusable equipment'
    }, {
      id: 'c3',
      name: 'Packaging',
      description: 'Materials for packing and delivery'
    }];
    const suppliers = [{
      id: 's1',
      name: 'Central Business Supplies',
      contact: 'Alex Mokoena',
      phone: '011 555 0100',
      email: 'orders@example.com',
      address: 'Johannesburg, South Africa',
      notes: 'Sample supplier'
    }, {
      id: 's2',
      name: 'Everyday Wholesale',
      contact: 'Sam Naidoo',
      phone: '021 555 0120',
      email: 'sales@example.org',
      address: 'Cape Town, South Africa',
      notes: 'Sample supplier'
    }];
    const samples = [
      ['Packing boxes', 'PKG-001', 'c3', 12, 22, 84, 'Box', 20, 's2'],
      ['Copy paper', 'SUP-001', 'c1', 65, 95, 4, 'Pack', 10, 's1'],
      ['Storage containers', 'EQP-001', 'c2', 48, 79, 32, 'Item', 8, 's1'],
      ['Adhesive tape', 'PKG-002', 'c3', 15, 25, 6, 'Item', 10, 's2'],
      ['Protective gloves', 'SUP-002', 'c1', 35, 55, 0, 'Box', 5, 's1'],
      ['Measuring tape', 'EQP-002', 'c2', 42, 75, 18, 'Piece', 5, 's2']
    ];
    const products = samples.map((p, i) => ({
      id: 'p' + (i + 1),
      name: p[0],
      sku: p[1],
      category: p[2],
      cost: p[3],
      price: p[4],
      quantity: p[5],
      unit: p[6],
      minimum: p[7],
      supplier: p[8],
      reference: '',
      description: 'Sample product — edit or remove to make this workspace your own.',
      createdAt: new Date(now - (6 - i) * 86400000).toISOString(),
      archived: false
    }));
    const stockTransactions = products.filter(p => p.quantity > 0).map((p, i) => ({
      id: 't' + i,
      productId: p.id,
      productName: p.name,
      sku: p.sku,
      type: 'Stock In',
      direction: 'in',
      quantity: p.quantity,
      previous: 0,
      next: p.quantity,
      date: p.createdAt,
      reason: 'Opening stock',
      reference: 'DEMO-' + (i + 1),
      supplierId: p.supplier,
      supplierName: suppliers.find(s => s.id === p.supplier).name,
      notes: 'Sample opening balance'
    }));
    return {
      version: 1,
      products,
      categories,
      suppliers,
      stockTransactions,
      settings: {
        ...defaults
      },
      demo: true
    };
  }
  // Add the approved sample categories once, preserving existing inventory records.
  function extendDemo(data) {
    if (!data.demo || data.demoCategoriesExpanded) return false;
    const samples = [
      ['raw-materials', 'Raw Materials', 'Timber boards', 'RAW-DEMO-001', 36, 45, 65],
      ['finished-goods', 'Finished Goods', 'Desk organisers', 'FIN-DEMO-001', 28, 30, 50],
      ['office-supplies', 'Office Supplies', 'Notebooks', 'OFF-DEMO-001', 24, 18, 30],
      ['maintenance', 'Maintenance', 'Replacement fittings', 'MNT-DEMO-001', 20, 12, 22],
      ['cleaning', 'Cleaning Supplies', 'Cleaning cloths', 'CLN-DEMO-001', 16, 8, 15]
    ];
    const uniqueId = (base, items) => {
      let id = base,
        i = 1;
      while (items.some(item => item.id === id)) id = base + '-' + i++;
      return id;
    };
    samples.forEach(([key, name, productName, baseSku, quantity, cost, price]) => {
      let category = data.categories.find(c => c.name.toLowerCase() === name.toLowerCase());
      if (!category) {
        category = {
          id: uniqueId('demo-category-' + key, data.categories),
          name,
          description: 'Sample inventory category'
        };
        data.categories.push(category);
      }
      let sku = baseSku,
        suffix = 1;
      while (data.products.some(p => p.sku.toLowerCase() === sku.toLowerCase())) sku = baseSku + '-' + suffix++;
      const product = {
        id: uniqueId('demo-product-' + key, data.products),
        name: productName,
        sku,
        category: category.id,
        cost,
        price,
        quantity,
        unit: 'Item',
        minimum: 5,
        supplier: '',
        reference: '',
        description: 'Sample product ? edit or remove to make this workspace your own.',
        createdAt: new Date().toISOString(),
        archived: false
      };
      data.products.push(product);
      data.stockTransactions.push({
        id: uniqueId('demo-stock-' + key, data.stockTransactions),
        productId: product.id,
        productName,
        sku,
        type: 'Stock In',
        direction: 'in',
        quantity,
        previous: 0,
        next: quantity,
        date: product.createdAt,
        reason: 'Opening stock',
        reference: 'DEMO-EXPANDED',
        supplierId: '',
        supplierName: '',
        notes: 'Sample opening balance'
      });
    });
    data.demoCategoriesExpanded = true;
    return true;
  }
  A.Storage = {
    key: KEY,
    defaults,
    load() {
      try {
        const raw = localStorage.getItem(KEY);
        if (!raw) {
          const data = seed();
          extendDemo(data);
          localStorage.setItem(KEY, JSON.stringify(data));
          return data;
        }
        const data = JSON.parse(raw);
        if (!['products', 'categories', 'suppliers', 'stockTransactions'].every(k => Array.isArray(data[k])) || !data.settings) throw new Error('Invalid saved inventory');
        data.settings = {
          ...defaults,
          ...data.settings
        };
        if (extendDemo(data)) localStorage.setItem(KEY, JSON.stringify(data));
        return data;
      } catch (error) {
        throw new Error('Saved inventory could not be opened. Check that browser storage is available. Your saved data has not been overwritten.');
      }
    },
    save(data) {
      try {
        localStorage.setItem(KEY, JSON.stringify(data));
      } catch (_) {
        throw new Error('Could not save changes. Browser storage may be full or unavailable.');
      }
    }
  };
})(window.InventoryApp);
