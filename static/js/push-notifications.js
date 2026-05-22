/**
 * TokenFlow Push Notifications - Production System
 * Système de notifications push automatique et intelligent
 * Compatible: Chrome, Firefox, Safari, Edge, Android, iOS PWA
 */

class TokenFlowPushNotifications {
    constructor() {
        this.isSupported = 'serviceWorker' in navigator && 'PushManager' in window;
        this.registration = null;
        this.subscription = null;
        this.vapidPublicKey = null;
        this.isInitialized = false;
        this.userPhone = null;
        this.notificationSound = null;
        this.badgeCount = 0;
        
        // Configuration intelligente
        this.config = {
            // Délai avant première demande (3 secondes après chargement)
            initialDelay: 3000,
            // Délai entre les demandes si refus (7 jours)
            retryDelay: 7 * 24 * 60 * 60 * 1000,
            // Délai si l'utilisateur clique sur "Plus tard" (24 heures)
            laterDelay: 24 * 60 * 60 * 1000,
            // Nombre maximum de demandes
            maxPrompts: 3,
            // Délai pour montrer le badge de notification
            badgeUpdateDelay: 5000
        };
        
        // Logs de débogage
        this.debug = true;
    }

    /**
     * Log avec préfixe TokenFlow
     */
    log(message, type = 'info') {
        if (!this.debug) return;
        
        const timestamp = new Date().toISOString();
        const prefix = `[TokenFlow Push] [${timestamp}]`;
        
        switch(type) {
            case 'info':
                console.log(`${prefix} ℹ️ ${message}`);
                break;
            case 'success':
                console.log(`${prefix} ✅ ${message}`);
                break;
            case 'error':
                console.error(`${prefix} ❌ ${message}`);
                break;
            case 'warn':
                console.warn(`${prefix} ⚠️ ${message}`);
                break;
        }
    }

    /**
     * Initialiser le système de notifications push
     * Doit être appelé au chargement de chaque page
     */
    async init() {
        this.log('Initialisation du système de notifications push...');
        
        if (!this.isSupported) {
            this.log('Notifications push non supportées sur ce navigateur', 'warn');
            return false;
        }

        try {
            // 1. Enregistrer le Service Worker
            this.log('Enregistrement du Service Worker...');
            this.registration = await navigator.serviceWorker.register('/static/js/sw.js');
            this.log('Service Worker enregistré avec succès', 'success');

            // 2. Récupérer la clé publique VAPID
            this.log('Récupération de la clé VAPID publique...');
            const response = await fetch('/api/push/vapid-keys');
            const data = await response.json();
            this.vapidPublicKey = data.publicKey;
            
            if (!this.vapidPublicKey) {
                this.log('Clé VAPID publique non configurée', 'error');
                return false;
            }
            
            this.log(`Clé VAPID récupérée (${this.vapidPublicKey.length} caractères)`, 'success');

            // 3. Vérifier l'abonnement existant
            this.subscription = await this.registration.pushManager.getSubscription();
            
            if (this.subscription) {
                this.log('Déjà abonné aux notifications push', 'success');
                this.isInitialized = true;
                
                // Mettre à jour le badge si nécessaire
                this.updateNotificationBadge();
                
                return true;
            }

            this.isInitialized = true;
            this.log('Initialisation terminée - en attente de permission', 'success');
            return true;
            
        } catch (error) {
            this.log(`Erreur lors de l\'initialisation: ${error.message}`, 'error');
            console.error(error);
            return false;
        }
    }

