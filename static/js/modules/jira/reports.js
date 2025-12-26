/**
 * Nexus AI - Jira Reports Module
 * Handles all logic related to Jira project selection, project metrics, 
 * report generation, and filtering.
 */

(function (window) {
    'use strict';

    // Ensure namespace exists
    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Jira = window.NexusModules.Jira || {};

    // ============================================
    // State & Variables
    // ============================================
    let grTestCasesChart = null;
    let grBugsSeverityChart = null;
    let currentProjectKey = null;
    let currentGeneralReport = null;
    let allProjects = [];
    let highlightedIndex = -1;

    // Pagination State
    let testCasesPagination = {
        currentPage: 1,
        itemsPerPage: 20,
        totalItems: 0,
        data: [],
        totals: null
    };

    let defectsPagination = {
        currentPage: 1,
        itemsPerPage: 20,
        totalItems: 0,
        data: []
    };

    // Filter System State
    let reportAvailableFields = [];
    let reportAvailableFieldsTestCases = [];
    let reportAvailableFieldsBugs = [];
    let reportFilterCount = 0;
    let reportActiveFilters = [];
    let reportActiveFiltersTestCases = [];
    let reportActiveFiltersBugs = [];
    let currentFilterTab = 'test-case';
    let paginationListenersSetup = false;

    // ============================================
    // Hub & Navigation Logic
    // ============================================

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
        if (typeof showProjectsSection === 'function') {
            showProjectsSection();
        } else {
            // Fallback for safety
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
                loadProjects();
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

    // ============================================
    // Project Selection Logic
    // ============================================

    async function loadProjects() {
        const projectsSection = document.getElementById('jira-projects-section');
        const projectsLoading = document.getElementById('projects-loading');
        const projectsError = document.getElementById('projects-error');
        const reportSection = document.getElementById('jira-report-section');

        if (projectsSection) projectsSection.style.display = 'block';
        if (reportSection) reportSection.style.display = 'block';
        if (projectsLoading) projectsLoading.style.display = 'block';
        if (projectsError) projectsError.style.display = 'none';

        try {
            const response = await fetch('/api/jira/projects');
            const data = await response.json();

            if (data.success && data.projects.length > 0) {
                if (projectsLoading) projectsLoading.style.display = 'none';
                allProjects = data.projects.map(project => ({
                    key: project.key,
                    name: project.name,
                    displayText: `${project.name} (${project.key})`
                }));
            } else {
                if (projectsLoading) projectsLoading.style.display = 'none';
                if (projectsError) {
                    projectsError.style.display = 'block';
                    projectsError.innerHTML = `<span>❌ ${data.error || 'No se encontraron proyectos'}</span>`;
                }
            }
        } catch (error) {
            if (projectsLoading) projectsLoading.style.display = 'none';
            if (projectsError) {
                projectsError.style.display = 'block';
                projectsError.innerHTML = `<span>❌ Error: ${error.message}</span>`;
            }
        }
    }

    function renderProjectOptions(projects) {
        const dropdown = document.getElementById('project-dropdown');
        if (!dropdown) return;

        if (!projects || projects.length === 0) {
            dropdown.innerHTML = '<div class="combobox-option no-results">No se encontraron proyectos</div>';
            dropdown.style.display = 'block';
            return;
        }

        dropdown.innerHTML = '';
        projects.forEach((project) => {
            const option = document.createElement('div');
            option.className = 'combobox-option';
            option.textContent = project.displayText;
            option.dataset.projectKey = project.key;
            option.dataset.projectName = project.name;
            option.onclick = () => selectProject(project.key, project.name, project.displayText);
            dropdown.appendChild(option);
        });

        dropdown.style.display = 'block';
        highlightedIndex = -1;
    }

    function filterProjectOptions(searchText) {
        if (!allProjects || allProjects.length === 0) {
            loadProjects().then(() => {
                const searchLower = searchText.toLowerCase().trim();
                const filtered = searchLower === '' ? allProjects : allProjects.filter(project =>
                    project.name.toLowerCase().includes(searchLower) ||
                    project.key.toLowerCase().includes(searchLower) ||
                    project.displayText.toLowerCase().includes(searchLower)
                );
                renderProjectOptions(filtered);
            });
            return;
        }

        const searchLower = searchText.toLowerCase().trim();
        const filtered = searchLower === '' ? allProjects : allProjects.filter(project =>
            project.name.toLowerCase().includes(searchLower) ||
            project.key.toLowerCase().includes(searchLower) ||
            project.displayText.toLowerCase().includes(searchLower)
        );

        renderProjectOptions(filtered);
    }

    function showProjectDropdown() {
        const dropdown = document.getElementById('project-dropdown');
        const input = document.getElementById('project-selector-input');

        if (!dropdown || !input) return;

        if (!allProjects || allProjects.length === 0) {
            loadProjects().then(() => {
                const searchText = input.value.trim();
                filterProjectOptions(searchText);
            });
            return;
        }

        const searchText = input.value.trim();
        filterProjectOptions(searchText);
    }

    function hideProjectDropdown() {
        setTimeout(() => {
            const dropdown = document.getElementById('project-dropdown');
            if (dropdown) dropdown.style.display = 'none';
            highlightedIndex = -1;
        }, 200);
    }

    function selectProject(projectKey, projectName, displayText) {
        const input = document.getElementById('project-selector-input');
        const hiddenInput = document.getElementById('project-selector');
        const dropdown = document.getElementById('project-dropdown');

        if (input) input.value = displayText;
        if (hiddenInput) hiddenInput.value = projectKey;
        if (dropdown) dropdown.style.display = 'none';

        const step2Container = document.getElementById('step-2-container');
        const step3Container = document.getElementById('step-3-container');

        if (step2Container) {
            step2Container.style.display = 'block';
            step2Container.classList.add('active');
        }
        if (step3Container) {
            step3Container.style.display = 'block';
            step3Container.classList.add('active');
        }

        const step1Container = document.getElementById('step-1-container');
        if (step1Container) step1Container.classList.add('completed');

        if (projectKey) {
            loadFilterFieldsForReport(projectKey);
        }
    }

    function handleProjectKeydown(event) {
        const dropdown = document.getElementById('project-dropdown');
        if (!dropdown || dropdown.style.display === 'none') return;

        const options = dropdown.querySelectorAll('.combobox-option:not(.no-results)');
        if (options.length === 0) return;

        if (event.key === 'ArrowDown') {
            event.preventDefault();
            highlightedIndex = (highlightedIndex + 1) % options.length;
            updateHighlight(options);
        } else if (event.key === 'ArrowUp') {
            event.preventDefault();
            highlightedIndex = highlightedIndex <= 0 ? options.length - 1 : highlightedIndex - 1;
            updateHighlight(options);
        } else if (event.key === 'Enter') {
            event.preventDefault();
            if (highlightedIndex >= 0 && highlightedIndex < options.length) {
                const option = options[highlightedIndex];
                selectProject(option.dataset.projectKey, option.dataset.projectName, option.textContent);
            }
        } else if (event.key === 'Escape') {
            dropdown.style.display = 'none';
            highlightedIndex = -1;
        }
    }

    function updateHighlight(options) {
        options.forEach((option, index) => {
            if (index === highlightedIndex) {
                option.classList.add('highlighted');
                option.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
            } else {
                option.classList.remove('highlighted');
            }
        });
    }

    // ============================================
    // Metrics Loading Logic
    // ============================================

    async function loadProjectMetrics(projectKey, projectName, filters = null) {
        currentProjectKey = projectKey;

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

        if (grTestCasesChart) {
            grTestCasesChart.destroy();
            grTestCasesChart = null;
        }
        if (grBugsSeverityChart) {
            grBugsSeverityChart.destroy();
            grBugsSeverityChart = null;
        }

        try {
            const userRole = window.USER_ROLE || "";
            const viewType = userRole === 'admin' ? 'general' : 'personal';
            let url = `/api/jira/metrics/${projectKey}?view_type=${viewType}`;

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
                displayMetrics(metrics);
                if (metricsLoading) metricsLoading.style.display = 'none';
                if (metricsContent) metricsContent.style.display = 'block';
            } else {
                await loadProjectMetricsWithSSE(projectKey, viewType, filters);
            }
        } catch (error) {
            console.error('Error en loadProjectMetrics, intentando con SSE:', error);
            const userRole = window.USER_ROLE || "";
            const viewType = userRole === 'admin' ? 'general' : 'personal';
            await loadProjectMetricsWithSSE(projectKey, viewType, filters);
        }
    }

    async function loadProjectMetricsWithSSE(projectKey, viewType, filters = null) {
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
                        displayMetrics(metrics);
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

    // ============================================
    // Metrics Rendering Logic
    // ============================================

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

        currentGeneralReport = generalReport;
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
        renderTestCasesChart(testMetrics.by_status || {});
        renderBugsChart(generalReport.bugs_by_severity_open || {});

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

        testCasesPagination.totals = { exitoso: tExit, en_progreso: tProg, fallado: tFall, total: tTotal };
        testCasesPagination.data = testCasesData;
        testCasesPagination.totalItems = testCasesData.length;
        testCasesPagination.currentPage = 1;
        renderTestCasesTable();

        const defectsByPerson = generalReport.defects_by_person || [];
        defectsPagination.data = defectsByPerson;
        defectsPagination.totalItems = defectsByPerson.length;
        defectsPagination.currentPage = 1;
        renderDefectsTable();

        setupPaginationListeners();

        // Trigger dynamic widgets from other module if project info exists
        if (window.activeWidgets && window.activeWidgets.length > 0 && currentProjectKey && typeof window.renderActiveWidgets === 'function') {
            window.renderActiveWidgets();
        }
    }

    function renderTestCasesChart(testStatusData) {
        const ctx = document.getElementById('gr-test-cases-chart');
        if (!ctx) return;
        if (grTestCasesChart) grTestCasesChart.destroy();

        grTestCasesChart = new Chart(ctx, {
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
        if (grBugsSeverityChart) grBugsSeverityChart.destroy();

        if (Object.keys(bugsBySeverity).length > 0) {
            grBugsSeverityChart = new Chart(canvas, {
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

    // ============================================
    // Table Rendering Logic
    // ============================================

    function renderTestCasesTable() {
        const body = document.getElementById('gr-test-cases-table-body');
        if (!body) return;

        body.innerHTML = '';
        const start = (testCasesPagination.currentPage - 1) * testCasesPagination.itemsPerPage;
        const end = start + testCasesPagination.itemsPerPage;
        const pageData = testCasesPagination.data.slice(start, end);

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

        if (testCasesPagination.currentPage === 1 && testCasesPagination.totals) {
            const totalRow = document.createElement('tr');
            totalRow.className = 'total-row';
            totalRow.innerHTML = `
                <td><strong>Total</strong></td>
                <td><strong>${testCasesPagination.totals.exitoso}</strong></td>
                <td><strong>${testCasesPagination.totals.en_progreso}</strong></td>
                <td><strong>${testCasesPagination.totals.fallado}</strong></td>
                <td><strong>${testCasesPagination.totals.total}</strong></td>
            `;
            body.appendChild(totalRow);
        }

        updateTestCasesPaginationControls();
    }

    function renderDefectsTable() {
        const body = document.getElementById('gr-defects-table-body');
        if (!body) return;

        body.innerHTML = '';
        const start = (defectsPagination.currentPage - 1) * defectsPagination.itemsPerPage;
        const end = start + defectsPagination.itemsPerPage;
        const pageData = defectsPagination.data.slice(start, end);

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
        const totalPages = Math.ceil(testCasesPagination.totalItems / testCasesPagination.itemsPerPage);
        const startItem = testCasesPagination.totalItems > 0 ? (testCasesPagination.currentPage - 1) * testCasesPagination.itemsPerPage + 1 : 0;
        const endItem = Math.min(testCasesPagination.currentPage * testCasesPagination.itemsPerPage, testCasesPagination.totalItems);

        const info = document.querySelector('#test-cases-pagination .pagination-info');
        const page = document.getElementById('test-cases-page');
        const prev = document.getElementById('test-cases-prev');
        const next = document.getElementById('test-cases-next');

        if (info) info.textContent = `Mostrando ${startItem}-${endItem} de ${testCasesPagination.totalItems} registros`;
        if (page) page.textContent = `Página ${testCasesPagination.currentPage}`;
        if (prev) prev.disabled = testCasesPagination.currentPage === 1;
        if (next) next.disabled = testCasesPagination.currentPage >= totalPages;
    }

    function updateDefectsPaginationControls() {
        const totalPages = Math.ceil(defectsPagination.totalItems / defectsPagination.itemsPerPage);
        const startItem = defectsPagination.totalItems > 0 ? (defectsPagination.currentPage - 1) * defectsPagination.itemsPerPage + 1 : 0;
        const endItem = Math.min(defectsPagination.currentPage * defectsPagination.itemsPerPage, defectsPagination.totalItems);

        const info = document.querySelector('#defects-pagination .pagination-info');
        const page = document.getElementById('defects-page');
        const prev = document.getElementById('defects-prev');
        const next = document.getElementById('defects-next');

        if (info) info.textContent = `Mostrando ${startItem}-${endItem} de ${defectsPagination.totalItems} registros`;
        if (page) page.textContent = `Página ${defectsPagination.currentPage}`;
        if (prev) prev.disabled = defectsPagination.currentPage === 1;
        if (next) next.disabled = defectsPagination.currentPage >= totalPages;
    }

    function setupPaginationListeners() {
        if (paginationListenersSetup) return;

        const tcPrev = document.getElementById('test-cases-prev');
        const tcNext = document.getElementById('test-cases-next');
        const dPrev = document.getElementById('defects-prev');
        const dNext = document.getElementById('defects-next');

        if (tcPrev) tcPrev.onclick = () => { if (testCasesPagination.currentPage > 1) { testCasesPagination.currentPage--; renderTestCasesTable(); } };
        if (tcNext) tcNext.onclick = () => { if (testCasesPagination.currentPage < Math.ceil(testCasesPagination.totalItems / testCasesPagination.itemsPerPage)) { testCasesPagination.currentPage++; renderTestCasesTable(); } };
        if (dPrev) dPrev.onclick = () => { if (defectsPagination.currentPage > 1) { defectsPagination.currentPage--; renderDefectsTable(); } };
        if (dNext) dNext.onclick = () => { if (defectsPagination.currentPage < Math.ceil(defectsPagination.totalItems / defectsPagination.itemsPerPage)) { defectsPagination.currentPage++; renderDefectsTable(); } };

        paginationListenersSetup = true;
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

    // ============================================
    // Filter System Logic
    // ============================================

    async function loadFilterFieldsForReport(projectKey, issuetype = null) {
        if (!projectKey) {
            if (issuetype === 'test-case' || issuetype === null) reportAvailableFieldsTestCases = [];
            if (issuetype === 'bug' || issuetype === null) reportAvailableFieldsBugs = [];
            if (!issuetype) reportAvailableFields = [];
            return;
        }

        try {
            let url = `/api/jira/project/${projectKey}/filter-fields`;
            if (issuetype) {
                const jiraIssuetype = issuetype === 'test-case' ? 'Test Case' : (issuetype === 'bug' ? 'Bug' : issuetype);
                url += `?issuetype=${encodeURIComponent(jiraIssuetype)}`;
            }

            const response = await fetch(url);
            const data = await response.json();

            if (data.success && data.fields) {
                const availableFieldsList = data.fields.available_fields || [];
                const fieldValues = data.fields.field_values || {};
                const standardMapping = {
                    'status': { label: 'Estado', type: 'select' },
                    'priority': { label: 'Prioridad', type: 'select' },
                    'assignee': { label: 'Asignado', type: 'text' },
                    'labels': { label: 'Etiqueta', type: 'text' },
                    'affectsVersions': { label: 'Affects Version', type: 'select' },
                    'fixVersions': { label: 'Versión de Corrección', type: 'select' }
                };

                const fieldsResult = [];

                for (const field of availableFieldsList) {
                    if (field.id === 'issuetype' || field.id.toLowerCase() === 'tipo') continue;

                    if (field.id in standardMapping) {
                        const m = standardMapping[field.id];
                        const opts = fieldValues[field.id] || [];
                        if (m.type === 'select' && opts.length === 0) continue;
                        fieldsResult.push({ value: field.id, label: m.label, type: m.type, options: opts });
                    } else if (field.custom) {
                        const opts = fieldValues[field.id] || field.allowedValues || field.allowed_values || [];
                        if (opts.length === 0) continue;
                        fieldsResult.push({ value: field.id, label: field.name, type: 'select', options: Array.isArray(opts) ? opts : [] });
                    }
                }

                if (issuetype === 'test-case') reportAvailableFieldsTestCases = fieldsResult;
                else if (issuetype === 'bug') reportAvailableFieldsBugs = fieldsResult;
                else {
                    reportAvailableFields = fieldsResult;
                    reportAvailableFieldsTestCases = fieldsResult;
                    reportAvailableFieldsBugs = fieldsResult;
                }
            }
        } catch (error) {
            console.error('Error al cargar campos de filtros:', error);
        }
    }

    function switchFilterTab(tabType) {
        currentFilterTab = tabType;
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));

        const tabEl = document.getElementById(`tab-${tabType}`);
        if (tabEl) tabEl.classList.add('active');

        const target = event && event.target ? event.target.closest('.filter-tab') : null;
        if (target) target.classList.add('active');

        const project = document.getElementById('project-selector')?.value || '';
        if (project) {
            const fields = tabType === 'test-case' ? reportAvailableFieldsTestCases : reportAvailableFieldsBugs;
            if (fields.length === 0) loadFilterFieldsForReport(project, tabType);
        }
    }

    async function addReportFilter(filterType = null) {
        const type = filterType || currentFilterTab;
        const project = document.getElementById('project-selector')?.value || '';

        if (!project) { alert('Por favor, selecciona un proyecto primero.'); return; }

        let available = type === 'test-case' ? reportAvailableFieldsTestCases : reportAvailableFieldsBugs;

        if (available.length === 0) {
            try {
                await loadFilterFieldsForReport(project, type);
                available = type === 'test-case' ? reportAvailableFieldsTestCases : reportAvailableFieldsBugs;
                if (available.length === 0) { alert('No se pudieron cargar los campos disponibles.'); return; }
            } catch (e) { return; }
        }

        reportFilterCount++;
        const grid = document.getElementById(type === 'test-case' ? 'filters-grid-test-case' : 'filters-grid-bug');
        if (!grid) return;

        const filterId = `report-filter-${type}-${reportFilterCount}`;
        const group = document.createElement('div');
        group.className = 'filter-group';
        group.id = filterId;
        group.dataset.filterType = type;

        const fieldSelect = document.createElement('select');
        fieldSelect.className = 'filter-field-select';
        fieldSelect.innerHTML = '<option value="">Selecciona un campo...</option>';
        available.forEach(f => {
            const opt = document.createElement('option');
            opt.value = f.value;
            opt.textContent = f.label;
            fieldSelect.appendChild(opt);
        });
        fieldSelect.onchange = () => updateReportFilterValue(filterId, fieldSelect.value, type);

        group.innerHTML = `
            <label class="filter-label">Campo</label>
            ${fieldSelect.outerHTML}
            <label class="filter-label">Valor</label>
            <div id="${filterId}-value">
                <input type="text" class="filter-value-input" placeholder="Selecciona un campo primero" disabled>
            </div>
            <button class="filter-remove-btn" onclick="removeReportFilter('${filterId}')" title="Eliminar filtro">✕</button>
        `;

        grid.appendChild(group);

        const newSelect = group.querySelector('.filter-field-select');
        newSelect.onchange = () => updateReportFilterValue(filterId, newSelect.value, type);
    }

    function updateReportFilterValue(filterId, fieldValue, filterType = null) {
        const type = filterType || document.getElementById(filterId)?.dataset.filterType || currentFilterTab;
        const available = type === 'test-case' ? reportAvailableFieldsTestCases : reportAvailableFieldsBugs;
        const field = available.find(f => f.value === fieldValue);
        const container = document.getElementById(`${filterId}-value`);

        if (!field || !container) {
            if (container) container.innerHTML = '<input type="text" class="filter-value-input" placeholder="Selecciona un campo primero" disabled>';
            return;
        }

        if (field.type === 'select') {
            container.innerHTML = `
                <select class="filter-value-select" onchange="updateReportActiveFilters()">
                    <option value="">Todos</option>
                    ${field.options.map(opt => `<option value="${opt}">${opt}</option>`).join('')}
                </select>`;
        } else {
            container.innerHTML = '<input type="text" class="filter-value-input" placeholder="Ingresa el valor..." onchange="updateReportActiveFilters()">';
        }
    }

    function removeReportFilter(filterId) {
        const el = document.getElementById(filterId);
        if (el) el.remove();
        reportActiveFilters = reportActiveFilters.filter(f => f.id !== filterId);
        reportActiveFiltersTestCases = reportActiveFiltersTestCases.filter(f => f.id !== filterId);
        reportActiveFiltersBugs = reportActiveFiltersBugs.filter(f => f.id !== filterId);
        updateReportActiveFilters();
    }

    function updateReportActiveFilters() {
        reportActiveFiltersTestCases = [];
        reportActiveFiltersBugs = [];
        reportActiveFilters = [];

        const process = (gridId, type, target) => {
            document.querySelectorAll(`${gridId} .filter-group`).forEach(g => {
                const fs = g.querySelector('.filter-field-select');
                const vi = g.querySelector('.filter-value-input');
                const vs = g.querySelector('.filter-value-select');
                if (fs && fs.value) {
                    const fields = type === 'test-case' ? reportAvailableFieldsTestCases : reportAvailableFieldsBugs;
                    const field = fields.find(f => f.value === fs.value);
                    const value = vi ? vi.value : (vs ? vs.value : '');
                    if (value) {
                        const filter = { id: g.id, field: fs.value, fieldLabel: field ? field.label : fs.value, value: value, type: type };
                        target.push(filter);
                        reportActiveFilters.push(filter);
                    }
                }
            });
        };

        process('#filters-grid-test-case', 'test-case', reportActiveFiltersTestCases);
        process('#filters-grid-bug', 'bug', reportActiveFiltersBugs);

        const tcCount = document.getElementById('test-case-filter-count');
        const bCount = document.getElementById('bug-filter-count');
        if (tcCount) tcCount.textContent = reportActiveFiltersTestCases.length;
        if (bCount) bCount.textContent = reportActiveFiltersBugs.length;

        const container = document.getElementById('active-report-filters');
        if (!container) return;

        const title = container.querySelector('div:first-child') || (() => {
            const t = document.createElement('div');
            t.style.cssText = 'width: 100%; margin-bottom: 0.5rem; font-size: 0.85rem; color: var(--text-muted); font-weight: 600;';
            t.textContent = 'Filtros Activos:';
            return t;
        })();

        container.innerHTML = '';
        container.appendChild(title);

        reportActiveFilters.forEach(f => {
            const b = document.createElement('div');
            b.className = `filter-badge ${f.type}`;
            b.innerHTML = `
                <span class="filter-badge-type">${f.type === 'test-case' ? 'TC' : 'BUG'}</span>
                <span>${f.fieldLabel}: ${f.value}</span>
                <span class="filter-badge-remove" onclick="removeReportFilter('${f.id}')">✕</span>
            `;
            container.appendChild(b);
        });
    }

    function generateReportWithFilters() {
        const projectKey = document.getElementById('project-selector')?.value || '';
        const projectInput = document.getElementById('project-selector-input');
        const projectName = projectInput ? projectInput.value.split(' (')[0] : '';

        if (!projectKey) { alert('Por favor, selecciona un proyecto primero.'); return; }

        const projectsSection = document.getElementById('jira-projects-section');
        const reportSection = document.getElementById('jira-report-section');
        if (projectsSection) projectsSection.style.display = 'none';
        if (reportSection) reportSection.style.display = 'block';

        loadProjectMetrics(projectKey, projectName, {
            testCases: reportActiveFiltersTestCases,
            bugs: reportActiveFiltersBugs
        });
    }

    async function onProjectChange() {
        const project = document.getElementById('project-selector')?.value || '';
        if (project) {
            await loadFilterFieldsForReport(project, 'test-case');
            await loadFilterFieldsForReport(project, 'bug');
        } else {
            reportAvailableFieldsTestCases = [];
            reportAvailableFieldsBugs = [];
            reportAvailableFields = [];
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
        reportActiveFilters = [];
        reportActiveFiltersTestCases = [];
        reportActiveFiltersBugs = [];
        reportFilterCount = 0;
        reportAvailableFields = [];
        reportAvailableFieldsTestCases = [];
        reportAvailableFieldsBugs = [];

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

        currentProjectKey = null;
        paginationListenersSetup = false;
        testCasesPagination = { currentPage: 1, itemsPerPage: 10, totalItems: 0, data: [], totals: null };
        defectsPagination = { currentPage: 1, itemsPerPage: 10, totalItems: 0, data: [] };

        if (grTestCasesChart) { grTestCasesChart.destroy(); grTestCasesChart = null; }
        if (grBugsSeverityChart) { grBugsSeverityChart.destroy(); grBugsSeverityChart = null; }
    }

    // ============================================
    // Public API
    // ============================================

    window.NexusModules.Jira.Reports = {
        init: initJiraReports,
        switchReportOperation,
        resetReportsToHub,
        loadProjects,
        filterProjectOptions,
        showProjectDropdown,
        hideProjectDropdown,
        handleProjectKeydown,
        switchFilterTab,
        addReportFilter,
        removeReportFilter,
        updateReportActiveFilters,
        generateReportWithFilters,
        showProjectsSection,
        onProjectChange
    };

    // Global Exposure for HTML compatibility
    window.initJiraReports = initJiraReports;
    window.switchReportOperation = switchReportOperation;
    window.resetReportsToHub = resetReportsToHub;
    window.filterProjectOptions = filterProjectOptions;
    window.showProjectDropdown = showProjectDropdown;
    window.hideProjectDropdown = hideProjectDropdown;
    window.handleProjectKeydown = handleProjectKeydown;
    window.switchFilterTab = switchFilterTab;
    window.addReportFilter = addReportFilter;
    window.removeReportFilter = removeReportFilter;
    window.updateReportActiveFilters = updateReportActiveFilters;
    window.generateReportWithFilters = generateReportWithFilters;
    window.showProjectsSection = showProjectsSection;
    window.onProjectChange = onProjectChange;

    // Sharing state with other modules (like Reports Download)
    Object.defineProperty(window, 'grTestCasesChart', { get: () => grTestCasesChart });
    Object.defineProperty(window, 'grBugsSeverityChart', { get: () => grBugsSeverityChart });
    Object.defineProperty(window, 'currentGeneralReport', { get: () => currentGeneralReport });
    Object.defineProperty(window, 'testCasesPagination', { get: () => testCasesPagination });
    Object.defineProperty(window, 'defectsPagination', { get: () => defectsPagination });

    Object.defineProperty(window, 'currentProjectKey', {
        get: () => currentProjectKey,
        set: (val) => currentProjectKey = val
    });

})(window);
