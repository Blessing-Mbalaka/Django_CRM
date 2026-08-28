(function () {
  'use strict';

  const tiles = Array.from(document.querySelectorAll('[data-suite-group]'));
  const panels = Array.from(document.querySelectorAll('[data-suite-panel]'));
  const placeholder = document.querySelector('[data-suite-placeholder]');

  if (!tiles.length) return;

  function closeGroups() {
    tiles.forEach((tile) => {
      tile.classList.remove('is-active');
      tile.setAttribute('aria-expanded', 'false');
    });
    panels.forEach((panel) => { panel.hidden = true; });
    if (placeholder) placeholder.hidden = false;
  }

  function openGroup(key, shouldScroll = false) {
    const tile = tiles.find((candidate) => candidate.dataset.suiteGroup === key);
    const panel = panels.find((candidate) => candidate.dataset.suitePanel === key);
    if (!tile || !panel) return;

    const wasOpen = tile.classList.contains('is-active');
    closeGroups();
    if (wasOpen) return;

    tile.classList.add('is-active');
    tile.setAttribute('aria-expanded', 'true');
    panel.hidden = false;
    if (placeholder) placeholder.hidden = true;

    if (shouldScroll && window.matchMedia('(max-width: 767.98px)').matches) {
      panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  tiles.forEach((tile) => tile.addEventListener('click', () => openGroup(tile.dataset.suiteGroup, true)));
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && tiles.some((tile) => tile.classList.contains('is-active'))) {
      closeGroups();
    }
  });
})();
