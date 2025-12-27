/**
 * Nexus AI - Jira Reports Tables Module
 * Handles table rendering and pagination logic.
 */

(function (window) {
    'use strict';

    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Jira = window.NexusModules.Jira || {};
    window.NexusModules.Jira.Reports = window.NexusModules.Jira.Reports || {};

    const State = window.NexusModules.Jira.Reports.State;

    function renderTestCasesTable() {
        const body = document.getElementById('gr-test-cases-table-body');
        if (!body) return;

        body.innerHTML = '';
        const start = (State.testCasesPagination.currentPage - 1) * State.testCasesPagination.itemsPerPage;
        const end = start + State.testCasesPagination.itemsPerPage;
        const pageData = State.testCasesPagination.data.slice(start, end);

        pageData.forEach(({ person, stats }) => {
            const row = document.createElement('tr');
            const displayName = person.length > 25 ? person.substring(0, 25) + '...' : person;
            row.innerHTML = `
                <td>${displayName}</td>
                <td>${stats.exitoso || 0}</td>
                <td>${stats.en_progreso > 0 ? `<span class="report-badge report-badge-warning">${stats.en_progreso}</span>` : '-'}</td>
                <td>${stats.fallado > 0 ? `<span class="report-badge report-badge-error">${stats.fallado}</span>` : '-'}</td>
                <td>${stats.total || 0}</td>
            `;
            body.appendChild(row);
        });

        if (State.testCasesPagination.currentPage === 1 && State.testCasesPagination.totals) {
            const totalRow = document.createElement('tr');
            totalRow.className = 'total-row';
            totalRow.innerHTML = `
                <td><strong>Total</strong></td>
                <td><strong>${State.testCasesPagination.totals.exitoso}</strong></td>
                <td><strong>${State.testCasesPagination.totals.en_progreso}</strong></td>
                <td><strong>${State.testCasesPagination.totals.fallado}</strong></td>
                <td><strong>${State.testCasesPagination.totals.total}</strong></td>
            `;
            body.appendChild(totalRow);
        }

        updateTestCasesPaginationControls();
    }

    function renderDefectsTable() {
        const body = document.getElementById('gr-defects-table-body');
        if (!body) return;

        body.innerHTML = '';
        const start = (State.defectsPagination.currentPage - 1) * State.defectsPagination.itemsPerPage;
        const end = start + State.defectsPagination.itemsPerPage;
        const pageData = State.defectsPagination.data.slice(start, end);

        pageData.forEach(defect => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${defect.key || '-'}</td>
                <td>${defect.assignee || 'Sin asignar'}</td>
                <td>${getStatusBadge(defect.status)}</td>
                <td>${defect.summary || '-'}</td>
                <td>${getSeverityBadge(defect.severity)}</td>
            `;
            body.appendChild(row);
        });

        updateDefectsPaginationControls();
    }

    function updateTestCasesPaginationControls() {
        const totalPages = Math.ceil(State.testCasesPagination.totalItems / State.testCasesPagination.itemsPerPage);
        const startItem = State.testCasesPagination.totalItems > 0 ? (State.testCasesPagination.currentPage - 1) * State.testCasesPagination.itemsPerPage + 1 : 0;
        const endItem = Math.min(State.testCasesPagination.currentPage * State.testCasesPagination.itemsPerPage, State.testCasesPagination.totalItems);

        const info = document.querySelector('#test-cases-pagination .pagination-info');
        const page = document.getElementById('test-cases-page');
        const prev = document.getElementById('test-cases-prev');
        const next = document.getElementById('test-cases-next');

        if (info) info.textContent = `Mostrando ${startItem}-${endItem} de ${State.testCasesPagination.totalItems} registros`;
        if (page) page.textContent = `Página ${State.testCasesPagination.currentPage}`;
        if (prev) prev.disabled = State.testCasesPagination.currentPage === 1;
        if (next) next.disabled = State.testCasesPagination.currentPage >= totalPages;
    }

    function updateDefectsPaginationControls() {
        const totalPages = Math.ceil(State.defectsPagination.totalItems / State.defectsPagination.itemsPerPage);
        const startItem = State.defectsPagination.totalItems > 0 ? (State.defectsPagination.currentPage - 1) * State.defectsPagination.itemsPerPage + 1 : 0;
        const endItem = Math.min(State.defectsPagination.currentPage * State.defectsPagination.itemsPerPage, State.defectsPagination.totalItems);

        const info = document.querySelector('#defects-pagination .pagination-info');
        const page = document.getElementById('defects-page');
        const prev = document.getElementById('defects-prev');
        const next = document.getElementById('defects-next');

        if (info) info.textContent = `Mostrando ${startItem}-${endItem} de ${State.defectsPagination.totalItems} registros`;
        if (page) page.textContent = `Página ${State.defectsPagination.currentPage}`;
        if (prev) prev.disabled = State.defectsPagination.currentPage === 1;
        if (next) next.disabled = State.defectsPagination.currentPage >= totalPages;
    }

    function setupPaginationListeners() {
        if (State.paginationListenersSetup) return;

        const tcPrev = document.getElementById('test-cases-prev');
        const tcNext = document.getElementById('test-cases-next');
        const dPrev = document.getElementById('defects-prev');
        const dNext = document.getElementById('defects-next');

        if (tcPrev) tcPrev.onclick = () => { if (State.testCasesPagination.currentPage > 1) { State.testCasesPagination.currentPage--; renderTestCasesTable(); } };
        if (tcNext) tcNext.onclick = () => { if (State.testCasesPagination.currentPage < Math.ceil(State.testCasesPagination.totalItems / State.testCasesPagination.itemsPerPage)) { State.testCasesPagination.currentPage++; renderTestCasesTable(); } };
        if (dPrev) dPrev.onclick = () => { if (State.defectsPagination.currentPage > 1) { State.defectsPagination.currentPage--; renderDefectsTable(); } };
        if (dNext) dNext.onclick = () => { if (State.defectsPagination.currentPage < Math.ceil(State.defectsPagination.totalItems / State.defectsPagination.itemsPerPage)) { State.defectsPagination.currentPage++; renderDefectsTable(); } };

        State.paginationListenersSetup = true;
    }

    function getStatusBadge(status) {
        const s = status.toLowerCase();
        const type = (s.includes('closed') || s.includes('cerrado') || s.includes('resolved') || s.includes('resuelto')) ? 'success' :
            (s.includes('progress') || s.includes('progreso') || s.includes('análisis')) ? 'warning' : 'error';
        return `<span class="report-badge report-badge-${type}">${status}</span>`;
    }

    function getSeverityBadge(severity) {
        const s = severity.toLowerCase();
        const type = (s.includes('critical') || s.includes('crítico')) ? 'critical' :
            (s.includes('major') || s.includes('mayor') || s.includes('alta')) ? 'major' :
                (s.includes('low') || s.includes('baja') || s.includes('menor')) ? 'low' : '';
        return `<span class="report-badge ${type ? 'report-badge-' + type : ''}">${severity}</span>`;
    }

    window.NexusModules.Jira.Reports.renderTestCasesTable = renderTestCasesTable;
    window.NexusModules.Jira.Reports.renderDefectsTable = renderDefectsTable;
    window.NexusModules.Jira.Reports.setupPaginationListeners = setupPaginationListeners;
    window.NexusModules.Jira.Reports.getStatusBadge = getStatusBadge;
    window.NexusModules.Jira.Reports.getSeverityBadge = getSeverityBadge;

})(window);
