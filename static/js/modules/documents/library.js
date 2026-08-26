import { collection } from '../../api/client.js';
import { createDocument, createLibrary, listDocuments, listLibraries, restoreDocument, trashDocument, updateDocument, uploadVersion } from '../../api/documents-api.js';
import { escapeHtml, formatDate, setBusy, setFeedback } from '../ui.js';

const state = { library: null, documents: [], view: 'files', query: '' };
const rows = document.getElementById('documentRows');

function formatBytes(bytes = 0) {
  if (!bytes) return '—';
  const units = ['B', 'KB', 'MB', 'GB'];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / (1024 ** index)).toFixed(index ? 1 : 0)} ${units[index]}`;
}

function visibleDocuments() {
  let items = [...state.documents];
  if (state.view === 'favourites') items = items.filter((item) => item.is_favourite);
  if (state.view === 'recent') items.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));
  if (state.query) items = items.filter((item) => item.title.toLowerCase().includes(state.query));
  return items;
}

function render() {
  const items = visibleDocuments();
  document.getElementById('documentCount').textContent = `${items.length} ${items.length === 1 ? 'file' : 'files'}`;
  if (!items.length) {
    rows.innerHTML = `<tr><td colspan="6" class="module-empty"><i class="bi bi-folder2-open"></i><strong>No documents here</strong><span>${state.view === 'trash' ? 'Deleted files will appear here.' : 'Upload the first file to this library.'}</span></td></tr>`;
    return;
  }
  rows.innerHTML = items.map((item) => {
    const version = item.latest_version;
    const action = state.view === 'trash'
      ? `<button class="table-action" data-restore="${item.id}"><i class="bi bi-arrow-counterclockwise"></i> Restore</button>`
      : `<button class="icon-button ${item.is_favourite ? 'is-favourite' : ''}" data-favourite="${item.id}" title="Favourite"><i class="bi bi-star${item.is_favourite ? '-fill' : ''}"></i></button><button class="icon-button" data-trash="${item.id}" title="Move to trash"><i class="bi bi-trash3"></i></button>`;
    const download = version?.file ? `<a class="document-name" href="${escapeHtml(version.file)}" target="_blank" rel="noopener"><i class="bi bi-file-earmark-text"></i><span>${escapeHtml(item.title)}<small>${escapeHtml(version.original_name)}</small></span></a>` : `<span class="document-name"><i class="bi bi-file-earmark"></i><span>${escapeHtml(item.title)}<small>No file version</small></span></span>`;
    return `<tr><td>${download}</td><td><span class="classification classification-${item.classification}">${escapeHtml(item.classification)}</span></td><td>${version ? `v${version.version_number}` : '—'}</td><td>${formatBytes(version?.size)}</td><td>${formatDate(item.updated_at?.slice(0, 10))}</td><td class="text-end text-nowrap">${action}</td></tr>`;
  }).join('');
}

async function ensureLibrary() {
  const libraries = collection(await listLibraries());
  state.library = libraries[0] || await createLibrary({ name: 'Company Documents', scope: 'personal' });
  document.getElementById('libraryName').textContent = state.library.name;
}

async function load() {
  try {
    await ensureLibrary();
    state.documents = collection(await listDocuments(state.view === 'trash'));
    render();
  } catch (error) {
    rows.innerHTML = '<tr><td colspan="6" class="module-empty text-danger">Unable to load documents.</td></tr>';
    setFeedback(error.message, 'danger');
  }
}

document.querySelectorAll('[data-document-view]').forEach((button) => button.addEventListener('click', async () => {
  document.querySelectorAll('[data-document-view]').forEach((item) => item.classList.remove('active'));
  button.classList.add('active');
  state.view = button.dataset.documentView;
  await load();
}));

document.getElementById('documentSearch').addEventListener('input', (event) => { state.query = event.target.value.trim().toLowerCase(); render(); });
document.getElementById('refreshDocuments').addEventListener('click', load);

rows.addEventListener('click', async (event) => {
  const favourite = event.target.closest('[data-favourite]');
  const trash = event.target.closest('[data-trash]');
  const restore = event.target.closest('[data-restore]');
  try {
    if (favourite) {
      const item = state.documents.find((document) => document.id === Number(favourite.dataset.favourite));
      await updateDocument(item.id, { is_favourite: !item.is_favourite });
      setFeedback(item.is_favourite ? 'Removed from favourites.' : 'Added to favourites.', 'success');
    } else if (trash && window.confirm('Move this document to Trash?')) {
      await trashDocument(trash.dataset.trash);
      setFeedback('Document moved to Trash.', 'success');
    } else if (restore) {
      await restoreDocument(restore.dataset.restore);
      setFeedback('Document restored.', 'success');
    } else return;
    await load();
  } catch (error) { setFeedback(error.message, 'danger'); }
});

document.getElementById('documentUploadForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  const button = document.getElementById('uploadDocumentButton');
  const file = document.getElementById('documentFile').files[0];
  setBusy(button, true, 'Uploading…');
  try {
    const documentRecord = await createDocument({ library: state.library.id, title: document.getElementById('documentTitle').value.trim(), classification: document.getElementById('documentClassification').value });
    await uploadVersion(documentRecord.id, file);
    bootstrap.Modal.getOrCreateInstance(document.getElementById('uploadModal')).hide();
    event.target.reset();
    setFeedback('Document uploaded successfully.', 'success');
    await load();
  } catch (error) { setFeedback(error.message, 'danger'); }
  finally { setBusy(button, false); }
});

load();

