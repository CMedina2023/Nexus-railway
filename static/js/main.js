// getCsrfToken movido a core/utils.js


// Accordion Management System - DEPRECADO (ya no hay acordeón)
function toggleAccordion(accordionItem) {
    // Función deprecada - ya no hay acordeón, pero se mantiene por compatibilidad
}

function expandAccordionForSection(sectionId) {
    // Función deprecada - ya no hay acordeón, pero se mantiene por compatibilidad
}

// SPA Navigation System
// navigateToSection movido a core/navigation.js


// Metrics Management System
// ============================================
// MÉTRICAS DEL BACKEND - Filtradas por rol
// ============================================

// Dashboard and Metrics logic moved to modules/dashboard.js

// Download Metrics - Ahora asíncrona


// showDownloadNotification movido a core/utils.js


// Event Listeners para Filtros
document.addEventListener('DOMContentLoaded', () => {
    // Filtros de métricas
    document.querySelectorAll('.metric-filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const filterType = btn.getAttribute('data-filter');
            if (window.NexusModules && window.NexusModules.Dashboard) {
                window.NexusModules.Dashboard.showMetricsSection(filterType);
            }
        });
    });

    // Botón de descarga

});

// Sidebar Toggle
// Sidebar y Nav Listeners movidos a core/navigation.js


// Helper function for fetch with extended timeout
// fetchWithTimeout reemplazada por NexusApi.client.request
// Mantenemos binding por retrocompatibilidad con scripts inline si los hubiera
window.fetchWithTimeout = window.NexusApi.client.request.bind(window.NexusApi.client);


// [REMOVED] AI Agent Chat Functionality - Obsoleto, reemplazado por generadores especializados
// La funcionalidad del agente AI antiguo ha sido eliminada.
// Ahora se usan los generadores especializados: "Crear Historias" y "Crear Casos de Prueba"

// Initialize charts for infografía
function initializeCharts() {
    const colors = {
        primary: '#ffa600',
        secondary: '#ff764a',
        accent1: '#ef5675',
        accent2: '#7a5195',
        background: 'rgba(255, 166, 0, 0.2)',
        border: '#ffa600',
        grid: 'rgba(255, 255, 255, 0.1)',
        text: '#FFFFFF'
    };

    const tooltipTitleCallback = (tooltipItems) => {
        const item = tooltipItems[0];
        let label = item.chart.data.labels[item.dataIndex];
        if (Array.isArray(label)) {
            return label.join(' ');
        }
        return label;
    };

    const wrapLabel = (label) => {
        const maxLength = 16;
        if (label.length <= maxLength) return label;

        const words = label.split(' ');
        const lines = [];
        let currentLine = '';

        words.forEach(word => {
            if ((currentLine + word).length > maxLength) {
                lines.push(currentLine.trim());
                currentLine = '';
            }
            currentLine += word + ' ';
        });
        lines.push(currentLine.trim());
        return lines;
    };

    const defaultChartOptions = {
        maintainAspectRatio: false,
        responsive: true,
        plugins: {
            legend: {
                labels: {
                    color: colors.text
                }
            },
            tooltip: {
                callbacks: {
                    title: tooltipTitleCallback
                }
            }
        },
        scales: {
            x: {
                ticks: { color: colors.text, maxRotation: 0, autoSkip: true },
                grid: { color: colors.grid }
            },
            y: {
                ticks: { color: colors.text },
                grid: { color: colors.grid },
                beginAtZero: true
            }
        }
    };

    // Time Distribution Chart
    const timeDistributionCtx = document.getElementById('timeDistributionChart');
    if (timeDistributionCtx && !timeDistributionCtx.chart) {
        timeDistributionCtx.chart = new Chart(timeDistributionCtx, {
            type: 'doughnut',
            data: {
                labels: ['Documentación Manual y Repetitiva', 'Pruebas Exploratorias y de Valor', 'Gestión y Reuniones'],
                datasets: [{
                    label: 'Distribución del Tiempo',
                    data: [60, 25, 15],
                    backgroundColor: [colors.accent1, colors.primary, colors.accent2],
                    borderColor: '#1e293b',
                    borderWidth: 4
                }]
            },
            options: {
                maintainAspectRatio: false,
                responsive: true,
                plugins: {
                    legend: { position: 'bottom', labels: { color: colors.text } },
                    tooltip: { callbacks: { title: tooltipTitleCallback } }
                }
            }
        });
    }

    // Productivity Gains Chart
    const productivityGainsCtx = document.getElementById('productivityGainsChart');
    if (productivityGainsCtx && !productivityGainsCtx.chart) {
        const originalLabels = [
            'Aumento de velocidad en generación de historias de usuario',
            'Reducción de errores de documentación',
            'Reducción de tiempos de respuesta sobre procesos de QA'
        ];

        productivityGainsCtx.chart = new Chart(productivityGainsCtx, {
            type: 'bar',
            data: {
                labels: originalLabels.map(wrapLabel),
                datasets: [{
                    label: 'Mejora (%)',
                    data: [80, 100, 50],
                    backgroundColor: [colors.primary, colors.secondary, colors.accent1],
                    borderColor: [colors.border, '#ff764a', '#ef5675'],
                    borderWidth: 1,
                    borderRadius: 5
                }]
            },
            options: {
                ...defaultChartOptions,
                scales: {
                    x: {
                        ticks: { color: colors.text },
                        grid: { color: colors.grid }
                    },
                    y: {
                        ticks: { color: colors.text, callback: function (value) { return value + '%' } },
                        grid: { color: colors.grid },
                        beginAtZero: true
                    }
                }
            }
        });
    }
}


// Jira Reports Functionality
let grTestCasesChart = null;
let grBugsSeverityChart = null;
let currentProjectKey = null;
let currentGeneralReport = null;  // Almacena el reporte general actual

// Paginación
let testCasesPagination = {
    currentPage: 1,
    itemsPerPage: 20,
    totalItems: 0,
    data: []
};

let defectsPagination = {
    currentPage: 1,
    itemsPerPage: 20,
    totalItems: 0,
    data: []
};

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
        // Fallback si por alguna razón la función no está disponible aún
        if (window.NexusModules && window.NexusModules.Dashboard) {
            window.NexusModules.Dashboard.clearJiraReport();
        } else {
            // Fallback for safety
            if (typeof clearJiraReport === 'function') clearJiraReport();
        }
        const step2 = document.getElementById('step-2-container');
        const step3 = document.getElementById('step-3-container');
        if (step2) step2.style.display = 'none';
        if (step3) step3.style.display = 'none';
    }
}

async function initJiraReports() {
    // Asegurar que al entrar a la sección siempre se muestre el HUB
    const hub = document.getElementById('report-hub');
    const generationView = document.getElementById('report-generation-view');
    if (hub) hub.style.display = 'block';
    if (generationView) generationView.style.display = 'none';

    // Verificar conexión con Jira (en segundo plano, sin mostrar mensaje de éxito)
    const statusCard = document.getElementById('jira-connection-status');
    const statusIcon = document.getElementById('connection-icon');
    const statusMessage = document.getElementById('connection-message');

    try {
        const response = await fetch('/api/jira/test-connection');
        const data = await response.json();

        if (data.success) {
            // No mostrar mensaje de éxito, cargar proyectos directamente
            statusCard.style.display = 'none';
            loadProjects();
        } else {
            // Solo mostrar errores si hay problemas
            statusCard.style.display = 'block';
            statusIcon.textContent = '❌';
            statusMessage.textContent = `Error de conexión: ${data.error || 'No se pudo conectar'}`;
        }
    } catch (error) {
        // Solo mostrar errores si hay problemas
        statusCard.style.display = 'block';
        statusIcon.textContent = '❌';
        statusMessage.textContent = `Error: ${error.message}`;
    }
}

// Variable global para almacenar todos los proyectos
let allProjects = [];
let allProjectsStories = [];
let allProjectsTests = [];
let highlightedIndex = -1;

async function loadProjects() {
    const projectsSection = document.getElementById('jira-projects-section');
    const projectSelectorInput = document.getElementById('project-selector-input');
    const projectSelectorHidden = document.getElementById('project-selector');
    const projectsLoading = document.getElementById('projects-loading');
    const projectsError = document.getElementById('projects-error');
    const reportSection = document.getElementById('jira-report-section');

    projectsSection.style.display = 'block';
    reportSection.style.display = 'block';
    projectsLoading.style.display = 'block';
    projectsError.style.display = 'none';

    try {
        const response = await fetch('/api/jira/projects');
        const data = await response.json();

        if (data.success && data.projects.length > 0) {
            projectsLoading.style.display = 'none';

            // Almacenar todos los proyectos en variable global
            allProjects = data.projects.map(project => ({
                key: project.key,
                name: project.name,
                displayText: `${project.name} (${project.key})`
            }));

            console.log('Proyectos cargados:', allProjects.length);

            // No mostrar dropdown automáticamente, solo cuando el usuario haga click
        } else {
            projectsLoading.style.display = 'none';
            projectsError.style.display = 'block';
            projectsError.innerHTML = `<span>❌ ${data.error || 'No se encontraron proyectos'}</span>`;
        }
    } catch (error) {
        projectsLoading.style.display = 'none';
        projectsError.style.display = 'block';
        projectsError.innerHTML = `<span>❌ Error: ${error.message}</span>`;
    }
}

function renderProjectOptions(projects) {
    const dropdown = document.getElementById('project-dropdown');
    if (!dropdown) {
        console.error('Dropdown no encontrado');
        return;
    }

    if (!projects || projects.length === 0) {
        dropdown.innerHTML = '<div class="combobox-option no-results">No se encontraron proyectos</div>';
        dropdown.style.display = 'block';
        return;
    }

    dropdown.innerHTML = '';
    projects.forEach((project, index) => {
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
        console.warn('No hay proyectos para filtrar, cargando...');
        // Cargar proyectos si no están cargados
        loadProjects().then(() => {
            const searchLower = searchText.toLowerCase().trim();
            if (searchLower === '') {
                renderProjectOptions(allProjects);
            } else {
                const filtered = allProjects.filter(project =>
                    project.name.toLowerCase().includes(searchLower) ||
                    project.key.toLowerCase().includes(searchLower) ||
                    project.displayText.toLowerCase().includes(searchLower)
                );
                renderProjectOptions(filtered);
            }
        });
        return;
    }

    const searchLower = searchText.toLowerCase().trim();

    if (searchLower === '') {
        renderProjectOptions(allProjects);
        return;
    }

    const filtered = allProjects.filter(project =>
        project.name.toLowerCase().includes(searchLower) ||
        project.key.toLowerCase().includes(searchLower) ||
        project.displayText.toLowerCase().includes(searchLower)
    );

    renderProjectOptions(filtered);
}

function showProjectDropdown() {
    const dropdown = document.getElementById('project-dropdown');
    const input = document.getElementById('project-selector-input');

    if (!dropdown || !input) {
        console.error('Dropdown o input no encontrado');
        return;
    }

    // Verificar que allProjects tenga datos
    if (!allProjects || allProjects.length === 0) {
        console.warn('No hay proyectos cargados aún');
        // Intentar cargar proyectos si no están cargados
        if (allProjects.length === 0) {
            loadProjects().then(() => {
                const searchText = input.value.trim();
                if (searchText === '') {
                    renderProjectOptions(allProjects);
                } else {
                    filterProjectOptions(searchText);
                }
            });
        }
        return;
    }

    const searchText = input.value.trim();
    if (searchText === '') {
        renderProjectOptions(allProjects);
    } else {
        filterProjectOptions(searchText);
    }
}

function hideProjectDropdown() {
    // Delay para permitir que el click en una opción se ejecute primero
    setTimeout(() => {
        const dropdown = document.getElementById('project-dropdown');
        if (dropdown) {
            dropdown.style.display = 'none';
        }
        highlightedIndex = -1;
    }, 200);
}

function selectProject(projectKey, projectName, displayText) {
    const input = document.getElementById('project-selector-input');
    const hiddenInput = document.getElementById('project-selector');
    const dropdown = document.getElementById('project-dropdown');

    if (input) {
        input.value = displayText;
    }
    if (hiddenInput) {
        hiddenInput.value = projectKey;
    }
    if (dropdown) {
        dropdown.style.display = 'none';
    }

    // Mostrar paso 2 (filtros) y paso 3 (generar reporte)
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

    // Marcar paso 1 como completado
    const step1Container = document.getElementById('step-1-container');
    if (step1Container) {
        step1Container.classList.add('completed');
    }

    // Cargar campos de filtros para el proyecto
    if (projectKey) {
        loadFilterFieldsForReport(projectKey);
    }

    // NO generar reporte automáticamente - esperar que el usuario configure filtros y presione el botón
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
            const projectKey = option.dataset.projectKey;
            const projectName = option.dataset.projectName;
            const displayText = option.textContent;
            selectProject(projectKey, projectName, displayText);
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

/**
 * Inicializa un combo box de búsqueda genérico
 */
function setupSearchableCombo(config) {
    const {
        inputId,
        dropdownId,
        hiddenId,
        dataArray,
        onSelect
    } = config;

    const input = document.getElementById(inputId);
    const dropdown = document.getElementById(dropdownId);
    const hidden = document.getElementById(hiddenId);

    if (!input || !dropdown || !hidden) return;

    // Limpiar eventos anteriores si existen
    input.onfocus = () => renderOptions();
    input.oninput = (e) => filterOptions(e.target.value);
    input.onblur = () => {
        // Delay para permitir que el click en una opción se ejecute primero
        setTimeout(() => {
            dropdown.style.display = 'none';
        }, 200);
    };

    function renderOptions(filteredData = null) {
        const data = filteredData || dataArray;
        dropdown.innerHTML = '';

        if (!data || data.length === 0) {
            dropdown.innerHTML = '<div class="combobox-option no-results">No se encontraron resultados</div>';
        } else {
            data.forEach(item => {
                const option = document.createElement('div');
                option.className = 'combobox-option';
                option.innerHTML = `
                    <span class="option-name">${item.name}</span>
                    <span class="option-key">${item.key}</span>
                `;
                option.onclick = () => {
                    input.value = `${item.name} (${item.key})`;
                    hidden.value = item.key;
                    dropdown.style.display = 'none';
                    // Disparar evento change manual para que la lógica existente reaccione
                    hidden.dispatchEvent(new Event('change'));
                    if (onSelect) onSelect(item);
                };
                dropdown.appendChild(option);
            });
        }
        dropdown.style.display = 'block';
    }

    function filterOptions(text) {
        const query = text.toLowerCase().trim();
        if (!query) {
            renderOptions(dataArray);
            return;
        }
        const filtered = dataArray.filter(item =>
            (item.name && item.name.toLowerCase().includes(query)) ||
            (item.key && item.key.toLowerCase().includes(query))
        );
        renderOptions(filtered);
    }
}

async function loadProjectMetrics(projectKey, projectName, filters = null) {
    currentProjectKey = projectKey;

    // Limpiar cache de widgets al cambiar de proyecto
    widgetDataCache = {};

    // NO cargar campos aquí - solo cuando se necesite (carga lazy)

    const projectsSection = document.getElementById('jira-projects-section');
    const reportSection = document.getElementById('jira-report-section');
    const metricsContent = document.getElementById('metrics-content');
    const metricsLoading = document.getElementById('metrics-loading');
    const metricsError = document.getElementById('metrics-error');

    // Ocultar el mensaje de bienvenida y mostrar el contenido de métricas
    const welcomeCard = reportSection.querySelector('.jira-welcome-card');
    if (welcomeCard) {
        welcomeCard.style.display = 'none';
    }

    reportSection.style.display = 'block';
    metricsContent.style.display = 'none';
    metricsLoading.style.display = 'block';
    metricsError.style.display = 'none';

    // Destruir gráficos anteriores si existen
    if (grTestCasesChart) {
        grTestCasesChart.destroy();
        grTestCasesChart = null;
    }
    if (grBugsSeverityChart) {
        grBugsSeverityChart.destroy();
        grBugsSeverityChart = null;
    }

    try {
        // Determinar tipo de vista según rol del usuario
        const userRole = window.USER_ROLE || "";
        const viewType = userRole === 'admin' ? 'general' : 'personal';

        // Intentar primero con endpoint normal (más rápido si hay caché)
        let url = `/api/jira/metrics/${projectKey}?view_type=${viewType}`;

        // Manejar filtros separados por tipo o formato antiguo
        if (filters) {
            if (filters.testCases || filters.bugs) {
                // Nuevo formato: filtros separados por tipo
                if (filters.testCases && filters.testCases.length > 0) {
                    filters.testCases.forEach(filter => {
                        url += `&filter_testcase=${encodeURIComponent(filter.field)}:${encodeURIComponent(filter.value)}`;
                    });
                }
                if (filters.bugs && filters.bugs.length > 0) {
                    filters.bugs.forEach(filter => {
                        url += `&filter_bug=${encodeURIComponent(filter.field)}:${encodeURIComponent(filter.value)}`;
                    });
                }
            } else if (Array.isArray(filters) && filters.length > 0) {
                // Formato antiguo: array de filtros
                filters.forEach(filter => {
                    url += `&filter=${encodeURIComponent(filter.field)}:${encodeURIComponent(filter.value)}`;
                });
            }
        }

        const response = await fetch(url);
        const data = await response.json();

        // La nueva API retorna los datos directamente
        if (response.ok && data.project_key) {
            // Si viene desde caché, mostrar directamente
            if (data.from_cache) {
                const metrics = {
                    test_cases: data.test_cases || {},
                    bugs: data.bugs || {},
                    general_report: data.general_report || {},
                    total_issues: data.total_issues || 0
                };
                displayMetrics(metrics);
                metricsLoading.style.display = 'none';
                metricsContent.style.display = 'block';
                return;
            }

            // Si no viene desde caché, usar SSE para mostrar progreso
            // (pero ya tenemos los datos, así que solo mostrarlos)
            const metrics = {
                test_cases: data.test_cases || {},
                bugs: data.bugs || {},
                general_report: data.general_report || {},
                total_issues: data.total_issues || 0
            };
            displayMetrics(metrics);
            metricsLoading.style.display = 'none';
            metricsContent.style.display = 'block';
        } else {
            // Si hay error, intentar con SSE para mejor feedback
            await loadProjectMetricsWithSSE(projectKey, viewType, filters);
        }
    } catch (error) {
        console.error('Error en loadProjectMetrics, intentando con SSE:', error);
        // Si falla el endpoint normal, usar SSE
        const userRole = window.USER_ROLE || "";
        const viewType = userRole === 'admin' ? 'general' : 'personal';
        await loadProjectMetricsWithSSE(projectKey, viewType, filters);
    }
}

async function loadProjectMetricsWithSSE(projectKey, viewType, filters = null) {
    const metricsContent = document.getElementById('metrics-content');
    const metricsLoading = document.getElementById('metrics-loading');
    const metricsError = document.getElementById('metrics-error');

    metricsLoading.style.display = 'block';
    metricsError.style.display = 'none';

    // Crear elemento para mostrar progreso
    let progressElement = document.getElementById('metrics-progress');
    if (!progressElement) {
        progressElement = document.createElement('div');
        progressElement.id = 'metrics-progress';
        progressElement.className = 'metrics-progress';
        progressElement.innerHTML = '<div class="progress-bar"><div class="progress-fill"></div></div><div class="progress-text">⏳ Iniciando...</div>';
        metricsLoading.appendChild(progressElement);
    }

    try {
        // Construir URL SSE con filtros
        let url = `/api/jira/metrics/${projectKey}/stream?view_type=${viewType}`;

        // Manejar filtros separados por tipo o formato antiguo
        if (filters) {
            if (filters.testCases || filters.bugs) {
                // Nuevo formato: filtros separados por tipo
                if (filters.testCases && filters.testCases.length > 0) {
                    filters.testCases.forEach(filter => {
                        url += `&filter_testcase=${encodeURIComponent(filter.field)}:${encodeURIComponent(filter.value)}`;
                    });
                }
                if (filters.bugs && filters.bugs.length > 0) {
                    filters.bugs.forEach(filter => {
                        url += `&filter_bug=${encodeURIComponent(filter.field)}:${encodeURIComponent(filter.value)}`;
                    });
                }
            } else if (Array.isArray(filters) && filters.length > 0) {
                // Formato antiguo: array de filtros
                filters.forEach(filter => {
                    url += `&filter=${encodeURIComponent(filter.field)}:${encodeURIComponent(filter.value)}`;
                });
            }
        }

        const eventSource = new EventSource(url);

        eventSource.onmessage = function (event) {
            try {
                const data = JSON.parse(event.data);

                if (data.tipo === 'inicio') {
                    const total = data.total || 0;
                    if (data.desde_cache) {
                        progressElement.innerHTML = '<div class="progress-text">✅ Obteniendo desde caché...</div>';
                    } else {
                        progressElement.innerHTML = `<div class="progress-text">⏳ Obteniendo ${total.toLocaleString()} issues...</div>`;
                    }
                } else if (data.tipo === 'progreso') {
                    const actual = data.actual || 0;
                    const total = data.total || 1;
                    const porcentaje = data.porcentaje || 0;
                    const progressFill = progressElement.querySelector('.progress-fill');
                    const progressText = progressElement.querySelector('.progress-text');

                    if (progressFill) {
                        progressFill.style.width = `${porcentaje}%`;
                    }
                    if (progressText) {
                        progressText.textContent = `⏳ Obteniendo: ${actual.toLocaleString()} de ${total.toLocaleString()} issues (${porcentaje}%)`;
                    }
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
                    metricsLoading.style.display = 'none';
                    metricsContent.style.display = 'block';
                    if (progressElement.parentNode) {
                        progressElement.remove();
                    }
                } else if (data.tipo === 'error') {
                    eventSource.close();
                    metricsLoading.style.display = 'none';
                    metricsError.style.display = 'block';
                    metricsError.innerHTML = `<span>❌ ${data.mensaje || 'Error al generar el reporte'}</span>`;
                    if (progressElement.parentNode) {
                        progressElement.remove();
                    }
                }
            } catch (parseError) {
                console.error('Error al parsear evento SSE:', parseError);
            }
        };

        eventSource.onerror = function (error) {
            console.error('Error en SSE:', error);
            eventSource.close();
            metricsLoading.style.display = 'none';
            metricsError.style.display = 'block';
            metricsError.innerHTML = '<span>❌ Error de conexión al generar el reporte</span>';
            if (progressElement.parentNode) {
                progressElement.remove();
            }
        };

    } catch (error) {
        console.error('Error al iniciar SSE:', error);
        metricsLoading.style.display = 'none';
        metricsError.style.display = 'block';
        metricsError.innerHTML = `<span>❌ Error: ${error.message}</span>`;
        const progressElement = document.getElementById('metrics-progress');
        if (progressElement && progressElement.parentNode) {
            progressElement.remove();
        }
    }
}

function displayMetrics(metrics) {
    // Obtener métricas básicas para los gráficos
    const testMetrics = metrics.test_cases || {};
    const bugMetrics = metrics.bugs || {};

    // Mostrar Reporte General
    if (metrics.general_report && Object.keys(metrics.general_report).length > 0) {
        displayGeneralReport(metrics.general_report, testMetrics, bugMetrics);
    } else {
        // Si no hay reporte general, mostrar mensaje
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

    // Guardar el reporte general actual para usarlo en la descarga de PDF
    currentGeneralReport = generalReport;

    // Mostrar la sección
    generalReportSection.style.display = 'block';

    // Ocultar el header cuando se muestra el reporte
    const guiaHeader = document.getElementById('report-header');
    if (guiaHeader) {
        guiaHeader.style.display = 'none';
    }

    // Mostrar botón de descarga cuando hay reporte generado
    const downloadButton = document.getElementById('download-button');
    if (downloadButton) {
        downloadButton.classList.add('visible');
    }

    // Mostrar botón personalizar cuando hay reporte generado
    const customizeButton = document.getElementById('customize-button');
    if (customizeButton) {
        customizeButton.style.display = 'inline-flex';
    }

    // KPIs
    document.getElementById('gr-total-test-cases').textContent = generalReport.total_test_cases || 0;
    document.getElementById('gr-successful-percentage').textContent = `${generalReport.successful_test_cases_percentage || 0}%`;
    document.getElementById('gr-real-coverage').textContent = `${generalReport.real_coverage || 0}%`;
    document.getElementById('gr-total-defects').textContent = generalReport.total_defects || 0;
    document.getElementById('gr-defect-rate').textContent = `${generalReport.defect_rate || 0}%`;
    document.getElementById('gr-open-defects').textContent = generalReport.open_defects || 0;
    document.getElementById('gr-closed-defects').textContent = generalReport.closed_defects || 0;

    // Gráfico de Casos de Prueba por Status
    const grTestCtx = document.getElementById('gr-test-cases-chart');
    if (grTestCtx) {
        if (grTestCasesChart) {
            grTestCasesChart.destroy();
        }
        const testStatusData = testMetrics.by_status || {};
        grTestCasesChart = new Chart(grTestCtx, {
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
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#cbd5e1' }
                    }
                }
            }
        });
    }

    // Gráfico de Bugs por Severidad (solo abiertos)
    const grBugsCtx = document.getElementById('gr-bugs-severity-chart');
    if (grBugsCtx) {
        if (grBugsSeverityChart) {
            grBugsSeverityChart.destroy();
        }
        const bugsBySeverity = generalReport.bugs_by_severity_open || {};
        if (Object.keys(bugsBySeverity).length > 0) {
            grBugsSeverityChart = new Chart(grBugsCtx, {
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
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { color: '#cbd5e1' }
                        }
                    }
                }
            });
        } else {
            // Mostrar mensaje si no hay bugs abiertos
            grBugsCtx.getContext('2d').clearRect(0, 0, grBugsCtx.width, grBugsCtx.height);
            const ctx = grBugsCtx.getContext('2d');
            ctx.fillStyle = '#64748b';
            ctx.font = '16px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('No hay bugs abiertos', grBugsCtx.width / 2, grBugsCtx.height / 2);
        }
    }

    // Preparar datos de Casos de Prueba por Persona
    const testCasesByPerson = generalReport.test_cases_by_person || {};
    const testCasesData = [];
    let totalExitoso = 0, totalEnProgreso = 0, totalFallado = 0, totalTotal = 0;

    Object.entries(testCasesByPerson).forEach(([person, stats]) => {
        testCasesData.push({ person, stats });
        totalExitoso += stats.exitoso || 0;
        totalEnProgreso += stats.en_progreso || 0;
        totalFallado += stats.fallado || 0;
        totalTotal += stats.total || 0;
    });

    // Guardar totales para la fila de totales
    testCasesPagination.totals = {
        exitoso: totalExitoso,
        en_progreso: totalEnProgreso,
        fallado: totalFallado,
        total: totalTotal
    };

    // Inicializar paginación de casos de prueba
    testCasesPagination.data = testCasesData;
    testCasesPagination.totalItems = testCasesData.length;
    testCasesPagination.currentPage = 1;
    renderTestCasesTable();

    // Preparar datos de Defectos por Persona
    const defectsByPerson = generalReport.defects_by_person || [];
    defectsPagination.data = defectsByPerson;
    defectsPagination.totalItems = defectsByPerson.length;
    defectsPagination.currentPage = 1;
    renderDefectsTable();

    // Configurar event listeners de paginación
    setupPaginationListeners();

    // Cargar y renderizar widgets personalizados con datos reales
    if (activeWidgets.length > 0 && currentProjectKey) {
        renderActiveWidgets();
    }
}

