import { apiRequest } from './client.js';

export const listLibraries = () => apiRequest('/document-libraries/');
export const createLibrary = (body) => apiRequest('/document-libraries/', { method: 'POST', body });
export const listDocuments = (trash = false) => apiRequest(`/documents/${trash ? '?trash=true' : ''}`);
export const createDocument = (body) => apiRequest('/documents/', { method: 'POST', body });
export const updateDocument = (id, body) => apiRequest(`/documents/${id}/`, { method: 'PATCH', body });
export const trashDocument = (id) => apiRequest(`/documents/${id}/`, { method: 'DELETE' });
export const restoreDocument = (id) => apiRequest(`/documents/${id}/restore/`, { method: 'POST', body: {} });
export const uploadVersion = (documentId, file) => {
  const body = new FormData();
  body.append('document', documentId);
  body.append('file', file);
  return apiRequest('/document-versions/', { method: 'POST', body });
};

