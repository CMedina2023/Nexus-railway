/**
 * Nexus AI - Generators Facade
 * Orquestador principal que inicializa los submódulos.
 * Reemplaza la implementación monolítica anterior.
 */
(function (window) {
    'use strict';

    // Ensure namespace exists without wiping it
    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Generators = window.NexusModules.Generators || {};

    let initialized = false;

    /**
     * Inicializa todos los generadores
     */
    function initGenerators() {
        if (initialized) {
            console.log('Nexus Generators already initialized');
            return;
        }

        console.log('Initializing Nexus Generators...');
        initialized = true;

        // Initialize Story Generator
        if (window.NexusModules.Generators.Story && typeof window.NexusModules.Generators.Story.init === 'function') {
            window.NexusModules.Generators.Story.init();
        } else {
            console.warn('Story Generator module not found or invalid');
        }

        // Initialize Story Jira
        if (window.NexusModules.Generators.StoryJira && typeof window.NexusModules.Generators.StoryJira.init === 'function') {
            window.NexusModules.Generators.StoryJira.init();
        }

        // Initialize Test Case Generator
        if (window.NexusModules.Generators.TestCase && typeof window.NexusModules.Generators.TestCase.init === 'function') {
            window.NexusModules.Generators.TestCase.init();
        } else {
            console.warn('Test Case Generator module not found or invalid');
        }

        // Initialize Test Case Jira
        if (window.NexusModules.Generators.TestCaseJira && typeof window.NexusModules.Generators.TestCaseJira.init === 'function') {
            window.NexusModules.Generators.TestCaseJira.init();
        }
    }

    // Expose init function
    window.NexusModules.Generators.init = initGenerators;

    // Auto-initialize if DOM is ready, otherwise wait
    // This ensures backward compatibility if main.js expects it to run automatically
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initGenerators);
    } else {
        initGenerators();
    }

})(window);