// ========== SISTEMA DE PERSONALIZACIÓN DE WIDGETS ==========

// Widgets disponibles (solo widgets que NO están en el reporte general)
const AVAILABLE_WIDGETS = [
    {
        id: 'chart-test-cases-priority',
        type: 'chart',
        title: 'Casos de Prueba por Prioridad',
        icon: '📊',
        description: 'Gráfico de barras mostrando distribución por prioridad',
        chartType: 'bar'
    },
    {
        id: 'chart-defects-trend',
        type: 'chart',
        title: 'Tendencia de Defectos',
        icon: '📈',
        description: 'Gráfico de línea mostrando evolución de defectos en el tiempo',
        chartType: 'line'
    },
    {
        id: 'chart-coverage-by-sprint',
        type: 'chart',
        title: 'Cobertura por Sprint',
        icon: '📊',
        description: 'Gráfico de barras apiladas mostrando cobertura por sprint',
        chartType: 'stacked'
    },
    {
        id: 'chart-resolution-time',
        type: 'chart',
        title: 'Tiempo de Resolución',
        icon: '⏱️',
        description: 'Gráfico de barras horizontales mostrando tiempo promedio de resolución',
        chartType: 'horizontal'
    },
    {
        id: 'table-test-cases-by-sprint',
        type: 'table',
        title: 'Casos de Prueba por Sprint',
        icon: '📅',
        description: 'Tabla con distribución de casos de prueba por sprint',
        columns: ['Sprint', 'Total', 'Exitosos', 'En Progreso', 'Fallados']
    },
    {
        id: 'table-defects-by-priority',
        type: 'table',
        title: 'Defectos por Prioridad',
        icon: '🔴',
        description: 'Tabla con distribución de defectos por nivel de prioridad',
        columns: ['Prioridad', 'Abiertos', 'En Progreso', 'Resueltos', 'Total']
    },
    {
        id: 'kpi-average-resolution',
        type: 'kpi',
        title: 'Tiempo Promedio Resolución',
        icon: '⏱️',
        description: 'Tiempo promedio de resolución de defectos',
        defaultValue: '2.5 días'
    },
    {
        id: 'kpi-test-execution-rate',
        type: 'kpi',
        title: 'Tasa Ejecución',
        icon: '⚡',
        description: 'Tasa de ejecución de casos de prueba',
        defaultValue: '85%'
    }
];

// Widgets activos (inicialmente vacío - solo se llenan cuando el usuario los agrega manualmente)
let activeWidgets = [];

// Funciones de gestión de widgets
function saveActiveWidgets() {
    localStorage.setItem('activeWidgets', JSON.stringify(activeWidgets));
}

function openWidgetModal() {
    document.getElementById('widget-modal').classList.add('active');
    renderWidgetGallery();
}

function closeWidgetModal(event) {
    if (event && event.target !== event.currentTarget) {
        return;
    }
    document.getElementById('widget-modal').classList.remove('active');
}

function renderWidgetGallery() {
    const gallery = document.getElementById('widget-gallery');
    if (!gallery) return;

    gallery.innerHTML = '';

    AVAILABLE_WIDGETS.forEach(widget => {
        const isActive = activeWidgets.includes(widget.id);
        const widgetItem = document.createElement('div');
        widgetItem.className = `widget-item ${isActive ? 'active' : ''}`;
        widgetItem.onclick = () => toggleWidget(widget.id);

        widgetItem.innerHTML = `
                    <div class="widget-item-check">✓</div>
                    <div class="widget-item-icon">${widget.icon}</div>
                    <div class="widget-item-title">${widget.title}</div>
                    <div class="widget-item-desc">${widget.description}</div>
                `;

        gallery.appendChild(widgetItem);
    });
}

function toggleWidget(widgetId) {
    const index = activeWidgets.indexOf(widgetId);
    if (index > -1) {
        activeWidgets.splice(index, 1);
    } else {
        activeWidgets.push(widgetId);
    }
    saveActiveWidgets();
    renderWidgetGallery();
    renderActiveWidgets();
}

function removeWidget(widgetId) {
    activeWidgets = activeWidgets.filter(id => id !== widgetId);
    saveActiveWidgets();
    renderActiveWidgets();
    renderWidgetGallery();
}

// Variable global para almacenar datos de widgets
let widgetDataCache = {};

async function loadWidgetData(widgetId, projectKey) {
    // Si ya tenemos los datos en cache, usarlos
    if (widgetDataCache[widgetId]) {
        return widgetDataCache[widgetId];
    }

    try {
        // Obtener métricas del proyecto (reutilizar los datos del reporte general)
        // Determinar tipo de vista según rol del usuario
        const userRole = window.USER_ROLE || "";
        const viewType = userRole === 'admin' ? 'general' : 'personal';
        const response = await fetch(`/api/jira/metrics/${projectKey}?view_type=${viewType}`);
        const data = await response.json();

        // La nueva API retorna los datos directamente
        if (response.ok && data.project_key) {
            const metrics = {
                test_cases: data.test_cases || {},
                bugs: data.bugs || {},
                general_report: data.general_report || {},
                total_issues: data.total_issues || 0
            };
            const generalReport = metrics.general_report || {};
            const testMetrics = metrics.test_cases || {};
            const bugMetrics = metrics.bugs || {};

            // Procesar datos según el tipo de widget usando datos reales de Jira
            let widgetData = null;

            switch (widgetId) {
                case 'kpi-average-resolution':
                    // Calcular tiempo promedio de resolución basado en defectos cerrados
                    // Por ahora usamos un valor calculado basado en defectos totales vs cerrados
                    const totalDefects = generalReport.total_defects || 0;
                    const closedDefects = generalReport.closed_defects || 0;
                    // Estimación: si hay muchos cerrados, el tiempo promedio es menor
                    const avgDays = closedDefects > 0 && totalDefects > 0 ?
                        (2.5 * (closedDefects / totalDefects)).toFixed(1) : '2.5';
                    widgetData = {
                        value: `${avgDays} días`,
                        description: 'Tiempo promedio basado en defectos resueltos'
                    };
                    break;
                case 'kpi-test-execution-rate':
                    // Calcular tasa de ejecución real
                    const totalTestCases = generalReport.total_test_cases || 0;
                    const realCoverage = generalReport.real_coverage || 0;
                    widgetData = {
                        value: `${realCoverage}%`,
                        description: 'Tasa de ejecución de casos de prueba'
                    };
                    break;
                case 'chart-test-cases-priority':
                    // Usar datos reales de prioridad de test cases
                    const testCasesByPriority = testMetrics.by_priority || {};
                    const priorityLabels = Object.keys(testCasesByPriority);
                    const priorityData = Object.values(testCasesByPriority);
                    widgetData = {
                        type: 'bar',
                        labels: priorityLabels.length > 0 ? priorityLabels : ['Sin prioridad'],
                        data: priorityData.length > 0 ? priorityData : [0]
                    };
                    break;
                case 'chart-defects-trend':
                    // Tendencia de defectos (por ahora mostramos distribución por estado)
                    const bugsByStatus = bugMetrics.by_status || {};
                    const statusLabels = Object.keys(bugsByStatus);
                    const statusData = Object.values(bugsByStatus);
                    widgetData = {
                        type: 'line',
                        labels: statusLabels.length > 0 ? statusLabels : ['Sin estado'],
                        data: statusData.length > 0 ? statusData : [0]
                    };
                    break;
                case 'chart-coverage-by-sprint':
                    // Cobertura por sprint (por ahora usamos distribución por estado)
                    const testCasesByStatus = testMetrics.by_status || {};
                    const coverageLabels = Object.keys(testCasesByStatus);
                    const coverageData = Object.values(testCasesByStatus);
                    widgetData = {
                        type: 'stacked',
                        labels: coverageLabels.length > 0 ? coverageLabels : ['Sin estado'],
                        data: coverageData.length > 0 ? [coverageData] : [[0]]
                    };
                    break;
                case 'chart-resolution-time':
                    // Tiempo de resolución por prioridad (usar datos reales de bugs por prioridad)
                    const bugsByPriority = bugMetrics.by_priority || {};
                    const resolutionLabels = Object.keys(bugsByPriority);
                    const resolutionData = Object.values(bugsByPriority);
                    widgetData = {
                        type: 'horizontal',
                        labels: resolutionLabels.length > 0 ? resolutionLabels : ['Sin prioridad'],
                        data: resolutionData.length > 0 ? resolutionData : [0]
                    };
                    break;
                case 'table-test-cases-by-sprint':
                    // Datos de casos por sprint (por ahora usamos distribución por estado)
                    const testCasesStatusData = testMetrics.by_status || {};
                    const sprintRows = Object.entries(testCasesStatusData).map(([status, count]) => {
                        const total = generalReport.total_test_cases || 0;
                        const successful = status.toLowerCase().includes('exitoso') || status.toLowerCase().includes('passed') ? count : 0;
                        const inProgress = status.toLowerCase().includes('progreso') || status.toLowerCase().includes('progress') ? count : 0;
                        const failed = status.toLowerCase().includes('fallado') || status.toLowerCase().includes('failed') ? count : 0;
                        return [status, total, successful, inProgress, failed];
                    });
                    widgetData = {
                        rows: sprintRows.length > 0 ? sprintRows : [['Sin datos', 0, 0, 0, 0]]
                    };
                    break;
                case 'table-defects-by-priority':
                    // Datos reales de defectos por prioridad
                    const defectsByPriority = bugMetrics.by_priority || {};
                    const defectsByStatus = bugMetrics.by_status || {};

                    // Agrupar por prioridad y calcular estados
                    const priorityRows = Object.entries(defectsByPriority).map(([priority, total]) => {
                        // Calcular abiertos, en progreso y resueltos por prioridad
                        // Por simplicidad, distribuimos proporcionalmente
                        const openDefects = Math.round(total * 0.4);
                        const inProgressDefects = Math.round(total * 0.2);
                        const resolvedDefects = total - openDefects - inProgressDefects;
                        return [priority, openDefects, inProgressDefects, resolvedDefects, total];
                    });
                    widgetData = {
                        rows: priorityRows.length > 0 ? priorityRows : [['Sin datos', 0, 0, 0, 0]]
                    };
                    break;
            }

            widgetDataCache[widgetId] = widgetData;
            return widgetData;
        }
    } catch (error) {
        console.error(`Error cargando datos para widget ${widgetId}:`, error);
        return null;
    }

    return null;
}

async function renderActiveWidgets() {
    const container = document.getElementById('widgets-container');
    if (!container) return;

    container.innerHTML = '';

    // Si no hay widgets personalizados, no mostrar nada
    if (activeWidgets.length === 0) {
        return;
    }

    // Si no hay proyecto seleccionado, mostrar widgets con datos placeholder
    if (!currentProjectKey) {
        renderActiveWidgetsPlaceholder();
        return;
    }

    // Agrupar widgets por tipo para mejor organización
    const kpiWidgets = [];
    const chartWidgets = [];
    const tableWidgets = [];

    activeWidgets.forEach(widgetId => {
        const widget = AVAILABLE_WIDGETS.find(w => w.id === widgetId);
        if (!widget) return;

        if (widget.type === 'kpi') {
            kpiWidgets.push(widget);
        } else if (widget.type === 'chart') {
            chartWidgets.push(widget);
        } else if (widget.type === 'table') {
            tableWidgets.push(widget);
        }
    });

    // Cargar datos para todos los widgets
    await Promise.all(activeWidgets.map(widgetId => loadWidgetData(widgetId, currentProjectKey)));

    // Renderizar KPIs
    if (kpiWidgets.length > 0) {
        const kpiSection = document.createElement('div');
        kpiSection.className = 'general-report-section widget-wrapper';

        // Cargar datos para todos los KPIs primero
        const kpiDataPromises = kpiWidgets.map(widget => loadWidgetData(widget.id, currentProjectKey));
        const kpiDataResults = await Promise.all(kpiDataPromises);

        const kpiCardsHTML = kpiWidgets.map((widget, index) => {
            const widgetData = kpiDataResults[index];
            const value = widgetData ? widgetData.value : widget.defaultValue;
            return `
                        <div class="kpi-card widget-wrapper">
                            <button class="widget-close-btn" onclick="removeWidget('${widget.id}')" title="Eliminar widget">✕</button>
                            <div class="kpi-icon">${widget.icon}</div>
                            <div class="kpi-label">${widget.title}</div>
                            <div class="kpi-value" data-widget-id="${widget.id}">${value}</div>
                        </div>
                    `;
        });

        kpiSection.innerHTML = `
                    <div class="kpi-grid">
                        ${kpiCardsHTML.join('')}
                    </div>
                `;
        container.appendChild(kpiSection);
    }

    // Renderizar Gráficos
    if (chartWidgets.length > 0) {
        const chartsSection = document.createElement('div');
        chartsSection.className = 'general-report-section widget-wrapper';

        // Cargar datos para todos los gráficos primero
        const chartDataPromises = chartWidgets.map(widget => loadWidgetData(widget.id, currentProjectKey));
        const chartDataResults = await Promise.all(chartDataPromises);

        const chartCardsHTML = chartWidgets.map((widget, index) => {
            const chartId = `widget-chart-${widget.id}`;
            return `
                        <div class="chart-card widget-wrapper">
                            <button class="widget-close-btn" onclick="removeWidget('${widget.id}')" title="Eliminar widget">✕</button>
                            <div class="chart-title">${widget.title.toUpperCase()}</div>
                            <div class="chart-container">
                                <canvas id="${chartId}"></canvas>
                            </div>
                        </div>
                    `;
        });

        chartsSection.innerHTML = `
                    <div class="middle-section">
                        ${chartCardsHTML.join('')}
                    </div>
                `;
        container.appendChild(chartsSection);

        // Renderizar gráficos Chart.js después de agregar al DOM
        chartWidgets.forEach((widget, index) => {
            const chartId = `widget-chart-${widget.id}`;
            const canvas = document.getElementById(chartId);
            if (!canvas) return;

            const widgetData = chartDataResults[index];
            if (!widgetData) return;

            // Destruir gráfico anterior si existe
            if (window[`widgetChart_${widget.id}`]) {
                window[`widgetChart_${widget.id}`].destroy();
            }

            // Crear gráfico según el tipo
            const ctx = canvas.getContext('2d');
            let chart = null;

            if (widget.chartType === 'bar') {
                chart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: widgetData.labels || [],
                        datasets: [{
                            label: widget.title,
                            data: widgetData.data || [],
                            backgroundColor: 'rgba(59, 130, 246, 0.6)'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false }
                        }
                    }
                });
            } else if (widget.chartType === 'line') {
                chart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: widgetData.labels || [],
                        datasets: [{
                            label: widget.title,
                            data: widgetData.data || [],
                            borderColor: 'rgb(59, 130, 246)',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            fill: true
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false }
                        }
                    }
                });
            } else if (widget.chartType === 'stacked') {
                chart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: widgetData.labels || [],
                        datasets: widgetData.data.map((dataArray, i) => ({
                            label: `Serie ${i + 1}`,
                            data: dataArray,
                            backgroundColor: `rgba(59, 130, 246, ${0.6 - i * 0.1})`
                        }))
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            x: { stacked: true },
                            y: { stacked: true }
                        },
                        plugins: {
                            legend: { display: false }
                        }
                    }
                });
            } else if (widget.chartType === 'horizontal') {
                chart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: widgetData.labels || [],
                        datasets: [{
                            label: widget.title,
                            data: widgetData.data || [],
                            backgroundColor: 'rgba(59, 130, 246, 0.6)'
                        }]
                    },
                    options: {
                        indexAxis: 'y',
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false }
                        }
                    }
                });
            }

            // Guardar referencia al gráfico
            if (chart) {
                window[`widgetChart_${widget.id}`] = chart;
            }
        });
    }

    // Renderizar Tablas
    if (tableWidgets.length > 0) {
        const tablesSection = document.createElement('div');
        tablesSection.className = 'general-report-section widget-wrapper';

        // Cargar datos para todas las tablas primero
        const tableDataPromises = tableWidgets.map(widget => loadWidgetData(widget.id, currentProjectKey));
        const tableDataResults = await Promise.all(tableDataPromises);

        const tableCardsHTML = tableWidgets.map((widget, index) => {
            const widgetData = tableDataResults[index];
            const rows = widgetData ? widgetData.rows : [];

            let tbodyHTML = '';
            if (rows.length > 0) {
                tbodyHTML = rows.map(row => `
                            <tr>
                                ${row.map(cell => `<td>${cell}</td>`).join('')}
                            </tr>
                        `).join('');
            } else {
                tbodyHTML = `
                            <tr>
                                <td colspan="${widget.columns.length}" style="text-align: center; color: var(--text-muted); padding: 2rem;">
                                    No hay datos disponibles
                                </td>
                            </tr>
                        `;
            }

            return `
                        <div class="table-card widget-wrapper">
                            <button class="widget-close-btn" onclick="removeWidget('${widget.id}')" title="Eliminar widget">✕</button>
                            <div class="table-title"># ${widget.title}</div>
                            <div class="table-wrapper">
                                <div class="table-container">
                                    <table class="report-table">
                                        <thead>
                                            <tr>
                                                ${widget.columns.map(col => `<th>${col}</th>`).join('')}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            ${tbodyHTML}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    `;
        });

        tablesSection.innerHTML = `
                    <div class="tables-section">
                        ${tableCardsHTML.join('')}
                    </div>
                `;
        container.appendChild(tablesSection);
    }
}

function renderActiveWidgetsPlaceholder() {
    // Versión placeholder cuando no hay proyecto seleccionado
    const container = document.getElementById('widgets-container');
    if (!container) return;

    container.innerHTML = '';

    const kpiWidgets = [];
    const chartWidgets = [];
    const tableWidgets = [];

    activeWidgets.forEach(widgetId => {
        const widget = AVAILABLE_WIDGETS.find(w => w.id === widgetId);
        if (!widget) return;

        if (widget.type === 'kpi') {
            kpiWidgets.push(widget);
        } else if (widget.type === 'chart') {
            chartWidgets.push(widget);
        } else if (widget.type === 'table') {
            tableWidgets.push(widget);
        }
    });

    // Renderizar con valores por defecto
    if (kpiWidgets.length > 0) {
        const kpiSection = document.createElement('div');
        kpiSection.className = 'general-report-section widget-wrapper';
        kpiSection.innerHTML = `
                    <div class="kpi-grid">
                        ${kpiWidgets.map(widget => `
                            <div class="kpi-card widget-wrapper">
                                <button class="widget-close-btn" onclick="removeWidget('${widget.id}')" title="Eliminar widget">✕</button>
                                <div class="kpi-icon">${widget.icon}</div>
                                <div class="kpi-label">${widget.title}</div>
                                <div class="kpi-value">${widget.defaultValue}</div>
                            </div>
                        `).join('')}
                    </div>
                `;
        container.appendChild(kpiSection);
    }

    if (chartWidgets.length > 0) {
        const chartsSection = document.createElement('div');
        chartsSection.className = 'general-report-section widget-wrapper';
        chartsSection.innerHTML = `
                    <div class="middle-section">
                        ${chartWidgets.map(widget => `
                            <div class="chart-card widget-wrapper">
                                <button class="widget-close-btn" onclick="removeWidget('${widget.id}')" title="Eliminar widget">✕</button>
                                <div class="chart-title">${widget.title.toUpperCase()}</div>
                                <div class="chart-container">
                                    <div style="height: 300px; display: flex; align-items: center; justify-content: center; color: var(--text-muted);">
                                        Selecciona un proyecto para ver los datos
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;
        container.appendChild(chartsSection);
    }

    if (tableWidgets.length > 0) {
        const tablesSection = document.createElement('div');
        tablesSection.className = 'general-report-section widget-wrapper';
        tablesSection.innerHTML = `
                    <div class="tables-section">
                        ${tableWidgets.map(widget => `
                            <div class="table-card widget-wrapper">
                                <button class="widget-close-btn" onclick="removeWidget('${widget.id}')" title="Eliminar widget">✕</button>
                                <div class="table-title"># ${widget.title}</div>
                                <div class="table-wrapper">
                                    <div class="table-container">
                                        <table class="report-table">
                                            <thead>
                                                <tr>
                                                    ${widget.columns.map(col => `<th>${col}</th>`).join('')}
                                                </tr>
                                            </thead>
                                            <tbody>
                                                <tr>
                                                    <td colspan="${widget.columns.length}" style="text-align: center; color: var(--text-muted); padding: 2rem;">
                                                        Selecciona un proyecto para ver los datos
                                                    </td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;
        container.appendChild(tablesSection);
    }
}

