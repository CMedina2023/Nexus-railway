/**
 * Nexus AI - Field Mapper Module
 * Handles UI rendering for validation results and field mapping configuration.
 */

(function (window) {
    'use strict';

    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Jira = window.NexusModules.Jira || {};
    window.NexusModules.Jira.BulkUpload = window.NexusModules.Jira.BulkUpload || {};

    // Helper functions
    function getFieldTypeIcon(type) {
        const icons = {
            'texto': '📝', 'número': '🔢', 'fecha': '📅', 'usuario': '👤',
            'opción': '📋', 'lista': '📋', 'prioridad': '⚡', 'estado': '📊'
        };
        return icons[type] || '📄';
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

    function renderFieldsStep(validationResult, csvColumns) {
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

    function renderMappingTable(validationResult, csvColumns, csvData, fieldMappings, updateCallback) {
        if (!validationResult || !validationResult.success) return;

        const mappingContainer = document.getElementById('mapping-table-container');
        const summaryEl = document.getElementById('mapping-validation-summary');

        if (!mappingContainer) return;

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

        const selects = mappingContainer.querySelectorAll('.jira-field-select');
        selects.forEach(select => {
            select.addEventListener('change', (e) => {
                updateCallback(e.target.dataset.csvColumn, e.target.value);
            });
        });
    }

    function renderConfigStep(defaultValues, updateCallback) {
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

        const issueTypeSelect = document.getElementById('default-issue-type');
        if (issueTypeSelect) {
            issueTypeSelect.addEventListener('change', (e) => updateCallback('issue_type', e.target.value));
        }
    }

    function renderPreviewTable(data, totalRows, projectKey) {
        const previewSummary = document.getElementById('preview-summary');
        const previewTable = document.getElementById('preview-table-container');

        if (previewSummary) {
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

    window.NexusModules.Jira.BulkUpload.FieldMapper = {
        renderFieldsStep: renderFieldsStep,
        renderMappingTable: renderMappingTable,
        renderConfigStep: renderConfigStep,
        renderPreviewTable: renderPreviewTable
    };

})(window);
