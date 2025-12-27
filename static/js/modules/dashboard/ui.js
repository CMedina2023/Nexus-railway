/**
 * Nexus AI - Dashboard UI Module
 * Handles UI interactions, rendering, and metric loading for the dashboard.
 */

(function (window) {
    'use strict';

    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Dashboard = window.NexusModules.Dashboard || {};

    // State
    let activePeriod = 'total'; // Default active period

    // ============================================
    // Loading & Updating Logic
    // ============================================

    // Load Dashboard Metrics - Actualiza los contadores en la vista principal del dashboard
    async function loadDashboardMetrics() {
        try {
            // Métricas del Generador H/CP
            const generatorMetrics = await window.NexusModules.Dashboard.getMetrics();
            const generatorStoriesEl = document.getElementById('generator-stories');
            const generatorTestCasesEl = document.getElementById('generator-testcases');

            if (generatorStoriesEl) {
                generatorStoriesEl.textContent = generatorMetrics.stories || 0;
            }
            if (generatorTestCasesEl) {
                generatorTestCasesEl.textContent = generatorMetrics.testCases || 0;
            }

            // Métricas de Reportes Jira
            const jiraMetrics = await window.NexusModules.Dashboard.getJiraMetrics();
            const reportsCountEl = document.getElementById('reports-count');
            const reportsLastEl = document.getElementById('reports-last');

            if (reportsCountEl) {
                reportsCountEl.textContent = jiraMetrics.reports.count || 0;
            }
            if (reportsLastEl) {
                reportsLastEl.textContent = jiraMetrics.reports.lastDate || '-';
            }

            // Métricas de Carga Masiva
            const uploadCountEl = document.getElementById('upload-count');
            const uploadItemsEl = document.getElementById('upload-items');

            if (uploadCountEl) {
                uploadCountEl.textContent = jiraMetrics.uploads.count || 0;
            }
            if (uploadItemsEl) {
                uploadItemsEl.textContent = jiraMetrics.uploads.itemsCount || 0;
            }
        } catch (error) {
            console.error('Error al cargar métricas del dashboard:', error);
        }
    }

    // Carga las métricas completas (Generador) y actualiza gráficos
    async function loadMetrics() {
        const metrics = await window.NexusModules.Dashboard.getMetrics();

        // Update counters
        const storiesCountEl = document.getElementById('stories-count');
        const testCasesCountEl = document.getElementById('test-cases-count');
        const totalCountEl = document.getElementById('total-count');

        if (storiesCountEl) storiesCountEl.textContent = metrics.stories;
        if (testCasesCountEl) testCasesCountEl.textContent = metrics.testCases;
        if (totalCountEl) totalCountEl.textContent = metrics.stories + metrics.testCases;

        // Calculate area distribution
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
        if (window.NexusModules.Dashboard.updateAreaChart) {
            window.NexusModules.Dashboard.updateAreaChart(areaDistribution);
        }

        // Update history
        const historyList = document.getElementById('history-list');
        if (!historyList) return;

        if (!metrics.history || metrics.history.length === 0) {
            historyList.innerHTML = `
                <li class="history-item" style="text-align: center; padding: 2rem; color: var(--text-muted);">
                    No hay historial aún. Las generaciones aparecerán aquí.
                </li>
            `;
            return;
        }

        historyList.innerHTML = metrics.history.map(item => {
            const date = new Date(item.date);
            const formattedDate = date.toLocaleDateString('es-ES', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });

            const icon = item.type === 'stories' ? '📝' : '🧪';
            const typeName = item.type === 'stories' ? 'Historias de Usuario' : 'Casos de Prueba';
            const iconClass = item.type === 'stories' ? 'story' : 'test';

            // Mostrar el área correctamente
            let area = item.area;
            if (!area || area === 'UNKNOWN' || area === 'No especificada' || area === 'Sin Área') {
                area = 'Sin Área';
            }

            return `
                <li class="history-item">
                    <div class="history-info">
                        <div class="history-icon ${iconClass}">${icon}</div>
                        <div class="history-details">
                            <div class="history-type">${typeName}</div>
                            <div class="history-meta">
                                <span class="history-area">🏢 ${area}</span>
                                <span class="history-date">${formattedDate}</span>
                            </div>
                        </div>
                    </div>
                    <div class="history-count">+${item.count}</div>
                </li>
            `;
        }).join('');
    }

    // Load Jira Metrics (Reportes y Cargas)
    async function loadJiraMetrics() {
        const jiraMetrics = await window.NexusModules.Dashboard.getJiraMetrics();

        // ========== MÉTRICAS DE REPORTES ==========
        const reportsTotalEl = document.getElementById('jira-reports-total');
        const reportsProjectsCountEl = document.getElementById('jira-reports-projects-count');
        const reportsWeeklyEl = document.getElementById('jira-reports-weekly');

        if (reportsTotalEl) {
            reportsTotalEl.textContent = jiraMetrics.reports.count || 0;
        }

        // Contar proyectos únicos
        const reportsProjects = Object.keys(jiraMetrics.reports.byProject || {});
        if (reportsProjectsCountEl) {
            reportsProjectsCountEl.textContent = reportsProjects.length;
        }

        // Calcular reportes en últimos 7 días
        const sevenDaysAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
        const recentReports = (jiraMetrics.reports.history || []).filter(h =>
            new Date(h.timestamp || h.date).getTime() > sevenDaysAgo
        ).length;
        if (reportsWeeklyEl) {
            reportsWeeklyEl.textContent = recentReports;
        }

        // Renderizar gráficos de reportes
        if (window.NexusModules.Dashboard.updateReportsCharts) {
            window.NexusModules.Dashboard.updateReportsCharts(jiraMetrics.reports);
        }

        // Renderizar métricas por proyecto - Reportes
        renderJiraMetricsByProject('reports', jiraMetrics.reports.byProject);

        // Renderizar historial de reportes
        renderReportsHistory(jiraMetrics.reports.history || []);

        // ========== MÉTRICAS DE CARGAS ==========
        const uploadsTotalEl = document.getElementById('jira-uploads-total');
        const uploadsItemsEl = document.getElementById('jira-uploads-items');
        const uploadsProjectsCountEl = document.getElementById('jira-uploads-projects-count');
        const uploadsAvgEl = document.getElementById('jira-uploads-avg');

        if (uploadsTotalEl) {
            uploadsTotalEl.textContent = jiraMetrics.uploads.count || 0;
        }
        if (uploadsItemsEl) {
            uploadsItemsEl.textContent = jiraMetrics.uploads.itemsCount || 0;
        }

        // Contar proyectos únicos con cargas
        const uploadsProjects = Object.keys(jiraMetrics.uploads.byProject || {});
        if (uploadsProjectsCountEl) {
            uploadsProjectsCountEl.textContent = uploadsProjects.length;
        }

        // Calcular promedio de items por carga
        const avgItems = jiraMetrics.uploads.count > 0
            ? Math.round((jiraMetrics.uploads.itemsCount || 0) / jiraMetrics.uploads.count)
            : 0;
        if (uploadsAvgEl) {
            uploadsAvgEl.textContent = avgItems;
        }

        // Renderizar gráficos de cargas
        if (window.NexusModules.Dashboard.updateUploadsCharts) {
            window.NexusModules.Dashboard.updateUploadsCharts(jiraMetrics.uploads);
        }

        // Renderizar métricas por proyecto - Cargas
        renderJiraMetricsByProject('uploads', jiraMetrics.uploads.byProject);

        // Renderizar historial de cargas
        renderUploadsHistory(jiraMetrics.uploads.history || []);
    }

    // Load All Metrics (Generator + Jira)
    async function loadAllMetrics() {
        // Cargar métricas del generador
        await loadMetrics();

        // Cargar métricas de Jira
        await loadJiraMetrics();

        // Asegurar que el filtro activo se muestre
        const activeFilter = document.querySelector('.metric-filter-btn.active');
        if (activeFilter) {
            const filterType = activeFilter.getAttribute('data-filter');
            showMetricsSection(filterType);
        }
    }

    // Esta función ya no guarda en localStorage, el backend maneja el guardado
    // Se mantiene por compatibilidad
    async function updateMetrics(type, count, area = null) {
        // Optimistic UI update
        try {
            if (activePeriod === 'total') {
                if (type === 'stories') {
                    const el = document.getElementById('stories-count');
                    if (el) {
                        const current = parseInt(el.textContent.replace(/,/g, '')) || 0;
                        el.textContent = (current + count).toLocaleString();
                    }
                } else if (type === 'test_cases') {
                    const el = document.getElementById('test-cases-count');
                    if (el) {
                        const current = parseInt(el.textContent.replace(/,/g, '')) || 0;
                        el.textContent = (current + count).toLocaleString();
                    }
                }
            }
        } catch (e) {
            console.warn('Error updating metric UI optimistically:', e);
        }

        // El backend guarda automáticamente cuando se generan historias/casos de prueba
        // Solo necesitamos recargar las métricas del backend
        if (window.NexusModules.Dashboard.clearMetricsCache) {
            window.NexusModules.Dashboard.clearMetricsCache(); // Invalidar cache
        }
        await loadMetrics();
    }

    // ============================================
    // Rendering Logic
    // ============================================

    function renderReportsHistory(history) {
        const historyList = document.getElementById('jira-reports-history-list');
        if (!historyList) return;

        if (history.length === 0) {
            historyList.innerHTML = `
                <li class="history-item" style="text-align: center; padding: 2rem; color: var(--text-muted);">
                    No hay historial aún. Los reportes aparecerán aquí.
                </li>
            `;
            return;
        }

        historyList.innerHTML = history.map(item => {
            const date = new Date(item.timestamp || item.date);
            const formattedDate = date.toLocaleDateString('es-ES', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });

            return `
                <li class="history-item">
                    <div class="history-info">
                        <div class="history-icon reports"><i class="fas fa-file-alt"></i></div>
                        <div class="history-details">
                            <div class="history-type">Reporte Generado</div>
                            <div class="history-meta">
                                <span class="history-area">📊 ${item.projectName || item.projectKey || 'Proyecto'}</span>
                                <span class="history-date">${formattedDate}</span>
                            </div>
                        </div>
                    </div>
                </li>
            `;
        }).join('');
    }

    function renderUploadsHistory(history) {
        const historyList = document.getElementById('jira-uploads-history-list');
        if (!historyList) return;

        if (history.length === 0) {
            historyList.innerHTML = `
                <li class="history-item" style="text-align: center; padding: 2rem; color: var(--text-muted);">
                    No hay historial aún. Las cargas aparecerán aquí.
                </li>
            `;
            return;
        }

        historyList.innerHTML = history.map(item => {
            const date = new Date(item.timestamp || item.date);
            const formattedDate = date.toLocaleDateString('es-ES', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });

            const types = Object.keys(item.issueTypesDistribution || {});
            const typesSummary = types.length > 0
                ? types.map(t => `${t} (${item.issueTypesDistribution[t]})`).join(', ')
                : 'Sin tipo especificado';

            return `
                <li class="history-item">
                    <div class="history-info">
                        <div class="history-icon uploads"><i class="fas fa-upload"></i></div>
                        <div class="history-details">
                            <div class="history-type">Carga Masiva</div>
                            <div class="history-meta">
                                <span class="history-area">📊 ${item.projectName || item.projectKey || 'Proyecto'}</span>
                                <span class="history-date">${formattedDate}</span>
                            </div>
                            <div class="history-extra" style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem;">
                                ${item.itemsCount || 0} items • Tipos: ${typesSummary}
                            </div>
                        </div>
                    </div>
                    <div class="history-count">+${item.itemsCount || 0}</div>
                </li>
            `;
        }).join('');
    }

    function renderJiraMetricsByProject(type, byProject) {
        const containerId = type === 'reports' ? 'jira-reports-by-project' : 'jira-uploads-by-project';
        const container = document.getElementById(containerId);
        if (!container) return;

        const projects = Object.keys(byProject);

        if (projects.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-inbox"></i>
                    <p>No hay ${type === 'reports' ? 'reportes' : 'cargas'} realizadas aún</p>
                </div>
            `;
            return;
        }

        container.innerHTML = projects.map(projectKey => {
            const project = byProject[projectKey];
            if (type === 'reports') {
                return `
                    <div class="jira-project-metric-item">
                        <div class="jira-project-metric-header">
                            <div class="jira-project-metric-name">${project.name || projectKey}</div>
                        </div>
                        <div class="jira-project-metric-stats">
                            <div class="jira-project-stat">
                                <span class="jira-project-stat-label">Reportes Generados</span>
                                <span class="jira-project-stat-value">${project.count}</span>
                            </div>
                            <div class="jira-project-stat">
                                <span class="jira-project-stat-label">Último Reporte</span>
                                <span class="jira-project-stat-value">${project.lastDate || '-'}</span>
                            </div>
                        </div>
                    </div>
                `;
            } else {
                // Calcular promedio de items por carga para este proyecto
                const avgItems = project.count > 0
                    ? Math.round((project.itemsCount || 0) / project.count)
                    : 0;

                // Mostrar distribución de tipos de issue
                const typesDistribution = project.issueTypesDistribution || {};
                const typesList = Object.keys(typesDistribution).length > 0
                    ? Object.entries(typesDistribution)
                        .map(([type, count]) => `${type}: ${count}`)
                        .join(', ')
                    : 'N/A';

                return `
                    <div class="jira-project-metric-item">
                        <div class="jira-project-metric-header">
                            <div class="jira-project-metric-name">${project.name || projectKey}</div>
                        </div>
                        <div class="jira-project-metric-stats">
                            <div class="jira-project-stat">
                                <span class="jira-project-stat-label">Cargas Realizadas</span>
                                <span class="jira-project-stat-value">${project.count}</span>
                            </div>
                            <div class="jira-project-stat">
                                <span class="jira-project-stat-label">Items Cargados</span>
                                <span class="jira-project-stat-value">${project.itemsCount || 0}</span>
                            </div>
                            <div class="jira-project-stat">
                                <span class="jira-project-stat-label">Promedio por Carga</span>
                                <span class="jira-project-stat-value">${avgItems}</span>
                            </div>
                            <div class="jira-project-stat">
                                <span class="jira-project-stat-label">Última Carga</span>
                                <span class="jira-project-stat-value">${project.lastDate || '-'}</span>
                            </div>
                            ${Object.keys(typesDistribution).length > 0 ? `
                            <div class="jira-project-stat" style="grid-column: 1 / -1; margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid var(--border);">
                                <span class="jira-project-stat-label">Distribución por Tipo</span>
                                <span class="jira-project-stat-value" style="font-size: 0.85rem; text-align: right;">${typesList}</span>
                            </div>
                            ` : ''}
                        </div>
                    </div>
                `;
            }
        }).join('');
    }

    // ============================================
    // UI Interactions
    // ============================================

    function showMetricsSection(filterType) {
        activePeriod = filterType; // Update active period state

        // Ocultar todas las secciones
        document.querySelectorAll('.metrics-section').forEach(section => {
            section.classList.remove('active');
        });

        // Mostrar la sección correspondiente
        const sectionId = `metrics-${filterType}`;
        const section = document.getElementById(sectionId);
        if (section) {
            section.classList.add('active');
        }

        // Actualizar botones de filtro
        document.querySelectorAll('.metric-filter-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        const activeBtn = document.querySelector(`[data-filter="${filterType}"]`);
        if (activeBtn) {
            activeBtn.classList.add('active');
        }
    }

    function clearJiraReport() {
        const metricsContent = document.getElementById('metrics-content');
        const welcomeCard = document.querySelector('.jira-welcome-card');
        const projectSelector = document.getElementById('project-selector');
        const widgetsContainer = document.getElementById('widgets-container');

        if (metricsContent) {
            metricsContent.style.display = 'none';
        }

        if (welcomeCard) {
            welcomeCard.style.display = 'block';
        }

        const projectInput = document.getElementById('project-selector-input');
        const projectHidden = document.getElementById('project-selector');
        if (projectInput) {
            projectInput.value = '';
        }
        if (projectHidden) {
            projectHidden.value = '';
        }

        if (widgetsContainer) {
            widgetsContainer.innerHTML = '';
        }

        // Ocultar botones
        const downloadButton = document.getElementById('download-button');
        const customizeButton = document.getElementById('customize-button');

        if (downloadButton) {
            downloadButton.classList.remove('visible');
        }

        if (customizeButton) {
            customizeButton.style.display = 'none';
        }
    }

    async function refreshMetrics() {
        if (window.NexusModules.Dashboard.clearMetricsCache) {
            window.NexusModules.Dashboard.clearMetricsCache();
        }
        await loadAllMetrics();
    }

    async function resetMetrics() {
        // Verificar rol antes de proceder (seguridad adicional en frontend)
        if (window.USER_ROLE !== 'admin') {
            alert('❌ No tienes permisos para realizar esta acción. Solo el administrador puede reiniciar métricas.');
            return;
        }

        if (!confirm('⚠️ ¿Estás seguro de que quieres reiniciar TODAS las métricas?\\n\\nEsta acción eliminará:\\n- Todas las historias de usuario generadas\\n- Todos los casos de prueba generados\\n- Todos los reportes de Jira\\n- Todas las cargas masivas\\n\\nEsta acción NO se puede deshacer.')) {
            return;
        }

        try {
            // Obtener el token CSRF del meta tag o cookie
            const csrfToken = window.getCsrfToken ? window.getCsrfToken() :
                (document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '');

            const response = await fetch('/api/dashboard/clear-metrics', {
                method: 'DELETE',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Error al limpiar métricas');
            }

            const data = await response.json();

            // Mostrar mensaje de éxito con detalles
            alert(`✅ Métricas limpiadas exitosamente:\n\n` +
                `- ${data.deleted.stories} historias eliminadas\n` +
                `- ${data.deleted.test_cases} casos de prueba eliminados\n` +
                `- ${data.deleted.reports} reportes eliminados\n` +
                `- ${data.deleted.bulk_uploads} cargas masivas eliminadas`);

            // Invalidar cache y recargar
            if (window.NexusModules.Dashboard.clearMetricsCache) {
                window.NexusModules.Dashboard.clearMetricsCache();
            }
            await loadAllMetrics();

        } catch (error) {
            console.error('Error al reiniciar métricas:', error);
            alert(`❌ Error al reiniciar métricas: ${error.message}`);
        }
    }

    // Export internal functions
    window.NexusModules.Dashboard.loadDashboardMetrics = loadDashboardMetrics;
    window.NexusModules.Dashboard.loadMetrics = loadMetrics;
    window.NexusModules.Dashboard.loadAllMetrics = loadAllMetrics;
    window.NexusModules.Dashboard.loadJiraMetrics = loadJiraMetrics;
    window.NexusModules.Dashboard.updateMetrics = updateMetrics;
    window.NexusModules.Dashboard.showMetricsSection = showMetricsSection;
    window.NexusModules.Dashboard.resetMetrics = resetMetrics;
    window.NexusModules.Dashboard.clearJiraReport = clearJiraReport;
    window.NexusModules.Dashboard.refreshMetrics = refreshMetrics;

})(window);
