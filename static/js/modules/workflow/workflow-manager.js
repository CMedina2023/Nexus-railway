/**
 * Módulo para gestionar el Workflow de Aprobación en el frontend
 * Responsabilidad: Manejar interacciones de UI y comunicación con API de workflow
 */

class WorkflowManager {
    constructor(config = {}) {
        this.baseUrl = '/api/workflow';
        this.artifactType = config.artifactType || null; // 'USER_STORY' | 'TEST_CASE'
        this.artifactId = config.artifactId || null;
        this.containerId = config.containerId || 'workflow-actions-container';
        this.currentUserRole = config.currentUserRole || 'user'; // 'admin', 'qa_lead', 'user'
        this.onStatusChange = config.onStatusChange || (() => { });

        this.init();
    }

    init() {
        if (this.artifactId && this.artifactType) {
            this.refreshStatus();
        }
    }

    setArtifact(type, id) {
        this.artifactType = type;
        this.artifactId = id;
        this.refreshStatus();
    }

    async refreshStatus() {
        if (!this.artifactId) return;

        try {
            const response = await fetch(`${this.baseUrl}/${this.artifactId}/status?artifact_type=${this.artifactType}`);
            if (!response.ok) throw new Error('Error fetching status');

            const workflow = await response.json();
            this.renderActions(workflow);
            this.updateBadge(workflow.current_status || 'DRAFT');

            if (this.onStatusChange) {
                this.onStatusChange(workflow.current_status || 'DRAFT');
            }
        } catch (error) {
            console.error('Workflow status error:', error);
            // Default to manual draft if error or not found
            this.renderActions({ current_status: 'DRAFT' });
        }
    }

    async submitForReview() {
        return this._transition('submit', {
            artifact_type: this.artifactType,
            artifact_id: this.artifactId
        });
    }

    async approve(workflowId, comments = 'Approved') {
        return this._transition('approve', { workflow_id: workflowId, comments });
    }

    async reject(workflowId, comments) {
        if (!comments) throw new Error('Comentarios requeridos para rechazar');
        return this._transition('reject', { workflow_id: workflowId, comments });
    }

    async requestChanges(workflowId, comments) {
        if (!comments) throw new Error('Comentarios requeridos para solicitar cambios');
        return this._transition('request-changes', { workflow_id: workflowId, comments });
    }

