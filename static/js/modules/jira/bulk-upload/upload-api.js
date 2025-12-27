/**
 * Nexus AI - Upload API Module
 * Handles all API communications for Bulk Upload.
 */

(function (window) {
    'use strict';

    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Jira = window.NexusModules.Jira || {};
    window.NexusModules.Jira.BulkUpload = window.NexusModules.Jira.BulkUpload || {};

    let currentUserRole = null;
    let currentUserEmail = null;

    async function loadCurrentUserInfo() {
        if (currentUserRole) return { role: currentUserRole, email: currentUserEmail };
        try {
            const resp = await fetch('/auth/session', { headers: { 'Accept': 'application/json' } });
            if (resp.ok) {
                const data = await resp.json();
                currentUserRole = data.role || 'usuario';
                currentUserEmail = data.email || '';
            } else {
                currentUserRole = 'usuario';
            }
        } catch (e) {
            currentUserRole = 'usuario';
        }
        return { role: currentUserRole, email: currentUserEmail };
    }

    async function fetchProjects() {
        try {
            const response = await fetch('/api/jira/projects');
            return await response.json();
        } catch (error) {
            console.error('Error al cargar proyectos:', error);
            throw error;
        }
    }

    async function validateProjectAccess(projectKey) {
        await loadCurrentUserInfo();

        if (!projectKey) {
            return { status: 'unknown', hasAccess: false, message: '' };
        }

        if (['admin', 'analista_qa'].includes(currentUserRole || 'usuario')) {
            return { status: 'done', hasAccess: true, message: 'Acceso permitido por rol' };
        }

        try {
            const resp = await fetch('/api/jira/validate-project-access', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.getCsrfToken()
                },
                body: JSON.stringify({ project_key: projectKey, email: currentUserEmail })
            });
            const data = await resp.json();
            const allowed = !!data.hasAccess;

            return {
                status: 'done',
                hasAccess: allowed,
                message: data.message || (allowed ? 'Acceso validado' : 'No tienes acceso a este proyecto. Contacta al administrador del proyecto en Jira.')
            };
        } catch (error) {
            return { status: 'error', hasAccess: false, message: error.message };
        }
    }

    async function validateCsvFields(csvColumns, projectKey) {
        try {
            const response = await fetch('/api/jira/validate-csv-fields', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.getCsrfToken()
                },
                body: JSON.stringify({
                    csv_columns: csvColumns,
                    project_key: projectKey
                })
            });
            return await response.json();
        } catch (error) {
            console.error('Error en validación:', error);
            throw error;
        }
    }

    async function downloadTemplate(projectKey) {
        try {
            let url = '/api/jira/download-template';
            if (projectKey) url += `?project_key=${encodeURIComponent(projectKey)}`;

            const response = await fetch(url);
            if (response.ok) {
                const blob = await response.blob();
                const url_obj = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url_obj;
                a.download = 'plantilla_carga_masiva_jira.csv';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url_obj);
                document.body.removeChild(a);
                return true;
            } else {
                return false;
            }
        } catch (error) {
            return false;
        }
    }

    async function uploadCsv(file, projectKey, fieldMappings, defaultValues) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('project_key', projectKey);
        formData.append('field_mappings', JSON.stringify(fieldMappings));
        formData.append('default_values', JSON.stringify(defaultValues));

        const response = await fetch('/api/jira/upload-csv', {
            method: 'POST',
            headers: { 'X-CSRFToken': window.getCsrfToken() },
            body: formData
        });

        return await response.json();
    }

    function getCurrentUserInfo() {
        return { role: currentUserRole, email: currentUserEmail };
    }

    window.NexusModules.Jira.BulkUpload.Api = {
        loadUserInfo: loadCurrentUserInfo,
        getUserInfo: getCurrentUserInfo,
        fetchProjects: fetchProjects,
        validateProjectAccess: validateProjectAccess,
        validateCsvFields: validateCsvFields,
        downloadTemplate: downloadTemplate,
        uploadCsv: uploadCsv
    };

})(window);
