/**
 * Nexus AI - Test Case Generator API
 * Maneja la interacción con la API para la generación de casos de prueba.
 */
(function (window) {
    'use strict';

    const NexusModules = window.NexusModules || {};
    NexusModules.Generators = NexusModules.Generators || {};
    NexusModules.Generators.TestCase = NexusModules.Generators.TestCase || {};

    // Dependencias
    const Api = NexusModules.Generators.Api;
    const TestUI = NexusModules.Generators.TestUI;
    const StateManager = NexusModules.Generators.TestCase.StateManager;

    /**
     * Cliente API específico para Casos de Prueba
     */
    NexusModules.Generators.TestCase.GeneratorApi = {
        /**
         * Llama a la API para generar casos de prueba
         * @param {HTMLFormElement} form - Formulario con los datos
         */
        async generateTests(form) {
            const formData = new FormData(form);
            const generateBtn = document.getElementById('tests-generate-btn');
            const progressContainer = document.getElementById('tests-progress-container');
            const progressBar = document.getElementById('tests-progress-bar');
            const progressPhase = document.getElementById('tests-progress-phase');
            const progressPercentage = document.getElementById('tests-progress-percentage');
            const progressMessage = document.getElementById('tests-progress-message');

            const areaSelect = document.getElementById('tests-area');
            const selectedArea = areaSelect ? areaSelect.value : '';

            // UI Setup
            this.setLoadingState(true, generateBtn, progressContainer);

            try {
                await Api.generateStream('/api/tests/generate', formData, {
                    onProgress: (data) => {
                        this.updateProgress(data, progressBar, progressPercentage, progressPhase, progressMessage);
                    },
                    onTerminal: (data) => {
                        this.handleGenerationTerminal(data, selectedArea);
                    },
                    onError: (error) => {
                        throw error;
                    }
                });
            } catch (error) {
                console.error('Error en generación:', error);
                window.showDownloadNotification('Error: ' + error.message, 'error');
            } finally {
                this.setLoadingState(false, generateBtn, progressContainer);
            }
        },

        /**
         * Actualiza el estado de carga visual
         */
        setLoadingState(isLoading, btn, container) {
            if (btn) {
                btn.disabled = isLoading;
                btn.innerHTML = isLoading ?
                    '<i class="fas fa-spinner fa-spin"></i> Procesando...' :
                    '<i class="fas fa-eye"></i> Generar e Ir a Vista Previa';
            }
            if (container) container.style.display = isLoading ? 'block' : 'none';
        },

        /**
         * Actualiza la barra de progreso
         */
        updateProgress(data, bar, percentage, phase, message) {
            if (data.progress !== undefined) {
                if (bar) bar.style.width = `${data.progress}%`;
                if (percentage) percentage.textContent = `${data.progress}%`;
            }
            if (data.status && phase) phase.textContent = data.status;
            if (data.message && message) message.textContent = data.message;
        },

        /**
         * Maneja el fin de la generación exitosa
         * @param {Object} data - Datos de la generación
         * @param {string} selectedArea - Área seleccionada para métricas
         */
        handleGenerationTerminal(data, selectedArea) {
            if (!data.test_cases) return;

            // Ocultar formulario y mostrar vista previa
            const formContainer = document.getElementById('tests-form-container');
            const previewSection = document.getElementById('tests-preview-section');
            const backBtnContainer = document.getElementById('tests-back-btn-container');

            if (formContainer) formContainer.style.display = 'none';
            if (previewSection) previewSection.style.display = 'block';
            if (backBtnContainer) backBtnContainer.style.display = 'block';

            // Guardar datos en el estado
            StateManager.setGeneratedData(data);

            // Mostrar vista previa en la UI
            TestUI.displayPreview(data, StateManager.getState());

            // Actualizar métricas
            if (data.test_cases_count > 0 && window.NexusModules?.Dashboard?.updateMetrics) {
                window.NexusModules.Dashboard.updateMetrics('test_cases', data.test_cases_count, selectedArea);
            }

            window.showDownloadNotification(`Casos de prueba generados exitosamente: ${data.test_cases_count} casos`, 'success');
            const section = document.getElementById('crear-casos-prueba');
            if (section) section.scrollIntoView({ behavior: 'smooth', block: 'start' });
        },

        /**
         * Descarga el HTML generado
         */
        downloadHTML() {
            const state = StateManager.getState();
            if (!state.currentHtml) return;

            const blob = new Blob([state.currentHtml], { type: 'text/html;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'casos_prueba.html';
            document.body.appendChild(a);
            a.click();
            URL.revokeObjectURL(url);
            document.body.removeChild(a);
            window.showDownloadNotification('HTML descargado exitosamente', 'success');
        }
    };

    window.NexusModules = NexusModules;
})(window);
