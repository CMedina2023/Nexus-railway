/**
 * Nexus AI - Jira Reports UI Module
 * Handles general UI interactions and main display logic.
 */

(function (window) {
    'use strict';

    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Jira = window.NexusModules.Jira || {};
    window.NexusModules.Jira.Reports = window.NexusModules.Jira.Reports || {};

    const State = window.NexusModules.Jira.Reports.State;
    const Reports = window.NexusModules.Jira.Reports;

    function switchReportOperation(type) {
        const hub = document.getElementById('report-hub');
        const generationView = document.getElementById('report-generation-view');

        if (type === 'generation') {
            if (hub) hub.style.display = 'none';
            if (generationView) generationView.style.display = 'block';
        } else {
            const cardTitle = type === 'history' ? 'Mis Reportes' : 'Reporte Final de Pruebas';
            alert(`ℹ️ El módulo "${cardTitle}" estará disponible en próximas actualizaciones.`);
        }
    }

    function resetReportsToHub() {
        const hub = document.getElementById('report-hub');
        const generationView = document.getElementById('report-generation-view');

        if (hub) hub.style.display = 'block';
        if (generationView) generationView.style.display = 'none';

        // Reiniciar completamente la sección de proyectos y filtros
        if (typeof Reports.showProjectsSection === 'function') {
            Reports.showProjectsSection();
        } else {
            // Fallback
            if (window.NexusModules.Dashboard && window.NexusModules.Dashboard.clearJiraReport) {
                window.NexusModules.Dashboard.clearJiraReport();
            } else if (typeof window.clearJiraReport === 'function') {
                window.clearJiraReport();
            }

            const step2 = document.getElementById('step-2-container');
            const step3 = document.getElementById('step-3-container');
            if (step2) step2.style.display = 'none';
            if (step3) step3.style.display = 'none';
        }
    }

    function displayMetrics(metrics) {
        const testMetrics = metrics.test_cases || {};
        const bugMetrics = metrics.bugs || {};

        if (metrics.general_report && Object.keys(metrics.general_report).length > 0) {
            displayGeneralReport(metrics.general_report, testMetrics, bugMetrics);
        } else {
            const generalReportSection = document.getElementById('general-report-section');
            if (generalReportSection) {
                generalReportSection.innerHTML = '<p style="text-align: center; color: var(--text-muted); padding: 2rem;">No hay datos disponibles para el reporte general.</p>';
                generalReportSection.style.display = 'block';
            }
        }
    }

    function displayGeneralReport(generalReport, testMetrics, bugMetrics) {
        const generalReportSection = document.getElementById('general-report-section');
        if (!generalReportSection) return;

        State.currentGeneralReport = generalReport;
        generalReportSection.style.display = 'block';

        const guiaHeader = document.getElementById('report-header');
        if (guiaHeader) guiaHeader.style.display = 'none';

        const downloadButton = document.getElementById('download-button');
        if (downloadButton) downloadButton.classList.add('visible');

        const customizeButton = document.getElementById('customize-button');
        if (customizeButton) customizeButton.style.display = 'inline-flex';

        // KPIs
        const kpiIds = {
            'gr-total-test-cases': generalReport.total_test_cases,
            'gr-successful-percentage': `${generalReport.successful_test_cases_percentage || 0}%`,
            'gr-real-coverage': `${generalReport.real_coverage || 0}%`,
            'gr-total-defects': generalReport.total_defects,
            'gr-defect-rate': `${generalReport.defect_rate || 0}%`,
            'gr-open-defects': generalReport.open_defects,
            'gr-closed-defects': generalReport.closed_defects
        };

        Object.entries(kpiIds).forEach(([id, val]) => {
            const el = document.getElementById(id);
            if (el) el.textContent = val || (id.includes('percentage') || id.includes('rate') ? '0%' : '0');
        });

        // Charts
        if (Reports.renderTestCasesChart) Reports.renderTestCasesChart(testMetrics.by_status || {});
        if (Reports.renderBugsChart) Reports.renderBugsChart(generalReport.bugs_by_severity_open || {});

        // Tables Data Preparation
        const testCasesByPerson = generalReport.test_cases_by_person || {};
        const testCasesData = [];
        let tExit = 0, tProg = 0, tFall = 0, tTotal = 0;

        Object.entries(testCasesByPerson).forEach(([person, stats]) => {
            testCasesData.push({ person, stats });
            tExit += stats.exitoso || 0;
            tProg += stats.en_progreso || 0;
            tFall += stats.fallado || 0;
            tTotal += stats.total || 0;
        });

        State.testCasesPagination.totals = { exitoso: tExit, en_progreso: tProg, fallado: tFall, total: tTotal };
        State.testCasesPagination.data = testCasesData;
        State.testCasesPagination.totalItems = testCasesData.length;
        State.testCasesPagination.currentPage = 1;

        if (Reports.renderTestCasesTable) Reports.renderTestCasesTable();

        const defectsByPerson = generalReport.defects_by_person || [];
        State.defectsPagination.data = defectsByPerson;
        State.defectsPagination.totalItems = defectsByPerson.length;
        State.defectsPagination.currentPage = 1;

        if (Reports.renderDefectsTable) Reports.renderDefectsTable();

        if (Reports.setupPaginationListeners) Reports.setupPaginationListeners();

        // Trigger dynamic widgets from other module if project info exists
        if (window.activeWidgets && window.activeWidgets.length > 0 && State.currentProjectKey && typeof window.renderActiveWidgets === 'function') {
            window.renderActiveWidgets();
        }
    }

    function showProjectsSection() {
        const projectsSec = document.getElementById('jira-projects-section');
        const reportSec = document.getElementById('jira-report-section');
        const projectInput = document.getElementById('project-selector-input');
        const projectHidden = document.getElementById('project-selector');
        const guiaHeader = document.getElementById('report-header');
        const downloadBtn = document.getElementById('download-button');
        const customizeBtn = document.getElementById('customize-button');

        if (projectInput) projectInput.value = '';
        if (projectHidden) projectHidden.value = '';
        if (guiaHeader) guiaHeader.style.display = 'block';
        if (projectsSec) projectsSec.style.display = 'block';
        if (downloadBtn) downloadBtn.classList.remove('visible');
        if (customizeBtn) customizeBtn.style.display = 'none';

        if (typeof window.activeWidgets !== 'undefined') {
            window.activeWidgets = [];
            window.widgetDataCache = {};
            if (typeof window.renderActiveWidgets === 'function') window.renderActiveWidgets();
        }

        // Reset Filter State
        State.reportActiveFilters = [];
        State.reportActiveFiltersTestCases = [];
        State.reportActiveFiltersBugs = [];
        State.reportFilterCount = 0;
        State.reportAvailableFields = [];
        State.reportAvailableFieldsTestCases = [];
        State.reportAvailableFieldsBugs = [];

        const gridTC = document.getElementById('filters-grid-test-case');
        const gridBug = document.getElementById('filters-grid-bug');
        if (gridTC) gridTC.innerHTML = '';
        if (gridBug) gridBug.innerHTML = '';

        const activeCont = document.getElementById('active-report-filters');
        if (activeCont) activeCont.innerHTML = '<div style="width: 100%; margin-bottom: 0.5rem; font-size: 0.85rem; color: var(--text-muted); font-weight: 600;">Filtros Activos:</div>';

        ['test-case-filter-count', 'bug-filter-count'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = '0';
        });

        // Reset Steps
        const s1 = document.getElementById('step-1-container');
        const s2 = document.getElementById('step-2-container');
        const s3 = document.getElementById('step-3-container');
        if (s1) s1.classList.remove('completed', 'active');
        if (s2) { s2.style.display = 'none'; s2.classList.remove('active'); }
        if (s3) { s3.style.display = 'none'; s3.classList.remove('active'); }

        const welcome = reportSec ? reportSec.querySelector('.jira-welcome-card') : null;
        if (welcome) welcome.style.display = 'block';

        const metricsCont = document.getElementById('metrics-content');
        if (metricsCont) metricsCont.style.display = 'none';

        State.currentProjectKey = null;
        State.paginationListenersSetup = false;
        State.testCasesPagination = { currentPage: 1, itemsPerPage: 10, totalItems: 0, data: [], totals: null };
        State.defectsPagination = { currentPage: 1, itemsPerPage: 10, totalItems: 0, data: [] };

        if (State.grTestCasesChart) { State.grTestCasesChart.destroy(); State.grTestCasesChart = null; }
        if (State.grBugsSeverityChart) { State.grBugsSeverityChart.destroy(); State.grBugsSeverityChart = null; }
    }

    window.NexusModules.Jira.Reports.switchReportOperation = switchReportOperation;
    window.NexusModules.Jira.Reports.resetReportsToHub = resetReportsToHub;
    window.NexusModules.Jira.Reports.displayMetrics = displayMetrics;
    window.NexusModules.Jira.Reports.displayGeneralReport = displayGeneralReport;
    window.NexusModules.Jira.Reports.showProjectsSection = showProjectsSection;

})(window);
