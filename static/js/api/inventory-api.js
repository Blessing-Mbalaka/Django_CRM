import { apiRequest } from './client.js';
export const listLocations = () => apiRequest('/stock-locations/');
export const createLocation = (body) => apiRequest('/stock-locations/', { method: 'POST', body });
export const listMovements = ({ product = '', location = '' } = {}) => { const query = new URLSearchParams(); if (product) query.set('product', product); if (location) query.set('location', location); return apiRequest(`/stock-movements/${query.size ? `?${query}` : ''}`); };
export const createMovement = (body) => apiRequest('/stock-movements/', { method: 'POST', body });
export const listReorderRules = () => apiRequest('/reorder-rules/');

