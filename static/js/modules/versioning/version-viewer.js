/**
 * Módulo: VersionViewer
 * Responsabilidad: Gestionar la UI de historial de versiones, diffs y rollback.
 */
class VersionViewer {
    constructor() {
        this.currentArtifactType = null;
        this.currentArtifactId = null;
        this.history = [];
        this.selectedVersion = null;
        this.compareVersion = null;
        this.isCompareMode = false;

        // Elementos DOM
        this.modal = document.getElementById('version-history-container');
        this.timelineList = document.getElementById('version-timeline-list');
        this.contentArea = document.getElementById('version-content-area');
        this.viewLabel = document.getElementById('view-mode-label');
        this.btnCompare = document.getElementById('btn-compare');
        this.btnRollback = document.getElementById('btn-rollback');
    }

    /**
     * Abre el modal y carga el histori para un artefacto específico.
     * @param {string} artifactType - 'TEST_CASE' o 'USER_STORY'
     * @param {int} artifactId - ID del artefacto
     */
    async open(artifactType, artifactId) {
        this.currentArtifactType = artifactType;
        this.currentArtifactId = artifactId;
        this.isCompareMode = false;
        this.selectedVersion = null;
        this.compareVersion = null;

        // Reset UI
        this.modal.classList.remove('hidden');
        this.contentArea.innerHTML = '<div class="text-gray-400 text-center mt-10">Cargando...</div>';
        this.updateToolbar();

        await this.loadHistory();
    }

    closeModal() {
        this.modal.classList.add('hidden');
    }

    async loadHistory() {
        try {
            const response = await fetch(`/api/versions/${this.currentArtifactType}/${this.currentArtifactId}/history`);
            if (!response.ok) throw new Error('Error cargando historial');

            const data = await response.json();
            this.history = data.versions;
            this.renderTimeline();

            // Seleccionar la última versión por defecto
            if (this.history.length > 0) {
                this.selectVersion(this.history[0].version_number);
            }
        } catch (error) {
            console.error(error);
            this.timelineList.innerHTML = `<div class="text-red-500 p-4">Error: ${error.message}</div>`;
        }
    }

    renderTimeline() {
        this.timelineList.innerHTML = '';
        const template = document.getElementById('tmpl-version-item');

        this.history.forEach(v => {
            const clone = template.content.cloneNode(true);
            const div = clone.querySelector('.version-item');

            div.dataset.version = v.version_number;
            div.querySelector('.version-badge').textContent = `v${v.version_number}`;
            div.querySelector('.date-label').textContent = new Date(v.created_at).toLocaleString();
            div.querySelector('.created-by').textContent = v.created_by;
            div.querySelector('.change-reason').textContent = v.change_reason || 'Sin descripción';

            // Evento click manejado por delegación o directo
            div.onclick = () => this.handleVersionClick(v);

            this.timelineList.appendChild(clone);
        });
    }

    async handleVersionClick(version) {
        if (this.isCompareMode) {
            this.compareVersion = version;
            await this.executeCompare();
        } else {
            this.selectedVersion = version;
            this.compareVersion = null; // Reset compare
            this.renderVersionDetails(version);
        }
        this.updateActiveState();
    }

    updateActiveState() {
        // Actualizar clases visuales en la lista
        const items = this.timelineList.querySelectorAll('.version-item');
        items.forEach(item => {
            item.classList.remove('border-blue-500', 'bg-blue-50', 'border-purple-500', 'bg-purple-50');
            item.classList.add('border-transparent');

            const vParam = item.dataset.version;

            if (this.selectedVersion && vParam === this.selectedVersion.version_number) {
                item.classList.remove('border-transparent');
                item.classList.add('border-blue-500', 'bg-blue-50');
            }

            if (this.compareVersion && vParam === this.compareVersion.version_number) {
                item.classList.remove('border-transparent');
                item.classList.add('border-purple-500', 'bg-purple-50');
            }
        });

        this.updateToolbar();
    }

    updateToolbar() {
        if (this.isCompareMode) {
            this.viewLabel.textContent = `Comparando v${this.selectedVersion?.version_number} vs v${this.compareVersion?.version_number || '...'}`;
            this.btnCompare.textContent = 'Cancelar Comparación';
            this.btnCompare.classList.remove('bg-blue-100', 'text-blue-700');
            this.btnCompare.classList.add('bg-gray-200', 'text-gray-700');
            this.btnRollback.classList.add('hidden');
        } else {
            this.viewLabel.textContent = this.selectedVersion ? `Detalles v${this.selectedVersion.version_number}` : 'Seleccione una versión';
            this.btnCompare.textContent = 'Comparar';
            this.btnCompare.classList.add('bg-blue-100', 'text-blue-700');
            this.btnCompare.classList.remove('bg-gray-200', 'text-gray-700');

            if (this.selectedVersion) {
                this.btnCompare.classList.remove('hidden');
                this.btnRollback.classList.remove('hidden');
            } else {
                this.btnCompare.classList.add('hidden');
                this.btnRollback.classList.add('hidden');
            }
        }
    }

