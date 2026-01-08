/**
 * Nexus AI - Story Jira Integration Module
 * Maneja la lógica de subida de historias de usuario a Jira.
 */
(function (window) {
    'use strict';

    const NexusModules = window.NexusModules || {};
    const Api = NexusModules.Generators.Api;
    const Utils = NexusModules.Generators.Utils;
    const ProjectCache = NexusModules.Generators.JiraProjectCache;
    const ButtonState = NexusModules.Generators.JiraButtonState;

    NexusModules.Generators.StoryJira = {
        /**
         * Inicializa la lógica de Jira para historias
         */
        init() {
            this.setupEventListeners();
            // Pre-cargar proyectos en background
            ProjectCache.preloadProjects();
        },

        /**
         * Configura los event listeners del modal de Jira
         */
        setupEventListeners() {
            const uploadJiraBtn = document.getElementById('stories-upload-jira-btn');
            if (uploadJiraBtn) {
                uploadJiraBtn.onclick = () => this.handleOpenJiraModal();
            }

            const modalClose = document.getElementById('jira-modal-close');
            const modalCancel = document.getElementById('jira-modal-cancel');
            if (modalClose) modalClose.onclick = () => this.closeJiraModal();
            if (modalCancel) modalCancel.onclick = () => this.closeJiraModal();

            const assigneeInput = document.getElementById('jira-assignee-input');
            if (assigneeInput) {
                assigneeInput.addEventListener('blur', () => this.validateAssignee());
            }

            const modalUploadBtn = document.getElementById('jira-modal-upload');
            if (modalUploadBtn) {
                modalUploadBtn.onclick = () => this.handleUpload();
            }
        },

        /**
         * Abre el modal de Jira y carga los proyectos
         */
        async handleOpenJiraModal() {
            const selected = document.querySelectorAll('.story-checkbox:checked');
            if (selected.length === 0) {
                window.showDownloadNotification('Por favor selecciona al menos una historia para subir', 'error');
                return;
            }

            const selectedStoriesRaw = Array.from(selected).map(cb => {
                const index = parseInt(cb.dataset.index);
                return window.currentStoriesData[index];
            });

            // US-W1.3 - Bloquear subida a Jira si no está APPROVED
            // Validamos tanto mayúsculas como minúsculas para robustez
            const selectedStories = selectedStoriesRaw.filter(s =>
                s.approval_status && s.approval_status.toUpperCase() === 'APPROVED'
            );
            const unapprovedCount = selectedStoriesRaw.length - selectedStories.length;

            if (unapprovedCount > 0) {
                if (selectedStories.length === 0) {
                    window.showDownloadNotification('Solo se pueden subir historias con estado Aprobado (APPROVED).', 'error');
                    return;
                }
                window.showDownloadNotification(`Se han omitido ${unapprovedCount} historias que no están aprobadas.`, 'warning');
            }

            window.selectedStoriesForUpload = selectedStories;

            try {
                ButtonState.showLoading('stories-upload-jira-btn', 'Cargando proyectos de Jira...');

                const projects = await ProjectCache.getProjects();
                await this.setupModalWithProjects(projects);

                document.getElementById('jira-modal-stories-count').textContent = `${selectedStories.length} historias seleccionadas para subir`;
                ButtonState.hideLoading('stories-upload-jira-btn');
                document.getElementById('jira-upload-modal').style.display = 'flex';
            } catch (error) {
                ButtonState.hideLoading('stories-upload-jira-btn');
                console.error('Error opening Jira modal:', error);
                window.showDownloadNotification('Error al abrir el modal de Jira', 'error');
            }
        },

        /**
         * Configura el modal con los proyectos cargados
         */
        async setupModalWithProjects(projects) {
            if (projects.length === 0) {
                window.showDownloadNotification('No se encontraron proyectos de Jira. Verifica tu configuración.', 'error');
                throw new Error('No projects found');
            }

            // Usar la utilidad setupSearchableCombo
            Utils.setupSearchableCombo({
                inputId: 'jira-project-search-input',
                dropdownId: 'jira-project-dropdown',
                hiddenId: 'jira-project-select',
                dataArray: projects
            });
        },

        /**
         * Carga los proyectos de Jira en el combobox (método legacy)
         * @deprecated Usar setupModalWithProjects con ProjectCache.getProjects() en su lugar
         */
        async loadJiraProjects() {
            try {
                const projects = await ProjectCache.getProjects();
                await this.setupModalWithProjects(projects);
            } catch (error) {
                console.error('Error loading Jira projects:', error);
                window.showDownloadNotification('Error al cargar proyectos de Jira', 'error');
                throw error;
            }
        },

        /**
         * Cierra el modal de Jira
         */
        closeJiraModal() {
            document.getElementById('jira-upload-modal').style.display = 'none';
            document.getElementById('jira-assignee-input').value = '';
            document.getElementById('jira-assignee-validation').style.display = 'none';

            // Limpiar búsqueda y selección
            const searchInput = document.getElementById('jira-project-search-input');
            const hiddenInput = document.getElementById('jira-project-select');
            const dropdown = document.getElementById('jira-project-dropdown');

            if (searchInput) searchInput.value = '';
            if (hiddenInput) hiddenInput.value = '';
            if (dropdown) dropdown.style.display = 'none';
        },

        /**
         * Valida el email del asignado
         */
        async validateAssignee() {
            const input = document.getElementById('jira-assignee-input');
            const validationDiv = document.getElementById('jira-assignee-validation');
            const email = input.value.trim();

            if (!email) {
                validationDiv.style.display = 'none';
                return;
            }

            // Validar formato
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                validationDiv.style.display = 'block';
                validationDiv.style.color = 'var(--error)';
                validationDiv.textContent = '❌ Formato de email inválido';
                return;
            }

            validationDiv.style.display = 'block';
            validationDiv.style.color = 'var(--text-muted)';
            validationDiv.textContent = '⏳ Validando usuario...';

            try {
                const data = await Api.validateJiraUser(email);
                if (data.valid) {
                    validationDiv.style.color = 'var(--success)';
                    validationDiv.textContent = '✅ Usuario encontrado en Jira';
                    window.assigneeAccountId = data.accountId;
                } else {
                    validationDiv.style.color = 'var(--error)';
                    validationDiv.textContent = '❌ ' + (data.error || 'Este correo no tiene cuenta en Jira');
                    window.assigneeAccountId = null;
                }
            } catch (error) {
                validationDiv.style.color = 'var(--error)';
                validationDiv.textContent = '❌ Error al validar usuario';
                window.assigneeAccountId = null;
            }
        },

        /**
         * Ejecuta la subida a Jira
         */
        async handleUpload() {
            const projectKey = document.getElementById('jira-project-select').value;
            if (!projectKey) {
                window.showDownloadNotification('Por favor selecciona un proyecto', 'error');
                Utils.highlightError('jira-project-search-input');
                return;
            }

            const assigneeEmail = document.getElementById('jira-assignee-input').value.trim();
            const validationDiv = document.getElementById('jira-assignee-validation');

            // Validar asignado si se proporciona y no ha sido validado
            if (assigneeEmail) {
                const isValidated = validationDiv.style.display === 'block' && validationDiv.textContent.includes('✅');
                if (!isValidated) {
                    await this.validateAssignee();
                    const nowValidated = validationDiv.style.display === 'block' && validationDiv.textContent.includes('✅');
                    if (!nowValidated) return;
                }
            }

            // Mostrar loading
            const loadingOverlay = document.getElementById('stories-loading-overlay');
            if (loadingOverlay) loadingOverlay.style.display = 'flex';

            try {
                const data = await Api.uploadToJira('stories', {
                    stories: window.selectedStoriesForUpload,
                    project_key: projectKey,
                    assignee_email: assigneeEmail || null
                });

                if (loadingOverlay) loadingOverlay.style.display = 'none';
                this.closeJiraModal();

                if (data.success) {
                    window.showDownloadNotification(data.message || 'Historias subidas exitosamente a Jira', 'success');

                    // Manejar descarga de archivo TXT si aplica
                    if (data.txt_content && data.txt_filename) {
                        this.downloadSummaryTxt(data.txt_content, data.txt_filename);
                    }
                } else {
                    window.showDownloadNotification('Error: ' + (data.error || 'No se pudieron subir las historias'), 'error');
                    if (data.txt_content && data.txt_filename) {
                        this.downloadSummaryTxt(data.txt_content, data.txt_filename);
                    }
                }
            } catch (error) {
                if (loadingOverlay) loadingOverlay.style.display = 'none';
                window.showDownloadNotification('Error de conexión: ' + error.message, 'error');
            }
        },

        /**
         * Descarga el resumen en TXT
         */
        downloadSummaryTxt(base64Content, filename) {
            try {
                const binaryString = atob(base64Content);
                const bytes = new Uint8Array(binaryString.length);
                for (let i = 0; i < binaryString.length; i++) {
                    bytes[i] = binaryString.charCodeAt(i);
                }
                const blob = new Blob([bytes], { type: 'text/plain;charset=utf-8' });
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = filename;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);
            } catch (error) {
                console.error('Error downloading summary TXT:', error);
            }
        }
    };

    window.NexusModules = NexusModules;
})(window);
