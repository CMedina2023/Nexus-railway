/**
 * Nexus AI - Admin Panel Module
 * Handles user management, roles, and system configuration.
 */

(function (window) {
    'use strict';

    // Ensure namespace exists
    window.NexusModules = window.NexusModules || {};

    // State
    let adminCurrentUser = null;
    let adminSearchTimeout = null;

    const roleLabels = {
        admin: 'Administrador',
        analista_qa: 'Analista QA',
        usuario: 'Usuario'
    };

    /**
     * Get current user session info
     */
    async function adminGetCurrentUser() {
        try {
            const response = await fetch('/auth/session', {
                headers: { 'Accept': 'application/json' }
            });
            if (response.ok) {
                adminCurrentUser = await response.json();
                return adminCurrentUser;
            }
        } catch (e) {
            console.error('Error al obtener usuario actual:', e);
        }
        return null;
    }

    /**
     * Load users with filters
     */
    async function adminLoadUsers() {
        const loading = document.getElementById('admin-loading');
        const table = document.getElementById('admin-users-table');
        const emptyState = document.getElementById('admin-empty-state');

        if (loading) loading.style.display = 'block';
        if (table) table.style.display = 'none';
        if (emptyState) emptyState.style.display = 'none';

        try {
            const searchInput = document.getElementById('admin-search-input');
            const roleFilter = document.getElementById('admin-role-filter');
            const statusFilter = document.getElementById('admin-status-filter');

            const search = searchInput ? searchInput.value : '';
            const role = roleFilter ? roleFilter.value : '';
            const status = statusFilter ? statusFilter.value : '';

            let url = '/admin/users?';
            if (search) url += `search=${encodeURIComponent(search)}&`;
            if (role) url += `role=${encodeURIComponent(role)}&`;
            if (status === 'active') url += 'active_only=true&';
            if (status === 'inactive') url += 'active_only=false&';

            const response = await fetch(url);
            if (!response.ok) {
                const errorText = await response.text();
                adminShowAlert(`Error HTTP ${response.status}: ${errorText.substring(0, 100)}`, 'error');
                return;
            }

            const data = await response.json();
            if (data.success) {
                adminDisplayUsers(data.users);
                adminUpdateStats(data.statistics);
            } else {
                adminShowAlert(`Error: ${data.error || 'Error desconocido'}`, 'error');
            }
        } catch (e) {
            adminShowAlert(`Error al cargar usuarios: ${e.message}`, 'error');
        } finally {
            if (loading) loading.style.display = 'none';
        }
    }

    /**
     * Render users in table
     */
    function adminDisplayUsers(users) {
        const tbody = document.getElementById('admin-users-tbody');
        const table = document.getElementById('admin-users-table');
        const emptyState = document.getElementById('admin-empty-state');

        if (!tbody || !table || !emptyState) return;

        tbody.innerHTML = '';

        if (!users || users.length === 0) {
            table.style.display = 'none';
            emptyState.style.display = 'block';
            return;
        }

        table.style.display = 'table';
        emptyState.style.display = 'none';

        users.forEach(user => {
            const row = document.createElement('tr');
            const createdDate = user.created_at ? new Date(user.created_at).toLocaleDateString('es-ES') : 'N/A';
            const lastLogin = user.last_login ? new Date(user.last_login).toLocaleDateString('es-ES') : 'Nunca';
            const role = (user.role || 'usuario').toLowerCase();
            const roleLabel = roleLabels[role] || role;

            row.innerHTML = `
                <td>${user.email || 'N/A'}</td>
                <td><span class="admin-badge ${role}">${roleLabel}</span></td>
                <td><span class="admin-badge ${user.active ? 'active' : 'inactive'}">${user.active ? 'Activo' : 'Inactivo'}</span></td>
                <td>${createdDate}</td>
                <td>${lastLogin}</td>
                <td>
                    <div class="admin-actions">
                        <select class="admin-btn admin-btn-sm admin-btn-secondary" onchange="adminChangeRole('${user.id}', this.value)" ${user.id === adminCurrentUser?.user_id ? 'disabled' : ''}>
                            <option value="admin" ${role === 'admin' ? 'selected' : ''}>Administrador</option>
                            <option value="analista_qa" ${role === 'analista_qa' ? 'selected' : ''}>Analista QA</option>
                            <option value="usuario" ${role === 'usuario' ? 'selected' : ''}>Usuario</option>
                        </select>
                        <button class="admin-btn admin-btn-sm ${user.active ? 'admin-btn-danger' : 'admin-btn-primary'}" 
                                onclick="adminToggleStatus('${user.id}', ${!user.active})"
                                ${user.id === adminCurrentUser?.user_id ? 'disabled' : ''}>
                            <i class="fas fa-${user.active ? 'ban' : 'check'}"></i>
                            ${user.active ? 'Desactivar' : 'Activar'}
                        </button>
                    </div>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    function adminUpdateStats(stats) {
        const ids = {
            'admin-stat-total': stats?.total,
            'admin-stat-active': stats?.active,
            'admin-stat-inactive': stats?.inactive,
            'admin-stat-admins': stats?.by_role?.admin
        };
        for (const [id, val] of Object.entries(ids)) {
            const el = document.getElementById(id);
            if (el) el.textContent = val || 0;
        }
    }

    async function adminChangeRole(userId, newRole) {
        if (!confirm(`¿Cambiar rol a ${newRole}?`)) {
            adminLoadUsers();
            return;
        }

        try {
            const response = await fetch(`/admin/users/${userId}/role`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.getCsrfToken()
                },
                body: JSON.stringify({ role: newRole })
            });

            const data = await response.json();
            if (data.success) {
                adminShowAlert(`Rol actualizado a ${newRole}`, 'success');
            } else {
                adminShowAlert(data.error || 'Error al actualizar rol', 'error');
            }
        } catch (e) {
            adminShowAlert('Error al actualizar rol', 'error');
        } finally {
            adminLoadUsers();
        }
    }

    async function adminToggleStatus(userId, newStatus) {
        const action = newStatus ? 'activar' : 'desactivar';
        if (!confirm(`¿${action.charAt(0).toUpperCase() + action.slice(1)} este usuario?`)) return;

        try {
            const response = await fetch(`/admin/users/${userId}/status`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.getCsrfToken()
                },
                body: JSON.stringify({ active: newStatus })
            });

            const data = await response.json();
            if (data.success) {
                adminShowAlert(`Usuario ${action}do exitosamente`, 'success');
            } else {
                adminShowAlert(data.error || 'Error al actualizar estado', 'error');
            }
        } catch (e) {
            adminShowAlert('Error al actualizar estado', 'error');
        } finally {
            adminLoadUsers();
        }
    }

    function adminShowAlert(message, type = 'success') {
        const container = document.getElementById('admin-alert-container');
        if (!container) return;

        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i><span>${message}</span>`;

        container.innerHTML = '';
        container.appendChild(alert);

        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 3000);
    }

    function adminInitPanel() {
        adminGetCurrentUser().then(() => adminLoadUsers());
    }

    // Setup listeners
    document.addEventListener('DOMContentLoaded', () => {
        const searchInput = document.getElementById('admin-search-input');
        const roleFilter = document.getElementById('admin-role-filter');
        const statusFilter = document.getElementById('admin-status-filter');

        if (searchInput) {
            searchInput.addEventListener('input', () => {
                clearTimeout(adminSearchTimeout);
                adminSearchTimeout = setTimeout(adminLoadUsers, 500);
            });
        }
        if (roleFilter) roleFilter.addEventListener('change', adminLoadUsers);
        if (statusFilter) statusFilter.addEventListener('change', adminLoadUsers);
    });

    // Public API
    window.NexusModules.Admin = {
        init: adminInitPanel,
        loadUsers: adminLoadUsers,
        changeRole: adminChangeRole,
        toggleStatus: adminToggleStatus
    };

    // Global Exposure for HTML
    window.adminInitPanel = adminInitPanel;
    window.adminLoadUsers = adminLoadUsers;
    window.adminChangeRole = adminChangeRole;
    window.adminToggleStatus = adminToggleStatus;

})(window);
