/**
 * Nexus AI - Feedback Module
 * Handles functionality related to sending feedback/bugs to Jira
 * Refactored to separate concerns:
 * - feedback/api.js: API interactions
 * - feedback/validator.js: Validation logic
 * - feedback/ui.js: DOM manipulation & UI state
 */

(function (window) {
    'use strict';

    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Feedback = window.NexusModules.Feedback || {};

    // Import sub-modules
    const API = window.NexusModules.Feedback.API;
    const Validator = window.NexusModules.Feedback.Validator;
    const UI = window.NexusModules.Feedback.UI;

    // State Variables
    let selectedFeedbackIssueType = 'Bug';
    let selectedFeedbackProjectKey = '';
    let feedbackProjectLocked = false;
    let feedbackAllProjects = [];

    // --- Data Loading ---

    function loadFeedbackProjects() {
        if (!API) return console.error('Feedback API module not loaded');

        API.getProjects()
            .then(data => {
                if (data.success && data.projects && data.projects.length > 0) {
                    feedbackAllProjects = data.projects;
                    UI.renderProjects(feedbackAllProjects, selectFeedbackProject);
                } else {
                    showAppNotification(data.error || 'No hay proyectos disponibles', 'error');
                }
            })
            .catch(error => {
                console.error('Error cargando proyectos:', error);
                showAppNotification('Error al cargar proyectos: ' + error.message, 'error');
            });
    }

    // --- UI Interactions (Global) ---

    window.filterFeedbackProjects = function (searchTerm) {
        if (feedbackProjectLocked) return;

        const filtered = feedbackAllProjects.filter(project =>
            project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            project.key.toLowerCase().includes(searchTerm.toLowerCase())
        );
        UI.renderProjects(filtered, selectFeedbackProject);
    };

    window.showFeedbackDropdown = function () {
        if (feedbackProjectLocked) return;
        UI.showDropdown();
        if (feedbackAllProjects.length > 0) {
            UI.renderProjects(feedbackAllProjects, selectFeedbackProject);
        }
    };

    window.hideFeedbackDropdown = function () {
        setTimeout(() => UI.hideDropdown(), 200);
    };

    window.handleFeedbackKeydown = function (event) {
        if (feedbackProjectLocked) {
            event.preventDefault();
        }
    };

    window.selectFeedbackIssueType = function (type) {
        selectedFeedbackIssueType = type;
        UI.setActiveIssueType(type);
    };

    window.formatFeedbackText = function (command) {
        document.execCommand(command, false, null);
        const editor = document.getElementById('feedback-editor-content');
        if (editor) editor.focus();
    };

    window.insertFeedbackLink = function () {
        const url = prompt('Ingresa la URL:');
        if (url) document.execCommand('createLink', false, url);
    };

    window.insertFeedbackImage = function (event) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function (e) {
                const img = document.createElement('img');
                img.src = e.target.result;
                img.style.maxWidth = '100%';
                const editor = document.getElementById('feedback-editor-content');
                if (editor) editor.appendChild(img);
            };
            reader.readAsDataURL(file);
        }
    };

    window.resetFeedbackForm = function () {
        UI.resetForm();
        window.selectFeedbackIssueType('Bug');
    };

    // --- Core Actions ---

    function selectFeedbackProject(projectKey, projectName) {
        if (feedbackProjectLocked && projectKey !== selectedFeedbackProjectKey) {
            UI.showNotification('El proyecto ya ha sido seleccionado y no puede ser cambiado', 'warning');
            return;
        }

        const validation = Validator.validateProjectSelection(projectKey);
        if (!validation.valid) {
            UI.showNotification(validation.message, 'warning');
            UI.clearProjectSelection();
            return;
        }

        UI.setProjectSelection(projectName, projectKey);
        validateFeedbackProject(projectKey);
    }

    function validateFeedbackProject(projectKey) {
        UI.setValidatingState();

        API.validateProject(projectKey)
            .then(data => {
                if (data.success && data.valid) {
                    selectedFeedbackProjectKey = projectKey;
                    feedbackProjectLocked = true;
                    UI.toggleFormEnable(true);

                    // Reconstruct the display value for success state
                    const input = document.getElementById('feedback-project-selector-input');
                    let displayValue = input ? input.value : '';
                    displayValue = displayValue.replace(' ⏳ Validando...', '') + ' ✓';

                    UI.setValidationSuccess(displayValue);
                    showAppNotification('Proyecto validado correctamente. Ya puedes enviar tu feedback.', 'success');
                } else {
                    showAppNotification(data.error || 'Proyecto no válido', 'error');
                    UI.resetValidationState();
                    UI.clearProjectSelection();
                }
            })
            .catch(error => {
                console.error('Error validando proyecto:', error);
                showAppNotification('Error al validar proyecto: ' + error.message, 'error');
                UI.resetValidationState();
                UI.clearProjectSelection();
            });
    }

    window.submitFeedback = async function () {
        const summary = UI.getSummary();
        const description = UI.getDescription();

        const validation = Validator.validateSubmission(summary, description);
        if (!validation.valid) {
            showAppNotification(validation.message, 'warning');
            return;
        }

        UI.setLoading(true);

        try {
            const data = await API.submitFeedback({
                project_key: selectedFeedbackProjectKey,
                issue_type: selectedFeedbackIssueType,
                summary: summary,
                description: description
            });

            UI.setLoading(false);

            if (data.success) {
                UI.showSuccess(data.issue_key, data.issue_url);
                showAppNotification(data.message || 'Feedback enviado exitosamente', 'success');
                window.resetFeedbackForm();
            } else {
                showAppNotification('Error: ' + (data.error || 'No se pudo enviar el feedback'), 'error');
            }
        } catch (error) {
            UI.setLoading(false);
            showAppNotification('Error de conexión: ' + error.message, 'error');
        }
    };

    // Helper to use global notification if available
    function showAppNotification(message, type) {
        if (typeof window.showDownloadNotification === 'function') {
            window.showDownloadNotification(message, type);
        } else {
            UI.showNotification(message, type);
        }
    }

    // --- Initialization ---

    function init() {
        UI.initObserver('feedback', () => {
            loadFeedbackProjects();
            const noProjectMessage = document.getElementById('feedback-no-project-message');
            if (noProjectMessage) noProjectMessage.style.display = 'block';
        });
    }

    window.NexusModules.Feedback.init = init;

})(window);
