import { apiRequest } from './client.js';

export const listUsers = () => apiRequest('/users/');
export const listPayrollEmployees = () => apiRequest('/payroll-employees/');
export const createPayrollEmployee = (body) => apiRequest('/payroll-employees/', { method: 'POST', body });
export const listPayRuns = () => apiRequest('/pay-runs/');
export const createPayRun = (body) => apiRequest('/pay-runs/', { method: 'POST', body });
export const approvePayRun = (id) => apiRequest(`/pay-runs/${id}/approve/`, { method: 'POST', body: {} });
export const markPayRunPaid = (id) => apiRequest(`/pay-runs/${id}/mark-paid/`, { method: 'POST', body: {} });
