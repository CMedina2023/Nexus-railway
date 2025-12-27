/**
 * Nexus AI - Jira Reports Filters Module
 * Handles filter loading and management for reports.
 */

(function (window) {
    'use strict';

    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Jira = window.NexusModules.Jira || {};
    window.NexusModules.Jira.Reports = window.NexusModules.Jira.Reports || {};

    const State = window.NexusModules.Jira.Reports.State;

    async function loadFilterFieldsForReport(projectKey, issuetype = null) {
        if (!projectKey) {
            if (issuetype === 'test-case' || issuetype === null) State.reportAvailableFieldsTestCases = [];
            if (issuetype === 'bug' || issuetype === null) State.reportAvailableFieldsBugs = [];
            if (!issuetype) State.reportAvailableFields = [];
            return;
        }

        try {
            let url = `/api/jira/project/${projectKey}/filter-fields`;
            if (issuetype) {
                const jiraIssuetype = issuetype === 'test-case' ? 'Test Case' : (issuetype === 'bug' ? 'Bug' : issuetype);
                url += `?issuetype=${encodeURIComponent(jiraIssuetype)}`;
            }

            const response = await fetch(url);
            const data = await response.json();

            if (data.success && data.fields) {
                const availableFieldsList = data.fields.available_fields || [];
                const fieldValues = data.fields.field_values || {};
                const standardMapping = {
                    'status': { label: 'Estado', type: 'select' },
                    'priority': { label: 'Prioridad', type: 'select' },
                    'assignee': { label: 'Asignado', type: 'text' },
                    'labels': { label: 'Etiqueta', type: 'text' },
                    'affectsVersions': { label: 'Affects Version', type: 'select' },
                    'fixVersions': { label: 'Versión de Corrección', type: 'select' }
                };

                const fieldsResult = [];

                for (const field of availableFieldsList) {
                    if (field.id === 'issuetype' || field.id.toLowerCase() === 'tipo') continue;

                    if (field.id in standardMapping) {
                        const m = standardMapping[field.id];
                        const opts = fieldValues[field.id] || [];
                        if (m.type === 'select' && opts.length === 0) continue;
                        fieldsResult.push({ value: field.id, label: m.label, type: m.type, options: opts });
                    } else if (field.custom) {
                        const opts = fieldValues[field.id] || field.allowedValues || field.allowed_values || [];
                        if (opts.length === 0) continue;
                        fieldsResult.push({ value: field.id, label: field.name, type: 'select', options: Array.isArray(opts) ? opts : [] });
                    }
                }

                if (issuetype === 'test-case') State.reportAvailableFieldsTestCases = fieldsResult;
                else if (issuetype === 'bug') State.reportAvailableFieldsBugs = fieldsResult;
                else {
                    State.reportAvailableFields = fieldsResult;
                    State.reportAvailableFieldsTestCases = fieldsResult;
                    State.reportAvailableFieldsBugs = fieldsResult;
                }
            }
        } catch (error) {
            console.error('Error al cargar campos de filtros:', error);
        }
    }

    function switchFilterTab(tabType) {
        State.currentFilterTab = tabType;
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));

        const tabEl = document.getElementById(`tab-${tabType}`);
        if (tabEl) tabEl.classList.add('active');

        const target = event && event.target ? event.target.closest('.filter-tab') : null;
        if (target) target.classList.add('active');

        const project = document.getElementById('project-selector')?.value || '';
        if (project) {
            const fields = tabType === 'test-case' ? State.reportAvailableFieldsTestCases : State.reportAvailableFieldsBugs;
            if (fields.length === 0) loadFilterFieldsForReport(project, tabType);
        }
    }

    async function addReportFilter(filterType = null) {
        const type = filterType || State.currentFilterTab;
        const project = document.getElementById('project-selector')?.value || '';

        if (!project) { alert('Por favor, selecciona un proyecto primero.'); return; }

        let available = type === 'test-case' ? State.reportAvailableFieldsTestCases : State.reportAvailableFieldsBugs;

        if (available.length === 0) {
            try {
                await loadFilterFieldsForReport(project, type);
                available = type === 'test-case' ? State.reportAvailableFieldsTestCases : State.reportAvailableFieldsBugs;
                if (available.length === 0) { alert('No se pudieron cargar los campos disponibles.'); return; }
            } catch (e) { return; }
        }

        State.reportFilterCount++;
        const grid = document.getElementById(type === 'test-case' ? 'filters-grid-test-case' : 'filters-grid-bug');
        if (!grid) return;

        const filterId = `report-filter-${type}-${State.reportFilterCount}`;
        const group = document.createElement('div');
        group.className = 'filter-group';
        group.id = filterId;
        group.dataset.filterType = type;

        const fieldSelect = document.createElement('select');
        fieldSelect.className = 'filter-field-select';
        fieldSelect.innerHTML = '<option value="">Selecciona un campo...</option>';
        available.forEach(f => {
            const opt = document.createElement('option');
            opt.value = f.value;
            opt.textContent = f.label;
            fieldSelect.appendChild(opt);
        });
        fieldSelect.onchange = () => updateReportFilterValue(filterId, fieldSelect.value, type);

        group.innerHTML = `
            <label class="filter-label">Campo</label>
            ${fieldSelect.outerHTML}
            <label class="filter-label">Valor</label>
            <div id="${filterId}-value">
                <input type="text" class="filter-value-input" placeholder="Selecciona un campo primero" disabled>
            </div>
            <button class="filter-remove-btn" onclick="removeReportFilter('${filterId}')" title="Eliminar filtro">✕</button>
        `;

        grid.appendChild(group);

        const newSelect = group.querySelector('.filter-field-select');
        newSelect.onchange = () => updateReportFilterValue(filterId, newSelect.value, type);
    }

    function updateReportFilterValue(filterId, fieldValue, filterType = null) {
        const type = filterType || document.getElementById(filterId)?.dataset.filterType || State.currentFilterTab;
        const available = type === 'test-case' ? State.reportAvailableFieldsTestCases : State.reportAvailableFieldsBugs;
        const field = available.find(f => f.value === fieldValue);
        const container = document.getElementById(`${filterId}-value`);

        if (!field || !container) {
            if (container) container.innerHTML = '<input type="text" class="filter-value-input" placeholder="Selecciona un campo primero" disabled>';
            return;
        }

        if (field.type === 'select') {
            container.innerHTML = `
                <select class="filter-value-select" onchange="window.NexusModules.Jira.Reports.updateReportActiveFilters()">
                    <option value="">Todos</option>
                    ${field.options.map(opt => `<option value="${opt}">${opt}</option>`).join('')}
                </select>`;
        } else {
            container.innerHTML = '<input type="text" class="filter-value-input" placeholder="Ingresa el valor..." onchange="window.NexusModules.Jira.Reports.updateReportActiveFilters()">';
        }
    }

    function removeReportFilter(filterId) {
        const el = document.getElementById(filterId);
        if (el) el.remove();
        State.reportActiveFilters = State.reportActiveFilters.filter(f => f.id !== filterId);
        State.reportActiveFiltersTestCases = State.reportActiveFiltersTestCases.filter(f => f.id !== filterId);
        State.reportActiveFiltersBugs = State.reportActiveFiltersBugs.filter(f => f.id !== filterId);
        updateReportActiveFilters();
    }

    function updateReportActiveFilters() {
        State.reportActiveFiltersTestCases = [];
        State.reportActiveFiltersBugs = [];
        State.reportActiveFilters = [];

        const process = (gridId, type, target) => {
            document.querySelectorAll(`${gridId} .filter-group`).forEach(g => {
                const fs = g.querySelector('.filter-field-select');
                const vi = g.querySelector('.filter-value-input');
                const vs = g.querySelector('.filter-value-select');
                if (fs && fs.value) {
                    const fields = type === 'test-case' ? State.reportAvailableFieldsTestCases : State.reportAvailableFieldsBugs;
                    const field = fields.find(f => f.value === fs.value);
                    const value = vi ? vi.value : (vs ? vs.value : '');
                    if (value) {
                        const filter = { id: g.id, field: fs.value, fieldLabel: field ? field.label : fs.value, value: value, type: type };
                        target.push(filter);
                        State.reportActiveFilters.push(filter);
                    }
                }
            });
        };

        process('#filters-grid-test-case', 'test-case', State.reportActiveFiltersTestCases);
        process('#filters-grid-bug', 'bug', State.reportActiveFiltersBugs);

        const tcCount = document.getElementById('test-case-filter-count');
        const bCount = document.getElementById('bug-filter-count');
        if (tcCount) tcCount.textContent = State.reportActiveFiltersTestCases.length;
        if (bCount) bCount.textContent = State.reportActiveFiltersBugs.length;

        const container = document.getElementById('active-report-filters');
        if (!container) return;

        const title = container.querySelector('div:first-child') || (() => {
            const t = document.createElement('div');
            t.style.cssText = 'width: 100%; margin-bottom: 0.5rem; font-size: 0.85rem; color: var(--text-muted); font-weight: 600;';
            t.textContent = 'Filtros Activos:';
            return t;
        })();

        container.innerHTML = '';
        container.appendChild(title);

        State.reportActiveFilters.forEach(f => {
            const b = document.createElement('div');
            b.className = `filter-badge ${f.type}`;
            b.innerHTML = `
                <span class="filter-badge-type">${f.type === 'test-case' ? 'TC' : 'BUG'}</span>
                <span>${f.fieldLabel}: ${f.value}</span>
                <span class="filter-badge-remove" onclick="removeReportFilter('${f.id}')">✕</span>
            `;
            container.appendChild(b);
        });
    }

    function generateReportWithFilters() {
        const projectKey = document.getElementById('project-selector')?.value || '';
        const projectInput = document.getElementById('project-selector-input');
        const projectName = projectInput ? projectInput.value.split(' (')[0] : '';

        if (!projectKey) { alert('Por favor, selecciona un proyecto primero.'); return; }

        const projectsSection = document.getElementById('jira-projects-section');
        const reportSection = document.getElementById('jira-report-section');
        if (projectsSection) projectsSection.style.display = 'none';
        if (reportSection) reportSection.style.display = 'block';

        if (window.NexusModules.Jira.Reports.loadProjectMetrics) {
            window.NexusModules.Jira.Reports.loadProjectMetrics(projectKey, projectName, {
                testCases: State.reportActiveFiltersTestCases,
                bugs: State.reportActiveFiltersBugs
            });
        }
    }

    window.NexusModules.Jira.Reports.loadFilterFieldsForReport = loadFilterFieldsForReport;
    window.NexusModules.Jira.Reports.switchFilterTab = switchFilterTab;
    window.NexusModules.Jira.Reports.addReportFilter = addReportFilter;
    window.NexusModules.Jira.Reports.removeReportFilter = removeReportFilter;
    window.NexusModules.Jira.Reports.updateReportActiveFilters = updateReportActiveFilters;
    window.NexusModules.Jira.Reports.generateReportWithFilters = generateReportWithFilters;

})(window);
