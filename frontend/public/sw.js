// Service Worker for EduSmart Stories
// Implements App Shell architecture with offline-first strategy

const CACHE_NAME = 'edusmart-v1';
const APP_SHELL_CACHE = 'edusmart-shell-v1';
const RUNTIME_CACHE = 'edusmart-runtime-v1';

// App Shell: Core files needed to render the UI
const APP_SHELL_FILES = [
  '/',
  '/index.html',
  '/manifest.json',
];

// Install event: Pre-cache the app shell
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing...');
  event.waitUntil(
    caches.open(APP_SHELL_CACHE).then((cache) => {
      console.log('[Service Worker] Caching app shell');
      return cache.addAll(APP_SHELL_FILES);
    }).then(() => {
      // Force the waiting service worker to become the active service worker
      return self.skipWaiting();
    })
  );
});

// Activate event: Clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activating...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== APP_SHELL_CACHE && cacheName !== RUNTIME_CACHE) {
            console.log('[Service Worker] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      // Take control of all pages immediately
      return self.clients.claim();
    })
  );
});

// Fetch event: Implement caching strategies
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip Chrome extensions and other non-http(s) requests
  if (!url.protocol.startsWith('http')) {
    return;
  }

  // Strategy 1: Cache-First for App Shell (HTML, CSS, JS)
  if (
    request.destination === 'document' ||
    request.destination === 'script' ||
    request.destination === 'style' ||
    url.pathname.endsWith('.css') ||
    url.pathname.endsWith('.js') ||
    url.pathname === '/' ||
    url.pathname.endsWith('.html')
  ) {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        if (cachedResponse) {
          console.log('[Service Worker] Serving from cache:', request.url);
          return cachedResponse;
        }
        
        // Not in cache, fetch from network and cache it
        return fetch(request).then((response) => {
          // Only cache successful responses
          if (response.status === 200) {
            const responseToCache = response.clone();
            caches.open(APP_SHELL_CACHE).then((cache) => {
              cache.put(request, responseToCache);
            });
          }
          return response;
        }).catch(() => {
          // If offline and not in cache, return offline page
          return caches.match('/index.html');
        });
      })
    );
    return;
  }

  // Strategy 2: Network-First for API calls (with fallback to cache)
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Cache successful API responses for offline fallback
          if (response.status === 200) {
            const responseToCache = response.clone();
            caches.open(RUNTIME_CACHE).then((cache) => {
              cache.put(request, responseToCache);
            });
          }
          return response;
        })
        .catch(() => {
          // Network failed, try cache
          return caches.match(request).then((cachedResponse) => {
            if (cachedResponse) {
              console.log('[Service Worker] API offline, serving from cache:', request.url);
              return cachedResponse;
            }
            // Return error response
            return new Response(
              JSON.stringify({ error: 'Offline', message: 'No cached data available' }),
              { status: 503, headers: { 'Content-Type': 'application/json' } }
            );
          });
        })
    );
    return;
  }

  // Strategy 3: Cache-First for images and media
  if (
    request.destination === 'image' ||
    request.destination === 'audio' ||
    request.destination === 'video' ||
    url.pathname.match(/\.(png|jpg|jpeg|gif|webp|svg|mp3|wav|ogg|mp4|webm)$/i)
  ) {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }
        
        return fetch(request).then((response) => {
          if (response.status === 200) {
            const responseToCache = response.clone();
            caches.open(RUNTIME_CACHE).then((cache) => {
              cache.put(request, responseToCache);
            });
          }
          return response;
        });
      })
    );
    return;
  }

  // Default: Network-First for everything else
  event.respondWith(
    fetch(request).catch(() => {
      return caches.match(request);
    })
  );
});

// Message handler for cache management from the app
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => caches.delete(cacheName))
        );
      })
    );
  }
});
