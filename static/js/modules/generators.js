/**
 * Módulo para los Generadores (Historias de Usuario y Casos de Prueba)
 */
(function (window) {
    // Referencia al contexto global si es necesario
    const NexusModules = window.NexusModules || {};
    window.NexusModules = NexusModules;

    // Namespace
    NexusModules.Generators = {};

    // ========================================================================
    // CREAR HISTORIAS - JavaScript
    // ========================================================================
    (function () {
        // Función para resetear el generador de historias
        function resetStoriesGenerator() {
            const formContainer = document.getElementById('stories-form-container');
            const previewSection = document.getElementById('stories-preview-section');
            const backBtnContainer = document.getElementById('stories-back-btn-container');
            const storiesForm = document.getElementById('stories-form');
            const storiesFileInput = document.getElementById('stories-file');
            const storiesFileInfo = document.getElementById('stories-file-info');
            const storiesFileName = document.getElementById('stories-file-name');
            const storiesRemoveFileBtn = document.getElementById('stories-remove-file-btn');
            const storiesContext = document.getElementById('stories-context');
            const storiesContextCounter = document.getElementById('stories-context-counter');
            const storiesType = document.getElementById('stories-type');
            const storiesArea = document.getElementById('stories-area');
            const previewTbody = document.getElementById('stories-preview-tbody');
            const previewCount = document.getElementById('stories-preview-count');
            const selectedCount = document.getElementById('stories-selected-count');

            // Resetear formulario
            if (storiesForm) storiesForm.reset();
            if (storiesFileInput) storiesFileInput.value = '';
            if (storiesFileInfo) storiesFileInfo.style.display = 'none';
            if (storiesFileName) storiesFileName.textContent = '';
            if (storiesRemoveFileBtn) storiesRemoveFileBtn.style.display = 'none';
            if (storiesContext) storiesContext.value = '';
            if (storiesContextCounter) storiesContextCounter.textContent = '0 / 2000 caracteres';
            if (storiesType) storiesType.value = 'funcionalidad';
            if (storiesArea) storiesArea.value = '';

            // Limpiar vista previa
            if (previewTbody) previewTbody.innerHTML = '';
            if (previewCount) previewCount.textContent = '0';
            if (selectedCount) selectedCount.textContent = '0 historias seleccionadas';

            // Resetear checkboxes
            const selectAllCheckbox = document.getElementById('stories-select-all');
            const tableSelectAllCheckbox = document.getElementById('stories-table-select-all');
            if (selectAllCheckbox) selectAllCheckbox.checked = false;
            if (tableSelectAllCheckbox) tableSelectAllCheckbox.checked = false;

            // Limpiar variables globales
            window.selectedStoriesForUpload = [];
            window.storiesData = null;
            currentStoriesData = null;
            currentStoriesHtml = null;
            currentStoriesCsv = null;

            // Mostrar formulario y ocultar vista previa
            if (formContainer) formContainer.style.display = 'block';
            if (previewSection) previewSection.style.display = 'none';
            if (backBtnContainer) backBtnContainer.style.display = 'none';

            // Asegurar que el form-card también se muestre
            const storiesFormCard = document.getElementById('stories-form');
            if (storiesFormCard) {
                const formCard = storiesFormCard.closest('.form-card');
                if (formCard) formCard.style.display = 'block';
            }

            // Activar la sección de crear historias
            if (typeof navigateToSection === 'function') {
                navigateToSection('crear-historias');
            } else {
                // Fallback: activar manualmente si navigateToSection no está disponible
                const crearHistoriasSection = document.getElementById('crear-historias');
                if (crearHistoriasSection) {
                    // Ocultar todas las secciones
                    document.querySelectorAll('.content-section').forEach(section => {
                        section.classList.remove('active');
                    });
                    // Activar la sección de crear historias
                    crearHistoriasSection.classList.add('active');
                    // Actualizar nav-item activo
                    document.querySelectorAll('.nav-item').forEach(item => {
                        item.classList.remove('active-link', 'active');
                    });
                    const activeNav = document.querySelector('[data-section="crear-historias"]');
                    if (activeNav) {
                        activeNav.classList.add('active-link');
                    }
                    crearHistoriasSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }
        }

        // Botón de regreso
        const backBtn = document.getElementById('stories-back-btn');
        if (backBtn) {
            backBtn.onclick = function () {
                resetStoriesGenerator();
            };
        }

        // Botón de reset
        const resetBtn = document.getElementById('stories-reset-btn');
        if (resetBtn) {
            resetBtn.onclick = function () {
                if (confirm('¿Estás seguro de que deseas hacer una nueva generación? Se perderán los datos actuales.')) {
                    resetStoriesGenerator();
                }
            };
        }
        const storiesDropZone = document.getElementById('stories-drop-zone');
        const storiesFileInput = document.getElementById('stories-file');
        const storiesForm = document.getElementById('stories-form');
        const storiesContext = document.getElementById('stories-context');
        const storiesCounter = document.getElementById('stories-context-counter');
        const storiesGenerateBtn = document.getElementById('stories-generate-btn');
        const storiesFileInfo = document.getElementById('stories-file-info');
        const storiesFileName = document.getElementById('stories-file-name');
        const storiesRemoveFileBtn = document.getElementById('stories-remove-file-btn');

        if (!storiesForm) return;

        // Setup drag and drop (igual que carga masiva)
        function setupStoriesDropZone() {
            if (!storiesDropZone || !storiesFileInput) return;

            // Click en la zona de arrastre - FIX: usar mousedown en lugar de click para evitar doble click
            storiesDropZone.addEventListener('mousedown', (e) => {
                // Solo si el click es directamente en el dropZone, no en elementos hijos
                if (e.target === storiesDropZone || e.target.closest('.drop-zone-content')) {
                    e.preventDefault();
                    storiesFileInput.click();
                }
            });

            // Prevenir comportamiento por defecto del navegador
            storiesDropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.stopPropagation();
                storiesDropZone.classList.add('drag-over');
            });

            storiesDropZone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                e.stopPropagation();
                storiesDropZone.classList.remove('drag-over');
            });

            storiesDropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                e.stopPropagation();
                storiesDropZone.classList.remove('drag-over');

                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    handleStoriesFileSelect(files[0]);
                }
            });

            // Cambio de archivo desde el input - FIX: usar change directamente sin prevenir default
            storiesFileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    handleStoriesFileSelect(e.target.files[0]);
                }
            });
        }

        function handleStoriesFileSelect(file) {
            // Validar que sea DOCX o PDF
            const validExtensions = ['.docx', '.pdf'];
            const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
            if (!validExtensions.includes(fileExtension)) {
                showDownloadNotification('❌ Solo se permiten archivos DOCX o PDF', 'error');
                return;
            }

            // Mostrar información del archivo
            if (storiesFileInfo && storiesFileName) {
                storiesFileName.textContent = file.name;
                storiesFileInfo.style.display = 'flex';
            }
        }

        // Botón para remover archivo
        if (storiesRemoveFileBtn) {
            storiesRemoveFileBtn.addEventListener('click', () => {
                storiesFileInput.value = '';
                if (storiesFileInfo) {
                    storiesFileInfo.style.display = 'none';
                }
            });
        }

        // Character counter
        if (storiesContext && storiesCounter) {
            storiesContext.addEventListener('input', (e) => {
                const length = e.target.value.length;
                const maxLength = 2000;
                storiesCounter.textContent = `${length} / ${maxLength} caracteres`;
                storiesCounter.classList.remove('warning', 'error');
                if (length > maxLength * 0.9) {
                    storiesCounter.classList.add('error');
                } else if (length > maxLength * 0.8) {
                    storiesCounter.classList.add('warning');
                }
            });
        }

        // Generate handler
        if (storiesForm) {
            storiesForm.addEventListener('submit', async (e) => {
                e.preventDefault();

                // Validación completa de campos requeridos
                const validationErrors = [];

                // Validar archivo
                if (!storiesFileInput.files.length) {
                    validationErrors.push('📄 Debes cargar un archivo (DOCX o PDF)');
                }

                // Validar área
                const areaSelect = document.getElementById('stories-area');
                if (!areaSelect || !areaSelect.value) {
                    validationErrors.push('📋 Debes seleccionar un área');
                }

                // Si hay errores, mostrarlos
                if (validationErrors.length > 0) {
                    const errorMessage = '⚠️ No puedes generar la vista previa:\n\n' + validationErrors.join('\n');
                    showDownloadNotification(errorMessage, 'error');

                    // Resaltar campos faltantes con animación
                    if (!storiesFileInput.files.length) {
                        const dropZone = document.getElementById('stories-drop-zone');
                        if (dropZone) {
                            dropZone.style.border = '2px solid #ef4444';
                            dropZone.style.boxShadow = '0 0 0 3px rgba(239, 68, 68, 0.2)';
                            dropZone.style.animation = 'shake 0.5s';
                            setTimeout(() => {
                                dropZone.style.border = '';
                                dropZone.style.boxShadow = '';
                                dropZone.style.animation = '';
                            }, 3000);
                        }
                    }

                    if (!areaSelect || !areaSelect.value) {
                        if (areaSelect) {
                            areaSelect.style.border = '2px solid #ef4444';
                            areaSelect.style.boxShadow = '0 0 0 3px rgba(239, 68, 68, 0.2)';
                            areaSelect.style.animation = 'shake 0.5s';
                            setTimeout(() => {
                                areaSelect.style.border = '';
                                areaSelect.style.boxShadow = '';
                                areaSelect.style.animation = '';
                            }, 3000);
                        }
                    }

                    return;
                }

                const selectedArea = areaSelect.value;
                const formData = new FormData(storiesForm);

                // UI Setup for Progress
                storiesGenerateBtn.disabled = true;
                storiesGenerateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';

                const progressContainer = document.getElementById('stories-progress-container');
                const progressBar = document.getElementById('stories-progress-bar');
                const progressPhase = document.getElementById('stories-progress-phase');
                const progressPercentage = document.getElementById('stories-progress-percentage');
                const progressMessage = document.getElementById('stories-progress-message');

                if (progressContainer) progressContainer.style.display = 'block';
                if (progressBar) progressBar.style.width = '0%';
                if (progressPhase) progressPhase.textContent = 'Iniciando generación...';
                if (progressPercentage) progressPercentage.textContent = '0%';

                try {
                    const response = await fetch('/api/stories/generate', {
                        method: 'POST',
                        body: formData,
                        headers: {
                            'X-CSRFToken': getCsrfToken()
                        }
                    });

                    if (!response.ok) {
                        throw new Error('Error en la respuesta del servidor');
                    }

                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();
                    let buffer = '';

                    while (true) {
                        const { value, done } = await reader.read();
                        if (done) break;

                        buffer += decoder.decode(value, { stream: true });
                        const lines = buffer.split('\n\n');
                        buffer = lines.pop();

                        for (const line of lines) {
                            if (line.trim().startsWith('data: ')) {
                                try {
                                    const data = JSON.parse(line.trim().substring(6));

                                    // Update Progress UI
                                    if (data.progress !== undefined) {
                                        if (progressBar) progressBar.style.width = `${data.progress}%`;
                                        if (progressPercentage) progressPercentage.textContent = `${data.progress}%`;
                                    }
                                    if (data.status && progressPhase) progressPhase.textContent = data.status;
                                    if (data.message && progressMessage) progressMessage.textContent = data.message;

                                    // Handle Terminal Event
                                    if (data.terminal) {
                                        if (data.error) {
                                            throw new Error(data.error);
                                        }

                                        if (data.data && data.data.stories) {
                                            const resultData = data.data;
                                            // Ocultar formulario y mostrar vista previa
                                            const formContainer = document.getElementById('stories-form-container');
                                            const previewSection = document.getElementById('stories-preview-section');
                                            const backBtnContainer = document.getElementById('stories-back-btn-container');

                                            if (formContainer) formContainer.style.display = 'none';
                                            if (previewSection) previewSection.style.display = 'block';
                                            if (backBtnContainer) backBtnContainer.style.display = 'block';

                                            // Guardar datos globales
                                            currentStoriesData = resultData.stories;
                                            currentStoriesHtml = resultData.html_content;
                                            currentStoriesCsv = resultData.csv_content;

                                            // Mostrar vista previa
                                            displayStoriesPreview(resultData);

                                            // Actualizar métricas
                                            if (resultData.stories_count > 0 && window.NexusModules?.Dashboard?.updateMetrics) {
                                                window.NexusModules.Dashboard.updateMetrics('stories', resultData.stories_count, selectedArea);
                                            }

                                            showDownloadNotification(`Historias generadas exitosamente: ${resultData.stories_count} historias`, 'success');
                                            document.getElementById('crear-historias').scrollIntoView({ behavior: 'smooth', block: 'start' });
                                        }
                                    }
                                } catch (e) {
                                    console.error('Error parsing SSE data:', e, line);
                                }
                            }
                        }
                    }
                } catch (error) {
                    console.error('Error en generación:', error);
                    showDownloadNotification('Error: ' + error.message, 'error');
                } finally {
                    storiesGenerateBtn.disabled = false;
                    storiesGenerateBtn.innerHTML = '<i class="fas fa-eye"></i> Generar e Ir a Vista Previa';
                    if (progressContainer) progressContainer.style.display = 'none';
                }
            });
        }

        // Inicializar drag and drop
        setupStoriesDropZone();

        // Variables globales para historias
        let currentStoriesData = null;
        let currentStoriesHtml = null;
        let currentStoriesCsv = null;

        // Función para mostrar vista previa de historias
        function displayStoriesPreview(data) {
            currentStoriesData = data.stories;
            // Si no viene nuevo HTML/CSV, mantenemos el original para preservar estilos
            if (data.html_content) currentStoriesHtml = data.html_content;
            if (data.csv_content) currentStoriesCsv = data.csv_content;

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
                                <input type="text" class="story-summary-input" data-index="${index}" value="${escapeHtml(story.summary)}" style="width: 100%; max-width: 300px; padding: 0.5rem; background: transparent; border: 1px solid transparent; border-radius: 4px; color: var(--text-primary); font-family: inherit; font-size: 0.9rem;">
                            </td>
                            <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                                <textarea class="story-description-input" data-index="${index}" rows="2" style="width: 100%; max-width: 400px; padding: 0.5rem; background: transparent; border: 1px solid transparent; border-radius: 4px; color: var(--text-secondary); font-family: inherit; font-size: 0.85rem; resize: none; min-height: 50px;">${escapeHtml(story.description)}</textarea>
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

            // Event listeners para edición
            updateStoriesEventListeners();
            updateSelectedCount();
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Función para formatear una historia individual para HTML
        function formatStoryForHTML(story, storyNum) {
            const title = story.summary || `Historia ${storyNum}`;
            const description = story.description || '';
            const priority = story.priority || 'Medium';
            const issuetype = story.issuetype || 'Story';

            // Parsear descripción para extraer COMO, QUIERO, PARA, etc.
            const comoMatch = description.match(/COMO:\s*([^\n]+)/i);
            const quieroMatch = description.match(/QUIERO:\s*([^\n]+)/i);
            const paraMatch = description.match(/PARA:\s*([^\n]+)/i);
            const criteriosMatch = description.match(/CRITERIOS\s+DE\s+ACEPTACI[ÓO]N:\s*([\s\S]*?)(?:\s+REGLAS|PRIORIDAD|COMPLEJIDAD|$)/i);

            let html = `<div class="story-container">
            <div class="story-title">HISTORIA #${storyNum}: ${escapeHtml(title)}</div>`;

            if (comoMatch) {
                html += `
                            <div class="story-item">
                                <span class="bullet">*</span>
                                <span class="story-item-label">COMO:</span>
                                <span class="story-item-content"> ${escapeHtml(comoMatch[1].trim())}</span>
                            </div>`;
            }

            if (quieroMatch) {
                html += `
                            <div class="story-item">
                                <span class="bullet">*</span>
                                <span class="story-item-label">QUIERO:</span>
                                <span class="story-item-content"> ${escapeHtml(quieroMatch[1].trim())}</span>
                            </div>`;
            }

            if (paraMatch) {
                html += `
                            <div class="story-item">
                                <span class="bullet">*</span>
                                <span class="story-item-label">PARA:</span>
                                <span class="story-item-content"> ${escapeHtml(paraMatch[1].trim())}</span>
                            </div>`;
            }

            // Si no hay estructura COMO/QUIERO/PARA, mostrar descripción completa
            if (!comoMatch && !quieroMatch && !paraMatch && description) {
                html += `
                            <div class="story-item">
                                <span class="bullet">*</span>
                                <span class="story-item-label">Descripción:</span>
                                <span class="story-item-content"> ${escapeHtml(description)}</span>
                            </div>`;
            }

            // Agregar criterios de aceptación si existen
            if (criteriosMatch) {
                const criterios = criteriosMatch[1].trim();
                html += `
                            <div class="story-item">
                                <span class="bullet">*</span>
                                <span class="story-item-label">Criterios de Aceptación:</span>
                                <span class="story-item-content"> ${escapeHtml(criterios)}</span>
                            </div>`;
            }

            html += `
                            <div class="story-item">
                                <span class="bullet">*</span>
                                <span class="story-item-label">Tipo:</span>
                                <span class="story-item-content"> ${issuetype}</span>
                            </div>
                            <div class="story-item">
                                <span class="bullet">*</span>
                                <span class="story-item-label">Prioridad:</span>
                                <span class="story-item-content"> ${priority}</span>
                            </div>
                        </div>`;

            return html;
        }

        function updateStoriesEventListeners() {
            // Select all checkboxes
            const selectAllCheckbox = document.getElementById('stories-select-all');
            const tableSelectAllCheckbox = document.getElementById('stories-table-select-all');

            if (selectAllCheckbox) {
                selectAllCheckbox.onchange = function () {
                    const checkboxes = document.querySelectorAll('.story-checkbox');
                    checkboxes.forEach(cb => cb.checked = this.checked);
                    if (tableSelectAllCheckbox) tableSelectAllCheckbox.checked = this.checked;
                    updateSelectedCount();
                };
            }

            if (tableSelectAllCheckbox) {
                tableSelectAllCheckbox.onchange = function () {
                    const checkboxes = document.querySelectorAll('.story-checkbox');
                    checkboxes.forEach(cb => cb.checked = this.checked);
                    if (selectAllCheckbox) selectAllCheckbox.checked = this.checked;
                    updateSelectedCount();
                };
            }

            // Individual checkboxes
            document.querySelectorAll('.story-checkbox').forEach(cb => {
                cb.onchange = updateSelectedCount;
            });

            // Update story data on input change
            document.querySelectorAll('.story-summary-input, .story-description-input, .story-priority-select').forEach(input => {
                input.onchange = function () {
                    const index = parseInt(this.dataset.index);
                    if (currentStoriesData && currentStoriesData[index]) {
                        if (this.classList.contains('story-summary-input')) {
                            currentStoriesData[index].summary = this.value;
                        } else if (this.classList.contains('story-description-input')) {
                            currentStoriesData[index].description = this.value;
                        } else if (this.classList.contains('story-priority-select')) {
                            currentStoriesData[index].priority = this.value;
                        }
                    }
                };
            });

            // Edit buttons
            document.querySelectorAll('.story-edit-btn').forEach(btn => {
                btn.onclick = function () {
                    const index = parseInt(this.getAttribute('data-index'));
                    openEditStoryModal(index);
                };
            });

            // Delete buttons
            document.querySelectorAll('.story-delete-btn').forEach(btn => {
                btn.onclick = function () {
                    const index = parseInt(this.dataset.index);
                    if (confirm('¿Estás seguro de eliminar esta historia?')) {
                        currentStoriesData.splice(index, 1);
                        displayStoriesPreview({ stories: currentStoriesData, stories_count: currentStoriesData.length });
                    }
                };
            });
        }

        function updateSelectedCount() {
            const checkboxes = document.querySelectorAll('.story-checkbox:checked');
            const count = checkboxes.length;
            const countEl = document.getElementById('stories-selected-count');
            if (countEl) {
                countEl.textContent = `${count} historias seleccionadas`;
            }
        }

        // Variables para el modal de edición de historias
        let editingStoryIndex = null;

        function openEditStoryModal(index) {
            if (!currentStoriesData || !currentStoriesData[index]) {
                showDownloadNotification('Error: Historia no encontrada', 'error');
                return;
            }

            const story = currentStoriesData[index];
            editingStoryIndex = index;

            // Llenar campos del modal
            const summaryInput = document.getElementById('edit-story-summary');
            const descriptionInput = document.getElementById('edit-story-description');
            const issuetypeSelect = document.getElementById('edit-story-issuetype');
            const prioritySelect = document.getElementById('edit-story-priority');

            if (summaryInput) summaryInput.value = story.summary || '';
            if (descriptionInput) descriptionInput.value = story.description || '';
            if (issuetypeSelect) issuetypeSelect.value = story.issuetype || 'Story';
            if (prioritySelect) prioritySelect.value = story.priority || 'Medium';

            // Mostrar modal
            const modal = document.getElementById('edit-story-modal');
            if (modal) modal.style.display = 'flex';
        }

        function closeEditStoryModal() {
            const modal = document.getElementById('edit-story-modal');
            if (modal) modal.style.display = 'none';
            editingStoryIndex = null;
        }

        function saveStoryChanges() {
            if (editingStoryIndex === null) return;

            const summaryInput = document.getElementById('edit-story-summary');
            const descriptionInput = document.getElementById('edit-story-description');
            const issuetypeSelect = document.getElementById('edit-story-issuetype');
            const prioritySelect = document.getElementById('edit-story-priority');

            if (!summaryInput || !descriptionInput || !issuetypeSelect || !prioritySelect) {
                showDownloadNotification('Error: Campos del modal no encontrados', 'error');
                return;
            }

            const summary = summaryInput.value.trim();
            const description = descriptionInput.value.trim();
            const issuetype = issuetypeSelect.value;
            const priority = prioritySelect.value;

            if (!summary || !description) {
                showDownloadNotification('Por favor completa todos los campos requeridos', 'error');
                return;
            }

            // Actualizar datos
            currentStoriesData[editingStoryIndex].summary = summary;
            currentStoriesData[editingStoryIndex].description = description;
            currentStoriesData[editingStoryIndex].issuetype = issuetype;
            currentStoriesData[editingStoryIndex].priority = priority;

            // Actualizar vista previa
            displayStoriesPreview({ stories: currentStoriesData, stories_count: currentStoriesData.length });

            closeEditStoryModal();
            showDownloadNotification('Historia actualizada exitosamente', 'success');
        }

        // Event listeners del modal de edición de historias
        const editStoryModalClose = document.getElementById('edit-story-modal-close');
        const editStoryCancel = document.getElementById('edit-story-cancel');
        const editStorySave = document.getElementById('edit-story-save');
        if (editStoryModalClose) editStoryModalClose.onclick = closeEditStoryModal;
        if (editStoryCancel) editStoryCancel.onclick = closeEditStoryModal;
        if (editStorySave) editStorySave.onclick = saveStoryChanges;

        // Botón revisar historias (visualizar HTML)
        const reviewBtn = document.getElementById('stories-review-btn');
        if (reviewBtn) {
            reviewBtn.onclick = function () {
                if (!currentStoriesData || currentStoriesData.length === 0) {
                    showDownloadNotification('No hay historias para revisar', 'error');
                    return;
                }
                openStoriesReview();
            };
        }

        function openStoriesReview() {
            const modal = document.getElementById('stories-review-modal');
            const iframe = document.getElementById('stories-html-viewer');

            if (!modal || !iframe) {
                showDownloadNotification('Error: Modal de revisión no encontrado', 'error');
                return;
            }

            // NO regenerar HTML - usar el HTML original guardado
            if (!currentStoriesHtml) {
                showDownloadNotification('No hay HTML disponible para revisar', 'error');
                return;
            }

            // Crear blob con el HTML original y mostrarlo en iframe
            const blob = new Blob([currentStoriesHtml], { type: 'text/html;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            iframe.src = url;

            modal.style.display = 'flex';
        }

        // Hacer funciones accesibles globalmente para los onclick del modal
        window.closeStoriesReview = function () {
            const modal = document.getElementById('stories-review-modal');
            const iframe = document.getElementById('stories-html-viewer');

            if (iframe && iframe.src) {
                URL.revokeObjectURL(iframe.src);
                iframe.src = '';
            }

            if (modal) {
                modal.style.display = 'none';
            }
        };

        window.downloadStoriesHTML = function () {
            if (!currentStoriesData || currentStoriesData.length === 0) {
                showDownloadNotification('No hay historias para descargar', 'error');
                return;
            }

            // NO regenerar HTML - usar el HTML original guardado
            if (!currentStoriesHtml) {
                showDownloadNotification('No hay HTML disponible para descargar', 'error');
                return;
            }

            const blob = new Blob([currentStoriesHtml], { type: 'text/html;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'historias_usuario.html';
            document.body.appendChild(a);
            a.click();
            URL.revokeObjectURL(url);
            document.body.removeChild(a);
            showDownloadNotification('HTML descargado exitosamente', 'success');
        };

        // Botón subir a Jira
        const uploadJiraBtn = document.getElementById('stories-upload-jira-btn');
        if (uploadJiraBtn) {
            uploadJiraBtn.onclick = function () {
                const selected = document.querySelectorAll('.story-checkbox:checked');
                if (selected.length === 0) {
                    showDownloadNotification('Por favor selecciona al menos una historia para subir', 'error');
                    return;
                }

                // Obtener historias seleccionadas
                const selectedStories = Array.from(selected).map(cb => {
                    const index = parseInt(cb.dataset.index);
                    return currentStoriesData[index];
                });

                // Cargar proyectos de Jira y mostrar modal
                loadJiraProjects().then(() => {
                    document.getElementById('jira-modal-stories-count').textContent = `${selectedStories.length} historias seleccionadas para subir`;
                    window.selectedStoriesForUpload = selectedStories;
                    document.getElementById('jira-upload-modal').style.display = 'flex';
                });
            };
        }

        // Cerrar modal
        const modalClose = document.getElementById('jira-modal-close');
        const modalCancel = document.getElementById('jira-modal-cancel');
        if (modalClose) modalClose.onclick = closeJiraModal;
        if (modalCancel) modalCancel.onclick = closeJiraModal;

        function closeJiraModal() {
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
        }

        // Validar email de asignado
        const assigneeInput = document.getElementById('jira-assignee-input');
        if (assigneeInput) {
            assigneeInput.addEventListener('blur', async function () {
                const email = this.value.trim();
                const validationDiv = document.getElementById('jira-assignee-validation');

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

                // Validar en Jira
                validationDiv.style.display = 'block';
                validationDiv.style.color = 'var(--text-muted)';
                validationDiv.textContent = '⏳ Validando usuario...';

                try {
                    const response = await fetch('/api/jira/validate-user', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCsrfToken()
                        },
                        body: JSON.stringify({ email: email })
                    });

                    const data = await response.json();
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
            });
        }

        // Cargar proyectos de Jira
        async function loadJiraProjects() {
            const hiddenInput = document.getElementById('jira-project-select');
            const searchInput = document.getElementById('jira-project-search-input');
            if (!hiddenInput) return;

            try {
                const response = await fetch('/api/jira/projects', {
                    headers: { 'X-CSRFToken': getCsrfToken() }
                });

                if (response.ok) {
                    const data = await response.json();
                    allProjectsStories = data.projects || [];

                    if (allProjectsStories.length === 0) {
                        showDownloadNotification('No se encontraron proyectos de Jira. Verifica tu configuración.', 'error');
                        return;
                    }

                    // Configurar el combo box
                    setupSearchableCombo({
                        inputId: 'jira-project-search-input',
                        dropdownId: 'jira-project-dropdown',
                        hiddenId: 'jira-project-select',
                        dataArray: allProjectsStories
                    });
                } else {
                    const errorData = await response.json();
                    showDownloadNotification('Error al cargar proyectos: ' + (errorData.error || 'Error desconocido'), 'error');
                }
            } catch (error) {
                console.error('Error al cargar proyectos:', error);
                showDownloadNotification('Error de conexión al cargar proyectos', 'error');
            }
        }

        // Subir a Jira
        const modalUploadBtn = document.getElementById('jira-modal-upload');
        if (modalUploadBtn) {
            modalUploadBtn.onclick = async function () {
                const projectKey = document.getElementById('jira-project-select').value;
                if (!projectKey) {
                    showDownloadNotification('Por favor selecciona un proyecto', 'error');
                    return;
                }

                const assigneeEmail = document.getElementById('jira-assignee-input').value.trim();
                const validationDiv = document.getElementById('jira-assignee-validation');

                // Validar asignado si se proporciona
                if (assigneeEmail) {
                    // Si no se ha validado aún o la validación falló, validar ahora
                    const isValidated = validationDiv.style.display === 'block' && validationDiv.textContent.includes('✅');
                    const isInvalid = validationDiv.style.display === 'block' && validationDiv.textContent.includes('❌');

                    if (!isValidated && !isInvalid) {
                        // Validar ahora antes de continuar
                        validationDiv.style.display = 'block';
                        validationDiv.style.color = 'var(--text-muted)';
                        validationDiv.textContent = '⏳ Validando usuario...';

                        try {
                            const validateResponse = await fetch('/api/jira/validate-user', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'X-CSRFToken': getCsrfToken()
                                },
                                body: JSON.stringify({ email: assigneeEmail })
                            });

                            const validateData = await validateResponse.json();
                            if (validateData.valid) {
                                validationDiv.style.color = 'var(--success)';
                                validationDiv.textContent = '✅ Usuario encontrado en Jira';
                                window.assigneeAccountId = validateData.accountId;
                            } else {
                                validationDiv.style.color = 'var(--error)';
                                validationDiv.textContent = '❌ ' + (validateData.error || 'Este correo no tiene cuenta en Jira');
                                window.assigneeAccountId = null;
                                showDownloadNotification('Por favor verifica que el email del asignado sea válido y tenga cuenta en Jira', 'error');
                                return;
                            }
                        } catch (error) {
                            validationDiv.style.color = 'var(--error)';
                            validationDiv.textContent = '❌ Error al validar usuario';
                            window.assigneeAccountId = null;
                            showDownloadNotification('Error al validar usuario de Jira', 'error');
                            return;
                        }
                    } else if (isInvalid) {
                        // Ya se validó y es inválido
                        showDownloadNotification('Por favor verifica que el email del asignado sea válido y tenga cuenta en Jira', 'error');
                        return;
                    } else if (!isValidated) {
                        // No se ha validado aún
                        showDownloadNotification('Por favor verifica que el email del asignado sea válido y tenga cuenta en Jira', 'error');
                        return;
                    }
                }

                // Mostrar loading
                document.getElementById('stories-loading-overlay').style.display = 'flex';

                try {
                    const response = await fetch('/api/jira/stories/upload-to-jira', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCsrfToken()
                        },
                        body: JSON.stringify({
                            stories: window.selectedStoriesForUpload,
                            project_key: projectKey,
                            assignee_email: assigneeEmail || null
                        })
                    });

                    const data = await response.json();

                    document.getElementById('stories-loading-overlay').style.display = 'none';
                    closeJiraModal();

                    if (data.success) {
                        showDownloadNotification(data.message || 'Historias subidas exitosamente a Jira', 'success');

                        // Descargar archivo TXT si está disponible
                        if (data.txt_content && data.txt_filename) {
                            try {
                                // Decodificar base64 y convertir a UTF-8
                                const binaryString = atob(data.txt_content);
                                const bytes = new Uint8Array(binaryString.length);
                                for (let i = 0; i < binaryString.length; i++) {
                                    bytes[i] = binaryString.charCodeAt(i);
                                }
                                const txtBlob = new Blob([bytes], { type: 'text/plain;charset=utf-8' });
                                const txtUrl = URL.createObjectURL(txtBlob);
                                const txtLink = document.createElement('a');
                                txtLink.href = txtUrl;
                                txtLink.download = data.txt_filename;
                                document.body.appendChild(txtLink);
                                txtLink.click();
                                document.body.removeChild(txtLink);
                                URL.revokeObjectURL(txtUrl);
                            } catch (error) {
                                console.error('Error al descargar TXT:', error);
                            }
                        }

                        // Opcional: ocultar historias subidas o actualizar vista
                    } else {
                        showDownloadNotification('Error: ' + (data.error || 'No se pudieron subir las historias'), 'error');

                        // Descargar TXT incluso si hay errores
                        if (data.txt_content && data.txt_filename) {
                            try {
                                // Decodificar base64 y convertir a UTF-8
                                const binaryString = atob(data.txt_content);
                                const bytes = new Uint8Array(binaryString.length);
                                for (let i = 0; i < binaryString.length; i++) {
                                    bytes[i] = binaryString.charCodeAt(i);
                                }
                                const txtBlob = new Blob([bytes], { type: 'text/plain;charset=utf-8' });
                                const txtUrl = URL.createObjectURL(txtBlob);
                                const txtLink = document.createElement('a');
                                txtLink.href = txtUrl;
                                txtLink.download = data.txt_filename;
                                document.body.appendChild(txtLink);
                                txtLink.click();
                                document.body.removeChild(txtLink);
                                URL.revokeObjectURL(txtUrl);
                            } catch (error) {
                                console.error('Error al descargar TXT:', error);
                            }
                        }
                    }
                } catch (error) {
                    document.getElementById('stories-loading-overlay').style.display = 'none';
                    showDownloadNotification('Error de conexión: ' + error.message, 'error');
                }
            };
        }
    })();

    // ========================================================================
    // CREAR CASOS DE PRUEBA - JavaScript
    // ========================================================================
    (function () {
        // Función para resetear el generador de casos de prueba
        function resetTestsGenerator() {
            const formContainer = document.getElementById('tests-form-container');
            const previewSection = document.getElementById('tests-preview-section');
            const backBtnContainer = document.getElementById('tests-back-btn-container');
            const testsForm = document.getElementById('tests-form');
            const testsFileInput = document.getElementById('tests-file');
            const testsFileInfo = document.getElementById('tests-file-info');
            const testsFileName = document.getElementById('tests-file-name');
            const testsRemoveFileBtn = document.getElementById('tests-remove-file-btn');
            const testsContext = document.getElementById('tests-context');
            const testsContextCounter = document.getElementById('tests-context-counter');
            const testsType = document.getElementById('tests-type');
            const testsArea = document.getElementById('tests-area');
            const previewTbody = document.getElementById('tests-preview-tbody');
            const previewCount = document.getElementById('tests-preview-count');
            const selectedCount = document.getElementById('tests-selected-count');

            // Resetear formulario
            if (testsForm) testsForm.reset();
            if (testsFileInput) testsFileInput.value = '';
            if (testsFileInfo) testsFileInfo.style.display = 'none';
            if (testsFileName) testsFileName.textContent = '';
            if (testsRemoveFileBtn) testsRemoveFileBtn.style.display = 'none';
            if (testsContext) testsContext.value = '';
            if (testsContextCounter) testsContextCounter.textContent = '0 / 2000 caracteres';
            if (testsType) testsType.value = 'funcionalidad';
            if (testsArea) testsArea.value = '';

            // Limpiar vista previa
            if (previewTbody) previewTbody.innerHTML = '';
            if (previewCount) previewCount.textContent = '0';
            if (selectedCount) selectedCount.textContent = '0 casos seleccionados';

            // Resetear checkboxes
            const selectAllCheckbox = document.getElementById('tests-select-all');
            const tableSelectAllCheckbox = document.getElementById('tests-table-select-all');
            if (selectAllCheckbox) selectAllCheckbox.checked = false;
            if (tableSelectAllCheckbox) tableSelectAllCheckbox.checked = false;

            // Limpiar variables globales
            window.selectedTestsForUpload = [];
            window.testsData = null;
            currentTestsData = null;
            currentTestsHtml = null;
            currentTestsCsv = null;

            // Mostrar formulario y ocultar vista previa
            if (formContainer) formContainer.style.display = 'block';
            if (previewSection) previewSection.style.display = 'none';
            if (backBtnContainer) backBtnContainer.style.display = 'none';

            // Asegurar que el form-card también se muestre
            const testsFormCard = document.getElementById('tests-form');
            if (testsFormCard) {
                const formCard = testsFormCard.closest('.form-card');
                if (formCard) formCard.style.display = 'block';
            }

            // Activar la sección de crear casos de prueba
            if (typeof navigateToSection === 'function') {
                navigateToSection('crear-casos-prueba');
            } else {
                // Fallback: activar manualmente si navigateToSection no está disponible
                const crearCasosPruebaSection = document.getElementById('crear-casos-prueba');
                if (crearCasosPruebaSection) {
                    // Ocultar todas las secciones
                    document.querySelectorAll('.content-section').forEach(section => {
                        section.classList.remove('active');
                    });
                    // Activar la sección de crear casos de prueba
                    crearCasosPruebaSection.classList.add('active');
                    // Actualizar nav-item activo
                    document.querySelectorAll('.nav-item').forEach(item => {
                        item.classList.remove('active-link', 'active');
                    });
                    const activeNav = document.querySelector('[data-section="crear-casos-prueba"]');
                    if (activeNav) {
                        activeNav.classList.add('active-link');
                    }
                    crearCasosPruebaSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }
        }

        // Botón de reset
        const resetBtn = document.getElementById('tests-reset-btn');
        if (resetBtn) {
            resetBtn.onclick = function () {
                if (confirm('¿Estás seguro de que deseas hacer una nueva generación? Se perderán los datos actuales.')) {
                    resetTestsGenerator();
                }
            };
        }

        const testsDropZone = document.getElementById('tests-drop-zone');
        const testsFileInput = document.getElementById('tests-file');
        const testsForm = document.getElementById('tests-form');
        const testsGenerateBtn = document.getElementById('tests-generate-btn');
        const testsFileInfo = document.getElementById('tests-file-info');
        const testsFileName = document.getElementById('tests-file-name');
        const testsRemoveFileBtn = document.getElementById('tests-remove-file-btn');

        if (!testsForm) return;

        // Setup drag and drop (igual que carga masiva)
        function setupTestsDropZone() {
            if (!testsDropZone || !testsFileInput) return;

            // Click en la zona de arrastre - FIX: usar mousedown en lugar de click para evitar doble click
            testsDropZone.addEventListener('mousedown', (e) => {
                // Solo si el click es directamente en el dropZone, no en elementos hijos
                if (e.target === testsDropZone || e.target.closest('.drop-zone-content')) {
                    e.preventDefault();
                    testsFileInput.click();
                }
            });

            // Prevenir comportamiento por defecto del navegador
            testsDropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.stopPropagation();
                testsDropZone.classList.add('drag-over');
            });

            testsDropZone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                e.stopPropagation();
                testsDropZone.classList.remove('drag-over');
            });

            testsDropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                e.stopPropagation();
                testsDropZone.classList.remove('drag-over');

                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    handleTestsFileSelect(files[0]);
                }
            });

            // Cambio de archivo desde el input - FIX: usar change directamente sin prevenir default
            testsFileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    handleTestsFileSelect(e.target.files[0]);
                }
            });
        }

        function handleTestsFileSelect(file) {
            // Validar que sea DOCX o PDF
            const validExtensions = ['.docx', '.pdf'];
            const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
            if (!validExtensions.includes(fileExtension)) {
                showDownloadNotification('❌ Solo se permiten archivos DOCX o PDF', 'error');
                return;
            }

            // Mostrar información del archivo
            if (testsFileInfo && testsFileName) {
                testsFileName.textContent = file.name;
                testsFileInfo.style.display = 'flex';
            }
        }

        // Botón para remover archivo
        if (testsRemoveFileBtn) {
            testsRemoveFileBtn.addEventListener('click', () => {
                testsFileInput.value = '';
                if (testsFileInfo) {
                    testsFileInfo.style.display = 'none';
                }
            });
        }

        // Variables globales para casos de prueba
        let currentTestsData = null;
        let currentTestsHtml = null;
        let currentTestsCsv = null;

        // Función helper para escapar HTML (necesaria para displayTestsPreview)
        function escapeHtml(text) {
            if (text === null || text === undefined) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Función para formatear un caso de prueba individual para HTML
        function formatTestCaseForHTML(testCase, caseNum) {
            const title = testCase.summary || `Caso de Prueba ${caseNum}`;
            const description = testCase.description || '';
            const priority = testCase.priority || 'Medium';
            const categoria = testCase.categoria || '';
            const tipoPrueba = testCase.tipo_prueba || 'Funcional';

            // Extraer información adicional de la descripción si está disponible
            const pasosMatch = description.match(/Pasos?:?\s*([\s\S]*?)(?=Resultado|$)/i);
            const resultadoMatch = description.match(/Resultado\s+esperado:?\s*([\s\S]*?)(?=Precondiciones|$)/i);
            const precondicionesMatch = description.match(/Precondiciones:?\s*([\s\S]*?)(?=Pasos|Resultado|$)/i);

            let html = `<div class="story-container">
        <div class="story-title">CASO DE PRUEBA #${caseNum}: ${escapeHtml(title)}</div>`;

            if (description) {
                // Si hay pasos y resultado en la descripción, mostrarlos por separado
                if (pasosMatch || resultadoMatch || precondicionesMatch) {
                    if (precondicionesMatch) {
                        html += `
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Precondiciones:</span>
                            <span class="story-item-content"> ${escapeHtml(precondicionesMatch[1].trim())}</span>
                        </div>`;
                    }

                    if (pasosMatch) {
                        const pasos = pasosMatch[1].trim().split(/\d+\./).filter(p => p.trim());
                        if (pasos.length > 0) {
                            html += `
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Pasos:</span>
                            <div class="story-sublist">`;
                            pasos.forEach((paso, i) => {
                                if (paso.trim()) {
                                    html += `
                                <div class="story-sublist-item">
                                    <span class="bullet">*</span>
                                    <strong>Paso ${i + 1}:</strong> ${escapeHtml(paso.trim())}
                                </div>`;
                                }
                            });
                            html += `
                            </div>
                        </div>`;
                        }
                    }

                    if (resultadoMatch) {
                        html += `
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Resultado Esperado:</span>
                            <span class="story-item-content"> ${escapeHtml(resultadoMatch[1].trim())}</span>
                        </div>`;
                    }
                } else {
                    // Mostrar descripción completa si no tiene estructura
                    html += `
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Descripción:</span>
                            <span class="story-item-content"> ${escapeHtml(description)}</span>
                        </div>`;
                }
            }

            if (tipoPrueba) {
                html += `
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Tipo de Prueba:</span>
                            <span class="story-item-content"> ${escapeHtml(tipoPrueba)}</span>
                        </div>`;
            }

            if (categoria) {
                html += `
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Categoría:</span>
                            <span class="story-item-content"> ${escapeHtml(categoria)}</span>
                        </div>`;
            }

            html += `
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Prioridad:</span>
                            <span class="story-item-content"> ${priority}</span>
                        </div>
                    </div>`;

            return html;
        }

        // Función para mostrar vista previa de casos de prueba
        function displayTestsPreview(data) {
            console.log('🔍 displayTestsPreview INICIADO');
            console.log('📦 data recibida:', data);
            console.log('📋 data.test_cases:', data.test_cases);
            console.log('🔢 Cantidad de casos:', data.test_cases ? data.test_cases.length : 'undefined');

            currentTestsData = data.test_cases;
            // Si no llega HTML/CSV en esta actualización (ej. edición), conservamos el original
            if (data.html_content) currentTestsHtml = data.html_content;
            if (data.csv_content) currentTestsCsv = data.csv_content;

            const previewSection = document.getElementById('tests-preview-section');
            const previewCount = document.getElementById('tests-preview-count');
            const previewTbody = document.getElementById('tests-preview-tbody');
            const testsForm = document.getElementById('tests-form');

            console.log('🔍 Elementos DOM encontrados:', {
                previewSection: !!previewSection,
                previewCount: !!previewCount,
                previewTbody: !!previewTbody,
                testsForm: !!testsForm
            });

            if (!previewSection || !previewCount || !previewTbody) {
                console.error('❌ ERROR: Elementos del DOM no encontrados');
                return;
            }

            // Ocultar formulario y mostrar vista previa
            if (testsForm) {
                testsForm.closest('.form-card').style.display = 'none';
            }
            previewSection.style.display = 'block';
            previewCount.textContent = data.test_cases_count || (data.test_cases ? data.test_cases.length : 0);
            console.log('✅ Sección de vista previa mostrada, contador actualizado:', previewCount.textContent);

            // Limpiar tabla
            previewTbody.innerHTML = '';
            console.log('🧹 Tabla limpiada');

            // Agregar casos de prueba a la tabla
            console.log('🔄 Iniciando forEach para agregar casos...');
            let casosAgregados = 0;
            data.test_cases.forEach((testCase, index) => {
                try {
                    console.log(`📝 Procesando caso ${index + 1}:`, testCase);

                    // Validar y obtener valores con fallbacks seguros
                    const caseIndex = testCase.index !== undefined ? testCase.index : (index + 1);
                    const caseSummary = testCase.summary || 'Sin título';
                    const caseDescription = testCase.description || '';
                    const caseIssuetype = testCase.issuetype || 'Test Case';
                    const casePriority = testCase.priority || 'Medium';
                    const caseTipoPrueba = testCase.tipo_prueba || 'Funcional';
                    const caseCategoria = testCase.categoria || '';

                    const row = document.createElement('tr');
                    row.innerHTML = `
                            <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                                <input type="checkbox" class="test-checkbox" data-index="${index}" checked style="width: 18px; height: 18px; cursor: pointer;">
                            </td>
                            <td style="padding: 1rem; border-bottom: 1px solid var(--border); font-weight: 600; color: var(--accent); text-align: center;">${caseIndex}</td>
                            <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                                <input type="text" class="test-summary-input" data-index="${index}" value="${escapeHtml(caseSummary)}" style="width: 100%; max-width: 300px; padding: 0.5rem; background: transparent; border: 1px solid transparent; border-radius: 4px; color: var(--text-primary); font-family: inherit; font-size: 0.9rem;">
                            </td>
                            <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                                <textarea class="test-description-input" data-index="${index}" rows="2" style="width: 100%; max-width: 400px; padding: 0.5rem; background: transparent; border: 1px solid transparent; border-radius: 4px; color: var(--text-secondary); font-family: inherit; font-size: 0.85rem; resize: none; min-height: 50px;">${escapeHtml(caseDescription)}</textarea>
                            </td>
                            <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                                <span style="display: inline-block; padding: 0.25rem 0.75rem; border-radius: 6px; font-size: 0.8rem; font-weight: 500; background: rgba(59, 130, 246, 0.2); color: var(--accent);">${escapeHtml(caseIssuetype)}</span>
                            </td>
                            <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                                <span style="display: inline-block; padding: 0.25rem 0.75rem; border-radius: 6px; font-size: 0.8rem; font-weight: 500; background: rgba(34, 197, 94, 0.2); color: #22c55e;">${escapeHtml(caseTipoPrueba)}</span>
                            </td>
                            <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                                <span style="display: inline-block; padding: 0.25rem 0.75rem; border-radius: 6px; font-size: 0.8rem; font-weight: 500; background: rgba(168, 85, 247, 0.2); color: #a855f7;">${escapeHtml(caseCategoria)}</span>
                            </td>
                            <td style="padding: 1rem; border-bottom: 1px solid var(--border);">
                                <select class="test-priority-select" data-index="${index}" style="padding: 0.5rem; background: var(--secondary-bg); border: 1px solid var(--border); border-radius: 4px; color: var(--text-primary); font-family: inherit; font-size: 0.9rem;">
                                    <option value="High" ${casePriority === 'High' ? 'selected' : ''}>High</option>
                                    <option value="Medium" ${casePriority === 'Medium' ? 'selected' : ''}>Medium</option>
                                    <option value="Low" ${casePriority === 'Low' ? 'selected' : ''}>Low</option>
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
                    casosAgregados++;
                    console.log(`✅ Caso ${index + 1} agregado exitosamente`);
                } catch (error) {
                    console.error(`❌ Error al agregar caso ${index + 1}:`, error, testCase);
                }
            });

            console.log(`✅ Total de casos agregados a la tabla: ${casosAgregados}`);
            console.log(`📊 Filas en tbody: ${previewTbody.children.length}`);

            // Event listeners para edición
            updateTestsEventListeners();
            updateTestsSelectedCount();
            console.log('✅ displayTestsPreview COMPLETADO');
        }

        function updateTestsEventListeners() {
            // Select all checkboxes
            const selectAllCheckbox = document.getElementById('tests-select-all');
            const tableSelectAllCheckbox = document.getElementById('tests-table-select-all');

            if (selectAllCheckbox) {
                selectAllCheckbox.onchange = function () {
                    const checkboxes = document.querySelectorAll('.test-checkbox');
                    checkboxes.forEach(cb => cb.checked = this.checked);
                    if (tableSelectAllCheckbox) tableSelectAllCheckbox.checked = this.checked;
                    updateTestsSelectedCount();
                };
            }

            if (tableSelectAllCheckbox) {
                tableSelectAllCheckbox.onchange = function () {
                    const checkboxes = document.querySelectorAll('.test-checkbox');
                    checkboxes.forEach(cb => cb.checked = this.checked);
                    if (selectAllCheckbox) selectAllCheckbox.checked = this.checked;
                    updateTestsSelectedCount();
                };
            }

            // Individual checkboxes
            document.querySelectorAll('.test-checkbox').forEach(cb => {
                cb.onchange = updateTestsSelectedCount;
            });

            // Update test case data on input change
            document.querySelectorAll('.test-summary-input, .test-description-input, .test-priority-select').forEach(input => {
                input.onchange = function () {
                    const index = parseInt(this.dataset.index);
                    if (currentTestsData && currentTestsData[index]) {
                        if (this.classList.contains('test-summary-input')) {
                            currentTestsData[index].summary = this.value;
                        } else if (this.classList.contains('test-description-input')) {
                            currentTestsData[index].description = this.value;
                        } else if (this.classList.contains('test-priority-select')) {
                            currentTestsData[index].priority = this.value;
                        }
                    }
                };
            });

            // Edit buttons
            document.querySelectorAll('.test-edit-btn').forEach(btn => {
                btn.onclick = function () {
                    const index = parseInt(this.getAttribute('data-index'));
                    openEditTestModal(index);
                };
            });

            // Delete buttons
            document.querySelectorAll('.test-delete-btn').forEach(btn => {
                btn.onclick = function () {
                    const index = parseInt(this.dataset.index);
                    if (confirm('¿Estás seguro de eliminar este caso de prueba?')) {
                        currentTestsData.splice(index, 1);
                        displayTestsPreview({ test_cases: currentTestsData, test_cases_count: currentTestsData.length });
                    }
                };
            });
        }

        function updateTestsSelectedCount() {
            const checkboxes = document.querySelectorAll('.test-checkbox:checked');
            const count = checkboxes.length;
            const countEl = document.getElementById('tests-selected-count');
            if (countEl) {
                countEl.textContent = `${count} casos seleccionados`;
            }
        }

        // Variables para el modal de edición de casos de prueba
        let editingTestIndex = null;

        function openEditTestModal(index) {
            if (!currentTestsData || !currentTestsData[index]) {
                showDownloadNotification('Error: Caso de prueba no encontrado', 'error');
                return;
            }

            const testCase = currentTestsData[index];
            editingTestIndex = index;

            // Llenar campos del modal
            const summaryInput = document.getElementById('edit-test-summary');
            const descriptionInput = document.getElementById('edit-test-description');
            const prioritySelect = document.getElementById('edit-test-priority');
            const categoriaInput = document.getElementById('edit-test-categoria');

            if (summaryInput) summaryInput.value = testCase.summary || '';
            if (descriptionInput) descriptionInput.value = testCase.description || '';
            if (prioritySelect) prioritySelect.value = testCase.priority || 'Medium';
            if (categoriaInput) categoriaInput.value = testCase.categoria || '';

            // Mostrar modal
            const modal = document.getElementById('edit-test-modal');
            if (modal) modal.style.display = 'flex';
        }

        function closeEditTestModal() {
            const modal = document.getElementById('edit-test-modal');
            if (modal) modal.style.display = 'none';
            editingTestIndex = null;
        }

        function saveTestChanges() {
            if (editingTestIndex === null) return;

            const summaryInput = document.getElementById('edit-test-summary');
            const descriptionInput = document.getElementById('edit-test-description');
            const prioritySelect = document.getElementById('edit-test-priority');
            const categoriaInput = document.getElementById('edit-test-categoria');

            if (!summaryInput || !descriptionInput || !prioritySelect || !categoriaInput) {
                showDownloadNotification('Error: Campos del modal no encontrados', 'error');
                return;
            }

            const summary = summaryInput.value.trim();
            const description = descriptionInput.value.trim();
            const priority = prioritySelect.value;
            const categoria = categoriaInput.value.trim();

            if (!summary || !description) {
                showDownloadNotification('Por favor completa todos los campos requeridos', 'error');
                return;
            }

            // Actualizar datos
            currentTestsData[editingTestIndex].summary = summary;
            currentTestsData[editingTestIndex].description = description;
            currentTestsData[editingTestIndex].priority = priority;
            currentTestsData[editingTestIndex].categoria = categoria;

            // Actualizar vista previa
            displayTestsPreview({ test_cases: currentTestsData, test_cases_count: currentTestsData.length });

            closeEditTestModal();
            showDownloadNotification('Caso de prueba actualizado exitosamente', 'success');
        }

        // Event listeners del modal de edición de casos de prueba
        const editTestModalClose = document.getElementById('edit-test-modal-close');
        const editTestCancel = document.getElementById('edit-test-cancel');
        const editTestSave = document.getElementById('edit-test-save');
        if (editTestModalClose) editTestModalClose.onclick = closeEditTestModal;
        if (editTestCancel) editTestCancel.onclick = closeEditTestModal;
        if (editTestSave) editTestSave.onclick = saveTestChanges;

        // Botón revisar casos (visualizar HTML)
        const testsReviewBtn = document.getElementById('tests-review-btn');
        if (testsReviewBtn) {
            testsReviewBtn.onclick = function () {
                if (!currentTestsData || currentTestsData.length === 0) {
                    showDownloadNotification('No hay casos de prueba para revisar', 'error');
                    return;
                }
                openTestsReview();
            };
        }

        function openTestsReview() {
            const modal = document.getElementById('tests-review-modal');
            const iframe = document.getElementById('tests-html-viewer');

            if (!modal || !iframe) {
                showDownloadNotification('Error: Modal de revisión no encontrado', 'error');
                return;
            }

            // NO regenerar HTML - usar el HTML original guardado
            if (!currentTestsHtml) {
                showDownloadNotification('No hay HTML disponible para revisar', 'error');
                return;
            }

            // Crear blob con el HTML original y mostrarlo en iframe
            const blob = new Blob([currentTestsHtml], { type: 'text/html;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            iframe.src = url;

            modal.style.display = 'flex';
        }

        // Hacer funciones accesibles globalmente para los onclick del modal
        window.closeTestsReview = function () {
            const modal = document.getElementById('tests-review-modal');
            const iframe = document.getElementById('tests-html-viewer');

            if (iframe && iframe.src) {
                URL.revokeObjectURL(iframe.src);
                iframe.src = '';
            }

            if (modal) {
                modal.style.display = 'none';
            }
        };

        window.downloadTestsHTML = function () {
            if (!currentTestsData || currentTestsData.length === 0) {
                showDownloadNotification('No hay casos de prueba para descargar', 'error');
                return;
            }

            // NO regenerar HTML - usar el HTML original guardado
            if (!currentTestsHtml) {
                showDownloadNotification('No hay HTML disponible para descargar', 'error');
                return;
            }

            const blob = new Blob([currentTestsHtml], { type: 'text/html;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'casos_prueba.html';
            document.body.appendChild(a);
            a.click();
            URL.revokeObjectURL(url);
            document.body.removeChild(a);
            showDownloadNotification('HTML descargado exitosamente', 'success');
        };

        // Botón subir a Jira
        const testsUploadJiraBtn = document.getElementById('tests-upload-jira-btn');
        if (testsUploadJiraBtn) {
            testsUploadJiraBtn.onclick = function () {
                const selected = document.querySelectorAll('.test-checkbox:checked');
                if (selected.length === 0) {
                    showDownloadNotification('Por favor selecciona al menos un caso de prueba para subir', 'error');
                    return;
                }

                // Obtener casos seleccionados
                const selectedTests = Array.from(selected).map(cb => {
                    const index = parseInt(cb.dataset.index);
                    return currentTestsData[index];
                });

                window.selectedTestsForUpload = selectedTests;
                openJiraTestsModal();
            };
        }

        // Generate handler
        if (testsForm) {
            testsForm.addEventListener('submit', async (e) => {
                e.preventDefault();

                // Validación completa de campos requeridos
                const validationErrors = [];

                // Validar archivo
                if (!testsFileInput.files.length) {
                    validationErrors.push('📄 Debes cargar un archivo (DOCX o PDF)');
                }

                // Validar área
                const areaSelect = document.getElementById('tests-area');
                if (!areaSelect || !areaSelect.value) {
                    validationErrors.push('📋 Debes seleccionar un área');
                }

                // Validar tipo de prueba
                const selectedTypes = Array.from(document.querySelectorAll('input[name="test_types"]:checked')).map(cb => cb.value);
                if (selectedTypes.length === 0) {
                    validationErrors.push('✅ Debes seleccionar al menos un tipo de prueba');
                }

                // Si hay errores, mostrarlos
                if (validationErrors.length > 0) {
                    const errorMessage = '⚠️ No puedes generar la vista previa:\n\n' + validationErrors.join('\n');
                    showDownloadNotification(errorMessage, 'error');

                    // Resaltar campos faltantes con animación
                    if (!testsFileInput.files.length) {
                        const dropZone = document.getElementById('tests-drop-zone');
                        if (dropZone) {
                            dropZone.style.border = '2px solid #ef4444';
                            dropZone.style.boxShadow = '0 0 0 3px rgba(239, 68, 68, 0.2)';
                            dropZone.style.animation = 'shake 0.5s';
                            setTimeout(() => {
                                dropZone.style.border = '';
                                dropZone.style.boxShadow = '';
                                dropZone.style.animation = '';
                            }, 3000);
                        }
                    }

                    if (!areaSelect || !areaSelect.value) {
                        if (areaSelect) {
                            areaSelect.style.border = '2px solid #ef4444';
                            areaSelect.style.boxShadow = '0 0 0 3px rgba(239, 68, 68, 0.2)';
                            areaSelect.style.animation = 'shake 0.5s';
                            setTimeout(() => {
                                areaSelect.style.border = '';
                                areaSelect.style.boxShadow = '';
                                areaSelect.style.animation = '';
                            }, 3000);
                        }
                    }

                    if (selectedTypes.length === 0) {
                        const checkboxContainers = document.querySelectorAll('input[name="test_types"]');
                        checkboxContainers.forEach(cb => {
                            const parent = cb.closest('div[style*="padding: 1rem"]');
                            if (parent) {
                                parent.style.border = '2px solid #ef4444';
                                parent.style.boxShadow = '0 0 0 3px rgba(239, 68, 68, 0.2)';
                                parent.style.animation = 'shake 0.5s';
                                setTimeout(() => {
                                    parent.style.border = '';
                                    parent.style.boxShadow = '';
                                    parent.style.animation = '';
                                }, 3000);
                            }
                        });
                    }

                    return;
                }

                const selectedArea = areaSelect.value;
                const formData = new FormData(testsForm);

                // UI Setup for Progress
                testsGenerateBtn.disabled = true;
                testsGenerateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';

                const progressContainer = document.getElementById('tests-progress-container');
                const progressBar = document.getElementById('tests-progress-bar');
                const progressPhase = document.getElementById('tests-progress-phase');
                const progressPercentage = document.getElementById('tests-progress-percentage');
                const progressMessage = document.getElementById('tests-progress-message');

                if (progressContainer) progressContainer.style.display = 'block';
                if (progressBar) progressBar.style.width = '0%';
                if (progressPhase) progressPhase.textContent = 'Iniciando generación...';
                if (progressPercentage) progressPercentage.textContent = '0%';

                try {
                    const response = await fetch('/api/tests/generate', {
                        method: 'POST',
                        body: formData,
                        headers: {
                            'X-CSRFToken': getCsrfToken()
                        }
                    });

                    if (!response.ok) {
                        throw new Error('Error en la respuesta del servidor');
                    }

                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();
                    let buffer = '';

                    while (true) {
                        const { value, done } = await reader.read();
                        if (done) break;

                        buffer += decoder.decode(value, { stream: true });
                        const lines = buffer.split('\n\n');
                        buffer = lines.pop();

                        for (const line of lines) {
                            if (line.trim().startsWith('data: ')) {
                                try {
                                    const data = JSON.parse(line.trim().substring(6));

                                    // Update Progress UI
                                    if (data.progress !== undefined) {
                                        if (progressBar) progressBar.style.width = `${data.progress}%`;
                                        if (progressPercentage) progressPercentage.textContent = `${data.progress}%`;
                                    }
                                    if (data.status && progressPhase) progressPhase.textContent = data.status;
                                    if (data.message && progressMessage) progressMessage.textContent = data.message;

                                    // Handle Terminal Event
                                    if (data.terminal) {
                                        if (data.error) {
                                            throw new Error(data.error);
                                        }

                                        if (data.data && data.data.test_cases) {
                                            const resultData = data.data;
                                            // Ocultar formulario y mostrar vista previa
                                            const formContainer = document.getElementById('crear-casos-prueba').querySelector('.form-card');
                                            const previewSection = document.getElementById('tests-preview-section');

                                            if (formContainer) formContainer.style.display = 'none';
                                            if (previewSection) previewSection.style.display = 'block';

                                            // Guardar datos globales
                                            currentTestsData = resultData.test_cases;
                                            currentTestsHtml = resultData.html_content;
                                            currentTestsCsv = resultData.csv_content;

                                            // Mostrar vista previa
                                            displayTestsPreview(resultData);

                                            // Actualizar métricas
                                            if (resultData.test_cases_count > 0 && window.NexusModules?.Dashboard?.updateMetrics) {
                                                window.NexusModules.Dashboard.updateMetrics('test_cases', resultData.test_cases_count, selectedArea);
                                            }

                                            showDownloadNotification(`Casos de prueba generados exitosamente: ${resultData.test_cases_count} casos`, 'success');
                                            document.getElementById('crear-casos-prueba').scrollIntoView({ behavior: 'smooth', block: 'start' });
                                        }
                                    }
                                } catch (e) {
                                    console.error('Error parsing SSE data:', e, line);
                                }
                            }
                        }
                    }
                } catch (error) {
                    console.error('Error en generación:', error);
                    showDownloadNotification('Error: ' + error.message, 'error');
                } finally {
                    testsGenerateBtn.disabled = false;
                    testsGenerateBtn.innerHTML = '<i class="fas fa-eye"></i> Generar e Ir a Vista Previa';
                    if (progressContainer) progressContainer.style.display = 'none';
                }
            });
        }

        // Inicializar drag and drop
        setupTestsDropZone();

        // Funciones para modal de Jira (casos de prueba)
        function openJiraTestsModal() {
            const modal = document.getElementById('jira-upload-tests-modal');
            const projectSelect = document.getElementById('jira-tests-project-select');
            const casesCountEl = document.getElementById('jira-tests-modal-cases-count');

            if (!modal || !projectSelect) {
                showDownloadNotification('Error: Modal de Jira no encontrado', 'error');
                return;
            }

            // Actualizar contador
            if (casesCountEl && window.selectedTestsForUpload) {
                casesCountEl.textContent = `${window.selectedTestsForUpload.length} casos seleccionados para subir`;
            }

            // Cargar proyectos de Jira
            loadJiraProjectsForTests();

            modal.style.display = 'flex';
        }

        function closeJiraTestsModal() {
            const modal = document.getElementById('jira-upload-tests-modal');
            if (modal) {
                modal.style.display = 'none';
            }
            // Limpiar campos y resetear pasos
            const projectSelect = document.getElementById('jira-tests-project-select');
            const assigneeInput = document.getElementById('jira-tests-assignee-input');
            const step1 = document.getElementById('jira-tests-step1');
            const step1_5 = document.getElementById('jira-tests-step1-5');
            const step2 = document.getElementById('jira-tests-step2');
            const validationResult = document.getElementById('jira-tests-validation-result');
            const validateBtn = document.getElementById('jira-tests-validate-fields-btn');
            const uploadBtn = document.getElementById('jira-tests-modal-upload');

            if (projectSelect) projectSelect.value = '';
            if (assigneeInput) assigneeInput.value = '';

            // Limpiar búsqueda y selección
            const searchInput = document.getElementById('jira-tests-project-search-input');
            const dropdown = document.getElementById('jira-tests-project-dropdown');
            if (searchInput) searchInput.value = '';
            if (dropdown) dropdown.style.display = 'none';

            // Reiniciar selects de campos
            const selects = ['jira-tests-tipo-prueba-select', 'jira-tests-nivel-prueba-select',
                'jira-tests-tipo-ejecucion-select', 'jira-tests-ambiente-select'];
            selects.forEach(selectId => {
                const select = document.getElementById(selectId);
                if (select) {
                    select.value = '';
                    select.innerHTML = '<option value="">Cargando valores...</option>';
                }
            });

            // Ocultar mensajes
            const messages = ['jira-tests-tipo-prueba-message', 'jira-tests-nivel-prueba-message',
                'jira-tests-tipo-ejecucion-message', 'jira-tests-ambiente-message'];
            messages.forEach(msgId => {
                const msg = document.getElementById(msgId);
                if (msg) {
                    msg.style.display = 'none';
                    msg.innerHTML = '';
                }
            });

            if (step1) step1.style.display = 'block';
            if (step1_5) step1_5.style.display = 'none';
            if (step2) step2.style.display = 'none';
            if (validationResult) {
                validationResult.style.display = 'none';
                validationResult.innerHTML = '';
            }
            if (validateBtn) {
                validateBtn.disabled = true;
                validateBtn.innerHTML = '<span>🔍</span><span>Validar Campos</span>';
            }
            if (uploadBtn) uploadBtn.style.display = 'none';

            // Resetear variables de validación
            testsAssigneeAccountId = null;
            testsAssigneeValidated = false;
            testsAssigneeInvalid = false;
            const assigneeValidation = document.getElementById('jira-tests-assignee-validation');
            if (assigneeValidation) {
                assigneeValidation.style.display = 'none';
                assigneeValidation.innerHTML = '';
            }
        }

        async function loadJiraProjectsForTests() {
            const hiddenInput = document.getElementById('jira-tests-project-select');
            const searchInput = document.getElementById('jira-tests-project-search-input');
            const validateBtn = document.getElementById('jira-tests-validate-fields-btn');
            if (!hiddenInput) return;

            try {
                const response = await fetch('/api/jira/projects', {
                    headers: {
                        'X-CSRFToken': getCsrfToken()
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    allProjectsTests = data.projects || [];

                    if (allProjectsTests.length === 0) {
                        showDownloadNotification('No se encontraron proyectos de Jira.', 'error');
                        return;
                    }

                    // Configurar el combo box
                    setupSearchableCombo({
                        inputId: 'jira-tests-project-search-input',
                        dropdownId: 'jira-tests-project-dropdown',
                        hiddenId: 'jira-tests-project-select',
                        dataArray: allProjectsTests,
                        onSelect: (item) => {
                            // Habilitar botón de validar cuando se seleccione un proyecto
                            if (validateBtn) {
                                validateBtn.disabled = false;
                            }
                            // Resetear validación si cambia el proyecto
                            const validationResult = document.getElementById('jira-tests-validation-result');
                            const step1_5 = document.getElementById('jira-tests-step1-5');
                            const step2 = document.getElementById('jira-tests-step2');
                            const uploadBtn = document.getElementById('jira-tests-modal-upload');
                            if (validationResult) {
                                validationResult.style.display = 'none';
                                validationResult.innerHTML = '';
                            }
                            if (step1_5) step1_5.style.display = 'none';
                            if (step2) step2.style.display = 'none';
                            if (uploadBtn) uploadBtn.style.display = 'none';

                            // Reiniciar selects de campos
                            const selects = ['jira-tests-tipo-prueba-select', 'jira-tests-nivel-prueba-select',
                                'jira-tests-tipo-ejecucion-select', 'jira-tests-ambiente-select'];
                            selects.forEach(selectId => {
                                const select = document.getElementById(selectId);
                                if (select) {
                                    select.value = '';
                                    select.innerHTML = '<option value="">Cargando valores...</option>';
                                }
                            });

                            // Ocultar mensajes
                            const messages = ['jira-tests-tipo-prueba-message', 'jira-tests-nivel-prueba-message',
                                'jira-tests-tipo-ejecucion-message', 'jira-tests-ambiente-message'];
                            messages.forEach(msgId => {
                                const msg = document.getElementById(msgId);
                                if (msg) {
                                    msg.style.display = 'none';
                                    msg.innerHTML = '';
                                }
                            });
                        }
                    });
                }
            } catch (error) {
                console.error('Error al cargar proyectos de Jira:', error);
            }
        }

        // Función para cargar valores de campos select
        async function loadTestCaseFieldValues(projectKey) {
            try {
                const response = await fetch('/api/jira/get-test-case-field-values', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({ project_key: projectKey })
                });

                const data = await response.json();

                if (!data.success) {
                    showDownloadNotification('Error al cargar valores de campos: ' + (data.error || 'Error desconocido'), 'error');
                    return;
                }

                const fieldConfig = {
                    'tipo_prueba': {
                        select: 'jira-tests-tipo-prueba-select',
                        container: 'jira-tests-tipo-prueba-container',
                        message: 'jira-tests-tipo-prueba-message',
                        label: 'Tipo de Prueba'
                    },
                    'nivel_prueba': {
                        select: 'jira-tests-nivel-prueba-select',
                        container: 'jira-tests-nivel-prueba-container',
                        message: 'jira-tests-nivel-prueba-message',
                        label: 'Nivel de Prueba'
                    },
                    'tipo_ejecucion': {
                        select: 'jira-tests-tipo-ejecucion-select',
                        container: 'jira-tests-tipo-ejecucion-container',
                        message: 'jira-tests-tipo-ejecucion-message',
                        label: 'Tipo de Ejecución'
                    },
                    'ambiente': {
                        select: 'jira-tests-ambiente-select',
                        container: 'jira-tests-ambiente-container',
                        message: 'jira-tests-ambiente-message',
                        label: 'Ambiente'
                    }
                };

                // Procesar cada campo
                for (const [fieldKey, config] of Object.entries(fieldConfig)) {
                    const fieldData = data.field_values[fieldKey];
                    const selectEl = document.getElementById(config.select);
                    const containerEl = document.getElementById(config.container);
                    const messageEl = document.getElementById(config.message);

                    if (!selectEl || !containerEl || !messageEl) continue;

                    // Resetear
                    selectEl.innerHTML = '';
                    selectEl.removeAttribute('required');
                    messageEl.style.display = 'none';
                    messageEl.innerHTML = '';

                    if (!fieldData || !fieldData.exists) {
                        // Campo no existe
                        containerEl.style.display = 'block';
                        selectEl.style.display = 'none';
                        messageEl.style.display = 'block';
                        messageEl.style.color = 'var(--warning)';
                        messageEl.innerHTML = `⚠️ El campo "${config.label}" no existe en este proyecto. Si realizas la carga ahora, este campo no se mostrará en los casos de prueba.`;
                    } else if (!fieldData.has_values || fieldData.values.length === 0) {
                        // Campo existe pero no tiene valores
                        containerEl.style.display = 'block';
                        selectEl.style.display = 'none';
                        messageEl.style.display = 'block';
                        messageEl.style.color = 'var(--warning)';
                        messageEl.innerHTML = `⚠️ El campo "${config.label}" existe pero no tiene opciones configuradas en el proyecto. Si realizas la carga ahora, este campo no se mostrará en los casos de prueba.`;
                    } else {
                        // Campo existe y tiene valores
                        containerEl.style.display = 'block';
                        selectEl.style.display = 'block';
                        selectEl.setAttribute('required', 'required');
                        selectEl.innerHTML = '<option value="">Seleccionar...</option>';
                        fieldData.values.forEach(val => {
                            const option = document.createElement('option');
                            option.value = val.value;
                            option.textContent = val.name || val.value;
                            selectEl.appendChild(option);
                        });
                    }
                }

                // Configurar event listeners para los selects
                setupSelectFieldsListeners();

                // Mostrar paso 1.5
                const step1_5 = document.getElementById('jira-tests-step1-5');
                if (step1_5) step1_5.style.display = 'block';

                // Verificar estado inicial después de cargar valores
                setTimeout(() => {
                    checkAndShowUploadButton();
                }, 100);

            } catch (error) {
                console.error('Error al cargar valores de campos:', error);
                showDownloadNotification('Error al cargar valores de campos: ' + error.message, 'error');
            }
        }

        // Función para validar que todos los campos select requeridos estén llenos
        function validateSelectFields() {
            const requiredSelects = document.querySelectorAll('#jira-tests-step1-5 select[required]');
            for (let select of requiredSelects) {
                if (!select.value || select.value.trim() === '') {
                    return false;
                }
            }
            return true;
        }

        // Función para verificar y mostrar el botón de subir
        function checkAndShowUploadButton() {
            const step2 = document.getElementById('jira-tests-step2');
            const uploadBtn = document.getElementById('jira-tests-modal-upload');
            const assigneeInput = document.getElementById('jira-tests-assignee-input');

            // Verificar que todos los campos select requeridos estén llenos
            if (!validateSelectFields()) {
                // Aún faltan campos - ocultar paso 2 y botón
                if (step2) step2.style.display = 'none';
                if (uploadBtn) uploadBtn.style.display = 'none';
                return;
            }

            // Todos los campos select están llenos - mostrar paso 2
            if (step2) step2.style.display = 'block';

            // Verificar asignado
            const assigneeEmail = assigneeInput ? assigneeInput.value.trim() : '';
            if (assigneeEmail) {
                // Si hay email, debe estar validado
                if (testsAssigneeValidated && !testsAssigneeInvalid) {
                    if (uploadBtn) uploadBtn.style.display = 'flex';
                } else {
                    if (uploadBtn) uploadBtn.style.display = 'none';
                }
            } else {
                // Si no hay email, mostrar botón directamente
                if (uploadBtn) uploadBtn.style.display = 'flex';
            }
        }

        // Configurar event listeners para los campos select
        function setupSelectFieldsListeners() {
            const selects = ['jira-tests-tipo-prueba-select', 'jira-tests-nivel-prueba-select',
                'jira-tests-tipo-ejecucion-select', 'jira-tests-ambiente-select'];

            selects.forEach(selectId => {
                const select = document.getElementById(selectId);
                if (select) {
                    // Remover listeners anteriores si existen
                    const newSelect = select.cloneNode(true);
                    select.parentNode.replaceChild(newSelect, select);

                    newSelect.addEventListener('change', function () {
                        checkAndShowUploadButton();
                    });
                }
            });
        }

        // Función para validar campos del proyecto
        async function validateTestCaseFields() {
            const projectSelect = document.getElementById('jira-tests-project-select');
            const validateBtn = document.getElementById('jira-tests-validate-fields-btn');
            const validationResult = document.getElementById('jira-tests-validation-result');
            const step2 = document.getElementById('jira-tests-step2');
            const uploadBtn = document.getElementById('jira-tests-modal-upload');

            if (!projectSelect || !projectSelect.value) {
                showDownloadNotification('Por favor selecciona un proyecto primero', 'error');
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
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({
                        project_key: projectSelect.value
                    })
                });

                const data = await response.json();

                if (validateBtn) {
                    validateBtn.disabled = false;
                    validateBtn.innerHTML = '<span>🔍</span><span>Validar Campos</span>';
                }

                if (validationResult) {
                    validationResult.style.display = 'block';

                    if (data.success) {
                        // Campos válidos - cargar valores de campos select
                        validationResult.innerHTML = `
                                <div style="padding: 1rem; border-radius: 8px; background: rgba(16, 185, 129, 0.2); border: 1px solid var(--success); color: #6ee7b7;">
                                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                                        <span>✅</span>
                                        <span style="font-weight: 600;">Todos los campos necesarios están disponibles</span>
                                    </div>
                                    <div style="font-size: 0.85rem; margin-top: 0.5rem;">
                                        El proyecto cuenta con todos los campos requeridos para crear casos de prueba.
                                    </div>
                                </div>
                            `;

                        // Cargar valores de campos select
                        await loadTestCaseFieldValues(projectSelect.value);

                        // Ocultar paso 1, mostrar paso 1.5
                        const step1 = document.getElementById('jira-tests-step1');
                        if (step1) step1.style.display = 'none';

                        // Ocultar paso 2 y botón de subir hasta que se llenen los campos select
                        if (step2) step2.style.display = 'none';
                        if (uploadBtn) uploadBtn.style.display = 'none';
                    } else {
                        // Campos faltantes
                        const missingFields = data.missing_fields || [];
                        const missingList = missingFields.map(f => {
                            const possibleNames = f.possible_names || [];
                            return `<li>${f.field} (posibles nombres: ${possibleNames.join(', ')})</li>`;
                        }).join('');

                        validationResult.innerHTML = `
                                <div style="padding: 1rem; border-radius: 8px; background: rgba(239, 68, 68, 0.2); border: 1px solid var(--error); color: #fca5a5;">
                                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                                        <span>❌</span>
                                        <span style="font-weight: 600;">Campos faltantes en el proyecto</span>
                                    </div>
                                    <div style="font-size: 0.85rem; margin-top: 0.5rem; margin-bottom: 0.5rem;">
                                        ${data.message || 'El proyecto no cuenta con todos los campos necesarios.'}
                                    </div>
                                    <div style="font-size: 0.85rem; margin-top: 0.5rem;">
                                        <strong>Campos faltantes:</strong>
                                        <ul style="margin-top: 0.5rem; padding-left: 1.5rem;">
                                            ${missingList}
                                        </ul>
                                    </div>
                                    <div style="font-size: 0.85rem; margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid rgba(239, 68, 68, 0.3);">
                                        Por favor, configura los campos faltantes en el proyecto de Jira antes de continuar.
                                    </div>
                                </div>
                            `;

                        // Ocultar pasos
                        const step1_5 = document.getElementById('jira-tests-step1-5');
                        if (step1_5) step1_5.style.display = 'none';
                        if (step2) step2.style.display = 'none';
                        if (uploadBtn) uploadBtn.style.display = 'none';
                    }
                }
            } catch (error) {
                console.error('Error al validar campos:', error);
                if (validateBtn) {
                    validateBtn.disabled = false;
                    validateBtn.innerHTML = '<span>🔍</span><span>Validar Campos</span>';
                }
                showDownloadNotification('Error al validar campos: ' + error.message, 'error');
            }
        }

        // Event listeners del modal
        const testsModalClose = document.getElementById('jira-tests-modal-close');
        const testsModalCancel = document.getElementById('jira-tests-modal-cancel');
        const validateFieldsBtn = document.getElementById('jira-tests-validate-fields-btn');
        if (testsModalClose) testsModalClose.onclick = closeJiraTestsModal;
        if (testsModalCancel) testsModalCancel.onclick = closeJiraTestsModal;
        if (validateFieldsBtn) validateFieldsBtn.onclick = validateTestCaseFields;

        // Validación de asignado
        let testsAssigneeAccountId = null;
        let testsAssigneeValidated = false;
        let testsAssigneeInvalid = false;

        const testsAssigneeInput = document.getElementById('jira-tests-assignee-input');
        if (testsAssigneeInput) {
            testsAssigneeInput.onblur = async function () {
                const email = this.value.trim();
                const validationDiv = document.getElementById('jira-tests-assignee-validation');

                if (!email) {
                    testsAssigneeAccountId = null;
                    testsAssigneeValidated = false;
                    testsAssigneeInvalid = false;
                    if (validationDiv) {
                        validationDiv.style.display = 'none';
                    }
                    // Si no hay email, verificar si se puede mostrar el botón
                    checkAndShowUploadButton();
                    return;
                }

                // Validar formato de email
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(email)) {
                    if (validationDiv) {
                        validationDiv.style.display = 'block';
                        validationDiv.style.color = 'var(--error)';
                        validationDiv.textContent = '❌ Formato de email inválido';
                    }
                    testsAssigneeInvalid = true;
                    testsAssigneeValidated = false;
                    return;
                }

                // Validar con Jira
                if (validationDiv) {
                    validationDiv.style.display = 'block';
                    validationDiv.style.color = 'var(--text-muted)';
                    validationDiv.textContent = '⏳ Validando...';
                }

                try {
                    const response = await fetch('/api/jira/validate-user', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCsrfToken()
                        },
                        body: JSON.stringify({ email: email })
                    });

                    if (response.ok) {
                        const validateData = await response.json();
                        if (validateData.valid && validateData.accountId) {
                            testsAssigneeAccountId = validateData.accountId;
                            testsAssigneeValidated = true;
                            testsAssigneeInvalid = false;
                            if (validationDiv) {
                                validationDiv.style.color = 'var(--success)';
                                validationDiv.textContent = '✅ Usuario encontrado en Jira';
                            }
                            // Verificar si se puede mostrar el botón de subir
                            checkAndShowUploadButton();
                        } else {
                            testsAssigneeInvalid = true;
                            testsAssigneeValidated = false;
                            if (validationDiv) {
                                validationDiv.style.color = 'var(--error)';
                                validationDiv.textContent = '❌ ' + (validateData.error || 'Este correo no tiene cuenta en Jira');
                            }
                            // Ocultar botón si el asignado es inválido
                            const uploadBtn = document.getElementById('jira-tests-modal-upload');
                            if (uploadBtn) uploadBtn.style.display = 'none';
                        }
                    } else {
                        const validateData = await response.json();
                        testsAssigneeInvalid = true;
                        testsAssigneeValidated = false;
                        if (validationDiv) {
                            validationDiv.style.color = 'var(--error)';
                            validationDiv.textContent = '❌ ' + (validateData.error || 'Error al validar usuario');
                        }
                        // Ocultar botón si hay error
                        const uploadBtn = document.getElementById('jira-tests-modal-upload');
                        if (uploadBtn) uploadBtn.style.display = 'none';
                    }
                } catch (error) {
                    if (validationDiv) {
                        validationDiv.style.color = 'var(--error)';
                        validationDiv.textContent = '❌ Error al validar usuario';
                    }
                    testsAssigneeInvalid = true;
                    testsAssigneeValidated = false;
                }
            };
        }

        // Botón subir a Jira
        const testsModalUploadBtn = document.getElementById('jira-tests-modal-upload');
        if (testsModalUploadBtn) {
            testsModalUploadBtn.onclick = async function () {
                const projectSelect = document.getElementById('jira-tests-project-select');
                const assigneeInput = document.getElementById('jira-tests-assignee-input');

                if (!projectSelect || !projectSelect.value) {
                    showDownloadNotification('Por favor selecciona un proyecto de Jira', 'error');
                    return;
                }

                const projectKey = projectSelect.value;
                const assigneeEmail = assigneeInput ? assigneeInput.value.trim() : '';

                // Obtener valores de campos select
                const tipoPruebaSelect = document.getElementById('jira-tests-tipo-prueba-select');
                const nivelPruebaSelect = document.getElementById('jira-tests-nivel-prueba-select');
                const tipoEjecucionSelect = document.getElementById('jira-tests-tipo-ejecucion-select');
                const ambienteSelect = document.getElementById('jira-tests-ambiente-select');

                const tipoPrueba = tipoPruebaSelect ? tipoPruebaSelect.value.trim() : '';
                const nivelPrueba = nivelPruebaSelect ? nivelPruebaSelect.value.trim() : '';
                const tipoEjecucion = tipoEjecucionSelect ? tipoEjecucionSelect.value.trim() : '';
                const ambiente = ambienteSelect ? ambienteSelect.value.trim() : '';

                // Validar asignado si se proporciona
                if (assigneeEmail) {
                    if (testsAssigneeInvalid) {
                        showDownloadNotification('Por favor verifica que el email del asignado sea válido y tenga cuenta en Jira', 'error');
                        return;
                    } else if (!testsAssigneeValidated) {
                        // Intentar validar ahora
                        if (assigneeInput) {
                            assigneeInput.focus();
                            assigneeInput.blur();
                            await new Promise(resolve => setTimeout(resolve, 1000));

                            if (testsAssigneeInvalid || !testsAssigneeValidated) {
                                showDownloadNotification('Por favor verifica que el email del asignado sea válido y tenga cuenta en Jira', 'error');
                                return;
                            }
                        }
                    }
                }

                // Mostrar loading
                const loadingOverlay = document.getElementById('tests-loading-overlay');
                if (loadingOverlay) loadingOverlay.style.display = 'flex';

                try {
                    const response = await fetch('/api/jira/tests/upload-to-jira', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCsrfToken()
                        },
                        body: JSON.stringify({
                            test_cases: window.selectedTestsForUpload,
                            project_key: projectKey,
                            assignee_email: assigneeEmail || null,
                            tipo_prueba: tipoPrueba,
                            nivel_prueba: nivelPrueba,
                            tipo_ejecucion: tipoEjecucion,
                            ambiente: ambiente
                        })
                    });

                    const data = await response.json();

                    if (loadingOverlay) loadingOverlay.style.display = 'none';
                    closeJiraTestsModal();

                    if (data.success) {
                        showDownloadNotification(data.message || 'Casos de prueba subidos exitosamente a Jira', 'success');

                        // Descargar archivo TXT si está disponible
                        if (data.txt_content && data.txt_filename) {
                            try {
                                // Decodificar base64
                                const txtContent = atob(data.txt_content);

                                const blob = new Blob([txtContent], { type: 'text/plain;charset=utf-8' });
                                const url = URL.createObjectURL(blob);
                                const a = document.createElement('a');
                                a.href = url;
                                a.download = data.txt_filename;
                                document.body.appendChild(a);
                                a.click();
                                URL.revokeObjectURL(url);
                                document.body.removeChild(a);
                            } catch (txtError) {
                                console.error('Error al descargar TXT:', txtError);
                            }
                        }
                    } else {
                        showDownloadNotification('Error: ' + (data.error || 'No se pudieron subir los casos de prueba'), 'error');
                    }
                } catch (error) {
                    if (loadingOverlay) loadingOverlay.style.display = 'none';
                    showDownloadNotification('Error de conexión: ' + error.message, 'error');
                }
            };
        }
    })();
})(window);
