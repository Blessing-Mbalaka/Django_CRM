(function (API, schema) {
  const configNode = document.querySelector('#academy-management-data');
  if (!configNode) return;
  const config = JSON.parse(configNode.textContent);
  const root = document.querySelector('#academyApp');
  const dialog = document.querySelector('#academyManageDialog');
  const form = document.querySelector('#academyManageForm');
  const fieldsRoot = document.querySelector('#academyManageFields');
  const errorsRoot = document.querySelector('#academyManageErrors');
  const title = document.querySelector('#academyManageDialogTitle');
  let currentEntity = 'courses'; let currentItems = []; let editingId = null; let csvMode = false; let csvValidated = false;
  const esc = value => String(value ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  const labelFor = item => item.title || item.name || item.prompt || item.label || item.display_name || item.slug || `#${item.id}`;
  const groups = () => [...new Set(Object.values(schema.entities).map(item => item.group))];

  async function options(field) {
    if (field.type === 'choice') return (config.choices[field.choice] || []).map(([value,label]) => ({ id:value, label }));
    if (field.type !== 'relation') return [];
    return (await API.list(config.endpoints[field.source])).map(item => ({ id:item.id, label:labelFor(item) }));
  }
  async function input(field, value) {
    const required = field.required || (!field.optional && field.type === 'relation') ? ' required' : '';
    if (field.type === 'checkbox') return `<label class="manage-check"><input name="${field.name}" type="checkbox" ${value ? 'checked' : ''}> ${esc(field.label)}</label>`;
    if (field.type === 'textarea') return `<label>${esc(field.label)}<textarea name="${field.name}"${required}>${esc(value)}</textarea></label>`;
    if (field.type === 'relation' || field.type === 'choice') {
      const items = await options(field);
      return `<label>${esc(field.label)}<select name="${field.name}"${required}><option value="">${field.optional ? 'None' : 'Choose'}</option>${items.map(item => `<option value="${esc(item.id)}" ${String(value ?? '') === String(item.id) ? 'selected' : ''}>${esc(item.label)}</option>`).join('')}</select></label>`;
    }
    const shown = field.type === 'datetime-local' && value ? String(value).slice(0,16) : (field.type === 'json' ? JSON.stringify(value || []) : value ?? '');
    return `<label>${esc(field.label)}<input name="${field.name}" type="${field.type === 'json' ? 'text' : field.type}" value="${esc(shown)}"${required}></label>`;
  }
  async function open(entityKey, id = null) {
    csvMode = false; csvValidated = false; document.querySelector('#academyManageSave').textContent = 'Save';
    currentEntity = entityKey; editingId = id;
    const entity = schema.entities[entityKey];
    const item = id ? currentItems.find(row => row.id === id) || await API.request(`${config.endpoints[entityKey]}${id}/`) : {};
    title.textContent = `${id ? 'Edit' : 'Add'} ${entity.label}`;
    fieldsRoot.innerHTML = (await Promise.all(entity.fields.map(field => input(field, item[field.name])))).join('');
    errorsRoot.hidden = true; errorsRoot.textContent = '';
    dialog.showModal();
  }
  function openFundingImport() {
    currentEntity = 'funding'; editingId = null; csvMode = true; csvValidated = false;
    title.textContent = 'Import funding opportunities';
    fieldsRoot.innerHTML = `<label>Funding CSV file<input name="funding_csv" type="file" accept=".csv,text/csv" required></label><p><a class="btn secondary small" href="${config.endpoints.funding}csv-template/">Download CSV template</a></p>`;
    errorsRoot.hidden = true; errorsRoot.textContent = '';
    document.querySelector('#academyManageSave').textContent = 'Preview CSV'; dialog.showModal();
  }
  function recordData() {
    const entity = schema.entities[currentEntity]; const data = {}; let hasFile = false;
    entity.fields.forEach(field => {
      const control = form.elements[field.name];
      if (field.type === 'file') { if (control.files[0]) hasFile = true; return; }
      if (field.type === 'checkbox') data[field.name] = control.checked;
      else if (field.type === 'number') { if (control.value === '') { if (field.optional) data[field.name] = null; return; } data[field.name] = Number(control.value); }
      else if (field.type === 'relation') data[field.name] = control.value === '' ? null : Number(control.value);
      else if (field.type === 'json') { try { data[field.name] = JSON.parse(control.value || '[]'); } catch (_) { throw new Error(`${field.label} must be valid JSON.`); } }
      else data[field.name] = control.value;
    });
    if (!hasFile) return data;
    const output = new FormData(); Object.entries(data).forEach(([key,value]) => output.append(key, typeof value === 'object' ? JSON.stringify(value) : value));
    entity.fields.filter(field => field.type === 'file').forEach(field => { const file = form.elements[field.name].files[0]; if (file) output.append(field.name, file); });
    return output;
  }
  function renderRows() {
    const entity = schema.entities[currentEntity];
    const rows = currentItems.map(item => `<article class="manage-row"><div><strong>${esc(labelFor(item))}</strong><small>${esc(item.slug || item.status || (item.is_published === false ? 'Draft' : ''))}</small></div><div><button class="btn secondary small" data-manage-edit="${item.id}">Edit</button><button class="btn secondary small danger" data-manage-remove="${item.id}">Archive / remove</button></div></article>`).join('');
    document.querySelector('#academyManageList').innerHTML = rows || '<section class="panel"><p>No records yet. Use Add to create the first one.</p></section>';
    document.querySelector('#academyManageEntityTitle').textContent = entity.label;
  }
  async function select(entityKey) { currentEntity = entityKey; currentItems = await API.list(config.endpoints[entityKey]); renderRows(); const csv = document.querySelector('[data-funding-import]'); if (csv) csv.hidden = entityKey !== 'funding'; }
  async function render() {
    document.querySelector('#pageTitle').textContent = 'Manage Academy';
    document.querySelectorAll('[data-route]').forEach(button => button.classList.toggle('active', button.dataset.route === 'manage'));
    root.innerHTML = `<section class="banner manage-banner"><div class="banner-copy"><span class="eyebrow">ACADEMY CONTROL CENTRE</span><h2>Manage Academy content</h2><p>Create, publish, edit and safely archive learning and support content without leaving the SME workspace.</p></div></section><div class="manage-layout"><aside class="panel manage-menu">${groups().map(group => `<section><h3>${esc(group)}</h3>${Object.entries(schema.entities).filter(([,item]) => item.group === group).map(([key,item]) => `<button type="button" data-manage-entity="${key}">${esc(item.label)}</button>`).join('')}</section>`).join('')}</aside><section><div class="page-heading"><div><h2 id="academyManageEntityTitle">Content</h2><p>Changes are immediately backed by the Academy database.</p></div><div class="manage-heading-actions"><button class="btn secondary" data-funding-import hidden>Import funding CSV</button><button class="btn" data-manage-add>Add item</button></div></div><div id="academyManageList"></div></section></div>`;
    await select(currentEntity);
  }
  root.addEventListener('click', async event => {
    const entity = event.target.closest('[data-manage-entity]'); if (entity) return select(entity.dataset.manageEntity);
    if (event.target.closest('[data-manage-add]')) return open(currentEntity);
    if (event.target.closest('[data-funding-import]')) return openFundingImport();
    const edit = event.target.closest('[data-manage-edit]'); if (edit) return open(currentEntity, Number(edit.dataset.manageEdit));
    const remove = event.target.closest('[data-manage-remove]');
    if (remove && window.confirm('Archive or remove this record? Learner history will be preserved.')) { await API.remove(config.endpoints[currentEntity], Number(remove.dataset.manageRemove)); await select(currentEntity); }
  });
  form.addEventListener('submit', async event => {
    event.preventDefault(); const save = document.querySelector('#academyManageSave'); save.disabled = true;
    try {
      if (csvMode) {
        const payload = new FormData(); payload.append('file', form.elements.funding_csv.files[0]);
        const result = await API.request(`${config.endpoints.funding}${csvValidated ? 'import-csv/' : 'preview-csv/'}`, { method: 'POST', body: payload });
        if (!csvValidated) { csvValidated = true; errorsRoot.hidden = false; errorsRoot.textContent = `${result.rows.length} valid row(s). Review complete; choose Import to save them.`; save.textContent = 'Import CSV'; }
        else { dialog.close(); await select('funding'); }
      } else { await API.save(config.endpoints[currentEntity], recordData(), editingId); dialog.close(); await select(currentEntity); }
    }
    catch (error) { errorsRoot.hidden = false; errorsRoot.textContent = Object.entries(error.fields || {}).map(([key,value]) => `${key}: ${Array.isArray(value) ? value.join(' ') : value}`).join(' ') || error.message; }
    finally { save.disabled = false; }
  });
  dialog.querySelectorAll('[data-dialog-close]').forEach(button => button.addEventListener('click', () => dialog.close()));
  window.AcademyAdmin = { render, open, openFundingImport, canManage: true };
})(window.AcademyAdminAPI, window.AcademyAdminSchema);
