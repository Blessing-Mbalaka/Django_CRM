import { apiRequest } from './client.js';

export const listBoards = () => apiRequest('/task-boards/');
export const createBoard = (body) => apiRequest('/task-boards/', { method: 'POST', body });
export const getBoard = (id) => apiRequest(`/task-boards/${id}/`);
export const listTasks = (boardId) => apiRequest(`/tasks/?board=${encodeURIComponent(boardId)}`);
export const createTask = (body) => apiRequest('/tasks/', { method: 'POST', body });
export const updateTask = (id, body) => apiRequest(`/tasks/${id}/`, { method: 'PATCH', body });
export const deleteTask = (id) => apiRequest(`/tasks/${id}/`, { method: 'DELETE' });
export const moveTask = (id, column, position = 0) => apiRequest(`/tasks/${id}/move/`, { method: 'POST', body: { column, position } });

