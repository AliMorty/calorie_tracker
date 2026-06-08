var CACHE_VERSION = 'v7';
var CACHE_NAME = 'calorie-tracker-' + CACHE_VERSION;

var FILES_TO_CACHE = [
  '/',
  '/index.html',
  '/css/styles.css',
  '/js/supabase.js',
  '/js/storage.js',
  '/js/ui.js',
  '/js/app.js',
  '/data/foods.json',
  '/data/common_foods.json'
];

// Install: cache all app files
self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function (cache) {
      return cache.addAll(FILES_TO_CACHE);
    })
  );
  // Activate immediately instead of waiting for old tabs to close
  self.skipWaiting();
});

// Activate: delete old caches when version changes
self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys.filter(function (key) {
          return key.startsWith('calorie-tracker-') && key !== CACHE_NAME;
        }).map(function (key) {
          return caches.delete(key);
        })
      );
    })
  );
  // Take control of all open tabs immediately
  self.clients.claim();
});

// Fetch: network first, fall back to cache
self.addEventListener('fetch', function (event) {
  event.respondWith(
    fetch(event.request).then(function (response) {
      // Got fresh response — update cache and return it
      var clone = response.clone();
      caches.open(CACHE_NAME).then(function (cache) {
        cache.put(event.request, clone);
      });
      return response;
    }).catch(function () {
      // Network failed — serve from cache (offline support)
      return caches.match(event.request);
    })
  );
});