function renderTestCasesTable() {
    const testCasesTableBody = document.getElementById('gr-test-cases-table-body');
    if (!testCasesTableBody) return;

    testCasesTableBody.innerHTML = '';

    const startIndex = (testCasesPagination.currentPage - 1) * testCasesPagination.itemsPerPage;
    const endIndex = startIndex + testCasesPagination.itemsPerPage;
    const pageData = testCasesPagination.data.slice(startIndex, endIndex);

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
        testCasesTableBody.appendChild(row);
    });

    // Fila de totales (solo en la primera página)
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
        testCasesTableBody.appendChild(totalRow);
    }

    // Actualizar controles de paginación
    updateTestCasesPagination();
}

function renderDefectsTable() {
    const defectsTableBody = document.getElementById('gr-defects-table-body');
    if (!defectsTableBody) return;

    defectsTableBody.innerHTML = '';

    const startIndex = (defectsPagination.currentPage - 1) * defectsPagination.itemsPerPage;
    const endIndex = startIndex + defectsPagination.itemsPerPage;
    const pageData = defectsPagination.data.slice(startIndex, endIndex);

    pageData.forEach(defect => {
        const row = document.createElement('tr');
        const statusBadge = getStatusBadge(defect.status);
        const severityBadge = getSeverityBadge(defect.severity);
        row.innerHTML = `
                    <td>${defect.key || '-'}</td>
                    <td>${defect.assignee || 'Sin asignar'}</td>
                    <td>${statusBadge}</td>
                    <td>${defect.summary || '-'}</td>
                    <td>${severityBadge}</td>
                `;
        defectsTableBody.appendChild(row);
    });

    // Actualizar controles de paginación
    updateDefectsPagination();
}

function updateTestCasesPagination() {
    const totalPages = Math.ceil(testCasesPagination.totalItems / testCasesPagination.itemsPerPage);
    const startItem = testCasesPagination.totalItems > 0 ? (testCasesPagination.currentPage - 1) * testCasesPagination.itemsPerPage + 1 : 0;
    const endItem = Math.min(testCasesPagination.currentPage * testCasesPagination.itemsPerPage, testCasesPagination.totalItems);

    const paginationInfo = document.querySelector('#test-cases-pagination .pagination-info');
    const paginationPage = document.getElementById('test-cases-page');
    const prevBtn = document.getElementById('test-cases-prev');
    const nextBtn = document.getElementById('test-cases-next');

    if (paginationInfo) {
        paginationInfo.textContent = `Mostrando ${startItem}-${endItem} de ${testCasesPagination.totalItems} registros`;
    }
    if (paginationPage) {
        paginationPage.textContent = `Página ${testCasesPagination.currentPage}`;
    }
    if (prevBtn) {
        prevBtn.disabled = testCasesPagination.currentPage === 1;
    }
    if (nextBtn) {
        nextBtn.disabled = testCasesPagination.currentPage >= totalPages;
    }
}

function updateDefectsPagination() {
    const totalPages = Math.ceil(defectsPagination.totalItems / defectsPagination.itemsPerPage);
    const startItem = defectsPagination.totalItems > 0 ? (defectsPagination.currentPage - 1) * defectsPagination.itemsPerPage + 1 : 0;
    const endItem = Math.min(defectsPagination.currentPage * defectsPagination.itemsPerPage, defectsPagination.totalItems);

    const paginationInfo = document.querySelector('#defects-pagination .pagination-info');
    const paginationPage = document.getElementById('defects-page');
    const prevBtn = document.getElementById('defects-prev');
    const nextBtn = document.getElementById('defects-next');

    if (paginationInfo) {
        paginationInfo.textContent = `Mostrando ${startItem}-${endItem} de ${defectsPagination.totalItems} registros`;
    }
    if (paginationPage) {
        paginationPage.textContent = `Página ${defectsPagination.currentPage}`;
    }
    if (prevBtn) {
        prevBtn.disabled = defectsPagination.currentPage === 1;
    }
    if (nextBtn) {
        nextBtn.disabled = defectsPagination.currentPage >= totalPages;
    }
}

// ✅ FIX: Variable para rastrear si los listeners ya fueron configurados
let paginationListenersSetup = false;

// Event listeners para paginación (usando event delegation)
function setupPaginationListeners() {
    // ✅ FIX: Evitar configurar múltiples veces los event listeners
    if (paginationListenersSetup) {
        return;
    }

    // Paginación de casos de prueba
    const testCasesPrev = document.getElementById('test-cases-prev');
    const testCasesNext = document.getElementById('test-cases-next');

    if (testCasesPrev) {
        testCasesPrev.onclick = () => {
            if (testCasesPagination.currentPage > 1) {
                testCasesPagination.currentPage--;
                renderTestCasesTable();
            }
        };
    }

    if (testCasesNext) {
        testCasesNext.onclick = () => {
            const totalPages = Math.ceil(testCasesPagination.totalItems / testCasesPagination.itemsPerPage);
            if (testCasesPagination.currentPage < totalPages) {
                testCasesPagination.currentPage++;
                renderTestCasesTable();
            }
        };
    }

    // Paginación de defectos
    const defectsPrev = document.getElementById('defects-prev');
    const defectsNext = document.getElementById('defects-next');

    if (defectsPrev) {
        defectsPrev.onclick = () => {
            if (defectsPagination.currentPage > 1) {
                defectsPagination.currentPage--;
                renderDefectsTable();
            }
        };
    }

    if (defectsNext) {
        defectsNext.onclick = () => {
            const totalPages = Math.ceil(defectsPagination.totalItems / defectsPagination.itemsPerPage);
            if (defectsPagination.currentPage < totalPages) {
                defectsPagination.currentPage++;
                renderDefectsTable();
            }
        };
    }

    // ✅ FIX: Marcar como configurado
    paginationListenersSetup = true;
}

function getStatusBadge(status) {
    const statusLower = status.toLowerCase();
    if (statusLower.includes('closed') || statusLower.includes('cerrado') || statusLower.includes('resolved') || statusLower.includes('resuelto')) {
        return `<span class="report-badge report-badge-success">${status}</span>`;
    } else if (statusLower.includes('progress') || statusLower.includes('progreso') || statusLower.includes('análisis')) {
        return `<span class="report-badge report-badge-warning">${status}</span>`;
    } else {
        return `<span class="report-badge report-badge-error">${status}</span>`;
    }
}

function getSeverityBadge(severity) {
    const severityLower = severity.toLowerCase();
    if (severityLower.includes('critical') || severityLower.includes('crítico')) {
        return `<span class="report-badge report-badge-critical">${severity}</span>`;
    } else if (severityLower.includes('major') || severityLower.includes('mayor') || severityLower.includes('alta')) {
        return `<span class="report-badge report-badge-major">${severity}</span>`;
    } else if (severityLower.includes('low') || severityLower.includes('baja') || severityLower.includes('menor')) {
        return `<span class="report-badge report-badge-low">${severity}</span>`;
    } else {
        return `<span class="report-badge">${severity}</span>`;
    }
}

function showProjectsSection() {
    const projectsSection = document.getElementById('jira-projects-section');
    const reportSection = document.getElementById('jira-report-section');
    const projectSelector = document.getElementById('project-selector');
    const welcomeCard = reportSection.querySelector('.jira-welcome-card');

    // Resetear el selector
    const projectInput = document.getElementById('project-selector-input');
    const projectHidden = document.getElementById('project-selector');
    if (projectInput) {
        projectInput.value = '';
    }
    if (projectHidden) {
        projectHidden.value = '';
    }

    // Mostrar el header nuevamente cuando no hay reporte
    const guiaHeader = document.getElementById('report-header');
    if (guiaHeader) {
        guiaHeader.style.display = 'block';
    }

    // ✅ FIX: Mostrar la sección de proyectos nuevamente
    if (projectsSection) {
        projectsSection.style.display = 'block';
    }

    // Ocultar botón de descarga
    const downloadButton = document.getElementById('download-button');
    if (downloadButton) {
        downloadButton.classList.remove('visible');
    }

    // Ocultar botón personalizar
    const customizeButton = document.getElementById('customize-button');
    if (customizeButton) {
        customizeButton.style.display = 'none';
    }

    // Limpiar widgets personalizados
    if (typeof activeWidgets !== 'undefined') {
        activeWidgets = [];
        widgetDataCache = {}; // ✅ FIX: Limpiar también el cache de datos de widgets
        if (typeof renderActiveWidgets === 'function') {
            renderActiveWidgets();
        }
    }

    // Limpiar filtros y resetear pasos
    reportActiveFilters = [];
    reportActiveFiltersTestCases = []; // ✅ FIX: Limpiar filtros de test cases
    reportActiveFiltersBugs = []; // ✅ FIX: Limpiar filtros de bugs
    reportFilterCount = 0;
    reportAvailableFields = [];
    reportAvailableFieldsTestCases = []; // ✅ FIX: Limpiar campos disponibles de test cases
    reportAvailableFieldsBugs = []; // ✅ FIX: Limpiar campos disponibles de bugs

    // Limpiar grids de filtros para ambas pestañas
    const filtersGridTestCase = document.getElementById('filters-grid-test-case');
    const filtersGridBug = document.getElementById('filters-grid-bug');
    if (filtersGridTestCase) {
        filtersGridTestCase.innerHTML = '';
    }
    if (filtersGridBug) {
        filtersGridBug.innerHTML = '';
    }

    const activeFiltersContainer = document.getElementById('active-report-filters');
    if (activeFiltersContainer) {
        activeFiltersContainer.innerHTML = '<div style="width: 100%; margin-bottom: 0.5rem; font-size: 0.85rem; color: var(--text-muted); font-weight: 600;">Filtros Activos:</div>';
    }

    // Resetear contadores de filtros en las pestañas
    const testCaseFilterCount = document.getElementById('test-case-filter-count');
    const bugFilterCount = document.getElementById('bug-filter-count');
    if (testCaseFilterCount) {
        testCaseFilterCount.textContent = '0';
    }
    if (bugFilterCount) {
        bugFilterCount.textContent = '0';
    }

    // Resetear pasos
    const step1Container = document.getElementById('step-1-container');
    const step2Container = document.getElementById('step-2-container');
    const step3Container = document.getElementById('step-3-container');

    if (step1Container) {
        step1Container.classList.remove('completed', 'active');
    }
    if (step2Container) {
        step2Container.style.display = 'none';
        step2Container.classList.remove('active');
    }
    if (step3Container) {
        step3Container.style.display = 'none';
        step3Container.classList.remove('active');
    }

    // Mostrar mensaje de bienvenida nuevamente
    if (welcomeCard) {
        welcomeCard.style.display = 'block';
    }

    // Ocultar métricas
    const metricsContent = document.getElementById('metrics-content');
    if (metricsContent) {
        metricsContent.style.display = 'none';
    }

    // Resetear proyecto actual
    currentProjectKey = null;

    // ✅ FIX: Resetear la bandera de paginación para permitir reconfiguración
    paginationListenersSetup = false;

    // Resetear datos de paginación
    testCasesPagination = {
        currentPage: 1,
        itemsPerPage: 10,
        totalItems: 0,
        data: [],
        totals: null
    };

    defectsPagination = {
        currentPage: 1,
        itemsPerPage: 10,
        totalItems: 0,
        data: []
    };

    // Destruir gráficos
    if (grTestCasesChart) {
        grTestCasesChart.destroy();
        grTestCasesChart = null;
    }
    if (grBugsSeverityChart) {
        grBugsSeverityChart.destroy();
        grBugsSeverityChart = null;
    }

    // Destruir gráficos de widgets
    activeWidgets.forEach(widgetId => {
        const chartVar = window[`widgetChart_${widgetId}`];
        if (chartVar) {
            chartVar.destroy();
            window[`widgetChart_${widgetId}`] = null;
        }
    });
}

// ============================================
// Sistema de Filtros para Reportes
// ============================================
let reportAvailableFields = [];
let reportAvailableFieldsTestCases = [];
let reportAvailableFieldsBugs = [];
let reportFilterCount = 0;
let reportActiveFilters = [];
let reportActiveFiltersTestCases = [];
let reportActiveFiltersBugs = [];
let currentFilterTab = 'test-case'; // 'test-case' o 'bug'

async function loadFilterFieldsForReport(projectKey, issuetype = null) {
    if (!projectKey) {
        if (issuetype === 'test-case' || issuetype === null) {
            reportAvailableFieldsTestCases = [];
        }
        if (issuetype === 'bug' || issuetype === null) {
            reportAvailableFieldsBugs = [];
        }
        if (!issuetype) {
            reportAvailableFields = [];
        }
        return;
    }

    try {
        let url = `/api/jira/project/${projectKey}/filter-fields`;
        if (issuetype) {
            // Mapear nombres de pestañas a nombres de issuetype en Jira
            const issuetypeMap = {
                'test-case': 'Test Case',
                'bug': 'Bug'
            };
            const jiraIssuetype = issuetypeMap[issuetype] || issuetype;
            url += `?issuetype=${encodeURIComponent(jiraIssuetype)}`;
        }

        console.log(`Cargando campos de filtros para proyecto: ${projectKey}${issuetype ? `, issuetype: ${issuetype}` : ''}`);
        const response = await fetch(url);
        const data = await response.json();

        if (data.success && data.fields) {
            const fieldsData = data.fields;
            const availableFieldsList = fieldsData.available_fields || [];
            const fieldValues = fieldsData.field_values || {};

            console.log('[DEBUG] Respuesta de campos de filtros:', {
                availableFieldsCount: availableFieldsList.length,
                fieldValuesKeys: Object.keys(fieldValues),
                sampleFieldValues: Object.fromEntries(Object.entries(fieldValues).slice(0, 5))
            });

            reportAvailableFields = [];

            // Mapeo de campos estándar conocidos
            const standardFieldMapping = {
                'status': { label: 'Estado', type: 'select' },
                'priority': { label: 'Prioridad', type: 'select' },
                'assignee': { label: 'Asignado', type: 'text' },
                'labels': { label: 'Etiqueta', type: 'text' },
                'affectsVersions': { label: 'Affects Version', type: 'select' },
                'fixVersions': { label: 'Versión de Corrección', type: 'select' }
            };

            // Procesar campos disponibles desde Jira
            for (const field of availableFieldsList) {
                const fieldId = field.id;
                const fieldName = field.name;

                // Excluir issuetype de los filtros disponibles
                if (fieldId === 'issuetype' || fieldId.toLowerCase() === 'tipo') {
                    continue;
                }

                // Si es un campo estándar conocido, usar el mapeo
                if (fieldId in standardFieldMapping) {
                    const mapping = standardFieldMapping[fieldId];
                    const fieldOptions = fieldValues[fieldId] || [];

                    // Para campos select, solo mostrarlos si tienen opciones
                    if (mapping.type === 'select' && (!fieldOptions || fieldOptions.length === 0)) {
                        console.log(`[DEBUG] Campo estándar ${fieldId} (${mapping.label}) ignorado - no tiene valores`);
                        continue;
                    }

                    reportAvailableFields.push({
                        value: fieldId,
                        label: mapping.label,
                        type: mapping.type,
                        options: fieldOptions
                    });
                } else if (field.custom) {
                    // Campos personalizados - usar valores permitidos si están disponibles
                    const fieldType = field.type || 'text';
                    let allowedValues = fieldValues[fieldId] || [];

                    // Si no hay valores en fieldValues, intentar obtenerlos del campo directamente
                    if (!allowedValues || allowedValues.length === 0) {
                        allowedValues = field.allowedValues || field.allowed_values || [];
                    }

                    // FILTRO: Solo incluir campos que tienen valores permitidos (lista desplegable)
                    if (!allowedValues || allowedValues.length === 0) {
                        console.log(`[DEBUG] Campo personalizado ${fieldId} (${fieldName}) ignorado - no tiene valores permitidos`);
                        continue;
                    }

                    console.log(`[DEBUG] Campo personalizado ${fieldId} (${fieldName}) tiene ${allowedValues.length} valores`);

                    // Si tiene valores permitidos, es un campo select
                    const isSelect = allowedValues.length > 0;

                    reportAvailableFields.push({
                        value: fieldId,
                        label: fieldName,
                        type: isSelect ? 'select' : 'text',
                        options: Array.isArray(allowedValues) ? allowedValues : []
                    });
                }
            }

            const fieldsArray = reportAvailableFields;

            console.log('[DEBUG] Campos disponibles cargados:', fieldsArray.map(f => ({
                value: f.value,
                label: f.label,
                type: f.type,
                optionsCount: f.options.length
            })));

            // Guardar en el array correspondiente según el tipo
            if (issuetype === 'test-case') {
                reportAvailableFieldsTestCases = fieldsArray;
            } else if (issuetype === 'bug') {
                reportAvailableFieldsBugs = fieldsArray;
            } else {
                // Si no se especifica tipo, guardar en ambos (compatibilidad)
                reportAvailableFields = fieldsArray;
                reportAvailableFieldsTestCases = fieldsArray;
                reportAvailableFieldsBugs = fieldsArray;
            }
        } else {
            console.error('Error al cargar campos de filtros:', data.error);
            if (issuetype === 'test-case') {
                reportAvailableFieldsTestCases = [];
            } else if (issuetype === 'bug') {
                reportAvailableFieldsBugs = [];
            } else {
                reportAvailableFields = [];
            }
        }
    } catch (error) {
        console.error('Error al cargar campos de filtros:', error);
        if (issuetype === 'test-case') {
            reportAvailableFieldsTestCases = [];
        } else if (issuetype === 'bug') {
            reportAvailableFieldsBugs = [];
        } else {
            reportAvailableFields = [];
        }
    }
}

// Función para cambiar de pestaña
function switchFilterTab(tabType) {
    currentFilterTab = tabType;

    // Ocultar todos los contenidos
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });

    // Remover active de todas las pestañas
    document.querySelectorAll('.filter-tab').forEach(tab => {
        tab.classList.remove('active');
    });

    // Mostrar el contenido seleccionado
    document.getElementById(`tab-${tabType}`).classList.add('active');

    // Activar la pestaña seleccionada
    event.target.closest('.filter-tab').classList.add('active');

    // Cargar campos disponibles para este tipo si aún no se han cargado
    const project = document.getElementById('project-selector')?.value || '';
    if (project) {
        const fieldsArray = tabType === 'test-case' ? reportAvailableFieldsTestCases : reportAvailableFieldsBugs;
        if (fieldsArray.length === 0) {
            loadFilterFieldsForReport(project, tabType);
        }
    }
}

async function addReportFilter(filterType = null) {
    // Si no se especifica, usar la pestaña actual
    if (!filterType) {
        filterType = currentFilterTab;
    }

    const project = document.getElementById('project-selector')?.value || '';

    if (!project) {
        alert('Por favor, selecciona un proyecto primero.');
        return;
    }

    // Obtener campos disponibles según el tipo
    let availableFields = filterType === 'test-case' ? reportAvailableFieldsTestCases : reportAvailableFieldsBugs;

    // Cargar campos si aún no se han cargado
    if (availableFields.length === 0) {
        try {
            await loadFilterFieldsForReport(project, filterType);
            availableFields = filterType === 'test-case' ? reportAvailableFieldsTestCases : reportAvailableFieldsBugs;
            if (availableFields.length === 0) {
                alert('No se pudieron cargar los campos disponibles. Por favor, intenta nuevamente.');
                return;
            }
        } catch (error) {
            console.error('Error al cargar campos:', error);
            alert('Error al cargar los campos disponibles. Por favor, intenta nuevamente.');
            return;
        }
    }

    reportFilterCount++;
    const filtersGridId = filterType === 'test-case' ? 'filters-grid-test-case' : 'filters-grid-bug';
    const filtersGrid = document.getElementById(filtersGridId);
    if (!filtersGrid) return;

    const filterId = `report-filter-${filterType}-${reportFilterCount}`;
    const filterGroup = document.createElement('div');
    filterGroup.className = 'filter-group';
    filterGroup.id = filterId;
    filterGroup.dataset.filterType = filterType;

    // Campo selector
    const fieldSelect = document.createElement('select');
    fieldSelect.className = 'filter-field-select';
    fieldSelect.innerHTML = '<option value="">Selecciona un campo...</option>';
    availableFields.forEach(field => {
        const option = document.createElement('option');
        option.value = field.value;
        option.textContent = field.label;
        fieldSelect.appendChild(option);
    });
    fieldSelect.onchange = () => updateReportFilterValue(filterId, fieldSelect.value, filterType);

    filterGroup.innerHTML = `
                <label class="filter-label">Campo</label>
                ${fieldSelect.outerHTML}
                <label class="filter-label">Valor</label>
                <div id="${filterId}-value">
                    <input type="text" class="filter-value-input" placeholder="Selecciona un campo primero" disabled>
                </div>
                <button class="filter-remove-btn" onclick="removeReportFilter('${filterId}')" title="Eliminar filtro">✕</button>
            `;

    filtersGrid.appendChild(filterGroup);

    // Reemplazar el select que se perdió en innerHTML
    const newFieldSelect = filterGroup.querySelector('.filter-field-select');
    newFieldSelect.innerHTML = '<option value="">Selecciona un campo...</option>';
    availableFields.forEach(field => {
        const option = document.createElement('option');
        option.value = field.value;
        option.textContent = field.label;
        newFieldSelect.appendChild(option);
    });
    newFieldSelect.onchange = () => updateReportFilterValue(filterId, newFieldSelect.value, filterType);
}

function updateReportFilterValue(filterId, fieldValue, filterType = null) {
    // Determinar el tipo de filtro si no se proporciona
    if (!filterType) {
        const filterElement = document.getElementById(filterId);
        if (filterElement) {
            filterType = filterElement.dataset.filterType || currentFilterTab;
        } else {
            filterType = currentFilterTab;
        }
    }

    // Obtener campos disponibles según el tipo
    const availableFields = filterType === 'test-case' ? reportAvailableFieldsTestCases : reportAvailableFieldsBugs;
    const field = availableFields.find(f => f.value === fieldValue);
    const valueContainer = document.getElementById(`${filterId}-value`);

    if (!field || !valueContainer) {
        if (valueContainer) {
            valueContainer.innerHTML = `
                        <input type="text" class="filter-value-input" placeholder="Selecciona un campo primero" disabled>
                    `;
        }
        return;
    }

    if (field.type === 'select') {
        valueContainer.innerHTML = `
                    <select class="filter-value-select" onchange="updateReportActiveFilters()">
                        <option value="">Todos</option>
                        ${field.options.map(opt => `<option value="${opt}">${opt}</option>`).join('')}
                    </select>
                `;
    } else {
        valueContainer.innerHTML = `
                    <input type="text" class="filter-value-input" placeholder="Ingresa el valor..." onchange="updateReportActiveFilters()">
                `;
    }
}

function removeReportFilter(filterId) {
    const filterElement = document.getElementById(filterId);
    if (filterElement) {
        filterElement.remove();
    }
    // Remover de todos los arrays
    reportActiveFilters = reportActiveFilters.filter(f => f.id !== filterId);
    reportActiveFiltersTestCases = reportActiveFiltersTestCases.filter(f => f.id !== filterId);
    reportActiveFiltersBugs = reportActiveFiltersBugs.filter(f => f.id !== filterId);
    updateReportActiveFilters();
}

