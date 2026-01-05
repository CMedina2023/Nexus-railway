/**
 * Nexus AI - Feedback API Module
 * Handles API calls for the feedback module
 */

(function (window) {
    'use strict';

    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Feedback = window.NexusModules.Feedback || {};

    window.NexusModules.Feedback.API = {
        /**
         * Fetches available projects (cached call in logic handled by caller, this just fetches)
         * @returns {Promise}
         */
        getProjects: function () {
            return fetch('/api/jira/projects', {
                method: 'GET',
                headers: {
                    'X-CSRFToken': getCsrfToken()
                }
            })
                .then(response => response.json());
        },

        /**
         * Validates a project key with the backend
         * @param {string} projectKey 
         * @returns {Promise}
         */
        validateProject: function (projectKey) {
            return fetch('/api/feedback/validate-project', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({ project_key: projectKey })
            })
                .then(response => response.json());
        },

        /**
         * Submits feedback data to the backend
         * @param {object} data { project_key, issue_type, summary, description }
         * @returns {Promise}
         */
        submitFeedback: function (data) {
            return fetch('/api/feedback/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify(data)
            })
                .then(response => response.json());
        }
    };

    // Helper compatibility function just in case getCsrfToken isn't global yet (though it should be)
    function getCsrfToken() {
        return window.getCsrfToken ? window.getCsrfToken() : '';
    }

})(window);
