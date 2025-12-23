/**
 * Nexus AI - Core Navigation System
 * Maneja la navegación SPA (Single Page Application)
 */

(function (window) {
    'use strict';

    /**
     * Navega a una sección específica del SPA
     * @param {string} sectionId - ID de la sección destino
     */
    async function navigateToSection(sectionId) {
        // Limpiar reporte si se está saliendo de jira-reportes
        const currentSection = document.querySelector('.content-section.active');
        if (currentSection && currentSection.id === 'jira-reportes' && sectionId !== 'jira-reportes') {
            if (window.clearJiraReport) window.clearJiraReport();
        }

        // Limpiar carga masiva si se está saliendo de jira-carga-masiva
        if (currentSection && (currentSection.id === 'jira-carga-masiva' || currentSection.id === 'carga-masiva') && sectionId !== currentSection.id) {
            if (window.NexusModules?.Jira?.BulkUpload?.reset) {
                window.NexusModules.Jira.BulkUpload.reset();
            } else if (window.resetCargaMasiva) {
                window.resetCargaMasiva();
            }
        }

        // Hide all sections
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });

        // Show selected section
        const targetSection = document.getElementById(sectionId);
        if (targetSection) {
            targetSection.classList.add('active');
        }

        // Update active nav item (usar active-link en lugar de active)
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active-link'); // Asegurarnos de limpiar todas las clases old style
            item.classList.remove('active');
        });

        const activeNav = document.querySelector(`[data-section="${sectionId}"]`);
        if (activeNav) {
            activeNav.classList.add('active-link');
        }

        // Hook system simple para inicialización de módulos
        // En el futuro, esto se manejará con eventos personalizados

        // Inicializar reportes si se navega a jira-reportes
        if (sectionId === 'jira-reportes' && window.initJiraReports) {
            window.initJiraReports();
        }

        // Inicializar carga masiva si se navega a jira-carga-masiva
        if (sectionId === 'jira-carga-masiva') {
            if (window.NexusModules?.Jira?.BulkUpload?.init) {
                window.NexusModules.Jira.BulkUpload.init();
            } else if (window.initCargaMasiva) {
                window.initCargaMasiva();
            }
        }

        // Cargar métricas del dashboard si se navega al dashboard
        if (sectionId === 'dashboard' && window.loadDashboardMetrics) {
            await window.loadDashboardMetrics();
        }

        // Initialize charts if navigating to infografia
        if (sectionId === 'infografia' && window.initializeCharts) {
            setTimeout(() => {
                window.initializeCharts();
            }, 100);
        }

        // Load metrics if navigating to metricas
        if (sectionId === 'metricas' && window.loadAllMetrics) {
            setTimeout(() => {
                window.loadAllMetrics();
            }, 100);
        }

        // Load admin panel if navigating to admin
        if (sectionId === 'admin' && window.adminInitPanel) {
            setTimeout(() => {
                window.adminInitPanel();
            }, 100);
        }

        // Scroll to top
        window.scrollTo(0, 0);
    }

    // Sidebar Toggle
    function initSidebar() {
        const sidebar = document.getElementById('sidebar');
        const sidebarToggle = document.getElementById('sidebarToggle');

        if (sidebarToggle && sidebar) {
            sidebarToggle.addEventListener('click', () => {
                sidebar.classList.toggle('collapsed');
            });
        }
    }

    // Configurar listeners de navegación
    function initNavigationListeners() {
        // Nav Item Click Handlers
        document.querySelectorAll('.nav-item, .quick-link, .card-action').forEach(item => {
            item.addEventListener('click', (e) => {
                const dataRoute = item.getAttribute('data-route');
                const href = item.getAttribute('href');
                const sectionId = item.getAttribute('data-section');

                // Si tiene data-route o href que sea una ruta externa
                if (dataRoute && dataRoute.startsWith('/auth/')) {
                    window.location.href = dataRoute;
                    return;
                }

                if (href && href !== '#' && href.startsWith('/auth/')) {
                    window.location.href = href;
                    return;
                }

                // Para secciones internas
                e.preventDefault();
                e.stopPropagation();
                if (sectionId) {
                    navigateToSection(sectionId);
                }
            });
        });

        // Inicializar el toggle del sidebar
        initSidebar();
    }

    // Exponer al scope global
    window.navigateToSection = navigateToSection;

    // Inicializar listeners cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initNavigationListeners);
    } else {
        initNavigationListeners();
    }

    // Namespace moderno
    window.NexusNavigation = {
        navigateTo: navigateToSection,
        init: initNavigationListeners
    };

})(window);
