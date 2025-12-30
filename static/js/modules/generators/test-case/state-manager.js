/**
 * Nexus AI - Test Case State Manager
 * Gestión del estado para el generador de casos de prueba.
 */
(function (window) {
    'use strict';

    const NexusModules = window.NexusModules || {};
    NexusModules.Generators = NexusModules.Generators || {};
    NexusModules.Generators.TestCase = NexusModules.Generators.TestCase || {};

    /**
     * Gestor de estado de Casos de Prueba
     */
    NexusModules.Generators.TestCase.StateManager = {
        state: {
            currentData: null,
            currentHtml: null,
            currentCsv: null,
            editingIndex: null
        },

        /**
         * Obtiene el estado actual
         * @returns {Object}
         */
        getState() {
            return this.state;
        },

        /**
         * Actualiza el estado con nuevos datos de generación
         * @param {Object} data - Datos devueltos por la API
         */
        setGeneratedData(data) {
            this.state.currentData = data.test_cases;
            window.currentTestsData = data.test_cases;
            this.state.currentHtml = data.html_content;
            this.state.currentCsv = data.csv_content;
        },

        /**
         * Resetea el estado a sus valores iniciales
         */
        resetState() {
            this.state.currentData = null;
            this.state.currentHtml = null;
            this.state.currentCsv = null;
            this.state.editingIndex = null;
        }
    };

    window.NexusModules = NexusModules;
})(window);
