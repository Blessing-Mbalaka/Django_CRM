import { apiRequest } from './client.js';
export const listSalesOrders = () => apiRequest('/sales-orders/');
export const createSalesOrder = (body) => apiRequest('/sales-orders/', { method: 'POST', body });
export const addSalesOrderLine = (body) => apiRequest('/sales-order-lines/', { method: 'POST', body });
export const confirmSalesOrder = (id) => apiRequest(`/sales-orders/${id}/confirm/`, { method: 'POST', body: {} });
export const invoiceSalesOrder = (id, dueDate) => apiRequest(`/sales-orders/${id}/invoice/`, { method: 'POST', body: { due_date: dueDate } });
export const fulfilSalesOrder = (id, body) => apiRequest(`/sales-orders/${id}/fulfil/`, { method: 'POST', body });

