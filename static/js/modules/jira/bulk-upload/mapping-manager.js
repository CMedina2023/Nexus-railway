/**
 * Nexus AI - Mapping Manager
 * Handles saving and loading of field mappings.
 */

(function (window) {
    'use strict';

    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Jira = window.NexusModules.Jira || {};
    window.NexusModules.Jira.BulkUpload = window.NexusModules.Jira.BulkUpload || {};

    const State = window.NexusModules.Jira.BulkUpload.State;

    function saveMapping(showStatusCallback) {
        const state = State.get();
        const projectSelector = document.getElementById('carga-masiva-project-selector');

        if (!projectSelector || !projectSelector.value) {
            if (showStatusCallback) showStatusCallback('error', 'Debes seleccionar un proyecto');
            return;
        }

        const mappingData = {
            project_key: projectSelector.value,
            field_mappings: state.fieldMappings,
            default_values: state.defaultValues,
            csv_columns: state.csvColumns,
            saved_at: new Date().toISOString()
        };

        const mappingName = prompt('Ingresa un nombre para este mapeo:');
        if (!mappingName) return;

        try {
            const savedMappings = JSON.parse(localStorage.getItem('jira_field_mappings') || '{}');
            savedMappings[mappingName] = mappingData;
            localStorage.setItem('jira_field_mappings', JSON.stringify(savedMappings));
            if (showStatusCallback) showStatusCallback('success', 'Mapeo guardado exitosamente');
        } catch (error) {
            console.error('Error al guardar mapeo:', error);
            if (showStatusCallback) showStatusCallback('error', 'Error al guardar el mapeo');
        }
    }

    function loadMapping(renderCallback, showStatusCallback) {
        const projectSelector = document.getElementById('carga-masiva-project-selector');
        if (!projectSelector || !projectSelector.value) {
            if (showStatusCallback) showStatusCallback('error', 'Debes seleccionar un proyecto');
            return;
        }

        try {
            const savedMappings = JSON.parse(localStorage.getItem('jira_field_mappings') || '{}');
            const mappingNames = Object.keys(savedMappings);
            if (mappingNames.length === 0) {
                if (showStatusCallback) showStatusCallback('error', 'No hay mapeos guardados');
                return;
            }

            const projectMappings = mappingNames.filter(name => savedMappings[name].project_key === projectSelector.value);
            if (projectMappings.length === 0) {
                if (showStatusCallback) showStatusCallback('error', 'No hay mapeos guardados para este proyecto');
                return;
            }

            const mappingName = prompt(`Mapeos disponibles:\n${projectMappings.join('\n')}\n\nIngresa el nombre del mapeo a cargar:`);
            if (!mappingName) return;

            const mappingData = savedMappings[mappingName];
            if (!mappingData) {
                if (showStatusCallback) showStatusCallback('error', 'El mapeo ingresado no existe');
                return;
            }

            if (mappingData.project_key !== projectSelector.value) {
                if (showStatusCallback) showStatusCallback('error', 'Este mapeo no corresponde al proyecto seleccionado');
                return;
            }

            State.update({
                fieldMappings: mappingData.field_mappings || {},
                defaultValues: mappingData.default_values || {}
            });

            if (renderCallback) renderCallback();
            if (showStatusCallback) showStatusCallback('success', 'Mapeo cargado exitosamente');
        } catch (error) {
            console.error('Error al cargar mapeo:', error);
            if (showStatusCallback) showStatusCallback('error', 'Error al cargar el mapeo');
        }
    }

    function setupButtons(renderCallback, showStatusCallback) {
        const saveMappingBtn = document.getElementById('save-mapping-btn');
        const loadMappingBtn = document.getElementById('load-mapping-btn');
        if (saveMappingBtn) saveMappingBtn.onclick = () => saveMapping(showStatusCallback);
        if (loadMappingBtn) loadMappingBtn.onclick = () => loadMapping(renderCallback, showStatusCallback);
    }

    window.NexusModules.Jira.BulkUpload.MappingManager = {
        save: saveMapping,
        load: loadMapping,
        setupButtons: setupButtons
    };

})(window);