    /**
     * Demander la permission et s'abonner automatiquement
     * Cette méthode est appelée automatiquement après le délai initial
     */
    async requestPermission() {
        this.log('Demande de permission pour les notifications push...');
        
        if (!this.isInitialized) {
            await this.init();
        }

        // Vérifier si l'utilisateur a déjà refusé récemment
        const lastDismiss = localStorage.getItem('push_prompt_dismissed');
        if (lastDismiss) {
            const timeSinceDismiss = Date.now() - parseInt(lastDismiss);
            if (timeSinceDismiss < this.config.laterDelay) {
                this.log('Utilisateur a cliqué sur "Plus tard" récemment, on attend...', 'info');
                return false;
            }
        }

        // Vérifier si on a déjà atteint le max de demandes
        const promptCount = parseInt(localStorage.getItem('push_prompt_count') || '0');
        if (promptCount >= this.config.maxPrompts) {
            this.log('Maximum de demandes atteint, on n\'embête plus l\'utilisateur', 'info');
            return false;
        }

        // Vérifier la permission actuelle
        const permission = await Notification.requestPermission();
        this.log(`Permission: ${permission}`, 'info');
        
        // Mettre à jour le compteur de demandes
        localStorage.setItem('push_prompt_count', promptCount + 1);
        
        if (permission !== 'granted') {
            this.log('Permission refusée ou ignorée', 'warn');
            localStorage.setItem('push_prompt_dismissed', Date.now());
            return false;
        }

        // S'abonner au push
        try {
            this.log('Subscription au service push...', 'info');
            this.subscription = await this.registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array(this.vapidPublicKey)
            });

            // Envoyer l'abonnement au serveur
            await this.sendSubscriptionToServer();
            
            this.log('Abonnement réussi aux notifications push!', 'success');
            
            // Supprimer le compteur de demandes (réinitialiser)
            localStorage.removeItem('push_prompt_count');
            localStorage.removeItem('push_prompt_dismissed');
            
