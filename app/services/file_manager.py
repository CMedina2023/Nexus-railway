"""
Servicio para gestión de archivos temporales y subidos
Responsabilidad única: Gestión de archivos del sistema
"""
import os
import logging
from typing import Optional
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

logger = logging.getLogger(__name__)


class FileManager:
    """Maneja operaciones de archivos temporales y subidos"""
    
    def __init__(self, upload_folder: str):
        """
        Inicializa el FileManager
        
        Args:
            upload_folder: Directorio donde se guardarán los archivos subidos
        """
        self.upload_folder = upload_folder
        self._ensure_upload_folder_exists()
    
    def _ensure_upload_folder_exists(self):
        """Asegura que el directorio de uploads existe"""
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)
            logger.info(f"Directorio de uploads creado: {self.upload_folder}")
    
    def save_uploaded_file(self, file: FileStorage, filename: Optional[str] = None) -> str:
        """
        Guarda un archivo subido en el directorio de uploads
        
        Args:
            file: Archivo subido a través de Flask request
            filename: Nombre opcional para el archivo. Si no se proporciona, usa secure_filename
            
        Returns:
            str: Ruta completa del archivo guardado
        """
        if filename is None:
            filename = secure_filename(file.filename)
        
        filepath = os.path.join(self.upload_folder, filename)
        file.save(filepath)
        logger.info(f"Archivo guardado: {filepath}")
        
        return filepath
    
    def clean_temp_file(self, filepath: Optional[str]) -> None:
        """
        Limpia archivos temporales de forma segura
        
        Args:
            filepath: Ruta del archivo a eliminar
        """
        if not filepath:
            return
        
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Archivo temporal eliminado: {filepath}")
        except Exception as e:
            logger.warning(f"No se pudo eliminar archivo temporal {filepath}: {e}")
    
    def file_exists(self, filename: str) -> bool:
        """
        Verifica si un archivo existe en el directorio de uploads
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            bool: True si el archivo existe, False en caso contrario
        """
        filepath = os.path.join(self.upload_folder, filename)
        return os.path.exists(filepath)
    
    def get_file_path(self, filename: str) -> str:
        """
        Obtiene la ruta completa de un archivo
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            str: Ruta completa del archivo
        """
        return os.path.join(self.upload_folder, filename)

