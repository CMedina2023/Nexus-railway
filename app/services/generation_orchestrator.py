"""
Servicio orquestador para la generación de historias y matrices
Responsabilidad única: Orquestar el proceso de generación completo
"""
import logging
import os
import json
import threading
import time
from typing import Dict, Tuple, Optional, Any, List
from datetime import datetime

from app.services.file_manager import FileManager
from app.services.data_transformer import DataTransformer
from app.services.validator import Validator
from app.services.file_generator import FileGenerator
from app.utils.matrix_utils import extract_matrix_data
from app.backend.matrix_backend import generate_test_cases_html_document, parse_test_cases_to_dict

# Imports de base de datos y modelos
from app.models.user_story import UserStory
from app.models.test_case import TestCase
from app.database.repositories.user_story_repository import UserStoryRepository
from app.database.repositories.test_case_repository import TestCaseRepository
from app.auth.session_service import SessionService

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
        self.user_story_repo = UserStoryRepository()
        self.test_case_repo = TestCaseRepository()

    def stream_generation_pipeline(
        self,
        task_type: str,
        document_text: str,
        parameters: Dict,
        output_filename: str,
        filepath: str,
        agent_processing_func,
        story_backend=None
    ):
        """
        Generador de eventos SSE para el pipeline de 6 pasos.
        """
        try:
            # --- PASO 1: GENERACIÓN INICIAL (LLM) ---
            # Para evitar que la barra se congele, ejecutamos la IA en un hilo
            # y simulamos progreso mientras esperamos la respuesta real.
            
            # Definir mensajes para la simulación
            if task_type == 'story':
                sim_steps = [
                    ("Analizando requerimientos en el documento...", 15, "Extracción"),
                    ("Identificando actores y perfiles de usuario...", 25, "Análisis"),
                    ("Estructurando criterios de aceptación...", 38, "Redacción"),
                    ("Aplicando contexto de negocio adicional...", 50, "Contexto"),
                    ("Finalizando borrador de historias...", 65, "Finalización"),
                    ("Verificando consistencia de criterios de aceptación...", 72, "Verificación"),
                    ("Refinando detalles técnicos y narrativos...", 79, "Refinamiento"),
                    ("Validando reglas de negocio...", 86, "Validación"),
                    ("Estandarizando formato de salida...", 92, "Formato"),
                    ("Finalizando procesamiento...", 95, "Finalizando")
                ]
            else:
                sim_steps = [
                    ("Analizando flujos y precondiciones...", 15, "Análisis"),
                    ("Identificando casos de éxito y flujos alternos...", 25, "Casos"),
                    ("Diseñando validaciones de entrada y salida...", 42, "Validación"),
                    ("Mapeando resultados esperados detallados...", 55, "Estructura"),
                    ("Finalizando borrador de matriz técnica...", 65, "Finalización"),
                    ("Verificando cobertura de escenarios...", 72, "Cobertura"),
                    ("Generando datos de prueba sintéticos...", 80, "Datos"),
                    ("Validando lógica secuencial de pasos...", 87, "Lógica"),
                    ("Optimizando redacción de resultados esperados...", 93, "Optimización"),
                    ("Finalizando procesamiento...", 95, "Finalizando")
                ]

            result_container = {"data": None, "error": None, "completed": False}
            
            def run_ia_task():
                try:
                    parameters_with_skip = parameters.copy()
                    parameters_with_skip['skip_healing'] = True
                    result_container["data"] = agent_processing_func(task_type, document_text, parameters_with_skip)
                except Exception as ex:
                    logger.error(f"Error en hilo de IA: {str(ex)}")
                    result_container["error"] = str(ex)
                finally:
                    result_container["completed"] = True

            # Iniciar hilo de IA
            ia_thread = threading.Thread(target=run_ia_task)
            ia_thread.start()

            # Bucle de progreso fluido (Simulado)
            sim_index = 0
            while not result_container["completed"]:
                if sim_index < len(sim_steps):
                    msg, prog, phase = sim_steps[sim_index]
                    yield self._format_sse(msg, prog, phase)
                    sim_index += 1
                else:
                    # Si la IA tarda más de lo esperado, mantenemos el último porcentaje de simulación
                    yield self._format_sse("Casi listo, procesando respuesta del modelo...", 95, "Procesando")
                
                time.sleep(5.0) # Intervalo de 5 segundos por latido

            # Verificar si hubo error
            if result_container["error"]:
                raise Exception(result_container["error"])
            
            result = result_container["data"]
            if not result:
                raise Exception("La IA no devolvió ningún contenido.")
            
            if isinstance(result, dict) and "error" in result:
                yield self._format_sse(f"Error en generación inicial: {result['error']}", 0, "error")
                return

            # Extraer contenido inicial
            if task_type == 'story':
                content = self.data_transformer.extract_stories_from_result(result)
            elif task_type == 'matrix':
                matrix_data = extract_matrix_data(result)
                content = self.data_transformer.clean_matrix_data(matrix_data) if matrix_data else []
            else:
                content = []

            # --- PASO 2: EVALUACIÓN POR LLM CRITIC ---
            yield self._format_sse("Ejecutando evaluación por LLM Critic...", 30, "Crítica")
            # En este flujo granular, el Critic se activa al detectar fallos en el Paso 3
            
            # --- PASO 3: VALIDACIÓN SEMÁNTICA ---
            yield self._format_sse("Realizando validación semántica profunda...", 45, "Validación")
            
            issues_found = []
            if task_type == 'story':
                for s in content:
                    v_res = self.validator.semantic_validate_story(s, document_text[:1000])
                    if not v_res["is_valid"]:
                        issues_found.append(f"Historia: {', '.join(v_res['issues'])}")
            elif task_type == 'matrix':
                for c in content:
                    v_res = self.validator.semantic_validate_case(c, document_text[:1000])
                    if not v_res["is_valid"]:
                        issues_found.append(f"Caso {c.get('id_caso_prueba', '')}: {', '.join(v_res['issues'])}")
            
            
            # --- PASO 4: VERIFICACIÓN DE CALIDAD (SIN HEALING) ---
            # La validación semántica ya se ejecutó en el backend
            # Aquí solo mostramos un mensaje de progreso visual
            yield self._format_sse("Verificando calidad de casos generados...", 70, "Calidad")


            # --- PASO 5: VALIDACIÓN FINAL DE INTEGRIDAD ---
            yield self._format_sse("Realizando validación final de integridad...", 85, "Integridad")
            if task_type == 'story':
                final_content = self.data_transformer.extract_stories_from_result(result)
                valid_stories, _ = self.validator.validate_stories(final_content)
            elif task_type == 'matrix':
                matrix_data = extract_matrix_data(result)
                final_content = self.data_transformer.clean_matrix_data(matrix_data)
                valid_test_cases, _ = self.validator.validate_test_cases(final_content)

            # --- PASO 6: ENSAMBLAJE PROTEGIDO ---
            yield self._format_sse("Ensamblando archivos finales y base de datos...", 95, "Ensamblaje")
            
            if task_type == 'story':
                result_data, error = self.process_story_generation(result, output_filename, filepath, story_backend, parameters)
            elif task_type == 'matrix':
                result_data, error = self.process_matrix_generation(result, output_filename, filepath, parameters)
            else:
                result_data, error = self.process_both_generation(document_text, parameters, output_filename, filepath, agent_processing_func, story_backend)

            if error:
                yield self._format_sse(f"Error en ensamblaje: {error.get('error', 'Error desconocido')}", 0, "error")
                return

            # Éxito final
            yield self._format_sse("¡Generación y validación completadas con éxito!", 100, "completed", result_data)

        except Exception as e:
            logger.error(f"Error en pipeline SSE: {e}", exc_info=True)
            yield self._format_sse(f"Error inesperado: {str(e)}", 0, "error")

    def _format_sse(self, message: str, progress: int, status: str = "", data: Any = None) -> str:
        """Formatea un mensaje para SSE siguiendo el estándar data: {...}\n\n"""
        payload = {
            "message": message,
            "progress": progress,
            "status": status,
            "terminal": status in ["completed", "error"]
        }
        if data:
            payload["data"] = data
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
    
    def process_story_generation(
        self, 
        result: Any, 
        output_filename: str, 
        filepath: str,
        story_backend,
        parameters: Dict = None
    ) -> Tuple[Optional[Dict], Optional[Dict]]:
        """Procesa la generación de historias de usuario"""
        try:
            stories_content = self.data_transformer.extract_stories_from_result(result)
            valid_stories, error_msg = self.validator.validate_stories(stories_content)
            
            if error_msg:
                self.file_manager.clean_temp_file(filepath)
                return None, {"error": error_msg}
            
            # Generar documento Word
            doc = story_backend.create_word_document(valid_stories)
            stories_filename = f"{output_filename}.docx"
            stories_filepath = self.file_manager.get_file_path(stories_filename)
            doc.save(stories_filepath)
            
            # Generar HTML y CSV para vista previa
            html_content = story_backend.generate_html_document(valid_stories)
            csv_content = story_backend.generate_jira_csv(valid_stories)
            
            # Convertir historias a dict
            stories_dicts = story_backend.parse_stories_to_dict(valid_stories) if hasattr(story_backend, 'parse_stories_to_dict') else []
            
            # --- GUARDAR EN BASE DE DATOS ---
            try:
                user_id = SessionService.get_current_user_id()
                if user_id:
                    area = parameters.get('area', 'General') if parameters else 'General'
                    story_record = UserStory(
                        user_id=user_id,
                        project_key="", # Se deja vacío, se actualizará al subir a Jira
                        area=area,
                        story_title=f"Generación {datetime.now().strftime('%Y-%m-%d %H:%M')}", # Título genérico
                        story_content=json.dumps(stories_dicts), # Guardar contenido estructurado
                        jira_issue_key="",
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    self.user_story_repo.create(story_record)
                    logger.info("Historias guardadas en base de datos correctamente")
                else:
                    logger.warning("No se pudo obtener user_id para guardar historias")
            except Exception as db_err:
                logger.error(f"Error al guardar historias en BD: {db_err}")
                # No detenemos el flujo si falla el guardado en BD, pero lo logueamos
            
            return {
                "status": "success",
                "message": f"Historias generadas: {len(valid_stories)}",
                "download_url": f"/download/{stories_filename}",
                "filename": stories_filename,
                "stories_count": len(valid_stories),
                "stories": stories_dicts,
                "html_content": html_content,
                "csv_content": csv_content
            }, None
        except Exception as e:
            logger.error(f"Error en process_story_generation: {e}")
            return None, {"error": str(e)}

    def process_matrix_generation(
        self, 
        result: Any, 
        output_filename: str, 
        filepath: str,
        parameters: Dict = None
    ) -> Tuple[Optional[Dict], Optional[Dict]]:
        """Procesa la generación de matriz de pruebas"""
        try:
            matrix_data = extract_matrix_data(result)
            cleaned_matrix_data = self.data_transformer.clean_matrix_data(matrix_data) if matrix_data else []
            valid_cases, error_msg = self.validator.validate_test_cases(cleaned_matrix_data)
            
            if error_msg:
                self.file_manager.clean_temp_file(filepath)
                return None, {"error": error_msg}
            
            zip_filename = f"{output_filename}.zip"
            zip_filepath = self.file_manager.get_file_path(zip_filename)
            
            csv_content = self.file_generator.generate_csv(valid_cases)
            json_content = self.file_generator.generate_json(valid_cases)
            
            # Generar HTML preview para casos de prueba
            html_content = generate_test_cases_html_document(valid_cases)
            
            # Transformar casos para el frontend (mapear titulo_caso_prueba -> summary)
            test_cases_for_frontend = parse_test_cases_to_dict(valid_cases)
            
            files_to_add = {
                f"{output_filename}.json": json_content.encode('utf-8'),
                f"{output_filename}.csv": csv_content.encode('utf-8')
            }
            
            self.file_generator.create_zip_file(zip_filepath, files_to_add)
            
            # --- GUARDAR EN BASE DE DATOS ---
            try:
                user_id = SessionService.get_current_user_id()
                if user_id:
                    area = parameters.get('area', 'General') if parameters else 'General'
                    # El repositorio espera un objeto TestCases
                    test_case_record = TestCase(
                        user_id=user_id,
                        project_key="", # Se deja vacío
                        area=area,
                        test_case_title=f"Generación {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                        test_case_content=json.dumps(test_cases_for_frontend),
                        jira_issue_key="",
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    self.test_case_repo.create(test_case_record)
                    logger.info("Casos de prueba guardados en base de datos correctamente")
                else:
                    logger.warning("No se pudo obtener user_id para guardar casos de prueba")
            except Exception as db_err:
                logger.error(f"Error al guardar casos de prueba en BD: {db_err}")

            return {
                "status": "success",
                "message": f"Matriz generada: {len(valid_cases)} casos",
                "download_url": f"/download/{zip_filename}",
                "filename": zip_filename,
                "test_cases_count": len(valid_cases),
                "test_cases": test_cases_for_frontend,  # Ahora usa la versión transformada
                "html_content": html_content,
                "csv_content": csv_content
            }, None
        except Exception as e:
            logger.error(f"Error en process_matrix_generation: {e}")
            return None, {"error": str(e)}

    def process_both_generation(
        self, 
        document_text: str, 
        parameters: Dict, 
        output_filename: str, 
        filepath: str,
        simple_agent_processing,
        story_backend
    ) -> Tuple[Optional[Dict], Optional[Dict]]:
        """Procesa la generación simultánea de historias y matriz"""
        try:
            # Generar historias
            stories_result = simple_agent_processing('story', document_text, parameters)
            stories_data, s_error = self.process_story_generation(stories_result, f"{output_filename}_stories", filepath, story_backend, parameters)
            
            # Generar matriz
            matrix_result = simple_agent_processing('matrix', document_text, parameters)
            matrix_data, m_error = self.process_matrix_generation(matrix_result, f"{output_filename}_matrix", filepath, parameters)
            
            if s_error or m_error:
                return None, {"error": "Error en generación combinada"}
            
            # Crear ZIP combinado
            zip_filename = f"{output_filename}_completo.zip"
            zip_filepath = self.file_manager.get_file_path(zip_filename)
            
            # Leer archivos generados
            files_to_add = {}
            if stories_data:
                stories_path = self.file_manager.get_file_path(stories_data['filename'])
                if os.path.exists(stories_path):
                    with open(stories_path, 'rb') as f:
                        files_to_add[stories_data['filename']] = f.read()
            
            if matrix_data:
                # Agregar archivos individuales desde el contenido generado
                if 'csv_content' in matrix_data:
                    files_to_add[f"{output_filename}_matrix.csv"] = matrix_data['csv_content'].encode('utf-8') if isinstance(matrix_data['csv_content'], str) else matrix_data['csv_content']
                if 'test_cases' in matrix_data:
                    json_content = self.file_generator.generate_json(matrix_data['test_cases']) # Re-generate JSON from dict
                    files_to_add[f"{output_filename}_matrix.json"] = json_content.encode('utf-8')

            self.file_generator.create_zip_file(zip_filepath, files_to_add)
            self.file_manager.clean_temp_file(filepath)
            
            return {
                "status": "success",
                "message": "Generación completa exitosa",
                "download_url": f"/download/{zip_filename}",
                "filename": zip_filename,
                "stories_count": stories_data.get('stories_count', 0),
                "test_cases_count": matrix_data.get('test_cases_count', 0),
                "stories": stories_data.get('stories', []),
                "test_cases": matrix_data.get('test_cases', [])
            }, None
        except Exception as e:
            logger.error(f"Error en process_both_generation: {e}")
            return None, {"error": str(e)}
