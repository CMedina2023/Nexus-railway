/**
 * Nexus AI - Generator API Facade
 * Maneja todas las peticiones a la API para los generadores.
 */
(function (window) {
    'use strict';

    const NexusModules = window.NexusModules || {};
    NexusModules.Generators = NexusModules.Generators || {};

    /**
     * Facade para las llamadas a la API de generación y Jira
     */
    NexusModules.Generators.Api = {
        /**
         * Genera contenido (Historias o Tests) usando Server-Sent Events
         * @param {string} endpoint - URL del API
         * @param {FormData} formData - Datos del formulario
         * @param {Object} callbacks - Objeto con callbacks: onProgress, onTerminal, onError
         */
        async generateStream(endpoint, formData, callbacks) {
            const { onProgress, onTerminal, onError } = callbacks;

            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': window.getCsrfToken ? window.getCsrfToken() : ''
                    }
                });

                if (!response.ok) {
                    throw new Error(`Error en la respuesta del servidor: ${response.status}`);
                }

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';

                while (true) {
                    const { value, done } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n\n');
                    buffer = lines.pop();

                    for (const line of lines) {
                        if (line.trim().startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.trim().substring(6));

                                if (data.terminal) {
                                    if (data.error) {
                                        if (onError) onError(new Error(data.error));
                                    } else if (onTerminal) {
                                        onTerminal(data.data);
                                    }
                                } else if (onProgress) {
                                    onProgress(data);
                                }
                            } catch (e) {
                                console.error('Error parsing SSE data:', e, line);
                            }
                        }
                    }
                }
            } catch (error) {
                if (onError) onError(error);
                else throw error;
            }
        },

        /**
         * Valida un usuario en Jira por su email
         * @param {string} email - Email del usuario
         * @returns {Promise<Object>} Datos del usuario
         */
        async validateJiraUser(email) {
            return window.NexusApi.client.post('/api/jira/validate-user', { email });
        },

        /**
         * Obtiene la lista de proyectos de Jira
         * @returns {Promise<Array>} Lista de proyectos
         */
        async getJiraProjects() {
            return window.NexusApi.client.get('/api/jira/projects');
        },

        /**
         * Sube contenido a Jira
         * @param {string} type - 'stories' o 'tests'
         * @param {Object} data - Datos a subir
         * @returns {Promise<Object>} Resultado de la subida
         */
        async uploadToJira(type, data) {
            // Map types to correct backend endpoints
            // Backend routes: /api/jira/stories/upload-to-jira, /api/jira/tests/upload-to-jira
            const endpoint = `/api/jira/${type}/upload-to-jira`;
            return window.NexusApi.client.post(endpoint, data);
        }
    };

    window.NexusModules = NexusModules;
})(window);
