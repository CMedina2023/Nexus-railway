/**
 * Nexus AI - UI State Manager for Jira Buttons
 * Gestiona los estados visuales de los botones de Jira (loading, disabled, etc.)
 */
(function (window) {
    'use strict';

    const NexusModules = window.NexusModules || {};
    NexusModules.Generators = NexusModules.Generators || {};

    /**
     * Gestor de estados de UI para botones de Jira
     */
    NexusModules.Generators.JiraButtonState = {
        /**
         * Muestra estado de carga en un botón
         * @param {string} buttonId - ID del botón
         * @param {string} message - Mensaje a mostrar
         */
        showLoading(buttonId, message = 'Cargando...') {
            const btn = document.getElementById(buttonId);
            if (!btn) return;

            btn.disabled = true;
            btn.style.opacity = '0.6';
            btn.style.cursor = 'wait';

            const span = btn.querySelector('span:last-child');
            if (span) {
                span.dataset.originalText = span.textContent;
                span.innerHTML = `<span style="display: inline-block; animation: spin 1s linear infinite;">⏳</span> ${message}`;
            }
        },

        /**
         * Oculta estado de carga y restaura el botón
         * @param {string} buttonId - ID del botón
         */
        hideLoading(buttonId) {
            const btn = document.getElementById(buttonId);
            if (!btn) return;

            btn.disabled = false;
            btn.style.opacity = '1';
            btn.style.cursor = 'pointer';

            const span = btn.querySelector('span:last-child');
            if (span && span.dataset.originalText) {
                span.textContent = span.dataset.originalText;
                delete span.dataset.originalText;
            }
        }
    };

    window.NexusModules = NexusModules;
})(window);
