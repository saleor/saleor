const cacheName = 'staticFiles';

// during the install phase you usually want to cache static assets
self.addEventListener('install', (e) => {
  // once the SW is installed, go ahead and fetch the resources to make this work offline
  e.waitUntil(
    caches.open(cacheName)
      .then((cache) => {
        return cache.addAll([
          '/',
          '/offline'
        ])
          .then(() => {
            self.skipWaiting();
          })
          .catch(e => console.error(e));
      })
      .catch(e => console.error(e))
  );
});

// when the browser fetches a url
self.addEventListener('fetch', (event) => {
  if (event.request.url.match(/http:\/\/.*((\.(css|js|svg)$)|(placeholder\d+x\d+\.png$))/)) {
    console.log(event.request.url);
    caches.open(cacheName)
      .then(cache => cache.add(event.request.url))
      .then(() => self.skipWaiting())
      .catch(e => {
        console.log(event.request.url);
        console.error(e);
      });
  }
  event.respondWith(
    fetch(event.request)
      .catch(() => {
        if (!event.request.url.match(/\.(js|css|eot|otf|png|svg|ttf|woff|woff2)(\?v=[0-9.]+)?$/)) {
          console.log(event.request.url);
          return caches.match('/offline')
            .then(res => res);
        }
        return caches.match(event.request);
      })
  );
});
