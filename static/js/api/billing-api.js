import { apiRequest } from './client.js';

export const listInvoices = () => apiRequest('/invoices/');
export const createInvoice = (body) => apiRequest('/invoices/', { method: 'POST', body });
export const addInvoiceLine = (body) => apiRequest('/invoice-lines/', { method: 'POST', body });
export const issueInvoice = (id) => apiRequest(`/invoices/${id}/issue/`, { method: 'POST', body: {} });
export const recordPayment = (body) => apiRequest('/payments/', { method: 'POST', body });
export const listClients = () => apiRequest('/clients/');

