

// Accordion Management System - DEPRECADO (ya no hay acordeón)
function toggleAccordion(accordionItem) {
    // Función deprecada - ya no hay acordeón, pero se mantiene por compatibilidad
}

function expandAccordionForSection(sectionId) {
    // Función deprecada - ya no hay acordeón, pero se mantiene por compatibilidad
}

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
// Helper function for fetch with extended timeout
// fetchWithTimeout reemplazada por NexusApi.client.request
// Mantenemos binding por retrocompatibilidad con scripts inline si los hubiera
window.fetchWithTimeout = window.NexusApi.client.request.bind(window.NexusApi.client);


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

    // Initialize Feedback Module
    if (window.NexusModules && window.NexusModules.Feedback && window.NexusModules.Feedback.init) {
        window.NexusModules.Feedback.init();
    }
});