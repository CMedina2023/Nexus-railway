/**
 * Nexus AI - Jira Reports Module
 * Entry point that exposes functionality from sub-modules.
 * NOW MODULARIZED: Logic is in jira/reports/*.js
 */

(function (window) {
    'use strict';

    window.NexusModules = window.NexusModules || {};
    // Ensure the namespace exists (should be populated by submodules)
    window.NexusModules.Jira = window.NexusModules.Jira || {};
    window.NexusModules.Jira.Reports = window.NexusModules.Jira.Reports || {};

    const Reports = window.NexusModules.Jira.Reports;
    const State = window.NexusModules.Jira.Reports.State;

    // We expose functions to window for backward compatibility with HTML on-click handlers
    // and older external module references.

    window.initJiraReports = Reports.initJiraReports;
    window.switchReportOperation = Reports.switchReportOperation;
    window.resetReportsToHub = Reports.resetReportsToHub;
    window.loadProjects = Reports.loadProjects;
    window.filterProjectOptions = Reports.filterProjectOptions;
    window.showProjectDropdown = Reports.showProjectDropdown;
    window.hideProjectDropdown = Reports.hideProjectDropdown;
    window.handleProjectKeydown = Reports.handleProjectKeydown;
    window.switchFilterTab = Reports.switchFilterTab;
    window.addReportFilter = Reports.addReportFilter;
    window.removeReportFilter = Reports.removeReportFilter;
    window.updateReportActiveFilters = Reports.updateReportActiveFilters;
    window.generateReportWithFilters = Reports.generateReportWithFilters;
    window.showProjectsSection = Reports.showProjectsSection;
    window.onProjectChange = Reports.onProjectChange;
    // selectProject is implicitly called by renders, but if referenced globally:
    window.selectProject = Reports.selectProject;

    // Property compatibility is handled in state.js via Object.defineProperty

})(window);
