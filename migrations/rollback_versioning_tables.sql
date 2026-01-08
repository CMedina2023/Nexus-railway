-- Rollback para eliminar tablas de versionado
-- Task: V1.3

DROP TABLE IF EXISTS change_logs;
DROP TABLE IF EXISTS artifact_versions;
