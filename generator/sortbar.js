/* Client-side sorting for any listing page.
   Cards carry data-v (telegram views), data-d (yyyymmdd), data-i (post id).
   Sorting only reorders the cards already on the current page — the choice is
   remembered in localStorage so it sticks while you browse. */
(function () {
  const grid = document.querySelector('main .grid');
  const bar = document.getElementById('sortbar');
  if (!grid || !bar) return;

  const cards = Array.from(grid.children).filter(el => el.classList.contains('post'));
  if (cards.length < 2) { bar.style.display = 'none'; return; }

  const KEY = 'conan:sort';
  const num = (el, a) => Number(el.getAttribute(a) || 0);

  const MODES = {
    new:   (a, b) => num(b, 'data-i') - num(a, 'data-i'),
    old:   (a, b) => num(a, 'data-i') - num(b, 'data-i'),
    views: (a, b) => num(b, 'data-v') - num(a, 'data-v'),
    least: (a, b) => num(a, 'data-v') - num(b, 'data-v'),
  };

  function apply(mode, save) {
    const fn = MODES[mode] || MODES.new;
    const frag = document.createDocumentFragment();
    cards.slice().sort(fn).forEach(c => frag.appendChild(c));
    grid.appendChild(frag);

    bar.querySelectorAll('button[data-sort]').forEach(b => {
      const on = b.dataset.sort === mode;
      b.classList.toggle('on', on);
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
    if (save) { try { localStorage.setItem(KEY, mode); } catch (e) {} }
  }

  bar.addEventListener('click', e => {
    const b = e.target.closest('button[data-sort]');
    if (b) apply(b.dataset.sort, true);
  });

  let init = 'new';
  try { init = localStorage.getItem(KEY) || 'new'; } catch (e) {}
  if (!MODES[init]) init = 'new';
  apply(init, false);
})();
