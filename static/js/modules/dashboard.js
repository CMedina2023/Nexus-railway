/**
 * Nexus AI - Dashboard & Metrics Module
 * Handles all logic related to dashboard metrics, charts, and history rendering.
 */

(function (window) {
    'use strict';

    // Ensure namespace exists
    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Dashboard = window.NexusModules.Dashboard || {};

    // ============================================
    // State & Variables
    // ============================================

    // Variable global para cachear las métricas
    let cachedMetrics = null;

    // Chart instances
    let areaChartInstance = null;
    let reportsByProjectChart = null;
    let reportsTrendChart = null;
    let uploadsByTypeChart = null;
    let uploadsByProjectChart = null;
    let uploadsTrendChart = null;

    // ============================================
    // Data Fetching
    // ============================================

    /**
     * Obtiene todas las métricas del dashboard desde el backend
     * @returns {Promise<Object>} Objeto con generator_metrics y jira_metrics
     */
    async function fetchDashboardMetrics() {
        if (cachedMetrics) {
            return cachedMetrics;
        }

        try {
            const csrfToken = window.getCsrfToken ? window.getCsrfToken() :
                (document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '');

            const response = await fetch('/api/dashboard/metrics', {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'X-CSRFToken': csrfToken
                }
            });

            if (!response.ok) {
                throw new Error('Error al obtener métricas del dashboard');
            }

            const data = await response.json();
            if (data.success) {
                cachedMetrics = data;
                return data;
            } else {
                throw new Error(data.error || 'Error al obtener métricas');
            }
        } catch (error) {
            console.error('Error al obtener métricas:', error);
            // Retornar estructura vacía en caso de error
            return {
                generator_metrics: {
                    stories: 0,
                    testCases: 0,
                    history: []
                },
                jira_metrics: {
                    reports: {
                        count: 0,
                        byProject: {},
                        lastDate: null
                    },
                    uploads: {
                        count: 0,
                        itemsCount: 0,
                        byProject: {},
                        issueTypesDistribution: {}
                    }
                }
            };
        }
    }

    /**
     * Obtiene métricas del generador (historias y casos de prueba)
     * @returns {Promise<Object>} Métricas del generador
     */
    async function getMetrics() {
        const data = await fetchDashboardMetrics();
        return data.generator_metrics || {
            stories: 0,
            testCases: 0,
            history: []
        };
    }

    /**
     * Obtiene métricas de Jira (reportes y cargas masivas)
     * @returns {Promise<Object>} Métricas de Jira
     */
    async function getJiraMetrics() {
        const data = await fetchDashboardMetrics();
        return data.jira_metrics || {
            reports: {
                count: 0,
                byProject: {},
                lastDate: null
            },
            uploads: {
                count: 0,
                itemsCount: 0,
                byProject: {},
                issueTypesDistribution: {}
            }
        };
    }

    // ============================================
    // Loading & Updating Logic
    // ============================================

    // Load Dashboard Metrics - Actualiza los contadores en la vista principal del dashboard
    async function loadDashboardMetrics() {
        try {
            // Métricas del Generador H/CP
            const generatorMetrics = await getMetrics();
            const generatorStoriesEl = document.getElementById('generator-stories');
            const generatorTestCasesEl = document.getElementById('generator-testcases');

            if (generatorStoriesEl) {
                generatorStoriesEl.textContent = generatorMetrics.stories || 0;
            }
            if (generatorTestCasesEl) {
                generatorTestCasesEl.textContent = generatorMetrics.testCases || 0;
            }

            // Métricas de Reportes Jira
            const jiraMetrics = await getJiraMetrics();
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
        const metrics = await getMetrics();

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
        updateAreaChart(areaDistribution);

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

    // Load Jira Metrics (Reportes y Cargas)
    async function loadJiraMetrics() {
        const jiraMetrics = await getJiraMetrics();

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
        updateReportsCharts(jiraMetrics.reports);

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
        updateUploadsCharts(jiraMetrics.uploads);

        // Renderizar métricas por proyecto - Cargas
        renderJiraMetricsByProject('uploads', jiraMetrics.uploads.byProject);

        // Renderizar historial de cargas
        renderUploadsHistory(jiraMetrics.uploads.history || []);
    }

    // Esta función ya no guarda en localStorage, el backend maneja el guardado
    // Se mantiene por compatibilidad
    async function updateMetrics(type, count, area = null) {
        // El backend guarda automáticamente cuando se generan historias/casos de prueba
        // Solo necesitamos recargar las métricas del backend
        cachedMetrics = null; // Invalidar cache
        await loadMetrics();
    }

    // ============================================
    // Chart Updates
    // ============================================

    function updateAreaChart(areaDistribution) {
        const canvas = document.getElementById('area-distribution-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');

        // Destroy existing chart if it exists
        if (areaChartInstance) {
            areaChartInstance.destroy();
        }

        const areas = Object.keys(areaDistribution);
        const counts = Object.values(areaDistribution);

        if (areas.length === 0) {
            // Show empty state
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = 'var(--text-muted)';
            ctx.font = '16px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('No hay datos disponibles', canvas.width / 2, canvas.height / 2);
            return;
        }

        // Define colors for each area
        const areaColors = {
            'Finanzas': '#3b82f6',
            'Recursos Humanos': '#10b981',
            'Tesoreria': '#f59e0b',
            'TI': '#8b5cf6',
            'Sin Área': '#6b7280',
            'Sin Proyecto': '#6b7280',
            'No especificada': '#6b7280',
            'UNKNOWN': '#6b7280'
        };

        const backgroundColors = areas.map(area => areaColors[area] || '#6b7280');

        areaChartInstance = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: areas,
                datasets: [{
                    data: counts,
                    backgroundColor: backgroundColors,
                    borderColor: 'var(--bg)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: 'var(--text-primary)',
                            padding: 15,
                            font: {
                                size: 14
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    function updateReportsCharts(reportsData) {
        // Gráfico de distribución por proyecto
        const byProjectCanvas = document.getElementById('reports-by-project-chart');
        if (byProjectCanvas) {
            const ctx = byProjectCanvas.getContext('2d');
            if (reportsByProjectChart) {
                reportsByProjectChart.destroy();
            }

            const projects = Object.keys(reportsData.byProject || {});
            const counts = projects.map(key => reportsData.byProject[key].count);
            const labels = projects.map(key => reportsData.byProject[key].name || key);

            if (projects.length === 0) {
                ctx.clearRect(0, 0, byProjectCanvas.width, byProjectCanvas.height);
                ctx.fillStyle = 'var(--text-muted)';
                ctx.font = '16px Arial';
                ctx.textAlign = 'center';
                ctx.fillText('No hay datos disponibles', byProjectCanvas.width / 2, byProjectCanvas.height / 2);
                return;
            }

            reportsByProjectChart = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: labels,
                    datasets: [{
                        data: counts,
                        backgroundColor: [
                            '#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444',
                            '#06b6d4', '#ec4899', '#84cc16', '#f97316', '#6366f1'
                        ],
                        borderColor: 'var(--primary-bg)',
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: 'var(--text-primary)',
                                padding: 15,
                                font: { size: 14 }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function (context) {
                                    const label = context.label || '';
                                    const value = context.parsed || 0;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return `${label}: ${value} reportes (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            });
        }

        // Gráfico de tendencia temporal
        const trendCanvas = document.getElementById('reports-trend-chart');
        if (trendCanvas) {
            const ctx = trendCanvas.getContext('2d');
            if (reportsTrendChart) {
                reportsTrendChart.destroy();
            }

            const history = reportsData.history || [];
            if (history.length === 0) {
                ctx.clearRect(0, 0, trendCanvas.width, trendCanvas.height);
                ctx.fillStyle = 'var(--text-muted)';
                ctx.font = '16px Arial';
                ctx.textAlign = 'center';
                ctx.fillText('No hay datos disponibles', trendCanvas.width / 2, trendCanvas.height / 2);
                return;
            }

            // Agrupar por semana
            const weeklyData = {};
            history.forEach(item => {
                const date = new Date(item.timestamp || item.date);
                const weekKey = `${date.getFullYear()}-W${Math.ceil(date.getDate() / 7)}`;
                weeklyData[weekKey] = (weeklyData[weekKey] || 0) + 1;
            });

            const weeks = Object.keys(weeklyData).sort();
            const weekCounts = weeks.map(w => weeklyData[w]);

            reportsTrendChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: weeks,
                    datasets: [{
                        label: 'Reportes Generados',
                        data: weekCounts,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            display: true,
                            labels: {
                                color: 'var(--text-primary)'
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                color: 'var(--text-secondary)',
                                stepSize: 1
                            },
                            grid: {
                                color: 'var(--border)'
                            }
                        },
                        x: {
                            ticks: {
                                color: 'var(--text-secondary)'
                            },
                            grid: {
                                color: 'var(--border)'
                            }
                        }
                    }
                }
            });
        }
    }

    function updateUploadsCharts(uploadsData) {
        // Gráfico de distribución por tipo de issue
        const byTypeCanvas = document.getElementById('uploads-by-type-chart');
        if (byTypeCanvas) {
            const ctx = byTypeCanvas.getContext('2d');
            if (uploadsByTypeChart) {
                uploadsByTypeChart.destroy();
            }

            const typesDistribution = uploadsData.issueTypesDistribution || {};
            const types = Object.keys(typesDistribution);
            const counts = types.map(t => typesDistribution[t]);

            if (types.length === 0) {
                ctx.clearRect(0, 0, byTypeCanvas.width, byTypeCanvas.height);
                ctx.fillStyle = 'var(--text-muted)';
                ctx.font = '16px Arial';
                ctx.textAlign = 'center';
                ctx.fillText('No hay datos disponibles', byTypeCanvas.width / 2, byTypeCanvas.height / 2);
                return;
            }

            // Paleta extendida de colores para asegurar unicidad
            const extendedPalette = [
                '#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6',
                '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1',
                '#14b8a6', '#d946ef', '#eab308', '#a855f7', '#22c55e',
                '#64748b', '#78716c', '#0ea5e9', '#f43f5e', '#a3e635'
            ];

            const typeColors = {
                'Bug': '#ef4444',
                'Story': '#3b82f6',
                'Test case': '#10b981',
                'Task': '#f59e0b',
                'Epic': '#8b5cf6'
            };

            // Función para obtener color único
            const getColor = (type, index) => {
                if (typeColors[type]) return typeColors[type];
                // Si no está predefinido, usar de la paleta extendida cíclicamente
                return extendedPalette[index % extendedPalette.length];
            };

            uploadsByTypeChart = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: types,
                    datasets: [{
                        data: counts,
                        backgroundColor: types.map((t, index) => getColor(t, index)),
                        borderColor: 'var(--primary-bg)',
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: 'var(--text-primary)',
                                padding: 15,
                                font: { size: 14 }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function (context) {
                                    const label = context.label || '';
                                    const value = context.parsed || 0;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return `${label}: ${value} items (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            });
        }

        // Gráfico de items por proyecto
        const byProjectCanvas = document.getElementById('uploads-by-project-chart');
        if (byProjectCanvas) {
            const ctx = byProjectCanvas.getContext('2d');
            if (uploadsByProjectChart) {
                uploadsByProjectChart.destroy();
            }

            const projects = Object.keys(uploadsData.byProject || {});
            const itemsCounts = projects.map(key => uploadsData.byProject[key].itemsCount || 0);
            const labels = projects.map(key => uploadsData.byProject[key].name || key);

            if (projects.length === 0) {
                ctx.clearRect(0, 0, byProjectCanvas.width, byProjectCanvas.height);
                ctx.fillStyle = 'var(--text-muted)';
                ctx.font = '16px Arial';
                ctx.textAlign = 'center';
                ctx.fillText('No hay datos disponibles', byProjectCanvas.width / 2, byProjectCanvas.height / 2);
                return;
            }

            uploadsByProjectChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Items Cargados',
                        data: itemsCounts,
                        backgroundColor: '#3b82f6',
                        borderColor: '#2563eb',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                color: 'var(--text-secondary)',
                                stepSize: 1
                            },
                            grid: {
                                color: 'var(--border)'
                            }
                        },
                        x: {
                            ticks: {
                                color: 'var(--text-secondary)'
                            },
                            grid: {
                                color: 'var(--border)'
                            }
                        }
                    }
                }
            });
        }

        // Gráfico de tendencia temporal
        const trendCanvas = document.getElementById('uploads-trend-chart');
        if (trendCanvas) {
            const ctx = trendCanvas.getContext('2d');
            if (uploadsTrendChart) {
                uploadsTrendChart.destroy();
            }

            const history = uploadsData.history || [];
            if (history.length === 0) {
                ctx.clearRect(0, 0, trendCanvas.width, trendCanvas.height);
                ctx.fillStyle = 'var(--text-muted)';
                ctx.font = '16px Arial';
                ctx.textAlign = 'center';
                ctx.fillText('No hay datos disponibles', trendCanvas.width / 2, trendCanvas.height / 2);
                return;
            }

            // Agrupar por semana
            const weeklyData = {};
            history.forEach(item => {
                const date = new Date(item.timestamp || item.date);
                const weekKey = `${date.getFullYear()}-W${Math.ceil(date.getDate() / 7)}`;
                weeklyData[weekKey] = (weeklyData[weekKey] || 0) + (item.itemsCount || 0);
            });

            const weeks = Object.keys(weeklyData).sort();
            const weekCounts = weeks.map(w => weeklyData[w]);

            uploadsTrendChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: weeks,
                    datasets: [{
                        label: 'Items Cargados',
                        data: weekCounts,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            display: true,
                            labels: {
                                color: 'var(--text-primary)'
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                color: 'var(--text-secondary)',
                                stepSize: 1
                            },
                            grid: {
                                color: 'var(--border)'
                            }
                        },
                        x: {
                            ticks: {
                                color: 'var(--text-secondary)'
                            },
                            grid: {
                                color: 'var(--border)'
                            }
                        }
                    }
                }
            });
        }
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
        cachedMetrics = null;
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
            cachedMetrics = null;
            await loadAllMetrics();

        } catch (error) {
            console.error('Error al reiniciar métricas:', error);
            alert(`❌ Error al reiniciar métricas: ${error.message}`);
        }
    }

    // ============================================
    // Public API
    // ============================================

    window.NexusModules.Dashboard = {
        fetchDashboardMetrics,
        getMetrics,
        getJiraMetrics,
        loadDashboardMetrics,
        loadMetrics,
        loadAllMetrics,
        loadJiraMetrics,
        updateMetrics,
        showMetricsSection,
        resetMetrics,
        clearJiraReport,
        refreshMetrics
    };

    // Backward Compatibility aliases (to be removed in future)
    window.fetchDashboardMetrics = fetchDashboardMetrics;
    window.getMetrics = getMetrics;
    window.getJiraMetrics = getJiraMetrics;
    window.loadDashboardMetrics = loadDashboardMetrics;
    window.loadMetrics = loadMetrics;
    window.loadAllMetrics = loadAllMetrics;
    window.loadJiraMetrics = loadJiraMetrics;
    window.updateMetrics = updateMetrics;
    window.showMetricsSection = showMetricsSection;
    window.resetMetrics = resetMetrics;
    window.clearJiraReport = clearJiraReport;

})(window);
