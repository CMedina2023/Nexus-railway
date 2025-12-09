"""
Servicio orquestador para la generación de historias y matrices
Responsabilidad única: Orquestar el proceso de generación completo
"""
import logging
import os
import zipfile
from typing import Dict, Tuple, Optional, Any

from app.services.file_manager import FileManager
from app.services.data_transformer import DataTransformer
from app.services.validator import Validator
from app.services.file_generator import FileGenerator
from app.utils.matrix_utils import extract_matrix_data

logger = logging.getLogger(__name__)


class GenerationOrchestrator:
    """Orquesta el proceso completo de generación de historias y matrices"""
    
    def __init__(
        self, 
        file_manager: FileManager,
        data_transformer: DataTransformer,
        validator: Validator,
        file_generator: FileGenerator
    ):
        """
        Inicializa el orquestador con sus dependencias
        
        Args:
            file_manager: Servicio para gestión de archivos
            data_transformer: Servicio para transformación de datos
            validator: Servicio para validación
            file_generator: Servicio para generación de archivos
        """
        self.file_manager = file_manager
        self.data_transformer = data_transformer
        self.validator = validator
        self.file_generator = file_generator
    
    def process_story_generation(
        self, 
        result: Any, 
        output_filename: str, 
        filepath: str,
        story_backend
    ) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        Procesa la generación de historias de usuario
        
        Args:
            result: Resultado del agente
            output_filename: Nombre del archivo de salida
            filepath: Ruta del archivo temporal subido
            story_backend: Módulo de backend para historias
            
        Returns:
            Tuple[Optional[Dict], Optional[Dict]]: 
            - (resultado_exitoso, None) si todo está bien
            - (None, error_dict) si hay error
        """
        try:
            # Extraer historias
            logger.debug(f"Contenido de result: {result}")
            stories_content = self.data_transformer.extract_stories_from_result(result)
            logger.info(f"Historias extraídas: {len(stories_content)} elementos")
            
            # Validar historias
            valid_stories, error_msg = self.validator.validate_stories(stories_content)
            if error_msg:
                logger.error(error_msg)
                self.file_manager.clean_temp_file(filepath)
                return None, {
                    "error": "No se pudieron generar historias de usuario. El documento puede ser demasiado grande o no contener información suficiente. Intenta con un documento más pequeño o más detallado."
                }
            
            # Crear documento Word
            doc = story_backend.create_word_document(valid_stories)
            stories_filename = f"{output_filename}.docx"
            stories_filepath = self.file_manager.get_file_path(stories_filename)
            doc.save(stories_filepath)
            
            story_count = len(valid_stories)
            story_word = "historia" if story_count == 1 else "historias"
            
            return {
                "status": "success",
                "message": f"Historias generadas exitosamente: {story_count} {story_word}",
                "download_url": f"/download/{stories_filename}",
                "filename": stories_filename,
                "stories_count": story_count
            }, None
            
        except Exception as e:
            logger.error(f"Error en process_story_generation: {e}", exc_info=True)
            self.file_manager.clean_temp_file(filepath)
            return None, {"error": f"Error al procesar historias: {str(e)}"}
    
    def process_matrix_generation(
        self, 
        result: Any, 
        output_filename: str, 
        filepath: str
    ) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        Procesa la generación de matriz de pruebas
        
        Args:
            result: Resultado del agente
            output_filename: Nombre del archivo de salida
            filepath: Ruta del archivo temporal subido
            
        Returns:
            Tuple[Optional[Dict], Optional[Dict]]: 
            - (resultado_exitoso, None) si todo está bien
            - (None, error_dict) si hay error
        """
        try:
            # Obtener datos de matriz
            logger.debug(f"Contenido de result: {result}")
            matrix_data = extract_matrix_data(result)
            
            if matrix_data:
                logger.debug(f"matrix_data tipo: {type(matrix_data)}, longitud: {len(matrix_data)}")
            
            # Limpiar y validar
            cleaned_matrix_data = self.data_transformer.clean_matrix_data(matrix_data) if matrix_data else []
            logger.info(f"Datos limpios: {len(cleaned_matrix_data)} elementos")
            
            # Validar casos
            valid_cases, error_msg = self.validator.validate_test_cases(cleaned_matrix_data)
            if error_msg:
                logger.error(f"No hay datos válidos: {error_msg}")
                self.file_manager.clean_temp_file(filepath)
                return None, {
                    "error": "No se pudieron generar casos de prueba. El documento puede ser demasiado grande, el procesamiento puede haber sido interrumpido por timeout, o el documento no contiene información suficiente. Intenta con un documento más pequeño o más detallado."
                }
            
            # Crear ZIP
            zip_filename = f"{output_filename}.zip"
            zip_filepath = self.file_manager.get_file_path(zip_filename)
            
            csv_content = self.file_generator.generate_csv(valid_cases)
            json_content = self.file_generator.generate_json(valid_cases)
            
            files_to_add = {
                f"{output_filename}.json": json_content.encode('utf-8'),
                f"{output_filename}.csv": csv_content.encode('utf-8')
            }
            
            self.file_generator.create_zip_file(zip_filepath, files_to_add)
            
            logger.info(f"Archivo ZIP creado con {len(valid_cases)} casos de prueba")
            
            case_count = len(valid_cases)
            case_word = "caso" if case_count == 1 else "casos"
            
            return {
                "status": "success",
                "message": f"Matriz de pruebas generada exitosamente con {case_count} {case_word}",
                "download_url": f"/download/{zip_filename}",
                "filename": zip_filename,
                "test_cases_count": case_count
            }, None
            
        except Exception as e:
            logger.error(f"Error en process_matrix_generation: {e}", exc_info=True)
            self.file_manager.clean_temp_file(filepath)
            return None, {"error": f"Error al procesar matriz: {str(e)}"}
    
    def process_both_generation(
        self, 
        document_text: str, 
        parameters: Dict, 
        output_filename: str, 
        filepath: str,
        simple_agent_processing,
        story_backend
    ) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        Procesa la generación de historias y matriz de pruebas
        
        Args:
            document_text: Texto del documento
            parameters: Parámetros de generación
            output_filename: Nombre del archivo de salida
            filepath: Ruta del archivo temporal subido
            simple_agent_processing: Función para procesar con el agente
            story_backend: Módulo de backend para historias
            
        Returns:
            Tuple[Optional[Dict], Optional[Dict]]: 
            - (resultado_exitoso, None) si todo está bien
            - (None, error_dict) si hay error
        """
        try:
            logger.info("Generando ambos: historias y matriz de pruebas")
            
            # Generar historias
            logger.info("Paso 1: Generando historias de usuario...")
            stories_result = simple_agent_processing('story', document_text, parameters)
            
            if isinstance(stories_result, dict) and "error" in stories_result:
                logger.error(f"Error al generar historias: {stories_result['error']}")
                self.file_manager.clean_temp_file(filepath)
                return None, {"error": f"Error al generar historias: {stories_result['error']}"}
            
            # Validar historias
            stories_content = self.data_transformer.extract_stories_from_result(stories_result)
            logger.info(f"Historias extraídas: {len(stories_content)} elementos")
            
            valid_stories, error_msg = self.validator.validate_stories(stories_content)
            if error_msg:
                logger.error(error_msg)
                self.file_manager.clean_temp_file(filepath)
                return None, {
                    "error": "No se pudieron generar historias de usuario. El documento puede ser demasiado grande o no contener información suficiente."
                }
            
            # Generar matriz
            logger.info("Paso 2: Generando matriz de pruebas...")
            matrix_result = simple_agent_processing('matrix', document_text, parameters)
            
            if isinstance(matrix_result, dict) and "error" in matrix_result:
                logger.error(f"Error al generar matriz: {matrix_result['error']}")
                self.file_manager.clean_temp_file(filepath)
                return None, {"error": f"Error al generar matriz: {matrix_result['error']}"}
            
            # Extraer y validar matriz
            matrix_data = extract_matrix_data(matrix_result)
            cleaned_matrix_data = self.data_transformer.clean_matrix_data(matrix_data) if matrix_data else []
            logger.info(f"Datos de matriz limpios: {len(cleaned_matrix_data)} elementos")
            
            valid_cases, error_msg = self.validator.validate_test_cases(cleaned_matrix_data)
            if error_msg:
                logger.error(error_msg)
                self.file_manager.clean_temp_file(filepath)
                return None, {
                    "error": "No se pudieron generar casos de prueba. El documento puede ser demasiado grande o no contener información suficiente."
                }
            
            # Crear archivos
            logger.info("Paso 3: Creando archivos...")
            
            # Documento Word para historias
            doc = story_backend.create_word_document(valid_stories)
            stories_filename = f"{output_filename}_historias.docx"
            stories_filepath = self.file_manager.get_file_path(stories_filename)
            doc.save(stories_filepath)
            
            # CSV y JSON para matriz
            csv_content = self.file_generator.generate_csv(valid_cases)
            json_content = self.file_generator.generate_json(valid_cases)
            
            # ZIP con ambos archivos
            zip_filename = f"{output_filename}_completo.zip"
            zip_filepath = self.file_manager.get_file_path(zip_filename)
            
            # Leer el archivo de historias en binario
            with open(stories_filepath, 'rb') as f:
                stories_file_content = f.read()
            
            files_to_add = {
                stories_filename: stories_file_content,
                f"{output_filename}_matriz.json": json_content.encode('utf-8'),
                f"{output_filename}_matriz.csv": csv_content.encode('utf-8')
            }
            
            self.file_generator.create_zip_file(zip_filepath, files_to_add)
            
            # Limpiar archivo temporal
            self.file_manager.clean_temp_file(filepath)
            
            story_count = len(valid_stories)
            story_word = "historia" if story_count == 1 else "historias"
            case_count = len(valid_cases)
            case_word = "caso" if case_count == 1 else "casos"
            
            logger.info(f"Proceso completado: {story_count} {story_word} y {case_count} {case_word}")
            
            return {
                "status": "success",
                "message": f"✅ Generación completada: {story_count} {story_word} de usuario y {case_count} {case_word} de prueba",
                "download_url": f"/download/{zip_filename}",
                "filename": zip_filename,
                "stories_count": story_count,
                "test_cases_count": case_count
            }, None
            
        except Exception as e:
            logger.error(f"Error en process_both_generation: {e}", exc_info=True)
            self.file_manager.clean_temp_file(filepath)
            return None, {"error": f"Error al procesar ambos: {str(e)}"}

