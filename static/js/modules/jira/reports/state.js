/**
 * Nexus AI - Jira Reports State Module
 * Holds shared state for the Jira Reports module.
 */

(function (window) {
    'use strict';

    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Jira = window.NexusModules.Jira || {};
    window.NexusModules.Jira.Reports = window.NexusModules.Jira.Reports || {};

    const state = {
        grTestCasesChart: null,
        grBugsSeverityChart: null,
        currentProjectKey: null,
        currentGeneralReport: null,
        allProjects: [],
        highlightedIndex: -1,

        // Pagination State
        testCasesPagination: {
            currentPage: 1,
            itemsPerPage: 20,
            totalItems: 0,
            data: [],
            totals: null
        },

        defectsPagination: {
            currentPage: 1,
            itemsPerPage: 20,
            totalItems: 0,
            data: []
        },

        // Filter System State
        reportAvailableFields: [],
        reportAvailableFieldsTestCases: [],
        reportAvailableFieldsBugs: [],
        reportFilterCount: 0,
        reportActiveFilters: [],
        reportActiveFiltersTestCases: [],
        reportActiveFiltersBugs: [],
        currentFilterTab: 'test-case',
        paginationListenersSetup: false
    };

    window.NexusModules.Jira.Reports.State = state;

    // Backward compatibility for property accessors on window (if used by other modules)
    Object.defineProperty(window, 'grTestCasesChart', {
        get: () => state.grTestCasesChart,
        set: (v) => state.grTestCasesChart = v
    });
    Object.defineProperty(window, 'grBugsSeverityChart', {
        get: () => state.grBugsSeverityChart,
        set: (v) => state.grBugsSeverityChart = v
    });
    Object.defineProperty(window, 'currentGeneralReport', {
        get: () => state.currentGeneralReport,
        set: (v) => state.currentGeneralReport = v
    });
    Object.defineProperty(window, 'testCasesPagination', {
        get: () => state.testCasesPagination,
        set: (v) => state.testCasesPagination = v
    });
    Object.defineProperty(window, 'defectsPagination', {
        get: () => state.defectsPagination,
        set: (v) => state.defectsPagination = v
    });
    Object.defineProperty(window, 'currentProjectKey', {
        get: () => state.currentProjectKey,
        set: (v) => state.currentProjectKey = v
    });

})(window);
