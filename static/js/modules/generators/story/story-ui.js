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
                row.innerHTML = `
                    <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                        <input type="checkbox" class="story-checkbox" data-index="${index}" checked style="width: 18px; height: 18px; cursor: pointer;">
                    </td>
                    <td style="padding: 1rem; border-bottom: 1px solid var(--border); font-weight: 600; color: var(--accent); text-align: center;">${story.index}</td>
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
            document.querySelectorAll('.story-summary-input, .story-description-input, .story-priority-select').forEach(input => {
                input.onchange = (e) => {
                    const index = parseInt(e.target.dataset.index);
                    if (state.currentData && state.currentData[index]) {
                        const val = e.target.value;
                        if (e.target.classList.contains('story-summary-input')) state.currentData[index].summary = val;
                        else if (e.target.classList.contains('story-description-input')) state.currentData[index].description = val;
                        else if (e.target.classList.contains('story-priority-select')) state.currentData[index].priority = val;
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

            if (!summary || !description) {
                window.showDownloadNotification('Por favor completa todos los campos requeridos', 'error');
                return;
            }

            state.currentData[state.editingIndex].summary = summary;
            state.currentData[state.editingIndex].description = description;
            state.currentData[state.editingIndex].issuetype = issuetype;
            state.currentData[state.editingIndex].priority = priority;

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
        }
    };

    window.NexusModules = NexusModules;
})(window);
