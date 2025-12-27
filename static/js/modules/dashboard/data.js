/**
 * Nexus AI - Dashboard Data Module
 * Handles data fetching and caching for dashboard metrics.
 */

(function (window) {
    'use strict';

    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Dashboard = window.NexusModules.Dashboard || {};

    // ============================================
    // State & Variables
    // ============================================

    // Variable global para cachear las métricas
    let cachedMetrics = null;

    // ============================================
    // Data Fetching
    // ============================================

    /**
     * Obtiene todas las métricas del dashboard desde el backend
     * @returns {Promise<Object>} Objeto con generator_metrics y jira_metrics
     */
    async function fetchDashboardMetrics() {
        if (cachedMetrics) {
            return cachedMetrics;
        }

        try {
            const csrfToken = window.getCsrfToken ? window.getCsrfToken() :
                (document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '');

            const response = await fetch(`/api/dashboard/metrics?t=${Date.now()}`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'X-CSRFToken': csrfToken
                }
            });

            if (!response.ok) {
                throw new Error('Error al obtener métricas del dashboard');
            }

            const data = await response.json();
            if (data.success) {
                cachedMetrics = data;
                return data;
            } else {
                throw new Error(data.error || 'Error al obtener métricas');
            }
        } catch (error) {
            console.error('Error al obtener métricas:', error);
            // Retornar estructura vacía en caso de error
            return {
                generator_metrics: {
                    stories: 0,
                    testCases: 0,
                    history: []
                },
                jira_metrics: {
                    reports: {
                        count: 0,
                        byProject: {},
                        lastDate: null
                    },
                    uploads: {
                        count: 0,
                        itemsCount: 0,
                        byProject: {},
                        issueTypesDistribution: {}
                    }
                }
            };
        }
    }

    /**
     * Obtiene métricas del generador (historias y casos de prueba)
     * @returns {Promise<Object>} Métricas del generador
     */
    async function getMetrics() {
        const data = await fetchDashboardMetrics();
        return data.generator_metrics || {
            stories: 0,
            testCases: 0,
            history: []
        };
    }

    /**
     * Obtiene métricas de Jira (reportes y cargas masivas)
     * @returns {Promise<Object>} Métricas de Jira
     */
    async function getJiraMetrics() {
        const data = await fetchDashboardMetrics();
        return data.jira_metrics || {
            reports: {
                count: 0,
                byProject: {},
                lastDate: null
            },
            uploads: {
                count: 0,
                itemsCount: 0,
                byProject: {},
                issueTypesDistribution: {}
            }
        };
    }

    function clearMetricsCache() {
        cachedMetrics = null;
    }

    // Export internal functions
    window.NexusModules.Dashboard.fetchDashboardMetrics = fetchDashboardMetrics;
    window.NexusModules.Dashboard.getMetrics = getMetrics;
    window.NexusModules.Dashboard.getJiraMetrics = getJiraMetrics;
    window.NexusModules.Dashboard.clearMetricsCache = clearMetricsCache;

})(window);
