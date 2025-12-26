/**
 * Nexus AI - Feedback Module
 * Handles functionality related to sending feedback/bugs to Jira
 */

(function (window) {
    'use strict';

    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Feedback = window.NexusModules.Feedback || {};

    let selectedFeedbackIssueType = 'Bug';
    let selectedFeedbackProjectKey = '';
    let feedbackProjectLocked = false; // Variable para bloquear cambio de proyecto
    let feedbackAllProjects = []; // Almacenar todos los proyectos

    // Cargar TODOS los proyectos disponibles (reutiliza endpoint existente)
    function loadFeedbackProjects() {
        fetch('/api/jira/projects', {
            method: 'GET',
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success && data.projects && data.projects.length > 0) {
                    feedbackAllProjects = data.projects;
                    renderFeedbackProjects(feedbackAllProjects);
                } else {
                    showDownloadNotification(data.error || 'No hay proyectos disponibles', 'error');
                }
            })
            .catch(error => {
                console.error('Error cargando proyectos:', error);
                showDownloadNotification('Error al cargar proyectos: ' + error.message, 'error');
            });
    }

    // Renderizar proyectos en el dropdown
    function renderFeedbackProjects(projects) {
        const dropdown = document.getElementById('feedback-dropdown');
        if (!dropdown) return;

        dropdown.innerHTML = '';

        if (projects.length === 0) {
            const noResults = document.createElement('div');
            noResults.className = 'combobox-option';
            noResults.style.color = 'var(--text-muted)';
            noResults.style.cursor = 'default';
            noResults.textContent = 'No se encontraron proyectos';
            dropdown.appendChild(noResults);
            return;
        }

        projects.forEach(project => {
            const option = document.createElement('div');
            option.className = 'combobox-option';
            option.textContent = `${project.name} (${project.key})`;
            option.dataset.key = project.key;
            option.dataset.name = project.name;
            option.dataset.isNexus = project.key === 'NA';

            option.addEventListener('mousedown', function (e) {
                e.preventDefault();
                selectFeedbackProject(project.key, project.name);
            });

            dropdown.appendChild(option);
        });
    }

    // Filtrar proyectos
    window.filterFeedbackProjects = function (searchTerm) {
        if (feedbackProjectLocked) return; // No permitir filtrar si está bloqueado

        const filtered = feedbackAllProjects.filter(project =>
            project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            project.key.toLowerCase().includes(searchTerm.toLowerCase())
        );
        renderFeedbackProjects(filtered);
    };

    // Mostrar dropdown
    window.showFeedbackDropdown = function () {
        if (feedbackProjectLocked) return; // No permitir abrir si está bloqueado

        const dropdown = document.getElementById('feedback-dropdown');
        if (dropdown) {
            dropdown.style.display = 'block';

            // Si ya hay proyectos cargados, mostrarlos
            if (feedbackAllProjects.length > 0) {
                renderFeedbackProjects(feedbackAllProjects);
            }
            // Si no, el mensaje "Cargando..." ya está en el HTML
        }
    };

    // Ocultar dropdown
    window.hideFeedbackDropdown = function () {
        setTimeout(() => {
            const dropdown = document.getElementById('feedback-dropdown');
            if (dropdown) dropdown.style.display = 'none';
        }, 200);
    };

    // Manejar teclas
    window.handleFeedbackKeydown = function (event) {
        if (feedbackProjectLocked) {
            event.preventDefault();
            return;
        }
        // Aquí puedes agregar navegación con flechas si lo deseas
    };

    // Mostrar notificación temporal de feedback
    function showFeedbackNotification(message, type = 'warning') {
        // Crear elemento de notificación
        const notification = document.createElement('div');
        notification.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: ${type === 'warning' ? 'rgba(245, 158, 11, 0.95)' : 'rgba(239, 68, 68, 0.95)'};
                    color: white;
                    padding: 1rem 1.5rem;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                    z-index: 9999;
                    animation: slideIn 0.3s ease;
                    max-width: 400px;
                    font-size: 0.9rem;
                `;
        notification.textContent = message;
        document.body.appendChild(notification);

        // Auto-ocultar después de 3 segundos
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        }, 3000);
    }

    // Seleccionar proyecto
    function selectFeedbackProject(projectKey, projectName) {
        if (feedbackProjectLocked && projectKey !== selectedFeedbackProjectKey) {
            showFeedbackNotification('El proyecto ya ha sido seleccionado y no puede ser cambiado', 'warning');
            return;
        }

        const input = document.getElementById('feedback-project-selector-input');
        const hiddenInput = document.getElementById('feedback-project-selector');

        // Verificar si es Nexus AI (NA)
        const isNexusAI = projectKey === 'NA';

        if (!isNexusAI) {
            showFeedbackNotification('⚠️ Por favor, asegúrate de seleccionar el proyecto "Nexus AI (NA)" para enviar feedback', 'warning');

            if (input) input.value = '';
            if (hiddenInput) hiddenInput.value = '';
            return;
        }

        // Es Nexus AI, proceder
        if (input) input.value = `${projectName} (${projectKey})`;
        if (hiddenInput) hiddenInput.value = projectKey;

        // Validar proyecto
        validateFeedbackProject(projectKey);
    }

    // Validar proyecto
    function validateFeedbackProject(projectKey) {
        const input = document.getElementById('feedback-project-selector-input');

        // Mostrar indicador de validación
        if (input) {
            input.style.opacity = '0.6';
            input.value = input.value + ' ⏳ Validando...';
        }

        fetch('/api/feedback/validate-project', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ project_key: projectKey })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success && data.valid) {
                    selectedFeedbackProjectKey = projectKey;
                    feedbackProjectLocked = true; // Bloquear cambio de proyecto
                    handleFeedbackProjectChange(true);

                    // Deshabilitar el input visualmente
                    if (input) {
                        // Remover el mensaje de validación
                        const projectName = input.value.replace(' ⏳ Validando...', '');
                        input.value = projectName + ' ✓';
                        input.setAttribute('readonly', 'readonly');
                        input.style.opacity = '0.7';
                        input.style.cursor = 'not-allowed';
                    }

                    showDownloadNotification('Proyecto validado correctamente. Ya puedes enviar tu feedback.', 'success');
                } else {
                    showDownloadNotification(data.error || 'Proyecto no válido', 'error');
                    // Resetear selección
                    const hiddenInput = document.getElementById('feedback-project-selector');
                    if (input) {
                        input.value = '';
                        input.style.opacity = '1';
                    }
                    if (hiddenInput) hiddenInput.value = '';
                }
            })
            .catch(error => {
                console.error('Error validando proyecto:', error);
                showDownloadNotification('Error al validar proyecto: ' + error.message, 'error');
                // Resetear en caso de error
                if (input) {
                    input.value = '';
                    input.style.opacity = '1';
                }
            });
    }

    // Manejo de cambio de proyecto
    function handleFeedbackProjectChange(isValid) {
        const feedbackForm = document.getElementById('feedback-form');
        const noProjectMessage = document.getElementById('feedback-no-project-message');

        if (isValid) {
            if (feedbackForm) feedbackForm.classList.remove('disabled');
            if (noProjectMessage) noProjectMessage.style.display = 'none';
        } else {
            if (feedbackForm) feedbackForm.classList.add('disabled');
            if (noProjectMessage) noProjectMessage.style.display = 'block';
        }
    }

    // Selección de tipo de issue
    window.selectFeedbackIssueType = function (type) {
        selectedFeedbackIssueType = type;
        const buttons = document.querySelectorAll('.feedback-issue-type-btn');
        buttons.forEach(btn => btn.classList.remove('active'));

        if (type === 'Bug') {
            buttons[0].classList.add('active');
        } else {
            buttons[1].classList.add('active');
        }
    };

    // Formato de texto
    window.formatFeedbackText = function (command) {
        document.execCommand(command, false, null);
        const editorContent = document.getElementById('feedback-editor-content');
        if (editorContent) editorContent.focus();
    };

    // Insertar enlace
    window.insertFeedbackLink = function () {
        const url = prompt('Ingresa la URL:');
        if (url) {
            document.execCommand('createLink', false, url);
        }
    };

    // Insertar imagen
    window.insertFeedbackImage = function (event) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function (e) {
                const img = document.createElement('img');
                img.src = e.target.result;
                img.style.maxWidth = '100%';
                const editorContent = document.getElementById('feedback-editor-content');
                if (editorContent) {
                    editorContent.appendChild(img);
                }
            };
            reader.readAsDataURL(file);
        }
    };

    // Enviar feedback
    window.submitFeedback = async function () {
        const summary = document.getElementById('feedback-summary');
        const editorContent = document.getElementById('feedback-editor-content');

        if (!summary || !editorContent) return;

        const summaryValue = summary.value.trim();
        const descriptionValue = editorContent.innerHTML.trim();

        if (!summaryValue) {
            showDownloadNotification('Por favor, ingresa un resumen para tu reporte', 'warning');
            return;
        }

        if (!descriptionValue || descriptionValue === '<br>') {
            showDownloadNotification('Por favor, ingresa una descripción para tu reporte', 'warning');
            return;
        }

        // Mostrar indicador de carga
        const feedbackForm = document.getElementById('feedback-form');
        const loadingIndicator = document.getElementById('feedback-loading-indicator');
        if (feedbackForm) feedbackForm.style.display = 'none';
        if (loadingIndicator) loadingIndicator.classList.add('active');

        try {
            const response = await fetch('/api/feedback/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    project_key: selectedFeedbackProjectKey,
                    issue_type: selectedFeedbackIssueType,
                    summary: summaryValue,
                    description: descriptionValue
                })
            });

            const data = await response.json();

            if (loadingIndicator) loadingIndicator.classList.remove('active');

            if (data.success) {
                const successMessage = document.getElementById('feedback-success-message');
                const successText = document.getElementById('feedback-success-text');

                if (successMessage) successMessage.classList.add('active');
                if (successText) {
                    successText.innerHTML = `Tu reporte ha sido creado como <strong>${data.issue_key}</strong>. <a href="${data.issue_url}" target="_blank" style="color: var(--accent); text-decoration: underline;">Ver en Jira</a>`;
                }

                showDownloadNotification(data.message || 'Feedback enviado exitosamente', 'success');
                resetFeedbackForm();

                // Ocultar mensaje de éxito después de 10 segundos
                setTimeout(() => {
                    if (successMessage) successMessage.classList.remove('active');
                    if (feedbackForm) feedbackForm.style.display = 'block';
                }, 10000);
            } else {
                if (feedbackForm) feedbackForm.style.display = 'block';
                showDownloadNotification('Error: ' + (data.error || 'No se pudo enviar el feedback'), 'error');
            }
        } catch (error) {
            if (loadingIndicator) loadingIndicator.classList.remove('active');
            if (feedbackForm) feedbackForm.style.display = 'block';
            showDownloadNotification('Error de conexión: ' + error.message, 'error');
        }
    };

    // Resetear formulario
    window.resetFeedbackForm = function () {
        const summary = document.getElementById('feedback-summary');
        const editorContent = document.getElementById('feedback-editor-content');

        if (summary) summary.value = '';
        if (editorContent) editorContent.innerHTML = '';

        selectFeedbackIssueType('Bug');
    };

    // Public Initialization
    function init() {
        // Inicializar cuando se muestra la sección de feedback
        const feedbackSection = document.getElementById('feedback');
        if (feedbackSection) {
            const observer = new MutationObserver(function (mutations) {
                mutations.forEach(function (mutation) {
                    if (mutation.attributeName === 'class') {
                        if (feedbackSection.classList.contains('active')) {
                            loadFeedbackProjects();

                            // Mostrar mensaje inicial
                            const noProjectMessage = document.getElementById('feedback-no-project-message');
                            if (noProjectMessage) noProjectMessage.style.display = 'block';
                        }
                    }
                });
            });

            observer.observe(feedbackSection, { attributes: true });
        }
    }

    window.NexusModules.Feedback.init = init;

})(window);
