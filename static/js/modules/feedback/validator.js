/**
 * Nexus AI - Feedback Validator Module
 * Handles validation logic for feedback forms
 */

(function (window) {
    'use strict';

    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Feedback = window.NexusModules.Feedback || {};

    window.NexusModules.Feedback.Validator = {
        /**
         * Checks if a project selection is valid for feedback (must be 'NA')
         * @param {string} projectKey 
         * @returns {object} { valid: boolean, message: string }
         */
        validateProjectSelection: function (projectKey) {
            if (projectKey !== 'NA') {
                return {
                    valid: false,
                    message: '⚠️ Por favor, asegúrate de seleccionar el proyecto "Nexus AI (NA)" para enviar feedback'
                };
            }
            return { valid: true };
        },

        /**
         * Validates the feedback submission form
         * @param {string} summary 
         * @param {string} description 
         * @returns {object} { valid: boolean, message: string }
         */
        validateSubmission: function (summary, description) {
            const summaryValue = summary ? summary.trim() : '';
            const descriptionValue = description ? description.trim() : '';

            if (!summaryValue) {
                return {
                    valid: false,
                    message: 'Por favor, ingresa un resumen para tu reporte'
                };
            }

            if (!descriptionValue || descriptionValue === '<br>') {
                return {
                    valid: false,
                    message: 'Por favor, ingresa una descripción para tu reporte'
                };
            }

            return { valid: true };
        }
    };

})(window);
