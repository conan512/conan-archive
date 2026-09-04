/* Advanced search for the DetectiveConanIR archive.
   index.json rows: [id, text(150), hashtags, cat, views, year]
   Images/dates are NOT in the index (they were 57% of its size) — they are
   hydrated afterwards from the small data/<n>.json shards. */
let DATA = null, CATS = null, SHARDS = {}, SUG = null;
const SHARD = __SHARD__;
const STATIC = __STATIC__;   // ids that have a real p/<id>.html page

const $ = i => document.getElementById(i);
const q = $('q'), res = $('results'), nor = $('normal'),
      grid = $('rgrid'), rc = $('rc');
const E = s => (s || '').replace(/[<>&]/g, x => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;' }[x]));
const fa = n => n.toLocaleString('fa');
const slug = t => t.trim().toLowerCase().replace(/[^\w\u0600-\u06FF]+/g, '-').replace(/^-|-$/g, '') || 'tag';
const href = id => STATIC.indexOf(id) >= 0 ? 'p/' + id + '.html' : 'post.html?id=' + id;

async function load() {
  if (!DATA) {
    rc.textContent = 'در حال بارگذاری…';
    [DATA, CATS] = await Promise.all([
      fetch('assets/index.json').then(r => r.json()),
      fetch('assets/cats.json').then(r => r.json())]);
    fillFilters();
  }
  return DATA;
}

/* ---------- filter UI ---------- */
function fillFilters() {
  const fc = $('fcat'), fy = $('fyear');
  if (fc && !fc.dataset.done) {
    Object.keys(CATS).forEach(k => {
      const o = document.createElement('option');
      o.value = k; o.textContent = CATS[k].i + ' ' + CATS[k].t; fc.appendChild(o);
    });
    fc.dataset.done = '1';
  }
  if (fy && !fy.dataset.done) {
    const ys = [...new Set(DATA.map(r => r[5]).filter(Boolean))].sort((a, b) => b - a);
    ys.forEach(y => {
      const o = document.createElement('option');
      o.value = y; o.textContent = y; fy.appendChild(o);
    });
    fy.dataset.done = '1';
  }
}

/* ---------- shards / hydration ---------- */
async function shard(n) {
  if (!SHARDS[n]) SHARDS[n] = fetch('data/' + n + '.json').then(r => r.json()).catch(() => ({}));
  return SHARDS[n];
}
function card(r) {
  const [id, txt, tags, cat, views] = r, c = (CATS && CATS[cat]) || { t: '', i: '' };
  const tg = (tags || []).slice(0, 5)
    .map(t => `<a class="tag" href="tag/${slug(t)}.html">#${E(t)}</a>`).join('');
  return `<article class="post noimg" data-id="${id}"><div class="pbody">
   <span class="pcat">${c.i} ${c.t}</span>
   <a class="ptext" href="${href(id)}">${E(txt)}</a>
   <div class="tags">${tg}</div><div class="pfoot">
   ${views ? `<span>👁 ${fa(views)}</span>` : ''}
   <a class="tg" href="https://t.me/DetectiveConanIR/${id}" target="_blank" rel="noopener">تلگرام ↗</a>
   </div></div></article>`;
}
async function hydrate(rows) {
  const groups = {};
  rows.forEach(r => { const n = Math.floor(r[0] / SHARD); (groups[n] = groups[n] || []).push(r[0]); });
  for (const n of Object.keys(groups)) {
    const data = await shard(n);
    groups[n].forEach(id => {
      const p = data[id]; if (!p) return;
      const m = (p.photos && p.photos[0]) || (p.videos && p.videos[0] && p.videos[0].thumb) || '';
      const el = grid.querySelector(`[data-id="${id}"]`); if (!el) return;
      if (m) {
        const play = p.videos && p.videos.length ? '<span class="play"><i>▶</i></span>' : '';
        el.classList.remove('noimg');
        el.insertAdjacentHTML('afterbegin',
          `<a class="pmedia" href="${href(id)}"><img loading="lazy" decoding="async" width="640" height="400" src="${m}">${play}</a>`);
      }
      const foot = el.querySelector('.pfoot');
      if (foot && p.date) foot.insertAdjacentHTML('afterbegin',
        `<span>🗓 ${p.date.slice(0, 10).replace(/-/g, '/')}</span>`);
    });
  }
}

/* ---------- autocomplete over hashtags ---------- */
function buildSug() {
  if (SUG) return SUG;
  const m = new Map();
  DATA.forEach(r => (r[2] || []).forEach(t => m.set(t, (m.get(t) || 0) + 1)));
  SUG = [...m.entries()].sort((a, b) => b[1] - a[1]);
  return SUG;
}
function suggest(s) {
  const box = $('sugbox'); if (!box) return;
  const bare = s.replace('#', '').toLowerCase();
  if (!bare || bare.length < 2) { box.style.display = 'none'; return; }
  const hit = buildSug().filter(([t]) => t.toLowerCase().includes(bare)).slice(0, 8);
  if (!hit.length) { box.style.display = 'none'; return; }
  box.innerHTML = hit.map(([t, n]) =>
    `<button type="button" data-t="${E(t)}">#${E(t)}<b>${fa(n)}</b></button>`).join('');
  box.style.display = '';
}

/* ---------- run ---------- */
let tmr;
function schedule() { clearTimeout(tmr); tmr = setTimeout(run, 200); }
q && q.addEventListener('input', schedule);
['fcat', 'fyear', 'fsort'].forEach(i => { const e = $(i); if (e) e.addEventListener('change', run); });
document.addEventListener('click', e => {
  const b = e.target.closest('#sugbox button');
  if (b) { q.value = '#' + b.dataset.t; $('sugbox').style.display = 'none'; run(); return; }
  if (!e.target.closest('.searchbar')) { const s = $('sugbox'); if (s) s.style.display = 'none'; }
});

async function run() {
  const s = q.value.trim().toLowerCase();
  const cat = ($('fcat') || {}).value || '';
  const yr = +(($('fyear') || {}).value || 0);
  const srt = ($('fsort') || {}).value || 'new';
  const filtering = cat || yr;
  if (s.length < 2 && !filtering) {
    res.style.display = 'none'; nor.style.display = '';
    const sb = $('sugbox'); if (sb) sb.style.display = 'none';
    return;
  }
  res.style.display = ''; nor.style.display = 'none';
  const d = await load();
  suggest(s);
  const bare = s.replace('#', '');
  let hit = d;
  if (s.length >= 2)
    hit = hit.filter(r => r[1].toLowerCase().includes(s) ||
      (r[2] || []).some(h => h.toLowerCase().includes(bare)));
  if (cat) hit = hit.filter(r => r[3] === cat);
  if (yr) hit = hit.filter(r => r[5] === yr);
  if (srt === 'views') hit = hit.slice().sort((a, b) => b[4] - a[4]);
  else if (srt === 'least') hit = hit.slice().sort((a, b) => a[4] - b[4]);
  else if (srt === 'old') hit = hit.slice().sort((a, b) => a[0] - b[0]);
  else hit = hit.slice().sort((a, b) => b[0] - a[0]);

  rc.textContent = fa(hit.length) + ' پست پیدا شد' + (hit.length > 90 ? ' (۹۰ مورد اول)' : '');
  const show = hit.slice(0, 90);
  grid.innerHTML = show.length ? show.map(card).join('') :
    '<div class="empty" style="grid-column:1/-1"><div class="big">🔍</div>پرونده‌ای پیدا نشد.</div>';
  if (show.length) hydrate(show);
}

const pre = new URLSearchParams(location.search).get('q');
if (pre && q) { q.value = pre; run(); }
