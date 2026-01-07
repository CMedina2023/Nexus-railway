/**
 * Nexus AI - Test Case Generator UI
 * Maneja la interfaz de usuario para la generación de casos de prueba.
 */
(function (window) {
    'use strict';

    const NexusModules = window.NexusModules || {};
    NexusModules.Generators = NexusModules.Generators || {};

    // Alias para utilidades
    const Utils = NexusModules.Generators.Utils;

    /**
     * Componente de UI para Casos de Prueba
     */
    NexusModules.Generators.TestUI = {
        /**
         * Muestra la vista previa de los casos de prueba generados
         * @param {Object} data - Datos de los casos de prueba
         * @param {Object} state - Estado del generador
         */
        displayPreview(data, state) {
            const previewSection = document.getElementById('tests-preview-section');
            const previewCount = document.getElementById('tests-preview-count');
            const previewTbody = document.getElementById('tests-preview-tbody');

            if (!previewSection || !previewCount || !previewTbody) return;

            // Mostrar sección
            previewSection.style.display = 'block';
            previewCount.textContent = data.test_cases_count;

            // Limpiar tabla
            previewTbody.innerHTML = '';

            // Agregar casos a la tabla
            data.test_cases.forEach((testCase, index) => {
                const row = document.createElement('tr');
                // Asegurar que raw_data existe
                const rawDesc = testCase.raw_data && testCase.raw_data.Descripcion ? testCase.raw_data.Descripcion : '';

                row.innerHTML = `
                    <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                        <input type="checkbox" class="test-checkbox" data-index="${index}" checked style="width: 18px; height: 18px; cursor: pointer;">
                    </td>
                    <td style="padding: 1rem; border-bottom: 1px solid var(--border); font-weight: 600; color: var(--accent); text-align: center;">${testCase.index}</td>
                    <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                        <input type="text" class="test-summary-input" data-index="${index}" value="${Utils.escapeHtml(testCase.summary)}" style="width: 100%; min-width: 250px; padding: 0.5rem; background: transparent; border: 1px solid transparent; border-radius: 4px; color: var(--text-primary); font-family: inherit; font-size: 0.9rem;">
                    </td>
                    <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                        <textarea class="test-desc-input" data-index="${index}" rows="2" style="width: 100%; min-width: 300px; padding: 0.5rem; background: transparent; border: 1px solid transparent; border-radius: 4px; color: var(--text-secondary); font-family: inherit; font-size: 0.85rem; resize: none;">${Utils.escapeHtml(rawDesc)}</textarea>
                    </td>
                    <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                        <span style="display: inline-block; padding: 0.25rem 0.75rem; border-radius: 6px; font-size: 0.8rem; font-weight: 500; background: rgba(16, 185, 129, 0.2); color: #10b981;">Manual</span>
                    </td>
                    <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                        <span style="font-size: 0.85rem; color: var(--text-secondary); white-space: nowrap;">${Utils.escapeHtml(testCase.tipo_prueba || 'Funcional')}</span>
                    </td>
                    <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                        <span style="font-size: 0.85rem; color: var(--text-secondary); white-space: nowrap;">${Utils.escapeHtml(testCase.categoria || '-')}</span>
                    </td>
                    <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                        ${this.renderCoverageStatus(testCase)}
                    </td>
                    <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                        ${this.renderApprovalStatus(testCase, index)}
                    </td>
                    <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                        ${this.renderApprovalActions(testCase, index)}
                    </td>
                    <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                        <select class="test-priority-select" data-index="${index}" style="padding: 0.5rem; background: var(--secondary-bg); border: 1px solid var(--border); border-radius: 4px; color: var(--text-primary); font-family: inherit; font-size: 0.9rem;">


                            <option value="High" ${testCase.priority === 'High' ? 'selected' : ''}>High</option>
                            <option value="Medium" ${testCase.priority === 'Medium' ? 'selected' : ''}>Medium</option>
                            <option value="Low" ${testCase.priority === 'Low' ? 'selected' : ''}>Low</option>
                        </select>
                    </td>
                    <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                        <div style="display: flex; gap: 0.5rem; align-items: center;">
                            <button class="test-edit-btn" data-index="${index}" style="padding: 0.5rem; background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3); color: var(--accent); border-radius: 6px; cursor: pointer; font-size: 1rem;" title="Editar">✏️</button>
                            <button class="test-delete-btn" data-index="${index}" style="padding: 0.5rem; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); color: var(--error); border-radius: 6px; cursor: pointer; font-size: 1rem;" title="Eliminar">🗑️</button>
                        </div>
                    </td>
                `;
                previewTbody.appendChild(row);
            });

            this.updateEventListeners(state);
            this.updateSelectedCount();
        },

        /**
         * Actualiza los event listeners de la tabla de vista previa
         */
        updateEventListeners(state) {
            const selectAllCheckbox = document.getElementById('tests-select-all');
            const tableSelectAllCheckbox = document.getElementById('tests-table-select-all');

            const handleSelectAll = (e) => {
                const checkboxes = document.querySelectorAll('.test-checkbox');
                checkboxes.forEach(cb => cb.checked = e.target.checked);
                if (selectAllCheckbox) selectAllCheckbox.checked = e.target.checked;
                if (tableSelectAllCheckbox) tableSelectAllCheckbox.checked = e.target.checked;
                this.updateSelectedCount();
            };

            if (selectAllCheckbox) selectAllCheckbox.onclick = handleSelectAll;
            if (tableSelectAllCheckbox) tableSelectAllCheckbox.onclick = handleSelectAll;

            // Checkboxes individuales
            document.querySelectorAll('.test-checkbox').forEach(cb => {
                cb.onchange = () => this.updateSelectedCount();
            });

            // Inputs de edición rápida
            document.querySelectorAll('.test-summary-input, .test-desc-input, .test-priority-select').forEach(input => {
                input.onchange = (e) => {
                    const index = parseInt(e.target.dataset.index);
                    if (state.currentData && state.currentData[index]) {
                        const val = e.target.value;
                        if (e.target.classList.contains('test-summary-input')) {
                            state.currentData[index].summary = val;
                        } else if (e.target.classList.contains('test-desc-input')) {
                            // Actualizar ambos lugares para consistencia
                            if (state.currentData[index].raw_data) {
                                state.currentData[index].raw_data.Descripcion = val;
                            }
                            // Nota: state.currentData[index].description suele ser el texto formateado completo
                            // No lo sobrescribimos aquí para no romper el formato Jira, solo editamos el campo raw
                        } else if (e.target.classList.contains('test-priority-select')) {
                            state.currentData[index].priority = val;
                        }
                    }
                };
            });

            // Botones de acción
            document.querySelectorAll('.test-edit-btn').forEach(btn => {
                btn.onclick = (e) => this.openEditModal(parseInt(e.target.getAttribute('data-index')), state);
            });

            document.querySelectorAll('.test-delete-btn').forEach(btn => {
                btn.onclick = (e) => {
                    const index = parseInt(e.target.dataset.index);
                    if (confirm('¿Estás seguro de eliminar este caso de prueba?')) {
                        state.currentData.splice(index, 1);
                        this.displayPreview({ test_cases: state.currentData, test_cases_count: state.currentData.length }, state);
                    }
                };
            });
        },

        /**
         * Actualiza el contador de casos seleccionados
         */
        updateSelectedCount() {
            const checkboxes = document.querySelectorAll('.test-checkbox:checked');
            const count = checkboxes.length;
            const countEl = document.getElementById('tests-selected-count');
            if (countEl) {
                countEl.textContent = `${count} casos de prueba seleccionados`;
            }
        },

        /**
         * Abre el modal de edición para un caso de prueba
         */
        openEditModal(index, state) {
            if (!state.currentData || !state.currentData[index]) return;

            const testCase = state.currentData[index];
            state.editingIndex = index;

            // Mapeo a los IDs reales en partials/app_modals.html
            const summaryEl = document.getElementById('edit-test-summary');
            const preconditionsEl = document.getElementById('edit-test-preconditions');
            const stepsEl = document.getElementById('edit-test-steps');
            const expectedEl = document.getElementById('edit-test-expected');
            const priorityEl = document.getElementById('edit-test-priority');
            const categoriaEl = document.getElementById('edit-test-categoria');

            if (summaryEl) summaryEl.value = testCase.summary || '';
            if (preconditionsEl) preconditionsEl.value = testCase.preconditions || '';

            if (stepsEl) {
                const steps = testCase.steps;
                stepsEl.value = Array.isArray(steps) ? steps.join('\n') : (steps || '');
            }

            if (expectedEl) {
                const expected = testCase.expected_result;
                expectedEl.value = Array.isArray(expected) ? expected.join('\n') : (expected || '');
            }
            if (priorityEl) priorityEl.value = testCase.priority || 'Medium';
            if (categoriaEl) categoriaEl.value = testCase.categoria || '';

            const modal = document.getElementById('edit-test-modal');
            if (modal) modal.style.display = 'flex';
        },

        /**
         * Cierra el modal de edición
         */
        closeEditModal(state) {
            const modal = document.getElementById('edit-test-modal');
            if (modal) modal.style.display = 'none';
            state.editingIndex = null;
        },

        /**
         * Guarda los cambios del modal de edición
         */
        saveEditChanges(state) {
            if (state.editingIndex === null) return;

            const summaryEl = document.getElementById('edit-test-summary');
            const preconditionsEl = document.getElementById('edit-test-preconditions');
            const stepsEl = document.getElementById('edit-test-steps');
            const expectedEl = document.getElementById('edit-test-expected');
            const priorityEl = document.getElementById('edit-test-priority');
            const categoriaEl = document.getElementById('edit-test-categoria');

            const summary = summaryEl ? summaryEl.value.trim() : '';
            const preconditions = preconditionsEl ? preconditionsEl.value.trim() : '';
            const steps = stepsEl ? stepsEl.value.trim() : '';
            const expected = expectedEl ? expectedEl.value.trim() : '';
            const priority = priorityEl ? priorityEl.value : 'Medium';
            const categoria = categoriaEl ? categoriaEl.value.trim() : '';

            if (!summary || !steps || !expected) {
                window.showDownloadNotification('Por favor completa los campos requeridos (*)', 'error');
                return;
            }

            // Actualizar objeto de datos
            const updatedItem = state.currentData[state.editingIndex];
            updatedItem.summary = summary;
            updatedItem.preconditions = preconditions;
            updatedItem.steps = steps;
            updatedItem.expected_result = expected;
            updatedItem.priority = priority;
            updatedItem.categoria = categoria;

            // Actualizar descripción en raw_data para que se vea coherentemente en la tabla si es necesario
            // En la tabla mostramos raw_data.Descripcion. Vamos a sincronizarla con los pasos para que sea util.
            if (!updatedItem.raw_data) updatedItem.raw_data = {};
            updatedItem.raw_data.Descripcion = steps;

            this.displayPreview({ test_cases: state.currentData, test_cases_count: state.currentData.length }, state);
            this.closeEditModal(state);
            window.showDownloadNotification('Caso de prueba actualizado exitosamente', 'success');
        },

        /**
         * Abre el modal de revisión de HTML
         */
        openReviewModal(state) {
            const modal = document.getElementById('tests-review-modal');
            const iframe = document.getElementById('tests-html-viewer');

            if (!modal || !iframe || !state.currentHtml) {
                window.showDownloadNotification('No hay contenido disponible para revisar', 'error');
                return;
            }

            const blob = new Blob([state.currentHtml], { type: 'text/html;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            iframe.src = url;
            modal.style.display = 'flex';
        },



        /**
         * Carga los requerimientos disponibles en el selector
         * @param {string} projectId - ID del proyecto actual
         */
        async loadRequirements(projectId = 'default') {
            const select = document.getElementById('tests-requirement');
            if (!select) return;

            try {
                // TODO: Obtener el project_id real del contexto
                const response = await fetch(`/api/traceability/matrix/${projectId}`);
                if (!response.ok) throw new Error('Error cargando requerimientos');

                const data = await response.json();
                const matrix = data.matrix || [];

                // Limpiar opciones manteniendo la default
                while (select.options.length > 1) {
                    select.remove(1);
                }

                matrix.forEach(item => {
                    const req = item.requirement;
                    const option = document.createElement('option');
                    option.value = req.id;
                    option.textContent = `${req.code} - ${req.title}`;
                    select.appendChild(option);
                });

                // Si hay un requirement_id pre-seleccionado (por URL/hidden input), seleccionarlo
                const hiddenInput = document.querySelector('input[name="requirement_id"]');
                if (hiddenInput && hiddenInput.value) {
                    select.value = hiddenInput.value;
                    // Sincronizar el hidden input con el select si cambia
                    select.onchange = () => { hiddenInput.value = select.value; };
                }

            } catch (error) {
                console.warn('No se pudieron cargar los requerimientos:', error);
            }
        },

        /**
         * Renderiza el estado de cobertura en la tabla
         */
        renderCoverageStatus(testCase) {
            if (testCase.requirement_id) {
                return `<span style="display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.25rem 0.5rem; border-radius: 6px; font-size: 0.75rem; font-weight: 500; background: rgba(59, 130, 246, 0.1); color: #3b82f6;" title="Vinculado al req: ${testCase.requirement_id}">
                            <i class="fas fa-link"></i> Linked
                        </span>`;
            }
            return `<span style="display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.25rem 0.5rem; border-radius: 6px; font-size: 0.75rem; font-weight: 500; background: rgba(107, 114, 128, 0.1); color: var(--text-muted);" title="Sin traza">
                        <i class="fas fa-unlink"></i> Unlinked
                    </span>`;
        },

        /**
         * Renderiza el estado de aprobación visual
         */
        renderApprovalStatus(testCase) {
            const status = testCase.approval_status || 'draft';
            let style = '';
            let icon = '';
            let text = status.toUpperCase();

            switch (status) {
                case 'approved':
                    style = 'background: rgba(16, 185, 129, 0.2); color: #10b981;';
                    icon = '<i class="fas fa-check-circle"></i>';
                    break;
                case 'rejected':
                    style = 'background: rgba(239, 68, 68, 0.2); color: #ef4444;';
                    icon = '<i class="fas fa-times-circle"></i>';
                    break;
                case 'review_pending':
                    style = 'background: rgba(245, 158, 11, 0.2); color: #f59e0b;';
                    icon = '<i class="fas fa-clock"></i>';
                    text = 'REVIEW';
                    break;
                default: // draft
                    style = 'background: rgba(107, 114, 128, 0.2); color: var(--text-muted);';
                    icon = '<i class="fas fa-pen"></i>';
                    break;
            }

            return `<span class="badge-approval" style="display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.25rem 0.5rem; border-radius: 6px; font-size: 0.7rem; font-weight: 600; letter-spacing: 0.5px; ${style}">
                        ${icon} ${text}
                    </span>`;
        },

        renderApprovalActions(testCase, index) {
            const status = testCase.approval_status || 'draft';

            // Si ya está aprobado, solo mostramos opción de revertir o rechazar
            if (status === 'approved') {
                return `
                    <button class="btn-workflow-action btn-reject" onclick="NexusModules.Generators.TestUI.setTestStatus(${index}, 'rejected')" title="Rechazar">
                        <i class="fas fa-times"></i>
                    </button>
                    <button class="btn-workflow-action btn-reset" onclick="NexusModules.Generators.TestUI.setTestStatus(${index}, 'draft')" title="Volver a Draft">
                         <i class="fas fa-undo"></i>
                    </button>
                `;
            }

            return `
                <div class="workflow-actions-group" style="display: flex; gap: 4px;">
                    <button class="btn-workflow-action btn-approve" onclick="NexusModules.Generators.TestUI.setTestStatus(${index}, 'approved')" title="Aprobar">
                        <i class="fas fa-check"></i>
                    </button>
                    <button class="btn-workflow-action btn-reject" onclick="NexusModules.Generators.TestUI.setTestStatus(${index}, 'rejected')" title="Rechazar">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
        },

        setTestStatus(index, newStatus) {
            // Actualizar estado localmente
            if (window.currentTestsData && window.currentTestsData[index]) {
                window.currentTestsData[index].approval_status = newStatus;

                // Si es aprobado, setear metadata
                if (newStatus === 'approved') {
                    window.currentTestsData[index].approved_at = new Date().toISOString();
                    // window.currentTestsData[index].approved_by = currentUserId; // TODO: Get User ID
                }

                // Refrescar tabla (re-render)
                // Necesitamos el 'state' original o reconstruirlo mínimamente
                // Como displayPreview usa 'data' que es {test_cases: ...}
                this.displayPreview({
                    test_cases: window.currentTestsData,
                    test_cases_count: window.currentTestsData.length
                }, { currentData: window.currentTestsData }); // Mock state
            }
        }
    };

    window.NexusModules = NexusModules;
})(window);
