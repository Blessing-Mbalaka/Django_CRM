import { collection } from '../../api/client.js';
import { createBoard, createTask, getBoard, listBoards, listTasks, moveTask } from '../../api/tasks-api.js';
import { escapeHtml, formatDate, setBusy, setFeedback } from '../ui.js';

const state = { boards: [], board: null, tasks: [], draggedTaskId: null, pointerDrag: null };
const boardElement = document.getElementById('kanbanBoard');
const boardSelect = document.getElementById('boardSelect');

function taskCard(task, columnIndex) {
  const maxIndex = state.board.columns.length - 1;
  return `<article class="kanban-card" draggable="true" data-task-id="${task.id}" tabindex="0"><div class="task-card-top"><span class="priority priority-${task.priority}">${escapeHtml(task.priority)}</span><span class="task-drag-handle" data-drag-handle role="button" aria-label="Drag ${escapeHtml(task.title)}" title="Drag task"><i class="bi bi-grip-vertical"></i></span></div><h3>${escapeHtml(task.title)}</h3>${task.description ? `<p>${escapeHtml(task.description)}</p>` : ''}<div class="task-card-meta"><span><i class="bi bi-calendar3"></i>${formatDate(task.due_date)}</span><div class="task-move-controls"><button ${columnIndex === 0 ? 'disabled' : ''} data-move-direction="-1" title="Move left" aria-label="Move ${escapeHtml(task.title)} left"><i class="bi bi-arrow-left"></i></button><button ${columnIndex === maxIndex ? 'disabled' : ''} data-move-direction="1" title="Move right" aria-label="Move ${escapeHtml(task.title)} right"><i class="bi bi-arrow-right"></i></button></div></div></article>`;
}

function render() {
  if (!state.board) { boardElement.innerHTML = '<div class="module-empty w-100">Create a board to begin.</div>'; return; }
  boardElement.innerHTML = state.board.columns.map((column, index) => {
    const tasks = state.tasks.filter((task) => task.column === column.id);
    return `<section class="kanban-column" data-column-id="${column.id}"><header><div><span class="column-dot"></span><h2>${escapeHtml(column.name)}</h2></div><span class="column-count">${tasks.length}</span></header><div class="kanban-card-list">${tasks.length ? tasks.map((task) => taskCard(task, index)).join('') : '<div class="kanban-empty">Drop tasks here</div>'}</div></section>`;
  }).join('');
}

async function selectBoard(id) {
  state.board = await getBoard(id);
  state.tasks = collection(await listTasks(id));
  boardSelect.value = String(id);
  render();
}

async function load() {
  try {
    state.boards = collection(await listBoards());
    if (!state.boards.length) state.boards = [await createBoard({ name: 'My Work', description: 'Daily SME operations' })];
    boardSelect.innerHTML = state.boards.map((board) => `<option value="${board.id}">${escapeHtml(board.name)}</option>`).join('');
    await selectBoard(state.board?.id || state.boards[0].id);
  } catch (error) { boardElement.innerHTML = '<div class="module-empty text-danger">Unable to load the board.</div>'; setFeedback(error.message, 'danger'); }
}

boardSelect.addEventListener('change', () => selectBoard(boardSelect.value));
document.getElementById('newBoardButton').addEventListener('click', async () => {
  const name = window.prompt('Board name');
  if (!name?.trim()) return;
  try { const board = await createBoard({ name: name.trim() }); state.boards.push(board); await load(); await selectBoard(board.id); setFeedback('Board created.', 'success'); } catch (error) { setFeedback(error.message, 'danger'); }
});

document.getElementById('taskForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  const button = document.getElementById('createTaskButton');
  setBusy(button, true, 'Creating…');
  try {
    const dueDate = document.getElementById('taskDueDate').value;
    const payload = { board: state.board.id, column: state.board.columns[1]?.id || state.board.columns[0].id, title: document.getElementById('taskTitle').value.trim(), description: document.getElementById('taskDescription').value.trim(), priority: document.getElementById('taskPriority').value };
    if (dueDate) payload.due_date = dueDate;
    await createTask(payload);
    bootstrap.Modal.getOrCreateInstance(document.getElementById('taskModal')).hide(); event.target.reset(); setFeedback('Task created.', 'success'); await selectBoard(state.board.id);
  } catch (error) { setFeedback(error.message, 'danger'); } finally { setBusy(button, false); }
});

