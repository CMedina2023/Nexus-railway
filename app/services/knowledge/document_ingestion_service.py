"""
Servicio de Ingesta de Documentos.
Orquesta la subida, validación y procesamiento inicial de documentos para la base
de conocimientos del proyecto.
"""
import logging
import hashlib
import os
from typing import List, Tuple
from datetime import datetime
from werkzeug.utils import secure_filename
from app.models.project_document import ProjectDocument
from app.models.project_context import ProjectContext
from app.services.knowledge.context_merger import ContextMerger
# from app.database.repositories.document_repository import DocumentRepository # Future dependency

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'txt', 'md', 'pdf', 'json', 'csv'}

class DocumentIngestionService:
    """
    Gestiona el ciclo de vida de la ingesta de documentos:
    Upload -> Hash/Dedup -> Persistencia -> Trigger de Fusión.
    """

    def __init__(self, context_merger: ContextMerger = None, upload_folder: str = "uploads/knowledge_base"):
        self.upload_folder = upload_folder
        self.context_merger = context_merger or ContextMerger()
        # self.doc_repo = DocumentRepository()

        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder, exist_ok=True)

    def allowed_file(self, filename: str) -> bool:
        """Verifica si la extensión del archivo es permitida."""
        return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    def ingest_files(self, files, project_key: str) -> Tuple[List[ProjectDocument], List[str]]:
        """
        Procesa una lista de archivos subidos (objetos FileStorage de Flask).
        
        Args:
            files: Lista de archivos subidos
            project_key: Clave del proyecto
            
        Returns:
            Tuple: (Lista de documentos procesados exitosamente, Lista de errores)
        """
        processed_docs = []
        errors = []

        for file in files:
            if file.filename == '':
                continue
                
            if not self.allowed_file(file.filename):
                errors.append(f"Archivo no permitido: {file.filename}")
                continue

            try:
                # 1. Guardar archivo físicamente
                filename = secure_filename(file.filename)
                project_path = os.path.join(self.upload_folder, project_key)
                os.makedirs(project_path, exist_ok=True)
                
                file_path = os.path.join(project_path, filename)
                file.save(file_path)

                # 2. Calcular Hash (Deduplicación simple)
                content_hash = self._calculate_file_hash(file_path)

                # 3. Crear registro ProjectDocument
                # TODO: Verificar en DB si el hash ya existe para este proyecto
                
                doc = ProjectDocument(
                    project_key=project_key,
                    filename=filename,
                    file_path=file_path,
                    file_type=filename.rsplit('.', 1)[1].lower(),
                    content_hash=content_hash,
                    status="processed" # Asumimos procesado por ahora
                )
                
                # TODO: Guardar doc en DB
                # self.doc_repo.save(doc)

                processed_docs.append(doc)
                
            except Exception as e:
                logger.error(f"Error ingiriendo archivo {file.filename}: {e}")
                errors.append(f"Error interno procesando {file.filename}")

        return processed_docs, errors

    def trigger_context_update(self, project_key: str, new_docs: List[ProjectDocument]) -> ProjectContext:
        """
        Inicia el proceso de actualización del ProjectContext con los nuevos documentos.
        Idealmente esto sería una tarea en background (Celery).
        """
        if not new_docs:
            return None

        # TODO: Cargar contexto actual de la DB
        # current_context = self.context_repo.get_by_project(project_key)
        current_context = None # Placeholder

        logger.info(f"Iniciando fusión de contexto para {len(new_docs)} documentos en {project_key}")
        
        updated_context = self.context_merger.merge_documents(new_docs, current_context)
        
        # TODO: Guardar updated_context en DB
        # self.context_repo.save(updated_context)
        
        logger.info(f"Contexto actualizado. Versión: {updated_context.version}")
        return updated_context

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calcula hash SHA256 del archivo."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
