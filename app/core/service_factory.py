"""
Factory para crear e inicializar servicios
Responsabilidad única: Crear instancias de servicios con sus dependencias
"""
import logging

from app.services.file_manager import FileManager
from app.services.document_analyzer import DocumentAnalyzer
from app.services.data_transformer import DataTransformer
from app.services.text_processor import TextProcessor
from app.services.validator import Validator
from app.services.file_generator import FileGenerator
from app.services.generation_orchestrator import GenerationOrchestrator

logger = logging.getLogger(__name__)


def create_file_manager(upload_folder: str) -> FileManager:
    """Crea una instancia de FileManager"""
    return FileManager(upload_folder)


def create_document_analyzer() -> DocumentAnalyzer:
    """Crea una instancia de DocumentAnalyzer"""
    return DocumentAnalyzer()


def create_data_transformer() -> DataTransformer:
    """Crea una instancia de DataTransformer"""
    return DataTransformer()


def create_validator() -> Validator:
    """Crea una instancia de Validator"""
    return Validator()


def create_file_generator() -> FileGenerator:
    """Crea una instancia de FileGenerator"""
    return FileGenerator()


def create_generation_orchestrator(upload_folder: str) -> GenerationOrchestrator:
    """
    Crea una instancia de GenerationOrchestrator con todas sus dependencias
    
    Args:
        upload_folder: Directorio de uploads
        
    Returns:
        GenerationOrchestrator configurado
    """
    file_manager = create_file_manager(upload_folder)
    data_transformer = create_data_transformer()
    validator = create_validator()
    file_generator = create_file_generator()
    
    return GenerationOrchestrator(
        file_manager=file_manager,
        data_transformer=data_transformer,
        validator=validator,
        file_generator=file_generator
    )