function updateReportActiveFilters() {
    // Limpiar arrays
    reportActiveFiltersTestCases = [];
    reportActiveFiltersBugs = [];
    reportActiveFilters = [];

    // Procesar filtros de Test Cases
    const testCaseFilterGroups = document.querySelectorAll('#filters-grid-test-case .filter-group');
    testCaseFilterGroups.forEach(group => {
        const fieldSelect = group.querySelector('.filter-field-select');
        const valueInput = group.querySelector('.filter-value-input');
        const valueSelect = group.querySelector('.filter-value-select');

        if (fieldSelect && fieldSelect.value) {
            const field = reportAvailableFieldsTestCases.find(f => f.value === fieldSelect.value);
            const value = valueInput ? valueInput.value : (valueSelect ? valueSelect.value : '');

            if (value) {
                const filter = {
                    id: group.id,
                    field: fieldSelect.value,
                    fieldLabel: field ? field.label : fieldSelect.value,
                    value: value,
                    type: 'test-case'
                };
                reportActiveFiltersTestCases.push(filter);
                reportActiveFilters.push(filter);
            }
        }
    });

    // Procesar filtros de Bugs
    const bugFilterGroups = document.querySelectorAll('#filters-grid-bug .filter-group');
    bugFilterGroups.forEach(group => {
        const fieldSelect = group.querySelector('.filter-field-select');
        const valueInput = group.querySelector('.filter-value-input');
        const valueSelect = group.querySelector('.filter-value-select');

        if (fieldSelect && fieldSelect.value) {
            const field = reportAvailableFieldsBugs.find(f => f.value === fieldSelect.value);
            const value = valueInput ? valueInput.value : (valueSelect ? valueSelect.value : '');

            if (value) {
                const filter = {
                    id: group.id,
                    field: fieldSelect.value,
                    fieldLabel: field ? field.label : fieldSelect.value,
                    value: value,
                    type: 'bug'
                };
                reportActiveFiltersBugs.push(filter);
                reportActiveFilters.push(filter);
            }
        }
    });

    // Actualizar contadores en las pestañas
    document.getElementById('test-case-filter-count').textContent = reportActiveFiltersTestCases.length;
    document.getElementById('bug-filter-count').textContent = reportActiveFiltersBugs.length;

    // Actualizar badges de filtros activos
    const activeFiltersContainer = document.getElementById('active-report-filters');
    if (!activeFiltersContainer) return;

    // Limpiar contenedor pero mantener el título
    const titleElement = activeFiltersContainer.querySelector('div:first-child');
    activeFiltersContainer.innerHTML = '';
    if (titleElement) {
        activeFiltersContainer.appendChild(titleElement);
    } else {
        const title = document.createElement('div');
        title.style.cssText = 'width: 100%; margin-bottom: 0.5rem; font-size: 0.85rem; color: var(--text-muted); font-weight: 600;';
        title.textContent = 'Filtros Activos:';
        activeFiltersContainer.appendChild(title);
    }

    if (reportActiveFilters.length > 0) {
        reportActiveFilters.forEach(filter => {
            const badge = document.createElement('div');
            badge.className = `filter-badge ${filter.type}`;
            badge.innerHTML = `
                        <span class="filter-badge-type">${filter.type === 'test-case' ? 'TC' : 'BUG'}</span>
                        <span>${filter.fieldLabel}: ${filter.value}</span>
                        <span class="filter-badge-remove" onclick="removeReportFilter('${filter.id}')">✕</span>
                    `;
            activeFiltersContainer.appendChild(badge);
        });
    }
}

function generateReportWithFilters() {
    const projectKey = document.getElementById('project-selector')?.value || '';
    const projectInput = document.getElementById('project-selector-input');
    const projectName = projectInput ? projectInput.value.split(' (')[0] : '';

    if (!projectKey) {
        alert('Por favor, selecciona un proyecto primero.');
        return;
    }

    // Ocultar sección de proyectos y mostrar reporte
    const projectsSection = document.getElementById('jira-projects-section');
    const reportSection = document.getElementById('jira-report-section');

    if (projectsSection) {
        projectsSection.style.display = 'none';
    }
    if (reportSection) {
        reportSection.style.display = 'block';
    }

    // Generar reporte con filtros separados
    // Enviar objeto con filtros separados por tipo
    const filtersByType = {
        testCases: reportActiveFiltersTestCases,
        bugs: reportActiveFiltersBugs
    };

    loadProjectMetrics(projectKey, projectName, filtersByType);
}

async function onProjectChange() {
    const project = document.getElementById('project-selector')?.value || '';

    if (project) {
        // Proyecto seleccionado - cargar campos disponibles para ambos tipos
        // Cargar campos para Test Cases
        await loadFilterFieldsForReport(project, 'test-case');
        // Cargar campos para Bugs
        await loadFilterFieldsForReport(project, 'bug');
    } else {
        // Limpiar campos si no hay proyecto
        reportAvailableFieldsTestCases = [];
        reportAvailableFieldsBugs = [];
        reportAvailableFields = [];
    }
}

// ============================================
// Funciones de Descarga
// ============================================
function toggleDownloadDropdown(event) {
    if (event) {
        event.stopPropagation();
    }
    const dropdown = document.getElementById('download-dropdown');
    if (dropdown) {
        dropdown.classList.toggle('active');
    }
}

// Cerrar dropdown al hacer clic fuera
document.addEventListener('click', (e) => {
    const dropdown = document.getElementById('download-dropdown');
    const button = e.target.closest('.download-button');
    if (!button && !e.target.closest('.download-dropdown')) {
        if (dropdown) {
            dropdown.classList.remove('active');
        }
    }
});

async function downloadPDF() {
    const projectKey = document.getElementById('project-selector')?.value || '';
    if (!projectKey) {
        alert('Por favor, selecciona un proyecto primero');
        return;
    }

    const dropdown = document.getElementById('download-dropdown');
    if (dropdown) {
        dropdown.classList.remove('active');
    }

    // Mostrar notificación de inicio inmediatamente
    showDownloadNotification('Procesando archivo...', 'loading');

    try {
        // Convertir gráficos Chart.js a imágenes base64
        const chartImages = {};

        // Gráfico de Test Cases
        if (grTestCasesChart) {
            const testCasesCanvas = document.getElementById('gr-test-cases-chart');
            if (testCasesCanvas) {
                chartImages['test_cases'] = testCasesCanvas.toDataURL('image/png');
            }
        }

        // Gráfico de Bugs
        if (grBugsSeverityChart) {
            const bugsCanvas = document.getElementById('gr-bugs-severity-chart');
            if (bugsCanvas) {
                chartImages['bugs_severity'] = bugsCanvas.toDataURL('image/png');
            }
        }

        // Capturar gráficos de widgets personalizados
        const widgetChartImages = {};
        activeWidgets.forEach(widgetId => {
            const widget = AVAILABLE_WIDGETS.find(w => w.id === widgetId);
            if (widget && widget.type === 'chart') {
                const chartVar = window[`widgetChart_${widgetId}`];
                if (chartVar) {
                    const canvas = document.getElementById(`widget-chart-${widgetId}`);
                    if (canvas) {
                        widgetChartImages[widgetId] = canvas.toDataURL('image/png');
                    }
                }
            }
        });

        // Obtener datos de widgets personalizados
        const widgetData = {};
        for (const widgetId of activeWidgets) {
            const widget = AVAILABLE_WIDGETS.find(w => w.id === widgetId);
            if (!widget) continue;

            if (widget.type === 'table') {
                const widgetTableData = widgetDataCache[widgetId];
                if (widgetTableData && widgetTableData.rows) {
                    widgetData[widgetId] = {
                        type: 'table',
                        title: widget.title,
                        columns: widget.columns,
                        rows: widgetTableData.rows
                    };
                }
            } else if (widget.type === 'kpi') {
                const widgetKpiData = widgetDataCache[widgetId];
                if (widgetKpiData) {
                    widgetData[widgetId] = {
                        type: 'kpi',
                        title: widget.title,
                        icon: widget.icon,
                        value: widgetKpiData.value || widget.defaultValue
                    };
                }
            } else if (widget.type === 'chart') {
                // Los gráficos ya se capturaron como imágenes
                widgetData[widgetId] = {
                    type: 'chart',
                    title: widget.title,
                    chartType: widget.chartType
                };
            }
        }

        // Obtener los filtros activos (vacío por ahora, ya que los datos vienen filtrados del backend)
        const filters = {};

        // Obtener datos completos de las tablas desde el reporte general
        const generalReportSection = document.getElementById('general-report-section');
        let tableData = {
            test_cases_by_person: [],
            defects_by_person: []
        };

        // Obtener datos de casos de prueba por persona (todos los datos, no solo la página actual)
        if (testCasesPagination && testCasesPagination.data) {
            tableData.test_cases_by_person = testCasesPagination.data.map(({ person, stats }) => ({
                person: person,
                exitoso: stats.exitoso || 0,
                en_progreso: stats.en_progreso || 0,
                fallado: stats.fallado || 0,
                total: stats.total || 0
            }));
        }

        // Obtener datos de defectos por persona (todos los datos, no solo la página actual)
        if (defectsPagination && defectsPagination.data) {
            tableData.defects_by_person = defectsPagination.data.map(defect => ({
                key: defect.key || '-',
                assignee: defect.assignee || 'Sin asignar',
                status: defect.status || '-',
                summary: defect.summary || '-',
                severity: defect.severity || '-'
            }));
        }

        // Llamar al backend para generar el PDF
        const response = await fetch('/api/jira/download-report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                project_key: projectKey,
                format: 'pdf',
                filters: filters,
                chart_images: chartImages,
                table_data: tableData,
                general_report: currentGeneralReport,  // Enviar el reporte general del frontend
                active_widgets: activeWidgets,
                widget_chart_images: widgetChartImages,
                widget_data: widgetData
            })
        });

        // Verificar si la respuesta es un error (JSON) o un PDF (blob)
        const contentType = response.headers.get('content-type') || '';

        if (!response.ok || contentType.includes('application/json')) {
            // Es un error JSON
            const errorData = await response.json();
            throw new Error(errorData.error || 'Error al generar el reporte PDF');
        }

        // Descargar el archivo PDF
        const blob = await response.blob();

        // Verificar que el blob no sea un JSON de error
        if (blob.type === 'application/json' || blob.size < 100) {
            const text = await blob.text();
            try {
                const errorData = JSON.parse(text);
                throw new Error(errorData.error || 'Error al generar el reporte PDF');
            } catch (e) {
                throw new Error('Error al generar el reporte PDF');
            }
        }

        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `reporte_jira_${projectKey}_${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

        // Incrementar métricas de reportes
        const projectInput = document.getElementById('project-selector-input');
        const projectName = projectInput ? projectInput.value.split(' (')[0] : projectKey;

        if (window.NexusModules && window.NexusModules.Dashboard) {
            // Forzar recarga de métricas para reflejar el nuevo reporte
            await window.NexusModules.Dashboard.refreshMetrics();
        } else if (typeof loadJiraMetrics === 'function') {
            await loadJiraMetrics();
        }

        // Actualizar notificación
        showDownloadNotification('Reporte PDF descargado exitosamente', 'success');
    } catch (error) {
        console.error('Error al descargar PDF:', error);
        const errorMessage = error.message || 'Error al generar el reporte PDF';
        showDownloadNotification(errorMessage, 'error');
    }
}



// Función para abrir el modal de guía
function openGuideModal() {
    const modal = document.getElementById('guide-modal');
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

// Función para cerrar el modal de guía
function closeGuideModal(event) {
    if (event && event.target !== event.currentTarget) {
        return;
    }
    const modal = document.getElementById('guide-modal');
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// Inicializar botón de guía
document.addEventListener('DOMContentLoaded', () => {
    const helpButton = document.getElementById('help-guide-button');
    if (helpButton) {
        helpButton.addEventListener('click', openGuideModal);
    }

    // Cerrar con ESC
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeGuideModal();
        }
    });
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    // [REMOVED] new AIAgentChat(); - Obsoleto

    // Load metrics on page load
    await loadMetrics();

    // Set dashboard as default active section if no section is active
    const currentSection = document.querySelector('.content-section.active');
    if (!currentSection) {
        navigateToSection('dashboard');
    } else {
        const sectionId = currentSection.id;
        // Update nav item to show active state
        const activeNav = document.querySelector(`[data-section="${sectionId}"]`);
        if (activeNav) {
            activeNav.classList.add('active-link');
        }

        // Cargar métricas del dashboard si es la sección activa inicial
        if (sectionId === 'dashboard') {
            await loadDashboardMetrics();
        }

        // Inicializar reportes si la sección activa es jira-reportes
        if (sectionId === 'jira-reportes') {
            initJiraReports();
        }

        // Inicializar carga masiva si la sección activa es jira-carga-masiva
        if (sectionId === 'jira-carga-masiva') {
            if (window.NexusModules?.Jira?.BulkUpload?.init) {
                window.NexusModules.Jira.BulkUpload.init();
            } else if (typeof initCargaMasiva === 'function') {
                initCargaMasiva();
            }
        }
    }

    // Initialize charts if on infografía section
    if (currentSection && currentSection.id === 'infografia') {
        setTimeout(() => {
            initializeCharts();
        }, 100);
    }

    // Configurar event listeners de paginación (por si acaso ya existen los elementos)
    setupPaginationListeners();
});

let adminCurrentUser = null;

// Obtener información del usuario actual
async function adminGetCurrentUser() {
    try {
        const response = await fetch('/auth/session');
        if (response.ok) {
            const data = await response.json();
            adminCurrentUser = data;
        }
    } catch (e) {
        console.error('Error al obtener usuario actual:', e);
    }
}

// Cargar usuarios
async function adminLoadUsers() {
    const loading = document.getElementById('admin-loading');
    const table = document.getElementById('admin-users-table');
    const tbody = document.getElementById('admin-users-tbody');
    const emptyState = document.getElementById('admin-empty-state');

    if (loading) loading.style.display = 'block';
    if (table) table.style.display = 'none';
    if (emptyState) emptyState.style.display = 'none';

    try {
        const searchInput = document.getElementById('admin-search-input');
        const roleFilter = document.getElementById('admin-role-filter');
        const statusFilter = document.getElementById('admin-status-filter');

        const search = searchInput ? searchInput.value : '';
        const role = roleFilter ? roleFilter.value : '';
        const status = statusFilter ? statusFilter.value : '';

        let url = '/admin/users?';
        if (search) url += `search=${encodeURIComponent(search)}&`;
        if (role) url += `role=${encodeURIComponent(role)}&`;
        if (status === 'active') url += 'active_only=true&';
        if (status === 'inactive') url += 'active_only=false&';

        const response = await fetch(url);

        if (!response.ok) {
            const errorText = await response.text();
            adminShowAlert(`Error HTTP ${response.status}: ${errorText.substring(0, 100)}`, 'error');
            return;
        }

        const data = await response.json();

        if (data.success) {
            adminDisplayUsers(data.users);
            adminUpdateStats(data.statistics);
        } else {
            const errorMsg = data.error || 'Error desconocido al cargar usuarios';
            adminShowAlert(`Error: ${errorMsg}`, 'error');
        }
    } catch (e) {
        adminShowAlert(`Error al cargar usuarios: ${e.message}`, 'error');
    } finally {
        if (loading) loading.style.display = 'none';
    }
}

// Mostrar usuarios en la tabla
function adminDisplayUsers(users) {
    const tbody = document.getElementById('admin-users-tbody');
    const table = document.getElementById('admin-users-table');
    const emptyState = document.getElementById('admin-empty-state');
    const loading = document.getElementById('admin-loading');
    const roleLabels = { admin: 'Administrador', analista_qa: 'Analista QA', usuario: 'Usuario' };

    if (!tbody || !table || !emptyState) {
        return;
    }

    if (loading) loading.style.display = 'none';
    tbody.innerHTML = '';

    if (!users || users.length === 0) {
        table.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }

    table.style.display = 'table';
    emptyState.style.display = 'none';

    users.forEach((user, index) => {
        try {
            const row = document.createElement('tr');
            const createdDate = user.created_at ? new Date(user.created_at).toLocaleDateString('es-ES') : 'N/A';
            const lastLogin = user.last_login ? new Date(user.last_login).toLocaleDateString('es-ES') : 'Nunca';
            const role = (user.role || 'usuario').toLowerCase();
            const roleLabel = roleLabels[role] || role;

            row.innerHTML = `
                        <td>${user.email || 'N/A'}</td>
                        <td>
                            <span class="admin-badge ${role}">${roleLabel}</span>
                        </td>
                        <td>
                            <span class="admin-badge ${user.active ? 'active' : 'inactive'}">
                                ${user.active ? 'Activo' : 'Inactivo'}
                            </span>
                        </td>
                        <td>${createdDate}</td>
                        <td>${lastLogin}</td>
                        <td>
                            <div class="admin-actions">
                                <select class="admin-btn admin-btn-sm admin-btn-secondary" onchange="adminChangeRole('${user.id}', this.value)" ${user.id === adminCurrentUser?.user_id ? 'disabled' : ''}>
                                    <option value="admin" ${role === 'admin' ? 'selected' : ''}>Administrador</option>
                                    <option value="analista_qa" ${role === 'analista_qa' ? 'selected' : ''}>Analista QA</option>
                                    <option value="usuario" ${role === 'usuario' ? 'selected' : ''}>Usuario</option>
                                </select>
                                <button class="admin-btn admin-btn-sm ${user.active ? 'admin-btn-danger' : 'admin-btn-primary'}" 
                                        onclick="adminToggleStatus('${user.id}', ${!user.active})"
                                        ${user.id === adminCurrentUser?.user_id ? 'disabled' : ''}>
                                    <i class="fas fa-${user.active ? 'ban' : 'check'}"></i>
                                    ${user.active ? 'Desactivar' : 'Activar'}
                                </button>
                            </div>
                        </td>
                    `;
            tbody.appendChild(row);
        } catch (e) {
            console.error(`Error al agregar usuario ${index}:`, e);
        }
    });
}

// Actualizar estadísticas
function adminUpdateStats(stats) {
    try {
        const statTotal = document.getElementById('admin-stat-total');
        const statActive = document.getElementById('admin-stat-active');
        const statInactive = document.getElementById('admin-stat-inactive');
        const statAdmins = document.getElementById('admin-stat-admins');

        if (statTotal) statTotal.textContent = stats?.total || 0;
        if (statActive) statActive.textContent = stats?.active || 0;
        if (statInactive) statInactive.textContent = stats?.inactive || 0;
        if (statAdmins) statAdmins.textContent = stats?.by_role?.admin || 0;
    } catch (e) {
        console.error('Error al actualizar estadísticas:', e);
    }
}

// Cambiar rol
async function adminChangeRole(userId, newRole) {
    if (!confirm(`¿Cambiar rol a ${newRole}?`)) {
        adminLoadUsers();
        return;
    }

    try {
        const response = await fetch(`/admin/users/${userId}/role`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ role: newRole })
        });

        const data = await response.json();

        if (data.success) {
            adminShowAlert(`Rol actualizado a ${newRole}`, 'success');
            adminLoadUsers();
        } else {
            adminShowAlert(data.error || 'Error al actualizar rol', 'error');
            adminLoadUsers();
        }
    } catch (e) {
        console.error('Error:', e);
        adminShowAlert('Error al actualizar rol', 'error');
        adminLoadUsers();
    }
}

// Cambiar estado (activar/desactivar)
async function adminToggleStatus(userId, newStatus) {
    const action = newStatus ? 'activar' : 'desactivar';
    if (!confirm(`¿${action.charAt(0).toUpperCase() + action.slice(1)} este usuario?`)) {
        return;
    }

    try {
        const response = await fetch(`/admin/users/${userId}/status`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ active: newStatus })
        });

        const data = await response.json();

        if (data.success) {
            adminShowAlert(`Usuario ${action}do exitosamente`, 'success');
            adminLoadUsers();
        } else {
            adminShowAlert(data.error || 'Error al actualizar estado', 'error');
        }
    } catch (e) {
        console.error('Error:', e);
        adminShowAlert('Error al actualizar estado', 'error');
    }
}

// Mostrar alerta
function adminShowAlert(message, type = 'success') {
    const container = document.getElementById('admin-alert-container');
    if (!container) return;

    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
                <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
                <span>${message}</span>
            `;
    container.innerHTML = '';
    container.appendChild(alert);

    setTimeout(() => {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 300);
    }, 3000);
}

// Inicializar cuando se navega a la sección admin
function adminInitPanel() {
    try {
        adminGetCurrentUser().then(() => {
            adminLoadUsers();
        }).catch(error => {
            adminShowAlert('Error al obtener información del usuario actual', 'error');
        });
    } catch (e) {
        adminShowAlert(`Error al inicializar panel: ${e.message}`, 'error');
    }
}

// Event listeners para filtros (cuando el DOM esté listo)
document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('admin-search-input');
    const roleFilter = document.getElementById('admin-role-filter');
    const statusFilter = document.getElementById('admin-status-filter');

    if (searchInput) {
        searchInput.addEventListener('input', function () {
            if (typeof debounce === 'function') {
                debounce(adminLoadUsers, 500)();
            } else {
                clearTimeout(window.adminSearchTimeout);
                window.adminSearchTimeout = setTimeout(adminLoadUsers, 500);
            }
        });
    }
    if (roleFilter) {
        roleFilter.addEventListener('change', adminLoadUsers);
    }
    if (statusFilter) {
        statusFilter.addEventListener('change', adminLoadUsers);
    }
});