            return true;
            
        } catch (error) {
            this.log(`Erreur lors de l\'abonnement: ${error.message}`, 'error');
            console.error(error);
            return false;
        }
    }

    /**
     * Afficher le popup personnalisé AVANT la demande de permission navigateur
     * Style Binance/Revolut - moderne et professionnel
     */
    showCustomPrompt() {
        this.log('Affichage du popup personnalisé...', 'info');
        
        // Vérifier si on doit montrer le popup
        const lastDismiss = localStorage.getItem('push_prompt_dismissed');
        if (lastDismiss) {
            const timeSinceDismiss = Date.now() - parseInt(lastDismiss);
            if (timeSinceDismiss < this.config.laterDelay) {
                return false;
            }
        }

        const promptCount = parseInt(localStorage.getItem('push_prompt_count') || '0');
        if (promptCount >= this.config.maxPrompts) {
            return false;
        }

        // Créer le modal
        const modal = document.createElement('div');
        modal.id = 'tokenflow-push-prompt';
        modal.className = 'tokenflow-push-prompt';
        
        modal.innerHTML = `
            <div class="tokenflow-push-prompt-overlay"></div>
            <div class="tokenflow-push-prompt-container">
                <div class="tokenflow-push-prompt-content">
                    <div class="tokenflow-push-prompt-icon">
                        <div class="icon-bell">
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                                <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                            </svg>
                        </div>
                        <div class="icon-ring"></div>
                    </div>
                    
                    <h3 class="tokenflow-push-prompt-title">
                        Restez informé en temps réel
                    </h3>
                    
                    <p class="tokenflow-push-prompt-description">
                        Recevez des notifications instantanées pour :
                    </p>
                    
                    <ul class="tokenflow-push-prompt-features">
                        <li>
                            <span class="feature-icon">✅</span>
                            <span>Dépôts et retraits validés</span>
                        </li>
                        <li>
                            <span class="feature-icon">💰</span>
                            <span>Revenus d\'investissement</span>
                        </li>
                        <li>
                            <span class="feature-icon">🤝</span>
                            <span>Commissions de parrainage</span>
                        </li>
                        <li>
                            <span class="feature-icon">🔒</span>
                            <span>Sécurité de votre compte</span>
                        </li>
                    </ul>
                    
                    <div class="tokenflow-push-prompt-buttons">
                        <button class="btn-allow" onclick="window.tokenFlowPush.handleAllow()">
                            <span class="btn-icon">🔔</span>
                            Autoriser les notifications
                        </button>
                        <button class="btn-later" onclick="window.tokenFlowPush.handleLater()">
                            Plus tard
                        </button>
                    </div>
                    
                    <p class="tokenflow-push-prompt-privacy">
                        <small>🔒 Vos données sont protégées. Désabonnez-vous à tout moment.</small>
                    </p>
                </div>
            </div>
        `;
        
        // Ajouter les styles
        const style = document.createElement('style');
        style.id = 'tokenflow-push-prompt-style';
        style.textContent = this.getPromptStyles();
        document.head.appendChild(style);
        
        // Ajouter au DOM
        document.body.appendChild(modal);
        
        // Animation d\'entrée
        setTimeout(() => {
            modal.classList.add('show');
        }, 10);
        
        this.log('Popup personnalisé affiché', 'success');
        return true;
    }

    /**
     * Styles CSS pour le popup personnalisé
     */
    getPromptStyles() {
        return `
            .tokenflow-push-prompt {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: 10000;
                justify-content: center;
                align-items: center;
                opacity: 0;
                transition: opacity 0.3s ease;
            }
            
            .tokenflow-push-prompt.show {
                display: flex;
                opacity: 1;
            }
            
            .tokenflow-push-prompt-overlay {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.6);
                backdrop-filter: blur(4px);
                -webkit-backdrop-filter: blur(4px);
            }
            
            .tokenflow-push-prompt-container {
                position: relative;
                z-index: 1;
                padding: 20px;
                animation: slideUp 0.4s ease-out;
            }
            
            @keyframes slideUp {
                from {
                    transform: translateY(30px);
                    opacity: 0;
                }
                to {
                    transform: translateY(0);
                    opacity: 1;
                }
            }
            
            .tokenflow-push-prompt-content {
                background: white;
                border-radius: 24px;
                padding: 32px;
                max-width: 400px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                text-align: center;
                position: relative;
                overflow: hidden;
            }
            
            .tokenflow-push-prompt-content::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, #6366F1, #8B5CF6, #EC4899);
            }
            
            .tokenflow-push-prompt-icon {
                position: relative;
                display: inline-block;
                margin-bottom: 24px;
            }
            
            .icon-bell {
                width: 80px;
                height: 80px;
                background: linear-gradient(135deg, #6366F1, #8B5CF6);
                border-radius: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                box-shadow: 0 10px 30px rgba(99, 102, 241, 0.3);
                animation: bellRing 2s ease-in-out infinite;
            }
            
            @keyframes bellRing {
                0%, 100% { transform: rotate(0deg); }
                10%, 30%, 50%, 70%, 90% { transform: rotate(-5deg); }
                20%, 40%, 60%, 80% { transform: rotate(5deg); }
            }
            
            .icon-ring {
                position: absolute;
                top: -5px;
                right: -5px;
                width: 20px;
                height: 20px;
                background: #10B981;
                border: 3px solid white;
                border-radius: 50%;
                animation: pulse 2s ease-in-out infinite;
            }
            
            @keyframes pulse {
                0%, 100% { transform: scale(1); opacity: 1; }
                50% { transform: scale(1.2); opacity: 0.8; }
            }
            
            .tokenflow-push-prompt-title {
                margin: 0 0 12px;
                color: #1A202C;
                font-size: 22px;
                font-weight: 700;
                line-height: 1.3;
            }
            
            .tokenflow-push-prompt-description {
                margin: 0 0 20px;
                color: #64748B;
                font-size: 14px;
                line-height: 1.5;
            }
            
            .tokenflow-push-prompt-features {
                list-style: none;
                padding: 0;
                margin: 0 0 24px;
                text-align: left;
                background: #F8FAFC;
                border-radius: 16px;
                padding: 20px;
            }
            
            .tokenflow-push-prompt-features li {
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 12px;
                color: #475569;
                font-size: 14px;
            }
            
            .tokenflow-push-prompt-features li:last-child {
                margin-bottom: 0;
            }
            
            .feature-icon {
                font-size: 16px;
                flex-shrink: 0;
            }
            
            .tokenflow-push-prompt-buttons {
                display: flex;
                flex-direction: column;
                gap: 12px;
                margin-bottom: 16px;
            }
            
            .btn-allow {
                padding: 16px 24px;
                background: linear-gradient(135deg, #6366F1, #8B5CF6);
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 16px;
                font-weight: 700;
                cursor: pointer;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                box-shadow: 0 8px 24px rgba(99, 102, 241, 0.3);
            }
            
            .btn-allow:hover {
                transform: translateY(-2px);
                box-shadow: 0 12px 32px rgba(99, 102, 241, 0.4);
            }
            
            .btn-allow:active {
                transform: translateY(0);
            }
            
            .btn-later {
                padding: 14px 24px;
                background: transparent;
                color: #64748B;
                border: 2px solid #E2E8F0;
                border-radius: 16px;
                font-size: 15px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .btn-later:hover {
                border-color: #94A3B8;
                color: #475569;
            }
            
            .btn-icon {
                font-size: 18px;
            }
            
            .tokenflow-push-prompt-privacy {
                margin: 0;
                color: #94A3B8;
                font-size: 12px;
            }
            
            /* Responsive */
            @media (max-width: 480px) {
                .tokenflow-push-prompt-container {
                    padding: 16px;
                }
                
                .tokenflow-push-prompt-content {
                    padding: 24px 20px;
                    border-radius: 20px;
                }
                
                .tokenflow-push-prompt-title {
                    font-size: 20px;
                }
                
                .icon-bell {
                    width: 64px;
                    height: 64px;
                    border-radius: 20px;
                }
                
                .icon-bell svg {
                    width: 36px;
                    height: 36px;
                }
            }
        `;
    }

    /**
     * Gestionnaire pour le bouton "Autoriser"
     */
    async handleAllow() {
        this.log('Utilisateur clique sur "Autoriser"', 'info');
        
        // Fermer le popup
        this.closePrompt();
        
        // Demander la permission navigateur
        const success = await this.requestPermission();
        
        if (success) {
            this.showSuccessMessage();
        } else {
            this.showErrorMessage();
        }
    }

    /**
     * Gestionnaire pour le bouton "Plus tard"
     */
    handleLater() {
        this.log('Utilisateur clique sur "Plus tard"', 'info');
        this.closePrompt();
        localStorage.setItem('push_prompt_dismissed', Date.now());
    }

    /**
     * Fermer le popup
     */
    closePrompt() {
        const prompt = document.getElementById('tokenflow-push-prompt');
        if (prompt) {
            prompt.classList.remove('show');
            setTimeout(() => {
                prompt.remove();
            }, 300);
        }
    }

    /**
     * Afficher un message de succès
     */
    showSuccessMessage() {
        this.showNotification(
            '🔔 Notifications activées!',
            'Vous recevrez maintenant les mises à jour importantes directement sur votre appareil.'
        );
    }

    /**
     * Afficher un message d\'erreur
     */
    showErrorMessage() {
        this.log('Échec de l\'activation des notifications', 'error');
    }

    /**
     * Envoyer l'abonnement au serveur
     */
    async sendSubscriptionToServer() {
        if (!this.subscription) {
            this.log('Pas d\'abonnement à envoyer', 'warn');
            return false;
        }

        try {
            const keys = this.subscription.keys;
            const subscriptionData = {
                endpoint: this.subscription.endpoint,
                p256dh: keys.p256dh,
                auth: keys.auth,
                browser: this.getBrowserInfo().name,
                device_type: this.getDeviceType(),
                os: this.getBrowserInfo().os,
                browser_version: this.getBrowserInfo().version
            };

            this.log('Envoi de l\'abonnement au serveur...', 'info');
            this.log(`Endpoint: ${subscriptionData.endpoint.substring(0, 50)}...`);
            this.log(`Navigateur: ${subscriptionData.browser} (${subscriptionData.os})`);
            this.log(`Type d\'appareil: ${subscriptionData.device_type}`);

            const response = await fetch('/api/push/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(subscriptionData)
            });

            const result = await response.json();
            
            if (result.success) {
                this.log('Abonnement sauvegardé avec succès sur le serveur', 'success');
                this.updateNotificationBadge();
                return true;
            } else {
                this.log(`Erreur serveur: ${result.error || 'Unknown'}`, 'error');
                return false;
            }
            
        } catch (error) {
            this.log(`Erreur lors de l\'envoi au serveur: ${error.message}`, 'error');
            console.error(error);
            return false;
        }
    }

    /**
     * Se désabonner des notifications push
     */
    async unsubscribe() {
        if (!this.subscription) {
            this.log('Déjà désabonné', 'info');
            return true;
        }

        try {
            this.log('Désabonnement des notifications push...', 'info');
            await this.subscription.unsubscribe();
            
            // Informer le serveur
            await fetch('/api/push/unsubscribe', {
                method: 'POST'
            });

            this.subscription = null;
            this.log('Désabonnement réussi', 'success');
            this.updateNotificationBadge();
            return true;
            
        } catch (error) {
            this.log(`Erreur lors du désabonnement: ${error.message}`, 'error');
            console.error(error);
            return false;
        }
    }

    /**
     * Afficher une notification locale
     */
    showNotification(title, body, options = {}) {
        if (!('Notification' in window)) {
            this.log('Notifications non supportées', 'warn');
            return;
        }

        const defaultOptions = {
            body: body,
            icon: '/static/images/logo.svg',
            badge: '/static/images/badge.png',
            vibrate: [100, 50, 100],
            requireInteraction: false,
            tag: 'tokenflow-notification',
            ...options
        };

        if (Notification.permission === 'granted') {
            new Notification(title, defaultOptions);
            this.log(`Notification affichée: ${title}`, 'info');
        } else {
            this.log('Permission non accordée pour afficher notification', 'warn');
        }
    }

    /**
     * Tester l'envoi d'une notification push
     */
    async testPushNotification() {
        try {
            this.log('Test d\'envoi de notification push...', 'info');
            
            const response = await fetch('/api/push/test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title: 'Test TokenFlow 🔔',
                    body: 'Ceci est une notification de test. Si vous la recevez, les notifications push functionnent correctement!',
                    timestamp: new Date().toISOString()
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.log('Test de notification réussi!', 'success');
                this.showNotification(
                    '✅ Test réussi',
                    'Les notifications push fonctionnent correctement sur votre appareil.'
                );
                return true;
            } else {
                this.log(`Échec du test: ${result.error || 'Unknown'}`, 'error');
                return false;
            }
            
        } catch (error) {
            this.log(`Erreur lors du test: ${error.message}`, 'error');
            console.error(error);
            return false;
        }
    }

    /**
     * Récupérer les notifications non lues
     */
    async getUnreadNotifications() {
        try {
            const response = await fetch('/api/notifications');
            const data = await response.json();
            
            if (data.success) {
                this.badgeCount = data.count;
                this.updateNotificationBadge();
                return data.notifications;
            }
            
            return [];
        } catch (error) {
            this.log(`Erreur récupération notifications: ${error.message}`, 'error');
            return [];
        }
    }

    /**
     * Marquer une notification comme lue
     */
    async markAsRead(notificationId) {
        try {
            await fetch(`/api/notifications/${notificationId}/read`, {
                method: 'POST'
            });
            
            // Mettre à jour le badge
            this.badgeCount = Math.max(0, this.badgeCount - 1);
            this.updateNotificationBadge();
            
        } catch (error) {
            this.log(`Erreur marquage comme lu: ${error.message}`, 'error');
        }
    }

    /**
     * Marquer toutes les notifications comme lues
     */
    async markAllAsRead() {
        try {
            await fetch('/api/notifications/mark-all-read', {
                method: 'POST'
            });
            
            this.badgeCount = 0;
            this.updateNotificationBadge();
            
        } catch (error) {
            this.log(`Erreur marquage tout comme lu: ${error.message}`, 'error');
        }
    }

    /**
     * Mettre à jour le badge de notification
     */
    updateNotificationBadge() {
        // Mettre à jour le badge du navigateur si supporté
        if ('setAppBadge' in navigator) {
            if (this.badgeCount > 0) {
                navigator.setAppBadge(this.badgeCount);
            } else {
                navigator.clearAppBadge();
            }
        }
        
        // Mettre à jour le badge dans l'UI si présent
        const badgeElement = document.querySelector('.notification-badge');
        if (badgeElement) {
            if (this.badgeCount > 0) {
                badgeElement.textContent = this.badgeCount > 99 ? '99+' : this.badgeCount;
                badgeElement.style.display = 'flex';
            } else {
                badgeElement.style.display = 'none';
            }
        }
        
        this.log(`Badge mis à jour: ${this.badgeCount} notifications non lues`, 'info');
    }

    /**
     * Obtenir les informations du navigateur
     */
    getBrowserInfo() {
        const userAgent = navigator.userAgent;
        let name = 'Unknown';
        let version = 'Unknown';
        let os = 'Unknown';
        
        // Détecter OS
        if (userAgent.indexOf('Win') !== -1) os = 'Windows';
        if (userAgent.indexOf('Mac') !== -1) os = 'macOS';
        if (userAgent.indexOf('Linux') !== -1) os = 'Linux';
        if (userAgent.indexOf('Android') !== -1) os = 'Android';
        if (userAgent.indexOf('like Mac') !== -1) os = 'iOS';
        
        // Détecter navigateur
        if (userAgent.indexOf('Chrome') > -1) {
            name = 'Chrome';
            version = userAgent.match(/Chrome\/(\d+)/)?.[1] || 'Unknown';
        } else if (userAgent.indexOf('Safari') > -1) {
            name = 'Safari';
            version = userAgent.match(/Version\/(\d+)/)?.[1] || 'Unknown';
        } else if (userAgent.indexOf('Firefox') > -1) {
            name = 'Firefox';
            version = userAgent.match(/Firefox\/(\d+)/)?.[1] || 'Unknown';
        } else if (userAgent.indexOf('Edg') > -1) {
            name = 'Edge';
            version = userAgent.match(/Edg\/(\d+)/)?.[1] || 'Unknown';
        }
        
        return { name, version, os };
    }

    /**
     * Obtenir le type d\'appareil
     */
    getDeviceType() {
        const userAgent = navigator.userAgent.toLowerCase();
        
        if (/android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent)) {
            return 'mobile';
        }
        
        if (/tablet|ipad|playbook|silk/i.test(userAgent)) {
            return 'tablet';
        }
        
        return 'desktop';
    }

    /**
     * Obtenir le statut complet
     */
    getStatus() {
        const browserInfo = this.getBrowserInfo();
        
        return {
            isSupported: this.isSupported,
            isInitialized: this.isInitialized,
            isSubscribed: !!this.subscription,
            permission: Notification.permission,
            browser: browserInfo.name,
            browserVersion: browserInfo.version,
            os: browserInfo.os,
            deviceType: this.getDeviceType(),
            badgeCount: this.badgeCount,
            promptCount: parseInt(localStorage.getItem('push_prompt_count') || '0'),
            lastDismiss: localStorage.getItem('push_prompt_dismissed')
        };
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
        return window.btoa(binary);
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
}

