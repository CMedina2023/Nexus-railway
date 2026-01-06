"""
Modelo de Documento del Proyecto
Responsabilidad única: Representar un archivo físico subido a la base de conocimiento del proyecto.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Any
import uuid

@dataclass
class ProjectDocument:
    """
    Representa un documento subido asociado a un proyecto.
    
    Attributes:
        id: UUID único del documento
        project_key: Clave del proyecto asociado
        filename: Nombre original del archivo
        file_path: Ruta física o lógica del archivo
        file_type: Extension o tipo MIME (pdf, md, txt)
        status: Estado del procesamiento ('pending', 'processed', 'error', 'archived')
        content_hash: Hash SHA256 para detectar duplicados
        extracted_summary: Resumen local de este archivo específico
        upload_date: Fecha de subida
        processed_at: Fecha de procesamiento exitoso
        error_message: Mensaje de error si falló el procesamiento
    """
    project_key: str
    filename: str
    file_path: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    file_type: str = "unknown"
    status: str = "pending"
    content_hash: str = ""
    extracted_summary: str = ""
    upload_date: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a diccionario"""
        return {
            'id': self.id,
            'project_key': self.project_key,
            'filename': self.filename,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'status': self.status,
            'content_hash': self.content_hash,
            'extracted_summary': self.extracted_summary,
            'upload_date': self.upload_date.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'error_message': self.error_message
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectDocument':
        """Crea una instancia desde un diccionario"""
        upload_date = datetime.fromisoformat(data['upload_date']) if isinstance(data.get('upload_date'), str) else data.get('upload_date', datetime.now())
        processed_at = datetime.fromisoformat(data['processed_at']) if data.get('processed_at') else None

        return cls(
            id=data.get('id', str(uuid.uuid4())),
            project_key=data.get('project_key', ''),
            filename=data.get('filename', ''),
            file_path=data.get('file_path', ''),
            file_type=data.get('file_type', 'unknown'),
            status=data.get('status', 'pending'),
            content_hash=data.get('content_hash', ''),
            extracted_summary=data.get('extracted_summary', ''),
            upload_date=upload_date,
            processed_at=processed_at,
            error_message=data.get('error_message')
        )
