-- Migración para añadir tablas de workflow de aprobación
-- Task: W1.3

CREATE TABLE IF NOT EXISTS approval_workflows (
    id INT AUTO_INCREMENT PRIMARY KEY,
    artifact_type VARCHAR(50) NOT NULL,
    artifact_id INT NOT NULL,
    current_status VARCHAR(50) NOT NULL DEFAULT 'DRAFT',
    requester_id INT NOT NULL,
    reviewer_id INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Restricción única: un artefacto solo tiene un workflow activo
    UNIQUE (artifact_type, artifact_id),
    
    -- Índices para búsquedas frecuentes
    INDEX idx_workflow_requester (requester_id),
    INDEX idx_workflow_reviewer (reviewer_id),
    INDEX idx_workflow_status (current_status),
    
    -- Foreign Keys (asumiendo tabla users existe, si no, remover constraints)
    CONSTRAINT fk_workflow_requester FOREIGN KEY (requester_id) REFERENCES users(id),
    CONSTRAINT fk_workflow_reviewer FOREIGN KEY (reviewer_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS approval_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    workflow_id INT NOT NULL,
    previous_status VARCHAR(50) NOT NULL,
    new_status VARCHAR(50) NOT NULL,
    actor_id INT NOT NULL,
    action VARCHAR(50) NOT NULL,
    comments TEXT,
    detailed_snapshot JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_history_workflow (workflow_id),
    INDEX idx_history_actor (actor_id),
    
    CONSTRAINT fk_history_workflow FOREIGN KEY (workflow_id) REFERENCES approval_workflows(id) ON DELETE CASCADE,
    CONSTRAINT fk_history_actor FOREIGN KEY (actor_id) REFERENCES users(id)
);