// ============================================
// INITIALISATION AUTOMATIQUE
// ============================================

// Instance globale
let tokenFlowPushInstance = null;

/**
 * Initialiser les notifications push au chargement de la page
 * Cette fonction est appelée automatiquement sur toutes les pages
 */
async function initializePushNotifications() {
    // Créer l'instance
    tokenFlowPushInstance = new TokenFlowPushNotifications();
    window.tokenFlowPush = tokenFlowPushInstance;
    
    // Initialiser le système
    const initialized = await tokenFlowPushInstance.init();
    
    if (!initialized) {
        console.warn('[TokenFlow Push] Échec de l\'initialisation');
        return;
    }
    
    // Si déjà abonné, mettre à jour le badge
    if (tokenFlowPushInstance.subscription) {
        await tokenFlowPushInstance.getUnreadNotifications();
        return;
    }
    
    // Vérifier si on doit montrer le popup
    const lastDismiss = localStorage.getItem('push_prompt_dismissed');
    const promptCount = parseInt(localStorage.getItem('push_prompt_count') || '0');
    
    // Ne pas montrer si refus récent ou max atteint
    if (lastDismiss) {
        const timeSinceDismiss = Date.now() - parseInt(lastDismiss);
        if (timeSinceDismiss < tokenFlowPushInstance.config.laterDelay) {
            return;
        }
    }
    
    if (promptCount >= tokenFlowPushInstance.config.maxPrompts) {
        return;
    }
    
    // Délai avant affichage (pour ne pas interrompre l'utilisateur immédiatement)
    setTimeout(() => {
        if (Notification.permission === 'default') {
            tokenFlowPushInstance.showCustomPrompt();
        }
    }, tokenFlowPushInstance.config.initialDelay);
}

