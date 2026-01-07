-- Rollback para tablas de workflow de aprobación
-- Task: W1.3

DROP TABLE IF EXISTS approval_history;
DROP TABLE IF EXISTS approval_workflows;
