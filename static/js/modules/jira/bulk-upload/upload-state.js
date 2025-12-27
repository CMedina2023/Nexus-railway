/**
 * Nexus AI - Upload State Manager
 * Centralizes state management for the Bulk Upload Wizard.
 */

(function (window) {
    'use strict';

    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Jira = window.NexusModules.Jira || {};
    window.NexusModules.Jira.BulkUpload = window.NexusModules.Jira.BulkUpload || {};

    const initialState = {
        isUploadingCsv: false,
        selectedCsvFile: null,
        cargaMasivaProjects: [],
        currentStep: 1,
        csvColumns: [],
        csvData: [],
        validationResult: null,
        fieldMappings: {},
        defaultValues: {},
        projectAccessState: { status: 'unknown', hasAccess: false, message: '' }
    };

    let state = { ...initialState };

    function getState() {
        return state;
    }

    function resetState() {
        // preserve projects if loaded to avoid refetching unnecessary
        const projects = state.cargaMasivaProjects;
        state = { ...initialState, cargaMasivaProjects: projects };
    }

    function updateState(updates) {
        state = { ...state, ...updates };
        return state;
    }

    // Expose
    window.NexusModules.Jira.BulkUpload.State = {
        get: getState,
        reset: resetState,
        update: updateState
    };

})(window);
