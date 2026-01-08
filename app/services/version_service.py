"""
Servicio de Versionado
Responsabilidad: Lógica de negocio para el ciclo de vida de versiones (creación, incremento, rollback, diff) (SRP)
"""
import logging
import json
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from app.models.artifact_version import ArtifactVersion
from app.models.change_log import ChangeLog
from app.database.repositories.version_repository import VersionRepository

logger = logging.getLogger(__name__)

class VersionService:
    """
    Servicio centralizado para gestionar el versionado de artefactos.
    Implementa la estrategia de Semantic Versioning definida en Nexus Railway.
    """

    def __init__(self):
        self.repository = VersionRepository()

    def create_initial_version(self, artifact_type: str, artifact_id: int, content_snapshot: str, created_by: str, is_draft: bool = True) -> ArtifactVersion:
        """
        Crea la primera versión de un artefacto.
        
        Args:
            artifact_type: 'TEST_CASE' o 'USER_STORY'
            artifact_id: ID del artefacto
            content_snapshot: JSON string del contenido
            created_by: Usuario creador
            is_draft: Si es borrador inicia en v0.1, si es oficial en v1.0
        """
        initial_version_number = "0.1" if is_draft else "1.0"
        
        version = ArtifactVersion(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            version_number=initial_version_number,
            content_snapshot=content_snapshot,
            change_reason="Creación inicial",
            created_by=created_by
        )
        
        return self.repository.create_version(version)

    def create_update_version(self, artifact_type: str, artifact_id: int, content_snapshot: str, created_by: str, change_reason: str, change_type: str = 'MINOR') -> ArtifactVersion:
        """
        Crea una nueva versión basada en cambios sobre la anterior.
        
        Args:
            change_type: 'MAJOR' (cambios estructurales/regeneración) o 'MINOR' (ediciones/cambios estado)
        """
        latest_version = self.repository.get_latest_version(artifact_type, artifact_id)
        
        if not latest_version:
            # Fallback si no existe versión previa (ej. artefactos legacy)
            logger.warning(f"No version found for {artifact_type} {artifact_id}. Creating initial v1.0")
            return self.create_initial_version(artifact_type, artifact_id, content_snapshot, created_by, is_draft=False)

        next_version_number = self._calculate_next_version(latest_version.version_number, change_type)
        
        new_version = ArtifactVersion(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            version_number=next_version_number,
            content_snapshot=content_snapshot,
            change_reason=change_reason,
            created_by=created_by,
            parent_version_id=latest_version.id
        )
        
        saved_version = self.repository.create_version(new_version)
        
        # Detectar cambios granulares para el changelog (best effort)
        self._generate_changelogs(latest_version, saved_version, created_by)
        
        return saved_version

    def rollback_to_version(self, artifact_type: str, artifact_id: int, target_version_number: str, user_id: str) -> ArtifactVersion:
        """
        Realiza un rollback creando una NUEVA versión que copia el contenido de la versión objetivo.
        La historia avanza hacia adelante: v1.5 (rollback a v1.2) -> v1.6 (contenido de v1.2)
        """
        target_version = self.repository.get_version_by_number(artifact_type, artifact_id, target_version_number)
        if not target_version:
            raise ValueError(f"Versión objetivo {target_version_number} no encontrada.")

        # Creamos una nueva versión MAJOR para marcar claramente el rollback
        return self.create_update_version(
            artifact_type=artifact_type,
            artifact_id=artifact_id,
            content_snapshot=target_version.content_snapshot,
            created_by=user_id,
            change_reason=f"Rollback a versión {target_version_number}",
            change_type='MAJOR'
        )

    def get_history(self, artifact_type: str, artifact_id: int) -> List[Dict[str, Any]]:
        """Obtiene historial serializable"""
        versions = self.repository.get_artifact_history(artifact_type, artifact_id)
        return [v.to_dict() for v in versions]

    def get_version_diff(self, artifact_type: str, artifact_id: int, version_a: str, version_b: str) -> Dict[str, Any]:
        """Compara dos versiones y retorna las diferencias estructurales"""
        v1 = self.repository.get_version_by_number(artifact_type, artifact_id, version_a)
        v2 = self.repository.get_version_by_number(artifact_type, artifact_id, version_b)
        
        if not v1 or not v2:
            raise ValueError("Una o ambas versiones no existen")

        return self._compute_json_diff(v1.content_snapshot, v2.content_snapshot)

    # --- Métodos Privados ---

    def _calculate_next_version(self, current_version: str, change_type: str) -> str:
        """Calcula semantic versioning: v1.2 + MINOR -> v1.3"""
        try:
            mayor, minor = map(int, current_version.split('.'))
        except ValueError:
            # Fallback para versiones mal formadas
            return "1.0"

        if change_type == 'MAJOR':
            mayor += 1
            minor = 0
        else: # MINOR
            minor += 1
            
        return f"{mayor}.{minor}"

    def _generate_changelogs(self, old_ver: ArtifactVersion, new_ver: ArtifactVersion, user_id: str):
        """Compara JSONs y genera registros ChangeLog para campos clave"""
        try:
            old_data = json.loads(old_ver.content_snapshot)
            new_data = json.loads(new_ver.content_snapshot)
            
            # Campos clave a monitorear
            monitored_fields = ['priority', 'status', 'approval_status', 'jira_issue_key', 'title', 'test_case_title', 'story_title']
            
            for field in monitored_fields:
                val_old = str(old_data.get(field, ''))
                val_new = str(new_data.get(field, ''))
                
                if val_old != val_new:
                    log = ChangeLog(
                        artifact_id=new_ver.artifact_id,
                        artifact_type=new_ver.artifact_type,
                        version_id=new_ver.id,
                        changed_field=field,
                        old_value=val_old,
                        new_value=val_new,
                        changed_by=user_id
                    )
                    self.repository.log_change(log)
                    
        except json.JSONDecodeError:
            logger.warning("No se pudo parsear snapshot para generar changelogs")

    def _compute_json_diff(self, json_a: str, json_b: str) -> Dict[str, Any]:
        """Calcula diferencial simple entre dos JSONs"""
        try:
            dict_a = json.loads(json_a)
            dict_b = json.loads(json_b)
            
            diff = {
                "added": {},
                "removed": {},
                "changed": {}
            }
            
            all_keys = set(dict_a.keys()) | set(dict_b.keys())
            
            for key in all_keys:
                if key not in dict_a:
                    diff["added"][key] = dict_b[key]
                elif key not in dict_b:
                    diff["removed"][key] = dict_a[key]
                elif dict_a[key] != dict_b[key]:
                    diff["changed"][key] = {"old": dict_a[key], "new": dict_b[key]}
            
            return diff
        except Exception as e:
            return {"error": f"Diff failed: {str(e)}"}
