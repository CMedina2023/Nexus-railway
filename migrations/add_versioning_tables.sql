-- Migración para añadir tablas de versionado y control de cambios
-- Task: V1.3

-- Tabla para almacenar snapshots históricos de artefactos (Test Cases, User Stories)
CREATE TABLE IF NOT EXISTS artifact_versions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    artifact_type VARCHAR(50) NOT NULL, -- 'TEST_CASE', 'USER_STORY'
    artifact_id INT NOT NULL,
    version_number VARCHAR(20) NOT NULL, -- '1.0', '1.1', '2.0'
    content_snapshot LONGTEXT NOT NULL, -- Snapshot completo (generalmente JSON serializado)
    change_reason TEXT,
    created_by VARCHAR(100) DEFAULT 'SYSTEM', -- Puede ser username, user_id (str) o 'SYSTEM'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    parent_version_id INT,

    -- Índices para búsqueda rápida de historial por artefacto
    INDEX idx_versions_artifact (artifact_type, artifact_id),
    -- Índice para ordenar cronológicamente
    INDEX idx_versions_created (created_at),

    -- Relación recursiva para historial enlazado (Linked List)
    CONSTRAINT fk_version_parent FOREIGN KEY (parent_version_id) REFERENCES artifact_versions(id) ON DELETE SET NULL
);

-- Tabla para auditoría granular de cambios en campos específicos
CREATE TABLE IF NOT EXISTS change_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    artifact_type VARCHAR(50) NOT NULL,
    artifact_id INT NOT NULL,
    version_id INT, -- Opcional, vincula el cambio a una versión específica
    changed_field VARCHAR(100) NOT NULL, -- ej. 'priority', 'status'
    old_value TEXT,
    new_value TEXT,
    changed_by VARCHAR(100) DEFAULT 'SYSTEM',
    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Índices
    INDEX idx_changelog_artifact (artifact_type, artifact_id),
    INDEX idx_changelog_version (version_id),
    INDEX idx_changelog_date (changed_at),

    -- Relación con tabla de versiones
    CONSTRAINT fk_changelog_version FOREIGN KEY (version_id) REFERENCES artifact_versions(id) ON DELETE SET NULL
);
