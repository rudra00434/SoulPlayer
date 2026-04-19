/**
 * SoulPlayer Minimal Service Worker
 * Required for PWA Installation. 
 * This version is a simple pass-through and DOES NOT cache resources
 * to prevent any "not updating" or "offline" bugs.
 */

const CACHE_NAME = 'soulplayer-v1-install-only';

self.addEventListener('install', (event) => {
    // Instant activation
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    // Clear any old caches from previous broken versions
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    return caches.delete(cacheName);
                })
            );
        })
    );
});

self.addEventListener('fetch', (event) => {
    // Pass-through: No interception, no caching.
    // This ensures Voice Search and dynamic content work perfectly.
    return;
});
