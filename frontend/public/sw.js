// Service Worker pour notifications push
self.addEventListener('install', (event) => {
  console.log('Service Worker installé')
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  console.log('Service Worker activé')
  event.waitUntil(clients.claim())
})

self.addEventListener('fetch', (event) => {
  // Stratégie cache-first pour les assets statiques
  if (event.request.url.match(/\.(js|css|png|jpg|jpeg|svg|woff2)$/)) {
    event.respondWith(
      caches.open('campushub-cache').then((cache) => {
        return cache.match(event.request).then((response) => {
          return response || fetch(event.request).then((response) => {
            cache.put(event.request, response.clone())
            return response
          })
        })
      })
    )
  } else {
    event.respondWith(fetch(event.request))
  }
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  
  const urlToOpen = event.notification.data?.url || '/'
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        if (clientList.length > 0) {
          let client = clientList[0]
          for (let i = 0; i < clientList.length; i++) {
            if (clientList[i].focused) {
              client = clientList[i]
              break
            }
          }
          return client.focus()
            .then(() => client.navigate(urlToOpen))
        }
        return clients.openWindow(urlToOpen)
      })
  )
})

self.addEventListener('notificationclose', (event) => {
  console.log('Notification fermée', event.notification.title)
})