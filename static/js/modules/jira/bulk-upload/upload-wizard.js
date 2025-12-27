/**
 * Nexus AI - Upload Wizard Module (Main Controller)
 * Orchestrates the bulk upload process using sub-modules.
 */

(function (window) {
    'use strict';

    // Ensure namespace exists
    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Jira = window.NexusModules.Jira || {};
    window.NexusModules.Jira.BulkUpload = window.NexusModules.Jira.BulkUpload || {};

    // Imports
    const Api = window.NexusModules.Jira.BulkUpload.Api;
    const FieldMapper = window.NexusModules.Jira.BulkUpload.FieldMapper;
    const ProjectSelector = window.NexusModules.Jira.BulkUpload.ProjectSelector;
    const State = window.NexusModules.Jira.BulkUpload.State;
    const StepNavigator = window.NexusModules.Jira.BulkUpload.StepNavigator;
    const MappingManager = window.NexusModules.Jira.BulkUpload.MappingManager;
    const FileHandler = window.NexusModules.Jira.BulkUpload.FileHandler;
    const CsvParser = window.NexusModules.Jira.BulkUpload.CsvParser; // Keep for preview re-read

    // --- Utility Functions ---

    function switchBulkLoadOperation(type) {
        const hub = document.getElementById('loader-hub');
        const individualView = document.getElementById('individual-load-view');

        if (type === 'individual') {
            if (hub) hub.style.display = 'none';
            if (individualView) individualView.style.display = 'block';
        } else {
            const cardTitle = type === 'folder' ? 'Carga por Carpeta' : 'Validador de Matrices';
            alert(`ℹ️ El módulo "${cardTitle}" estará disponible en próximas actualizaciones.`);
        }
    }

    function resetBulkLoadToHub() {
        const hub = document.getElementById('loader-hub');
        const individualView = document.getElementById('individual-load-view');

        if (hub) hub.style.display = 'block';
        if (individualView) individualView.style.display = 'none';
        resetCargaMasiva();
    }

    function showUploadStatus(type, message) {
        const uploadStatus = document.getElementById('upload-status');
        const uploadStatusIcon = document.getElementById('upload-status-icon');
        const uploadStatusMessage = document.getElementById('upload-status-message');

        if (uploadStatus) {
            uploadStatus.style.display = 'block';
            uploadStatus.className = 'upload-status-card';
            if (type === 'success') uploadStatus.classList.add('success');
            if (type === 'error') uploadStatus.classList.add('error');
        }
        if (uploadStatusIcon) uploadStatusIcon.textContent = type === 'success' ? '✅' : '❌';
        if (uploadStatusMessage) uploadStatusMessage.textContent = message;
    }

    // --- Initialization ---

    async function initCargaMasiva() {
        const hub = document.getElementById('loader-hub');
        const individualView = document.getElementById('individual-load-view');
        if (hub) hub.style.display = 'block';
        if (individualView) individualView.style.display = 'none';

        await Api.loadUserInfo();
        const projectInput = document.getElementById('carga-masiva-project-selector-input');
        const projectsLoading = document.getElementById('carga-masiva-projects-loading');
        const projectsError = document.getElementById('carga-masiva-projects-error');

        if (!projectInput) return;

        if (projectsLoading) projectsLoading.style.display = 'block';
        if (projectsError) projectsError.style.display = 'none';

        try {
            const data = await Api.fetchProjects();

            if (data.success && data.projects.length > 0) {
                const projects = data.projects.map(project => ({
                    key: project.key,
                    name: project.name,
                    displayText: `${project.name} (${project.key})`
                }));
                State.update({ cargaMasivaProjects: projects });

                if (projectsLoading) projectsLoading.style.display = 'none';
            } else {
                if (projectsLoading) projectsLoading.style.display = 'none';
                if (projectsError) {
                    projectsError.style.display = 'block';
                    projectsError.innerHTML = `<span>❌ ${data.error || 'No se encontraron proyectos'}</span>`;
                }
            }
        } catch (error) {
            console.error('Error al cargar proyectos:', error);
            if (projectsLoading) projectsLoading.style.display = 'none';
            if (projectsError) {
                projectsError.style.display = 'block';
                projectsError.innerHTML = `<span>❌ Error: ${error.message}</span>`;
            }
        }

        ProjectSelector.updateAccessMessage(null, '');
        FileHandler.setupDropZone(onFileProcessed, showUploadStatus);
        setupCargaMasivaButtons();
        StepNavigator.goToStep(1, {}); // Init UI
    }

    // --- Dropdown Proxy Logic ---

    function showCargaMasivaDropdown() {
        const state = State.get();
        ProjectSelector.showDropdown(state.cargaMasivaProjects, selectCargaMasivaProject);
    }

    function hideCargaMasivaDropdown() {
        ProjectSelector.hideDropdown();
    }

    function filterCargaMasivaProjects(searchText) {
        const state = State.get();
        ProjectSelector.filterProjects(searchText, state.cargaMasivaProjects, selectCargaMasivaProject);
    }

    function handleCargaMasivaKeydown(event) {
        ProjectSelector.handleKeydown(event, selectCargaMasivaProject);
    }

    async function selectCargaMasivaProject(projectKey, projectName, displayText) {
        const input = document.getElementById('carga-masiva-project-selector-input');
        const hiddenInput = document.getElementById('carga-masiva-project-selector');
        const dropdown = document.getElementById('carga-masiva-dropdown');

        if (input) input.value = displayText;
        if (hiddenInput) hiddenInput.value = projectKey;
        if (dropdown) dropdown.style.display = 'none';

        State.update({ projectAccessState: { status: 'loading', hasAccess: false, message: '' } });
        await Api.loadUserInfo();
        const accessResult = await Api.validateProjectAccess(projectKey);
        State.update({ projectAccessState: accessResult });

        ProjectSelector.updateAccessMessage(accessResult.status === 'done' && accessResult.hasAccess ? 'success' : 'error', accessResult.message);

        const userInfo = Api.getUserInfo();
        const state = State.get();

        if (projectKey && (accessResult.hasAccess || ['admin', 'analista_qa'].includes(userInfo.role || 'usuario'))) {
            StepNavigator.goToStep(2, getStepCallbacks());
            if (state.selectedCsvFile && state.csvColumns.length > 0) {
                setTimeout(() => startValidation(), 500);
            }
        } else {
            StepNavigator.goToStep(1, getStepCallbacks());
        }
    }

    // --- Core Action Logic ---

    function onFileProcessed() {
        const state = State.get();
        StepNavigator.goToStep(2, getStepCallbacks());

        const projectSelector = document.getElementById('carga-masiva-project-selector');
        if (projectSelector && projectSelector.value) {
            setTimeout(() => startValidation(), 500);
        }
    }

    function setupCargaMasivaButtons() {
        // Wiring up local buttons not handled by sub-modules
        const removeFileBtn = document.getElementById('remove-file-btn');
        const projectSelector = document.getElementById('carga-masiva-project-selector');
        const prevStepBtn = document.getElementById('prev-step-btn');
        const revalidateBtn = document.getElementById('revalidate-btn');
        const uploadBtn = document.getElementById('upload-csv-btn');
        const downloadTemplateLink = document.getElementById('download-template-link');

        // Remove old listeners if any (simple approach)
        const newRemoveBtn = removeFileBtn ? removeFileBtn.cloneNode(true) : null;
        if (removeFileBtn && newRemoveBtn) removeFileBtn.parentNode.replaceChild(newRemoveBtn, removeFileBtn);
        if (newRemoveBtn) newRemoveBtn.addEventListener('click', resetCargaMasiva);

        // Re-attach project selector listener
        if (projectSelector) {
            // Cloning to remove old event listeners
            const newProjectSelector = projectSelector.cloneNode(true);
            projectSelector.parentNode.replaceChild(newProjectSelector, projectSelector);

            newProjectSelector.addEventListener('change', async () => {
                await Api.loadUserInfo();
                State.update({ projectAccessState: { status: 'loading', hasAccess: false, message: '' } });
                const accessResult = await Api.validateProjectAccess(newProjectSelector.value);
                State.update({ projectAccessState: accessResult });
                const userInfo = Api.getUserInfo();
                const state = State.get();

                if (newProjectSelector.value && (accessResult.hasAccess || ['admin', 'analista_qa'].includes(userInfo.role || 'usuario'))) {
                    const step = state.currentStep === 1 ? 2 : state.currentStep;
                    StepNavigator.goToStep(step, getStepCallbacks());
                    if (state.selectedCsvFile && state.csvColumns.length > 0) startValidation();
                } else {
                    StepNavigator.goToStep(1, getStepCallbacks());
                }
            });
        }

        // Navigation buttons handled by StepNavigator, except specific actions
        const newRevalidateBtn = revalidateBtn ? revalidateBtn.cloneNode(true) : null;
        if (revalidateBtn && newRevalidateBtn) revalidateBtn.parentNode.replaceChild(newRevalidateBtn, revalidateBtn);
        if (newRevalidateBtn) newRevalidateBtn.addEventListener('click', startValidation);

        const newPrevBtn = prevStepBtn ? prevStepBtn.cloneNode(true) : null;
        if (prevStepBtn && newPrevBtn) prevStepBtn.parentNode.replaceChild(newPrevBtn, prevStepBtn);
        if (newPrevBtn) {
            newPrevBtn.addEventListener('click', () => {
                const state = State.get();
                if (state.currentStep > 1) {
                    StepNavigator.goToStep(state.currentStep - 1, getStepCallbacks());
                }
            });
        }

        const newUploadBtn = uploadBtn ? uploadBtn.cloneNode(true) : null;
        if (uploadBtn && newUploadBtn) uploadBtn.parentNode.replaceChild(newUploadBtn, uploadBtn);
        if (newUploadBtn) newUploadBtn.addEventListener('click', async () => {
            const state = State.get();
            if (state.isUploadingCsv) return;
            await uploadCsvToJira();
        });

        const newDownloadLink = downloadTemplateLink ? downloadTemplateLink.cloneNode(true) : null;
        if (downloadTemplateLink && newDownloadLink) downloadTemplateLink.parentNode.replaceChild(newDownloadLink, downloadTemplateLink);
        if (newDownloadLink) {
            newDownloadLink.addEventListener('click', async (e) => {
                e.preventDefault();
                const sel = document.getElementById('carga-masiva-project-selector');
                const projectKey = sel ? sel.value : null;
                const success = await Api.downloadTemplate(projectKey);
                if (!success) showUploadStatus('error', '❌ Error al descargar la plantilla');
            });
        }
    }

    function getStepCallbacks() {
        return {
            onGoToMapping: () => {
                StepNavigator.goToStep(5, getStepCallbacks());
                renderMappingStep();
            },
            onGoToPreview: () => {
                const projectSelector = document.getElementById('carga-masiva-project-selector');
                const state = State.get();
                const validationErrors = [];

                if (!state.selectedCsvFile) validationErrors.push('📄 Debes cargar un archivo CSV');
                if (!projectSelector || !projectSelector.value) validationErrors.push('📋 Debes seleccionar un proyecto');
                if (state.csvColumns.length === 0) validationErrors.push('📊 El archivo CSV debe tener columnas válidas');

                if (validationErrors.length > 0) {
                    window.showDownloadNotification('⚠️ No puedes continuar a la vista previa:\n\n' + validationErrors.join('\n'), 'error');
                    return;
                }

                renderConfigStep();
                StepNavigator.goToStep(6, getStepCallbacks());
                setTimeout(() => showPreview(), 100);
            },
            onGoToUpload: () => {
                StepNavigator.goToStep(7, getStepCallbacks());
                renderUploadStep();
            }
        };
    }

    // --- Validation & Rendering Wrappers ---

    async function startValidation() {
        const projectSelector = document.getElementById('carga-masiva-project-selector');
        const state = State.get();
        if (!projectSelector || !projectSelector.value || !state.selectedCsvFile || state.csvColumns.length === 0) return;

        const userInfo = Api.getUserInfo();
        if ((userInfo.role || 'usuario') === 'usuario') {
            if (state.projectAccessState.status === 'loading') {
                ProjectSelector.updateAccessMessage('loading', 'Verificando permisos en el proyecto...');
                return;
            }
            if (!state.projectAccessState.hasAccess) {
                ProjectSelector.updateAccessMessage('error', 'No tienes acceso a este proyecto. Contacta al administrador del proyecto en Jira.');
                StepNavigator.goToStep(1, getStepCallbacks());
                return;
            }
        }

        StepNavigator.goToStep(3, getStepCallbacks());

        const validationSteps = document.getElementById('validation-steps');
        if (validationSteps) {
            validationSteps.innerHTML = `
                <div class="validation-step"><span>Leyendo columnas del CSV...</span><span id="step-1-status" style="color: var(--accent);">⏳</span></div>
                <div class="validation-step"><span>Obteniendo campos del proyecto...</span><span id="step-2-status" style="color: var(--text-muted);">⏸</span></div>
                <div class="validation-step"><span>Comparando y buscando coincidencias...</span><span id="step-3-status" style="color: var(--text-muted);">⏸</span></div>
                <div class="validation-step"><span>Generando sugerencias de mapeo...</span><span id="step-4-status" style="color: var(--text-muted);">⏸</span></div>
            `;
        }

        try {
            StepNavigator.updateValidationStep(1, true);
            await new Promise(resolve => setTimeout(resolve, 500));

            StepNavigator.updateValidationStep(2, true);
            const projectKey = projectSelector.value;

            StepNavigator.updateValidationStep(3, true);
            const validationData = await Api.validateCsvFields(state.csvColumns, projectKey);
            State.update({ validationResult: validationData });

            StepNavigator.updateValidationStep(4, true);
            await new Promise(resolve => setTimeout(resolve, 500));

            StepNavigator.goToStep(4, getStepCallbacks());
            await new Promise(resolve => setTimeout(resolve, 100));
            FieldMapper.renderFieldsStep(validationData, state.csvColumns);

        } catch (error) {
            console.error('Error en validación:', error);
            showUploadStatus('error', '❌ Error al validar campos');
        }
    }

    function renderMappingStep() {
        const state = State.get();
        const validationResult = state.validationResult;

        if (!validationResult || !validationResult.success) return;

        // Auto-fill suggested mappings if empty
        if (Object.keys(state.fieldMappings).length === 0) {
            const initialMappings = {};
            validationResult.mappings.forEach(mapping => {
                if (mapping.suggested && mapping.jira_field_id) {
                    initialMappings[mapping.csv_column] = {
                        jira_field_id: mapping.jira_field_id,
                        jira_field_name: mapping.jira_field_name,
                        jira_field_type: mapping.jira_field_type
                    };
                }
            });
            State.update({ fieldMappings: initialMappings });
        }

        FieldMapper.renderMappingTable(
            validationResult,
            state.csvColumns,
            state.csvData,
            State.get().fieldMappings,
            updateFieldMapping
        );
        renderConfigStep();
        MappingManager.setupButtons(() => renderMappingStep(), showUploadStatus);
    }

    function updateFieldMapping(csvColumn, jiraFieldId) {
        const state = State.get();
        const mappings = { ...state.fieldMappings };
        const allFields = [
            ...(state.validationResult.required_fields || []),
            ...(state.validationResult.optional_fields || [])
        ];

        if (jiraFieldId) {
            const field = allFields.find(f => f.id === jiraFieldId);
            if (field) {
                mappings[csvColumn] = {
                    jira_field_id: field.id,
                    jira_field_name: field.name,
                    jira_field_type: field.type
                };
            }
        } else {
            delete mappings[csvColumn];
        }

        State.update({ fieldMappings: mappings });
        renderMappingStep();
    }

    function renderConfigStep() {
        let defaultValues = { ...State.get().defaultValues };

        // Ensure default value is set if not already present
        if (!defaultValues.issue_type) defaultValues.issue_type = 'Story';
        if (defaultValues.priority) delete defaultValues.priority; // Cleanup

        FieldMapper.renderConfigStep(defaultValues, (key, value) => {
            const current = State.get().defaultValues;
            State.update({ defaultValues: { ...current, [key]: value } });
        });

        // Update state to reflect initial defaults if they changed
        State.update({ defaultValues });
    }

    function showPreview() {
        const projectKey = document.getElementById('carga-masiva-project-selector')?.value || 'N/A';
        const state = State.get();
        if (state.selectedCsvFile) {
            // Re-read file to ensure fresh preview
            CsvParser.readFile(state.selectedCsvFile).then(result => {
                FieldMapper.renderPreviewTable(result.data, result.data.length, projectKey);
            });
        } else if (state.csvData.length > 0) {
            FieldMapper.renderPreviewTable(state.csvData, state.csvData.length, projectKey);
        }
    }

    function renderUploadStep() {
        const uploadFinalStatus = document.getElementById('upload-final-status');
        if (!uploadFinalStatus) return;

        const projectKey = document.getElementById('carga-masiva-project-selector')?.value || 'N/A';
        const state = State.get();

        uploadFinalStatus.innerHTML = `
            <div style="text-align: center; padding: 2rem;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🚀</div>
                <div style="font-size: 1.2rem; font-weight: 600; margin-bottom: 0.5rem; color: var(--text-primary);">Listo para Cargar</div>
                <div style="color: var(--text-muted); margin-bottom: 2rem;">Se crearán los issues en el proyecto <strong>${projectKey}</strong> con los mapeos configurados</div>
                <div style="background: var(--secondary-bg); border-radius: 8px; padding: 1.5rem; text-align: left; max-width: 600px; margin: 0 auto;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;"><span style="color: var(--text-secondary);">Proyecto:</span><span style="font-weight: 600; color: var(--text-primary);">${projectKey}</span></div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;"><span style="color: var(--text-secondary);">Archivo CSV:</span><span style="font-weight: 600; color: var(--text-primary);">${state.selectedCsvFile ? state.selectedCsvFile.name : 'N/A'}</span></div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;"><span style="color: var(--text-secondary);">Campos mapeados:</span><span style="font-weight: 600; color: var(--text-primary);">${Object.keys(state.fieldMappings).length}</span></div>
                    <div style="display: flex; justify-content: space-between;"><span style="color: var(--text-secondary);">Valores por defecto:</span><span style="font-weight: 600; color: var(--text-primary);">${Object.keys(state.defaultValues).length}</span></div>
                </div>
            </div>`;
    }

    async function uploadCsvToJira() {
        if (State.get().isUploadingCsv) return;

        const projectSelector = document.getElementById('carga-masiva-project-selector');
        const state = State.get();
        if (!projectSelector || !projectSelector.value || !state.selectedCsvFile) {
            showUploadStatus('error', '❌ Faltan datos para cargar');
            return;
        }

        const userInfo = Api.getUserInfo();
        if ((userInfo.role || 'usuario') === 'usuario') {
            if (state.projectAccessState.status === 'loading') {
                ProjectSelector.updateAccessMessage('loading', 'Verificando permisos en el proyecto...');
                return;
            }
            if (!state.projectAccessState.hasAccess) {
                ProjectSelector.updateAccessMessage('error', 'No tienes acceso a este proyecto. Contacta al administrador del proyecto en Jira.');
                return;
            }
        }

        State.update({ isUploadingCsv: true });

        const uploadStatus = document.getElementById('upload-status');
        const uploadStatusIcon = document.getElementById('upload-status-icon');
        const uploadStatusMessage = document.getElementById('upload-status-message');
        const uploadBtn = document.getElementById('upload-csv-btn');

        if (uploadStatus) {
            uploadStatus.style.display = 'block';
            uploadStatus.className = 'upload-status-card';
        }
        if (uploadStatusIcon) uploadStatusIcon.textContent = '⏳';
        if (uploadStatusMessage) uploadStatusMessage.textContent = 'Procesando archivo CSV...';
        if (uploadBtn) uploadBtn.disabled = true;

        try {
            const data = await Api.uploadCsv(state.selectedCsvFile, projectSelector.value, state.fieldMappings, state.defaultValues);

            if (data.success) {
                if (uploadStatusIcon) uploadStatusIcon.textContent = '✅';
                if (uploadStatusMessage) uploadStatusMessage.textContent = data.message || 'Archivo cargado exitosamente';
                if (uploadStatus) uploadStatus.classList.add('success');

                if (window.NexusModules && window.NexusModules.Dashboard) {
                    await window.NexusModules.Dashboard.refreshMetrics();
                } else if (typeof window.loadJiraMetrics === 'function') {
                    await window.loadJiraMetrics();
                }

                if (data.txt_content && data.txt_filename) {
                    downloadTxtFile(data.txt_content, data.txt_filename);
                }

                if (uploadBtn) uploadBtn.disabled = false;
                setTimeout(() => resetCargaMasiva(), 5000);
            } else {
                throw new Error(data.error || 'Error al cargar el archivo');
            }
        } catch (error) {
            console.error('Error al cargar CSV:', error);
            if (uploadStatusIcon) uploadStatusIcon.textContent = '❌';
            if (uploadStatusMessage) uploadStatusMessage.textContent = `❌ Error: ${error.message}`;
            if (uploadStatus) uploadStatus.classList.add('error');
            if (uploadBtn) uploadBtn.disabled = false;
        } finally {
            State.update({ isUploadingCsv: false });
        }
    }

    function downloadTxtFile(base64Content, filename) {
        try {
            window.showDownloadNotification('Procesando archivo...', 'loading');
            const binaryString = atob(base64Content);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) bytes[i] = binaryString.charCodeAt(i);
            const blob = new Blob([bytes], { type: 'text/plain;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            window.showDownloadNotification('Archivo TXT descargado exitosamente', 'success');
        } catch (error) {
            window.showDownloadNotification('Error al descargar archivo TXT', 'error');
        }
    }

    function resetCargaMasiva() {
        State.reset();
        StepNavigator.resetUI();
        ProjectSelector.updateAccessMessage(null, '');
    }

    // Initialize module interface
    window.NexusModules.Jira.BulkUpload = {
        init: initCargaMasiva,
        reset: resetCargaMasiva,
        switchOperation: switchBulkLoadOperation,
        resetToHub: resetBulkLoadToHub,
        // Optional exports for DOM event handlers
        handlers: {
            showDropdown: showCargaMasivaDropdown,
            hideDropdown: hideCargaMasivaDropdown,
            filterProjects: filterCargaMasivaProjects,
            handleKeydown: handleCargaMasivaKeydown,
            switchOperation: switchBulkLoadOperation,
            resetToHub: resetBulkLoadToHub
        }
    };

    // Global exposes for existing inline HTML/onclick handlers
    window.showCargaMasivaDropdown = showCargaMasivaDropdown;
    window.hideCargaMasivaDropdown = hideCargaMasivaDropdown;
    window.filterCargaMasivaProjects = filterCargaMasivaProjects;
    window.handleCargaMasivaKeydown = handleCargaMasivaKeydown;
    window.switchBulkLoadOperation = switchBulkLoadOperation;
    window.resetBulkLoadToHub = resetBulkLoadToHub;

})(window);
