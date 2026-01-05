/**
 * Nexus AI - Feedback UI Module
 * Handles DOM manipulation and UI rendering for the feedback module
 */

(function (window) {
    'use strict';

    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Feedback = window.NexusModules.Feedback || {};

    const UI = {
        elements: {
            dropdown: 'feedback-dropdown',
            projectInput: 'feedback-project-selector-input',
            hiddenProjectInput: 'feedback-project-selector',
            form: 'feedback-form',
            noProjectMessage: 'feedback-no-project-message',
            summary: 'feedback-summary',
            editor: 'feedback-editor-content',
            loadingIndicator: 'feedback-loading-indicator',
            successMessage: 'feedback-success-message',
            successText: 'feedback-success-text',
            section: 'feedback'
        },

        getElement: function (id) {
            return document.getElementById(this.elements[id] || id);
        },

        /**
         * Renders the list of projects in the dropdown
         * @param {Array} projects 
         * @param {Function} onSelectCallback callback when a project is clicked
         */
        renderProjects: function (projects, onSelectCallback) {
            const dropdown = this.getElement('dropdown');
            if (!dropdown) return;

            dropdown.innerHTML = '';

            if (projects.length === 0) {
                const noResults = document.createElement('div');
                noResults.className = 'combobox-option';
                noResults.style.color = 'var(--text-muted)';
                noResults.style.cursor = 'default';
                noResults.textContent = 'No se encontraron proyectos';
                dropdown.appendChild(noResults);
                return;
            }

            projects.forEach(project => {
                const option = document.createElement('div');
                option.className = 'combobox-option';
                option.textContent = `${project.name} (${project.key})`;
                option.dataset.key = project.key;
                option.dataset.name = project.name;
                option.dataset.isNexus = project.key === 'NA';

                option.addEventListener('mousedown', function (e) {
                    e.preventDefault();
                    if (onSelectCallback) onSelectCallback(project.key, project.name);
                });

                dropdown.appendChild(option);
            });
        },

        showDropdown: function () {
            const dropdown = this.getElement('dropdown');
            if (dropdown) dropdown.style.display = 'block';
        },

        hideDropdown: function () {
            const dropdown = this.getElement('dropdown');
            if (dropdown) dropdown.style.display = 'none';
        },

        /**
         * updates the UI for project selection state
         * @param {string} projectName 
         * @param {string} projectKey 
         */
        setProjectSelection: function (projectName, projectKey) {
            const input = this.getElement('projectInput');
            const hiddenInput = this.getElement('hiddenProjectInput');

            if (input) input.value = `${projectName} (${projectKey})`;
            if (hiddenInput) hiddenInput.value = projectKey;
        },

        clearProjectSelection: function () {
            const input = this.getElement('projectInput');
            const hiddenInput = this.getElement('hiddenProjectInput');
            if (input) input.value = '';
            if (hiddenInput) hiddenInput.value = '';
        },

        /**
         * UI changes when validation starts
         */
        setValidatingState: function () {
            const input = this.getElement('projectInput');
            if (input) {
                input.style.opacity = '0.6';
                if (!input.value.includes('Validando')) {
                    input.value = input.value + ' ⏳ Validando...';
                }
            }
        },

        /**
         * UI changes when validation succeeds
         * @param {string} finalValue The final text to show in input
         */
        setValidationSuccess: function (finalValue) {
            const input = this.getElement('projectInput');
            if (input) {
                input.value = finalValue;
                input.setAttribute('readonly', 'readonly');
                input.style.opacity = '0.7';
                input.style.cursor = 'not-allowed';
            }
        },

        /**
         * Reset validation UI state
         */
        resetValidationState: function () {
            const input = this.getElement('projectInput');
            if (input) {
                input.removeAttribute('readonly');
                input.style.opacity = '1';
                input.style.cursor = 'text';
            }
        },

        toggleFormEnable: function (enable) {
            const form = this.getElement('form');
            const msg = this.getElement('noProjectMessage');

            if (enable) {
                if (form) form.classList.remove('disabled');
                if (msg) msg.style.display = 'none';
            } else {
                if (form) form.classList.add('disabled');
                if (msg) msg.style.display = 'block';
            }
        },

        setActiveIssueType: function (type) {
            const buttons = document.querySelectorAll('.feedback-issue-type-btn');
            buttons.forEach(btn => btn.classList.remove('active'));

            if (type === 'Bug' && buttons[0]) buttons[0].classList.add('active');
            else if (type !== 'Bug' && buttons[1]) buttons[1].classList.add('active');
        },

        getSummary: function () {
            const el = this.getElement('summary');
            return el ? el.value : '';
        },

        getDescription: function () {
            const el = this.getElement('editor');
            return el ? el.innerHTML : '';
        },

        setLoading: function (loading) {
            const form = this.getElement('form');
            const indicator = this.getElement('loadingIndicator');

            if (loading) {
                if (form) form.style.display = 'none';
                if (indicator) indicator.classList.add('active');
            } else {
                if (form) form.style.display = 'block';
                if (indicator) indicator.classList.remove('active');
            }
        },

        showSuccess: function (issueKey, issueUrl) {
            const msg = this.getElement('successMessage');
            const text = this.getElement('successText');

            if (msg) msg.classList.add('active');
            if (text) {
                text.innerHTML = `Tu reporte ha sido creado como <strong>${issueKey}</strong>. <a href="${issueUrl}" target="_blank" style="color: var(--accent); text-decoration: underline;">Ver en Jira</a>`;
            }

            // Auto hide logic might be better here or in controller, putting here for UI completeness
            setTimeout(() => {
                if (msg) msg.classList.remove('active');
                // Ensure form comes back if it was hidden
                const form = this.getElement('form');
                if (form) form.style.display = 'block';
            }, 10000);
        },

        resetForm: function () {
            const summary = this.getElement('summary');
            const editor = this.getElement('editor');
            if (summary) summary.value = '';
            if (editor) editor.innerHTML = '';
            // Issue type reset handled by controller calling setActiveIssueType
        },

        showNotification: function (message, type = 'warning') {
            // Re-implement the original notification logic
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: ${type === 'warning' ? 'rgba(245, 158, 11, 0.95)' : 'rgba(239, 68, 68, 0.95)'};
                color: white;
                padding: 1rem 1.5rem;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                z-index: 9999;
                animation: slideIn 0.3s ease;
                max-width: 400px;
                font-size: 0.9rem;
            `;
            // If success, maybe green? Original code used warning for everything except success maybe uses a different function `showDownloadNotification`? 
            // The original code used `showDownloadNotification` for API errors and successes, 
            // and `showFeedbackNotification` for local validation.
            // I will implement this as the local notification style.

            if (type === 'success') {
                notification.style.background = 'rgba(16, 185, 129, 0.95)';
            }

            notification.textContent = message;
            document.body.appendChild(notification);

            setTimeout(() => {
                notification.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => {
                    if (notification.parentNode) notification.remove();
                }, 300);
            }, 3000);
        },

        // Expose init observer
        initObserver: function (sectionId, onVisible) {
            const section = document.getElementById(sectionId);
            if (section) {
                const observer = new MutationObserver(function (mutations) {
                    mutations.forEach(function (mutation) {
                        if (mutation.attributeName === 'class') {
                            if (section.classList.contains('active')) {
                                onVisible();
                            }
                        }
                    });
                });
                observer.observe(section, { attributes: true });
            }
        }
    };

    window.NexusModules.Feedback.UI = UI;

})(window);
