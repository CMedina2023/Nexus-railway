/**
 * Nexus AI - Dashboard & Metrics Module
 * Entry point that exposes functionality from sub-modules.
 * NOW MODULARIZED: Logic is in dashboard/data.js, dashboard/charts.js, dashboard/templates.js, dashboard/renderers.js, dashboard/ui-interactions.js, dashboard/data-loader.js
 */

(function (window) {
    'use strict';

    window.NexusModules = window.NexusModules || {};
    // Ensure the namespace exists (should be populated by submodules)
    window.NexusModules.Dashboard = window.NexusModules.Dashboard || {};

    const Dashboard = window.NexusModules.Dashboard;

    // Backward Compatibility aliases (to be removed in future)
    window.fetchDashboardMetrics = Dashboard.fetchDashboardMetrics;
    window.getMetrics = Dashboard.getMetrics;
    window.getJiraMetrics = Dashboard.getJiraMetrics;
    window.loadDashboardMetrics = Dashboard.loadDashboardMetrics;
    window.loadMetrics = Dashboard.loadMetrics;
    window.loadAllMetrics = Dashboard.loadAllMetrics;
    window.loadJiraMetrics = Dashboard.loadJiraMetrics;
    window.updateMetrics = Dashboard.updateMetrics;
    window.showMetricsSection = Dashboard.showMetricsSection;
    window.resetMetrics = Dashboard.resetMetrics;
    window.clearJiraReport = Dashboard.clearJiraReport;
    window.refreshMetrics = Dashboard.refreshMetrics;

})(window);
