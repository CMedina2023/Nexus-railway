/**
 * Nexus AI - Test Case UI Handlers
 * Manejo de eventos y UI específica para la generación de casos de prueba.
 */
(function (window) {
    'use strict';

    const NexusModules = window.NexusModules || {};
    NexusModules.Generators = NexusModules.Generators || {};
    NexusModules.Generators.TestCase = NexusModules.Generators.TestCase || {};

    // Dependencias
    const Utils = NexusModules.Generators.Utils;
    const TestUI = NexusModules.Generators.TestUI;
    const Validator = NexusModules.Generators.TestCase.Validator;
    const GeneratorApi = NexusModules.Generators.TestCase.GeneratorApi;
    const StateManager = NexusModules.Generators.TestCase.StateManager;

    /**
     * Manejadores de UI para Casos de Prueba
     */
    NexusModules.Generators.TestCase.UIHandlers = {
        /**
         * Inicializa los manejadores
         */
        init() {
            const testsForm = document.getElementById('tests-form');
            if (testsForm) {
                this.setupForm(testsForm);
            }
            this.setupUIHandlers();
            // Cargar requerimientos al iniciar
            if (TestUI.loadRequirements) {
                TestUI.loadRequirements();
            }

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
                if (Validator.validateForm(form)) {
                    await GeneratorApi.generateTests(form);
                }
            });
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
            this.setupNavigationHandlers();
            this.setupFileHandlers();
            this.setupModalHandlers();
            this.setupGlobalExports();
        },

        /**
         * Handlers para navegación y reset
         */
        setupNavigationHandlers() {
            const backBtn = document.getElementById('tests-back-btn');
            if (backBtn) backBtn.onclick = () => this.reset();

            const resetBtn = document.getElementById('tests-reset-btn');
            if (resetBtn) {
                resetBtn.onclick = () => {
                    if (confirm('¿Estás seguro de que deseas hacer una nueva generación? Se perderán los datos actuales.')) {
                        this.reset();
                    }
                };
            }
        },

        /**
         * Handlers para archivos
         */
        setupFileHandlers() {
            const removeFileBtn = document.getElementById('tests-remove-file-btn');
            if (removeFileBtn) {
                removeFileBtn.onclick = () => {
                    const fileInput = document.getElementById('tests-file');
                    if (fileInput) fileInput.value = '';
                    const info = document.getElementById('tests-file-info');
                    if (info) info.style.display = 'none';
                };
            }
        },

        /**
         * Handlers para modales
         */
        setupModalHandlers() {
            const state = StateManager.getState();

            const editSaveBtn = document.getElementById('edit-test-save');
            if (editSaveBtn) editSaveBtn.onclick = () => TestUI.saveEditChanges(state);

            const editCancelBtn = document.getElementById('edit-test-cancel');
            if (editCancelBtn) editCancelBtn.onclick = () => TestUI.closeEditModal(state);

            const editCloseBtn = document.getElementById('edit-test-modal-close');
            if (editCloseBtn) editCloseBtn.onclick = () => TestUI.closeEditModal(state);

            const reviewBtn = document.getElementById('tests-review-btn');
            if (reviewBtn) {
                reviewBtn.onclick = () => TestUI.openReviewModal(state);
            }
        },

        /**
         * Exporta funciones globales necesarias
         */
        setupGlobalExports() {
            window.closeTestsReview = () => TestUI.closeReviewModal();
            window.downloadTestsHTML = () => GeneratorApi.downloadHTML();
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
            StateManager.resetState();

            // UI Sections
            const formContainer = document.getElementById('tests-form-container');
            const previewSection = document.getElementById('tests-preview-section');
            const backBtnContainer = document.getElementById('tests-back-btn-container');

            if (formContainer) formContainer.style.display = 'block';
            if (previewSection) previewSection.style.display = 'none';
            if (backBtnContainer) backBtnContainer.style.display = 'none';

            if (window.navigateToSection) {
                window.navigateToSection('crear-casos-prueba');
            }
        }
    };

    window.NexusModules = NexusModules;
})(window);
