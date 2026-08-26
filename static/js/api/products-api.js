import { apiRequest } from './client.js';
export const listProducts = (type = '') => apiRequest(`/products/${type ? `?type=${encodeURIComponent(type)}` : ''}`);
export const createProduct = (body) => apiRequest('/products/', { method: 'POST', body });
export const updateProduct = (id, body) => apiRequest(`/products/${id}/`, { method: 'PATCH', body });

