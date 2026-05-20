/**
 * TokenFlow Push Notifications
 * Gestion des notifications push côté client
 */

class TokenFlowPushNotifications {
    constructor() {
        this.isSupported = 'serviceWorker' in navigator && 'PushManager' in window;
        this.registration = null;
        this.subscription = null;
        this.vapidPublicKey = null;
        this.isInitialized = false;
    }

    /**
     * Initialiser le système de notifications push
     */
    async init() {
        if (!this.isSupported) {
            console.warn('Push notifications not supported');
            return false;
        }

        try {
            // Enregistrer le Service Worker
            this.registration = await navigator.serviceWorker.register('/static/js/sw.js');
            console.log('Service Worker registered:', this.registration);

            // Récupérer la clé publique VAPID
            const response = await fetch('/api/push/vapid-keys');
            const data = await response.json();
            this.vapidPublicKey = data.publicKey;

            // Vérifier si déjà abonné
            this.subscription = await this.registration.pushManager.getSubscription();
            
            if (this.subscription) {
                console.log('Already subscribed to push notifications');
                this.isInitialized = true;
                return true;
            }

            this.isInitialized = true;
            return true;
        } catch (error) {
            console.error('Error initializing push notifications:', error);
            return false;
        }
    }

    /**
     * Demander la permission et s'abonner
     */
    async requestPermission() {
        if (!this.isInitialized) {
            await this.init();
        }

        // Vérifier la permission
        const permission = await Notification.requestPermission();
        
        if (permission !== 'granted') {
            console.warn('Notification permission denied');
            return false;
        }

        // S'abonner au push
        try {
            this.subscription = await this.registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array(this.vapidPublicKey)
            });

            // Envoyer l'abonnement au serveur
            await this.sendSubscriptionToServer();
            
            console.log('Subscribed to push notifications');
            return true;
        } catch (error) {
            console.error('Error subscribing to push:', error);
            return false;
        }
    }

    /**
     * Envoyer l'abonnement au serveur
     */
    async sendSubscriptionToServer() {
        if (!this.subscription) return;

        try {
            const subscriptionData = {
                endpoint: this.subscription.endpoint,
                p256dh: this.subscription.getKey('p256dh') ? 
                    this.arrayBufferToBase64(this.subscription.getKey('p256dh')) : '',
                auth: this.subscription.getKey('auth') ? 
                    this.arrayBufferToBase64(this.subscription.getKey('auth')) : '',
                browser: this.getBrowserName(),
                device_type: this.isMobile() ? 'mobile' : 'desktop'
            };

            const response = await fetch('/api/push/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(subscriptionData)
            });

            const result = await response.json();
            
            if (result.success) {
                console.log('Subscription saved to server');
                this.showNotification('🔔 Notifications activées', 'Vous recevrez les mises à jour importantes directement sur votre appareil.');
            }
            
            return result.success;
        } catch (error) {
            console.error('Error sending subscription to server:', error);
            return false;
        }
    }

    /**
     * Se désabonner des notifications push
     */
    async unsubscribe() {
        if (!this.subscription) return true;

        try {
            await this.subscription.unsubscribe();
            
            // Informer le serveur
            await fetch('/api/push/unsubscribe', {
                method: 'POST'
            });

            this.subscription = null;
            console.log('Unsubscribed from push notifications');
            return true;
        } catch (error) {
            console.error('Error unsubscribing:', error);
            return false;
        }
    }

    /**
     * Afficher une notification locale
     */
    showNotification(title, body, options = {}) {
        if (!('Notification' in window)) return;

        const defaultOptions = {
            body: body,
            icon: '/static/images/logo.svg',
            badge: '/static/images/badge.png',
            vibrate: [100, 50, 100],
            requireInteraction: false,
            ...options
        };

        if (Notification.permission === 'granted') {
            new Notification(title, defaultOptions);
        }
    }

    /**
     * Tester l'envoi d'une notification push
     */
    async testPushNotification() {
        try {
            const response = await fetch('/api/push/test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title: 'Test TokenFlow 🔔',
                    body: 'Ceci est une notification de test. Si vous la recevez, les notifications push fonctionnent correctement !'
                })
            });

            const result = await response.json();
            return result.success;
        } catch (error) {
            console.error('Error testing push notification:', error);
            return false;
        }
    }

    /**
     * Convertir ArrayBuffer en Base64
     */
    arrayBufferToBase64(buffer) {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    }

    /**
     * Convertir Base64 en Uint8Array
     */
    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/\-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }

    /**
     * Détecter le nom du navigateur
     */
    getBrowserName() {
        const userAgent = navigator.userAgent;
        if (userAgent.indexOf('Chrome') > -1) return 'Chrome';
        if (userAgent.indexOf('Safari') > -1) return 'Safari';
        if (userAgent.indexOf('Firefox') > -1) return 'Firefox';
        if (userAgent.indexOf('Edg') > -1) return 'Edge';
        return 'Unknown';
    }

    /**
     * Détecter si l'appareil est mobile
     */
    isMobile() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }

    /**
     * Vérifier l'état des notifications
     */
    getStatus() {
        return {
            isSupported: this.isSupported,
            isInitialized: this.isInitialized,
            isSubscribed: !!this.subscription,
            permission: Notification.permission,
            browser: this.getBrowserName(),
            isMobile: this.isMobile()
        };
    }
}

