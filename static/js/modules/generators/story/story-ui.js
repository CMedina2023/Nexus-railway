/**
 * Nexus AI - Story Generator UI
 * Maneja la interfaz de usuario para la generación de historias.
 */
(function (window) {
    'use strict';

    const NexusModules = window.NexusModules || {};
    NexusModules.Generators = NexusModules.Generators || {};

    // Alias para utilidades
    const Utils = NexusModules.Generators.Utils;

    /**
     * Componente de UI para Historias de Usuario
     */
    NexusModules.Generators.StoryUI = {
        /**
         * Muestra la vista previa de las historias generadas
         * @param {Object} data - Datos de las historias
         */
        displayPreview(data, state) {
            const previewSection = document.getElementById('stories-preview-section');
            const previewCount = document.getElementById('stories-preview-count');
            const previewTbody = document.getElementById('stories-preview-tbody');

            if (!previewSection || !previewCount || !previewTbody) return;

            // Mostrar sección
            previewSection.style.display = 'block';
            previewCount.textContent = data.stories_count;

            // Limpiar tabla
            previewTbody.innerHTML = '';


            // Agregar historias a la tabla
            data.stories.forEach((story, index) => {
                const row = document.createElement('tr');
                const reqId = story.requirement_id || '-';

                row.innerHTML = `
                    <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                        <input type="checkbox" class="story-checkbox" data-index="${index}" checked style="width: 18px; height: 18px; cursor: pointer;">
                    </td>
                    <td style="padding: 1rem; border-bottom: 1px solid var(--border); font-weight: 600; color: var(--accent); text-align: center;">${story.index}</td>
                    <!-- Columna ID Requerimiento -->
                    <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                        <input type="text" class="story-req-id-input" data-index="${index}" value="${Utils.escapeHtml(reqId)}" style="width: 100%; max-width: 100px; padding: 0.5rem; background: var(--secondary-bg); border: 1px solid var(--border); border-radius: 4px; color: var(--text-primary); font-family: inherit; font-size: 0.85rem;" placeholder="REQ-000">
                    </td>
                    <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                        <input type="text" class="story-summary-input" data-index="${index}" value="${Utils.escapeHtml(story.summary)}" style="width: 100%; max-width: 300px; padding: 0.5rem; background: transparent; border: 1px solid transparent; border-radius: 4px; color: var(--text-primary); font-family: inherit; font-size: 0.9rem;">
                    </td>
                    <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                        <textarea class="story-description-input" data-index="${index}" rows="2" style="width: 100%; max-width: 400px; padding: 0.5rem; background: transparent; border: 1px solid transparent; border-radius: 4px; color: var(--text-secondary); font-family: inherit; font-size: 0.85rem; resize: none; min-height: 50px;">${Utils.escapeHtml(story.description)}</textarea>
                    </td>
                    <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                        <span style="display: inline-block; padding: 0.25rem 0.75rem; border-radius: 6px; font-size: 0.8rem; font-weight: 500; background: rgba(59, 130, 246, 0.2); color: var(--accent);">${story.issuetype}</span>
                    </td>
                    <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                        ${this.renderApprovalStatus(story, index)}
                    </td>
                    <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                        ${this.renderApprovalActions(story, index)}
                    </td>
                    <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                        <select class="story-priority-select" data-index="${index}" style="padding: 0.5rem; background: var(--secondary-bg); border: 1px solid var(--border); border-radius: 4px; color: var(--text-primary); font-family: inherit; font-size: 0.9rem;">
                            <option value="High" ${story.priority === 'High' ? 'selected' : ''}>High</option>
                            <option value="Medium" ${story.priority === 'Medium' ? 'selected' : ''}>Medium</option>
                            <option value="Low" ${story.priority === 'Low' ? 'selected' : ''}>Low</option>
                        </select>
                    </td>
                    <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                        <div style="display: flex; gap: 0.5rem; align-items: center;">
                            <button class="story-edit-btn" data-index="${index}" style="padding: 0.5rem; background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3); color: var(--accent); border-radius: 6px; cursor: pointer; font-size: 1rem;" title="Editar">✏️</button>
                            <button class="story-delete-btn" data-index="${index}" style="padding: 0.5rem; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); color: var(--error); border-radius: 6px; cursor: pointer; font-size: 1rem;" title="Eliminar">🗑️</button>
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
            const selectAllCheckbox = document.getElementById('stories-select-all');
            const tableSelectAllCheckbox = document.getElementById('stories-table-select-all');

            const handleSelectAll = (e) => {
                const checkboxes = document.querySelectorAll('.story-checkbox');
                checkboxes.forEach(cb => cb.checked = e.target.checked);
                if (selectAllCheckbox) selectAllCheckbox.checked = e.target.checked;
                if (tableSelectAllCheckbox) tableSelectAllCheckbox.checked = e.target.checked;
                this.updateSelectedCount();
            };

            if (selectAllCheckbox) selectAllCheckbox.onclick = handleSelectAll;
            if (tableSelectAllCheckbox) tableSelectAllCheckbox.onclick = handleSelectAll;

            // Checkboxes individuales
            document.querySelectorAll('.story-checkbox').forEach(cb => {
                cb.onchange = () => this.updateSelectedCount();
            });

            // Inputs de edición rápida
            document.querySelectorAll('.story-summary-input, .story-description-input, .story-priority-select, .story-req-id-input').forEach(input => {
                input.onchange = (e) => {
                    const index = parseInt(e.target.dataset.index);
                    if (state.currentData && state.currentData[index]) {
                        const val = e.target.value;
                        if (e.target.classList.contains('story-summary-input')) state.currentData[index].summary = val;
                        else if (e.target.classList.contains('story-description-input')) state.currentData[index].description = val;
                        else if (e.target.classList.contains('story-priority-select')) state.currentData[index].priority = val;
                        else if (e.target.classList.contains('story-req-id-input')) state.currentData[index].requirement_id = val === '-' ? null : val;
                    }
                };
            });

            // Botones de acción
            document.querySelectorAll('.story-edit-btn').forEach(btn => {
                btn.onclick = (e) => this.openEditModal(parseInt(e.target.getAttribute('data-index')), state);
            });

            document.querySelectorAll('.story-delete-btn').forEach(btn => {
                btn.onclick = (e) => {
                    const index = parseInt(e.target.dataset.index);
                    if (confirm('¿Estás seguro de eliminar esta historia?')) {
                        state.currentData.splice(index, 1);
                        this.displayPreview({ stories: state.currentData, stories_count: state.currentData.length }, state);
                    }
                };
            });
        },

        /**
         * Actualiza el contador de historias seleccionadas
         */
        updateSelectedCount() {
            const checkboxes = document.querySelectorAll('.story-checkbox:checked');
            const count = checkboxes.length;
            const countEl = document.getElementById('stories-selected-count');
            if (countEl) {
                countEl.textContent = `${count} historias seleccionadas`;
            }
        },

        /**
         * Abre el modal de edición para una historia
         */
        openEditModal(index, state) {
            if (!state.currentData || !state.currentData[index]) return;

            const story = state.currentData[index];
            state.editingIndex = index;

            document.getElementById('edit-story-summary').value = story.summary || '';
            document.getElementById('edit-story-description').value = story.description || '';
            document.getElementById('edit-story-issuetype').value = story.issuetype || 'Story';
            document.getElementById('edit-story-priority').value = story.priority || 'Medium';
            const reqInput = document.getElementById('edit-story-requirement');
            if (reqInput) reqInput.value = story.requirement_id || '';

            const modal = document.getElementById('edit-story-modal');
            if (modal) modal.style.display = 'flex';
        },

        /**
         * Cierra el modal de edición
         */
        closeEditModal(state) {
            const modal = document.getElementById('edit-story-modal');
            if (modal) modal.style.display = 'none';
            state.editingIndex = null;
        },

        /**
         * Guarda los cambios del modal de edición
         */
        saveEditChanges(state) {
            if (state.editingIndex === null) return;

            const summary = document.getElementById('edit-story-summary').value.trim();
            const description = document.getElementById('edit-story-description').value.trim();
            const issuetype = document.getElementById('edit-story-issuetype').value;
            const priority = document.getElementById('edit-story-priority').value;
            const reqInput = document.getElementById('edit-story-requirement');
            const reqId = reqInput ? reqInput.value.trim() : null;

            if (!summary || !description) {
                window.showDownloadNotification('Por favor completa todos los campos requeridos', 'error');
                return;
            }

            state.currentData[state.editingIndex].summary = summary;
            state.currentData[state.editingIndex].description = description;
            state.currentData[state.editingIndex].issuetype = issuetype;
            state.currentData[state.editingIndex].priority = priority;
            if (reqId !== null) state.currentData[state.editingIndex].requirement_id = reqId;

            this.displayPreview({ stories: state.currentData, stories_count: state.currentData.length }, state);
            this.closeEditModal(state);
            window.showDownloadNotification('Historia actualizada exitosamente', 'success');
        },

        /**
         * Abre el modal de revisión de HTML
         */
        openReviewModal(state) {
            const modal = document.getElementById('stories-review-modal');
            const iframe = document.getElementById('stories-html-viewer');

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
         * Cierra el modal de revisión
         */
        closeReviewModal() {
            const modal = document.getElementById('stories-review-modal');
            const iframe = document.getElementById('stories-html-viewer');

            if (iframe && iframe.src) {
                URL.revokeObjectURL(iframe.src);
                iframe.src = '';
            }
            if (modal) modal.style.display = 'none';
        },

        /**
         * Renderiza el estado de aprobación visual
         */
        renderApprovalStatus(story) {
            const status = story.approval_status || 'DRAFT'; // Default to DRAFT if undefined
            // Convert to uppercase for consistent handling
            const statusUpper = status.toUpperCase();

            let style = '';
            let icon = '';
            let text = statusUpper;

            switch (statusUpper) {
                case 'APPROVED':
                    style = 'background: rgba(16, 185, 129, 0.2); color: #10b981;';
                    icon = '<i class="fas fa-check-circle"></i>';
                    break;
                case 'REJECTED':
                    style = 'background: rgba(239, 68, 68, 0.2); color: #ef4444;';
                    icon = '<i class="fas fa-times-circle"></i>';
                    break;
                case 'PENDING_REVIEW':
                    style = 'background: rgba(245, 158, 11, 0.2); color: #f59e0b;';
                    icon = '<i class="fas fa-clock"></i>';
                    text = 'REVIEW';
                    break;
                default: // DRAFT
                    style = 'background: rgba(107, 114, 128, 0.2); color: var(--text-muted);';
                    icon = '<i class="fas fa-pen"></i>';
                    break;
            }

            return `<span class="badge-approval" style="display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.25rem 0.5rem; border-radius: 6px; font-size: 0.7rem; font-weight: 600; letter-spacing: 0.5px; ${style}">
                        ${icon} ${text}
                    </span>`;
        },

        /**
         * Renderiza los botones de acción del workflow
         */
        renderApprovalActions(story, index) {
            const status = (story.approval_status || 'DRAFT').toUpperCase();

            // Si ya está aprobado, solo mostramos opción de revertir o rechazar (si aplica)
            if (status === 'APPROVED') {
                return `
                    <button class="btn-workflow-action btn-reject" onclick="NexusModules.Generators.StoryUI.setStoryStatus(${index}, 'REJECTED')" title="Rechazar" style="border:none; background:transparent; cursor:pointer; color:#ef4444;">
                        <i class="fas fa-times"></i>
                    </button>
                    <button class="btn-workflow-action btn-reset" onclick="NexusModules.Generators.StoryUI.setStoryStatus(${index}, 'DRAFT')" title="Volver a Draft" style="border:none; background:transparent; cursor:pointer; color:var(--text-muted);">
                         <i class="fas fa-undo"></i>
                    </button>
                `;
            }

            return `
                <div class="workflow-actions-group" style="display: flex; gap: 8px; justify-content: center;">
                    <button class="btn-workflow-action btn-approve" onclick="NexusModules.Generators.StoryUI.setStoryStatus(${index}, 'APPROVED')" title="Aprobar" style="border:none; background:transparent; cursor:pointer; color:#10b981;">
                        <i class="fas fa-check"></i>
                    </button>
                    <button class="btn-workflow-action btn-reject" onclick="NexusModules.Generators.StoryUI.setStoryStatus(${index}, 'REJECTED')" title="Rechazar" style="border:none; background:transparent; cursor:pointer; color:#ef4444;">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
        },

        /**
         * Actualiza el estado de aprobación de una historia
         */
        setStoryStatus(index, newStatus) {
            // Actualizar estado localmente
            if (window.currentStoriesData && window.currentStoriesData[index]) {
                window.currentStoriesData[index].approval_status = newStatus;

                // Si es aprobado, setear metadata
                if (newStatus === 'APPROVED') {
                    window.currentStoriesData[index].approved_at = new Date().toISOString();
                }

                // Refrescar tabla (re-render)
                // Necesitamos el 'state' original o reconstruirlo mínimamente
                this.displayPreview({
                    stories: window.currentStoriesData,
                    stories_count: window.currentStoriesData.length
                }, { currentData: window.currentStoriesData });
            }
        }
    };

    window.NexusModules = NexusModules;
})(window);