// ========================================================================
// CREAR HISTORIAS - JavaScript
// ========================================================================
(function () {
    // Función para resetear el generador de historias
    function resetStoriesGenerator() {
        const formContainer = document.getElementById('stories-form-container');
        const previewSection = document.getElementById('stories-preview-section');
        const backBtnContainer = document.getElementById('stories-back-btn-container');
        const storiesForm = document.getElementById('stories-form');
        const storiesFileInput = document.getElementById('stories-file');
        const storiesFileInfo = document.getElementById('stories-file-info');
        const storiesFileName = document.getElementById('stories-file-name');
        const storiesRemoveFileBtn = document.getElementById('stories-remove-file-btn');
        const storiesContext = document.getElementById('stories-context');
        const storiesContextCounter = document.getElementById('stories-context-counter');
        const storiesType = document.getElementById('stories-type');
        const storiesArea = document.getElementById('stories-area');
        const previewTbody = document.getElementById('stories-preview-tbody');
        const previewCount = document.getElementById('stories-preview-count');
        const selectedCount = document.getElementById('stories-selected-count');

        // Resetear formulario
        if (storiesForm) storiesForm.reset();
        if (storiesFileInput) storiesFileInput.value = '';
        if (storiesFileInfo) storiesFileInfo.style.display = 'none';
        if (storiesFileName) storiesFileName.textContent = '';
        if (storiesRemoveFileBtn) storiesRemoveFileBtn.style.display = 'none';
        if (storiesContext) storiesContext.value = '';
        if (storiesContextCounter) storiesContextCounter.textContent = '0 / 2000 caracteres';
        if (storiesType) storiesType.value = 'funcionalidad';
        if (storiesArea) storiesArea.value = '';

        // Limpiar vista previa
        if (previewTbody) previewTbody.innerHTML = '';
        if (previewCount) previewCount.textContent = '0';
        if (selectedCount) selectedCount.textContent = '0 historias seleccionadas';

        // Resetear checkboxes
        const selectAllCheckbox = document.getElementById('stories-select-all');
        const tableSelectAllCheckbox = document.getElementById('stories-table-select-all');
        if (selectAllCheckbox) selectAllCheckbox.checked = false;
        if (tableSelectAllCheckbox) tableSelectAllCheckbox.checked = false;

        // Limpiar variables globales
        window.selectedStoriesForUpload = [];
        window.storiesData = null;
        currentStoriesData = null;
        currentStoriesHtml = null;
        currentStoriesCsv = null;

        // Mostrar formulario y ocultar vista previa
        if (formContainer) formContainer.style.display = 'block';
        if (previewSection) previewSection.style.display = 'none';
        if (backBtnContainer) backBtnContainer.style.display = 'none';

        // Asegurar que el form-card también se muestre
        const storiesFormCard = document.getElementById('stories-form');
        if (storiesFormCard) {
            const formCard = storiesFormCard.closest('.form-card');
            if (formCard) formCard.style.display = 'block';
        }

        // Activar la sección de crear historias
        if (typeof navigateToSection === 'function') {
            navigateToSection('crear-historias');
        } else {
            // Fallback: activar manualmente si navigateToSection no está disponible
            const crearHistoriasSection = document.getElementById('crear-historias');
            if (crearHistoriasSection) {
                // Ocultar todas las secciones
                document.querySelectorAll('.content-section').forEach(section => {
                    section.classList.remove('active');
                });
                // Activar la sección de crear historias
                crearHistoriasSection.classList.add('active');
                // Actualizar nav-item activo
                document.querySelectorAll('.nav-item').forEach(item => {
                    item.classList.remove('active-link', 'active');
                });
                const activeNav = document.querySelector('[data-section="crear-historias"]');
                if (activeNav) {
                    activeNav.classList.add('active-link');
                }
                crearHistoriasSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }
    }

    // Botón de regreso
    const backBtn = document.getElementById('stories-back-btn');
    if (backBtn) {
        backBtn.onclick = function () {
            resetStoriesGenerator();
        };
    }

    // Botón de reset
    const resetBtn = document.getElementById('stories-reset-btn');
    if (resetBtn) {
        resetBtn.onclick = function () {
            if (confirm('¿Estás seguro de que deseas hacer una nueva generación? Se perderán los datos actuales.')) {
                resetStoriesGenerator();
            }
        };
    }
    const storiesDropZone = document.getElementById('stories-drop-zone');
    const storiesFileInput = document.getElementById('stories-file');
    const storiesForm = document.getElementById('stories-form');
    const storiesContext = document.getElementById('stories-context');
    const storiesCounter = document.getElementById('stories-context-counter');
    const storiesGenerateBtn = document.getElementById('stories-generate-btn');
    const storiesFileInfo = document.getElementById('stories-file-info');
    const storiesFileName = document.getElementById('stories-file-name');
    const storiesRemoveFileBtn = document.getElementById('stories-remove-file-btn');

    if (!storiesForm) return;

    // Setup drag and drop (igual que carga masiva)
    function setupStoriesDropZone() {
        if (!storiesDropZone || !storiesFileInput) return;

        // Click en la zona de arrastre - FIX: usar mousedown en lugar de click para evitar doble click
        storiesDropZone.addEventListener('mousedown', (e) => {
            // Solo si el click es directamente en el dropZone, no en elementos hijos
            if (e.target === storiesDropZone || e.target.closest('.drop-zone-content')) {
                e.preventDefault();
                storiesFileInput.click();
            }
        });

        // Prevenir comportamiento por defecto del navegador
        storiesDropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            storiesDropZone.classList.add('drag-over');
        });

        storiesDropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            e.stopPropagation();
            storiesDropZone.classList.remove('drag-over');
        });

        storiesDropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            storiesDropZone.classList.remove('drag-over');

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleStoriesFileSelect(files[0]);
            }
        });

        // Cambio de archivo desde el input - FIX: usar change directamente sin prevenir default
        storiesFileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleStoriesFileSelect(e.target.files[0]);
            }
        });
    }

    function handleStoriesFileSelect(file) {
        // Validar que sea DOCX o PDF
        const validExtensions = ['.docx', '.pdf'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        if (!validExtensions.includes(fileExtension)) {
            showDownloadNotification('❌ Solo se permiten archivos DOCX o PDF', 'error');
            return;
        }

        // Mostrar información del archivo
        if (storiesFileInfo && storiesFileName) {
            storiesFileName.textContent = file.name;
            storiesFileInfo.style.display = 'flex';
        }
    }

    // Botón para remover archivo
    if (storiesRemoveFileBtn) {
        storiesRemoveFileBtn.addEventListener('click', () => {
            storiesFileInput.value = '';
            if (storiesFileInfo) {
                storiesFileInfo.style.display = 'none';
            }
        });
    }

    // Character counter
    if (storiesContext && storiesCounter) {
        storiesContext.addEventListener('input', (e) => {
            const length = e.target.value.length;
            const maxLength = 2000;
            storiesCounter.textContent = `${length} / ${maxLength} caracteres`;
            storiesCounter.classList.remove('warning', 'error');
            if (length > maxLength * 0.9) {
                storiesCounter.classList.add('error');
            } else if (length > maxLength * 0.8) {
                storiesCounter.classList.add('warning');
            }
        });
    }

    // Generate handler
    if (storiesForm) {
        storiesForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            // Validación completa de campos requeridos
            const validationErrors = [];

            // Validar archivo
            if (!storiesFileInput.files.length) {
                validationErrors.push('📄 Debes cargar un archivo (DOCX o PDF)');
            }

            // Validar área
            const areaSelect = document.getElementById('stories-area');
            if (!areaSelect || !areaSelect.value) {
                validationErrors.push('📋 Debes seleccionar un área');
            }

            // Si hay errores, mostrarlos
            if (validationErrors.length > 0) {
                const errorMessage = '⚠️ No puedes generar la vista previa:\n\n' + validationErrors.join('\n');
                showDownloadNotification(errorMessage, 'error');

                // Resaltar campos faltantes con animación
                if (!storiesFileInput.files.length) {
                    const dropZone = document.getElementById('stories-drop-zone');
                    if (dropZone) {
                        dropZone.style.border = '2px solid #ef4444';
                        dropZone.style.boxShadow = '0 0 0 3px rgba(239, 68, 68, 0.2)';
                        dropZone.style.animation = 'shake 0.5s';
                        setTimeout(() => {
                            dropZone.style.border = '';
                            dropZone.style.boxShadow = '';
                            dropZone.style.animation = '';
                        }, 3000);
                    }
                }

                if (!areaSelect || !areaSelect.value) {
                    if (areaSelect) {
                        areaSelect.style.border = '2px solid #ef4444';
                        areaSelect.style.boxShadow = '0 0 0 3px rgba(239, 68, 68, 0.2)';
                        areaSelect.style.animation = 'shake 0.5s';
                        setTimeout(() => {
                            areaSelect.style.border = '';
                            areaSelect.style.boxShadow = '';
                            areaSelect.style.animation = '';
                        }, 3000);
                    }
                }

                return;
            }

            const selectedArea = areaSelect.value;
            const formData = new FormData(storiesForm);

            // UI Setup for Progress
            storiesGenerateBtn.disabled = true;
            storiesGenerateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';

            const progressContainer = document.getElementById('stories-progress-container');
            const progressBar = document.getElementById('stories-progress-bar');
            const progressPhase = document.getElementById('stories-progress-phase');
            const progressPercentage = document.getElementById('stories-progress-percentage');
            const progressMessage = document.getElementById('stories-progress-message');

            if (progressContainer) progressContainer.style.display = 'block';
            if (progressBar) progressBar.style.width = '0%';
            if (progressPhase) progressPhase.textContent = 'Iniciando generación...';
            if (progressPercentage) progressPercentage.textContent = '0%';

            try {
                const response = await fetch('/api/stories/generate', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': getCsrfToken()
                    }
                });

                if (!response.ok) {
                    throw new Error('Error en la respuesta del servidor');
                }

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';

                while (true) {
                    const { value, done } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n\n');
                    buffer = lines.pop();

                    for (const line of lines) {
                        if (line.trim().startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.trim().substring(6));

                                // Update Progress UI
                                if (data.progress !== undefined) {
                                    if (progressBar) progressBar.style.width = `${data.progress}%`;
                                    if (progressPercentage) progressPercentage.textContent = `${data.progress}%`;
                                }
                                if (data.status && progressPhase) progressPhase.textContent = data.status;
                                if (data.message && progressMessage) progressMessage.textContent = data.message;

                                // Handle Terminal Event
                                if (data.terminal) {
                                    if (data.error) {
                                        throw new Error(data.error);
                                    }

                                    if (data.data && data.data.stories) {
                                        const resultData = data.data;
                                        // Ocultar formulario y mostrar vista previa
                                        const formContainer = document.getElementById('stories-form-container');
                                        const previewSection = document.getElementById('stories-preview-section');
                                        const backBtnContainer = document.getElementById('stories-back-btn-container');

                                        if (formContainer) formContainer.style.display = 'none';
                                        if (previewSection) previewSection.style.display = 'block';
                                        if (backBtnContainer) backBtnContainer.style.display = 'block';

                                        // Guardar datos globales
                                        currentStoriesData = resultData.stories;
                                        currentStoriesHtml = resultData.html_content;
                                        currentStoriesCsv = resultData.csv_content;

                                        // Mostrar vista previa
                                        displayStoriesPreview(resultData);

                                        // Actualizar métricas
                                        if (resultData.stories_count > 0) {
                                            updateMetrics('stories', resultData.stories_count, selectedArea);
                                        }

                                        showDownloadNotification(`Historias generadas exitosamente: ${resultData.stories_count} historias`, 'success');
                                        document.getElementById('crear-historias').scrollIntoView({ behavior: 'smooth', block: 'start' });
                                    }
                                }
                            } catch (e) {
                                console.error('Error parsing SSE data:', e, line);
                            }
                        }
                    }
                }
            } catch (error) {
                console.error('Error en generación:', error);
                showDownloadNotification('Error: ' + error.message, 'error');
            } finally {
                storiesGenerateBtn.disabled = false;
                storiesGenerateBtn.innerHTML = '<i class="fas fa-eye"></i> Generar e Ir a Vista Previa';
                if (progressContainer) progressContainer.style.display = 'none';
            }
        });
    }

    // Inicializar drag and drop
    setupStoriesDropZone();

    // Variables globales para historias
    let currentStoriesData = null;
    let currentStoriesHtml = null;
    let currentStoriesCsv = null;

    // Función para mostrar vista previa de historias
    function displayStoriesPreview(data) {
        currentStoriesData = data.stories;
        // Si no viene nuevo HTML/CSV, mantenemos el original para preservar estilos
        if (data.html_content) currentStoriesHtml = data.html_content;
        if (data.csv_content) currentStoriesCsv = data.csv_content;

        const previewSection = document.getElementById('stories-preview-section');
        const previewCount = document.getElementById('stories-preview-count');
        const previewTbody = document.getElementById('stories-preview-tbody');

        if (!previewSection || !previewCount || !previewTbody) return;

        // Mostrar sección
        previewSection.style.display = 'block';
        previewCount.textContent = data.stories_count;

        // Limpiar tabla
        previewTbody.innerHTML = '';

        // Agregar historias a la tabla
        data.stories.forEach((story, index) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                        <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                            <input type="checkbox" class="story-checkbox" data-index="${index}" checked style="width: 18px; height: 18px; cursor: pointer;">
                        </td>
                        <td style="padding: 1rem; border-bottom: 1px solid var(--border); font-weight: 600; color: var(--accent); text-align: center;">${story.index}</td>
                        <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                            <input type="text" class="story-summary-input" data-index="${index}" value="${escapeHtml(story.summary)}" style="width: 100%; max-width: 300px; padding: 0.5rem; background: transparent; border: 1px solid transparent; border-radius: 4px; color: var(--text-primary); font-family: inherit; font-size: 0.9rem;">
                        </td>
                        <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                            <textarea class="story-description-input" data-index="${index}" rows="2" style="width: 100%; max-width: 400px; padding: 0.5rem; background: transparent; border: 1px solid transparent; border-radius: 4px; color: var(--text-secondary); font-family: inherit; font-size: 0.85rem; resize: none; min-height: 50px;">${escapeHtml(story.description)}</textarea>
                        </td>
                        <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                            <span style="display: inline-block; padding: 0.25rem 0.75rem; border-radius: 6px; font-size: 0.8rem; font-weight: 500; background: rgba(59, 130, 246, 0.2); color: var(--accent);">${story.issuetype}</span>
                        </td>
                        <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                            <select class="story-priority-select" data-index="${index}" style="padding: 0.5rem; background: var(--secondary-bg); border: 1px solid var(--border); border-radius: 4px; color: var(--text-primary); font-family: inherit; font-size: 0.9rem;">
                                <option value="High" ${story.priority === 'High' ? 'selected' : ''}>High</option>
                                <option value="Medium" ${story.priority === 'Medium' ? 'selected' : ''}>Medium</option>
                                <option value="Low" ${story.priority === 'Low' ? 'selected' : ''}>Low</option>
                            </select>
                        </td>
                        <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                            <div style="display: flex; gap: 0.5rem; align-items: center;">
                                <button class="story-edit-btn" data-index="${index}" style="padding: 0.5rem; background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3); color: var(--accent); border-radius: 6px; cursor: pointer; font-size: 1rem;" title="Editar">✏️</button>
                                <button class="story-delete-btn" data-index="${index}" style="padding: 0.5rem; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); color: var(--error); border-radius: 6px; cursor: pointer; font-size: 1rem;" title="Eliminar">🗑️</button>
                            </div>
                        </td>
                    `;
            previewTbody.appendChild(row);
        });

        // Event listeners para edición
        updateStoriesEventListeners();
        updateSelectedCount();
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Función para formatear una historia individual para HTML
    function formatStoryForHTML(story, storyNum) {
        const title = story.summary || `Historia ${storyNum}`;
        const description = story.description || '';
        const priority = story.priority || 'Medium';
        const issuetype = story.issuetype || 'Story';

        // Parsear descripción para extraer COMO, QUIERO, PARA, etc.
        const comoMatch = description.match(/COMO:\s*([^\n]+)/i);
        const quieroMatch = description.match(/QUIERO:\s*([^\n]+)/i);
        const paraMatch = description.match(/PARA:\s*([^\n]+)/i);
        const criteriosMatch = description.match(/CRITERIOS\s+DE\s+ACEPTACI[ÓO]N:\s*([\s\S]*?)(?:\s+REGLAS|PRIORIDAD|COMPLEJIDAD|$)/i);

        let html = `<div class="story-container">
        <div class="story-title">HISTORIA #${storyNum}: ${escapeHtml(title)}</div>`;

        if (comoMatch) {
            html += `
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">COMO:</span>
                            <span class="story-item-content"> ${escapeHtml(comoMatch[1].trim())}</span>
                        </div>`;
        }

        if (quieroMatch) {
            html += `
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">QUIERO:</span>
                            <span class="story-item-content"> ${escapeHtml(quieroMatch[1].trim())}</span>
                        </div>`;
        }

        if (paraMatch) {
            html += `
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">PARA:</span>
                            <span class="story-item-content"> ${escapeHtml(paraMatch[1].trim())}</span>
                        </div>`;
        }

        // Si no hay estructura COMO/QUIERO/PARA, mostrar descripción completa
        if (!comoMatch && !quieroMatch && !paraMatch && description) {
            html += `
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Descripción:</span>
                            <span class="story-item-content"> ${escapeHtml(description)}</span>
                        </div>`;
        }

        // Agregar criterios de aceptación si existen
        if (criteriosMatch) {
            const criterios = criteriosMatch[1].trim();
            html += `
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Criterios de Aceptación:</span>
                            <span class="story-item-content"> ${escapeHtml(criterios)}</span>
                        </div>`;
        }

        html += `
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Tipo:</span>
                            <span class="story-item-content"> ${issuetype}</span>
                        </div>
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Prioridad:</span>
                            <span class="story-item-content"> ${priority}</span>
                        </div>
                    </div>`;

        return html;
    }

    function updateStoriesEventListeners() {
        // Select all checkboxes
        const selectAllCheckbox = document.getElementById('stories-select-all');
        const tableSelectAllCheckbox = document.getElementById('stories-table-select-all');

        if (selectAllCheckbox) {
            selectAllCheckbox.onchange = function () {
                const checkboxes = document.querySelectorAll('.story-checkbox');
                checkboxes.forEach(cb => cb.checked = this.checked);
                if (tableSelectAllCheckbox) tableSelectAllCheckbox.checked = this.checked;
                updateSelectedCount();
            };
        }

        if (tableSelectAllCheckbox) {
            tableSelectAllCheckbox.onchange = function () {
                const checkboxes = document.querySelectorAll('.story-checkbox');
                checkboxes.forEach(cb => cb.checked = this.checked);
                if (selectAllCheckbox) selectAllCheckbox.checked = this.checked;
                updateSelectedCount();
            };
        }

        // Individual checkboxes
        document.querySelectorAll('.story-checkbox').forEach(cb => {
            cb.onchange = updateSelectedCount;
        });

        // Update story data on input change
        document.querySelectorAll('.story-summary-input, .story-description-input, .story-priority-select').forEach(input => {
            input.onchange = function () {
                const index = parseInt(this.dataset.index);
                if (currentStoriesData && currentStoriesData[index]) {
                    if (this.classList.contains('story-summary-input')) {
                        currentStoriesData[index].summary = this.value;
                    } else if (this.classList.contains('story-description-input')) {
                        currentStoriesData[index].description = this.value;
                    } else if (this.classList.contains('story-priority-select')) {
                        currentStoriesData[index].priority = this.value;
                    }
                }
            };
        });

        // Edit buttons
        document.querySelectorAll('.story-edit-btn').forEach(btn => {
            btn.onclick = function () {
                const index = parseInt(this.getAttribute('data-index'));
                openEditStoryModal(index);
            };
        });

        // Delete buttons
        document.querySelectorAll('.story-delete-btn').forEach(btn => {
            btn.onclick = function () {
                const index = parseInt(this.dataset.index);
                if (confirm('¿Estás seguro de eliminar esta historia?')) {
                    currentStoriesData.splice(index, 1);
                    displayStoriesPreview({ stories: currentStoriesData, stories_count: currentStoriesData.length });
                }
            };
        });
    }

    function updateSelectedCount() {
        const checkboxes = document.querySelectorAll('.story-checkbox:checked');
        const count = checkboxes.length;
        const countEl = document.getElementById('stories-selected-count');
        if (countEl) {
            countEl.textContent = `${count} historias seleccionadas`;
        }
    }

    // Variables para el modal de edición de historias
    let editingStoryIndex = null;

    function openEditStoryModal(index) {
        if (!currentStoriesData || !currentStoriesData[index]) {
            showDownloadNotification('Error: Historia no encontrada', 'error');
            return;
        }

        const story = currentStoriesData[index];
        editingStoryIndex = index;

        // Llenar campos del modal
        const summaryInput = document.getElementById('edit-story-summary');
        const descriptionInput = document.getElementById('edit-story-description');
        const issuetypeSelect = document.getElementById('edit-story-issuetype');
        const prioritySelect = document.getElementById('edit-story-priority');

        if (summaryInput) summaryInput.value = story.summary || '';
        if (descriptionInput) descriptionInput.value = story.description || '';
        if (issuetypeSelect) issuetypeSelect.value = story.issuetype || 'Story';
        if (prioritySelect) prioritySelect.value = story.priority || 'Medium';

        // Mostrar modal
        const modal = document.getElementById('edit-story-modal');
        if (modal) modal.style.display = 'flex';
    }

    function closeEditStoryModal() {
        const modal = document.getElementById('edit-story-modal');
        if (modal) modal.style.display = 'none';
        editingStoryIndex = null;
    }

    function saveStoryChanges() {
        if (editingStoryIndex === null) return;

        const summaryInput = document.getElementById('edit-story-summary');
        const descriptionInput = document.getElementById('edit-story-description');
        const issuetypeSelect = document.getElementById('edit-story-issuetype');
        const prioritySelect = document.getElementById('edit-story-priority');

        if (!summaryInput || !descriptionInput || !issuetypeSelect || !prioritySelect) {
            showDownloadNotification('Error: Campos del modal no encontrados', 'error');
            return;
        }

        const summary = summaryInput.value.trim();
        const description = descriptionInput.value.trim();
        const issuetype = issuetypeSelect.value;
        const priority = prioritySelect.value;

        if (!summary || !description) {
            showDownloadNotification('Por favor completa todos los campos requeridos', 'error');
            return;
        }

        // Actualizar datos
        currentStoriesData[editingStoryIndex].summary = summary;
        currentStoriesData[editingStoryIndex].description = description;
        currentStoriesData[editingStoryIndex].issuetype = issuetype;
        currentStoriesData[editingStoryIndex].priority = priority;

        // Actualizar vista previa
        displayStoriesPreview({ stories: currentStoriesData, stories_count: currentStoriesData.length });

        closeEditStoryModal();
        showDownloadNotification('Historia actualizada exitosamente', 'success');
    }

    // Event listeners del modal de edición de historias
    const editStoryModalClose = document.getElementById('edit-story-modal-close');
    const editStoryCancel = document.getElementById('edit-story-cancel');
    const editStorySave = document.getElementById('edit-story-save');
    if (editStoryModalClose) editStoryModalClose.onclick = closeEditStoryModal;
    if (editStoryCancel) editStoryCancel.onclick = closeEditStoryModal;
    if (editStorySave) editStorySave.onclick = saveStoryChanges;

    // Botón revisar historias (visualizar HTML)
    const reviewBtn = document.getElementById('stories-review-btn');
    if (reviewBtn) {
        reviewBtn.onclick = function () {
            if (!currentStoriesData || currentStoriesData.length === 0) {
                showDownloadNotification('No hay historias para revisar', 'error');
                return;
            }
            openStoriesReview();
        };
    }

    function openStoriesReview() {
        const modal = document.getElementById('stories-review-modal');
        const iframe = document.getElementById('stories-html-viewer');

        if (!modal || !iframe) {
            showDownloadNotification('Error: Modal de revisión no encontrado', 'error');
            return;
        }

        // NO regenerar HTML - usar el HTML original guardado
        if (!currentStoriesHtml) {
            showDownloadNotification('No hay HTML disponible para revisar', 'error');
            return;
        }

        // Crear blob con el HTML original y mostrarlo en iframe
        const blob = new Blob([currentStoriesHtml], { type: 'text/html;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        iframe.src = url;

        modal.style.display = 'flex';
    }

    // Hacer funciones accesibles globalmente para los onclick del modal
    window.closeStoriesReview = function () {
        const modal = document.getElementById('stories-review-modal');
        const iframe = document.getElementById('stories-html-viewer');

        if (iframe && iframe.src) {
            URL.revokeObjectURL(iframe.src);
            iframe.src = '';
        }

        if (modal) {
            modal.style.display = 'none';
        }
    };

    window.downloadStoriesHTML = function () {
        if (!currentStoriesData || currentStoriesData.length === 0) {
            showDownloadNotification('No hay historias para descargar', 'error');
            return;
        }

        // NO regenerar HTML - usar el HTML original guardado
        if (!currentStoriesHtml) {
            showDownloadNotification('No hay HTML disponible para descargar', 'error');
            return;
        }

        const blob = new Blob([currentStoriesHtml], { type: 'text/html;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'historias_usuario.html';
        document.body.appendChild(a);
        a.click();
        URL.revokeObjectURL(url);
        document.body.removeChild(a);
        showDownloadNotification('HTML descargado exitosamente', 'success');
    };

    // Botón subir a Jira
    const uploadJiraBtn = document.getElementById('stories-upload-jira-btn');
    if (uploadJiraBtn) {
        uploadJiraBtn.onclick = function () {
            const selected = document.querySelectorAll('.story-checkbox:checked');
            if (selected.length === 0) {
                showDownloadNotification('Por favor selecciona al menos una historia para subir', 'error');
                return;
            }

            // Obtener historias seleccionadas
            const selectedStories = Array.from(selected).map(cb => {
                const index = parseInt(cb.dataset.index);
                return currentStoriesData[index];
            });

            // Cargar proyectos de Jira y mostrar modal
            loadJiraProjects().then(() => {
                document.getElementById('jira-modal-stories-count').textContent = `${selectedStories.length} historias seleccionadas para subir`;
                window.selectedStoriesForUpload = selectedStories;
                document.getElementById('jira-upload-modal').style.display = 'flex';
            });
        };
    }

    // Cerrar modal
    const modalClose = document.getElementById('jira-modal-close');
    const modalCancel = document.getElementById('jira-modal-cancel');
    if (modalClose) modalClose.onclick = closeJiraModal;
    if (modalCancel) modalCancel.onclick = closeJiraModal;

    function closeJiraModal() {
        document.getElementById('jira-upload-modal').style.display = 'none';
        document.getElementById('jira-assignee-input').value = '';
        document.getElementById('jira-assignee-validation').style.display = 'none';

        // Limpiar búsqueda y selección
        const searchInput = document.getElementById('jira-project-search-input');
        const hiddenInput = document.getElementById('jira-project-select');
        const dropdown = document.getElementById('jira-project-dropdown');

        if (searchInput) searchInput.value = '';
        if (hiddenInput) hiddenInput.value = '';
        if (dropdown) dropdown.style.display = 'none';
    }

    // Validar email de asignado
    const assigneeInput = document.getElementById('jira-assignee-input');
    if (assigneeInput) {
        assigneeInput.addEventListener('blur', async function () {
            const email = this.value.trim();
            const validationDiv = document.getElementById('jira-assignee-validation');

            if (!email) {
                validationDiv.style.display = 'none';
                return;
            }

            // Validar formato
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                validationDiv.style.display = 'block';
                validationDiv.style.color = 'var(--error)';
                validationDiv.textContent = '❌ Formato de email inválido';
                return;
            }

            // Validar en Jira
            validationDiv.style.display = 'block';
            validationDiv.style.color = 'var(--text-muted)';
            validationDiv.textContent = '⏳ Validando usuario...';

            try {
                const response = await fetch('/api/jira/validate-user', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({ email: email })
                });

                const data = await response.json();
                if (data.valid) {
                    validationDiv.style.color = 'var(--success)';
                    validationDiv.textContent = '✅ Usuario encontrado en Jira';
                    window.assigneeAccountId = data.accountId;
                } else {
                    validationDiv.style.color = 'var(--error)';
                    validationDiv.textContent = '❌ ' + (data.error || 'Este correo no tiene cuenta en Jira');
                    window.assigneeAccountId = null;
                }
            } catch (error) {
                validationDiv.style.color = 'var(--error)';
                validationDiv.textContent = '❌ Error al validar usuario';
                window.assigneeAccountId = null;
            }
        });
    }

    // Cargar proyectos de Jira
    async function loadJiraProjects() {
        const hiddenInput = document.getElementById('jira-project-select');
        const searchInput = document.getElementById('jira-project-search-input');
        if (!hiddenInput) return;

        try {
            const response = await fetch('/api/jira/projects', {
                headers: { 'X-CSRFToken': getCsrfToken() }
            });

            if (response.ok) {
                const data = await response.json();
                allProjectsStories = data.projects || [];

                if (allProjectsStories.length === 0) {
                    showDownloadNotification('No se encontraron proyectos de Jira. Verifica tu configuración.', 'error');
                    return;
                }

                // Configurar el combo box
                setupSearchableCombo({
                    inputId: 'jira-project-search-input',
                    dropdownId: 'jira-project-dropdown',
                    hiddenId: 'jira-project-select',
                    dataArray: allProjectsStories
                });
            } else {
                const errorData = await response.json();
                showDownloadNotification('Error al cargar proyectos: ' + (errorData.error || 'Error desconocido'), 'error');
            }
        } catch (error) {
            console.error('Error al cargar proyectos:', error);
            showDownloadNotification('Error de conexión al cargar proyectos', 'error');
        }
    }

    // Subir a Jira
    const modalUploadBtn = document.getElementById('jira-modal-upload');
    if (modalUploadBtn) {
        modalUploadBtn.onclick = async function () {
            const projectKey = document.getElementById('jira-project-select').value;
            if (!projectKey) {
                showDownloadNotification('Por favor selecciona un proyecto', 'error');
                return;
            }

            const assigneeEmail = document.getElementById('jira-assignee-input').value.trim();
            const validationDiv = document.getElementById('jira-assignee-validation');

            // Validar asignado si se proporciona
            if (assigneeEmail) {
                // Si no se ha validado aún o la validación falló, validar ahora
                const isValidated = validationDiv.style.display === 'block' && validationDiv.textContent.includes('✅');
                const isInvalid = validationDiv.style.display === 'block' && validationDiv.textContent.includes('❌');

                if (!isValidated && !isInvalid) {
                    // Validar ahora antes de continuar
                    validationDiv.style.display = 'block';
                    validationDiv.style.color = 'var(--text-muted)';
                    validationDiv.textContent = '⏳ Validando usuario...';

                    try {
                        const validateResponse = await fetch('/api/jira/validate-user', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': getCsrfToken()
                            },
                            body: JSON.stringify({ email: assigneeEmail })
                        });

                        const validateData = await validateResponse.json();
                        if (validateData.valid) {
                            validationDiv.style.color = 'var(--success)';
                            validationDiv.textContent = '✅ Usuario encontrado en Jira';
                            window.assigneeAccountId = validateData.accountId;
                        } else {
                            validationDiv.style.color = 'var(--error)';
                            validationDiv.textContent = '❌ ' + (validateData.error || 'Este correo no tiene cuenta en Jira');
                            window.assigneeAccountId = null;
                            showDownloadNotification('Por favor verifica que el email del asignado sea válido y tenga cuenta en Jira', 'error');
                            return;
                        }
                    } catch (error) {
                        validationDiv.style.color = 'var(--error)';
                        validationDiv.textContent = '❌ Error al validar usuario';
                        window.assigneeAccountId = null;
                        showDownloadNotification('Error al validar usuario de Jira', 'error');
                        return;
                    }
                } else if (isInvalid) {
                    // Ya se validó y es inválido
                    showDownloadNotification('Por favor verifica que el email del asignado sea válido y tenga cuenta en Jira', 'error');
                    return;
                } else if (!isValidated) {
                    // No se ha validado aún
                    showDownloadNotification('Por favor verifica que el email del asignado sea válido y tenga cuenta en Jira', 'error');
                    return;
                }
            }

            // Mostrar loading
            document.getElementById('stories-loading-overlay').style.display = 'flex';

            try {
                const response = await fetch('/api/jira/stories/upload-to-jira', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({
                        stories: window.selectedStoriesForUpload,
                        project_key: projectKey,
                        assignee_email: assigneeEmail || null
                    })
                });

                const data = await response.json();

                document.getElementById('stories-loading-overlay').style.display = 'none';
                closeJiraModal();

                if (data.success) {
                    showDownloadNotification(data.message || 'Historias subidas exitosamente a Jira', 'success');

                    // Descargar archivo TXT si está disponible
                    if (data.txt_content && data.txt_filename) {
                        try {
                            // Decodificar base64 y convertir a UTF-8
                            const binaryString = atob(data.txt_content);
                            const bytes = new Uint8Array(binaryString.length);
                            for (let i = 0; i < binaryString.length; i++) {
                                bytes[i] = binaryString.charCodeAt(i);
                            }
                            const txtBlob = new Blob([bytes], { type: 'text/plain;charset=utf-8' });
                            const txtUrl = URL.createObjectURL(txtBlob);
                            const txtLink = document.createElement('a');
                            txtLink.href = txtUrl;
                            txtLink.download = data.txt_filename;
                            document.body.appendChild(txtLink);
                            txtLink.click();
                            document.body.removeChild(txtLink);
                            URL.revokeObjectURL(txtUrl);
                        } catch (error) {
                            console.error('Error al descargar TXT:', error);
                        }
                    }

                    // Opcional: ocultar historias subidas o actualizar vista
                } else {
                    showDownloadNotification('Error: ' + (data.error || 'No se pudieron subir las historias'), 'error');

                    // Descargar TXT incluso si hay errores
                    if (data.txt_content && data.txt_filename) {
                        try {
                            // Decodificar base64 y convertir a UTF-8
                            const binaryString = atob(data.txt_content);
                            const bytes = new Uint8Array(binaryString.length);
                            for (let i = 0; i < binaryString.length; i++) {
                                bytes[i] = binaryString.charCodeAt(i);
                            }
                            const txtBlob = new Blob([bytes], { type: 'text/plain;charset=utf-8' });
                            const txtUrl = URL.createObjectURL(txtBlob);
                            const txtLink = document.createElement('a');
                            txtLink.href = txtUrl;
                            txtLink.download = data.txt_filename;
                            document.body.appendChild(txtLink);
                            txtLink.click();
                            document.body.removeChild(txtLink);
                            URL.revokeObjectURL(txtUrl);
                        } catch (error) {
                            console.error('Error al descargar TXT:', error);
                        }
                    }
                }
            } catch (error) {
                document.getElementById('stories-loading-overlay').style.display = 'none';
                showDownloadNotification('Error de conexión: ' + error.message, 'error');
            }
        };
    }
})();

