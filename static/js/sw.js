/**
 * TokenFlow Service Worker
 * Gestion des notifications push en arrière-plan
 */

const CACHE_NAME = 'tokenflow-v1';
const STATIC_ASSETS = [
    '/',
    '/static/css/fintech.css',
    '/static/js/fintech.js',
    '/static/images/logo.svg',
    '/dashboard',
    '/produits_rapide'
];

// Installation du Service Worker
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => self.skipWaiting())
    );
});

// Activation et nettoyage des anciens caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((name) => name !== CACHE_NAME)
                        .map((name) => caches.delete(name))
                );
            })
            .then(() => self.clients.claim())
    );
});

// Gestion des notifications push
self.addEventListener('push', (event) => {
    if (!event.data) return;

    let data;
    try {
        data = event.data.json();
    } catch (e) {
        data = { title: 'TokenFlow', body: event.data.text() };
    }

    const options = {
        body: data.body || 'Nouvelle notification de TokenFlow',
        icon: '/static/images/logo.svg',
        badge: '/static/images/badge.png',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: data.id || Date.now(),
            url: data.url || '/dashboard'
        },
        actions: [
            {
                action: 'open',
                title: 'Ouvrir',
                icon: '/static/images/open-icon.png'
            },
            {
                action: 'close',
                title: 'Fermer',
                icon: '/static/images/close-icon.png'
            }
        ],
        tag: data.tag || 'tokenflow-notification',
        renotify: true,
        requireInteraction: data.requireInteraction || false,
        silent: false
    };

    // Ajouter un son de notification
    if (data.sound) {
        options.silent = false;
    }

    event.waitUntil(
        self.registration.showNotification(data.title || 'TokenFlow', options)
    );
});

// Gestion des clics sur les notifications
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    const urlToOpen = event.notification.data?.url || '/dashboard';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((clientList) => {
                // Si une fenêtre est déjà ouverte, la focaliser
                for (const client of clientList) {
                    if (client.url === urlToOpen && 'focus' in client) {
                        return client.focus();
                    }
                }
                // Sinon, ouvrir une nouvelle fenêtre
                if (clients.openWindow) {
                    return clients.openWindow(urlToOpen);
                }
            })
    );
});

// Gestion des actions de notification
self.addEventListener('notificationclose', (event) => {
    console.log('Notification fermée par l\'utilisateur');
});

// Background sync pour les actions hors ligne
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-notifications') {
        event.waitUntil(syncNotifications());
    }
});

async function syncNotifications() {
    // Synchroniser les notifications en arrière-plan
    try {
        const response = await fetch('/api/notifications/sync');
        if (response.ok) {
            const data = await response.json();
            // Traiter les notifications synchronisées
            console.log('Notifications synchronisées:', data);
        }
    } catch (error) {
        console.error('Erreur de synchronisation:', error);
    }
}

// Message du Service Worker
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});

console.log('Service Worker TokenFlow chargé');