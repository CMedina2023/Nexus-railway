/**
 * Nexus AI - Jira Bulk Upload Module
 * Handles all logic related to bulk uploading issues to Jira via CSV.
 */

(function (window) {
    'use strict';

    // Ensure namespace exists
    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Jira = window.NexusModules.Jira || {};

    // Module State
    let cargaMasivaEventListeners = {
        uploadBtn: null,
        removeFileBtn: null,
        prevStepBtn: null,
        revalidateBtn: null,
        previewBtn: null,
        downloadTemplateLink: null,
        projectSelector: null
    };

    let isUploadingCsv = false;
    let selectedCsvFile = null;
    let cargaMasivaProjects = [];
    let currentStep = 1;
    let csvColumns = [];
    let csvData = [];
    let validationResult = null;
    let fieldMappings = {};
    let defaultValues = {};
    let currentUserRole = null;
    let currentUserEmail = null;
    let projectAccessState = { status: 'unknown', hasAccess: false, message: '' };
    let cargaMasivaHighlightedIndex = -1;

    // --- Utility Functions ---

    function parseCSV(text) {
        const rows = [];
        let currentRow = [];
        let currentField = '';
        let insideQuotes = false;

        for (let i = 0; i < text.length; i++) {
            const char = text[i];
            const nextChar = text[i + 1];

            if (char === '"') {
                if (insideQuotes && nextChar === '"') {
                    currentField += '"';
                    i++;
                } else {
                    insideQuotes = !insideQuotes;
                }
            } else if (char === ',' && !insideQuotes) {
                currentRow.push(currentField.trim());
                currentField = '';
            } else if ((char === '\n' || char === '\r') && !insideQuotes) {
                if (currentField || currentRow.length > 0) {
                    currentRow.push(currentField.trim());
                    rows.push(currentRow);
                    currentRow = [];
                    currentField = '';
                }
                if (char === '\r' && nextChar === '\n') {
                    i++;
                }
            } else {
                currentField += char;
            }
        }

        if (currentField || currentRow.length > 0) {
            currentRow.push(currentField.trim());
            rows.push(currentRow);
        }

        return rows;
    }

    async function loadCurrentUserInfo() {
        if (currentUserRole) return;
        try {
            const resp = await fetch('/auth/session', { headers: { 'Accept': 'application/json' } });
            if (resp.ok) {
                const data = await resp.json();
                currentUserRole = data.role || 'usuario';
                currentUserEmail = data.email || '';
            } else {
                currentUserRole = 'usuario';
            }
        } catch (e) {
            currentUserRole = 'usuario';
        }
    }

    function updateCargaMasivaAccessMessage(type, message) {
        const msgEl = document.getElementById('carga-masiva-access-message');
        const uploadBtn = document.getElementById('upload-csv-btn');
        if (!msgEl) return;

        if (!message) {
            msgEl.style.display = 'none';
        } else {
            msgEl.style.display = 'block';
            msgEl.textContent = message;
            msgEl.style.color = type === 'error' ? '#ef4444' : type === 'loading' ? 'var(--text-secondary)' : '#22c55e';
        }

        if (uploadBtn) {
            if (type === 'error' || type === 'loading') {
                uploadBtn.disabled = true;
            } else if (type === 'success') {
                uploadBtn.disabled = false;
            }
        }
    }

    async function validateCargaMasivaProjectAccess(projectKey) {
        await loadCurrentUserInfo();

        if (!projectKey) {
            projectAccessState = { status: 'unknown', hasAccess: false, message: '' };
            updateCargaMasivaAccessMessage(null, '');
            return false;
        }

        if (['admin', 'analista_qa'].includes(currentUserRole || 'usuario')) {
            projectAccessState = { status: 'done', hasAccess: true, message: 'Acceso permitido por rol' };
            updateCargaMasivaAccessMessage('success', 'Acceso permitido por rol');
            return true;
        }

        projectAccessState = { status: 'loading', hasAccess: false, message: '' };
        updateCargaMasivaAccessMessage('loading', 'Verificando permisos en el proyecto...');

        try {
            const resp = await fetch('/api/jira/validate-project-access', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.getCsrfToken()
                },
                body: JSON.stringify({ project_key: projectKey, email: currentUserEmail })
            });
            const data = await resp.json();
            const allowed = !!data.hasAccess;
            projectAccessState = { status: 'done', hasAccess: allowed, message: data.message || '' };

            if (allowed) {
                updateCargaMasivaAccessMessage('success', data.message || 'Acceso validado');
            } else {
                updateCargaMasivaAccessMessage('error', data.message || 'No tienes acceso a este proyecto. Contacta al administrador del proyecto en Jira.');
            }
            return allowed;
        } catch (error) {
            projectAccessState = { status: 'error', hasAccess: false, message: error.message };
            updateCargaMasivaAccessMessage('error', 'No se pudo validar el acceso. Intenta nuevamente.');
            return false;
        }
    }

    // --- UI/Flow Management ---

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

    // --- Initialization ---

    async function initCargaMasiva() {
        const hub = document.getElementById('loader-hub');
        const individualView = document.getElementById('individual-load-view');
        if (hub) hub.style.display = 'block';
        if (individualView) individualView.style.display = 'none';

        await loadCurrentUserInfo();
        const projectInput = document.getElementById('carga-masiva-project-selector-input');
        const projectsLoading = document.getElementById('carga-masiva-projects-loading');
        const projectsError = document.getElementById('carga-masiva-projects-error');

        if (!projectInput) return;

        if (projectsLoading) projectsLoading.style.display = 'block';
        if (projectsError) projectsError.style.display = 'none';

        try {
            const response = await fetch('/api/jira/projects');
            const data = await response.json();

            if (data.success && data.projects.length > 0) {
                cargaMasivaProjects = data.projects.map(project => ({
                    key: project.key,
                    name: project.name,
                    displayText: `${project.name} (${project.key})`
                }));
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

        projectAccessState = { status: 'unknown', hasAccess: false, message: '' };
        updateCargaMasivaAccessMessage(null, '');
        setupDropZone();
        setupCargaMasivaButtons();
        updateStepIndicator(1);
    }

    // --- Dropdown Logic ---

    function renderCargaMasivaOptions(projects) {
        const dropdown = document.getElementById('carga-masiva-dropdown');
        if (!dropdown) return;

        if (!projects || projects.length === 0) {
            dropdown.innerHTML = '<div class="combobox-option no-results">No se encontraron proyectos</div>';
            dropdown.style.display = 'block';
            return;
        }

        dropdown.innerHTML = '';
        projects.forEach((project) => {
            const option = document.createElement('div');
            option.className = 'combobox-option';
            option.textContent = project.displayText;
            option.dataset.projectKey = project.key;
            option.dataset.projectName = project.name;
            option.onclick = () => selectCargaMasivaProject(project.key, project.name, project.displayText);
            dropdown.appendChild(option);
        });

        dropdown.style.display = 'block';
        cargaMasivaHighlightedIndex = -1;
    }

    function filterCargaMasivaProjects(searchText) {
        if (!cargaMasivaProjects || cargaMasivaProjects.length === 0) return;

        const searchLower = searchText.toLowerCase().trim();
        if (searchLower === '') {
            renderCargaMasivaOptions(cargaMasivaProjects);
            return;
        }

        const filtered = cargaMasivaProjects.filter(project =>
            project.name.toLowerCase().includes(searchLower) ||
            project.key.toLowerCase().includes(searchLower) ||
            project.displayText.toLowerCase().includes(searchLower)
        );

        renderCargaMasivaOptions(filtered);
    }

    function showCargaMasivaDropdown() {
        const dropdown = document.getElementById('carga-masiva-dropdown');
        const input = document.getElementById('carga-masiva-project-selector-input');
        if (!dropdown || !input) return;

        if (!cargaMasivaProjects || cargaMasivaProjects.length === 0) return;

        const searchText = input.value.trim();
        if (searchText === '') {
            renderCargaMasivaOptions(cargaMasivaProjects);
        } else {
            filterCargaMasivaProjects(searchText);
        }
    }

    function hideCargaMasivaDropdown() {
        setTimeout(() => {
            const dropdown = document.getElementById('carga-masiva-dropdown');
            if (dropdown) dropdown.style.display = 'none';
            cargaMasivaHighlightedIndex = -1;
        }, 200);
    }

    async function selectCargaMasivaProject(projectKey, projectName, displayText) {
        const input = document.getElementById('carga-masiva-project-selector-input');
        const hiddenInput = document.getElementById('carga-masiva-project-selector');
        const dropdown = document.getElementById('carga-masiva-dropdown');

        if (input) input.value = displayText;
        if (hiddenInput) hiddenInput.value = projectKey;
        if (dropdown) dropdown.style.display = 'none';

        projectAccessState = { status: 'loading', hasAccess: false, message: '' };
        await loadCurrentUserInfo();
        const allowed = await validateCargaMasivaProjectAccess(projectKey);

        if (projectKey && (allowed || ['admin', 'analista_qa'].includes(currentUserRole || 'usuario'))) {
            goToStep(2);
            if (selectedCsvFile && csvColumns.length > 0) {
                setTimeout(() => startValidation(), 500);
            }
        } else {
            goToStep(1);
        }
    }

    function handleCargaMasivaKeydown(event) {
        const dropdown = document.getElementById('carga-masiva-dropdown');
        if (!dropdown || dropdown.style.display === 'none') return;

        const options = dropdown.querySelectorAll('.combobox-option:not(.no-results)');
        if (options.length === 0) return;

        if (event.key === 'ArrowDown') {
            event.preventDefault();
            cargaMasivaHighlightedIndex = (cargaMasivaHighlightedIndex + 1) % options.length;
            updateCargaMasivaHighlight(options);
        } else if (event.key === 'ArrowUp') {
            event.preventDefault();
            cargaMasivaHighlightedIndex = cargaMasivaHighlightedIndex <= 0 ? options.length - 1 : cargaMasivaHighlightedIndex - 1;
            updateCargaMasivaHighlight(options);
        } else if (event.key === 'Enter') {
            event.preventDefault();
            if (cargaMasivaHighlightedIndex >= 0 && cargaMasivaHighlightedIndex < options.length) {
                const option = options[cargaMasivaHighlightedIndex];
                selectCargaMasivaProject(
                    option.dataset.projectKey,
                    option.dataset.projectName,
                    option.textContent
                );
            }
        } else if (event.key === 'Escape') {
            dropdown.style.display = 'none';
            cargaMasivaHighlightedIndex = -1;
        }
    }

    function updateCargaMasivaHighlight(options) {
        options.forEach((option, index) => {
            if (index === cargaMasivaHighlightedIndex) {
                option.classList.add('highlighted');
                option.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
            } else {
                option.classList.remove('highlighted');
            }
        });
    }

    // --- File Handling ---

    function setupDropZone() {
        const dropZone = document.getElementById('csv-drop-zone');
        const fileInput = document.getElementById('csv-file-input');

        if (!dropZone || !fileInput) return;

        dropZone.addEventListener('mousedown', (e) => {
            if (e.target === dropZone || e.target.closest('.drop-zone-content')) {
                e.preventDefault();
                fileInput.click();
            }
        });

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('drag-over');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFileSelect(files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFileSelect(e.target.files[0]);
            }
        });
    }

    async function handleFileSelect(file) {
        if (!file.name.toLowerCase().endsWith('.csv')) {
            showUploadStatus('error', '❌ Solo se permiten archivos CSV');
            return;
        }

        selectedCsvFile = file;
        const fileInfo = document.getElementById('file-info');
        const fileName = document.getElementById('file-name');

        if (fileInfo && fileName) {
            fileName.textContent = file.name;
            fileInfo.style.display = 'flex';
        }

        try {
            const text = await file.text();
            const lines = text.split('\n');
            if (lines.length > 0) {
                csvColumns = lines[0].split(',').map(col => col.trim().replace(/^"|"$/g, ''));
                const reader = new FileReader();
                reader.onload = async (e) => {
                    const csvText = e.target.result;
                    const parsed = parseCSV(csvText);
                    if (parsed.length > 0) {
                        const headers = parsed[0];
                        csvData = [];
                        for (let i = 1; i < Math.min(parsed.length, 6); i++) {
                            if (parsed[i] && parsed[i].length > 0) {
                                const row = {};
                                headers.forEach((h, idx) => {
                                    row[h] = parsed[i][idx] || '';
                                });
                                csvData.push(row);
                            }
                        }
                    }
                };
                reader.readAsText(file, 'UTF-8');
            }

            goToStep(2);
            const projectSelector = document.getElementById('carga-masiva-project-selector');
            if (projectSelector && projectSelector.value) {
                setTimeout(() => startValidation(), 500);
            }
        } catch (error) {
            console.error('Error al leer CSV:', error);
            showUploadStatus('error', '❌ Error al leer el archivo CSV');
        }
    }

    // --- Buttons & Steps ---

    function setupCargaMasivaButtons() {
        const removeFileBtn = document.getElementById('remove-file-btn');
        const projectSelector = document.getElementById('carga-masiva-project-selector');
        const downloadTemplateLink = document.getElementById('download-template-link');
        const prevStepBtn = document.getElementById('prev-step-btn');
        const revalidateBtn = document.getElementById('revalidate-btn');
        const previewBtn = document.getElementById('preview-btn');
        const uploadBtn = document.getElementById('upload-csv-btn');

        if (cargaMasivaEventListeners.removeFileBtn && removeFileBtn) removeFileBtn.removeEventListener('click', cargaMasivaEventListeners.removeFileBtn);
        if (cargaMasivaEventListeners.projectId && projectSelector) projectSelector.removeEventListener('change', cargaMasivaEventListeners.projectSelector);

        // Clean previous listeners
        // (Since we are using an object to track them, we can just overwrite them if we re-run this setup, 
        // essentially implementing a fresh bind)

        if (removeFileBtn) {
            removeFileBtn.addEventListener('click', resetCargaMasiva);
        }

        if (projectSelector) {
            projectSelector.addEventListener('change', async () => {
                await loadCurrentUserInfo();
                projectAccessState = { status: 'loading', hasAccess: false, message: '' };
                const allowed = await validateCargaMasivaProjectAccess(projectSelector.value);

                if (projectSelector.value && (allowed || ['admin', 'analista_qa'].includes(currentUserRole || 'usuario'))) {
                    if (currentStep === 1) goToStep(2);
                    if (selectedCsvFile && csvColumns.length > 0) startValidation();
                } else {
                    goToStep(1);
                }
            });
        }

        if (prevStepBtn) {
            prevStepBtn.addEventListener('click', () => {
                if (currentStep > 1) goToStep(currentStep - 1);
            });
        }

        if (revalidateBtn) {
            revalidateBtn.addEventListener('click', startValidation);
        }

        if (uploadBtn) {
            uploadBtn.addEventListener('click', async () => {
                if (isUploadingCsv) return;
                await uploadCsvToJira();
            });
        }

        if (downloadTemplateLink) {
            downloadTemplateLink.addEventListener('click', async (e) => {
                e.preventDefault();
                try {
                    const projectKey = projectSelector ? projectSelector.value : null;
                    let url = '/api/jira/download-template';
                    if (projectKey) url += `?project_key=${encodeURIComponent(projectKey)}`;

                    const response = await fetch(url);
                    if (response.ok) {
                        const blob = await response.blob();
                        const url_obj = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url_obj;
                        a.download = 'plantilla_carga_masiva_jira.csv';
                        document.body.appendChild(a);
                        a.click();
                        window.URL.revokeObjectURL(url_obj);
                        document.body.removeChild(a);
                    } else {
                        showUploadStatus('error', '❌ Error al descargar la plantilla');
                    }
                } catch (error) {
                    showUploadStatus('error', '❌ Error al descargar la plantilla');
                }
            });
        }
    }

    function goToStep(step) {
        currentStep = step;
        updateStepIndicator(step);
        showStepContent(step);
        updateActionsBar(step);
    }

    function updateStepIndicator(step) {
        const steps = document.querySelectorAll('.step');
        steps.forEach((s, idx) => {
            const stepNum = parseInt(s.dataset.step || idx + 1);
            s.classList.remove('active', 'completed');
            if (stepNum < step) {
                s.classList.add('completed');
            } else if (stepNum === step) {
                s.classList.add('active');
            }
        });
    }

    function showStepContent(step) {
        for (let i = 1; i <= 7; i++) {
            const content = document.getElementById(`step-${i}-content`);
            if (content) {
                content.style.display = 'none';
                content.classList.remove('active');
            }
        }
        const currentContent = document.getElementById(`step-${step}-content`);
        if (currentContent) {
            currentContent.style.display = 'block';
            currentContent.classList.add('active');
        }
    }

    function updateActionsBar(step) {
        const actionsBar = document.getElementById('carga-masiva-actions');
        const prevBtn = document.getElementById('prev-step-btn');
        const revalidateBtn = document.getElementById('revalidate-btn');
        const uploadBtn = document.getElementById('upload-csv-btn');

        if (!actionsBar) return;

        actionsBar.style.display = step >= 2 ? 'flex' : 'none';

        if (prevBtn) prevBtn.style.display = step > 1 ? 'inline-flex' : 'none';
        if (revalidateBtn) revalidateBtn.style.display = (step >= 4 && step <= 5) ? 'inline-flex' : 'none';
        if (uploadBtn) uploadBtn.style.display = step === 7 ? 'inline-flex' : 'none';

        const nextBtn = document.getElementById('next-step-btn');
        if (nextBtn) nextBtn.remove();

        if (step === 4 || step === 5 || step === 6) {
            const nextButton = document.createElement('button');
            nextButton.id = 'next-step-btn';
            nextButton.className = 'btn btn-primary';
            nextButton.textContent = step === 4 ? 'Continuar al Mapeo →' :
                step === 5 ? 'Continuar a Vista Previa →' : 'Continuar a Carga →';

            nextButton.onclick = () => {
                if (step === 4) {
                    goToStep(5);
                    renderMappingStep();
                } else if (step === 5) {
                    const projectSelector = document.getElementById('carga-masiva-project-selector');
                    const validationErrors = [];

                    if (!selectedCsvFile) validationErrors.push('📄 Debes cargar un archivo CSV');
                    if (!projectSelector || !projectSelector.value) validationErrors.push('📋 Debes seleccionar un proyecto');
                    if (csvColumns.length === 0) validationErrors.push('📊 El archivo CSV debe tener columnas válidas');

                    if (validationErrors.length > 0) {
                        window.showDownloadNotification('⚠️ No puedes continuar a la vista previa:\n\n' + validationErrors.join('\n'), 'error');
                        return;
                    }

                    renderConfigStep();
                    goToStep(6);
                    setTimeout(() => showPreview(), 100);
                } else if (step === 6) {
                    goToStep(7);
                    renderUploadStep();
                }
            };

            const actionsRight = actionsBar.querySelector('.actions-right');
            if (actionsRight) actionsRight.insertBefore(nextButton, actionsRight.firstChild);
        }
    }

    // --- Validation & Rendering ---

    async function startValidation() {
        const projectSelector = document.getElementById('carga-masiva-project-selector');
        if (!projectSelector || !projectSelector.value || !selectedCsvFile || csvColumns.length === 0) return;

        if ((currentUserRole || 'usuario') === 'usuario') {
            if (projectAccessState.status === 'loading') {
                updateCargaMasivaAccessMessage('loading', 'Verificando permisos en el proyecto...');
                return;
            }
            if (!projectAccessState.hasAccess) {
                updateCargaMasivaAccessMessage('error', 'No tienes acceso a este proyecto. Contacta al administrador del proyecto en Jira.');
                goToStep(1);
                return;
            }
        }

        goToStep(3);

        const validationSteps = document.getElementById('validation-steps');
        if (validationSteps) {
            validationSteps.innerHTML = `
                <div class="validation-step">
                    <span>Leyendo columnas del CSV...</span>
                    <span id="step-1-status" style="color: var(--accent);">⏳</span>
                </div>
                <div class="validation-step">
                    <span>Obteniendo campos del proyecto...</span>
                    <span id="step-2-status" style="color: var(--text-muted);">⏸</span>
                </div>
                <div class="validation-step">
                    <span>Comparando y buscando coincidencias...</span>
                    <span id="step-3-status" style="color: var(--text-muted);">⏸</span>
                </div>
                <div class="validation-step">
                    <span>Generando sugerencias de mapeo...</span>
                    <span id="step-4-status" style="color: var(--text-muted);">⏸</span>
                </div>
            `;
        }

        try {
            updateValidationStep(1, true);
            await new Promise(resolve => setTimeout(resolve, 500));

            updateValidationStep(2, true);
            const projectKey = projectSelector.value;

            updateValidationStep(3, true);
            const validationResponse = await fetch('/api/jira/validate-csv-fields', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.getCsrfToken()
                },
                body: JSON.stringify({
                    csv_columns: csvColumns,
                    project_key: projectKey
                })
            });

            const validationData = await validationResponse.json();
            validationResult = validationData;

            updateValidationStep(4, true);
            await new Promise(resolve => setTimeout(resolve, 500));

            goToStep(4);
            await new Promise(resolve => setTimeout(resolve, 100));
            renderFieldsStep();

        } catch (error) {
            console.error('Error en validación:', error);
            showUploadStatus('error', '❌ Error al validar campos');
        }
    }

    function updateValidationStep(stepNum, completed) {
        const statusEl = document.getElementById(`step-${stepNum}-status`);
        if (statusEl) {
            statusEl.textContent = completed ? '✓' : '⏳';
            statusEl.style.color = completed ? 'var(--success)' : 'var(--accent)';
        }
    }

    function renderFieldsStep() {
        if (!validationResult || !validationResult.success) return;

        const summaryEl = document.getElementById('validation-summary');
        const requiredSection = document.getElementById('required-fields-section');
        const optionalSection = document.getElementById('optional-fields-section');
        const unmappedSection = document.getElementById('unmapped-csv-columns');

        const mappedCount = validationResult.mappings.filter(m => m.suggested).length;
        const totalColumns = csvColumns.length;
        if (summaryEl) {
            summaryEl.className = 'validation-summary success';
            summaryEl.style.display = 'block';
            summaryEl.textContent = `✓ Validación completada. Se encontraron ${mappedCount} coincidencias automáticas de ${totalColumns} columnas.`;
        }

        const filteredRequiredFields = (validationResult.required_fields || []).filter(f => {
            const fieldId = f.id ? f.id.toLowerCase() : '';
            const fieldName = f.name ? f.name.toLowerCase() : '';
            return fieldId !== 'project' && fieldName !== 'project' && fieldName !== 'proyecto';
        });

        if (requiredSection) {
            if (filteredRequiredFields.length > 0) {
                requiredSection.innerHTML = `
                    <h3 style="font-size: 1.1rem; font-weight: 600; margin-bottom: 1rem; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
                        <span>⚠️</span><span>Campos Requeridos de Jira</span>
                    </h3>
                    <div style="background: var(--secondary-bg); border-radius: 8px; padding: 1rem;">
                        ${renderFieldList(filteredRequiredFields, validationResult.mappings)}
                    </div>`;
            } else {
                requiredSection.innerHTML = `
                    <h3 style="font-size: 1.1rem; font-weight: 600; margin-bottom: 1rem; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
                        <span>⚠️</span><span>Campos Requeridos de Jira</span>
                    </h3>
                    <div style="background: var(--secondary-bg); border-radius: 8px; padding: 1rem; text-align: center; color: var(--text-muted);">
                        No hay campos requeridos adicionales (Project ya está seleccionado)
                    </div>`;
            }
        }

        const filteredOptionalFields = (validationResult.optional_fields || []).filter(f => {
            const fieldId = f.id ? f.id.toLowerCase() : '';
            const fieldName = f.name ? f.name.toLowerCase() : '';
            return fieldId !== 'project' && fieldName !== 'project' && fieldName !== 'proyecto';
        });

        if (optionalSection) {
            optionalSection.innerHTML = `
                <h3 style="font-size: 1.1rem; font-weight: 600; margin-bottom: 1rem; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
                    <span>ℹ️</span><span>Campos Opcionales de Jira (${filteredOptionalFields.length} disponibles)</span>
                </h3>
                <div style="background: var(--secondary-bg); border-radius: 8px; padding: 1rem; max-height: 400px; overflow-y: auto;">
                    ${filteredOptionalFields.length > 0
                    ? renderFieldList(filteredOptionalFields, validationResult.mappings)
                    : '<div style="text-align: center; color: var(--text-muted);">No hay campos opcionales disponibles</div>'}
                </div>`;
        }

        const unmappedCols = (validationResult.unmapped_csv_columns || []).filter(col => {
            const colLower = col.toLowerCase();
            return colLower !== 'priority' && colLower !== 'prioridad';
        });

        if (unmappedSection && unmappedCols.length > 0) {
            unmappedSection.innerHTML = `
                <h3 style="font-size: 1.1rem; font-weight: 600; margin-bottom: 1rem; color: var(--warning); display: flex; align-items: center; gap: 0.5rem;">
                    <span>⚠️</span><span>Columnas del CSV sin Equivalente en Jira</span>
                </h3>
                <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid var(--warning); border-radius: 8px; padding: 1rem;">
                    ${unmappedCols.map(col => `
                        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem;">
                            <span style="color: var(--warning);">⚠</span>
                            <div>
                                <div style="font-weight: 600; color: var(--text-primary);">${col}</div>
                                <div style="font-size: 0.85rem; color: var(--text-muted);">Esta columna se ignorará al cargar</div>
                            </div>
                        </div>`).join('')}
                </div>`;
        } else if (unmappedSection) {
            unmappedSection.innerHTML = '';
        }
    }

    function renderFieldList(fields, mappings) {
        return fields.map(field => {
            const mapping = mappings.find(m => m.jira_field_id === field.id && m.suggested);
            const mapped = !!mapping;

            return `
                <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.75rem; background: ${mapped ? 'rgba(16, 185, 129, 0.1)' : 'rgba(59, 130, 246, 0.1)'}; border: 1px solid ${mapped ? 'var(--success)' : 'var(--accent)'}; border-radius: 6px; margin-bottom: 0.75rem;">
                    <div style="display: flex; align-items: center; gap: 0.75rem; flex: 1;">
                        <span style="color: ${mapped ? 'var(--success)' : 'var(--accent)'}; font-size: 1.2rem; font-weight: bold;">${mapped ? '✓' : '○'}</span>
                        <div style="flex: 1;">
                            <div style="font-weight: 600; color: var(--text-primary); font-size: 0.95rem; margin-bottom: 0.25rem;">${field.name || 'Campo sin nombre'}</div>
                            <div style="font-size: 0.85rem; color: var(--text-muted);">${mapped ? `Mapeado desde: "${mapping.csv_column}"` : 'Disponible para mapear'}</div>
                        </div>
                    </div>
                </div>`;
        }).join('');
    }

    function getFieldTypeIcon(type) {
        const icons = {
            'texto': '📝', 'número': '🔢', 'fecha': '📅', 'usuario': '👤',
            'opción': '📋', 'lista': '📋', 'prioridad': '⚡', 'estado': '📊'
        };
        return icons[type] || '📄';
    }

    function renderMappingStep() {
        if (!validationResult || !validationResult.success) return;

        const mappingContainer = document.getElementById('mapping-table-container');
        const summaryEl = document.getElementById('mapping-validation-summary');

        if (!mappingContainer) return;

        if (Object.keys(fieldMappings).length === 0) {
            validationResult.mappings.forEach(mapping => {
                if (mapping.suggested && mapping.jira_field_id) {
                    fieldMappings[mapping.csv_column] = {
                        jira_field_id: mapping.jira_field_id,
                        jira_field_name: mapping.jira_field_name,
                        jira_field_type: mapping.jira_field_type
                    };
                }
            });
        }

        const allFields = [
            ...(validationResult.required_fields || []),
            ...(validationResult.optional_fields || [])
        ].filter(f => {
            const fieldId = f.id ? f.id.toLowerCase() : '';
            const fieldName = f.name ? f.name.toLowerCase() : '';
            return fieldId !== 'project' && fieldName !== 'project' && fieldName !== 'proyecto';
        });

        const requiredFieldsToCheck = (validationResult.required_fields || []).filter(f => {
            const fieldId = f.id ? f.id.toLowerCase() : '';
            const fieldName = f.name ? f.name.toLowerCase() : '';
            return fieldId !== 'project' && fieldName !== 'project' && fieldName !== 'proyecto';
        });

        const requiredMapped = requiredFieldsToCheck.every(req => {
            return Object.values(fieldMappings).some(m => m.jira_field_id === req.id);
        });

        if (summaryEl) {
            summaryEl.className = requiredMapped ? 'validation-summary success' : 'validation-summary warning';
            summaryEl.style.display = 'block';
            summaryEl.textContent = requiredMapped
                ? '✓ Mapeo válido. Todos los campos requeridos están mapeados.'
                : '⚠ Algunos campos requeridos no están mapeados. Revisa los mapeos antes de continuar.';
        }

        let tableHTML = `
            <table class="mapping-table">
                <thead>
                    <tr>
                        <th style="width: 25%;">Columna CSV</th>
                        <th style="width: 35%;">Campo de Jira</th>
                        <th style="width: 15%;">Tipo</th>
                        <th style="width: 10%;">Requerido</th>
                        <th style="width: 15%;">Estado</th>
                    </tr>
                </thead>
                <tbody>`;

        csvColumns.forEach(csvCol => {
            const csvColLower = csvCol.toLowerCase();
            if (csvColLower === 'project' || csvColLower === 'proyecto' || csvColLower === 'project key') return;

            const currentMapping = fieldMappings[csvCol];
            const suggestedMapping = validationResult.mappings.find(m => m.csv_column === csvCol && !m.skip);
            const isRequired = suggestedMapping && suggestedMapping.required;
            const mappedField = currentMapping
                ? allFields.find(f => f.id === currentMapping.jira_field_id)
                : null;

            tableHTML += `
                <tr>
                    <td>
                        <div class="csv-column">${csvCol}</div>
                        ${csvData.length > 0 && csvData[0][csvCol] ?
                    `<div class="csv-sample">Ejemplo: "${String(csvData[0][csvCol]).substring(0, 30)}${String(csvData[0][csvCol]).length > 30 ? '...' : ''}"</div>` : ''}
                    </td>
                    <td>
                        <select class="jira-field-select" data-csv-column="${csvCol}" style="color: var(--text-primary); background: var(--primary-bg);">
                            <option value="" style="color: var(--text-muted); background: var(--primary-bg);">-- No mapear --</option>
                            ${allFields.map(field => {
                        const selected = currentMapping && currentMapping.jira_field_id === field.id;
                        const suggested = suggestedMapping && suggestedMapping.jira_field_id === field.id;
                        return `<option value="${field.id}" ${selected ? 'selected' : ''} style="color: var(--text-primary); background: var(--primary-bg);">${field.name || 'Campo sin nombre'}${suggested ? ' ✓' : ''}</option>`;
                    }).join('')}
                        </select>
                    </td>
                    <td>${mappedField ? `<span class="field-type-badge">${getFieldTypeIcon(mappedField.type)} ${mappedField.type}</span>` : '<span style="color: var(--text-muted);">-</span>'}</td>
                    <td>${isRequired ? '<span class="required-badge">⚠ Requerido</span>' : '<span style="color: var(--text-muted); font-size: 0.85rem;">Opcional</span>'}</td>
                    <td>
                        <div class="mapping-status ${mappedField ? 'status-valid' : 'status-warning'}">
                            <span>${mappedField ? '✓' : '○'}</span>
                            <span>${mappedField ? 'Válido' : 'Sin mapear'}</span>
                        </div>
                    </td>
                </tr>`;
        });

        tableHTML += '</tbody></table>';
        mappingContainer.innerHTML = tableHTML;

        // Add Listeners to selects manually after innerHTML update
        const selects = mappingContainer.querySelectorAll('.jira-field-select');
        selects.forEach(select => {
            select.addEventListener('change', (e) => {
                updateFieldMapping(e.target.dataset.csvColumn, e.target.value);
            });
        });

        renderConfigStep();
        setupMappingButtons();
    }

    function updateFieldMapping(csvColumn, jiraFieldId) {
        const allFields = [
            ...(validationResult.required_fields || []),
            ...(validationResult.optional_fields || [])
        ];

        if (jiraFieldId) {
            const field = allFields.find(f => f.id === jiraFieldId);
            if (field) {
                fieldMappings[csvColumn] = {
                    jira_field_id: field.id,
                    jira_field_name: field.name,
                    jira_field_type: field.type
                };
            }
        } else {
            delete fieldMappings[csvColumn];
        }
        renderMappingStep();
    }

    function setupMappingButtons() {
        const saveMappingBtn = document.getElementById('save-mapping-btn');
        const loadMappingBtn = document.getElementById('load-mapping-btn');
        if (saveMappingBtn) saveMappingBtn.onclick = saveMapping;
        if (loadMappingBtn) loadMappingBtn.onclick = loadMapping;
    }

    function saveMapping() {
        const projectSelector = document.getElementById('carga-masiva-project-selector');
        if (!projectSelector || !projectSelector.value) {
            showUploadStatus('error', '❌ Debes seleccionar un proyecto');
            return;
        }

        const mappingData = {
            project_key: projectSelector.value,
            field_mappings: fieldMappings,
            default_values: defaultValues,
            csv_columns: csvColumns,
            saved_at: new Date().toISOString()
        };

        const mappingName = prompt('Ingresa un nombre para este mapeo:');
        if (!mappingName) return;

        try {
            const savedMappings = JSON.parse(localStorage.getItem('jira_field_mappings') || '{}');
            savedMappings[mappingName] = mappingData;
            localStorage.setItem('jira_field_mappings', JSON.stringify(savedMappings));
            showUploadStatus('success', '✅ Mapeo guardado exitosamente');
        } catch (error) {
            console.error('Error al guardar mapeo:', error);
            showUploadStatus('error', '❌ Error al guardar el mapeo');
        }
    }

    function loadMapping() {
        const projectSelector = document.getElementById('carga-masiva-project-selector');
        if (!projectSelector || !projectSelector.value) {
            showUploadStatus('error', '❌ Debes seleccionar un proyecto');
            return;
        }

        try {
            const savedMappings = JSON.parse(localStorage.getItem('jira_field_mappings') || '{}');
            const mappingNames = Object.keys(savedMappings);
            if (mappingNames.length === 0) {
                showUploadStatus('error', '❌ No hay mapeos guardados');
                return;
            }

            const projectMappings = mappingNames.filter(name => savedMappings[name].project_key === projectSelector.value);
            if (projectMappings.length === 0) {
                showUploadStatus('error', '❌ No hay mapeos guardados para este proyecto');
                return;
            }

            const mappingName = prompt(`Mapeos disponibles:\n${projectMappings.join('\n')}\n\nIngresa el nombre del mapeo a cargar:`);
            if (!mappingName || !savedMappings[mappingName]) return;

            const mappingData = savedMappings[mappingName];
            if (mappingData.project_key !== projectSelector.value) {
                showUploadStatus('error', '❌ Este mapeo no corresponde al proyecto seleccionado');
                return;
            }

            fieldMappings = mappingData.field_mappings || {};
            defaultValues = mappingData.default_values || {};
            renderMappingStep();
            showUploadStatus('success', '✅ Mapeo cargado exitosamente');
        } catch (error) {
            console.error('Error al cargar mapeo:', error);
            showUploadStatus('error', '❌ Error al cargar el mapeo');
        }
    }

    function renderConfigStep() {
        const configPanel = document.getElementById('config-panel');
        if (!configPanel) return;

        configPanel.innerHTML = `
            <div class="form-group">
                <label class="form-label">Tipo de Issue por Defecto</label>
                <select class="form-select" id="default-issue-type" style="color: var(--text-primary); background: var(--secondary-bg);">
                    <option value="Story" ${defaultValues.issue_type === 'Story' || !defaultValues.issue_type ? 'selected' : ''} style="color: var(--text-primary); background: var(--secondary-bg);">Story</option>
                    <option value="Bug" ${defaultValues.issue_type === 'Bug' ? 'selected' : ''} style="color: var(--text-primary); background: var(--secondary-bg);">Bug</option>
                    <option value="Task" ${defaultValues.issue_type === 'Task' ? 'selected' : ''} style="color: var(--text-primary); background: var(--secondary-bg);">Task</option>
                    <option value="Epic" ${defaultValues.issue_type === 'Epic' ? 'selected' : ''} style="color: var(--text-primary); background: var(--secondary-bg);">Epic</option>
                </select>
                <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem;">Se usará si no se mapea el campo "Tipo de Issue"</div>
            </div>`;

        // Ensure default value is set if not already present
        if (!defaultValues.issue_type) {
            defaultValues.issue_type = 'Story';
        }

        const issueTypeSelect = document.getElementById('default-issue-type');
        if (issueTypeSelect) {
            issueTypeSelect.addEventListener('change', (e) => defaultValues.issue_type = e.target.value);
        }

        if (defaultValues.priority) delete defaultValues.priority;
    }

    function showPreview() {
        if (selectedCsvFile) {
            const reader = new FileReader();
            reader.onload = (e) => {
                const parsed = parseCSV(e.target.result);
                if (parsed.length > 1) {
                    const headers = parsed[0];
                    const previewData = [];
                    for (let i = 1; i < Math.min(parsed.length, 6); i++) {
                        if (parsed[i] && parsed[i].length > 0) {
                            const row = {};
                            headers.forEach((h, idx) => row[h] = parsed[i][idx] || '');
                            previewData.push(row);
                        }
                    }
                    renderPreviewTable(previewData, parsed.length - 1);
                }
            };
            reader.readAsText(selectedCsvFile, 'UTF-8');
        } else if (csvData.length > 0) {
            renderPreviewTable(csvData, csvData.length);
        }
    }

    function renderPreviewTable(data, totalRows) {
        const previewSummary = document.getElementById('preview-summary');
        const previewTable = document.getElementById('preview-table-container');

        if (previewSummary) {
            const projectKey = document.getElementById('carga-masiva-project-selector')?.value || 'N/A';
            previewSummary.innerHTML = `<div style="padding: 1rem; background: rgba(16, 185, 129, 0.1); border: 1px solid var(--success); border-radius: 8px; color: var(--success); margin-bottom: 1rem;">✓ Se crearán <strong>${totalRows}</strong> issues en el proyecto <strong>${projectKey}</strong></div>`;
        }

        if (previewTable && data.length > 0) {
            const headers = Object.keys(data[0] || {});
            let tableHTML = `
                <table class="preview-table">
                    <thead><tr><th>#</th>${headers.map(h => `<th>${h}</th>`).join('')}<th>Estado</th></tr></thead>
                    <tbody>`;

            data.slice(0, 5).forEach((row, idx) => {
                tableHTML += `<tr><td>${idx + 1}</td>${headers.map(h => `<td>${String(row[h] || '-').substring(0, 50)}${String(row[h] || '').length > 50 ? '...' : ''}</td>`).join('')}<td><span style="color: var(--success);">✓</span></td></tr>`;
            });

            if (totalRows > 5) tableHTML += `<tr><td colspan="${headers.length + 2}" style="text-align: center; color: var(--text-muted);">... y ${totalRows - 5} más</td></tr>`;
            tableHTML += '</tbody></table>';
            previewTable.innerHTML = tableHTML;
        }
    }

    function renderUploadStep() {
        const uploadFinalStatus = document.getElementById('upload-final-status');
        if (!uploadFinalStatus) return;

        const projectKey = document.getElementById('carga-masiva-project-selector')?.value || 'N/A';
        uploadFinalStatus.innerHTML = `
            <div style="text-align: center; padding: 2rem;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🚀</div>
                <div style="font-size: 1.2rem; font-weight: 600; margin-bottom: 0.5rem; color: var(--text-primary);">Listo para Cargar</div>
                <div style="color: var(--text-muted); margin-bottom: 2rem;">Se crearán los issues en el proyecto <strong>${projectKey}</strong> con los mapeos configurados</div>
                <div style="background: var(--secondary-bg); border-radius: 8px; padding: 1.5rem; text-align: left; max-width: 600px; margin: 0 auto;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;"><span style="color: var(--text-secondary);">Proyecto:</span><span style="font-weight: 600; color: var(--text-primary);">${projectKey}</span></div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;"><span style="color: var(--text-secondary);">Archivo CSV:</span><span style="font-weight: 600; color: var(--text-primary);">${selectedCsvFile ? selectedCsvFile.name : 'N/A'}</span></div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;"><span style="color: var(--text-secondary);">Campos mapeados:</span><span style="font-weight: 600; color: var(--text-primary);">${Object.keys(fieldMappings).length}</span></div>
                    <div style="display: flex; justify-content: space-between;"><span style="color: var(--text-secondary);">Valores por defecto:</span><span style="font-weight: 600; color: var(--text-primary);">${Object.keys(defaultValues).length}</span></div>
                </div>
            </div>`;
    }

    async function uploadCsvToJira() {
        if (isUploadingCsv) return;

        const projectSelector = document.getElementById('carga-masiva-project-selector');
        if (!projectSelector || !projectSelector.value || !selectedCsvFile) {
            showUploadStatus('error', '❌ Faltan datos para cargar');
            return;
        }

        if ((currentUserRole || 'usuario') === 'usuario') {
            if (projectAccessState.status === 'loading') {
                updateCargaMasivaAccessMessage('loading', 'Verificando permisos en el proyecto...');
                return;
            }
            if (!projectAccessState.hasAccess) {
                updateCargaMasivaAccessMessage('error', 'No tienes acceso a este proyecto. Contacta al administrador del proyecto en Jira.');
                return;
            }
        }

        isUploadingCsv = true;
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
            const formData = new FormData();
            formData.append('file', selectedCsvFile);
            formData.append('project_key', projectSelector.value);
            formData.append('field_mappings', JSON.stringify(fieldMappings));
            formData.append('default_values', JSON.stringify(defaultValues));

            const response = await fetch('/api/jira/upload-csv', {
                method: 'POST',
                headers: { 'X-CSRFToken': window.getCsrfToken() },
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                if (uploadStatusIcon) uploadStatusIcon.textContent = '✅';
                if (uploadStatusMessage) uploadStatusMessage.textContent = data.message || 'Archivo cargado exitosamente';
                if (uploadStatus) uploadStatus.classList.add('success');

                // Try calling global increment or mock it if module isolated
                // Actualizar métricas del dashboard si el módulo está disponible
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
            isUploadingCsv = false;
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

    function hideUploadStatus() {
        const uploadStatus = document.getElementById('upload-status');
        if (uploadStatus) {
            uploadStatus.style.display = 'none';
        }
    }

    function resetCargaMasiva() {
        selectedCsvFile = null;
        csvColumns = [];
        csvData = [];
        validationResult = null;
        fieldMappings = {};
        defaultValues = {};
        currentStep = 1;
        isUploadingCsv = false;

        const uploadBtn = document.getElementById('upload-csv-btn');
        if (uploadBtn) uploadBtn.disabled = false;

        const projectInput = document.getElementById('carga-masiva-project-selector-input');
        const projectHidden = document.getElementById('carga-masiva-project-selector');
        const projectDropdown = document.getElementById('carga-masiva-dropdown');
        if (projectInput) projectInput.value = '';
        if (projectHidden) projectHidden.value = '';
        if (projectDropdown) projectDropdown.style.display = 'none';

        const fileInfo = document.getElementById('file-info');
        const fileInput = document.getElementById('csv-file-input');
        if (fileInfo) fileInfo.style.display = 'none';
        if (fileInput) fileInput.value = '';

        const previewSummary = document.getElementById('preview-summary');
        const previewTable = document.getElementById('preview-table-container');
        if (previewSummary) previewSummary.innerHTML = '';
        if (previewTable) previewTable.innerHTML = '';

        const validationSummary = document.getElementById('validation-summary');
        const requiredFieldsSection = document.getElementById('required-fields-section');
        const optionalFieldsSection = document.getElementById('optional-fields-section');
        const fieldMappingsSection = document.getElementById('field-mappings-section');
        if (validationSummary) { validationSummary.innerHTML = ''; validationSummary.style.display = 'none'; }
        if (requiredFieldsSection) requiredFieldsSection.innerHTML = '';
        if (optionalFieldsSection) optionalFieldsSection.innerHTML = '';
        if (fieldMappingsSection) fieldMappingsSection.innerHTML = '';

        const uploadFinalStatus = document.getElementById('upload-final-status');
        if (uploadFinalStatus) uploadFinalStatus.innerHTML = '';

        projectAccessState = { status: 'unknown', hasAccess: false, message: '' };
        updateCargaMasivaAccessMessage(null, '');
        goToStep(1);
        hideUploadStatus();
    }

    // Expose Public Module Interface
    window.NexusModules.Jira.BulkUpload = {
        init: initCargaMasiva,
        reset: resetCargaMasiva,
        switchOperation: switchBulkLoadOperation,
        resetToHub: resetBulkLoadToHub,
        // Optional exports for DOM event handlers if needed
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
