const CACHE_NAME = 'neuronest-offline-cache-v2';
const PRECACHE_ASSETS = [
  '/',
  '/favicon.svg',
];

// Install Event - pre-cache the app shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[Service Worker] Pre-caching static assets');
      return cache.addAll(PRECACHE_ASSETS);
    }).then(() => self.skipWaiting())
  );
});

// Activate Event - clear stale caches from previous versions
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('[Service Worker] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch Event — Network-First with Cache Fallback
// NOTE: TF.js model weights are now webpack-bundled (runtime:"tfjs"),
// so no special CDN caching is needed for MediaPipe assets.
self.addEventListener('fetch', (event) => {
  // Only handle GET requests over http/https
  if (event.request.method !== 'GET') return;
  if (!event.request.url.startsWith('http')) return;

  const requestUrl = new URL(event.request.url);

  event.respondWith(
    caches.open(CACHE_NAME).then((cache) => {
      return fetch(event.request)
        .then((networkResponse) => {
          // Cache successful same-origin responses to grow the offline shell
          if (networkResponse.status === 200 && requestUrl.origin === self.location.origin) {
            cache.put(event.request, networkResponse.clone());
          }
          return networkResponse;
        })
        .catch(() => {
          // Network failed — serve from cache
          return cache.match(event.request).then((cachedResponse) => {
            if (cachedResponse) {
              return cachedResponse;
            }
            // For page navigations not yet cached, return the root SPA shell
            if (event.request.mode === 'navigate') {
              return cache.match('/');
            }
            return new Response('Offline and resource not cached', {
              status: 503,
              statusText: 'Offline',
            });
          });
        });
    })
  );
});
