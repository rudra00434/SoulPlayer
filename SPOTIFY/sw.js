/**
 * SoulPlayer Advanced Service Worker
 * Features: Static Assets Caching + Background Media Caching
 */

const CACHE_NAME = 'soulplayer-v2';
const MEDIA_CACHE = 'soulplayer-media-v1';

const STATIC_ASSETS = [
    '/',
    '/static/soulplayer_icon.png',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
    'https://cdn.tailwindcss.com',
    'https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap'
];

// 1. Install: Cache the Shell
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
    );
    self.skipWaiting();
});

// 2. Activate: Take control immediately
self.addEventListener('activate', (event) => {
    event.waitUntil(
        Promise.all([
            caches.keys().then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName !== CACHE_NAME && cacheName !== MEDIA_CACHE) {
                            return caches.delete(cacheName);
                        }
                    })
                );
            }),
            self.clients.claim()
        ])
    );
});

// 3. Fetch Handler
self.addEventListener('fetch', (event) => {
    const url = event.request.url;

    // Logic for Media (MP3s / JioSaavn Streams)
    const isMedia = url.includes('.mp3') || url.includes('.m4a') ||
        url.includes('jiosaavn') || url.includes('googleusercontent');

    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            if (cachedResponse) return cachedResponse;

            return fetch(event.request).then((networkResponse) => {
                if (url.includes('/static/') && !isMedia) {
                    const responseClone = networkResponse.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(event.request, responseClone));
                }
                return networkResponse;
            });
        }).catch(() => {
            if (event.request.mode === 'navigate') {
                return caches.match('/');
            }
        })
    );
});

// 4. Message Handler: Robust downloading
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'DOWNLOAD_SONG') {
        const { url, songId } = event.data;

        event.waitUntil(
            caches.open(MEDIA_CACHE).then((cache) => {
                return fetch(url, { mode: 'cors', credentials: 'omit' })
                    .catch(() => fetch(url, { mode: 'no-cors' }))
                    .then((response) => {
                        return cache.put(url, response).then(() => {
                            return self.clients.matchAll({ includeUncontrolled: true, type: 'window' });
                        });
                    })
                    .then((clients) => {
                        if (clients && clients.length) {
                            clients.forEach(client => {
                                client.postMessage({
                                    type: 'DOWNLOAD_COMPLETE',
                                    songId: songId
                                });
                            });
                        }
                    });
            })
        );
    }
});
