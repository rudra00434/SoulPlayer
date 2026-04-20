/**
 * SoulPlayer Advanced Service Worker (Stability Edition)
 * Features: Static Assets Caching + Background Media Caching + Range Request Support
 */

const CACHE_NAME = 'soulplayer-v3'; // Incremented version
const MEDIA_CACHE = 'soulplayer-media-v1';

const STATIC_ASSETS = [
    '/',
    '/static/soulplayer_icon.png',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
    'https://cdn.tailwindcss.com',
    'https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
    );
    self.skipWaiting();
});

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

/**
 * Helper to handle Range Requests for Media
 * Highly critical for deployed sites & mobile browsers
 */
async function handleRangeRequest(request, cacheName) {
    const cache = await caches.open(cacheName);
    const cachedResponse = await cache.match(request);

    if (!cachedResponse) {
        return fetch(request);
    }

    const rangeHeader = request.headers.get('Range');
    if (!rangeHeader) {
        return cachedResponse;
    }

    const bytes = await cachedResponse.arrayBuffer();
    const match = /bytes=(\d+)-(\d+)?/.exec(rangeHeader);
    if (!match) {
        return cachedResponse;
    }

    const start = parseInt(match[1], 10);
    const end = match[2] ? parseInt(match[2], 10) : bytes.byteLength - 1;

    if (start >= bytes.byteLength || end >= bytes.byteLength) {
        return new Response('', {
            status: 416,
            statusText: 'Range Not Satisfiable',
            headers: { 'Content-Range': `bytes */${bytes.byteLength}` }
        });
    }

    const slicedBuffer = bytes.slice(start, end + 1);
    const newHeaders = new Headers(cachedResponse.headers);
    newHeaders.set('Content-Range', `bytes ${start}-${end}/${bytes.byteLength}`);
    newHeaders.set('Content-Length', slicedBuffer.byteLength);

    return new Response(slicedBuffer, {
        status: 206,
        statusText: 'Partial Content',
        headers: newHeaders
    });
}

self.addEventListener('fetch', (event) => {
    const url = event.request.url;
    const isMedia = url.includes('.mp3') || url.includes('.m4a') ||
        url.includes('jiosaavn') || url.includes('googleusercontent');

    if (isMedia) {
        event.respondWith(handleRangeRequest(event.request, MEDIA_CACHE));
    } else {
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
            })
        );
    }
});

self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'DOWNLOAD_SONG') {
        const { url, songId } = event.data;

        event.waitUntil(
            caches.open(MEDIA_CACHE).then((cache) => {
                // Try CORS first, then fallback to no-cors
                return fetch(url, { mode: 'cors' })
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
