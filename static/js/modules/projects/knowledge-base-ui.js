/**
 * Knowledge Base UI Module
 * Handles interactions for the "Unified Knowledge Base" (K1.4)
 */
(function (window) {
    'use strict';

    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Projects = window.NexusModules.Projects || {};

    let currentProjectKey = '';
    const API_BASE = '/api/knowledge';

    const KnowledgeBaseUI = {
        /**
         * Inicializa la UI de Base de Conocimiento
         * @param {string} projectKey - Identificador único del proyecto (Jira Key)
         */
        init: function (projectKey) {
            currentProjectKey = projectKey || document.getElementById('knowledge-base-container')?.dataset.projectKey;

            if (!currentProjectKey) {
                console.warn('KnowledgeBaseUI: No Project Key provided.');
                return;
            }

            console.log('Initializing KnowledgeBaseUI for project:', currentProjectKey);
            this.bindEvents();
            this.loadDocuments();
            this.loadContext();
        },

        bindEvents: function () {
            const dropzone = document.getElementById('dropzone-area');
            const fileInput = document.getElementById('file-input');
            const refreshBtn = document.getElementById('refresh-context-btn');

            if (dropzone && fileInput) {
                // Click to open file dialog
                dropzone.addEventListener('click', () => fileInput.click());

                // File selection
                fileInput.addEventListener('change', (e) => this.handleUpload(e.target.files));

                // Drag & Drop
                dropzone.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    dropzone.classList.add('border-blue-400', 'bg-gray-800');
                });

                dropzone.addEventListener('dragleave', (e) => {
                    e.preventDefault();
                    dropzone.classList.remove('border-blue-400', 'bg-gray-800');
                });

                dropzone.addEventListener('drop', (e) => {
                    e.preventDefault();
                    dropzone.classList.remove('border-blue-400', 'bg-gray-800');
                    if (e.dataTransfer.files.length > 0) {
                        this.handleUpload(e.dataTransfer.files);
                    }
                });
            }

            if (refreshBtn) {
                refreshBtn.addEventListener('click', () => {
                    this.loadContext();
                    this.loadDocuments();
                });
            }
        },

        handleUpload: async function (files) {
            const overlay = document.getElementById('upload-overlay');
            if (overlay) overlay.classList.remove('hidden');

            const formData = new FormData();
            formData.append('project_key', currentProjectKey);

            // Add files
            Array.from(files).forEach(file => {
                formData.append('files[]', file);
            });

            // Get CSRF Token
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
            if (csrfToken) {
                formData.append('csrf_token', csrfToken);
            }

            try {
                const response = await fetch(`${API_BASE}/upload`, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': csrfToken // Also send in header just in case
                    }
                });

                const result = await response.json();

                if (response.ok) {
                    this.showNotification('Archivos subidos correctamente. Procesando...', 'success');
                    this.loadDocuments();
                    this.loadContext(); // Context might update quickly or wait for trigger
                } else {
                    this.showNotification('Error al subir: ' + (result.error || 'Desconocido'), 'error');
                }
            } catch (error) {
                console.error('Upload Error:', error);
                this.showNotification('Error de conexión', 'error');
            } finally {
                if (overlay) overlay.classList.add('hidden');
                // Reset input
                const fileInput = document.getElementById('file-input');
                if (fileInput) fileInput.value = '';
            }
        },

        loadDocuments: async function () {
            const listContainer = document.getElementById('documents-list');
            if (!listContainer) return;

            try {
                const response = await fetch(`${API_BASE}/documents/${currentProjectKey}`);
                if (!response.ok) throw new Error('Failed to fetch docs');

                const docs = await response.json();
                this.renderDocuments(docs);
            } catch (error) {
                console.error('List Docs Error:', error);
                listContainer.innerHTML = '<div class="text-red-400 text-xs text-center p-2">Error al cargar docs</div>';
            }
        },

        renderDocuments: function (docs) {
            const listContainer = document.getElementById('documents-list');
            if (!docs || docs.length === 0) {
                listContainer.innerHTML = '<div class="text-center py-4 text-gray-500 text-sm italic">No hay documentos subidos.</div>';
                return;
            }

            let html = '';
            docs.forEach(doc => {
                const icon = this.getFileIcon(doc.file_type);
                const statusColor = doc.status === 'processed' ? 'text-green-400' : (doc.status === 'error' ? 'text-red-400' : 'text-yellow-400');
                const statusIcon = doc.status === 'processed' ? 'fa-check-circle' : (doc.status === 'error' ? 'fa-exclamation-circle' : 'fa-clock');

                html += `
                    <div class="bg-gray-800/50 rounded-lg p-3 flex items-start space-x-3 border border-gray-700 hover:border-gray-600 transition-colors">
                        <div class="mt-1">${icon}</div>
                        <div class="flex-1 min-w-0">
                            <p class="text-sm font-medium text-gray-300 truncate" title="${doc.filename}">${doc.filename}</p>
                            <div class="flex items-center mt-1 space-x-2">
                                <span class="text-xs ${statusColor}"><i class="fas ${statusIcon} mr-1"></i>${doc.status}</span>
                                <span class="text-xs text-gray-500">${new Date(doc.upload_date).toLocaleDateString()}</span>
                            </div>
                        </div>
                    </div>
                `;
            });
            listContainer.innerHTML = html;
        },

        loadContext: async function () {
            try {
                const response = await fetch(`${API_BASE}/context/${currentProjectKey}`);
                if (!response.ok) throw new Error('Failed to fetch context');

                const context = await response.json();
                this.renderContext(context);
            } catch (error) {
                console.error('Context Error:', error);
            }
        },

        renderContext: function (data) {
            // Update Version Badge
            const badge = document.getElementById('context-version-badge');
            if (badge) badge.innerText = `v${data.version || 0}`;

            // Summary
            const summaryEl = document.getElementById('ctx-summary-content');
            if (summaryEl) summaryEl.innerText = data.summary || 'La IA está analizando los documentos para generar un resumen...';

            // Glossary
            const glossaryContainer = document.getElementById('ctx-glossary-content');
            if (glossaryContainer) {
                if (data.glossary && Object.keys(data.glossary).length > 0) {
                    let html = '';
                    for (const [term, def] of Object.entries(data.glossary)) {
                        html += `
                            <div class="bg-gray-900/50 p-2 rounded border border-gray-700/50">
                                <span class="text-blue-300 font-bold text-xs block">${term}</span>
                                <span class="text-gray-400 text-xs">${def}</span>
                            </div>
                        `;
                    }
                    glossaryContainer.innerHTML = html;
                } else {
                    glossaryContainer.innerHTML = '<span class="text-gray-500 text-xs italic">Sin términos definidos.</span>';
                }
            }

            // Rules
            const rulesContainer = document.getElementById('ctx-rules-content');
            if (rulesContainer) {
                if (data.business_rules && data.business_rules.length > 0) {
                    let html = '';
                    data.business_rules.forEach(rule => {
                        html += `<li class="flex items-start"><i class="fas fa-angle-right text-purple-500 mt-1 mr-2 opacity-70"></i><span>${rule}</span></li>`;
                    });
                    rulesContainer.innerHTML = html;
                } else {
                    rulesContainer.innerHTML = '<li class="text-gray-500 italic">No se han detectado reglas de negocio.</li>';
                }
            }

            // Tech Constraints
            const techContainer = document.getElementById('ctx-tech-content');
            if (techContainer) {
                if (data.tech_constraints && data.tech_constraints.length > 0) {
                    let html = '';
                    data.tech_constraints.forEach(item => {
                        html += `<span class="px-2 py-1 bg-gray-700/50 text-gray-300 rounded text-xs border border-gray-600">${item}</span>`;
                    });
                    techContainer.innerHTML = html;
                } else {
                    techContainer.innerHTML = '<span class="text-gray-500 text-xs italic">Sin restricciones técnicas.</span>';
                }
            }
        },

        getFileIcon: function (fileType) {
            // Simple mapping
            if (fileType && fileType.includes('pdf')) return '<i class="fas fa-file-pdf text-red-500 text-lg"></i>';
            if (fileType && (fileType.includes('word') || fileType.includes('doc'))) return '<i class="fas fa-file-word text-blue-500 text-lg"></i>';
            if (fileType && fileType.includes('sheet') || fileType.includes('csv')) return '<i class="fas fa-file-csv text-green-500 text-lg"></i>';
            return '<i class="fas fa-file-alt text-gray-400 text-lg"></i>';
        },

        showNotification: function (message, type = 'info') {
            // Check if there is a global notification system
            if (window.NexusModules && window.NexusModules.Notifications) {
                window.NexusModules.Notifications.show(message, type);
            } else {
                alert(message); // Fallback
            }
        }
    };

    // Expose module
    window.NexusModules.Projects.KnowledgeBaseUI = KnowledgeBaseUI;

})(window);
