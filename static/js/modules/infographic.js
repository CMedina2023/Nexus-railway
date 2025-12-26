/**
 * Nexus AI - Infographic Module
 * Handles the initialization and rendering of infographic charts.
 */

(function (window) {
    'use strict';

    // Ensure namespace exists
    window.NexusModules = window.NexusModules || {};

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
            legend: { labels: { color: colors.text } },
            tooltip: { callbacks: { title: tooltipTitleCallback } }
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

    /**
     * Initialize charts for infografía
     */
    function initializeCharts() {
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

    // Public API
    window.NexusModules.Infographic = {
        init: initializeCharts
    };

    // Global Exposure
    window.initializeCharts = initializeCharts;

})(window);