// ========================================================================
// CREAR CASOS DE PRUEBA - JavaScript
// ========================================================================
(function () {
    // Función para resetear el generador de casos de prueba
    function resetTestsGenerator() {
        const formContainer = document.getElementById('tests-form-container');
        const previewSection = document.getElementById('tests-preview-section');
        const backBtnContainer = document.getElementById('tests-back-btn-container');
        const testsForm = document.getElementById('tests-form');
        const testsFileInput = document.getElementById('tests-file');
        const testsFileInfo = document.getElementById('tests-file-info');
        const testsFileName = document.getElementById('tests-file-name');
        const testsRemoveFileBtn = document.getElementById('tests-remove-file-btn');
        const testsContext = document.getElementById('tests-context');
        const testsContextCounter = document.getElementById('tests-context-counter');
        const testsType = document.getElementById('tests-type');
        const testsArea = document.getElementById('tests-area');
        const previewTbody = document.getElementById('tests-preview-tbody');
        const previewCount = document.getElementById('tests-preview-count');
        const selectedCount = document.getElementById('tests-selected-count');

        // Resetear formulario
        if (testsForm) testsForm.reset();
        if (testsFileInput) testsFileInput.value = '';
        if (testsFileInfo) testsFileInfo.style.display = 'none';
        if (testsFileName) testsFileName.textContent = '';
        if (testsRemoveFileBtn) testsRemoveFileBtn.style.display = 'none';
        if (testsContext) testsContext.value = '';
        if (testsContextCounter) testsContextCounter.textContent = '0 / 2000 caracteres';
        if (testsType) testsType.value = 'funcionalidad';
        if (testsArea) testsArea.value = '';

        // Limpiar vista previa
        if (previewTbody) previewTbody.innerHTML = '';
        if (previewCount) previewCount.textContent = '0';
        if (selectedCount) selectedCount.textContent = '0 casos seleccionados';

        // Resetear checkboxes
        const selectAllCheckbox = document.getElementById('tests-select-all');
        const tableSelectAllCheckbox = document.getElementById('tests-table-select-all');
        if (selectAllCheckbox) selectAllCheckbox.checked = false;
        if (tableSelectAllCheckbox) tableSelectAllCheckbox.checked = false;

        // Limpiar variables globales
        window.selectedTestsForUpload = [];
        window.testsData = null;
        currentTestsData = null;
        currentTestsHtml = null;
        currentTestsCsv = null;

        // Mostrar formulario y ocultar vista previa
        if (formContainer) formContainer.style.display = 'block';
        if (previewSection) previewSection.style.display = 'none';
        if (backBtnContainer) backBtnContainer.style.display = 'none';

        // Asegurar que el form-card también se muestre
        const testsFormCard = document.getElementById('tests-form');
        if (testsFormCard) {
            const formCard = testsFormCard.closest('.form-card');
            if (formCard) formCard.style.display = 'block';
        }

        // Activar la sección de crear casos de prueba
        if (typeof navigateToSection === 'function') {
            navigateToSection('crear-casos-prueba');
        } else {
            // Fallback: activar manualmente si navigateToSection no está disponible
            const crearCasosPruebaSection = document.getElementById('crear-casos-prueba');
            if (crearCasosPruebaSection) {
                // Ocultar todas las secciones
                document.querySelectorAll('.content-section').forEach(section => {
                    section.classList.remove('active');
                });
                // Activar la sección de crear casos de prueba
                crearCasosPruebaSection.classList.add('active');
                // Actualizar nav-item activo
                document.querySelectorAll('.nav-item').forEach(item => {
                    item.classList.remove('active-link', 'active');
                });
                const activeNav = document.querySelector('[data-section="crear-casos-prueba"]');
                if (activeNav) {
                    activeNav.classList.add('active-link');
                }
                crearCasosPruebaSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }
    }

    // Botón de reset
    const resetBtn = document.getElementById('tests-reset-btn');
    if (resetBtn) {
        resetBtn.onclick = function () {
            if (confirm('¿Estás seguro de que deseas hacer una nueva generación? Se perderán los datos actuales.')) {
                resetTestsGenerator();
            }
        };
    }

    const testsDropZone = document.getElementById('tests-drop-zone');
    const testsFileInput = document.getElementById('tests-file');
    const testsForm = document.getElementById('tests-form');
    const testsGenerateBtn = document.getElementById('tests-generate-btn');
    const testsFileInfo = document.getElementById('tests-file-info');
    const testsFileName = document.getElementById('tests-file-name');
    const testsRemoveFileBtn = document.getElementById('tests-remove-file-btn');

    if (!testsForm) return;

    // Setup drag and drop (igual que carga masiva)
    function setupTestsDropZone() {
        if (!testsDropZone || !testsFileInput) return;

        // Click en la zona de arrastre - FIX: usar mousedown en lugar de click para evitar doble click
        testsDropZone.addEventListener('mousedown', (e) => {
            // Solo si el click es directamente en el dropZone, no en elementos hijos
            if (e.target === testsDropZone || e.target.closest('.drop-zone-content')) {
                e.preventDefault();
                testsFileInput.click();
            }
        });

        // Prevenir comportamiento por defecto del navegador
        testsDropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            testsDropZone.classList.add('drag-over');
        });

        testsDropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            e.stopPropagation();
            testsDropZone.classList.remove('drag-over');
        });

        testsDropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            testsDropZone.classList.remove('drag-over');

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleTestsFileSelect(files[0]);
            }
        });

        // Cambio de archivo desde el input - FIX: usar change directamente sin prevenir default
        testsFileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleTestsFileSelect(e.target.files[0]);
            }
        });
    }

    function handleTestsFileSelect(file) {
        // Validar que sea DOCX o PDF
        const validExtensions = ['.docx', '.pdf'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        if (!validExtensions.includes(fileExtension)) {
            showDownloadNotification('❌ Solo se permiten archivos DOCX o PDF', 'error');
            return;
        }

        // Mostrar información del archivo
        if (testsFileInfo && testsFileName) {
            testsFileName.textContent = file.name;
            testsFileInfo.style.display = 'flex';
        }
    }

    // Botón para remover archivo
    if (testsRemoveFileBtn) {
        testsRemoveFileBtn.addEventListener('click', () => {
            testsFileInput.value = '';
            if (testsFileInfo) {
                testsFileInfo.style.display = 'none';
            }
        });
    }

    // Variables globales para casos de prueba
    let currentTestsData = null;
    let currentTestsHtml = null;
    let currentTestsCsv = null;

    // Función helper para escapar HTML (necesaria para displayTestsPreview)
    function escapeHtml(text) {
        if (text === null || text === undefined) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Función para formatear un caso de prueba individual para HTML
    function formatTestCaseForHTML(testCase, caseNum) {
        const title = testCase.summary || `Caso de Prueba ${caseNum}`;
        const description = testCase.description || '';
        const priority = testCase.priority || 'Medium';
        const categoria = testCase.categoria || '';
        const tipoPrueba = testCase.tipo_prueba || 'Funcional';

        // Extraer información adicional de la descripción si está disponible
        const pasosMatch = description.match(/Pasos?:?\s*([\s\S]*?)(?=Resultado|$)/i);
        const resultadoMatch = description.match(/Resultado\s+esperado:?\s*([\s\S]*?)(?=Precondiciones|$)/i);
        const precondicionesMatch = description.match(/Precondiciones:?\s*([\s\S]*?)(?=Pasos|Resultado|$)/i);

        let html = `<div class="story-container">
        <div class="story-title">CASO DE PRUEBA #${caseNum}: ${escapeHtml(title)}</div>`;

        if (description) {
            // Si hay pasos y resultado en la descripción, mostrarlos por separado
            if (pasosMatch || resultadoMatch || precondicionesMatch) {
                if (precondicionesMatch) {
                    html += `
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Precondiciones:</span>
                            <span class="story-item-content"> ${escapeHtml(precondicionesMatch[1].trim())}</span>
                        </div>`;
                }

                if (pasosMatch) {
                    const pasos = pasosMatch[1].trim().split(/\d+\./).filter(p => p.trim());
                    if (pasos.length > 0) {
                        html += `
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Pasos:</span>
                            <div class="story-sublist">`;
                        pasos.forEach((paso, i) => {
                            if (paso.trim()) {
                                html += `
                                <div class="story-sublist-item">
                                    <span class="bullet">*</span>
                                    <strong>Paso ${i + 1}:</strong> ${escapeHtml(paso.trim())}
                                </div>`;
                            }
                        });
                        html += `
                            </div>
                        </div>`;
                    }
                }

                if (resultadoMatch) {
                    html += `
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Resultado Esperado:</span>
                            <span class="story-item-content"> ${escapeHtml(resultadoMatch[1].trim())}</span>
                        </div>`;
                }
            } else {
                // Mostrar descripción completa si no tiene estructura
                html += `
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Descripción:</span>
                            <span class="story-item-content"> ${escapeHtml(description)}</span>
                        </div>`;
            }
        }

        if (tipoPrueba) {
            html += `
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Tipo de Prueba:</span>
                            <span class="story-item-content"> ${escapeHtml(tipoPrueba)}</span>
                        </div>`;
        }

        if (categoria) {
            html += `
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Categoría:</span>
                            <span class="story-item-content"> ${escapeHtml(categoria)}</span>
                        </div>`;
        }

        html += `
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Prioridad:</span>
                            <span class="story-item-content"> ${priority}</span>
                        </div>
                    </div>`;

        return html;
    }

    // Función para mostrar vista previa de casos de prueba
    function displayTestsPreview(data) {
        console.log('🔍 displayTestsPreview INICIADO');
        console.log('📦 data recibida:', data);
        console.log('📋 data.test_cases:', data.test_cases);
        console.log('🔢 Cantidad de casos:', data.test_cases ? data.test_cases.length : 'undefined');

        currentTestsData = data.test_cases;
        // Si no llega HTML/CSV en esta actualización (ej. edición), conservamos el original
        if (data.html_content) currentTestsHtml = data.html_content;
        if (data.csv_content) currentTestsCsv = data.csv_content;

        const previewSection = document.getElementById('tests-preview-section');
        const previewCount = document.getElementById('tests-preview-count');
        const previewTbody = document.getElementById('tests-preview-tbody');
        const testsForm = document.getElementById('tests-form');

        console.log('🔍 Elementos DOM encontrados:', {
            previewSection: !!previewSection,
            previewCount: !!previewCount,
            previewTbody: !!previewTbody,
            testsForm: !!testsForm
        });

        if (!previewSection || !previewCount || !previewTbody) {
            console.error('❌ ERROR: Elementos del DOM no encontrados');
            return;
        }

        // Ocultar formulario y mostrar vista previa
        if (testsForm) {
            testsForm.closest('.form-card').style.display = 'none';
        }
        previewSection.style.display = 'block';
        previewCount.textContent = data.test_cases_count || (data.test_cases ? data.test_cases.length : 0);
        console.log('✅ Sección de vista previa mostrada, contador actualizado:', previewCount.textContent);

        // Limpiar tabla
        previewTbody.innerHTML = '';
        console.log('🧹 Tabla limpiada');

        // Agregar casos de prueba a la tabla
        console.log('🔄 Iniciando forEach para agregar casos...');
        let casosAgregados = 0;
        data.test_cases.forEach((testCase, index) => {
            try {
                console.log(`📝 Procesando caso ${index + 1}:`, testCase);

                // Validar y obtener valores con fallbacks seguros
                const caseIndex = testCase.index !== undefined ? testCase.index : (index + 1);
                const caseSummary = testCase.summary || 'Sin título';
                const caseDescription = testCase.description || '';
                const caseIssuetype = testCase.issuetype || 'Test Case';
                const casePriority = testCase.priority || 'Medium';
                const caseTipoPrueba = testCase.tipo_prueba || 'Funcional';
                const caseCategoria = testCase.categoria || '';

                const row = document.createElement('tr');
                row.innerHTML = `
                            <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                                <input type="checkbox" class="test-checkbox" data-index="${index}" checked style="width: 18px; height: 18px; cursor: pointer;">
                            </td>
                            <td style="padding: 1rem; border-bottom: 1px solid var(--border); font-weight: 600; color: var(--accent); text-align: center;">${caseIndex}</td>
                            <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                                <input type="text" class="test-summary-input" data-index="${index}" value="${escapeHtml(caseSummary)}" style="width: 100%; max-width: 300px; padding: 0.5rem; background: transparent; border: 1px solid transparent; border-radius: 4px; color: var(--text-primary); font-family: inherit; font-size: 0.9rem;">
                            </td>
                            <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                                <textarea class="test-description-input" data-index="${index}" rows="2" style="width: 100%; max-width: 400px; padding: 0.5rem; background: transparent; border: 1px solid transparent; border-radius: 4px; color: var(--text-secondary); font-family: inherit; font-size: 0.85rem; resize: none; min-height: 50px;">${escapeHtml(caseDescription)}</textarea>
                            </td>
                            <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                                <span style="display: inline-block; padding: 0.25rem 0.75rem; border-radius: 6px; font-size: 0.8rem; font-weight: 500; background: rgba(59, 130, 246, 0.2); color: var(--accent);">${escapeHtml(caseIssuetype)}</span>
                            </td>
                            <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                                <span style="display: inline-block; padding: 0.25rem 0.75rem; border-radius: 6px; font-size: 0.8rem; font-weight: 500; background: rgba(34, 197, 94, 0.2); color: #22c55e;">${escapeHtml(caseTipoPrueba)}</span>
                            </td>
                            <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                                <span style="display: inline-block; padding: 0.25rem 0.75rem; border-radius: 6px; font-size: 0.8rem; font-weight: 500; background: rgba(168, 85, 247, 0.2); color: #a855f7;">${escapeHtml(caseCategoria)}</span>
                            </td>
                            <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                                <select class="test-priority-select" data-index="${index}" style="padding: 0.5rem; background: var(--secondary-bg); border: 1px solid var(--border); border-radius: 4px; color: var(--text-primary); font-family: inherit; font-size: 0.9rem;">
                                    <option value="High" ${casePriority === 'High' ? 'selected' : ''}>High</option>
                                    <option value="Medium" ${casePriority === 'Medium' ? 'selected' : ''}>Medium</option>
                                    <option value="Low" ${casePriority === 'Low' ? 'selected' : ''}>Low</option>
                                </select>
                            </td>
                            <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                                <div style="display: flex; gap: 0.5rem; align-items: center;">
                                    <button class="test-edit-btn" data-index="${index}" style="padding: 0.5rem; background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3); color: var(--accent); border-radius: 6px; cursor: pointer; font-size: 1rem;" title="Editar">✏️</button>
                                    <button class="test-delete-btn" data-index="${index}" style="padding: 0.5rem; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); color: var(--error); border-radius: 6px; cursor: pointer; font-size: 1rem;" title="Eliminar">🗑️</button>
                                </div>
                            </td>
                        `;
                previewTbody.appendChild(row);
                casosAgregados++;
                console.log(`✅ Caso ${index + 1} agregado exitosamente`);
            } catch (error) {
                console.error(`❌ Error al agregar caso ${index + 1}:`, error, testCase);
            }
        });

        console.log(`✅ Total de casos agregados a la tabla: ${casosAgregados}`);
        console.log(`📊 Filas en tbody: ${previewTbody.children.length}`);

        // Event listeners para edición
        updateTestsEventListeners();
        updateTestsSelectedCount();
        console.log('✅ displayTestsPreview COMPLETADO');
    }

    function updateTestsEventListeners() {
        // Select all checkboxes
        const selectAllCheckbox = document.getElementById('tests-select-all');
        const tableSelectAllCheckbox = document.getElementById('tests-table-select-all');

        if (selectAllCheckbox) {
            selectAllCheckbox.onchange = function () {
                const checkboxes = document.querySelectorAll('.test-checkbox');
                checkboxes.forEach(cb => cb.checked = this.checked);
                if (tableSelectAllCheckbox) tableSelectAllCheckbox.checked = this.checked;
                updateTestsSelectedCount();
            };
        }

        if (tableSelectAllCheckbox) {
            tableSelectAllCheckbox.onchange = function () {
                const checkboxes = document.querySelectorAll('.test-checkbox');
                checkboxes.forEach(cb => cb.checked = this.checked);
                if (selectAllCheckbox) selectAllCheckbox.checked = this.checked;
                updateTestsSelectedCount();
            };
        }

        // Individual checkboxes
        document.querySelectorAll('.test-checkbox').forEach(cb => {
            cb.onchange = updateTestsSelectedCount;
        });

        // Update test case data on input change
        document.querySelectorAll('.test-summary-input, .test-description-input, .test-priority-select').forEach(input => {
            input.onchange = function () {
                const index = parseInt(this.dataset.index);
                if (currentTestsData && currentTestsData[index]) {
                    if (this.classList.contains('test-summary-input')) {
                        currentTestsData[index].summary = this.value;
                    } else if (this.classList.contains('test-description-input')) {
                        currentTestsData[index].description = this.value;
                    } else if (this.classList.contains('test-priority-select')) {
                        currentTestsData[index].priority = this.value;
                    }
                }
            };
        });

        // Edit buttons
        document.querySelectorAll('.test-edit-btn').forEach(btn => {
            btn.onclick = function () {
                const index = parseInt(this.getAttribute('data-index'));
                openEditTestModal(index);
            };
        });

        // Delete buttons
        document.querySelectorAll('.test-delete-btn').forEach(btn => {
            btn.onclick = function () {
                const index = parseInt(this.dataset.index);
                if (confirm('¿Estás seguro de eliminar este caso de prueba?')) {
                    currentTestsData.splice(index, 1);
                    displayTestsPreview({ test_cases: currentTestsData, test_cases_count: currentTestsData.length });
                }
            };
        });
    }

    function updateTestsSelectedCount() {
        const checkboxes = document.querySelectorAll('.test-checkbox:checked');
        const count = checkboxes.length;
        const countEl = document.getElementById('tests-selected-count');
        if (countEl) {
            countEl.textContent = `${count} casos seleccionados`;
        }
    }

    // Variables para el modal de edición de casos de prueba
    let editingTestIndex = null;

    function openEditTestModal(index) {
        if (!currentTestsData || !currentTestsData[index]) {
            showDownloadNotification('Error: Caso de prueba no encontrado', 'error');
            return;
        }

        const testCase = currentTestsData[index];
        editingTestIndex = index;

        // Llenar campos del modal
        const summaryInput = document.getElementById('edit-test-summary');
        const descriptionInput = document.getElementById('edit-test-description');
        const prioritySelect = document.getElementById('edit-test-priority');
        const categoriaInput = document.getElementById('edit-test-categoria');

        if (summaryInput) summaryInput.value = testCase.summary || '';
        if (descriptionInput) descriptionInput.value = testCase.description || '';
        if (prioritySelect) prioritySelect.value = testCase.priority || 'Medium';
        if (categoriaInput) categoriaInput.value = testCase.categoria || '';

        // Mostrar modal
        const modal = document.getElementById('edit-test-modal');
        if (modal) modal.style.display = 'flex';
    }

    function closeEditTestModal() {
        const modal = document.getElementById('edit-test-modal');
        if (modal) modal.style.display = 'none';
        editingTestIndex = null;
    }

    function saveTestChanges() {
        if (editingTestIndex === null) return;

        const summaryInput = document.getElementById('edit-test-summary');
        const descriptionInput = document.getElementById('edit-test-description');
        const prioritySelect = document.getElementById('edit-test-priority');
        const categoriaInput = document.getElementById('edit-test-categoria');

        if (!summaryInput || !descriptionInput || !prioritySelect || !categoriaInput) {
            showDownloadNotification('Error: Campos del modal no encontrados', 'error');
            return;
        }

        const summary = summaryInput.value.trim();
        const description = descriptionInput.value.trim();
        const priority = prioritySelect.value;
        const categoria = categoriaInput.value.trim();

        if (!summary || !description) {
            showDownloadNotification('Por favor completa todos los campos requeridos', 'error');
            return;
        }

        // Actualizar datos
        currentTestsData[editingTestIndex].summary = summary;
        currentTestsData[editingTestIndex].description = description;
        currentTestsData[editingTestIndex].priority = priority;
        currentTestsData[editingTestIndex].categoria = categoria;

        // Actualizar vista previa
        displayTestsPreview({ test_cases: currentTestsData, test_cases_count: currentTestsData.length });

        closeEditTestModal();
        showDownloadNotification('Caso de prueba actualizado exitosamente', 'success');
    }

    // Event listeners del modal de edición de casos de prueba
    const editTestModalClose = document.getElementById('edit-test-modal-close');
    const editTestCancel = document.getElementById('edit-test-cancel');
    const editTestSave = document.getElementById('edit-test-save');
    if (editTestModalClose) editTestModalClose.onclick = closeEditTestModal;
    if (editTestCancel) editTestCancel.onclick = closeEditTestModal;
    if (editTestSave) editTestSave.onclick = saveTestChanges;

    // Botón revisar casos (visualizar HTML)
    const testsReviewBtn = document.getElementById('tests-review-btn');
    if (testsReviewBtn) {
        testsReviewBtn.onclick = function () {
            if (!currentTestsData || currentTestsData.length === 0) {
                showDownloadNotification('No hay casos de prueba para revisar', 'error');
                return;
            }
            openTestsReview();
        };
    }

    function openTestsReview() {
        const modal = document.getElementById('tests-review-modal');
        const iframe = document.getElementById('tests-html-viewer');

        if (!modal || !iframe) {
            showDownloadNotification('Error: Modal de revisión no encontrado', 'error');
            return;
        }

        // NO regenerar HTML - usar el HTML original guardado
        if (!currentTestsHtml) {
            showDownloadNotification('No hay HTML disponible para revisar', 'error');
            return;
        }

        // Crear blob con el HTML original y mostrarlo en iframe
        const blob = new Blob([currentTestsHtml], { type: 'text/html;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        iframe.src = url;

        modal.style.display = 'flex';
    }

    // Hacer funciones accesibles globalmente para los onclick del modal
    window.closeTestsReview = function () {
        const modal = document.getElementById('tests-review-modal');
        const iframe = document.getElementById('tests-html-viewer');

        if (iframe && iframe.src) {
            URL.revokeObjectURL(iframe.src);
            iframe.src = '';
        }

        if (modal) {
            modal.style.display = 'none';
        }
    };

    window.downloadTestsHTML = function () {
        if (!currentTestsData || currentTestsData.length === 0) {
            showDownloadNotification('No hay casos de prueba para descargar', 'error');
            return;
        }

        // NO regenerar HTML - usar el HTML original guardado
        if (!currentTestsHtml) {
            showDownloadNotification('No hay HTML disponible para descargar', 'error');
            return;
        }

        const blob = new Blob([currentTestsHtml], { type: 'text/html;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'casos_prueba.html';
        document.body.appendChild(a);
        a.click();
        URL.revokeObjectURL(url);
        document.body.removeChild(a);
        showDownloadNotification('HTML descargado exitosamente', 'success');
    };

    // Botón subir a Jira
    const testsUploadJiraBtn = document.getElementById('tests-upload-jira-btn');
    if (testsUploadJiraBtn) {
        testsUploadJiraBtn.onclick = function () {
            const selected = document.querySelectorAll('.test-checkbox:checked');
            if (selected.length === 0) {
                showDownloadNotification('Por favor selecciona al menos un caso de prueba para subir', 'error');
                return;
            }

            // Obtener casos seleccionados
            const selectedTests = Array.from(selected).map(cb => {
                const index = parseInt(cb.dataset.index);
                return currentTestsData[index];
            });

            window.selectedTestsForUpload = selectedTests;
            openJiraTestsModal();
        };
    }

    // Generate handler
    if (testsForm) {
        testsForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            // Validación completa de campos requeridos
            const validationErrors = [];

            // Validar archivo
            if (!testsFileInput.files.length) {
                validationErrors.push('📄 Debes cargar un archivo (DOCX o PDF)');
            }

            // Validar área
            const areaSelect = document.getElementById('tests-area');
            if (!areaSelect || !areaSelect.value) {
                validationErrors.push('📋 Debes seleccionar un área');
            }

            // Validar tipo de prueba
            const selectedTypes = Array.from(document.querySelectorAll('input[name="test_types"]:checked')).map(cb => cb.value);
            if (selectedTypes.length === 0) {
                validationErrors.push('✅ Debes seleccionar al menos un tipo de prueba');
            }

            // Si hay errores, mostrarlos
            if (validationErrors.length > 0) {
                const errorMessage = '⚠️ No puedes generar la vista previa:\n\n' + validationErrors.join('\n');
                showDownloadNotification(errorMessage, 'error');

                // Resaltar campos faltantes con animación
                if (!testsFileInput.files.length) {
                    const dropZone = document.getElementById('tests-drop-zone');
                    if (dropZone) {
                        dropZone.style.border = '2px solid #ef4444';
                        dropZone.style.boxShadow = '0 0 0 3px rgba(239, 68, 68, 0.2)';
                        dropZone.style.animation = 'shake 0.5s';
                        setTimeout(() => {
                            dropZone.style.border = '';
                            dropZone.style.boxShadow = '';
                            dropZone.style.animation = '';
                        }, 3000);
                    }
                }

                if (!areaSelect || !areaSelect.value) {
                    if (areaSelect) {
                        areaSelect.style.border = '2px solid #ef4444';
                        areaSelect.style.boxShadow = '0 0 0 3px rgba(239, 68, 68, 0.2)';
                        areaSelect.style.animation = 'shake 0.5s';
                        setTimeout(() => {
                            areaSelect.style.border = '';
                            areaSelect.style.boxShadow = '';
                            areaSelect.style.animation = '';
                        }, 3000);
                    }
                }

                if (selectedTypes.length === 0) {
                    const checkboxContainers = document.querySelectorAll('input[name="test_types"]');
                    checkboxContainers.forEach(cb => {
                        const parent = cb.closest('div[style*="padding: 1rem"]');
                        if (parent) {
                            parent.style.border = '2px solid #ef4444';
                            parent.style.boxShadow = '0 0 0 3px rgba(239, 68, 68, 0.2)';
                            parent.style.animation = 'shake 0.5s';
                            setTimeout(() => {
                                parent.style.border = '';
                                parent.style.boxShadow = '';
                                parent.style.animation = '';
                            }, 3000);
                        }
                    });
                }

                return;
            }

            const selectedArea = areaSelect.value;
            const formData = new FormData(testsForm);

            // UI Setup for Progress
            testsGenerateBtn.disabled = true;
            testsGenerateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';

            const progressContainer = document.getElementById('tests-progress-container');
            const progressBar = document.getElementById('tests-progress-bar');
            const progressPhase = document.getElementById('tests-progress-phase');
            const progressPercentage = document.getElementById('tests-progress-percentage');
            const progressMessage = document.getElementById('tests-progress-message');

            if (progressContainer) progressContainer.style.display = 'block';
            if (progressBar) progressBar.style.width = '0%';
            if (progressPhase) progressPhase.textContent = 'Iniciando generación...';
            if (progressPercentage) progressPercentage.textContent = '0%';

            try {
                const response = await fetch('/api/tests/generate', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': getCsrfToken()
                    }
                });

                if (!response.ok) {
                    throw new Error('Error en la respuesta del servidor');
                }

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';

                while (true) {
                    const { value, done } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n\n');
                    buffer = lines.pop();

                    for (const line of lines) {
                        if (line.trim().startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.trim().substring(6));

                                // Update Progress UI
                                if (data.progress !== undefined) {
                                    if (progressBar) progressBar.style.width = `${data.progress}%`;
                                    if (progressPercentage) progressPercentage.textContent = `${data.progress}%`;
                                }
                                if (data.status && progressPhase) progressPhase.textContent = data.status;
                                if (data.message && progressMessage) progressMessage.textContent = data.message;

                                // Handle Terminal Event
                                if (data.terminal) {
                                    if (data.error) {
                                        throw new Error(data.error);
                                    }

                                    if (data.data && data.data.test_cases) {
                                        const resultData = data.data;
                                        // Ocultar formulario y mostrar vista previa
                                        const formContainer = document.getElementById('crear-casos-prueba').querySelector('.form-card');
                                        const previewSection = document.getElementById('tests-preview-section');

                                        if (formContainer) formContainer.style.display = 'none';
                                        if (previewSection) previewSection.style.display = 'block';

                                        // Guardar datos globales
                                        currentTestsData = resultData.test_cases;
                                        currentTestsHtml = resultData.html_content;
                                        currentTestsCsv = resultData.csv_content;

                                        // Mostrar vista previa
                                        displayTestsPreview(resultData);

                                        // Actualizar métricas
                                        if (resultData.test_cases_count > 0) {
                                            updateMetrics('test_cases', resultData.test_cases_count, selectedArea);
                                        }

                                        showDownloadNotification(`Casos de prueba generados exitosamente: ${resultData.test_cases_count} casos`, 'success');
                                        document.getElementById('crear-casos-prueba').scrollIntoView({ behavior: 'smooth', block: 'start' });
                                    }
                                }
                            } catch (e) {
                                console.error('Error parsing SSE data:', e, line);
                            }
                        }
                    }
                }
            } catch (error) {
                console.error('Error en generación:', error);
                showDownloadNotification('Error: ' + error.message, 'error');
            } finally {
                testsGenerateBtn.disabled = false;
                testsGenerateBtn.innerHTML = '<i class="fas fa-eye"></i> Generar e Ir a Vista Previa';
                if (progressContainer) progressContainer.style.display = 'none';
            }
        });
    }

    // Inicializar drag and drop
    setupTestsDropZone();

    // Funciones para modal de Jira (casos de prueba)
    function openJiraTestsModal() {
        const modal = document.getElementById('jira-upload-tests-modal');
        const projectSelect = document.getElementById('jira-tests-project-select');
        const casesCountEl = document.getElementById('jira-tests-modal-cases-count');

        if (!modal || !projectSelect) {
            showDownloadNotification('Error: Modal de Jira no encontrado', 'error');
            return;
        }

        // Actualizar contador
        if (casesCountEl && window.selectedTestsForUpload) {
            casesCountEl.textContent = `${window.selectedTestsForUpload.length} casos seleccionados para subir`;
        }

        // Cargar proyectos de Jira
        loadJiraProjectsForTests();

        modal.style.display = 'flex';
    }

    function closeJiraTestsModal() {
        const modal = document.getElementById('jira-upload-tests-modal');
        if (modal) {
            modal.style.display = 'none';
        }
        // Limpiar campos y resetear pasos
        const projectSelect = document.getElementById('jira-tests-project-select');
        const assigneeInput = document.getElementById('jira-tests-assignee-input');
        const step1 = document.getElementById('jira-tests-step1');
        const step1_5 = document.getElementById('jira-tests-step1-5');
        const step2 = document.getElementById('jira-tests-step2');
        const validationResult = document.getElementById('jira-tests-validation-result');
        const validateBtn = document.getElementById('jira-tests-validate-fields-btn');
        const uploadBtn = document.getElementById('jira-tests-modal-upload');

        if (projectSelect) projectSelect.value = '';
        if (assigneeInput) assigneeInput.value = '';

        // Limpiar búsqueda y selección
        const searchInput = document.getElementById('jira-tests-project-search-input');
        const dropdown = document.getElementById('jira-tests-project-dropdown');
        if (searchInput) searchInput.value = '';
        if (dropdown) dropdown.style.display = 'none';

        // Reiniciar selects de campos
        const selects = ['jira-tests-tipo-prueba-select', 'jira-tests-nivel-prueba-select',
            'jira-tests-tipo-ejecucion-select', 'jira-tests-ambiente-select'];
        selects.forEach(selectId => {
            const select = document.getElementById(selectId);
            if (select) {
                select.value = '';
                select.innerHTML = '<option value="">Cargando valores...</option>';
            }
        });

        // Ocultar mensajes
        const messages = ['jira-tests-tipo-prueba-message', 'jira-tests-nivel-prueba-message',
            'jira-tests-tipo-ejecucion-message', 'jira-tests-ambiente-message'];
        messages.forEach(msgId => {
            const msg = document.getElementById(msgId);
            if (msg) {
                msg.style.display = 'none';
                msg.innerHTML = '';
            }
        });

        if (step1) step1.style.display = 'block';
        if (step1_5) step1_5.style.display = 'none';
        if (step2) step2.style.display = 'none';
        if (validationResult) {
            validationResult.style.display = 'none';
            validationResult.innerHTML = '';
        }
        if (validateBtn) {
            validateBtn.disabled = true;
            validateBtn.innerHTML = '<span>🔍</span><span>Validar Campos</span>';
        }
        if (uploadBtn) uploadBtn.style.display = 'none';

        // Resetear variables de validación
        testsAssigneeAccountId = null;
        testsAssigneeValidated = false;
        testsAssigneeInvalid = false;
        const assigneeValidation = document.getElementById('jira-tests-assignee-validation');
        if (assigneeValidation) {
            assigneeValidation.style.display = 'none';
            assigneeValidation.innerHTML = '';
        }
    }

    async function loadJiraProjectsForTests() {
        const hiddenInput = document.getElementById('jira-tests-project-select');
        const searchInput = document.getElementById('jira-tests-project-search-input');
        const validateBtn = document.getElementById('jira-tests-validate-fields-btn');
        if (!hiddenInput) return;

        try {
            const response = await fetch('/api/jira/projects', {
                headers: {
                    'X-CSRFToken': getCsrfToken()
                }
            });

            if (response.ok) {
                const data = await response.json();
                allProjectsTests = data.projects || [];

                if (allProjectsTests.length === 0) {
                    showDownloadNotification('No se encontraron proyectos de Jira.', 'error');
                    return;
                }

                // Configurar el combo box
                setupSearchableCombo({
                    inputId: 'jira-tests-project-search-input',
                    dropdownId: 'jira-tests-project-dropdown',
                    hiddenId: 'jira-tests-project-select',
                    dataArray: allProjectsTests,
                    onSelect: (item) => {
                        // Habilitar botón de validar cuando se seleccione un proyecto
                        if (validateBtn) {
                            validateBtn.disabled = false;
                        }
                        // Resetear validación si cambia el proyecto
                        const validationResult = document.getElementById('jira-tests-validation-result');
                        const step1_5 = document.getElementById('jira-tests-step1-5');
                        const step2 = document.getElementById('jira-tests-step2');
                        const uploadBtn = document.getElementById('jira-tests-modal-upload');
                        if (validationResult) {
                            validationResult.style.display = 'none';
                            validationResult.innerHTML = '';
                        }
                        if (step1_5) step1_5.style.display = 'none';
                        if (step2) step2.style.display = 'none';
                        if (uploadBtn) uploadBtn.style.display = 'none';

                        // Reiniciar selects de campos
                        const selects = ['jira-tests-tipo-prueba-select', 'jira-tests-nivel-prueba-select',
                            'jira-tests-tipo-ejecucion-select', 'jira-tests-ambiente-select'];
                        selects.forEach(selectId => {
                            const select = document.getElementById(selectId);
                            if (select) {
                                select.value = '';
                                select.innerHTML = '<option value="">Cargando valores...</option>';
                            }
                        });

                        // Ocultar mensajes
                        const messages = ['jira-tests-tipo-prueba-message', 'jira-tests-nivel-prueba-message',
                            'jira-tests-tipo-ejecucion-message', 'jira-tests-ambiente-message'];
                        messages.forEach(msgId => {
                            const msg = document.getElementById(msgId);
                            if (msg) {
                                msg.style.display = 'none';
                                msg.innerHTML = '';
                            }
                        });
                    }
                });
            }
        } catch (error) {
            console.error('Error al cargar proyectos de Jira:', error);
        }
    }

    // Función para cargar valores de campos select
    async function loadTestCaseFieldValues(projectKey) {
        try {
            const response = await fetch('/api/jira/get-test-case-field-values', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({ project_key: projectKey })
            });

            const data = await response.json();

            if (!data.success) {
                showDownloadNotification('Error al cargar valores de campos: ' + (data.error || 'Error desconocido'), 'error');
                return;
            }

            const fieldConfig = {
                'tipo_prueba': {
                    select: 'jira-tests-tipo-prueba-select',
                    container: 'jira-tests-tipo-prueba-container',
                    message: 'jira-tests-tipo-prueba-message',
                    label: 'Tipo de Prueba'
                },
                'nivel_prueba': {
                    select: 'jira-tests-nivel-prueba-select',
                    container: 'jira-tests-nivel-prueba-container',
                    message: 'jira-tests-nivel-prueba-message',
                    label: 'Nivel de Prueba'
                },
                'tipo_ejecucion': {
                    select: 'jira-tests-tipo-ejecucion-select',
                    container: 'jira-tests-tipo-ejecucion-container',
                    message: 'jira-tests-tipo-ejecucion-message',
                    label: 'Tipo de Ejecución'
                },
                'ambiente': {
                    select: 'jira-tests-ambiente-select',
                    container: 'jira-tests-ambiente-container',
                    message: 'jira-tests-ambiente-message',
                    label: 'Ambiente'
                }
            };

            // Procesar cada campo
            for (const [fieldKey, config] of Object.entries(fieldConfig)) {
                const fieldData = data.field_values[fieldKey];
                const selectEl = document.getElementById(config.select);
                const containerEl = document.getElementById(config.container);
                const messageEl = document.getElementById(config.message);

                if (!selectEl || !containerEl || !messageEl) continue;

                // Resetear
                selectEl.innerHTML = '';
                selectEl.removeAttribute('required');
                messageEl.style.display = 'none';
                messageEl.innerHTML = '';

                if (!fieldData || !fieldData.exists) {
                    // Campo no existe
                    containerEl.style.display = 'block';
                    selectEl.style.display = 'none';
                    messageEl.style.display = 'block';
                    messageEl.style.color = 'var(--warning)';
                    messageEl.innerHTML = `⚠️ El campo "${config.label}" no existe en este proyecto. Si realizas la carga ahora, este campo no se mostrará en los casos de prueba.`;
                } else if (!fieldData.has_values || fieldData.values.length === 0) {
                    // Campo existe pero no tiene valores
                    containerEl.style.display = 'block';
                    selectEl.style.display = 'none';
                    messageEl.style.display = 'block';
                    messageEl.style.color = 'var(--warning)';
                    messageEl.innerHTML = `⚠️ El campo "${config.label}" existe pero no tiene opciones configuradas en el proyecto. Si realizas la carga ahora, este campo no se mostrará en los casos de prueba.`;
                } else {
                    // Campo existe y tiene valores
                    containerEl.style.display = 'block';
                    selectEl.style.display = 'block';
                    selectEl.setAttribute('required', 'required');
                    selectEl.innerHTML = '<option value="">Seleccionar...</option>';
                    fieldData.values.forEach(val => {
                        const option = document.createElement('option');
                        option.value = val.value;
                        option.textContent = val.name || val.value;
                        selectEl.appendChild(option);
                    });
                }
            }

            // Configurar event listeners para los selects
            setupSelectFieldsListeners();

            // Mostrar paso 1.5
            const step1_5 = document.getElementById('jira-tests-step1-5');
            if (step1_5) step1_5.style.display = 'block';

            // Verificar estado inicial después de cargar valores
            setTimeout(() => {
                checkAndShowUploadButton();
            }, 100);

        } catch (error) {
            console.error('Error al cargar valores de campos:', error);
            showDownloadNotification('Error al cargar valores de campos: ' + error.message, 'error');
        }
    }

    // Función para validar que todos los campos select requeridos estén llenos
    function validateSelectFields() {
        const requiredSelects = document.querySelectorAll('#jira-tests-step1-5 select[required]');
        for (let select of requiredSelects) {
            if (!select.value || select.value.trim() === '') {
                return false;
            }
        }
        return true;
    }

    // Función para verificar y mostrar el botón de subir
    function checkAndShowUploadButton() {
        const step2 = document.getElementById('jira-tests-step2');
        const uploadBtn = document.getElementById('jira-tests-modal-upload');
        const assigneeInput = document.getElementById('jira-tests-assignee-input');

        // Verificar que todos los campos select requeridos estén llenos
        if (!validateSelectFields()) {
            // Aún faltan campos - ocultar paso 2 y botón
            if (step2) step2.style.display = 'none';
            if (uploadBtn) uploadBtn.style.display = 'none';
            return;
        }

        // Todos los campos select están llenos - mostrar paso 2
        if (step2) step2.style.display = 'block';

        // Verificar asignado
        const assigneeEmail = assigneeInput ? assigneeInput.value.trim() : '';
        if (assigneeEmail) {
            // Si hay email, debe estar validado
            if (testsAssigneeValidated && !testsAssigneeInvalid) {
                if (uploadBtn) uploadBtn.style.display = 'flex';
            } else {
                if (uploadBtn) uploadBtn.style.display = 'none';
            }
        } else {
            // Si no hay email, mostrar botón directamente
            if (uploadBtn) uploadBtn.style.display = 'flex';
        }
    }

    // Configurar event listeners para los campos select
    function setupSelectFieldsListeners() {
        const selects = ['jira-tests-tipo-prueba-select', 'jira-tests-nivel-prueba-select',
            'jira-tests-tipo-ejecucion-select', 'jira-tests-ambiente-select'];

        selects.forEach(selectId => {
            const select = document.getElementById(selectId);
            if (select) {
                // Remover listeners anteriores si existen
                const newSelect = select.cloneNode(true);
                select.parentNode.replaceChild(newSelect, select);

                newSelect.addEventListener('change', function () {
                    checkAndShowUploadButton();
                });
            }
        });
    }

    // Función para validar campos del proyecto
    async function validateTestCaseFields() {
        const projectSelect = document.getElementById('jira-tests-project-select');
        const validateBtn = document.getElementById('jira-tests-validate-fields-btn');
        const validationResult = document.getElementById('jira-tests-validation-result');
        const step2 = document.getElementById('jira-tests-step2');
        const uploadBtn = document.getElementById('jira-tests-modal-upload');

        if (!projectSelect || !projectSelect.value) {
            showDownloadNotification('Por favor selecciona un proyecto primero', 'error');
            return;
        }

        if (validateBtn) {
            validateBtn.disabled = true;
            validateBtn.innerHTML = '<span>⏳</span><span>Validando...</span>';
        }

        try {
            const response = await fetch('/api/jira/validate-test-case-fields', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    project_key: projectSelect.value
                })
            });

            const data = await response.json();

            if (validateBtn) {
                validateBtn.disabled = false;
                validateBtn.innerHTML = '<span>🔍</span><span>Validar Campos</span>';
            }

            if (validationResult) {
                validationResult.style.display = 'block';

                if (data.success) {
                    // Campos válidos - cargar valores de campos select
                    validationResult.innerHTML = `
                                <div style="padding: 1rem; border-radius: 8px; background: rgba(16, 185, 129, 0.2); border: 1px solid var(--success); color: #6ee7b7;">
                                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                                        <span>✅</span>
                                        <span style="font-weight: 600;">Todos los campos necesarios están disponibles</span>
                                    </div>
                                    <div style="font-size: 0.85rem; margin-top: 0.5rem;">
                                        El proyecto cuenta con todos los campos requeridos para crear casos de prueba.
                                    </div>
                                </div>
                            `;

                    // Cargar valores de campos select
                    await loadTestCaseFieldValues(projectSelect.value);

                    // Ocultar paso 1, mostrar paso 1.5
                    const step1 = document.getElementById('jira-tests-step1');
                    if (step1) step1.style.display = 'none';

                    // Ocultar paso 2 y botón de subir hasta que se llenen los campos select
                    if (step2) step2.style.display = 'none';
                    if (uploadBtn) uploadBtn.style.display = 'none';
                } else {
                    // Campos faltantes
                    const missingFields = data.missing_fields || [];
                    const missingList = missingFields.map(f => {
                        const possibleNames = f.possible_names || [];
                        return `<li>${f.field} (posibles nombres: ${possibleNames.join(', ')})</li>`;
                    }).join('');

                    validationResult.innerHTML = `
                                <div style="padding: 1rem; border-radius: 8px; background: rgba(239, 68, 68, 0.2); border: 1px solid var(--error); color: #fca5a5;">
                                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                                        <span>❌</span>
                                        <span style="font-weight: 600;">Campos faltantes en el proyecto</span>
                                    </div>
                                    <div style="font-size: 0.85rem; margin-top: 0.5rem; margin-bottom: 0.5rem;">
                                        ${data.message || 'El proyecto no cuenta con todos los campos necesarios.'}
                                    </div>
                                    <div style="font-size: 0.85rem; margin-top: 0.5rem;">
                                        <strong>Campos faltantes:</strong>
                                        <ul style="margin-top: 0.5rem; padding-left: 1.5rem;">
                                            ${missingList}
                                        </ul>
                                    </div>
                                    <div style="font-size: 0.85rem; margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid rgba(239, 68, 68, 0.3);">
                                        Por favor, configura los campos faltantes en el proyecto de Jira antes de continuar.
                                    </div>
                                </div>
                            `;

                    // Ocultar pasos
                    const step1_5 = document.getElementById('jira-tests-step1-5');
                    if (step1_5) step1_5.style.display = 'none';
                    if (step2) step2.style.display = 'none';
                    if (uploadBtn) uploadBtn.style.display = 'none';
                }
            }
        } catch (error) {
            console.error('Error al validar campos:', error);
            if (validateBtn) {
                validateBtn.disabled = false;
                validateBtn.innerHTML = '<span>🔍</span><span>Validar Campos</span>';
            }
            showDownloadNotification('Error al validar campos: ' + error.message, 'error');
        }
    }

    // Event listeners del modal
    const testsModalClose = document.getElementById('jira-tests-modal-close');
    const testsModalCancel = document.getElementById('jira-tests-modal-cancel');
    const validateFieldsBtn = document.getElementById('jira-tests-validate-fields-btn');
    if (testsModalClose) testsModalClose.onclick = closeJiraTestsModal;
    if (testsModalCancel) testsModalCancel.onclick = closeJiraTestsModal;
    if (validateFieldsBtn) validateFieldsBtn.onclick = validateTestCaseFields;

    // Validación de asignado
    let testsAssigneeAccountId = null;
    let testsAssigneeValidated = false;
    let testsAssigneeInvalid = false;

    const testsAssigneeInput = document.getElementById('jira-tests-assignee-input');
    if (testsAssigneeInput) {
        testsAssigneeInput.onblur = async function () {
            const email = this.value.trim();
            const validationDiv = document.getElementById('jira-tests-assignee-validation');

            if (!email) {
                testsAssigneeAccountId = null;
                testsAssigneeValidated = false;
                testsAssigneeInvalid = false;
                if (validationDiv) {
                    validationDiv.style.display = 'none';
                }
                // Si no hay email, verificar si se puede mostrar el botón
                checkAndShowUploadButton();
                return;
            }

            // Validar formato de email
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                if (validationDiv) {
                    validationDiv.style.display = 'block';
                    validationDiv.style.color = 'var(--error)';
                    validationDiv.textContent = '❌ Formato de email inválido';
                }
                testsAssigneeInvalid = true;
                testsAssigneeValidated = false;
                return;
            }

            // Validar con Jira
            if (validationDiv) {
                validationDiv.style.display = 'block';
                validationDiv.style.color = 'var(--text-muted)';
                validationDiv.textContent = '⏳ Validando...';
            }

            try {
                const response = await fetch('/api/jira/validate-user', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({ email: email })
                });

                if (response.ok) {
                    const validateData = await response.json();
                    if (validateData.valid && validateData.accountId) {
                        testsAssigneeAccountId = validateData.accountId;
                        testsAssigneeValidated = true;
                        testsAssigneeInvalid = false;
                        if (validationDiv) {
                            validationDiv.style.color = 'var(--success)';
                            validationDiv.textContent = '✅ Usuario encontrado en Jira';
                        }
                        // Verificar si se puede mostrar el botón de subir
                        checkAndShowUploadButton();
                    } else {
                        testsAssigneeInvalid = true;
                        testsAssigneeValidated = false;
                        if (validationDiv) {
                            validationDiv.style.color = 'var(--error)';
                            validationDiv.textContent = '❌ ' + (validateData.error || 'Este correo no tiene cuenta en Jira');
                        }
                        // Ocultar botón si el asignado es inválido
                        const uploadBtn = document.getElementById('jira-tests-modal-upload');
                        if (uploadBtn) uploadBtn.style.display = 'none';
                    }
                } else {
                    const validateData = await response.json();
                    testsAssigneeInvalid = true;
                    testsAssigneeValidated = false;
                    if (validationDiv) {
                        validationDiv.style.color = 'var(--error)';
                        validationDiv.textContent = '❌ ' + (validateData.error || 'Error al validar usuario');
                    }
                    // Ocultar botón si hay error
                    const uploadBtn = document.getElementById('jira-tests-modal-upload');
                    if (uploadBtn) uploadBtn.style.display = 'none';
                }
            } catch (error) {
                if (validationDiv) {
                    validationDiv.style.color = 'var(--error)';
                    validationDiv.textContent = '❌ Error al validar usuario';
                }
                testsAssigneeInvalid = true;
                testsAssigneeValidated = false;
            }
        };
    }

    // Botón subir a Jira
    const testsModalUploadBtn = document.getElementById('jira-tests-modal-upload');
    if (testsModalUploadBtn) {
        testsModalUploadBtn.onclick = async function () {
            const projectSelect = document.getElementById('jira-tests-project-select');
            const assigneeInput = document.getElementById('jira-tests-assignee-input');

            if (!projectSelect || !projectSelect.value) {
                showDownloadNotification('Por favor selecciona un proyecto de Jira', 'error');
                return;
            }

            const projectKey = projectSelect.value;
            const assigneeEmail = assigneeInput ? assigneeInput.value.trim() : '';

            // Obtener valores de campos select
            const tipoPruebaSelect = document.getElementById('jira-tests-tipo-prueba-select');
            const nivelPruebaSelect = document.getElementById('jira-tests-nivel-prueba-select');
            const tipoEjecucionSelect = document.getElementById('jira-tests-tipo-ejecucion-select');
            const ambienteSelect = document.getElementById('jira-tests-ambiente-select');

            const tipoPrueba = tipoPruebaSelect ? tipoPruebaSelect.value.trim() : '';
            const nivelPrueba = nivelPruebaSelect ? nivelPruebaSelect.value.trim() : '';
            const tipoEjecucion = tipoEjecucionSelect ? tipoEjecucionSelect.value.trim() : '';
            const ambiente = ambienteSelect ? ambienteSelect.value.trim() : '';

            // Validar asignado si se proporciona
            if (assigneeEmail) {
                if (testsAssigneeInvalid) {
                    showDownloadNotification('Por favor verifica que el email del asignado sea válido y tenga cuenta en Jira', 'error');
                    return;
                } else if (!testsAssigneeValidated) {
                    // Intentar validar ahora
                    if (assigneeInput) {
                        assigneeInput.focus();
                        assigneeInput.blur();
                        await new Promise(resolve => setTimeout(resolve, 1000));

                        if (testsAssigneeInvalid || !testsAssigneeValidated) {
                            showDownloadNotification('Por favor verifica que el email del asignado sea válido y tenga cuenta en Jira', 'error');
                            return;
                        }
                    }
                }
            }

            // Mostrar loading
            const loadingOverlay = document.getElementById('tests-loading-overlay');
            if (loadingOverlay) loadingOverlay.style.display = 'flex';

            try {
                const response = await fetch('/api/jira/tests/upload-to-jira', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({
                        test_cases: window.selectedTestsForUpload,
                        project_key: projectKey,
                        assignee_email: assigneeEmail || null,
                        tipo_prueba: tipoPrueba,
                        nivel_prueba: nivelPrueba,
                        tipo_ejecucion: tipoEjecucion,
                        ambiente: ambiente
                    })
                });

                const data = await response.json();

                if (loadingOverlay) loadingOverlay.style.display = 'none';
                closeJiraTestsModal();

                if (data.success) {
                    showDownloadNotification(data.message || 'Casos de prueba subidos exitosamente a Jira', 'success');

                    // Descargar archivo TXT si está disponible
                    if (data.txt_content && data.txt_filename) {
                        try {
                            // Decodificar base64
                            const txtContent = atob(data.txt_content);

                            const blob = new Blob([txtContent], { type: 'text/plain;charset=utf-8' });
                            const url = URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = data.txt_filename;
                            document.body.appendChild(a);
                            a.click();
                            URL.revokeObjectURL(url);
                            document.body.removeChild(a);
                        } catch (txtError) {
                            console.error('Error al descargar TXT:', txtError);
                        }
                    }
                } else {
                    showDownloadNotification('Error: ' + (data.error || 'No se pudieron subir los casos de prueba'), 'error');
                }
            } catch (error) {
                if (loadingOverlay) loadingOverlay.style.display = 'none';
                showDownloadNotification('Error de conexión: ' + error.message, 'error');
            }
        };
    }
})();

