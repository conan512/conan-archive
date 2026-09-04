/* Service worker for the DetectiveConanIR archive.
   Strategy:
     - HTML pages : network-first, fall back to cache, then offline.html
     - assets/data: stale-while-revalidate (instant, refreshes in background)
     - CDN images : cache-first with a capped runtime cache
   Designed for flaky mobile connections: once a page has been seen, it opens
   again with no network at all. */
const V = 'conan-__VERSION__-v1';
const SHELL = V + '-shell';
const RUNTIME = V + '-run';
const IMGS = V + '-img';
const IMG_MAX = 220;

const PRECACHE = [
  './', './index.html', './offline.html', './archive/index.html',
  './tags.html', './random.html',
  './assets/theme.css', './assets/search.js', './assets/cats.json',
  './manifest.webmanifest',
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(SHELL)
      .then(c => Promise.allSettled(PRECACHE.map(u => c.add(u))))
      .then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(ks => Promise.all(ks.filter(k => k.indexOf(V) !== 0).map(k => caches.delete(k))))
      .then(() => self.clients.claim()));
});

async function trim(name, max) {
  const c = await caches.open(name);
  const keys = await c.keys();
  if (keys.length > max) await Promise.all(keys.slice(0, keys.length - max).map(k => c.delete(k)));
}

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  const sameOrigin = url.origin === location.origin;

  // images (including telegram CDN) — cache first
  if (req.destination === 'image') {
    e.respondWith((async () => {
      const c = await caches.open(IMGS);
      const hit = await c.match(req);
      if (hit) return hit;
      try {
        const r = await fetch(req);
        if (r && (r.ok || r.type === 'opaque')) { c.put(req, r.clone()); trim(IMGS, IMG_MAX); }
        return r;
      } catch (err) {
        return hit || Response.error();
      }
    })());
    return;
  }

  if (!sameOrigin) return;   // fonts/CDN css: let the browser handle it

  // navigations / html — network first, cache fallback
  if (req.mode === 'navigate' || (req.headers.get('accept') || '').includes('text/html')) {
    e.respondWith((async () => {
      try {
        const r = await fetch(req);
        const c = await caches.open(RUNTIME);
        c.put(req, r.clone());
        trim(RUNTIME, 120);
        return r;
      } catch (err) {
        return (await caches.match(req)) ||
               (await caches.match('./offline.html')) ||
               new Response('offline', { status: 503 });
      }
    })());
    return;
  }

  // css/js/json — stale-while-revalidate
  e.respondWith((async () => {
    const c = await caches.open(RUNTIME);
    const hit = await c.match(req);
    const net = fetch(req).then(r => {
      if (r && r.ok) { c.put(req, r.clone()); trim(RUNTIME, 120); }
      return r;
    }).catch(() => null);
    return hit || (await net) || new Response('{}', { headers: { 'content-type': 'application/json' } });
  })());
});
