# EIEAAS Inventory

Open `index.html` in a modern browser, or use VS Code Live Server. No build step, backend or installation is required. Keep the parent `assets/` folder in place because the design shares illustrations with the invoicing frontend.

## Files

- `css/style.css`: responsive layout and shared visual styling.
- `js/storage.js`: localStorage adapter and first-run sample data.
- `js/inventory.js`: validated CRUD operations, stock arithmetic and movement history.
- `js/ui.js`: screen and form templates with escaped user content.
- `js/reports.js`: report datasets, CSV export and downloads.
- `js/app.js`: navigation, events, forms, dialogs and notifications.

Data is stored under `eieaas_inventory_v1`, separately from invoicing. For consistent saved data, use the same browser and URL each time. Settings includes a JSON backup download and a confirmed action to clear all inventory data. Changing currency changes formatting, not exchange values.

Products can be archived; their transactions remain in history. SKUs remain unique, including archived products. Existing product quantities must be changed through stock movements to preserve the log. Assigned categories cannot be deleted. Deleting a supplier unassigns products but preserves its name on historical transactions.

Replace the storage adapter and connect domain operations to backend endpoints when adding server persistence. The current app is frontend-only and does not coordinate simultaneous edits from multiple users.

## Editing the design

The CSS and JavaScript use two-space indentation. Keep each CSS property on its own line, and keep selectors and functions in separate blocks.

- **Colours:** edit the variables in `:root` at the top of `css/style.css`.
- **Sidebar:** find `One shared inventory sidebar` in `css/style.css`. This section controls both widths, icon colours, active items, and the transition. The toggle handler is in `js/app.js` under `sidebarToggle`.
- **Banner:** edit the text and image path in `dashboard()` in `js/ui.js`. The image is `../assets/inventory-banner.png`; its layout is near the end of `css/style.css`.
- **Summary cards:** edit `metrics` inside `dashboard()`. The `Compact dashboard summary cards` CSS section controls their spacing.
- **Rose chart:** edit `stockRose()` in `js/ui.js`. Its `colors` array controls the slice colours; slice sizes come from product quantities. Look for `.stock-rose` and `.rose-legend` in the CSS for layout.
- **Stock In / Stock Out:** edit `movementForm()` and `movementPage()` in `js/ui.js`. `.form-panel.movement-panel` controls their full-width layout.
- **Sample inventory:** `seed()` and `extendDemo()` in `js/storage.js` define the sample records. Existing browser data is retained; changing seed values does not overwrite saved records.

The first CSS sections define shared components. Responsive rules adapt them to smaller screens. The named sections near the end contain the final inventory design adjustments, so edit those when a shared style is overridden later in the file.

After editing, refresh `inventory/index.html` and check both sidebar widths and the page you changed. No build command is needed.
