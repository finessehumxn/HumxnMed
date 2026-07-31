/* HumxnMed Clinical console — offline shell cache.
   Stale-while-revalidate for the console page + its gate script, so the console
   OPENS even when signal drops (OR / hospital dead zones). Never touches POST
   requests (the AI endpoints) or any other page. */
var CACHE = 'mc-console-v1';
var SHELL = ['/console', '/pro-gate.js'];

self.addEventListener('install', function (e) {
  self.skipWaiting();
  e.waitUntil(caches.open(CACHE).then(function (c) { return c.addAll(SHELL); }).catch(function(){}));
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.filter(function (k) { return k !== CACHE; }).map(function (k) { return caches.delete(k); }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;                 // never intercept POST (AI calls)
  var url;
  try { url = new URL(req.url); } catch (_) { return; }
  if (url.origin !== self.location.origin) return;  // only same-origin
  var isConsole = (req.mode === 'navigate' && url.pathname === '/console');
  var isShell = url.pathname === '/console' || url.pathname === '/pro-gate.js';
  if (!isConsole && !isShell) return;               // pass everything else straight through
  e.respondWith(
    caches.open(CACHE).then(function (c) {
      return c.match(req, { ignoreSearch: true }).then(function (cached) {
        var net = fetch(req).then(function (res) {
          if (res && res.ok) { try { c.put(req, res.clone()); } catch (_) {} }
          return res;
        }).catch(function () { return cached; });
        return cached || net;                        // cache-first, refresh in background
      });
    })
  );
});
