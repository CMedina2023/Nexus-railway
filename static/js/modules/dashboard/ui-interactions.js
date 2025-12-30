/**
 * Nexus AI - Dashboard UI Interactions Module
 * Handles UI events, navigation, and user actions in the dashboard.
 */

(function (window) {
    'use strict';

    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Dashboard = window.NexusModules.Dashboard || {};

    const Dashboard = window.NexusModules.Dashboard;

    // State
    let activePeriod = 'total';

    /**
     * Shows a specific metrics section and updates filter buttons
     * @param {string} filterType - Section to show
     */
    function showMetricsSection(filterType) {
        activePeriod = filterType;

        // Ocultar todas las secciones
        document.querySelectorAll('.metrics-section').forEach(section => {
            section.classList.remove('active');
        });

        // Mostrar la sección correspondiente
        const sectionId = `metrics-${filterType}`;
        const section = document.getElementById(sectionId);
        if (section) {
            section.classList.add('active');
        }

        // Actualizar botones de filtro
        document.querySelectorAll('.metric-filter-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        const activeBtn = document.querySelector(`[data-filter="${filterType}"]`);
        if (activeBtn) {
            activeBtn.classList.add('active');
        }
    }

    /**
     * Clears the current Jira report view
     */
    function clearJiraReport() {
        const uiElements = {
            metricsContent: document.getElementById('metrics-content'),
            welcomeCard: document.querySelector('.jira-welcome-card'),
            projectInput: document.getElementById('project-selector-input'),
            projectHidden: document.getElementById('project-selector'),
            widgetsContainer: document.getElementById('widgets-container'),
            downloadButton: document.getElementById('download-button'),
            customizeButton: document.getElementById('customize-button')
        };

        if (uiElements.metricsContent) uiElements.metricsContent.style.display = 'none';
        if (uiElements.welcomeCard) uiElements.welcomeCard.style.display = 'block';
        if (uiElements.projectInput) uiElements.projectInput.value = '';
        if (uiElements.projectHidden) uiElements.projectHidden.value = '';
        if (uiElements.widgetsContainer) uiElements.widgetsContainer.innerHTML = '';
        if (uiElements.downloadButton) uiElements.downloadButton.classList.remove('visible');
        if (uiElements.customizeButton) uiElements.customizeButton.style.display = 'none';
    }

    /**
     * Refreshes all metrics after invalidating cache
     */
    async function refreshMetrics() {
        if (Dashboard.clearMetricsCache) {
            Dashboard.clearMetricsCache();
        }
        if (Dashboard.loadAllMetrics) {
            await Dashboard.loadAllMetrics();
        }
    }

    /**
     * Resets all metrics for the system (Admin only)
     */
    async function resetMetrics() {
        if (window.USER_ROLE !== 'admin') {
            alert('❌ No tienes permisos para realizar esta acción. Solo el administrador puede reiniciar métricas.');
            return;
        }

        if (!confirm('⚠️ ¿Estás seguro de que quieres reiniciar TODAS las métricas?\n\nEsta acción eliminará:\n- Todas las historias de usuario generadas\n- Todos los casos de prueba generados\n- Todos los reportes de Jira\n- Todas las cargas masivas\n\nEsta acción NO se puede deshacer.')) {
            return;
        }

        try {
            const csrfToken = window.getCsrfToken ? window.getCsrfToken() :
                (document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '');

            const response = await fetch('/api/dashboard/clear-metrics', {
                method: 'DELETE',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Error al limpiar métricas');
            }

            const data = await response.json();

            alert(`✅ Métricas limpiadas exitosamente:\n\n` +
                `- ${data.deleted.stories} historias eliminadas\n` +
                `- ${data.deleted.test_cases} casos de prueba eliminados\n` +
                `- ${data.deleted.reports} reportes eliminados\n` +
                `- ${data.deleted.bulk_uploads} cargas masivas eliminadas`);

            await refreshMetrics();

        } catch (error) {
            console.error('Error al reiniciar métricas:', error);
            alert(`❌ Error al reiniciar métricas: ${error.message}`);
        }
    }

    /**
     * Optimistic update for metrics counters
     * @param {string} type - Metric type
     * @param {number} count - Count to add
     * @param {string} area - Area (not used in current logic)
     */
    async function updateMetrics(type, count, area = null) {
        try {
            if (activePeriod === 'total') {
                const elementId = type === 'stories' ? 'stories-count' : (type === 'test_cases' ? 'test-cases-count' : null);
                if (elementId) {
                    const el = document.getElementById(elementId);
                    if (el) {
                        const current = parseInt(el.textContent.replace(/,/g, '')) || 0;
                        el.textContent = (current + count).toLocaleString();
                    }
                }
            }
        } catch (e) {
            console.warn('Error updating metric UI optimistically:', e);
        }

        await refreshMetrics();
    }

    // Export internal functions
    window.NexusModules.Dashboard.showMetricsSection = showMetricsSection;
    window.NexusModules.Dashboard.clearJiraReport = clearJiraReport;
    window.NexusModules.Dashboard.refreshMetrics = refreshMetrics;
    window.NexusModules.Dashboard.resetMetrics = resetMetrics;
    window.NexusModules.Dashboard.updateMetrics = updateMetrics;

})(window);
