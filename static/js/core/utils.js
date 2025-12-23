/**
 * Nexus AI - Core Utilities
 * Funciones de utilidad global encapsuladas.
 */

(function (window) {
    'use strict';

    /**
     * Helper function to get CSRF token form meta tag
     * @returns {string} The CSRF token or empty string
     */
    function getCsrfToken() {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        return metaTag ? metaTag.getAttribute('content') : '';
    }

    /**
     * Helper function to get cookies by name
     * @param {string} name - Cookie name
     * @returns {string|undefined} Cookie value
     */
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }

    /**
     * Show Download/Processing Notification (Toast)
     * @param {string} message - Message to display
     * @param {string} type - 'loading', 'success', 'error', 'warning'
     */
    function showDownloadNotification(message, type = 'loading') {
        // Buscar notificación existente
        let notification = document.getElementById('download-notification');

        // Si existe y es de tipo loading, actualizarla en lugar de removerla
        if (notification && notification.classList.contains('loading') && (type === 'success' || type === 'error')) {
            // Actualizar la notificación existente
            notification.className = `download-notification ${type}`;

            let icon = '⏳';
            if (type === 'success') {
                icon = '✅';
            } else if (type === 'error') {
                icon = '❌';
            }

            const iconElement = notification.querySelector('.download-notification-icon');
            const messageElement = notification.querySelector('.download-notification-message');

            if (iconElement) {
                iconElement.innerHTML = icon;
            }
            if (messageElement) {
                messageElement.textContent = message;
            }

            // Auto-ocultar después de 3 segundos
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => {
                    notification.remove();
                }, 300);
            }, 3000);

            return;
        }

        // Si no existe o no es de tipo loading, remover la existente y crear nueva
        if (notification) {
            notification.remove();
        }

        // Crear nueva notificación
        notification = document.createElement('div');
        notification.id = 'download-notification';
        notification.className = `download-notification ${type}`;

        let icon = '⏳';
        if (type === 'success') {
            icon = '✅';
        } else if (type === 'error') {
            icon = '❌';
        } else {
            icon = '<i class="fas fa-spinner"></i>';
        }

        notification.innerHTML = `
                    <div class="download-notification-icon">${icon}</div>
                    <div class="download-notification-message">${message}</div>
                `;

        document.body.appendChild(notification);

        // Mostrar con animación
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);

        // Auto-ocultar después de 3 segundos si es success o error
        if (type === 'success' || type === 'error') {
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => {
                    notification.remove();
                }, 300);
            }, 3000);
        }
    }

    // Exponer al scope global (retrocompatibilidad)
    window.getCsrfToken = getCsrfToken;
    window.getCookie = getCookie;
    window.showDownloadNotification = showDownloadNotification;

    // Namespace moderno (para uso futuro)
    window.NexusUtils = {
        getCsrfToken,
        getCookie,
        showDownloadNotification
    };

})(window);
