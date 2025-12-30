/**
 * Nexus AI - Dashboard Renderers Module
 * Handles DOM manipulation and rendering of metrics data.
 */

(function (window) {
    'use strict';

    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Dashboard = window.NexusModules.Dashboard || {};

    const Templates = window.NexusModules.Dashboard.Templates;

    /**
     * Renders the history of generated items (stories/test cases)
     * @param {Array} history - Array of history items
     */
    function renderGeneratorsHistory(history) {
        const historyList = document.getElementById('history-list');
        if (!historyList) return;

        if (!history || history.length === 0) {
            historyList.innerHTML = Templates.historyEmptyStateTemplate('No hay historial aún. Las generaciones aparecerán aquí.');
            return;
        }

        historyList.innerHTML = history.map(item => Templates.historyItemTemplate(item)).join('');
    }

    /**
     * Renders the history of Jira reports
     * @param {Array} history - Array of report history items
     */
    function renderReportsHistory(history) {
        const historyList = document.getElementById('jira-reports-history-list');
        if (!historyList) return;

        if (!history || history.length === 0) {
            historyList.innerHTML = Templates.historyEmptyStateTemplate('No hay historial aún. Los reportes aparecerán aquí.');
            return;
        }

        historyList.innerHTML = history.map(item => Templates.jiraReportHistoryItemTemplate(item)).join('');
    }

    /**
     * Renders the history of Jira uploads
     * @param {Array} history - Array of upload history items
     */
    function renderUploadsHistory(history) {
        const historyList = document.getElementById('jira-uploads-history-list');
        if (!historyList) return;

        if (!history || history.length === 0) {
            historyList.innerHTML = Templates.historyEmptyStateTemplate('No hay historial aún. Las cargas aparecerán aquí.');
            return;
        }

        historyList.innerHTML = history.map(item => Templates.jiraUploadHistoryItemTemplate(item)).join('');
    }

    /**
     * Renders Jira metrics grouped by project
     * @param {string} type - 'reports' or 'uploads'
     * @param {Object} byProject - Metrics data grouped by project key
     */
    function renderJiraMetricsByProject(type, byProject) {
        const containerId = type === 'reports' ? 'jira-reports-by-project' : 'jira-uploads-by-project';
        const container = document.getElementById(containerId);
        if (!container) return;

        const projectKeys = Object.keys(byProject || {});

        if (projectKeys.length === 0) {
            const message = type === 'reports' ? 'No hay reportes realizados aún' : 'No hay cargas realizadas aún';
            container.innerHTML = Templates.emptyStateTemplate(message);
            return;
        }

        container.innerHTML = projectKeys.map(projectKey =>
            Templates.jiraProjectMetricTemplate(type, projectKey, byProject[projectKey])
        ).join('');
    }

    /**
     * Updates counters in the generator metrics section
     * @param {Object} metrics - Generator metrics
     */
    function updateGeneratorCounters(metrics) {
        const storiesCountEl = document.getElementById('stories-count');
        const testCasesCountEl = document.getElementById('test-cases-count');
        const totalCountEl = document.getElementById('total-count');

        if (storiesCountEl) storiesCountEl.textContent = metrics.stories || 0;
        if (testCasesCountEl) testCasesCountEl.textContent = metrics.testCases || 0;
        if (totalCountEl) totalCountEl.textContent = (metrics.stories || 0) + (metrics.testCases || 0);
    }

    /**
     * Updates summary counters on the main dashboard view
     * @param {Object} generatorMetrics - Metrics from generators
     * @param {Object} jiraMetrics - Metrics from Jira
     */
    function updateDashboardSummaryCounters(generatorMetrics, jiraMetrics) {
        // Generator counters
        const generatorStoriesEl = document.getElementById('generator-stories');
        const generatorTestCasesEl = document.getElementById('generator-testcases');

        if (generatorStoriesEl) generatorStoriesEl.textContent = generatorMetrics.stories || 0;
        if (generatorTestCasesEl) generatorTestCasesEl.textContent = generatorMetrics.testCases || 0;

        // Jira Reports counters
        const reportsCountEl = document.getElementById('reports-count');
        const reportsLastEl = document.getElementById('reports-last');

        if (reportsCountEl) reportsCountEl.textContent = jiraMetrics.reports.count || 0;
        if (reportsLastEl) reportsLastEl.textContent = jiraMetrics.reports.lastDate || '-';

        // Jira Uploads counters
        const uploadCountEl = document.getElementById('upload-count');
        const uploadItemsEl = document.getElementById('upload-items');

        if (uploadCountEl) uploadCountEl.textContent = jiraMetrics.uploads.count || 0;
        if (uploadItemsEl) uploadItemsEl.textContent = jiraMetrics.uploads.itemsCount || 0;
    }

    /**
     * Updates counters in the Jira reports section
     * @param {Object} reportsMetrics - Jira reports metrics
     */
    function updateJiraReportsCounters(reportsMetrics) {
        const reportsTotalEl = document.getElementById('jira-reports-total');
        const reportsProjectsCountEl = document.getElementById('jira-reports-projects-count');
        const reportsWeeklyEl = document.getElementById('jira-reports-weekly');

        if (reportsTotalEl) {
            reportsTotalEl.textContent = reportsMetrics.count || 0;
        }

        const projectKeys = Object.keys(reportsMetrics.byProject || {});
        if (reportsProjectsCountEl) {
            reportsProjectsCountEl.textContent = projectKeys.length;
        }

        const sevenDaysAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
        const recentReports = (reportsMetrics.history || []).filter(h =>
            new Date(h.timestamp || h.date).getTime() > sevenDaysAgo
        ).length;

        if (reportsWeeklyEl) {
            reportsWeeklyEl.textContent = recentReports;
        }
    }

    /**
     * Updates counters in the Jira uploads section
     * @param {Object} uploadsMetrics - Jira uploads metrics
     */
    function updateJiraUploadsCounters(uploadsMetrics) {
        const uploadsTotalEl = document.getElementById('jira-uploads-total');
        const uploadsItemsEl = document.getElementById('jira-uploads-items');
        const uploadsProjectsCountEl = document.getElementById('jira-uploads-projects-count');
        const uploadsAvgEl = document.getElementById('jira-uploads-avg');

        if (uploadsTotalEl) {
            uploadsTotalEl.textContent = uploadsMetrics.count || 0;
        }
        if (uploadsItemsEl) {
            uploadsItemsEl.textContent = uploadsMetrics.itemsCount || 0;
        }

        const projectKeys = Object.keys(uploadsMetrics.byProject || {});
        if (uploadsProjectsCountEl) {
            uploadsProjectsCountEl.textContent = projectKeys.length;
        }

        const avgItems = uploadsMetrics.count > 0
            ? Math.round((uploadsMetrics.itemsCount || 0) / uploadsMetrics.count)
            : 0;

        if (uploadsAvgEl) {
            uploadsAvgEl.textContent = avgItems;
        }
    }

    // Export internal functions
    window.NexusModules.Dashboard.renderers = {
        renderGeneratorsHistory,
        renderReportsHistory,
        renderUploadsHistory,
        renderJiraMetricsByProject,
        updateGeneratorCounters,
        updateDashboardSummaryCounters,
        updateJiraReportsCounters,
        updateJiraUploadsCounters
    };

})(window);
