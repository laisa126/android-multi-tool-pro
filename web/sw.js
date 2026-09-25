const CACHE_NAME = 'amt-pro-v2.5-offline';
const ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/sw.js'
];

// Install: cache core shell for 100% offline
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS)).catch(()=>{})
  );
  self.skipWaiting();
});

// Activate: clean old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.map(k => { if (k !== CACHE_NAME) return caches.delete(k); })
    ))
  );
  self.clients.claim();
});

// Fetch: offline-first strategy
// - For navigation / shell: cache-first, fallback to network
// - For API (/api/): network-first, fallback to cached JSON if offline
self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);

  // API calls - try network, but if offline return cached or dummy offline response
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(req).catch(() => caches.match(req).then(cached => {
        if (cached) return cached;
        // Offline fallback: return empty success so UI stays usable offline
        return new Response(JSON.stringify({offline:true, devices:[], count:0, message:"Offline mode - no internet needed. Hardware scan still works via USB."}), {
          headers: {'Content-Type':'application/json'}
        });
      }))
    );
    return;
  }

  // Shell assets - cache first
  event.respondWith(
    caches.match(req).then(cached => {
      if (cached) return cached;
      return fetch(req).then(res => {
        // Cache successful GETs for offline
        if (res.ok) {
          const clone = res.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(req, clone));
        }
        return res;
      }).catch(() => {
        // If both fail and it's navigation, return index.html
        if (req.headers.get('accept') && req.headers.get('accept').includes('text/html')) {
          return caches.match('/index.html');
        }
      });
    })
  );
});
