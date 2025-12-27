/**
 * Nexus AI - Jira Reports Charts Module
 * Handles chart rendering for Jira reports.
 */

(function (window) {
    'use strict';

    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Jira = window.NexusModules.Jira || {};
    window.NexusModules.Jira.Reports = window.NexusModules.Jira.Reports || {};

    const State = window.NexusModules.Jira.Reports.State;

    function renderTestCasesChart(testStatusData) {
        const ctx = document.getElementById('gr-test-cases-chart');
        if (!ctx) return;

        if (State.grTestCasesChart) {
            State.grTestCasesChart.destroy();
        }

        State.grTestCasesChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(testStatusData),
                datasets: [{
                    data: Object.values(testStatusData),
                    backgroundColor: ['#10b981', '#f59e0b', '#ef4444', '#3b82f6', '#8b5cf6', '#64748b']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { color: '#cbd5e1' } } }
            }
        });
    }

    function renderBugsChart(bugsBySeverity) {
        const canvas = document.getElementById('gr-bugs-severity-chart');
        if (!canvas) return;

        if (State.grBugsSeverityChart) {
            State.grBugsSeverityChart.destroy();
        }

        if (Object.keys(bugsBySeverity).length > 0) {
            State.grBugsSeverityChart = new Chart(canvas, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(bugsBySeverity),
                    datasets: [{
                        data: Object.values(bugsBySeverity),
                        backgroundColor: ['#fbbf24', '#dc2626', '#991b1b', '#f59e0b', '#ef4444']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'bottom', labels: { color: '#cbd5e1' } } }
                }
            });
        } else {
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#64748b';
            ctx.font = '16px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('No hay bugs abiertos', canvas.width / 2, canvas.height / 2);
        }
    }

    window.NexusModules.Jira.Reports.renderTestCasesChart = renderTestCasesChart;
    window.NexusModules.Jira.Reports.renderBugsChart = renderBugsChart;

})(window);