    renderVersionDetails(version) {
        try {
            const content = JSON.parse(version.content_snapshot);
            const prettyJson = JSON.stringify(content, null, 2);
            this.contentArea.innerHTML = `<pre class="whitespace-pre-wrap text-gray-800">${this.escapeHtml(prettyJson)}</pre>`;
        } catch (e) {
            this.contentArea.innerHTML = `<pre>${version.content_snapshot}</pre>`;
        }
    }

    enableCompareMode() {
        if (this.isCompareMode) {
            // Cancelar
            this.isCompareMode = false;
            this.compareVersion = null;
            this.renderVersionDetails(this.selectedVersion);
        } else {
            // Activar
            this.isCompareMode = true;
            this.viewLabel.textContent = "Seleccione otra versión para comparar...";
        }
        this.updateActiveState();
    }

    async executeCompare() {
        if (!this.selectedVersion || !this.compareVersion) return;

        this.contentArea.innerHTML = '<div class="text-center">Calculando diferencias...</div>';

        try {
            const v1 = this.compareVersion.version_number; // Older usually?
            const v2 = this.selectedVersion.version_number;

            const response = await fetch(`/api/versions/${this.currentArtifactType}/${this.currentArtifactId}/diff?v1=${v1}&v2=${v2}`);
            const data = await response.json();

            this.renderDiff(data.diff);

        } catch (error) {
            this.contentArea.innerHTML = `<div class="text-red-500">Error: ${error.message}</div>`;
        }
    }

    renderDiff(diff) {
        let html = '<div class="space-y-4">';

        // Added
        for (const [key, val] of Object.entries(diff.added)) {
            html += this.createDiffBlock('Agregado', key, null, val, 'bg-green-50 border-green-200 text-green-800');
        }

        // Removed
        for (const [key, val] of Object.entries(diff.removed)) {
            html += this.createDiffBlock('Eliminado', key, val, null, 'bg-red-50 border-red-200 text-red-800');
        }

        // Changed
        for (const [key, val] of Object.entries(diff.changed)) {
            html += this.createDiffBlock('Modificado', key, val.old, val.new, 'bg-yellow-50 border-yellow-200 text-yellow-800');
        }

        if (Object.keys(diff.added).length === 0 && Object.keys(diff.removed).length === 0 && Object.keys(diff.changed).length === 0) {
            html += '<div class="text-center text-gray-500 italic">No hay diferencias estructurales.</div>';
        }

        html += '</div>';
        this.contentArea.innerHTML = html;
    }

    createDiffBlock(type, key, oldVal, newVal, classes) {
        return `
            <div class="border rounded p-2 ${classes}">
                <div class="font-bold text-xs uppercase mb-1 flex items-center">
                    <span class="mr-2">${type}:</span> ${key}
                </div>
                <div class="grid grid-cols-2 gap-2 text-xs font-mono">
                    ${oldVal !== null ? `<div class="overflow-hidden"><span class="block text-gray-500 mb-1">Antes:</span>${this.formatVal(oldVal)}</div>` : '<div></div>'}
                    ${newVal !== null ? `<div class="overflow-hidden"><span class="block text-gray-500 mb-1">Después:</span>${this.formatVal(newVal)}</div>` : '<div></div>'}
                </div>
            </div>
        `;
    }

    formatVal(val) {
        if (typeof val === 'object') return `<pre>${JSON.stringify(val, null, 2)}</pre>`;
        return `<span>${this.escapeHtml(String(val))}</span>`;
    }

    async confirmRollback() {
        if (!this.selectedVersion) return;

        const vNum = this.selectedVersion.version_number;
        if (!confirm(`¿Estás seguro de hacer ROLLBACK a la versión v${vNum}?\n\nEsto creará una NUEVA versión con el contenido de v${vNum}.`)) {
            return;
        }

        try {
            const response = await fetch(`/api/versions/${this.currentArtifactType}/${this.currentArtifactId}/rollback`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target_version: vNum })
            });

            if (!response.ok) throw new Error('Error en rollback');

            const data = await response.json();
            alert(`Rollback exitoso. Nueva versión actual: v${data.new_current_version}`);

            // Recargar para mostrar la nueva versión
            await this.loadHistory();

        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    }

    escapeHtml(text) {
        if (!text) return text;
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}

// Instancia global
const versionViewer = new VersionViewer();
window.versionViewer = versionViewer;
