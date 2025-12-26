/**
 * Nexus AI - Jira Project Cache Module
 * Gestiona la pre-carga y caché de proyectos de Jira para respuesta instantánea.
 */
(function (window) {
    'use strict';

    const NexusModules = window.NexusModules || {};
    NexusModules.Generators = NexusModules.Generators || {};

    /**
     * Gestor de caché de proyectos de Jira
     */
    NexusModules.Generators.JiraProjectCache = {
        // Estado del caché
        projectsCache: null,
        loadingProjects: false,
        loadingError: null,

        /**
         * Pre-carga proyectos de Jira en background
         */
        async preloadProjects() {
            if (this.loadingProjects || this.projectsCache) return;

            this.loadingProjects = true;
            this.loadingError = null;

            try {
                const Api = NexusModules.Generators.Api;
                const data = await Api.getJiraProjects();
                this.projectsCache = data.projects || [];
                console.log('✅ Proyectos de Jira pre-cargados:', this.projectsCache.length);
            } catch (error) {
                console.error('⚠️ Error pre-cargando proyectos de Jira:', error);
                this.loadingError = error;
            } finally {
                this.loadingProjects = false;
            }
        },

        /**
         * Obtiene proyectos del caché o espera a que se carguen
         * @param {number} maxWaitMs - Tiempo máximo de espera en ms
         * @returns {Promise<Array>} Lista de proyectos
         */
        async getProjects(maxWaitMs = 30000) {
            // Si ya tenemos caché, retornar inmediatamente
            if (this.projectsCache && this.projectsCache.length > 0) {
                return this.projectsCache;
            }

            // Si hay error previo, reintentar
            if (this.loadingError) {
                this.projectsCache = null;
                await this.preloadProjects();
            }

            // Esperar hasta que termine la carga
            const startTime = Date.now();
            while (this.loadingProjects && (Date.now() - startTime) < maxWaitMs) {
                await new Promise(resolve => setTimeout(resolve, 100));
            }

            if (this.projectsCache && this.projectsCache.length > 0) {
                return this.projectsCache;
            }

            throw new Error('No se pudieron cargar los proyectos de Jira');
        },

        /**
         * Verifica si hay proyectos en caché
         * @returns {boolean}
         */
        hasCache() {
            return this.projectsCache !== null && this.projectsCache.length > 0;
        },

        /**
         * Limpia el caché
         */
        clearCache() {
            this.projectsCache = null;
            this.loadingError = null;
        },

        /**
         * Refresca el caché forzando una nueva carga
         */
        async refreshCache() {
            this.clearCache();
            await this.preloadProjects();
        }
    };

    window.NexusModules = NexusModules;
})(window);
