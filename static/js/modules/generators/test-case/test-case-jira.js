/**
 * Nexus AI - Test Case Jira Integration Module
 * Maneja la lógica de subida de casos de prueba a Jira.
 */
(function (window) {
    'use strict';

    const NexusModules = window.NexusModules || {};
    const Api = NexusModules.Generators.Api;
    const Utils = NexusModules.Generators.Utils;
    const ProjectCache = NexusModules.Generators.JiraProjectCache;
    const ButtonState = NexusModules.Generators.JiraButtonState;

    NexusModules.Generators.TestCaseJira = {
        state: {
            assigneeAccountId: null,
            assigneeValidated: false,
            assigneeInvalid: false
        },

        /**
         * Inicializa la lógica de Jira para casos de prueba
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
            const uploadJiraBtn = document.getElementById('tests-upload-jira-btn');
            if (uploadJiraBtn) {
                uploadJiraBtn.onclick = () => this.handleOpenModal();
            }

            const modalClose = document.getElementById('jira-tests-modal-close');
            const modalCancel = document.getElementById('jira-tests-modal-cancel');
            if (modalClose) modalClose.onclick = () => this.closeModal();
            if (modalCancel) modalCancel.onclick = () => this.closeModal();

            const validateFieldsBtn = document.getElementById('jira-tests-validate-fields-btn');
            if (validateFieldsBtn) {
                validateFieldsBtn.onclick = () => this.validateFields();
            }

            const assigneeInput = document.getElementById('jira-tests-assignee-input');
            if (assigneeInput) {
                assigneeInput.onblur = () => this.validateAssignee();
            }

            const modalUploadBtn = document.getElementById('jira-tests-modal-upload');
            if (modalUploadBtn) {
                modalUploadBtn.onclick = () => this.handleUpload();
            }
        },

        /**
         * Abre el modal y prepara el estado inicial
         */
        async handleOpenModal() {
            const selected = document.querySelectorAll('.test-checkbox:checked');
            if (selected.length === 0) {
                window.showDownloadNotification('Por favor selecciona al menos un caso de prueba para subir', 'error');
                return;
            }

            // Historias seleccionadas
            const selectedTestsRaw = Array.from(selected).map(cb => {
                const index = parseInt(cb.dataset.index);
                return window.currentTestsData[index];
            });

            // TC-W1.3 - Bloquear subida si no está APPROVED
            const selectedTests = selectedTestsRaw.filter(t => t.approval_status === 'approved');
            const unapprovedCount = selectedTestsRaw.length - selectedTests.length;

            if (unapprovedCount > 0) {
                if (selectedTests.length === 0) {
                    window.showDownloadNotification('Solo se pueden subir casos con estado Aprobado (APPROVED).', 'error');
                    return;
                }
                window.showDownloadNotification(`Se han omitido ${unapprovedCount} casos que no están aprobados.`, 'warning');
            }

            window.selectedTestsForUpload = selectedTests;

            const modal = document.getElementById('jira-upload-tests-modal');
            const casesCountEl = document.getElementById('jira-tests-modal-cases-count');

            if (casesCountEl) {
                casesCountEl.textContent = `${selectedTests.length} casos seleccionados para subir`;
            }

            try {
                ButtonState.showLoading('tests-upload-jira-btn', 'Cargando proyectos de Jira...');

                const projects = await ProjectCache.getProjects();
                await this.setupModalWithProjects(projects);

                ButtonState.hideLoading('tests-upload-jira-btn');
                modal.style.display = 'flex';
            } catch (error) {
                ButtonState.hideLoading('tests-upload-jira-btn');
                console.error('Error opening Jira tests modal:', error);
                window.showDownloadNotification('Error al abrir el modal de Jira', 'error');
            }
        },

        /**
         * Configura el modal con los proyectos cargados
         */
        async setupModalWithProjects(projects) {
            if (projects.length === 0) {
                window.showDownloadNotification('No se encontraron proyectos de Jira.', 'error');
                throw new Error('No projects found');
            }

            Utils.setupSearchableCombo({
                inputId: 'jira-tests-project-search-input',
                dropdownId: 'jira-tests-project-dropdown',
                hiddenId: 'jira-tests-project-select',
                dataArray: projects,
                onSelect: (item) => {
                    this.handleProjectSelect(item);
                }
            });
        },

        /**
         * Cierra el modal y resetea campos
         */
        closeModal() {
            const modal = document.getElementById('jira-upload-tests-modal');
            if (modal) modal.style.display = 'none';

            // Resetear inputs
            const projectSelect = document.getElementById('jira-tests-project-select');
            const assigneeInput = document.getElementById('jira-tests-assignee-input');
            if (projectSelect) projectSelect.value = '';
            if (assigneeInput) assigneeInput.value = '';

            // Limpiar búsqueda
            const searchInput = document.getElementById('jira-tests-project-search-input');
            const dropdown = document.getElementById('jira-tests-project-dropdown');
            if (searchInput) searchInput.value = '';
            if (dropdown) dropdown.style.display = 'none';

            // Resetear pasos y vistas
            ['jira-tests-step1', 'jira-tests-step1-5', 'jira-tests-step2'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.style.display = id === 'jira-tests-step1' ? 'block' : 'none';
            });

            const validationResult = document.getElementById('jira-tests-validation-result');
            if (validationResult) {
                validationResult.style.display = 'none';
                validationResult.innerHTML = '';
            }

            const validateBtn = document.getElementById('jira-tests-validate-fields-btn');
            if (validateBtn) {
                validateBtn.disabled = true;
                validateBtn.innerHTML = '<span>🔍</span><span>Validar Campos</span>';
            }

            const uploadBtn = document.getElementById('jira-tests-modal-upload');
            if (uploadBtn) uploadBtn.style.display = 'none';

            // Limpiar selects dinámicos
            const selects = ['jira-tests-tipo-prueba-select', 'jira-tests-nivel-prueba-select',
                'jira-tests-tipo-ejecucion-select', 'jira-tests-ambiente-select'];
            selects.forEach(id => {
                const s = document.getElementById(id);
                if (s) {
                    s.value = '';
                    s.innerHTML = '<option value="">Cargando valores...</option>';
                }
            });

            // Ocultar mensajes de campos
            ['jira-tests-tipo-prueba-message', 'jira-tests-nivel-prueba-message',
                'jira-tests-tipo-ejecucion-message', 'jira-tests-ambiente-message'].forEach(id => {
                    const m = document.getElementById(id);
                    if (m) {
                        m.style.display = 'none';
                        m.innerHTML = '';
                    }
                });

            this.state = {
                assigneeAccountId: null,
                assigneeValidated: false,
                assigneeInvalid: false
            };

            const assigneeValidation = document.getElementById('jira-tests-assignee-validation');
            if (assigneeValidation) {
                assigneeValidation.style.display = 'none';
                assigneeValidation.innerHTML = '';
            }
        },

        /**
         * Carga proyectos de Jira y configura combobox (método legacy)
         * @deprecated Usar setupModalWithProjects con ProjectCache.getProjects() en su lugar
         */
        async loadJiraProjects() {
            try {
                const projects = await ProjectCache.getProjects();
                await this.setupModalWithProjects(projects);
            } catch (error) {
                console.error('Error loading Jira projects for tests:', error);
                window.showDownloadNotification('Error al cargar proyectos de Jira', 'error');
                throw error;
            }
        },

        /**
         * Maneja la selección de un proyecto
         */
        handleProjectSelect(item) {
            const validateBtn = document.getElementById('jira-tests-validate-fields-btn');
            if (validateBtn) validateBtn.disabled = false;

            // Resetear estados posteriores
            ['jira-tests-validation-result', 'jira-tests-step1-5', 'jira-tests-step2'].forEach(id => {
                const el = document.getElementById(id);
                if (el) {
                    el.style.display = 'none';
                    if (id === 'jira-tests-validation-result') el.innerHTML = '';
                }
            });

            const uploadBtn = document.getElementById('jira-tests-modal-upload');
            if (uploadBtn) uploadBtn.style.display = 'none';

            // Resetear selects dinámicos
            const selects = ['jira-tests-tipo-prueba-select', 'jira-tests-nivel-prueba-select',
                'jira-tests-tipo-ejecucion-select', 'jira-tests-ambiente-select'];
            selects.forEach(id => {
                const s = document.getElementById(id);
                if (s) {
                    s.value = '';
                    s.innerHTML = '<option value="">Cargando valores...</option>';
                }
            });
        },

        /**
         * Valida disponibilidad de campos obligatorios en el proyecto
         */
        async validateFields() {
            const projectKey = document.getElementById('jira-tests-project-select').value;
            const validateBtn = document.getElementById('jira-tests-validate-fields-btn');
            const validationResult = document.getElementById('jira-tests-validation-result');

            if (!projectKey) {
                window.showDownloadNotification('Por favor selecciona un proyecto primero', 'error');
                return;
            }

            if (validateBtn) {
                validateBtn.disabled = true;
                validateBtn.innerHTML = '<span>⏳</span><span>Validando...</span>';
            }

            try {
                const response = await fetch('/api/jira/validate-test-case-fields', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': window.getCsrfToken()
                    },
                    body: JSON.stringify({ project_key: projectKey })
                });

                const data = await response.json();

                if (validateBtn) {
                    validateBtn.disabled = false;
                    validateBtn.innerHTML = '<span>🔍</span><span>Validar Campos</span>';
                }

                if (validationResult) {
                    validationResult.style.display = 'block';

                    // Filtramos los campos que son de configuración manual para no alertar sobre ellos aquí
                    // ya que se manejarán visualmente en el siguiente paso
                    const manualFields = ['Tipo de Prueba', 'Nivel de Prueba', 'Tipo de Ejecución', 'Ambiente'];
                    const realMissingFields = (data.missing_fields || []).filter(f => !manualFields.includes(f.field));

                    if (data.success || realMissingFields.length === 0) {
                        validationResult.innerHTML = `
                            <div style="padding: 1rem; border-radius: 8px; background: rgba(16, 185, 129, 0.2); border: 1px solid var(--success); color: #6ee7b7;">
                                <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                                    <span>✅</span>
                                    <span style="font-weight: 600;">Campos básicos validados</span>
                                </div>
                                <div style="font-size: 0.85rem; margin-top: 0.5rem;">
                                    Podemos proceder con la configuración manual.
                                </div>
                            </div>
                        `;
                    } else {
                        // Mostrar campos faltantes (excluyendo los manuales) como advertencia
                        const missingList = realMissingFields.map(f => {
                            const expectedNames = (f.possible_names || []).join(', ');
                            return `<li style="margin-bottom: 0.25rem;">
                                <strong>${f.field}</strong>
                                <div style="font-size: 0.75rem; color: var(--text-muted); margin-left: 0.5rem;">
                                    Nombres esperados: ${expectedNames}
                                </div>
                            </li>`;
                        }).join('');

                        validationResult.innerHTML = `
                            <div style="padding: 1rem; border-radius: 8px; background: rgba(245, 158, 11, 0.1); border: 1px solid #f59e0b; color: #f59e0b;">
                                <div style="display: flex; align-items: start; gap: 0.5rem; margin-bottom: 0.5rem;">
                                    <span style="font-size: 1.25rem;">⚠️</span>
                                    <div>
                                        <div style="font-weight: 600; margin-bottom: 0.25rem;">Configuración incompleta</div>
                                        <div style="font-size: 0.85rem; opacity: 0.9;">
                                            El proyecto no tiene algunos campos básicos configurados. La información relacionada se omitirá.
                                        </div>
                                    </div>
                                </div>
                                <ul style="margin-top: 0.5rem; padding-left: 2rem; font-size: 0.9rem; list-style-type: disc;">
                                    ${missingList}
                                </ul>
                            </div>
                        `;
                    }

                    // Siempre procedemos
                    await this.loadFieldValues(projectKey);
                    document.getElementById('jira-tests-step1').style.display = 'none';
                    document.getElementById('jira-tests-step1-5').style.display = 'block';
                }
            } catch (error) {
                console.error('Error validating fields:', error);
                if (validateBtn) {
                    validateBtn.disabled = false;
                    validateBtn.innerHTML = '<span>🔍</span><span>Validar Campos</span>';
                }
            }
        },

        /**
         * Carga los valores permitidos para los campos personalizados
         */
        async loadFieldValues(projectKey) {
            try {
                const response = await fetch('/api/jira/get-test-case-field-values', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': window.getCsrfToken()
                    },
                    body: JSON.stringify({ project_key: projectKey })
                });

                const data = await response.json();
                if (!data.success) return;

                const fieldConfig = {
                    'tipo_prueba': { select: 'jira-tests-tipo-prueba-select', container: 'jira-tests-tipo-prueba-container', message: 'jira-tests-tipo-prueba-message', label: 'Tipo de Prueba' },
                    'nivel_prueba': { select: 'jira-tests-nivel-prueba-select', container: 'jira-tests-nivel-prueba-container', message: 'jira-tests-nivel-prueba-message', label: 'Nivel de Prueba' },
                    'tipo_ejecucion': { select: 'jira-tests-tipo-ejecucion-select', container: 'jira-tests-tipo-ejecucion-container', message: 'jira-tests-tipo-ejecucion-message', label: 'Tipo de Ejecución' },
                    'ambiente': { select: 'jira-tests-ambiente-select', container: 'jira-tests-ambiente-container', message: 'jira-tests-ambiente-message', label: 'Ambiente' },
                    'ciclo': { select: 'jira-tests-ciclo-select', container: 'jira-tests-ciclo-container', message: 'jira-tests-ciclo-message', label: 'Ciclo' }
                };

                for (const [key, config] of Object.entries(fieldConfig)) {
                    const fieldData = data.field_values[key];
                    const select = document.getElementById(config.select);
                    const container = document.getElementById(config.container);
                    const message = document.getElementById(config.message);

                    if (!select || !container || !message) continue;

                    select.innerHTML = '';
                    // Reseteamos estado visual
                    select.style.display = 'block';
                    select.disabled = false;
                    message.style.display = 'none';

                    // Si el campo no existe o no tiene valores
                    if (!fieldData || !fieldData.exists || !fieldData.has_values || fieldData.values.length === 0) {
                        select.disabled = true; // Deshabilitamos el select pero lo dejamos visible
                        select.removeAttribute('required'); // Ya no es obligatorio porque no se puede llenar

                        // Añadimos una opción dummy
                        const opt = document.createElement('option');
                        opt.textContent = "No disponible";
                        select.appendChild(opt);

                        // Mostramos el mensaje de advertencia debajo
                        message.style.display = 'block';
                        message.style.color = 'var(--warning)'; // O usar var(--text-orange) si existe, o #f59e0b
                        message.innerHTML = `⚠️ El campo "${config.label}" no se encontró en Jira. Se omitirá en la carga.`;
                    } else {
                        // Campo existe y tiene valores
                        select.setAttribute('required', 'required');
                        select.innerHTML = '<option value="">Seleccionar...</option>';
                        fieldData.values.forEach(v => {
                            const opt = document.createElement('option');
                            opt.value = v.value;
                            opt.textContent = v.name || v.value;
                            select.appendChild(opt);
                        });

                        // Agregar listener para reactividad
                        select.onchange = () => this.checkAndShowUploadButton();
                    }
                }

                this.checkAndShowUploadButton();
            } catch (error) {
                console.error('Error loading field values:', error);
            }
        },

        /**
         * Verifica si se cumplen todas las condiciones para mostrar el botón de subida
         */
        checkAndShowUploadButton() {
            const step1_5 = document.getElementById('jira-tests-step1-5');
            // Solo validamos los selects que SI son requeridos (los que existen)
            const requiredSelects = step1_5.querySelectorAll('select[required]');
            let allFilled = true;

            for (let s of requiredSelects) {
                if (!s.value) { allFilled = false; break; }
            }

            const step2 = document.getElementById('jira-tests-step2');
            const uploadBtn = document.getElementById('jira-tests-modal-upload');
            const assigneeInput = document.getElementById('jira-tests-assignee-input');

            // Si hay campos requeridos sin llenar, ocultamos lo siguiente
            if (!allFilled) {
                if (step2) step2.style.display = 'none';
                if (uploadBtn) uploadBtn.style.display = 'none';
                return;
            }

            // Si todo lo obligatorio está lleno (o no había nada obligatorio), seguimos
            if (step2) step2.style.display = 'block';

            const email = assigneeInput ? assigneeInput.value.trim() : '';
            if (email) {
                if (this.state.assigneeValidated && !this.state.assigneeInvalid) {
                    if (uploadBtn) uploadBtn.style.display = 'flex';
                } else {
                    if (uploadBtn) uploadBtn.style.display = 'none';
                }
            } else {
                if (uploadBtn) uploadBtn.style.display = 'flex';
            }
        },

        /**
         * Valida el email del asignado
         */
        async validateAssignee() {
            const input = document.getElementById('jira-tests-assignee-input');
            const validationDiv = document.getElementById('jira-tests-assignee-validation');
            const email = input.value.trim();

            if (!email) {
                this.state = { assigneeAccountId: null, assigneeValidated: false, assigneeInvalid: false };
                if (validationDiv) validationDiv.style.display = 'none';
                this.checkAndShowUploadButton();
                return;
            }

            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                if (validationDiv) {
                    validationDiv.style.display = 'block';
                    validationDiv.style.color = 'var(--error)';
                    validationDiv.textContent = '❌ Formato de email inválido';
                }
                this.state.assigneeInvalid = true;
                this.state.assigneeValidated = false;
                this.checkAndShowUploadButton();
                return;
            }

            if (validationDiv) {
                validationDiv.style.display = 'block';
                validationDiv.style.color = 'var(--text-muted)';
                validationDiv.textContent = '⏳ Validando...';
            }

            try {
                const data = await Api.validateJiraUser(email);
                if (data.valid) {
                    this.state.assigneeAccountId = data.accountId;
                    this.state.assigneeValidated = true;
                    this.state.assigneeInvalid = false;
                    if (validationDiv) {
                        validationDiv.style.color = 'var(--success)';
                        validationDiv.textContent = '✅ Usuario encontrado en Jira';
                    }
                } else {
                    this.state.assigneeInvalid = true;
                    this.state.assigneeValidated = false;
                    if (validationDiv) {
                        validationDiv.style.color = 'var(--error)';
                        validationDiv.textContent = '❌ ' + (data.error || 'No encontrado');
                    }
                }
                this.checkAndShowUploadButton();
            } catch (error) {
                console.error('Error validating assignee:', error);
            }
        },

        /**
         * Ejecuta la subida final a Jira
         */
        async handleUpload() {
            const projectKey = document.getElementById('jira-tests-project-select').value;
            const assigneeEmail = document.getElementById('jira-tests-assignee-input').value.trim();

            // Recoger valores de campos personalizados
            const customFields = {
                tipo_prueba: document.getElementById('jira-tests-tipo-prueba-select').value,
                nivel_prueba: document.getElementById('jira-tests-nivel-prueba-select').value,
                tipo_ejecucion: document.getElementById('jira-tests-tipo-ejecucion-select').value,
                ambiente: document.getElementById('jira-tests-ambiente-select').value,
                ciclo: document.getElementById('jira-tests-ciclo-select').value
            };

            const loadingOverlay = document.getElementById('stories-loading-overlay'); // Reusar o usar uno específico si existe
            if (loadingOverlay) loadingOverlay.style.display = 'flex';

            try {
                const data = await Api.uploadToJira('tests', {
                    test_cases: window.selectedTestsForUpload,
                    project_key: projectKey,
                    assignee_email: assigneeEmail || null,
                    custom_fields: customFields
                });

                if (loadingOverlay) loadingOverlay.style.display = 'none';

                if (data.success) {
                    window.showDownloadNotification(data.message || 'Casos de prueba subidos exitosamente', 'success');
                    this.closeModal();
                    if (data.txt_content && data.txt_filename) {
                        this.downloadSummaryTxt(data.txt_content, data.txt_filename);
                    }
                } else {
                    window.showDownloadNotification('Error: ' + (data.error || 'Error desconocido'), 'error');
                }
            } catch (error) {
                if (loadingOverlay) loadingOverlay.style.display = 'none';
                window.showDownloadNotification('Error de conexión: ' + error.message, 'error');
            }
        },

        downloadSummaryTxt(base64Content, filename) {
            try {
                const txtContent = atob(base64Content);
                const blob = new Blob([txtContent], { type: 'text/plain;charset=utf-8' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } catch (err) {
                console.error('Error downloading summary TXT:', err);
            }
        }
    };

    window.NexusModules = NexusModules;
})(window);
