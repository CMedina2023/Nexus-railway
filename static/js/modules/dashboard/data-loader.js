/**
 * Nexus AI - Dashboard Data Loader Module
 * Orchestrates data fetching and distribution to charts and renderers.
 */

(function (window) {
    'use strict';

    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Dashboard = window.NexusModules.Dashboard || {};

    const Dashboard = window.NexusModules.Dashboard;
    const renderers = Dashboard.renderers;

    /**
     * Updates counters on the main dashboard landing view
     */
    async function loadDashboardMetrics() {
        try {
            const generatorMetrics = await Dashboard.getMetrics();
            const jiraMetrics = await Dashboard.getJiraMetrics();

            if (renderers && renderers.updateDashboardSummaryCounters) {
                renderers.updateDashboardSummaryCounters(generatorMetrics, jiraMetrics);
            }
        } catch (error) {
            console.error('Error al cargar métricas del dashboard:', error);
        }
    }

    /**
     * Loads generator specific metrics and updates charts/history
     */
    async function loadMetrics() {
        try {
            const metrics = await Dashboard.getMetrics();

            // Update counters
            if (renderers && renderers.updateGeneratorCounters) {
                renderers.updateGeneratorCounters(metrics);
            }

            // Calculate area distribution for charts
            const areaDistribution = {};
            if (metrics.history) {
                metrics.history.forEach(item => {
                    let area = item.area;
                    if (!area || area === 'UNKNOWN' || area === 'No especificada' || area === 'Sin Área') {
                        area = 'Sin Área';
                    }
                    areaDistribution[area] = (areaDistribution[area] || 0) + (item.count || 1);
                });
            }

            // Update area distribution chart
            if (Dashboard.updateAreaChart) {
                Dashboard.updateAreaChart(areaDistribution);
            }

            // Update history list
            if (renderers && renderers.renderGeneratorsHistory) {
                renderers.renderGeneratorsHistory(metrics.history);
            }
        } catch (error) {
            console.error('Error al cargar métricas de generadores:', error);
        }
    }

    /**
     * Loads Jira specific metrics (Reports and Uploads)
     */
    async function loadJiraMetrics() {
        try {
            const jiraMetrics = await Dashboard.getJiraMetrics();

            // ========== MÉTRICAS DE REPORTES ==========
            if (renderers && renderers.updateJiraReportsCounters) {
                renderers.updateJiraReportsCounters(jiraMetrics.reports);
            }

            // Render charts
            if (Dashboard.updateReportsCharts) {
                Dashboard.updateReportsCharts(jiraMetrics.reports);
            }

            // Render project summaries
            if (renderers && renderers.renderJiraMetricsByProject) {
                renderers.renderJiraMetricsByProject('reports', jiraMetrics.reports.byProject);
            }

            // Render history
            if (renderers && renderers.renderReportsHistory) {
                renderers.renderReportsHistory(jiraMetrics.reports.history || []);
            }

            // ========== MÉTRICAS DE CARGAS ==========
            if (renderers && renderers.updateJiraUploadsCounters) {
                renderers.updateJiraUploadsCounters(jiraMetrics.uploads);
            }

            // Render charts
            if (Dashboard.updateUploadsCharts) {
                Dashboard.updateUploadsCharts(jiraMetrics.uploads);
            }

            // Render project summaries
            if (renderers && renderers.renderJiraMetricsByProject) {
                renderers.renderJiraMetricsByProject('uploads', jiraMetrics.uploads.byProject);
            }

            // Render history
            if (renderers && renderers.renderUploadsHistory) {
                renderers.renderUploadsHistory(jiraMetrics.uploads.history || []);
            }
        } catch (error) {
            console.error('Error al cargar métricas de Jira:', error);
        }
    }

    /**
     * Loads all metrics for the dashboard
     */
    async function loadAllMetrics() {
        await Promise.all([
            loadMetrics(),
            loadJiraMetrics()
        ]);

        // Ensure active section is shown if navigation state exists
        const activeFilter = document.querySelector('.metric-filter-btn.active');
        if (activeFilter && Dashboard.showMetricsSection) {
            const filterType = activeFilter.getAttribute('data-filter');
            Dashboard.showMetricsSection(filterType);
        }
    }

    // Export internal functions
    window.NexusModules.Dashboard.loadDashboardMetrics = loadDashboardMetrics;
    window.NexusModules.Dashboard.loadMetrics = loadMetrics;
    window.NexusModules.Dashboard.loadJiraMetrics = loadJiraMetrics;
    window.NexusModules.Dashboard.loadAllMetrics = loadAllMetrics;

})(window);
