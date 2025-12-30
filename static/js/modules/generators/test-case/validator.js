/**
 * Nexus AI - Test Case Validator
 * Lógica de validación para el formulario de casos de prueba.
 */
(function (window) {
    'use strict';

    const NexusModules = window.NexusModules || {};
    NexusModules.Generators = NexusModules.Generators || {};
    NexusModules.Generators.TestCase = NexusModules.Generators.TestCase || {};

    // Dependencias
    const Utils = NexusModules.Generators.Utils;

    /**
     * Validador de Casos de Prueba
     */
    NexusModules.Generators.TestCase.Validator = {
        /**
         * Valida los campos del formulario antes de enviar
         * @param {HTMLFormElement} form - Formulario a validar
         * @returns {boolean} True si es válido
         */
        validateForm(form) {
            const fileInput = document.getElementById('tests-file');
            const areaSelect = document.getElementById('tests-area');
            const selectedTypes = Array.from(document.querySelectorAll('input[name="test_types"]:checked'));
            const validationErrors = [];

            if (!fileInput.files.length) {
                validationErrors.push('📄 Debes cargar un archivo (DOCX o PDF)');
                Utils.highlightError('tests-drop-zone');
            }

            if (!areaSelect || !areaSelect.value) {
                validationErrors.push('📋 Debes seleccionar un área');
                Utils.highlightError('tests-area');
            }

            if (selectedTypes.length === 0) {
                validationErrors.push('✅ Debes seleccionar al menos un tipo de prueba');
                const checkboxContainers = document.querySelectorAll('input[name="test_types"]');
                checkboxContainers.forEach(cb => {
                    const parent = cb.closest('.checkbox-item');
                    if (parent) Utils.highlightError(parent);
                });
            }

            if (validationErrors.length > 0) {
                const errorMessage = '⚠️ No puedes generar la vista previa:\n\n' + validationErrors.join('\n');
                window.showDownloadNotification(errorMessage, 'error');
                return false;
            }

            return true;
        }
    };

    window.NexusModules = NexusModules;
})(window);
