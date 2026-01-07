/**
 * Nexus AI - Test Case Generator Logic
 * Orquestador para la generación de casos de prueba.
 */
(function (window) {
    'use strict';

    const NexusModules = window.NexusModules || {};
    NexusModules.Generators = NexusModules.Generators || {};

    /**
     * Orquestador de Casos de Prueba
     * Actúa como facade para los submódulos especializados.
     * Importante: Se extienden las propiedades ya existentes para evitar recursión.
     */
    const TestCase = NexusModules.Generators.TestCase || {};

    /**
     * Inicializa el generador de casos de prueba
     */
    TestCase.init = function () {
        this.captureRequirementId();
        if (this.UIHandlers && typeof this.UIHandlers.init === 'function') {
            this.UIHandlers.init();
        } else {
            console.error('Test Case UIHandlers not found or invalid');
        }
    };

    /**
     * Captura el requirement_id de la URL y lo agrega al formulario
     */
    TestCase.captureRequirementId = function () {
        const urlParams = new URLSearchParams(window.location.search);
        const requirementId = urlParams.get('requirement_id');

        if (requirementId) {
            console.log('Requirement ID capturado:', requirementId);
            const form = document.getElementById('tests-form');
            if (form) {
                let hiddenInput = form.querySelector('input[name="requirement_id"]');
                if (!hiddenInput) {
                    hiddenInput = document.createElement('input');
                    hiddenInput.type = 'hidden';
                    hiddenInput.name = 'requirement_id';
                    form.appendChild(hiddenInput);
                }
                hiddenInput.value = requirementId;
            }
        }
    };

    /**
     * Compatibilidad con el estado anterior
     */
    Object.defineProperty(TestCase, 'state', {
        get: function () {
            return this.StateManager ? this.StateManager.getState() : {};
        },
        configurable: true
    });

    // Aseguramos que el módulo esté en el namespace
    NexusModules.Generators.TestCase = TestCase;
    window.NexusModules = NexusModules;
})(window);