// Initialiser les notifications push au chargement de la page
document.addEventListener('DOMContentLoaded', async () => {
    const pushNotifications = new TokenFlowPushNotifications();
    
    // Initialiser le système
    await pushNotifications.init();
    
    // Afficher un bouton pour activer les notifications si pas encore fait
    const status = pushNotifications.getStatus();
    if (status.isSupported && !status.isSubscribed && status.permission === 'default') {
        // Afficher une invitation à activer les notifications
        showNotificationPrompt(pushNotifications);
    }
    
    // Rendre disponible globalement
    window.tokenFlowPush = pushNotifications;
});

/**
 * Afficher une invitation à activer les notifications
 */
function showNotificationPrompt(pushNotifications) {
    // Créer le modal d'invitation
    const modal = document.createElement('div');
    modal.className = 'notification-prompt';
    modal.innerHTML = `
        <div class="notification-prompt-content">
            <div class="notification-prompt-icon">🔔</div>
            <h3>Activez les notifications push</h3>
            <p>Recevez les mises à jour importantes directement sur votre appareil, même quand vous n'êtes pas sur le site.</p>
            <div class="notification-prompt-buttons">
                <button class="btn-enable-push" onclick="enablePushNotifications()">Activer</button>
                <button class="btn-dismiss-prompt" onclick="dismissNotificationPrompt()">Plus tard</button>
            </div>
        </div>
    `;
    
    // Ajouter le style
    const style = document.createElement('style');
    style.textContent = `
        .notification-prompt {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
            animation: slideIn 0.3s ease;
        }
        .notification-prompt-content {
            background: white;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.15);
            max-width: 320px;
            border: 1px solid #E2E8F0;
        }
        .notification-prompt-icon {
            font-size: 48px;
            text-align: center;
            margin-bottom: 12px;
        }
        .notification-prompt-content h3 {
            margin: 0 0 8px;
            color: #1A202C;
            font-size: 16px;
            font-weight: 700;
        }
        .notification-prompt-content p {
            margin: 0 0 16px;
            color: #4A5568;
            font-size: 13px;
            line-height: 1.5;
        }
        .notification-prompt-buttons {
            display: flex;
            gap: 8px;
        }
        .btn-enable-push {
            flex: 1;
            padding: 10px 16px;
            background: linear-gradient(135deg, #6366F1, #8B5CF6);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 13px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .btn-enable-push:hover {
            transform: translateY(-1px);
        }
        .btn-dismiss-prompt {
            flex: 1;
            padding: 10px 16px;
            background: #F1F5F9;
            color: #64748B;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 13px;
            cursor: pointer;
        }
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
    `;
    
    document.head.appendChild(style);
    document.body.appendChild(modal);
    
    // Stocker la référence
    window.notificationPrompt = modal;
}

/**
 * Activer les notifications push
 */
async function enablePushNotifications() {
    if (window.tokenFlowPush) {
        const success = await window.tokenFlowPush.requestPermission();
        if (success && window.notificationPrompt) {
            window.notificationPrompt.remove();
        }
    }
}

/**
 * Fermer le modal d'invitation
 */
function dismissNotificationPrompt() {
    if (window.notificationPrompt) {
        window.notificationPrompt.remove();
        // Ne plus montrer pendant 7 jours
        localStorage.setItem('push_prompt_dismissed', Date.now());
    }
}

// Exporter pour utilisation dans d'autres scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TokenFlowPushNotifications;
}