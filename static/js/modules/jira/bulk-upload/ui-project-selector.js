/**
 * Nexus AI - Project Selector UI Module
 * Handles the project selection, access message, and dropdown logic.
 */

(function (window) {
    'use strict';

    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Jira = window.NexusModules.Jira || {};
    window.NexusModules.Jira.BulkUpload = window.NexusModules.Jira.BulkUpload || {};

    let cargaMasivaHighlightedIndex = -1;

    function renderOptions(projects, onSelect) {
        const dropdown = document.getElementById('carga-masiva-dropdown');
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
            option.onclick = () => onSelect(project.key, project.name, project.displayText);
            dropdown.appendChild(option);
        });

        dropdown.style.display = 'block';
        cargaMasivaHighlightedIndex = -1;
    }

    function filterProjects(searchText, allProjects, onSelect) {
        if (!allProjects || allProjects.length === 0) return;

        const searchLower = searchText.toLowerCase().trim();
        if (searchLower === '') {
            renderOptions(allProjects, onSelect);
            return;
        }

        const filtered = allProjects.filter(project =>
            project.name.toLowerCase().includes(searchLower) ||
            project.key.toLowerCase().includes(searchLower) ||
            project.displayText.toLowerCase().includes(searchLower)
        );

        renderOptions(filtered, onSelect);
    }

    function showDropdown(allProjects, onSelect) {
        const dropdown = document.getElementById('carga-masiva-dropdown');
        const input = document.getElementById('carga-masiva-project-selector-input');
        if (!dropdown || !input) return;

        if (!allProjects || allProjects.length === 0) return;

        const searchText = input.value.trim();
        if (searchText === '') {
            renderOptions(allProjects, onSelect);
        } else {
            filterProjects(searchText, allProjects, onSelect);
        }
    }

    function hideDropdown() {
        setTimeout(() => {
            const dropdown = document.getElementById('carga-masiva-dropdown');
            if (dropdown) dropdown.style.display = 'none';
            cargaMasivaHighlightedIndex = -1;
        }, 200);
    }

    function handleKeydown(event, onSelect) {
        const dropdown = document.getElementById('carga-masiva-dropdown');
        if (!dropdown || dropdown.style.display === 'none') return;

        const options = dropdown.querySelectorAll('.combobox-option:not(.no-results)');
        if (options.length === 0) return;

        if (event.key === 'ArrowDown') {
            event.preventDefault();
            cargaMasivaHighlightedIndex = (cargaMasivaHighlightedIndex + 1) % options.length;
            updateHighlight(options);
        } else if (event.key === 'ArrowUp') {
            event.preventDefault();
            cargaMasivaHighlightedIndex = cargaMasivaHighlightedIndex <= 0 ? options.length - 1 : cargaMasivaHighlightedIndex - 1;
            updateHighlight(options);
        } else if (event.key === 'Enter') {
            event.preventDefault();
            if (cargaMasivaHighlightedIndex >= 0 && cargaMasivaHighlightedIndex < options.length) {
                const option = options[cargaMasivaHighlightedIndex];
                onSelect(
                    option.dataset.projectKey,
                    option.dataset.projectName,
                    option.textContent
                );
            }
        } else if (event.key === 'Escape') {
            dropdown.style.display = 'none';
            cargaMasivaHighlightedIndex = -1;
        }
    }

    function updateHighlight(options) {
        options.forEach((option, index) => {
            if (index === cargaMasivaHighlightedIndex) {
                option.classList.add('highlighted');
                option.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
            } else {
                option.classList.remove('highlighted');
            }
        });
    }

    function updateAccessMessage(type, message) {
        const msgEl = document.getElementById('carga-masiva-access-message');
        const uploadBtn = document.getElementById('upload-csv-btn');
        if (!msgEl) return;

        if (!message) {
            msgEl.style.display = 'none';
        } else {
            msgEl.style.display = 'block';
            msgEl.textContent = message;
            msgEl.style.color = type === 'error' ? '#ef4444' : type === 'loading' ? 'var(--text-secondary)' : '#22c55e';
        }

        if (uploadBtn) {
            if (type === 'error' || type === 'loading') {
                uploadBtn.disabled = true;
            } else if (type === 'success') {
                uploadBtn.disabled = false;
            }
        }
    }

    window.NexusModules.Jira.BulkUpload.ProjectSelector = {
        renderOptions,
        filterProjects,
        showDropdown,
        hideDropdown,
        handleKeydown,
        updateAccessMessage
    };

})(window);