    async _transition(action, payload) {
        try {
            const response = await fetch(`${this.baseUrl}/${action}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Transition failed');

            this.refreshStatus();
            return data;
        } catch (error) {
            console.error(`Workflow transition error (${action}):`, error);
            alert(`Error: ${error.message}`);
            throw error;
        }
    }

    renderActions(workflow) {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        const status = workflow.current_status || 'DRAFT';
        const workflowId = workflow.id;

        let actionsHtml = '';

        // Lógica de visualización de botones según estado y rol
        // NOTA: La validación real ocurre en backend, esto es solo UX

        if (status === 'DRAFT' || status === 'CHANGES_REQUESTED') {
            actionsHtml = `
                <button class="btn btn-primary btn-sm" onclick="workflowManager.submitForReview()">
                    <i class="fas fa-paper-plane"></i> Enviar a Revisión
                </button>
            `;
        } else if (status === 'PENDING_REVIEW') {
            // Asumimos que cualquier usuario puede ver los botones por ahora, 
            // idealmente verificar this.currentUserRole
            actionsHtml = `
                <div class="btn-group">
                    <button class="btn btn-success btn-sm" onclick="workflowManager.openApprovalModal(${workflowId}, 'approve')">
                        <i class="fas fa-check"></i> Aprobar
                    </button>
                    <button class="btn btn-warning btn-sm" onclick="workflowManager.openApprovalModal(${workflowId}, 'changes')">
                        <i class="fas fa-edit"></i> Pedir Cambios
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="workflowManager.openApprovalModal(${workflowId}, 'reject')">
                        <i class="fas fa-times"></i> Rechazar
                    </button>
                </div>
            `;
        } else if (status === 'APPROVED') {
            actionsHtml = `<span class="text-success"><i class="fas fa-check-circle"></i> Aprobado para Jira</span>`;
        } else if (status === 'REJECTED') {
            actionsHtml = `<span class="text-danger"><i class="fas fa-ban"></i> Rechazado</span>`;
        }

        container.innerHTML = actionsHtml;

        // Agregar botón de historial siempre
        const historyBtn = document.createElement('button');
        historyBtn.className = 'btn btn-link btn-sm ms-2';
        historyBtn.innerHTML = '<i class="fas fa-history"></i> Historial';
        historyBtn.onclick = () => this.showHistory(workflowId || this.artifactId); // Fallback logic
        container.appendChild(historyBtn);
    }

    updateBadge(status) {
        const badges = {
            'DRAFT': 'bg-secondary',
            'PENDING_REVIEW': 'bg-primary',
            'APPROVED': 'bg-success',
            'CHANGES_REQUESTED': 'bg-warning text-dark',
            'REJECTED': 'bg-danger',
            'SYNCED': 'bg-info'
        };

        const badgeEl = document.getElementById('workflow-status-badge');
        if (badgeEl) {
            badgeEl.className = `badge ${badges[status] || 'bg-secondary'}`;
            badgeEl.textContent = status.replace('_', ' ');
        }
    }

    openApprovalModal(workflowId, action) {
        // Implementación simple de modal usando prompts por ahora o custom modal si existe
        // Idealmente conectar con un modal HTML real
        const modal = new bootstrap.Modal(document.getElementById('workflowActionModal'));
        const titleEl = document.getElementById('workflowModalTitle');
        const confirmBtn = document.getElementById('workflowModalConfirm');
        const commentInput = document.getElementById('workflowModalComment');

        // Guardar estado en el modal
        confirmBtn.dataset.workflowId = workflowId;
        confirmBtn.dataset.action = action;

        if (action === 'approve') {
            titleEl.textContent = 'Aprobar Artefacto';
            commentInput.placeholder = 'Comentarios opcionales...';
            confirmBtn.className = 'btn btn-success';
            confirmBtn.textContent = 'Aprobar';
        } else if (action === 'reject') {
            titleEl.textContent = 'Rechazar Artefacto';
            commentInput.placeholder = 'Razón del rechazo (obligatorio)...';
            confirmBtn.className = 'btn btn-danger';
            confirmBtn.textContent = 'Rechazar';
        } else {
            titleEl.textContent = 'Solicitar Cambios';
            commentInput.placeholder = 'Qué cambios se requieren (obligatorio)...';
            confirmBtn.className = 'btn btn-warning';
            confirmBtn.textContent = 'Solicitar';
        }

        modal.show();
    }

    // Método llamado desde el modal
    async handleModalConfirm() {
        const confirmBtn = document.getElementById('workflowModalConfirm');
        const commentInput = document.getElementById('workflowModalComment');
        const workflowId = confirmBtn.dataset.workflowId;
        const action = confirmBtn.dataset.action;
        const comments = commentInput.value;

        try {
            if (action === 'approve') {
                await this.approve(workflowId, comments);
            } else if (action === 'reject') {
                await this.reject(workflowId, comments);
            } else if (action === 'changes') {
                await this.requestChanges(workflowId, comments);
            }

            // Cerrar modal
            const modalEl = document.getElementById('workflowActionModal');
            const modal = bootstrap.Modal.getInstance(modalEl);
            modal.hide();
            commentInput.value = ''; // Reset

        } catch (e) {
            // Error ya manejado en métodos individuales, pero aseguramos UI feedback
            console.error("Modal action failed", e);
        }
    }

    async showHistory(id) {
        // TODO: Implementar modal de historial
        console.log("Show history for", id);
        try {
            const response = await fetch(`${this.baseUrl}/${this.artifactId}/history?artifact_type=${this.artifactType}`);
            const data = await response.json();

            const historyBody = document.getElementById('workflowHistoryBody');
            if (historyBody && data.history) {
                historyBody.innerHTML = data.history.map(h => `
                    <tr>
                        <td>${new Date(h.created_at).toLocaleString()}</td>
                        <td>${h.action}</td>
                        <td>${h.actor_id}</td> <!-- TODO: Resolve name -->
                        <td>${h.comments || '-'}</td>
                    </tr>
                 `).join('');

                const modal = new bootstrap.Modal(document.getElementById('workflowHistoryModal'));
                modal.show();
            }
        } catch (e) {
            console.error("Error fetching history", e);
        }
    }
}

// Exponer instancia global para uso fácil
window.workflowManager = new WorkflowManager();
