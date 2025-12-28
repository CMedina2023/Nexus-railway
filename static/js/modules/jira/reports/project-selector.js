/**
 * Nexus AI - Jira Reports Project Selector Module
 * Handles project list loading, filtering, and selection.
 */

(function (window) {
    'use strict';

    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Jira = window.NexusModules.Jira || {};
    window.NexusModules.Jira.Reports = window.NexusModules.Jira.Reports || {};

    const State = window.NexusModules.Jira.Reports.State;

    async function loadProjects() {
        const projectsSection = document.getElementById('jira-projects-section');
        const projectsLoading = document.getElementById('projects-loading');
        const projectsError = document.getElementById('projects-error');
        const reportSection = document.getElementById('jira-report-section');

        if (projectsSection) projectsSection.style.display = 'block';
        if (reportSection) reportSection.style.display = 'block';
        if (projectsLoading) projectsLoading.style.display = 'block';
        if (projectsError) projectsError.style.display = 'none';

        try {
            const response = await fetch('/api/jira/projects');
            const data = await response.json();

            if (data.success && data.projects.length > 0) {
                if (projectsLoading) projectsLoading.style.display = 'none';
                State.allProjects = data.projects.map(project => ({
                    key: project.key,
                    name: project.name,
                    displayText: `${project.name} (${project.key})`
                }));
            } else {
                if (projectsLoading) projectsLoading.style.display = 'none';
                if (projectsError) {
                    projectsError.style.display = 'block';
                    projectsError.innerHTML = `<span>❌ ${data.error || 'No se encontraron proyectos'}</span>`;
                }
            }
        } catch (error) {
            if (projectsLoading) projectsLoading.style.display = 'none';
            if (projectsError) {
                projectsError.style.display = 'block';
                projectsError.innerHTML = `<span>❌ Error: ${error.message}</span>`;
            }
        }
    }

    function renderProjectOptions(projects) {
        const dropdown = document.getElementById('project-dropdown');
        if (!dropdown) return;

        if (!projects || projects.length === 0) {
            dropdown.innerHTML = '<div class="combobox-option no-results">No se encontraron proyectos</div>';
            dropdown.style.display = 'block';
            return;
        }

        dropdown.innerHTML = '';
        projects.forEach((project) => {
            const option = document.createElement('div');
            option.className = 'combobox-option';
            option.textContent = project.displayText;
            option.dataset.projectKey = project.key;
            option.dataset.projectName = project.name;
            option.onclick = () => selectProject(project.key, project.name, project.displayText);
            dropdown.appendChild(option);
        });

        dropdown.style.display = 'block';
        State.highlightedIndex = -1;
    }

    function filterProjectOptions(searchText) {
        if (!State.allProjects || State.allProjects.length === 0) {
            loadProjects().then(() => {
                const searchLower = searchText.toLowerCase().trim();
                const filtered = searchLower === '' ? State.allProjects : State.allProjects.filter(project =>
                    project.name.toLowerCase().includes(searchLower) ||
                    project.key.toLowerCase().includes(searchLower) ||
                    project.displayText.toLowerCase().includes(searchLower)
                );
                renderProjectOptions(filtered);
            });
            return;
        }

        const searchLower = searchText.toLowerCase().trim();
        const filtered = searchLower === '' ? State.allProjects : State.allProjects.filter(project =>
            project.name.toLowerCase().includes(searchLower) ||
            project.key.toLowerCase().includes(searchLower) ||
            project.displayText.toLowerCase().includes(searchLower)
        );

        renderProjectOptions(filtered);
    }

    function showProjectDropdown() {
        const dropdown = document.getElementById('project-dropdown');
        const input = document.getElementById('project-selector-input');

        if (!dropdown || !input) return;

        if (!State.allProjects || State.allProjects.length === 0) {
            loadProjects().then(() => {
                const searchText = input.value.trim();
                filterProjectOptions(searchText);
            });
            return;
        }

        const searchText = input.value.trim();
        filterProjectOptions(searchText);
    }

    function hideProjectDropdown() {
        setTimeout(() => {
            const dropdown = document.getElementById('project-dropdown');
            if (dropdown) dropdown.style.display = 'none';
            State.highlightedIndex = -1;
        }, 200);
    }

    function selectProject(projectKey, projectName, displayText) {
        const input = document.getElementById('project-selector-input');
        const hiddenInput = document.getElementById('project-selector');
        const dropdown = document.getElementById('project-dropdown');

        if (input) input.value = displayText;
        if (hiddenInput) hiddenInput.value = projectKey;
        if (dropdown) dropdown.style.display = 'none';

        const step2Container = document.getElementById('step-2-container');
        const step3Container = document.getElementById('step-3-container');

        if (step2Container) {
            step2Container.style.display = 'block';
            step2Container.classList.add('active');
        }
        if (step3Container) {
            step3Container.style.display = 'block';
            step3Container.classList.add('active');
        }

        const step1Container = document.getElementById('step-1-container');
        if (step1Container) step1Container.classList.add('completed');

        if (projectKey && window.NexusModules.Jira.Reports.loadFilterFieldsForReport) {
            window.NexusModules.Jira.Reports.loadFilterFieldsForReport(projectKey);
        }

        // Reset widgets when selecting a new project
        if (typeof window.activeWidgets !== 'undefined') {
            window.activeWidgets = [];
        }
    }

    function handleProjectKeydown(event) {
        const dropdown = document.getElementById('project-dropdown');
        if (!dropdown || dropdown.style.display === 'none') return;

        const options = dropdown.querySelectorAll('.combobox-option:not(.no-results)');
        if (options.length === 0) return;

        if (event.key === 'ArrowDown') {
            event.preventDefault();
            State.highlightedIndex = (State.highlightedIndex + 1) % options.length;
            updateHighlight(options);
        } else if (event.key === 'ArrowUp') {
            event.preventDefault();
            State.highlightedIndex = State.highlightedIndex <= 0 ? options.length - 1 : State.highlightedIndex - 1;
            updateHighlight(options);
        } else if (event.key === 'Enter') {
            event.preventDefault();
            if (State.highlightedIndex >= 0 && State.highlightedIndex < options.length) {
                const option = options[State.highlightedIndex];
                selectProject(option.dataset.projectKey, option.dataset.projectName, option.textContent);
            }
        } else if (event.key === 'Escape') {
            dropdown.style.display = 'none';
            State.highlightedIndex = -1;
        }
    }

    function updateHighlight(options) {
        options.forEach((option, index) => {
            if (index === State.highlightedIndex) {
                option.classList.add('highlighted');
                option.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
            } else {
                option.classList.remove('highlighted');
            }
        });
    }

    async function onProjectChange() {
        const project = document.getElementById('project-selector')?.value || '';
        if (project && window.NexusModules.Jira.Reports.loadFilterFieldsForReport) {
            await window.NexusModules.Jira.Reports.loadFilterFieldsForReport(project, 'test-case');
            await window.NexusModules.Jira.Reports.loadFilterFieldsForReport(project, 'bug');
        } else {
            State.reportAvailableFieldsTestCases = [];
            State.reportAvailableFieldsBugs = [];
            State.reportAvailableFields = [];
        }
    }

    window.NexusModules.Jira.Reports.loadProjects = loadProjects;
    window.NexusModules.Jira.Reports.renderProjectOptions = renderProjectOptions;
    window.NexusModules.Jira.Reports.filterProjectOptions = filterProjectOptions;
    window.NexusModules.Jira.Reports.showProjectDropdown = showProjectDropdown;
    window.NexusModules.Jira.Reports.hideProjectDropdown = hideProjectDropdown;
    window.NexusModules.Jira.Reports.selectProject = selectProject;
    window.NexusModules.Jira.Reports.handleProjectKeydown = handleProjectKeydown;
    window.NexusModules.Jira.Reports.onProjectChange = onProjectChange;

})(window);
