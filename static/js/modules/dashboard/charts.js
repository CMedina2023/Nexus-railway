/**
 * Nexus AI - Dashboard Charts Module
 * Handles chart rendering and updates for dashboard metrics.
 */

(function (window) {
    'use strict';

    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Dashboard = window.NexusModules.Dashboard || {};

    // Chart instances
    let areaChartInstance = null;
    let reportsByProjectChart = null;
    let reportsTrendChart = null;
    let uploadsByTypeChart = null;
    let uploadsByProjectChart = null;
    let uploadsTrendChart = null;

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

            // Agrupar por día (YYYY-MM-DD)
            const trendData = {};
            history.forEach(item => {
                const date = new Date(item.timestamp || item.date);
                // Formato YYYY-MM-DD local
                const year = date.getFullYear();
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const day = String(date.getDate()).padStart(2, '0');
                const dayKey = `${year}-${month}-${day}`;

                trendData[dayKey] = (trendData[dayKey] || 0) + 1;
            });

            const dates = Object.keys(trendData).sort();
            const counts = dates.map(d => trendData[d]);

            reportsTrendChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: dates,
                    datasets: [{
                        label: 'Reportes Generados',
                        data: counts,
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
                        },
                        tooltip: {
                            callbacks: {
                                title: function (context) {
                                    return context[0].label;
                                }
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
                                color: 'var(--text-secondary)',
                                maxRotation: 45,
                                minRotation: 45
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

            // Agrupar por día (YYYY-MM-DD)
            const trendData = {};
            history.forEach(item => {
                const date = new Date(item.timestamp || item.date);
                // Formato YYYY-MM-DD local
                const year = date.getFullYear();
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const day = String(date.getDate()).padStart(2, '0');
                const dayKey = `${year}-${month}-${day}`;

                trendData[dayKey] = (trendData[dayKey] || 0) + (item.itemsCount || 0); // Para uploads usamos item.itemsCount
            });

            const dates = Object.keys(trendData).sort();
            const counts = dates.map(d => trendData[d]);

            uploadsTrendChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: dates,
                    datasets: [{
                        label: 'Items Cargados',
                        data: counts,
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
                        },
                        tooltip: {
                            callbacks: {
                                title: function (context) {
                                    return context[0].label;
                                }
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
                                color: 'var(--text-secondary)',
                                maxRotation: 45,
                                minRotation: 45
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

    // Export internal functions
    window.NexusModules.Dashboard.updateAreaChart = updateAreaChart;
    window.NexusModules.Dashboard.updateReportsCharts = updateReportsCharts;
    window.NexusModules.Dashboard.updateUploadsCharts = updateUploadsCharts;

})(window);