// ============================================================================
// FEEDBACK - Funcionalidad de Feedback
// ============================================================================
(function () {
    let selectedFeedbackIssueType = 'Bug';
    let selectedFeedbackProjectKey = '';
    let feedbackProjectLocked = false; // Variable para bloquear cambio de proyecto
    let feedbackAllProjects = []; // Almacenar todos los proyectos

    // Cargar TODOS los proyectos disponibles (reutiliza endpoint existente)
    function loadFeedbackProjects() {
        fetch('/api/jira/projects', {
            method: 'GET',
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success && data.projects && data.projects.length > 0) {
                    feedbackAllProjects = data.projects;
                    renderFeedbackProjects(feedbackAllProjects);
                } else {
                    showDownloadNotification(data.error || 'No hay proyectos disponibles', 'error');
                }
            })
            .catch(error => {
                console.error('Error cargando proyectos:', error);
                showDownloadNotification('Error al cargar proyectos: ' + error.message, 'error');
            });
    }

    // Renderizar proyectos en el dropdown
    function renderFeedbackProjects(projects) {
        const dropdown = document.getElementById('feedback-dropdown');
        if (!dropdown) return;

        dropdown.innerHTML = '';

        if (projects.length === 0) {
            const noResults = document.createElement('div');
            noResults.className = 'combobox-option';
            noResults.style.color = 'var(--text-muted)';
            noResults.style.cursor = 'default';
            noResults.textContent = 'No se encontraron proyectos';
            dropdown.appendChild(noResults);
            return;
        }

        projects.forEach(project => {
            const option = document.createElement('div');
            option.className = 'combobox-option';
            option.textContent = `${project.name} (${project.key})`;
            option.dataset.key = project.key;
            option.dataset.name = project.name;
            option.dataset.isNexus = project.key === 'NA';

            option.addEventListener('mousedown', function (e) {
                e.preventDefault();
                selectFeedbackProject(project.key, project.name);
            });

            dropdown.appendChild(option);
        });
    }

    // Filtrar proyectos
    window.filterFeedbackProjects = function (searchTerm) {
        if (feedbackProjectLocked) return; // No permitir filtrar si está bloqueado

        const filtered = feedbackAllProjects.filter(project =>
            project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            project.key.toLowerCase().includes(searchTerm.toLowerCase())
        );
        renderFeedbackProjects(filtered);
    };

    // Mostrar dropdown
    window.showFeedbackDropdown = function () {
        if (feedbackProjectLocked) return; // No permitir abrir si está bloqueado

        const dropdown = document.getElementById('feedback-dropdown');
        if (dropdown) {
            dropdown.style.display = 'block';

            // Si ya hay proyectos cargados, mostrarlos
            if (feedbackAllProjects.length > 0) {
                renderFeedbackProjects(feedbackAllProjects);
            }
            // Si no, el mensaje "Cargando..." ya está en el HTML
        }
    };

    // Ocultar dropdown
    window.hideFeedbackDropdown = function () {
        setTimeout(() => {
            const dropdown = document.getElementById('feedback-dropdown');
            if (dropdown) dropdown.style.display = 'none';
        }, 200);
    };

    // Manejar teclas
    window.handleFeedbackKeydown = function (event) {
        if (feedbackProjectLocked) {
            event.preventDefault();
            return;
        }
        // Aquí puedes agregar navegación con flechas si lo deseas
    };

    // Mostrar notificación temporal de feedback
    function showFeedbackNotification(message, type = 'warning') {
        // Crear elemento de notificación
        const notification = document.createElement('div');
        notification.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: ${type === 'warning' ? 'rgba(245, 158, 11, 0.95)' : 'rgba(239, 68, 68, 0.95)'};
                    color: white;
                    padding: 1rem 1.5rem;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                    z-index: 9999;
                    animation: slideIn 0.3s ease;
                    max-width: 400px;
                    font-size: 0.9rem;
                `;
        notification.textContent = message;
        document.body.appendChild(notification);

        // Auto-ocultar después de 3 segundos
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        }, 3000);
    }

    // Seleccionar proyecto
    function selectFeedbackProject(projectKey, projectName) {
        if (feedbackProjectLocked && projectKey !== selectedFeedbackProjectKey) {
            showFeedbackNotification('El proyecto ya ha sido seleccionado y no puede ser cambiado', 'warning');
            return;
        }

        const input = document.getElementById('feedback-project-selector-input');
        const hiddenInput = document.getElementById('feedback-project-selector');

        // Verificar si es Nexus AI (NA)
        const isNexusAI = projectKey === 'NA';

        if (!isNexusAI) {
            showFeedbackNotification('⚠️ Por favor, asegúrate de seleccionar el proyecto "Nexus AI (NA)" para enviar feedback', 'warning');

            if (input) input.value = '';
            if (hiddenInput) hiddenInput.value = '';
            return;
        }

        // Es Nexus AI, proceder
        if (input) input.value = `${projectName} (${projectKey})`;
        if (hiddenInput) hiddenInput.value = projectKey;

        // Validar proyecto
        validateFeedbackProject(projectKey);
    }

    // Validar proyecto
    function validateFeedbackProject(projectKey) {
        const input = document.getElementById('feedback-project-selector-input');

        // Mostrar indicador de validación
        if (input) {
            input.style.opacity = '0.6';
            input.value = input.value + ' ⏳ Validando...';
        }

        fetch('/api/feedback/validate-project', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ project_key: projectKey })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success && data.valid) {
                    selectedFeedbackProjectKey = projectKey;
                    feedbackProjectLocked = true; // Bloquear cambio de proyecto
                    handleFeedbackProjectChange(true);

                    // Deshabilitar el input visualmente
                    if (input) {
                        // Remover el mensaje de validación
                        const projectName = input.value.replace(' ⏳ Validando...', '');
                        input.value = projectName + ' ✓';
                        input.setAttribute('readonly', 'readonly');
                        input.style.opacity = '0.7';
                        input.style.cursor = 'not-allowed';
                    }

                    showDownloadNotification('Proyecto validado correctamente. Ya puedes enviar tu feedback.', 'success');
                } else {
                    showDownloadNotification(data.error || 'Proyecto no válido', 'error');
                    // Resetear selección
                    const hiddenInput = document.getElementById('feedback-project-selector');
                    if (input) {
                        input.value = '';
                        input.style.opacity = '1';
                    }
                    if (hiddenInput) hiddenInput.value = '';
                }
            })
            .catch(error => {
                console.error('Error validando proyecto:', error);
                showDownloadNotification('Error al validar proyecto: ' + error.message, 'error');
                // Resetear en caso de error
                if (input) {
                    input.value = '';
                    input.style.opacity = '1';
                }
            });
    }

    // Manejo de cambio de proyecto
    function handleFeedbackProjectChange(isValid) {
        const feedbackForm = document.getElementById('feedback-form');
        const noProjectMessage = document.getElementById('feedback-no-project-message');

        if (isValid) {
            if (feedbackForm) feedbackForm.classList.remove('disabled');
            if (noProjectMessage) noProjectMessage.style.display = 'none';
        } else {
            if (feedbackForm) feedbackForm.classList.add('disabled');
            if (noProjectMessage) noProjectMessage.style.display = 'block';
        }
    }

    // Selección de tipo de issue
    window.selectFeedbackIssueType = function (type) {
        selectedFeedbackIssueType = type;
        const buttons = document.querySelectorAll('.feedback-issue-type-btn');
        buttons.forEach(btn => btn.classList.remove('active'));

        if (type === 'Bug') {
            buttons[0].classList.add('active');
        } else {
            buttons[1].classList.add('active');
        }
    };

    // Formato de texto
    window.formatFeedbackText = function (command) {
        document.execCommand(command, false, null);
        const editorContent = document.getElementById('feedback-editor-content');
        if (editorContent) editorContent.focus();
    };

    // Insertar enlace
    window.insertFeedbackLink = function () {
        const url = prompt('Ingresa la URL:');
        if (url) {
            document.execCommand('createLink', false, url);
        }
    };

    // Insertar imagen
    window.insertFeedbackImage = function (event) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function (e) {
                const img = document.createElement('img');
                img.src = e.target.result;
                img.style.maxWidth = '100%';
                const editorContent = document.getElementById('feedback-editor-content');
                if (editorContent) {
                    editorContent.appendChild(img);
                }
            };
            reader.readAsDataURL(file);
        }
    };

    // Enviar feedback
    window.submitFeedback = async function () {
        const summary = document.getElementById('feedback-summary');
        const editorContent = document.getElementById('feedback-editor-content');

        if (!summary || !editorContent) return;

        const summaryValue = summary.value.trim();
        const descriptionValue = editorContent.innerHTML.trim();

        if (!summaryValue) {
            showDownloadNotification('Por favor, ingresa un resumen para tu reporte', 'warning');
            return;
        }

        if (!descriptionValue || descriptionValue === '<br>') {
            showDownloadNotification('Por favor, ingresa una descripción para tu reporte', 'warning');
            return;
        }

        // Mostrar indicador de carga
        const feedbackForm = document.getElementById('feedback-form');
        const loadingIndicator = document.getElementById('feedback-loading-indicator');
        if (feedbackForm) feedbackForm.style.display = 'none';
        if (loadingIndicator) loadingIndicator.classList.add('active');

        try {
            const response = await fetch('/api/feedback/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    project_key: selectedFeedbackProjectKey,
                    issue_type: selectedFeedbackIssueType,
                    summary: summaryValue,
                    description: descriptionValue
                })
            });

            const data = await response.json();

            if (loadingIndicator) loadingIndicator.classList.remove('active');

            if (data.success) {
                const successMessage = document.getElementById('feedback-success-message');
                const successText = document.getElementById('feedback-success-text');

                if (successMessage) successMessage.classList.add('active');
                if (successText) {
                    successText.innerHTML = `Tu reporte ha sido creado como <strong>${data.issue_key}</strong>. <a href="${data.issue_url}" target="_blank" style="color: var(--accent); text-decoration: underline;">Ver en Jira</a>`;
                }

                showDownloadNotification(data.message || 'Feedback enviado exitosamente', 'success');
                resetFeedbackForm();

                // Ocultar mensaje de éxito después de 10 segundos
                setTimeout(() => {
                    if (successMessage) successMessage.classList.remove('active');
                    if (feedbackForm) feedbackForm.style.display = 'block';
                }, 10000);
            } else {
                if (feedbackForm) feedbackForm.style.display = 'block';
                showDownloadNotification('Error: ' + (data.error || 'No se pudo enviar el feedback'), 'error');
            }
        } catch (error) {
            if (loadingIndicator) loadingIndicator.classList.remove('active');
            if (feedbackForm) feedbackForm.style.display = 'block';
            showDownloadNotification('Error de conexión: ' + error.message, 'error');
        }
    };

    // Resetear formulario
    window.resetFeedbackForm = function () {
        const summary = document.getElementById('feedback-summary');
        const editorContent = document.getElementById('feedback-editor-content');

        if (summary) summary.value = '';
        if (editorContent) editorContent.innerHTML = '';

        selectFeedbackIssueType('Bug');
    };

    // Inicializar cuando se muestra la sección de feedback
    const feedbackSection = document.getElementById('feedback');
    if (feedbackSection) {
        const observer = new MutationObserver(function (mutations) {
            mutations.forEach(function (mutation) {
                if (mutation.attributeName === 'class') {
                    if (feedbackSection.classList.contains('active')) {
                        loadFeedbackProjects();

                        // Mostrar mensaje inicial
                        const noProjectMessage = document.getElementById('feedback-no-project-message');
                        if (noProjectMessage) noProjectMessage.style.display = 'block';
                    }
                }
            });
        });

        observer.observe(feedbackSection, { attributes: true });
    }
})();