import { apiRequest } from './client.js';
export const listAccounts = () => apiRequest('/accounts/');
export const createAccount = (body) => apiRequest('/accounts/', { method: 'POST', body });
export const listJournals = () => apiRequest('/journals/');
export const createJournal = (body) => apiRequest('/journals/', { method: 'POST', body });
export const postJournal = (id) => apiRequest(`/journals/${id}/post/`, { method: 'POST', body: {} });
export const reverseJournal = (id, body) => apiRequest(`/journals/${id}/reverse/`, { method: 'POST', body });
