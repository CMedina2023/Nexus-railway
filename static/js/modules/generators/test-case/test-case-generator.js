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
        if (this.UIHandlers && typeof this.UIHandlers.init === 'function') {
            this.UIHandlers.init();
        } else {
            console.error('Test Case UIHandlers not found or invalid');
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
