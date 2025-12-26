/**
 * Nexus AI - Jira Reports Download Module
 * Handles the generation and download of Jira reports in PDF and Excel formats.
 */

(function (window) {
    'use strict';

    // Ensure namespace exists
    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Jira = window.NexusModules.Jira || {};

    /**
     * Toggle download dropdown visibility
     */
    function toggleDownloadDropdown(event) {
        if (event) {
            event.stopPropagation();
        }
        const dropdown = document.getElementById('download-dropdown');
        if (dropdown) {
            dropdown.classList.toggle('active');
        }
    }

    /**
     * Close download dropdown when clicking outside
     */
    document.addEventListener('click', (e) => {
        const dropdown = document.getElementById('download-dropdown');
        const button = e.target.closest('.download-button');
        if (!button && !e.target.closest('.download-dropdown')) {
            if (dropdown) {
                dropdown.classList.remove('active');
            }
        }
    });

    /**
     * Download report as PDF
     */
    async function downloadPDF() {
        // We use window properties to access state from other modules
        const projectKey = document.getElementById('project-selector')?.value || window.currentProjectKey || '';

        if (!projectKey) {
            alert('Por favor, selecciona un proyecto primero');
            return;
        }

        const dropdown = document.getElementById('download-dropdown');
        if (dropdown) {
            dropdown.classList.remove('active');
        }

        // Mostrar notificación de inicio inmediatamente
        if (typeof window.showDownloadNotification === 'function') {
            window.showDownloadNotification('Procesando archivo...', 'loading');
        } else {
            console.log('Procesando archivo...');
        }

        try {
            // Convertir gráficos Chart.js a imágenes base64
            const chartImages = {};

            // Gráfico de Test Cases
            const testCasesCanvas = document.getElementById('gr-test-cases-chart');
            if (testCasesCanvas && window.grTestCasesChart) {
                chartImages['test_cases'] = testCasesCanvas.toDataURL('image/png');
            }

            // Gráfico de Bugs
            const bugsCanvas = document.getElementById('gr-bugs-severity-chart');
            if (bugsCanvas && window.grBugsSeverityChart) {
                chartImages['bugs_severity'] = bugsCanvas.toDataURL('image/png');
            }

            // Capturar gráficos de widgets personalizados
            const widgetChartImages = {};
            const activeWidgets = window.activeWidgets || [];
            const availableWidgets = window.AVAILABLE_WIDGETS || [];

            activeWidgets.forEach(widgetId => {
                const widget = availableWidgets.find(w => w.id === widgetId);
                if (widget && widget.type === 'chart') {
                    const canvas = document.getElementById(`widget-chart-${widgetId}`);
                    if (canvas && window[`widgetChart_${widgetId}`]) {
                        widgetChartImages[widgetId] = canvas.toDataURL('image/png');
                    }
                }
            });

            // Obtener datos de widgets personalizados
            const widgetData = {};
            const widgetDataCache = window.widgetDataCache || {};

            for (const widgetId of activeWidgets) {
                const widget = availableWidgets.find(w => w.id === widgetId);
                if (!widget) continue;

                if (widget.type === 'table') {
                    const data = widgetDataCache[widgetId];
                    if (data && data.rows) {
                        widgetData[widgetId] = {
                            type: 'table',
                            title: widget.title,
                            columns: widget.columns,
                            rows: data.rows
                        };
                    }
                } else if (widget.type === 'kpi') {
                    const data = widgetDataCache[widgetId];
                    if (data) {
                        widgetData[widgetId] = {
                            type: 'kpi',
                            title: widget.title,
                            icon: widget.icon,
                            value: data.value || widget.defaultValue
                        };
                    }
                } else if (widget.type === 'chart') {
                    widgetData[widgetId] = {
                        type: 'chart',
                        title: widget.title,
                        chartType: widget.chartType
                    };
                }
            }

            // Filtros activos (del módulo Reports)
            const filters = {}; // El backend ya filtra, pero se mantiene la estructura

            // Obtener datos de tablas desde paginación global
            const tableData = {
                test_cases_by_person: [],
                defects_by_person: []
            };

            if (window.testCasesPagination && window.testCasesPagination.data) {
                tableData.test_cases_by_person = window.testCasesPagination.data.map(({ person, stats }) => ({
                    person: person,
                    exitoso: stats.exitoso || 0,
                    en_progreso: stats.en_progreso || 0,
                    fallado: stats.fallado || 0,
                    total: stats.total || 0
                }));
            }

            if (window.defectsPagination && window.defectsPagination.data) {
                tableData.defects_by_person = window.defectsPagination.data.map(defect => ({
                    key: defect.key || '-',
                    assignee: defect.assignee || 'Sin asignar',
                    status: defect.status || '-',
                    summary: defect.summary || '-',
                    severity: defect.severity || '-'
                }));
            }

            // Llamar al backend
            const response = await fetch('/api/jira/download-report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.getCsrfToken()
                },
                body: JSON.stringify({
                    project_key: projectKey,
                    format: 'pdf',
                    filters: filters,
                    chart_images: chartImages,
                    table_data: tableData,
                    general_report: window.currentGeneralReport || {},
                    active_widgets: activeWidgets,
                    widget_chart_images: widgetChartImages,
                    widget_data: widgetData
                })
            });

            const contentType = response.headers.get('content-type') || '';
            if (!response.ok || contentType.includes('application/json')) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Error al generar el reporte PDF');
            }

            const blob = await response.blob();
            if (blob.type === 'application/json' || blob.size < 100) {
                throw new Error('Error al generar el reporte PDF (archivo corrupto o vacío)');
            }

            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `reporte_jira_${projectKey}_${new Date().toISOString().split('T')[0]}.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            // Incrementar métricas
            if (window.NexusModules && window.NexusModules.Dashboard && window.NexusModules.Dashboard.refreshMetrics) {
                await window.NexusModules.Dashboard.refreshMetrics();
            }

            if (typeof window.showDownloadNotification === 'function') {
                window.showDownloadNotification('Reporte PDF descargado exitosamente', 'success');
            }
        } catch (error) {
            console.error('Error al descargar PDF:', error);
            if (typeof window.showDownloadNotification === 'function') {
                window.showDownloadNotification(error.message || 'Error al generar el reporte PDF', 'error');
            }
        }
    }

    // Public API
    window.NexusModules.Jira.Downloads = {
        toggleDropdown: toggleDownloadDropdown,
        downloadPDF
    };

    // Global Exposure
    window.toggleDownloadDropdown = toggleDownloadDropdown;
    window.downloadPDF = downloadPDF;

})(window);