async function move(taskId, columnId, position = 0) {
  try { await moveTask(taskId, columnId, position); await selectBoard(state.board.id); setFeedback('Task position saved.', 'success'); } catch (error) { setFeedback(error.message, 'danger'); }
}

function dropPosition(column, clientY, taskId) {
  const cards = [...column.querySelectorAll('.kanban-card')].filter((card) => card.dataset.taskId !== String(taskId));
  const index = cards.findIndex((card) => clientY < card.getBoundingClientRect().top + card.getBoundingClientRect().height / 2);
  return index === -1 ? cards.length : index;
}

function clearDragState() {
  boardElement.querySelectorAll('.is-drop-target').forEach((column) => column.classList.remove('is-drop-target'));
  boardElement.querySelectorAll('.is-dragging').forEach((card) => card.classList.remove('is-dragging'));
  document.body.classList.remove('kanban-is-dragging');
  state.draggedTaskId = null;
  state.pointerDrag = null;
}

function markDropTarget(column) {
  boardElement.querySelectorAll('.is-drop-target').forEach((item) => item.classList.toggle('is-drop-target', item === column));
}

boardElement.addEventListener('click', (event) => {
  const button = event.target.closest('[data-move-direction]'); if (!button) return;
  const card = button.closest('[data-task-id]'); const task = state.tasks.find((item) => item.id === Number(card.dataset.taskId));
  const index = state.board.columns.findIndex((column) => column.id === task.column) + Number(button.dataset.moveDirection);
  if (state.board.columns[index]) move(task.id, state.board.columns[index].id, 0);
});
// Native HTML drag-and-drop remains available when dragging the card body.
boardElement.addEventListener('dragstart', (event) => {
  const card = event.target.closest('[data-task-id]');
  if (!card || !event.dataTransfer) return;
  state.draggedTaskId = card.dataset.taskId;
  event.dataTransfer.effectAllowed = 'move';
  event.dataTransfer.setData('text/plain', state.draggedTaskId);
  requestAnimationFrame(() => card.classList.add('is-dragging'));
});
boardElement.addEventListener('dragover', (event) => {
  const column = event.target.closest('[data-column-id]');
  if (!column) return;
  event.preventDefault();
  if (event.dataTransfer) event.dataTransfer.dropEffect = 'move';
  markDropTarget(column);
});
boardElement.addEventListener('drop', (event) => {
  const column = event.target.closest('[data-column-id]');
  if (!column) return;
  event.preventDefault();
  const taskId = event.dataTransfer?.getData('text/plain') || state.draggedTaskId;
  const position = dropPosition(column, event.clientY, taskId);
  clearDragState();
  if (taskId) move(taskId, column.dataset.columnId, position);
});
boardElement.addEventListener('dragend', clearDragState);

// Pointer dragging on the grip supports mouse, touch and pen consistently.
boardElement.addEventListener('pointerdown', (event) => {
  const handle = event.target.closest('[data-drag-handle]');
  if (!handle) return;
  const card = handle.closest('[data-task-id]');
  state.pointerDrag = { pointerId: event.pointerId, taskId: card.dataset.taskId, column: null, clientY: event.clientY };
  handle.setPointerCapture(event.pointerId);
  card.classList.add('is-dragging');
  document.body.classList.add('kanban-is-dragging');
  event.preventDefault();
});
boardElement.addEventListener('pointermove', (event) => {
  if (!state.pointerDrag || state.pointerDrag.pointerId !== event.pointerId) return;
  const column = document.elementFromPoint(event.clientX, event.clientY)?.closest('[data-column-id]');
  state.pointerDrag.column = column;
  state.pointerDrag.clientY = event.clientY;
  markDropTarget(column);
  event.preventDefault();
});
boardElement.addEventListener('pointerup', (event) => {
  if (!state.pointerDrag || state.pointerDrag.pointerId !== event.pointerId) return;
  const { taskId, column, clientY } = state.pointerDrag;
  const position = column ? dropPosition(column, clientY, taskId) : 0;
  clearDragState();
  if (column) move(taskId, column.dataset.columnId, position);
});
boardElement.addEventListener('pointercancel', clearDragState);

load();
