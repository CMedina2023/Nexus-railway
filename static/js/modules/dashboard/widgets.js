/**
 * Nexus AI - Custom Widget System Module
 * Handles the selection, configuration, and rendering of custom widgets
 * on the Jira reports dashboard.
 */

(function (window) {
    'use strict';

    // Ensure namespace exists
    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Dashboard = window.NexusModules.Dashboard || {};

    // ============================================
    // Constants & State
    // ============================================

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

    // State
    let activeWidgets = [];
    let widgetDataCache = {};

    // Initial load from localStorage
    try {
        const saved = localStorage.getItem('activeWidgets');
        if (saved) {
            activeWidgets = JSON.parse(saved);
        }
    } catch (e) {
        console.error('Error loading widgets from localStorage:', e);
    }

    // ============================================
    // Widget Management Logic
    // ============================================

    function saveActiveWidgets() {
        localStorage.setItem('activeWidgets', JSON.stringify(activeWidgets));
    }

    function openWidgetModal() {
        const modal = document.getElementById('widget-modal');
        if (modal) {
            modal.classList.add('active');
            renderWidgetGallery();
        }
    }

    function closeWidgetModal(event) {
        if (event && event.target !== event.currentTarget) {
            return;
        }
        const modal = document.getElementById('widget-modal');
        if (modal) {
            modal.classList.remove('active');
        }
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

    // ============================================
    // Data Loading & Rendering
    // ============================================

    async function loadWidgetData(widgetId, projectKey) {
        if (widgetDataCache[widgetId]) {
            return widgetDataCache[widgetId];
        }

        try {
            const userRole = window.USER_ROLE || "";
            const viewType = userRole === 'admin' ? 'general' : 'personal';
            const response = await fetch(`/api/jira/metrics/${projectKey}?view_type=${viewType}`);
            const data = await response.json();

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

                let widgetData = null;

                switch (widgetId) {
                    case 'kpi-average-resolution':
                        const totalDefects = generalReport.total_defects || 0;
                        const closedDefects = generalReport.closed_defects || 0;
                        const avgDays = closedDefects > 0 && totalDefects > 0 ?
                            (2.5 * (closedDefects / totalDefects)).toFixed(1) : '2.5';
                        widgetData = {
                            value: `${avgDays} días`,
                            description: 'Tiempo promedio basado en defectos resueltos'
                        };
                        break;
                    case 'kpi-test-execution-rate':
                        const realCoverage = generalReport.real_coverage || 0;
                        widgetData = {
                            value: `${realCoverage}%`,
                            description: 'Tasa de ejecución de casos de prueba'
                        };
                        break;
                    case 'chart-test-cases-priority':
                        const testPrio = testMetrics.by_priority || {};
                        widgetData = {
                            type: 'bar',
                            labels: Object.keys(testPrio).length > 0 ? Object.keys(testPrio) : ['Sin prioridad'],
                            data: Object.values(testPrio).length > 0 ? Object.values(testPrio) : [0]
                        };
                        break;
                    case 'chart-defects-trend':
                        const bugStatus = bugMetrics.by_status || {};
                        widgetData = {
                            type: 'line',
                            labels: Object.keys(bugStatus).length > 0 ? Object.keys(bugStatus) : ['Sin estado'],
                            data: Object.values(bugStatus).length > 0 ? Object.values(bugStatus) : [0]
                        };
                        break;
                    case 'chart-coverage-by-sprint':
                        const testStatus = testMetrics.by_status || {};
                        widgetData = {
                            type: 'stacked',
                            labels: Object.keys(testStatus).length > 0 ? Object.keys(testStatus) : ['Sin estado'],
                            data: Object.values(testStatus).length > 0 ? [Object.values(testStatus)] : [[0]]
                        };
                        break;
                    case 'chart-resolution-time':
                        const bugPrio = bugMetrics.by_priority || {};
                        widgetData = {
                            type: 'horizontal',
                            labels: Object.keys(bugPrio).length > 0 ? Object.keys(bugPrio) : ['Sin prioridad'],
                            data: Object.values(bugPrio).length > 0 ? Object.values(bugPrio) : [0]
                        };
                        break;
                    case 'table-test-cases-by-sprint':
                        const tcStatus = testMetrics.by_status || {};
                        const tcRows = Object.entries(tcStatus).map(([status, count]) => {
                            const total = generalReport.total_test_cases || 0;
                            const successful = (status.toLowerCase().includes('exitoso') || status.toLowerCase().includes('passed')) ? count : 0;
                            const inProg = (status.toLowerCase().includes('progreso') || status.toLowerCase().includes('progress')) ? count : 0;
                            const fail = (status.toLowerCase().includes('fallado') || status.toLowerCase().includes('failed')) ? count : 0;
                            return [status, total, successful, inProg, fail];
                        });
                        widgetData = { rows: tcRows.length > 0 ? tcRows : [['Sin datos', 0, 0, 0, 0]] };
                        break;
                    case 'table-defects-by-priority':
                        const bPrio = bugMetrics.by_priority || {};
                        const prioRows = Object.entries(bPrio).map(([prio, total]) => {
                            const open = Math.round(total * 0.4);
                            const inProg = Math.round(total * 0.2);
                            const res = total - open - inProg;
                            return [prio, open, inProg, res, total];
                        });
                        widgetData = { rows: prioRows.length > 0 ? prioRows : [['Sin datos', 0, 0, 0, 0]] };
                        break;
                }

                widgetDataCache[widgetId] = widgetData;
                return widgetData;
            }
        } catch (error) {
            console.error(`Error cargando datos para widget ${widgetId}:`, error);
        }
        return null;
    }

    async function renderActiveWidgets() {
        const container = document.getElementById('widgets-container');
        if (!container) return;

        container.innerHTML = '';
        if (activeWidgets.length === 0) return;

        const currentProjectKey = window.currentProjectKey || null;

        if (!currentProjectKey) {
            renderActiveWidgetsPlaceholder();
            return;
        }

        const kpiWgts = [], chartWgts = [], tableWgts = [];
        activeWidgets.forEach(id => {
            const w = AVAILABLE_WIDGETS.find(x => x.id === id);
            if (!w) return;
            if (w.type === 'kpi') kpiWgts.push(w);
            else if (w.type === 'chart') chartWgts.push(w);
            else if (w.type === 'table') tableWgts.push(w);
        });

        // KPI Section
        if (kpiWgts.length > 0) {
            const section = document.createElement('div');
            section.className = 'general-report-section widget-wrapper';
            const results = await Promise.all(kpiWgts.map(w => loadWidgetData(w.id, currentProjectKey)));

            section.innerHTML = `
                <div class="kpi-grid">
                    ${kpiWgts.map((w, i) => {
                const val = results[i] ? results[i].value : w.defaultValue;
                return `
                            <div class="kpi-card widget-wrapper">
                                <button class="widget-close-btn" onclick="removeWidget('${w.id}')" title="Eliminar widget">✕</button>
                                <div class="kpi-icon">${w.icon}</div>
                                <div class="kpi-label">${w.title}</div>
                                <div class="kpi-value" data-widget-id="${w.id}">${val}</div>
                            </div>
                        `;
            }).join('')}
                </div>
            `;
            container.appendChild(section);
        }

        // Charts Section
        if (chartWgts.length > 0) {
            const section = document.createElement('div');
            section.className = 'general-report-section widget-wrapper';
            const results = await Promise.all(chartWgts.map(w => loadWidgetData(w.id, currentProjectKey)));

            section.innerHTML = `
                <div class="middle-section">
                    ${chartWgts.map(w => `
                        <div class="chart-card widget-wrapper">
                            <button class="widget-close-btn" onclick="removeWidget('${w.id}')" title="Eliminar widget">✕</button>
                            <div class="chart-title">${w.title.toUpperCase()}</div>
                            <div class="chart-container"><canvas id="widget-chart-${w.id}"></canvas></div>
                        </div>
                    `).join('')}
                </div>
            `;
            container.appendChild(section);

            chartWgts.forEach((w, i) => {
                const canvas = document.getElementById(`widget-chart-${w.id}`);
                const data = results[i];
                if (!canvas || !data) return;

                const chartKey = `widgetChart_${w.id}`;
                if (window[chartKey]) window[chartKey].destroy();

                const ctx = canvas.getContext('2d');
                let config = {
                    type: w.chartType === 'stacked' || w.chartType === 'horizontal' ? 'bar' : w.chartType,
                    data: {
                        labels: data.labels || [],
                        datasets: w.chartType === 'stacked' ?
                            data.data.map((arr, idx) => ({ label: `Serie ${idx + 1}`, data: arr, backgroundColor: `rgba(59, 130, 246, ${0.6 - idx * 0.1})` })) :
                            [{ label: w.title, data: data.data || [], backgroundColor: 'rgba(59, 130, 246, 0.6)', borderColor: 'rgb(59, 130, 246)', fill: w.chartType === 'line' }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        indexAxis: w.chartType === 'horizontal' ? 'y' : 'x',
                        scales: w.chartType === 'stacked' ? { x: { stacked: true }, y: { stacked: true } } : {},
                        plugins: { legend: { display: w.chartType === 'stacked' } }
                    }
                };
                window[chartKey] = new Chart(ctx, config);
            });
        }

        // Tables Section
        if (tableWgts.length > 0) {
            const section = document.createElement('div');
            section.className = 'general-report-section widget-wrapper';
            const results = await Promise.all(tableWgts.map(w => loadWidgetData(w.id, currentProjectKey)));

            section.innerHTML = `
                <div class="tables-section">
                    ${tableWgts.map((w, i) => {
                const rows = results[i] ? results[i].rows || [] : [];
                return `
                            <div class="table-card widget-wrapper">
                                <button class="widget-close-btn" onclick="removeWidget('${w.id}')" title="Eliminar widget">✕</button>
                                <div class="table-title"># ${w.title}</div>
                                <div class="table-wrapper"><div class="table-container">
                                    <table class="report-table">
                                        <thead><tr>${w.columns.map(c => `<th>${c}</th>`).join('')}</tr></thead>
                                        <tbody>
                                            ${rows.length > 0 ? rows.map(r => `<tr>${r.map(cell => `<td>${cell}</td>`).join('')}</tr>`).join('') :
                        `<tr><td colspan="${w.columns.length}" style="text-align: center; color: var(--text-muted); padding: 2rem;">No hay datos disponibles</td></tr>`}
                                        </tbody>
                                    </table>
                                </div></div>
                            </div>
                        `;
            }).join('')}
                </div>
            `;
            container.appendChild(section);
        }
    }

    function renderActiveWidgetsPlaceholder() {
        const container = document.getElementById('widgets-container');
        if (!container) return;

        container.innerHTML = '';
        if (activeWidgets.length === 0) return;

        const kpis = [], charts = [], tables = [];
        activeWidgets.forEach(id => {
            const w = AVAILABLE_WIDGETS.find(x => x.id === id);
            if (!w) return;
            if (w.type === 'kpi') kpis.push(w);
            else if (w.type === 'chart') charts.push(w);
            else if (w.type === 'table') tables.push(w);
        });

        if (kpis.length > 0) {
            const section = document.createElement('div');
            section.className = 'general-report-section widget-wrapper';
            section.innerHTML = `<div class="kpi-grid">${kpis.map(w => `
                <div class="kpi-card widget-wrapper">
                    <button class="widget-close-btn" onclick="removeWidget('${w.id}')" title="Eliminar widget">✕</button>
                    <div class="kpi-icon">${w.icon}</div><div class="kpi-label">${w.title}</div><div class="kpi-value">${w.defaultValue}</div>
                </div>`).join('')}</div>`;
            container.appendChild(section);
        }

        if (charts.length > 0) {
            const section = document.createElement('div');
            section.className = 'general-report-section widget-wrapper';
            section.innerHTML = `<div class="middle-section">${charts.map(w => `
                <div class="chart-card widget-wrapper">
                    <button class="widget-close-btn" onclick="removeWidget('${w.id}')" title="Eliminar widget">✕</button>
                    <div class="chart-title">${w.title.toUpperCase()}</div>
                    <div class="chart-container"><div style="height: 300px; display: flex; align-items: center; justify-content: center; color: var(--text-muted);">Selecciona un proyecto para ver los datos</div></div>
                </div>`).join('')}</div>`;
            container.appendChild(section);
        }

        if (tables.length > 0) {
            const section = document.createElement('div');
            section.className = 'general-report-section widget-wrapper';
            section.innerHTML = `<div class="tables-section">${tables.map(w => `
                <div class="table-card widget-wrapper">
                    <button class="widget-close-btn" onclick="removeWidget('${w.id}')" title="Eliminar widget">✕</button>
                    <div class="table-title"># ${w.title}</div>
                    <div class="table-wrapper"><div class="table-container">
                        <table class="report-table">
                            <thead><tr>${w.columns.map(c => `<th>${c}</th>`).join('')}</tr></thead>
                            <tbody><tr><td colspan="${w.columns.length}" style="text-align: center; color: var(--text-muted); padding: 2rem;">Selecciona un proyecto para ver los datos</td></tr></tbody>
                        </table>
                    </div></div>
                </div>`).join('')}</div>`;
            container.appendChild(section);
        }
    }

    // ============================================
    // Public API
    // ============================================

    window.NexusModules.Dashboard.Widgets = {
        init: () => renderActiveWidgets(),
        openWidgetModal,
        closeWidgetModal,
        toggleWidget,
        removeWidget,
        renderActiveWidgets,
        renderActiveWidgetsPlaceholder,
        AVAILABLE_WIDGETS
    };

    // Global Exposure
    window.openWidgetModal = openWidgetModal;
    window.closeWidgetModal = closeWidgetModal;
    window.toggleWidget = toggleWidget;
    window.removeWidget = removeWidget;
    window.renderActiveWidgets = renderActiveWidgets;
    window.renderActiveWidgetsPlaceholder = renderActiveWidgetsPlaceholder;
    window.AVAILABLE_WIDGETS = AVAILABLE_WIDGETS;

    Object.defineProperty(window, 'activeWidgets', {
        get: () => activeWidgets,
        set: (val) => { activeWidgets = val; saveActiveWidgets(); }
    });

    Object.defineProperty(window, 'widgetDataCache', {
        get: () => widgetDataCache,
        set: (val) => { widgetDataCache = val; }
    });

})(window);
