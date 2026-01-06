/**
 * Nexus AI - Jira Reports Data Module
 * Handles data fetching (API/SSE) for Jira reports.
 */

(function (window) {
    'use strict';

    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Jira = window.NexusModules.Jira || {};
    window.NexusModules.Jira.Reports = window.NexusModules.Jira.Reports || {};

    const State = window.NexusModules.Jira.Reports.State;
    // We assume these functions will be available on the namespace
    // Ideally we'd pass them in or use the namespace
    // But since they are siblings, they will be attached to NexusModules.Jira.Reports

    async function initJiraReports() {
        const hub = document.getElementById('report-hub');
        const generationView = document.getElementById('report-generation-view');
        if (hub) hub.style.display = 'block';
        if (generationView) generationView.style.display = 'none';

        const statusCard = document.getElementById('jira-connection-status');
        const statusIcon = document.getElementById('connection-icon');
        const statusMessage = document.getElementById('connection-message');

        try {
            const response = await fetch('/api/jira/test-connection');
            const data = await response.json();

            if (data.success) {
                if (statusCard) statusCard.style.display = 'none';
                if (window.NexusModules.Jira.Reports.loadProjects) {
                    window.NexusModules.Jira.Reports.loadProjects();
                }
            } else {
                if (statusCard) {
                    statusCard.style.display = 'block';
                    statusIcon.textContent = '❌';
                    statusMessage.textContent = `Error de conexión: ${data.error || 'No se pudo conectar'}`;
                }
            }
        } catch (error) {
            if (statusCard) {
                statusCard.style.display = 'block';
                statusIcon.textContent = '❌';
                statusMessage.textContent = `Error: ${error.message}`;
            }
        }
    }

    async function loadProjectMetrics(projectKey, projectName, filters = null, forceRefresh = false) {
        State.currentProjectKey = projectKey;

        // Reset widgets cache from dashboard if available
        if (window.widgetDataCache) window.widgetDataCache = {};

        const reportSection = document.getElementById('jira-report-section');
        const metricsContent = document.getElementById('metrics-content');
        const metricsLoading = document.getElementById('metrics-loading');
        const metricsError = document.getElementById('metrics-error');

        const welcomeCard = reportSection ? reportSection.querySelector('.jira-welcome-card') : null;
        if (welcomeCard) welcomeCard.style.display = 'none';

        if (reportSection) reportSection.style.display = 'block';
        if (metricsContent) metricsContent.style.display = 'none';
        if (metricsLoading) metricsLoading.style.display = 'block';
        if (metricsError) metricsError.style.display = 'none';

        if (State.grTestCasesChart) {
            State.grTestCasesChart.destroy();
            State.grTestCasesChart = null;
        }
        if (State.grBugsSeverityChart) {
            State.grBugsSeverityChart.destroy();
            State.grBugsSeverityChart = null;
        }

        try {
            const userRole = window.USER_ROLE || "";
            const viewType = userRole === 'admin' ? 'general' : 'personal';
            let url = `/api/jira/metrics/${projectKey}?view_type=${viewType}`;

            if (forceRefresh) {
                url += '&force_refresh=true';
            }

            if (filters) {
                if (filters.testCases || filters.bugs) {
                    if (filters.testCases) {
                        filters.testCases.forEach(f => url += `&filter_testcase=${encodeURIComponent(f.field)}:${encodeURIComponent(f.value)}`);
                    }
                    if (filters.bugs) {
                        filters.bugs.forEach(f => url += `&filter_bug=${encodeURIComponent(f.field)}:${encodeURIComponent(f.value)}`);
                    }
                } else if (Array.isArray(filters)) {
                    filters.forEach(f => url += `&filter=${encodeURIComponent(f.field)}:${encodeURIComponent(f.value)}`);
                }
            }

            const response = await fetch(url);
            const data = await response.json();

            if (response.ok && data.project_key) {
                const metrics = {
                    test_cases: data.test_cases || {},
                    bugs: data.bugs || {},
                    general_report: data.general_report || {},
                    total_issues: data.total_issues || 0
                };
                if (window.NexusModules.Jira.Reports.displayMetrics) {
                    window.NexusModules.Jira.Reports.displayMetrics(metrics);
                }
                if (metricsLoading) metricsLoading.style.display = 'none';
                if (metricsContent) metricsContent.style.display = 'block';
            } else {
                await loadProjectMetricsWithSSE(projectKey, viewType, filters, forceRefresh);
            }
        } catch (error) {
            console.error('Error en loadProjectMetrics, intentando con SSE:', error);
            const userRole = window.USER_ROLE || "";
            const viewType = userRole === 'admin' ? 'general' : 'personal';
            await loadProjectMetricsWithSSE(projectKey, viewType, filters, forceRefresh);
        }
    }

    async function loadProjectMetricsWithSSE(projectKey, viewType, filters = null, forceRefresh = false) {
        const metricsContent = document.getElementById('metrics-content');
        const metricsLoading = document.getElementById('metrics-loading');
        const metricsError = document.getElementById('metrics-error');

        if (metricsLoading) metricsLoading.style.display = 'block';
        if (metricsError) metricsError.style.display = 'none';

        let progressElement = document.getElementById('metrics-progress');
        if (!progressElement && metricsLoading) {
            progressElement = document.createElement('div');
            progressElement.id = 'metrics-progress';
            progressElement.className = 'metrics-progress';
            progressElement.innerHTML = '<div class="progress-bar"><div class="progress-fill"></div></div><div class="progress-text">⏳ Iniciando...</div>';
            metricsLoading.appendChild(progressElement);
        }

        try {
            let url = `/api/jira/metrics/${projectKey}/stream?view_type=${viewType}`;

            if (forceRefresh) {
                url += '&force_refresh=true';
            }

            if (filters) {
                if (filters.testCases || filters.bugs) {
                    if (filters.testCases) {
                        filters.testCases.forEach(f => url += `&filter_testcase=${encodeURIComponent(f.field)}:${encodeURIComponent(f.value)}`);
                    }
                    if (filters.bugs) {
                        filters.bugs.forEach(f => url += `&filter_bug=${encodeURIComponent(f.field)}:${encodeURIComponent(f.value)}`);
                    }
                } else if (Array.isArray(filters)) {
                    filters.forEach(f => url += `&filter=${encodeURIComponent(f.field)}:${encodeURIComponent(f.value)}`);
                }
            }

            const eventSource = new EventSource(url);

            eventSource.onmessage = function (event) {
                try {
                    const data = JSON.parse(event.data);
                    if (data.tipo === 'inicio') {
                        const total = data.total || 0;
                        progressElement.innerHTML = data.desde_cache ?
                            '<div class="progress-text">✅ Obteniendo desde caché...</div>' :
                            `<div class="progress-text">⏳ Obteniendo ${total.toLocaleString()} issues...</div>`;
                    } else if (data.tipo === 'progreso') {
                        const actual = data.actual || 0;
                        const total = data.total || 1;
                        const porcentaje = data.porcentaje || 0;
                        const progressFill = progressElement.querySelector('.progress-fill');
                        const progressText = progressElement.querySelector('.progress-text');
                        if (progressFill) progressFill.style.width = `${porcentaje}%`;
                        if (progressText) progressText.textContent = `⏳ Obteniendo: ${actual.toLocaleString()} de ${total.toLocaleString()} issues (${porcentaje}%)`;
                    } else if (data.tipo === 'calculando') {
                        progressElement.innerHTML = '<div class="progress-text">🔄 Calculando métricas...</div>';
                    } else if (data.tipo === 'completado') {
                        eventSource.close();
                        const metrics = {
                            test_cases: data.reporte.test_cases || {},
                            bugs: data.reporte.bugs || {},
                            general_report: data.reporte.general_report || {},
                            total_issues: data.reporte.total_issues || 0
                        };
                        if (window.NexusModules.Jira.Reports.displayMetrics) {
                            window.NexusModules.Jira.Reports.displayMetrics(metrics);
                        }
                        if (metricsLoading) metricsLoading.style.display = 'none';
                        if (metricsContent) metricsContent.style.display = 'block';
                        if (progressElement.parentNode) progressElement.remove();
                    } else if (data.tipo === 'error') {
                        eventSource.close();
                        if (metricsLoading) metricsLoading.style.display = 'none';
                        if (metricsError) {
                            metricsError.style.display = 'block';
                            metricsError.innerHTML = `<span>❌ ${data.mensaje || 'Error al generar el reporte'}</span>`;
                        }
                        if (progressElement.parentNode) progressElement.remove();
                    }
                } catch (parseError) {
                    console.error('Error al parsear evento SSE:', parseError);
                }
            };

            eventSource.onerror = function (error) {
                console.error('Error en SSE:', error);
                eventSource.close();
                if (metricsLoading) metricsLoading.style.display = 'none';
                if (metricsError) {
                    metricsError.style.display = 'block';
                    metricsError.innerHTML = '<span>❌ Error de conexión al generar el reporte</span>';
                }
                if (progressElement && progressElement.parentNode) progressElement.remove();
            };

        } catch (error) {
            console.error('Error al iniciar SSE:', error);
            if (metricsLoading) metricsLoading.style.display = 'none';
            if (metricsError) {
                metricsError.style.display = 'block';
                metricsError.innerHTML = `<span>❌ Error: ${error.message}</span>`;
            }
            if (progressElement && progressElement.parentNode) progressElement.remove();
        }
    }

    async function saveReport(title, projectKey, content) {
        const response = await fetch('/api/jira/reports/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.getCsrfToken ? window.getCsrfToken() : ''
            },
            body: JSON.stringify({
                title: title,
                project_key: projectKey,
                report_content: content
            })
        });
        return await response.json();
    }

    async function fetchMyReports(page = 1, perPage = 10) {
        const response = await fetch(`/api/jira/reports/list?page=${page}&per_page=${perPage}&_t=${new Date().getTime()}`);
        return await response.json();
    }

    async function getReportDetail(id) {
        const response = await fetch(`/api/jira/reports/${id}?_t=${new Date().getTime()}`);
        return await response.json();
    }

    async function deleteReport(id) {
        const response = await fetch(`/api/jira/reports/${id}`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': window.getCsrfToken ? window.getCsrfToken() : ''
            }
        });
        return await response.json();
    }

    async function updateReport(id, data) {
        const response = await fetch(`/api/jira/reports/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.getCsrfToken ? window.getCsrfToken() : ''
            },
            body: JSON.stringify(data)
        });
        return await response.json();
    }

    window.NexusModules.Jira.Reports.initJiraReports = initJiraReports;
    window.NexusModules.Jira.Reports.loadProjectMetrics = loadProjectMetrics;
    window.NexusModules.Jira.Reports.loadProjectMetricsWithSSE = loadProjectMetricsWithSSE;

    // New Data API
    window.NexusModules.Jira.Reports.Data = {
        saveReport,
        fetchMyReports,
        getReportDetail,
        deleteReport,
        updateReport
    };

})(window);
