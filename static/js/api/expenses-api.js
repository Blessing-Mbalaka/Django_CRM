import { apiRequest } from './client.js';

export const listExpenses = (status = '') => apiRequest(`/expenses/${status ? `?status=${encodeURIComponent(status)}` : ''}`);
export const createExpense = (body) => apiRequest('/expenses/', { method: 'POST', body });
export const submitExpense = (id) => apiRequest(`/expenses/${id}/submit/`, { method: 'POST', body: {} });
export const approveExpense = (id, comment = '') => apiRequest(`/expenses/${id}/approve/`, { method: 'POST', body: { comment } });
export const rejectExpense = (id, comment = '') => apiRequest(`/expenses/${id}/reject/`, { method: 'POST', body: { comment } });
export const listCategories = () => apiRequest('/expense-categories/');
export const createCategory = (name) => apiRequest('/expense-categories/', { method: 'POST', body: { name, is_active: true } });

