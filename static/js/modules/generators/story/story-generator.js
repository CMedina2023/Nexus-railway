/**
 * Nexus AI - Story Generator Logic
 * Orquestador para la generación de historias de usuario.
 */
(function (window) {
    'use strict';

    const NexusModules = window.NexusModules || {};
    NexusModules.Generators = NexusModules.Generators || {};

    // Dependencias
    const Api = NexusModules.Generators.Api;
    const Utils = NexusModules.Generators.Utils;
    const StoryUI = NexusModules.Generators.StoryUI;

    /**
     * Orquestador de Historias
     */
    NexusModules.Generators.Story = {
        state: {
            currentData: null,
            currentHtml: null,
            currentCsv: null,
            editingIndex: null
        },

        /**
         * Inicializa el generador de historias
         */
        init() {
            const storiesForm = document.getElementById('stories-form');
            if (!storiesForm) return;

            this.setupForm(storiesForm);
            this.setupUIHandlers();

            // Setup DropZone
            Utils.setupDropZone('stories-drop-zone', 'stories-file', (file) => {
                this.handleFileSelect(file);
            });

            // Setup Char Counter
            Utils.setupCharCounter('stories-context', 'stories-context-counter', 2000);
        },

        /**
         * Configura el comportamiento del formulario
         */
        setupForm(form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                if (this.validateForm(form)) {
                    await this.generateStories(form);
                }
            });
        },

        /**
         * Valida los campos del formulario antes de enviar
         */
        validateForm(form) {
            const fileInput = document.getElementById('stories-file');
            const areaSelect = document.getElementById('stories-area');
            const validationErrors = [];

            if (!fileInput.files.length) {
                validationErrors.push('📄 Debes cargar un archivo (DOCX o PDF)');
                Utils.highlightError('stories-drop-zone');
            }

            if (!areaSelect || !areaSelect.value) {
                validationErrors.push('📋 Debes seleccionar un área');
                Utils.highlightError('stories-area');
            }

            if (validationErrors.length > 0) {
                const errorMessage = '⚠️ No puedes generar la vista previa:\n\n' + validationErrors.join('\n');
                window.showDownloadNotification(errorMessage, 'error');
                return false;
            }

            return true;
        },

        /**
         * Llama a la API para generar historias
         */
        async generateStories(form) {
            const formData = new FormData(form);
            const generateBtn = document.getElementById('stories-generate-btn');
            const progressContainer = document.getElementById('stories-progress-container');
            const progressBar = document.getElementById('stories-progress-bar');
            const progressPhase = document.getElementById('stories-progress-phase');
            const progressPercentage = document.getElementById('stories-progress-percentage');
            const progressMessage = document.getElementById('stories-progress-message');

            const areaSelect = document.getElementById('stories-area');
            const selectedArea = areaSelect ? areaSelect.value : '';

            // UI Setup
            if (generateBtn) {
                generateBtn.disabled = true;
                generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
            }
            if (progressContainer) progressContainer.style.display = 'block';

            try {
                await Api.generateStream('/api/stories/generate', formData, {
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
            if (!data.stories) return;

            // Ocultar formulario y mostrar vista previa
            const formContainer = document.getElementById('stories-form-container');
            const previewSection = document.getElementById('stories-preview-section');
            const backBtnContainer = document.getElementById('stories-back-btn-container');

            if (formContainer) formContainer.style.display = 'none';
            if (previewSection) previewSection.style.display = 'block';
            if (backBtnContainer) backBtnContainer.style.display = 'block';

            // Guardar datos en el estado
            this.state.currentData = data.stories;
            window.currentStoriesData = data.stories;
            this.state.currentHtml = data.html_content;
            this.state.currentCsv = data.csv_content;

            // Mostrar vista previa en la UI
            StoryUI.displayPreview(data, this.state);

            // Actualizar métricas
            if (data.stories_count > 0 && window.NexusModules?.Dashboard?.updateMetrics) {
                window.NexusModules.Dashboard.updateMetrics('stories', data.stories_count, selectedArea);
            }

            window.showDownloadNotification(`Historias generadas exitosamente: ${data.stories_count} historias`, 'success');
            const section = document.getElementById('crear-historias');
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

            const storiesFileInfo = document.getElementById('stories-file-info');
            const storiesFileName = document.getElementById('stories-file-name');

            if (storiesFileInfo && storiesFileName) {
                storiesFileName.textContent = file.name;
                storiesFileInfo.style.display = 'flex';
            }
        },

        /**
         * Configura los manejadores de eventos generales de la sección
         */
        setupUIHandlers() {
            // Botón Regresar
            const backBtn = document.getElementById('stories-back-btn');
            if (backBtn) backBtn.onclick = () => this.reset();

            // Botón Reset
            const resetBtn = document.getElementById('stories-reset-btn');
            if (resetBtn) {
                resetBtn.onclick = () => {
                    if (confirm('¿Estás seguro de que deseas hacer una nueva generación? Se perderán los datos actuales.')) {
                        this.reset();
                    }
                };
            }

            // Remover archivo
            const removeFileBtn = document.getElementById('stories-remove-file-btn');
            if (removeFileBtn) {
                removeFileBtn.onclick = () => {
                    const fileInput = document.getElementById('stories-file');
                    if (fileInput) fileInput.value = '';
                    const info = document.getElementById('stories-file-info');
                    if (info) info.style.display = 'none';
                };
            }

            // Modal de edición - Botones
            const editSaveBtn = document.getElementById('edit-story-save');
            if (editSaveBtn) editSaveBtn.onclick = () => StoryUI.saveEditChanges(this.state);

            const editCancelBtn = document.getElementById('edit-story-cancel');
            if (editCancelBtn) editCancelBtn.onclick = () => StoryUI.closeEditModal(this.state);

            const editCloseBtn = document.getElementById('edit-story-modal-close');
            if (editCloseBtn) editCloseBtn.onclick = () => StoryUI.closeEditModal(this.state);

            // Botón Revisar Historias
            const reviewBtn = document.getElementById('stories-review-btn');
            if (reviewBtn) {
                reviewBtn.onclick = () => StoryUI.openReviewModal(this.state);
            }

            // Exportar funciones globales necesarias para el HTML (si las hay)
            window.closeStoriesReview = () => StoryUI.closeReviewModal();
            window.downloadStoriesHTML = () => this.downloadHTML();
        },

        /**
         * Resetea el generador a su estado inicial
         */
        reset() {
            const form = document.getElementById('stories-form');
            if (form) form.reset();

            const fileInfo = document.getElementById('stories-file-info');
            if (fileInfo) fileInfo.style.display = 'none';

            const counter = document.getElementById('stories-context-counter');
            if (counter) counter.textContent = '0 / 2000 caracteres';

            const previewTbody = document.getElementById('stories-preview-tbody');
            if (previewTbody) previewTbody.innerHTML = '';

            // Reset state
            this.state.currentData = null;
            this.state.currentHtml = null;
            this.state.currentCsv = null;

            // UI Sections
            document.getElementById('stories-form-container').style.display = 'block';
            document.getElementById('stories-preview-section').style.display = 'none';
            document.getElementById('stories-back-btn-container').style.display = 'none';

            if (window.navigateToSection) {
                window.navigateToSection('crear-historias');
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
            a.download = 'historias_usuario.html';
            document.body.appendChild(a);
            a.click();
            URL.revokeObjectURL(url);
            document.body.removeChild(a);
            window.showDownloadNotification('HTML descargado exitosamente', 'success');
        }
    };

    window.NexusModules = NexusModules;
})(window);
