/**
 * Nexus AI - UI Step Navigator
 * Handles visual transitions between wizard steps.
 */

(function (window) {
    'use strict';

    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Jira = window.NexusModules.Jira || {};
    window.NexusModules.Jira.BulkUpload = window.NexusModules.Jira.BulkUpload || {};

    const State = window.NexusModules.Jira.BulkUpload.State;

    function updateStepIndicator(step) {
        const steps = document.querySelectorAll('.step');
        steps.forEach((s, idx) => {
            const stepNum = parseInt(s.dataset.step || idx + 1);
            s.classList.remove('active', 'completed');
            if (stepNum < step) {
                s.classList.add('completed');
            } else if (stepNum === step) {
                s.classList.add('active');
            }
        });
    }

    function showStepContent(step) {
        for (let i = 1; i <= 7; i++) {
            const content = document.getElementById(`step-${i}-content`);
            if (content) {
                content.style.display = 'none';
                content.classList.remove('active');
            }
        }
        const currentContent = document.getElementById(`step-${step}-content`);
        if (currentContent) {
            currentContent.style.display = 'block';
            currentContent.classList.add('active');
        }
    }

    function updateActionsBar(step, callbacks) {
        const actionsBar = document.getElementById('carga-masiva-actions');
        const prevBtn = document.getElementById('prev-step-btn');
        const revalidateBtn = document.getElementById('revalidate-btn');
        const uploadBtn = document.getElementById('upload-csv-btn');

        if (!actionsBar) return;

        actionsBar.style.display = step >= 2 ? 'flex' : 'none';

        if (prevBtn) prevBtn.style.display = step > 1 ? 'inline-flex' : 'none';
        if (revalidateBtn) revalidateBtn.style.display = (step >= 4 && step <= 5) ? 'inline-flex' : 'none';
        if (uploadBtn) uploadBtn.style.display = step === 7 ? 'inline-flex' : 'none';

        const nextBtn = document.getElementById('next-step-btn');
        if (nextBtn) nextBtn.remove();

        if (step === 4 || step === 5 || step === 6) {
            const nextButton = document.createElement('button');
            nextButton.id = 'next-step-btn';
            nextButton.className = 'btn btn-primary';
            nextButton.textContent = step === 4 ? 'Continuar al Mapeo →' :
                step === 5 ? 'Continuar a Vista Previa →' : 'Continuar a Carga →';

            nextButton.onclick = () => {
                if (step === 4 && callbacks.onGoToMapping) callbacks.onGoToMapping();
                else if (step === 5 && callbacks.onGoToPreview) callbacks.onGoToPreview();
                else if (step === 6 && callbacks.onGoToUpload) callbacks.onGoToUpload();
            };

            const actionsRight = actionsBar.querySelector('.actions-right');
            if (actionsRight) actionsRight.insertBefore(nextButton, actionsRight.firstChild);
        }
    }

    function goToStep(step, callbacks = {}) {
        State.update({ currentStep: step });
        updateStepIndicator(step);
        showStepContent(step);
        updateActionsBar(step, callbacks);
    }

    function updateValidationStep(stepNum, completed) {
        const statusEl = document.getElementById(`step-${stepNum}-status`);
        if (statusEl) {
            statusEl.textContent = completed ? '✓' : '⏳';
            statusEl.style.color = completed ? 'var(--success)' : 'var(--accent)';
        }
    }

    function resetUI() {
        const uploadBtn = document.getElementById('upload-csv-btn');
        if (uploadBtn) uploadBtn.disabled = false;

        const projectInput = document.getElementById('carga-masiva-project-selector-input');
        const projectHidden = document.getElementById('carga-masiva-project-selector');
        const projectDropdown = document.getElementById('carga-masiva-dropdown');
        if (projectInput) projectInput.value = '';
        if (projectHidden) projectHidden.value = '';
        if (projectDropdown) projectDropdown.style.display = 'none';

        const fileInfo = document.getElementById('file-info');
        const fileInput = document.getElementById('csv-file-input');
        if (fileInfo) fileInfo.style.display = 'none';
        if (fileInput) fileInput.value = '';

        const previewSummary = document.getElementById('preview-summary');
        const previewTable = document.getElementById('preview-table-container');
        if (previewSummary) previewSummary.innerHTML = '';
        if (previewTable) previewTable.innerHTML = '';

        const validationSummary = document.getElementById('validation-summary');
        const requiredFieldsSection = document.getElementById('required-fields-section');
        const optionalFieldsSection = document.getElementById('optional-fields-section');
        const fieldMappingsSection = document.getElementById('field-mappings-section');
        if (validationSummary) { validationSummary.innerHTML = ''; validationSummary.style.display = 'none'; }
        if (requiredFieldsSection) requiredFieldsSection.innerHTML = '';
        if (optionalFieldsSection) optionalFieldsSection.innerHTML = '';
        if (fieldMappingsSection) fieldMappingsSection.innerHTML = '';

        const uploadFinalStatus = document.getElementById('upload-final-status');
        if (uploadFinalStatus) uploadFinalStatus.innerHTML = '';

        const uploadStatus = document.getElementById('upload-status');
        if (uploadStatus) uploadStatus.style.display = 'none';

        goToStep(1, {});
    }

    window.NexusModules.Jira.BulkUpload.StepNavigator = {
        goToStep,
        updateValidationStep,
        resetUI
    };

})(window);
