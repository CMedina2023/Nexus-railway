/**
 * Nexus AI - Test Case Generator Logic
 * Orquestador para la generación de casos de prueba.
 */
(function (window) {
    'use strict';

    const NexusModules = window.NexusModules || {};
    NexusModules.Generators = NexusModules.Generators || {};

    // Dependencias
    const Api = NexusModules.Generators.Api;
    const Utils = NexusModules.Generators.Utils;
    const TestUI = NexusModules.Generators.TestUI;

    /**
     * Orquestador de Casos de Prueba
     */
    NexusModules.Generators.TestCase = {
        state: {
            currentData: null,
            currentHtml: null,
            currentCsv: null,
            editingIndex: null
        },

        /**
         * Inicializa el generador de casos de prueba
         */
        init() {
            const testsForm = document.getElementById('tests-form');
            if (!testsForm) return;

            this.setupForm(testsForm);
            this.setupUIHandlers();

            // Setup DropZone
            Utils.setupDropZone('tests-drop-zone', 'tests-file', (file) => {
                this.handleFileSelect(file);
            });
        },

        /**
         * Configura el comportamiento del formulario
         */
        setupForm(form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                if (this.validateForm(form)) {
                    await this.generateTests(form);
                }
            });
        },

        /**
         * Valida los campos del formulario antes de enviar
         */
        validateForm(form) {
            const fileInput = document.getElementById('tests-file');
            const areaSelect = document.getElementById('tests-area');
            const selectedTypes = Array.from(document.querySelectorAll('input[name="test_types"]:checked'));
            const validationErrors = [];

            if (!fileInput.files.length) {
                validationErrors.push('📄 Debes cargar un archivo (DOCX o PDF)');
                Utils.highlightError('tests-drop-zone');
            }

            if (!areaSelect || !areaSelect.value) {
                validationErrors.push('📋 Debes seleccionar un área');
                Utils.highlightError('tests-area');
            }

            if (selectedTypes.length === 0) {
                validationErrors.push('✅ Debes seleccionar al menos un tipo de prueba');
                const checkboxContainers = document.querySelectorAll('input[name="test_types"]');
                checkboxContainers.forEach(cb => {
                    const parent = cb.closest('.checkbox-item');
                    if (parent) Utils.highlightError(parent);
                });
            }

            if (validationErrors.length > 0) {
                const errorMessage = '⚠️ No puedes generar la vista previa:\n\n' + validationErrors.join('\n');
                window.showDownloadNotification(errorMessage, 'error');
                return false;
            }

            return true;
        },

        /**
         * Llama a la API para generar casos de prueba
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
            if (generateBtn) {
                generateBtn.disabled = true;
                generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
            }
            if (progressContainer) progressContainer.style.display = 'block';

            try {
                await Api.generateStream('/api/tests/generate', formData, {
                    onProgress: (data) => {
                        if (data.progress !== undefined) {
                            if (progressBar) progressBar.style.width = `${data.progress}%`;
                            if (progressPercentage) progressPercentage.textContent = `${data.progress}%`;
                        }
                        if (data.status && progressPhase) progressPhase.textContent = data.status;
                        if (data.message && progressMessage) progressMessage.textContent = data.message;
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
                if (generateBtn) {
                    generateBtn.disabled = false;
                    generateBtn.innerHTML = '<i class="fas fa-eye"></i> Generar e Ir a Vista Previa';
                }
                if (progressContainer) progressContainer.style.display = 'none';
            }
        },

        /**
         * Maneja el fin de la generación exitosa
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
            this.state.currentData = data.test_cases;
            window.currentTestsData = data.test_cases;
            this.state.currentHtml = data.html_content;
            this.state.currentCsv = data.csv_content;

            // Mostrar vista previa en la UI
            TestUI.displayPreview(data, this.state);

            // Actualizar métricas
            if (data.test_cases_count > 0 && window.NexusModules?.Dashboard?.updateMetrics) {
                window.NexusModules.Dashboard.updateMetrics('test_cases', data.test_cases_count, selectedArea);
            }

            window.showDownloadNotification(`Casos de prueba generados exitosamente: ${data.test_cases_count} casos`, 'success');
            const section = document.getElementById('crear-casos-prueba');
            if (section) section.scrollIntoView({ behavior: 'smooth', block: 'start' });
        },

        /**
         * Maneja la selección de archivos
         */
        handleFileSelect(file) {
            const validExtensions = ['.docx', '.pdf'];
            const fileExtension = '.' + file.name.split('.').pop().toLowerCase();

            if (!validExtensions.includes(fileExtension)) {
                window.showDownloadNotification('❌ Solo se permiten archivos DOCX o PDF', 'error');
                return;
            }

            const testsFileInfo = document.getElementById('tests-file-info');
            const testsFileName = document.getElementById('tests-file-name');

            if (testsFileInfo && testsFileName) {
                testsFileName.textContent = file.name;
                testsFileInfo.style.display = 'flex';
            }
        },

        /**
         * Configura los manejadores de eventos generales de la sección
         */
        setupUIHandlers() {
            // Botón Regresar
            const backBtn = document.getElementById('tests-back-btn');
            if (backBtn) backBtn.onclick = () => this.reset();

            // Botón Reset
            const resetBtn = document.getElementById('tests-reset-btn');
            if (resetBtn) {
                resetBtn.onclick = () => {
                    if (confirm('¿Estás seguro de que deseas hacer una nueva generación? Se perderán los datos actuales.')) {
                        this.reset();
                    }
                };
            }

            // Remover archivo
            const removeFileBtn = document.getElementById('tests-remove-file-btn');
            if (removeFileBtn) {
                removeFileBtn.onclick = () => {
                    const fileInput = document.getElementById('tests-file');
                    if (fileInput) fileInput.value = '';
                    const info = document.getElementById('tests-file-info');
                    if (info) info.style.display = 'none';
                };
            }

            // Modal de edición - Botones
            const editSaveBtn = document.getElementById('edit-test-save');
            if (editSaveBtn) editSaveBtn.onclick = () => TestUI.saveEditChanges(this.state);

            const editCancelBtn = document.getElementById('edit-test-cancel');
            if (editCancelBtn) editCancelBtn.onclick = () => TestUI.closeEditModal(this.state);

            const editCloseBtn = document.getElementById('edit-test-modal-close');
            if (editCloseBtn) editCloseBtn.onclick = () => TestUI.closeEditModal(this.state);

            // Botón Revisar Casos
            const reviewBtn = document.getElementById('tests-review-btn');
            if (reviewBtn) {
                reviewBtn.onclick = () => TestUI.openReviewModal(this.state);
            }

            // Exportar funciones globales necesarias para el HTML
            window.closeTestsReview = () => TestUI.closeReviewModal();
            window.downloadTestsHTML = () => this.downloadHTML();
        },

        /**
         * Resetea el generador a su estado inicial
         */
        reset() {
            const form = document.getElementById('tests-form');
            if (form) form.reset();

            const fileInfo = document.getElementById('tests-file-info');
            if (fileInfo) fileInfo.style.display = 'none';

            const previewTbody = document.getElementById('tests-preview-tbody');
            if (previewTbody) previewTbody.innerHTML = '';

            // Reset state
            this.state.currentData = null;
            this.state.currentHtml = null;
            this.state.currentCsv = null;

            // UI Sections
            document.getElementById('tests-form-container').style.display = 'block';
            document.getElementById('tests-preview-section').style.display = 'none';
            document.getElementById('tests-back-btn-container').style.display = 'none';

            if (window.navigateToSection) {
                window.navigateToSection('crear-casos-prueba');
            }
        },

        /**
         * Descarga el HTML generado
         */
        downloadHTML() {
            if (!this.state.currentHtml) return;

            const blob = new Blob([this.state.currentHtml], { type: 'text/html;charset=utf-8' });
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
