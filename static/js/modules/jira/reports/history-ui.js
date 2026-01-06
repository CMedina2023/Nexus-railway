/**
 * Nexus AI - Jira Reports History UI Module
 * Handles the "My Reports" view and interactions.
 */

(function (window) {
    'use strict';

    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Jira = window.NexusModules.Jira || {};
    window.NexusModules.Jira.Reports = window.NexusModules.Jira.Reports || {};

    const State = window.NexusModules.Jira.Reports.State;
    const Data = window.NexusModules.Jira.Reports.Data;
    const UI = window.NexusModules.Jira.Reports; // Main UI module

    async function loadMyReports(page = 1) {
        const container = document.getElementById('history-list-container');
        const loading = document.getElementById('history-loading');
        const empty = document.getElementById('history-empty');
        const tbody = document.getElementById('history-table-body');
        const pagination = document.getElementById('history-pagination');

        if (loading) loading.style.display = 'block';
        if (container) container.style.display = 'none';
        if (empty) empty.style.display = 'none';

        try {
            const result = await Data.fetchMyReports(page);

            if (loading) loading.style.display = 'none';

            if (result.success && result.data.items && result.data.items.length > 0) {
                if (container) container.style.display = 'block';
                renderReportsTable(result.data.items, tbody);
                renderPagination(result.data, pagination);
            } else {
                if (empty) empty.style.display = 'block';
            }
        } catch (error) {
            console.error('Error loading reports:', error);
            if (loading) loading.style.display = 'none';
            // Show error
        }
    }

    function renderReportsTable(items, tbody) {
        if (!tbody) return;
        tbody.innerHTML = items.map(item => `
            <tr>
                <td style="font-weight: 500; color: var(--text-primary);">
                    ${item.report_title || 'Sin título'}
                </td>
                <td>
                    <span class="badge ${item.project_key ? 'badge-blue' : 'badge-gray'}">
                        ${item.project_key || 'N/A'}
                    </span>
                </td>
                <td>${formatDate(item.created_at)}</td>
                <td>${formatDate(item.updated_at)}</td>
                <td>
                    <div class="action-buttons">
                        <button class="action-btn view" onclick="window.viewSavedReport(${item.id})" title="Ver Reporte">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="action-btn update" onclick="window.updateSavedReport(${item.id})" title="Actualizar Datos">
                            <i class="fas fa-sync-alt"></i>
                        </button>
                        <button class="action-btn delete" onclick="window.deleteSavedReport(${item.id})" title="Eliminar">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    function renderPagination(meta, container) {
        if (!container) return;

        let html = '';
        if (meta.total_pages > 1) {
            html += `<div class="pagination-info">Página ${meta.page} de ${meta.total_pages} (${meta.total} reportes)</div>`;
            html += `<div class="pagination-controls">`;

            // Prev
            html += `<button class="pagination-btn" ${meta.page <= 1 ? 'disabled' : ''} onclick="window.loadMyReportsPage(${meta.page - 1})">«</button>`;

            // Pages (simple version)
            html += `<span class="pagination-page"> ${meta.page} </span>`;

            // Next
            html += `<button class="pagination-btn" ${meta.page >= meta.total_pages ? 'disabled' : ''} onclick="window.loadMyReportsPage(${meta.page + 1})">»</button>`;

            html += `</div>`;
        } else {
            html += `<div class="pagination-info">Mostrando ${meta.items.length} reportes</div>`;
        }

        container.innerHTML = html;
        container.style.display = 'flex';
        container.style.justifyContent = 'space-between';
    }

    function formatDate(dateStr) {
        if (!dateStr) return '-';
        return new Date(dateStr).toLocaleDateString() + ' ' + new Date(dateStr).toLocaleTimeString();
    }

    async function viewSavedReport(id) {
        try {
            const response = await Data.getReportDetail(id);
            if (response.success) {
                const report = response.data;
                const content = typeof report.report_content === 'string'
                    ? JSON.parse(report.report_content)
                    : report.report_content;

                // Set state to indicate we are viewing a saved report
                State.currentSavedReportId = report.id;
                State.currentProjectKey = report.project_key;

                // Update Back Button Text
                if (UI.updateBackButtonState) UI.updateBackButtonState();

                // switchReportOperation displays the 'report-generation-view' but keeps children state.
                // We need to explicitly hide the history view
                const historyView = document.getElementById('report-history-view');
                if (historyView) historyView.style.display = 'none';

                UI.switchReportOperation('generation');

                // 1. Ocultar estrictamente el Wizard (Selector y Pasos)
                const projectsSection = document.getElementById('jira-projects-section');
                if (projectsSection) projectsSection.style.setProperty('display', 'none', 'important');

                // 2. Ocultar tarjeta de bienvenida
                const welcomeCard = document.querySelector('.jira-welcome-card');
                if (welcomeCard) welcomeCard.style.display = 'none';

                // 3. Asegurar que la sección de reporte y contenido sea visible
                const reportSection = document.getElementById('jira-report-section');
                if (reportSection) reportSection.style.display = 'block';

                const metricsContent = document.getElementById('metrics-content');
                if (metricsContent) metricsContent.style.display = 'block';

                // 4. Reconstruir objeto de métricas para Chart.js
                // Usamos 'raw_data' si existe (nuevos guardados), o fallback a lo que haya en general_report
                const rawTestCases = content.raw_data?.test_cases_by_status ||
                    content.general_report?.test_cases_by_status || {};

                const rawBugs = content.raw_data?.bugs_by_severity_open ||
                    content.general_report?.bugs_by_severity_open || {};

                // Inyectamos los datos de bugs en general_report porque ahí los busca 'displayGeneralReport'
                const generalReportWithData = { ...content.general_report };
                if (!generalReportWithData.bugs_by_severity_open) {
                    generalReportWithData.bugs_by_severity_open = rawBugs;
                }

                const metrics = {
                    general_report: generalReportWithData,
                    test_cases: {
                        by_status: rawTestCases
                    },
                    bugs: {} // La estructura actual no usa esto directamente para el gráfico, sino general_report
                };

                UI.displayMetrics(metrics);

                // Hide "Save" button or change text?
                // For now, hide it as we are viewing.
                const saveBtn = document.getElementById('save-report-btn');
                if (saveBtn) saveBtn.style.display = 'none';

                // Restore active widgets if present
                if (content.active_widgets && Array.isArray(content.active_widgets)) {
                    window.activeWidgets = content.active_widgets;
                    window.widgetDataCache = content.widget_data;
                    if (typeof window.renderActiveWidgets === 'function') {
                        window.renderActiveWidgets();
                    }
                }

                // Restore filters visually? (Optional)
            }
        } catch (e) {
            console.error(e);
            alert('Error al cargar reporte');
        }
    }

    async function updateSavedReport(id) {
        if (!confirm('¿Desea actualizar este reporte con datos en tiempo real de Jira?')) return;

        try {
            const response = await Data.getReportDetail(id);
            if (response.success) {
                const report = response.data;
                const content = typeof report.report_content === 'string'
                    ? JSON.parse(report.report_content)
                    : report.report_content;

                // Set state
                State.currentSavedReportId = report.id;
                State.currentProjectKey = report.project_key;

                // Update Back Button Text
                if (UI.updateBackButtonState) UI.updateBackButtonState();

                // 1. Ocultar estrictamente el Historial
                const historyView = document.getElementById('report-history-view');
                if (historyView) historyView.style.display = 'none';

                // Switch view
                UI.switchReportOperation('generation');

                // 2. Ocultar estrictamente el Wizard (Selector y Pasos)
                const projectsSection = document.getElementById('jira-projects-section');
                if (projectsSection) projectsSection.style.setProperty('display', 'none', 'important');

                // 3. Ocultar tarjeta de bienvenida
                const welcomeCard = document.querySelector('.jira-welcome-card');
                if (welcomeCard) welcomeCard.style.display = 'none';

                // 4. Asegurar contenedor visible
                const reportSection = document.getElementById('jira-report-section');
                if (reportSection) reportSection.style.display = 'block';

                // Trigger Generation
                // Retrieve filters from saved content
                const filters = content.filters || null;
                const userRole = window.USER_ROLE || "";
                const viewType = userRole === 'admin' ? 'general' : 'personal';

                // Call SSE
                await UI.loadProjectMetricsWithSSE(report.project_key, viewType, filters, true);

                // Show "Update" button instead of Save
                const saveBtn = document.getElementById('save-report-btn');
                if (saveBtn) {
                    saveBtn.classList.add('visible');
                    saveBtn.setAttribute('data-update-id', report.id);
                    saveBtn.querySelector('span').textContent = 'Guardar Actualización';
                }
            }
        } catch (e) {
            console.error(e);
            alert('Error al iniciar actualización');
        }
    }

    async function deleteSavedReport(id) {
        if (!confirm('¿Está seguro de eliminar este reporte?')) return;
        try {
            const res = await Data.deleteReport(id);
            if (res.success) {
                loadMyReports(1); // Refresh
            } else {
                alert('Error al eliminar: ' + res.error);
            }
        } catch (e) {
            console.error(e);
            alert('Error al eliminar reporte');
        }
    }

    // Expose
    window.loadMyReportsPage = loadMyReports;
    window.viewSavedReport = viewSavedReport;
    window.updateSavedReport = updateSavedReport;
    window.deleteSavedReport = deleteSavedReport;

    window.NexusModules.Jira.Reports.History = {
        loadMyReports
    };

})(window);