// ============================================
// GESTIONNAIRES D'ÉVÉNEMENTS
// ============================================

// Initialiser au chargement du DOM
document.addEventListener('DOMContentLoaded', initializePushNotifications);

// Réinitialiser si le service worker change
if (navigator.serviceWorker) {
    navigator.serviceWorker.addEventListener('controllerchange', () => {
        console.log('[TokenFlow Push] Service Worker changé, réinitialisation...');
        if (tokenFlowPushInstance) {
            tokenFlowPushInstance.init();
        }
    });
}

// Gérer les messages du service worker
if (navigator.serviceWorker) {
    navigator.serviceWorker.addEventListener('message', (event) => {
        if (event.data && event.data.type === 'NOTIFICATION_CLICK') {
            console.log('[TokenFlow Push] Notification cliquée:', event.data.data);
            // Naviguer vers l'URL de la notification
            if (event.data.data.url) {
                window.location.href = event.data.data.url;
            }
        }
    });
}

// ============================================
// FONCTIONS UTILITAIRES GLOBALES
// ============================================

/**
 * Vérifier le statut des notifications push
 */
function checkPushStatus() {
    if (window.tokenFlowPush) {
        const status = window.tokenFlowPush.getStatus();
        console.log('[TokenFlow Push] Status:', status);
        return status;
    }
    return null;
}

/**
 * Tester manuellement les notifications (pour debugging)
 */
function testPush() {
    if (window.tokenFlowPush) {
        return window.tokenFlowPush.testPushNotification();
    }
    console.error('[TokenFlow Push] Système non initialisé');
    return false;
}

/**
 * Se désabonner manuellement
 */
function disablePush() {
    if (window.tokenFlowPush) {
        return window.tokenFlowPush.unsubscribe();
    }
    console.error('[TokenFlow Push] Système non initialisé');
    return false;
}

// Exporter pour utilisation dans d'autres scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TokenFlowPushNotifications;
}

console.log('[TokenFlow Push] Script chargé - En attente d\'initialisation...');