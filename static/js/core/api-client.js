/**
 * Nexus AI - Core API Client
 * Cliente HTTP centralizado para manejar todas las peticiones al backend.
 */

(function (window) {
    'use strict';

    // Dependencia de Utils (CSRF Token)
    const getCsrfToken = window.getCsrfToken || window.NexusUtils.getCsrfToken;

    /**
     * Cliente HTTP con soporte para timeout y CSRF
     */
    const apiClient = {
        /**
         * Realiza una petición GET
         * @param {string} url - Endpoint URL
         * @param {Object} options - Opciones de fetch adicionales
         * @returns {Promise<any>} Respuesta JSON
         */
        async get(url, options = {}) {
            return this.request(url, { ...options, method: 'GET' });
        },

        /**
         * Realiza una petición POST
         * @param {string} url - Endpoint URL
         * @param {Object} body - Cuerpo de la petición (se convertirá a JSON)
         * @param {Object} options - Opciones de fetch adicionales
         * @returns {Promise<any>} Respuesta JSON
         */
        async post(url, body, options = {}) {
            return this.request(url, {
                ...options,
                method: 'POST',
                body: JSON.stringify(body),
                headers: {
                    ...options.headers,
                    'Content-Type': 'application/json'
                }
            });
        },

        /**
         * Función genérica de petición con timeout
         */
        async request(url, options = {}, timeout = 600000) { // 10 min default
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), timeout);

            // Inyectar CSRF Token
            const headers = {
                'Accept': 'application/json',
                ...(options.headers || {})
            };

            const token = getCsrfToken();
            if (token) {
                headers['X-CSRFToken'] = token;
            }

            // Opciones por defecto
            const fetchOptions = {
                ...options,
                headers,
                signal: controller.signal,
                credentials: 'include' // Para mantener la sesión
            };

            try {
                const response = await fetch(url, fetchOptions);
                clearTimeout(timeoutId);

                // Manejo de errores HTTP
                if (!response.ok) {
                    const errorBody = await response.text().then(text => {
                        try { return JSON.parse(text); } catch { return { error: text }; }
                    });

                    const error = new Error(errorBody.error || `Error HTTP ${response.status}`);
                    error.status = response.status;
                    error.details = errorBody;
                    throw error;
                }

                return await response.json();
            } catch (error) {
                clearTimeout(timeoutId);
                if (error.name === 'AbortError') {
                    throw new Error('La solicitud tardó demasiado tiempo en responder.');
                }
                throw error;
            }
        }
    };

    /**
     * Servicios específicos del Dashboard
     */
    const dashboardService = {
        /**
         * Obtiene las métricas de actividad (historias, test cases)
         */
        async getActivityMetrics() {
            try {
                const data = await apiClient.get('/api/dashboard/activity-metrics');
                if (data.success) {
                    return data.metrics;
                }
                return null;
            } catch (e) {
                console.error('Error fetching activity metrics:', e);
                return null;
            }
        },

        /**
         * Obtiene el historial de historias generadas
         */
        async getStoriesHistory(limit = 50) {
            try {
                const data = await apiClient.get(`/api/dashboard/stories?limit=${limit}`);
                return data.success ? data.stories : [];
            } catch (e) {
                console.error('Error fetching stories history:', e);
                return [];
            }
        },

        /**
         * Obtiene el historial de casos de prueba generados
         */
        async getTestCasesHistory(limit = 50) {
            try {
                const data = await apiClient.get(`/api/dashboard/test-cases?limit=${limit}`);
                return data.success ? data.test_cases : [];
            } catch (e) {
                console.error('Error fetching test cases history:', e);
                return [];
            }
        },

        /**
         * Obtiene el historial de reportes de Jira
         */
        async getReportsHistory(limit = 50) {
            try {
                const data = await apiClient.get(`/api/dashboard/reports?limit=${limit}`);
                return data.success ? data.reports : [];
            } catch (e) {
                console.error('Error fetching reports history:', e);
                return [];
            }
        },

        /**
         * Obtiene el historial de cargas masivas
         */
        async getBulkUploadsHistory(limit = 50) {
            try {
                const data = await apiClient.get(`/api/dashboard/bulk-uploads?limit=${limit}`);
                return data.success ? data.bulk_uploads : [];
            } catch (e) {
                console.error('Error fetching bulk uploads history:', e);
                return [];
            }
        }
    };

    // Exponer al scope global
    window.apiClient = apiClient;
    window.dashboardService = dashboardService;
    window.fetchWithTimeout = apiClient.request.bind(apiClient); // Retrocompatibilidad

    // Namespace moderno
    window.NexusApi = {
        client: apiClient,
        dashboard: dashboardService
    };

})(window);
