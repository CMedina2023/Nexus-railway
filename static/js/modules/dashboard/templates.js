/**
 * Nexus AI - Dashboard Templates Module
 * Contains functions that return HTML strings for the dashboard.
 */

(function (window) {
    'use strict';

    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Dashboard = window.NexusModules.Dashboard || {};

    /**
     * Creates HTML for a history list item (Generators)
     * @param {Object} item - History item data
     * @returns {string} HTML string
     */
    function historyItemTemplate(item) {
        const date = new Date(item.date);
        const formattedDate = date.toLocaleDateString('es-ES', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        const icon = item.type === 'stories' ? '📝' : '🧪';
        const typeName = item.type === 'stories' ? 'Historias de Usuario' : 'Casos de Prueba';
        const iconClass = item.type === 'stories' ? 'story' : 'test';

        let area = item.area;
        if (!area || area === 'UNKNOWN' || area === 'No especificada' || area === 'Sin Área') {
            area = 'Sin Área';
        }

        return `
            <li class="history-item">
                <div class="history-info">
                    <div class="history-icon ${iconClass}">${icon}</div>
                    <div class="history-details">
                        <div class="history-type">${typeName}</div>
                        <div class="history-meta">
                            <span class="history-area">🏢 ${area}</span>
                            <span class="history-date">${formattedDate}</span>
                        </div>
                    </div>
                </div>
                <div class="history-count">+${item.count}</div>
            </li>
        `;
    }

    /**
     * Creates HTML for a Jira Report history item
     * @param {Object} item - Report history item
     * @returns {string} HTML string
     */
    function jiraReportHistoryItemTemplate(item) {
        const date = new Date(item.timestamp || item.date);
        const formattedDate = date.toLocaleDateString('es-ES', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        return `
            <li class="history-item">
                <div class="history-info">
                    <div class="history-icon reports"><i class="fas fa-file-alt"></i></div>
                    <div class="history-details">
                        <div class="history-type">Reporte Generado</div>
                        <div class="history-meta">
                            <span class="history-area">📊 ${item.projectName || item.projectKey || 'Proyecto'}</span>
                            <span class="history-date">${formattedDate}</span>
                        </div>
                    </div>
                </div>
            </li>
        `;
    }

    /**
     * Creates HTML for a Jira Upload history item
     * @param {Object} item - Upload history item
     * @returns {string} HTML string
     */
    function jiraUploadHistoryItemTemplate(item) {
        const date = new Date(item.timestamp || item.date);
        const formattedDate = date.toLocaleDateString('es-ES', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        const types = Object.keys(item.issueTypesDistribution || {});
        const typesSummary = types.length > 0
            ? types.map(t => `${t} (${item.issueTypesDistribution[t]})`).join(', ')
            : 'Sin tipo especificado';

        return `
            <li class="history-item">
                <div class="history-info">
                    <div class="history-icon uploads"><i class="fas fa-upload"></i></div>
                    <div class="history-details">
                        <div class="history-type">Carga Masiva</div>
                        <div class="history-meta">
                            <span class="history-area">📊 ${item.projectName || item.projectKey || 'Proyecto'}</span>
                            <span class="history-date">${formattedDate}</span>
                        </div>
                        <div class="history-extra" style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem;">
                            ${item.itemsCount || 0} items • Tipos: ${typesSummary}
                        </div>
                    </div>
                </div>
                <div class="history-count">+${item.itemsCount || 0}</div>
            </li>
        `;
    }

    /**
     * Creates HTML for a Jira Project summary card
     * @param {string} type - 'reports' or 'uploads'
     * @param {string} projectKey - Project key
     * @param {Object} project - Project metrics data
     * @returns {string} HTML string
     */
    function jiraProjectMetricTemplate(type, projectKey, project) {
        if (type === 'reports') {
            return `
                <div class="jira-project-metric-item">
                    <div class="jira-project-metric-header">
                        <div class="jira-project-metric-name">${project.name || projectKey}</div>
                    </div>
                    <div class="jira-project-metric-stats">
                        <div class="jira-project-stat">
                            <span class="jira-project-stat-label">Reportes Generados</span>
                            <span class="jira-project-stat-value">${project.count}</span>
                        </div>
                        <div class="jira-project-stat">
                            <span class="jira-project-stat-label">Último Reporte</span>
                            <span class="jira-project-stat-value">${project.lastDate || '-'}</span>
                        </div>
                    </div>
                </div>
            `;
        } else {
            const avgItems = project.count > 0
                ? Math.round((project.itemsCount || 0) / project.count)
                : 0;

            const typesDistribution = project.issueTypesDistribution || {};
            const typesList = Object.keys(typesDistribution).length > 0
                ? Object.entries(typesDistribution)
                    .map(([type, count]) => `${type}: ${count}`)
                    .join(', ')
                : 'N/A';

            return `
                <div class="jira-project-metric-item">
                    <div class="jira-project-metric-header">
                        <div class="jira-project-metric-name">${project.name || projectKey}</div>
                    </div>
                    <div class="jira-project-metric-stats">
                        <div class="jira-project-stat">
                            <span class="jira-project-stat-label">Cargas Realizadas</span>
                            <span class="jira-project-stat-value">${project.count}</span>
                        </div>
                        <div class="jira-project-stat">
                            <span class="jira-project-stat-label">Items Cargados</span>
                            <span class="jira-project-stat-value">${project.itemsCount || 0}</span>
                        </div>
                        <div class="jira-project-stat">
                            <span class="jira-project-stat-label">Promedio por Carga</span>
                            <span class="jira-project-stat-value">${avgItems}</span>
                        </div>
                        <div class="jira-project-stat">
                            <span class="jira-project-stat-label">Última Carga</span>
                            <span class="jira-project-stat-value">${project.lastDate || '-'}</span>
                        </div>
                        ${Object.keys(typesDistribution).length > 0 ? `
                        <div class="jira-project-stat" style="grid-column: 1 / -1; margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid var(--border);">
                            <span class="jira-project-stat-label">Distribución por Tipo</span>
                            <span class="jira-project-stat-value" style="font-size: 0.85rem; text-align: right;">${typesList}</span>
                        </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }
    }

    /**
     * Creates HTML for an empty state
     * @param {string} message - Message to display
     * @returns {string} HTML string
     */
    function emptyStateTemplate(message) {
        return `
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <p>${message}</p>
            </div>
        `;
    }

    /**
     * Creates HTML for a generic history empty state
     * @param {string} message - Message to display
     * @returns {string} HTML string
     */
    function historyEmptyStateTemplate(message) {
        return `
            <li class="history-item" style="text-align: center; padding: 2rem; color: var(--text-muted);">
                ${message}
            </li>
        `;
    }

    // Export internal functions
    window.NexusModules.Dashboard.Templates = {
        historyItemTemplate,
        jiraReportHistoryItemTemplate,
        jiraUploadHistoryItemTemplate,
        jiraProjectMetricTemplate,
        emptyStateTemplate,
        historyEmptyStateTemplate
    };

})(window);
