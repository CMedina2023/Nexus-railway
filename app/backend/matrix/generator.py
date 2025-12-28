"""
Módulo de generación para Matrix Backend.
Contiene la lógica core de generación de matrices de prueba usando IA.
"""
import os
import time
import logging
import json
import re
import traceback
import google.generativeai as genai
from typing import List, Dict, Tuple, Optional

from app.core.config import Config
from app.utils.file_utils import extract_text_from_file
from app.utils.retry_utils import call_with_retry
from app.utils.document_chunker import DocumentChunker, ChunkingStrategy
from app.services.validator import Validator

from app.backend.matrix.parser import clean_text, clean_json_response, extract_stories_from_text

logger = logging.getLogger(__name__)

validator = Validator()

# ----------------------------
# Prompts de Calidad
# ----------------------------
HEALING_PROMPT_BATCH = """
Eres un experto en Quality Assurance Senior. Tu tarea es CORREGIR y MEJORAR un grupo de casos de prueba que no cumplen con los estándares de calidad.

ERRORES DETECTADOS POR EL VALIDADOR PARA ESTE LOTE:
{batch_issues}

CASOS A CORREGIR:
{batch_cases}

CONTEXTO DE LA HISTORIA:
{story_context}

TIPOS DE PRUEBA PERMITIDOS EN ESTA SOLICITUD:
{allowed_types}

REGLAS DE ORO PARA LA CORRECCIÓN:
1. VERBOS DE ACCIÓN: Cada paso DEBE iniciar con un verbo de acción (ej: "Hacer clic", "Ingresar", "Seleccionar", "Validar").
2. RESULTADOS PRECISOS: Los resultados esperados NO pueden ser vagos. Describe exactamente qué debe ocurrir en la interfaz o sistema.
3. ESTRUCTURA: Mantén exactamente el mismo formato JSON.
4. INTEGRIDAD: Devuelve TODOS los casos proporcionados, pero en su versión corregida.
5. TIPO DE PRUEBA: NO CAMBIES el campo 'Tipo_de_prueba' de cada caso. Debe permanecer EXACTAMENTE igual al original. Solo se permiten estos tipos: {allowed_types}
6. CAMPOS INMUTABLES: Los siguientes campos NO deben cambiar: 'id_caso_prueba', 'Tipo_de_prueba', 'historia_de_usuario', 'Nivel_de_prueba', 'Tipo_de_ejecucion', 'Ambiente', 'Ciclo', 'issuetype'.

Responde ÚNICAMENTE con un array JSON que contenga los casos corregidos:
"""


# ----------------------------
# Utilidades de lectura
# ----------------------------
def split_document_into_chunks(text, max_chunk_size=None):
    """
    Divide un texto largo en fragmentos más pequeños usando DocumentChunker.
    
    Args:
        text: Texto del documento a dividir
        max_chunk_size: Tamaño máximo del chunk (default: Config.MATRIX_MAX_CHUNK_SIZE)
        
    Returns:
        List[str]: Lista de chunks del documento
    """
    if max_chunk_size is None:
        max_chunk_size = Config.MATRIX_MAX_CHUNK_SIZE
    
    chunker = DocumentChunker(max_chunk_size=max_chunk_size, strategy=ChunkingStrategy.LINEAR)
    return chunker.split_document_into_chunks(text, max_chunk_size)


def generar_matriz_test(contexto, flujo, historia, texto_documento, tipos_prueba=['funcional', 'no_funcional'], skip_healing=False):
    try:
        api_key = Config.GOOGLE_API_KEY
        if not api_key:
            return {"status": "error",
                    "message": "API Key no configurada. Configura GOOGLE_API_KEY en el archivo .env"}

        if not texto_documento or len(texto_documento.strip()) < Config.MIN_DOCUMENT_LENGTH:
            return {"status": "error",
                    "message": "El documento parece estar vacío o es demasiado corto. Verifica que el archivo contenga texto legible."}

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(Config.GEMINI_MODEL)

        # Definir prompt_base
        prompt_base = """
Eres un experto en Testing y Quality Assurance. Tu tarea es analizar requerimientos y generar casos de prueba completos.

RESPUESTA REQUERIDA: Devuelve ÚNICAMENTE un array JSON válido con objetos de casos de prueba. Cada objeto debe tener exactamente estas claves:

{
  "id_caso_prueba": "TC001",
  "titulo_caso_prueba": "Título descriptivo del caso",
  "Descripcion": "Descripción detallada del caso de prueba",
  "Precondiciones": "Requisitos previos para ejecutar la prueba",
  "Tipo_de_prueba": "Funcional" o "No Funcional",
  "Nivel_de_prueba": "UAT",
  "Tipo_de_ejecucion": "Manual",
  "Pasos": ["Paso 1", "Paso 2", "Paso 3"],
  "Resultado_esperado": ["Resultado esperado 1", "Resultado esperado 2"],
  "Categoria": "Categoría según el tipo de prueba",
  "Ambiente": "QA",
  "Ciclo": "Ciclo 1",
  "issuetype": "Test Case",
  "Prioridad": "Alta/Media/Baja",
  "historia_de_usuario": "Referencia a la historia de usuario"
}

CATEGORÍAS VÁLIDAS:
- Funcional: "Flujo Principal", "Flujos Alternativos", "Casos Límite", "Casos de Error"
- No Funcional: "Rendimiento", "Seguridad", "Usabilidad", "Compatibilidad", "Confiabilidad"

REGLAS CRÍTICAS PARA EL TÍTULO (titulo_caso_prueba):
⚠️ El título DEBE ser ESPECÍFICO y DESCRIPTIVO. Describe claramente QUÉ se está probando.
⚠️ NUNCA uses textos genéricos como "Título descriptivo del caso", "Caso de prueba", "Por definir", etc.
⚠️ El título debe tener entre 10 y 100 caracteres y resumir el objetivo del caso.
⚠️ Ejemplos BUENOS: "Validar inicio de sesión con credenciales correctas", "Verificar mensaje de error con email inválido"
⚠️ Ejemplos MALOS: "Caso de prueba 1", "Prueba", "Por definir"

IMPORTANTE: Responde SOLO con el array JSON, sin texto adicional antes o después.
        """

        # Construir prompt específico según tipos seleccionados
        incluir_funcionales = "funcional" in tipos_prueba
        incluir_no_funcionales = "no_funcional" in tipos_prueba

        if incluir_funcionales and incluir_no_funcionales:
            prompt_tipos = """
GENERA CASOS FUNCIONALES Y NO FUNCIONALES:

FUNCIONALES (no tengas un limite de casos generados, siempre y cuando el documento se preste para hacerlo):
- Flujos principales y alternativos
- Validaciones de campos y datos
- Casos límite y condiciones borde
- Manejo de errores y excepciones

NO FUNCIONALES (no tengas un limite de casos generados, siempre y cuando el documento se preste para hacerlo):
- Rendimiento y carga
- Seguridad y autorización
- Usabilidad y experiencia de usuario
- Compatibilidad entre sistemas
- Confiabilidad y disponibilidad
            """
        elif incluir_funcionales:
            prompt_tipos = """
GENERA SOLO CASOS FUNCIONALES (no tengas un limite de casos generados, siempre y cuando el documento se preste para hacerlo):
- Todos los flujos principales
- Flujos alternativos y de excepción
- Validación exhaustiva de datos
- Casos límite y condiciones extremas
- Manejo completo de errores
- Estados del sistema y transiciones
            """
        else:
            prompt_tipos = """
GENERA SOLO CASOS NO FUNCIONALES (no tengas un limite de casos generados, siempre y cuando el documento se preste para hacerlo):
- Rendimiento bajo diferentes cargas
- Seguridad y vectores de ataque
- Usabilidad en diferentes contextos
- Compatibilidad con múltiples entornos
- Confiabilidad y recuperación ante fallos
            """

        # Extraer historias del documento
        historias = extract_stories_from_text(texto_documento)
        logger.debug(f"Historias encontradas: {historias}")

        # Dividir el documento por historias en lugar de solo por tamaño
        chunks = []
        current_chunk = ""
        current_historia = historias[0] if historias else "Historia de usuario general"
        historia_chunks = {current_historia: []}

        paragraphs = texto_documento.split('\n')
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if re.match(r'HISTORIA #\d+:', para):
                if current_chunk.strip():
                    chunks.append((current_historia, current_chunk.strip()))
                    historia_chunks[current_historia].append(current_chunk.strip())
                current_historia = para
                if current_historia not in historia_chunks:
                    historia_chunks[current_historia] = []  # Inicializar la nueva historia
                current_chunk = para + "\n"
            else:
                if len(current_chunk) + len(para) + 1 < (Config.MATRIX_MAX_CHUNK_SIZE * 0.6):  # ~60% del tamaño máximo para chunks internos
                    current_chunk += para + "\n"
                else:
                    chunks.append((current_historia, current_chunk.strip()))
                    historia_chunks[current_historia].append(current_chunk.strip())
                    current_chunk = para + "\n"

        if current_chunk.strip():
            chunks.append((current_historia, current_chunk.strip()))
            historia_chunks[current_historia].append(current_chunk.strip())

        logger.debug(f"Total de chunks generados: {len(chunks)}")
        logger.debug(f"Contenido de historia_chunks: {list(historia_chunks.keys())}")

        all_cases = []
        total_chunks = len(chunks)

        logger.info(f"Procesando {total_chunks} fragmentos del documento...")

        for i, (historia_chunk, chunk) in enumerate(chunks):
            if not chunk.strip():
                logger.warning(f"Fragmento {i + 1}/{total_chunks} está vacío, omitiendo...")
                continue

            logger.info(f"Procesando fragmento {i + 1}/{total_chunks} (Historia: {historia_chunk})")
            
            # Pacing: Obligar a un respiro entre fragmentos para no saturar RPM
            if i > 0:
                logger.info("Esperando 5 segundos para respetar cuota RPM...")
                time.sleep(5)
                
            logger.debug(f"Tamaño del chunk: {len(chunk)} caracteres")
            chunk = clean_text(chunk)
            logger.debug(f"Tamaño del chunk limpio: {len(chunk)} caracteres")

            prompt_completo = f"""{prompt_base}
{prompt_tipos}
CONTEXTO DEL SISTEMA:
{contexto or 'Sistema de software a ser probado'}
FLUJO ESPECÍFICO:
{flujo or 'Flujos generales del sistema'}
HISTORIA DE USUARIO:
{historia_chunk}
FRAGMENTO DEL DOCUMENTO A ANALIZAR ({i + 1}/{total_chunks}):
{chunk}
INSTRUCCIONES:
1. Analiza este fragmento del documento
2. Genera casos de prueba específicos para el contenido encontrado
3. Asegúrate de que cada caso sea único y tenga valor específico
4. Los pasos deben ser claros y ejecutables
5. Los resultados esperados deben ser verificables
6. Usa '{historia_chunk}' como valor para el campo 'historia_de_usuario' en cada caso
Responde ÚNICAMENTE con el array JSON de casos de prueba:"""
            logger.debug(f"Prompt enviado (primeros 500 caracteres): {prompt_completo[:500]}...")

            # Normalizar tipos_prueba ANTES de la función interna para que esté disponible en el scope del healing
            # Convertir "no_funcional" a "no funcional" y viceversa
            tipos_prueba_normalized = []
            for tipo in tipos_prueba:
                tipo_lower = tipo.lower()
                tipos_prueba_normalized.append(tipo_lower)
                # Agregar variante con espacio/guión bajo
                if '_' in tipo_lower:
                    tipos_prueba_normalized.append(tipo_lower.replace('_', ' '))
                else:
                    tipos_prueba_normalized.append(tipo_lower.replace(' ', '_'))
            
            logger.debug(f"Tipos de prueba normalizados: {tipos_prueba_normalized}")

            # Reintentos con backoff exponencial usando función reutilizable
            def generate_matrix_chunk():
                timeout_seconds = Config.GEMINI_TIMEOUT_BASE + (i * Config.GEMINI_TIMEOUT_INCREMENT)
                response = model.generate_content(prompt_completo, request_options={"timeout": timeout_seconds})
                
                if not response or not hasattr(response, 'text') or not response.text:
                    raise ValueError("Respuesta vacía o inválida del modelo")
                
                logger.debug(f"Respuesta del modelo (primeros 500 caracteres): {response.text[:500]}...")
                cases_chunk = clean_json_response(response.text)
                
                if not cases_chunk or not isinstance(cases_chunk, list) or len(cases_chunk) == 0:
                    raise ValueError("No se pudo procesar JSON o la respuesta está vacía")
                
                # Filtrar por tipo de prueba con normalización
                logger.debug(f"Casos generados antes del filtrado: {len(cases_chunk)}")
                if cases_chunk:
                    for case in cases_chunk[:3]:  # Mostrar los primeros 3
                        logger.debug(f"  - Tipo: '{case.get('Tipo_de_prueba', 'N/A')}' | Título: {case.get('titulo_caso_prueba', 'N/A')[:50]}")
                
                cases_chunk = [
                    case for case in cases_chunk
                    if case.get('Tipo_de_prueba', '').lower() in tipos_prueba_normalized
                ]
                
                logger.debug(f"Casos después del filtrado: {len(cases_chunk)}")
                
                if len(cases_chunk) == 0:
                    raise ValueError("No se generaron casos válidos después del filtrado")
                
                # Normalizar casos
                for j, case in enumerate(cases_chunk):
                    if not case.get('id_caso_prueba'):
                        case['id_caso_prueba'] = f"TC{len(all_cases) + j + 1:03d}"
                    case['historia_de_usuario'] = historia_chunk
                    
                    # Manejar cada campo con lógica específica
                    # TÍTULO: Generar un título significativo basado en descripción o tipo
                    titulo = case.get('titulo_caso_prueba', '')
                    if not titulo or titulo.strip() == '' or 'por definir' in titulo.lower() or 'título descriptivo' in titulo.lower():
                        # Intentar generar título desde descripción
                        descripcion = case.get('Descripcion', '')
                        if descripcion and descripcion.strip() and 'por definir' not in descripcion.lower():
                            # Usar primeros 60 caracteres de la descripción como título
                            titulo = descripcion[:60].strip()
                            if len(descripcion) > 60:
                                titulo += '...'
                        else:
                            # Generar título basado en tipo de prueba y categoría
                            tipo_prueba = case.get('Tipo_de_prueba', 'Funcional')
                            categoria = case.get('Categoria', '')
                            if categoria:
                                titulo = f"Validar {categoria} - {tipo_prueba}"
                            else:
                                titulo = f"Caso de prueba {tipo_prueba} - {case['id_caso_prueba']}"
                        case['titulo_caso_prueba'] = titulo
                    
                    # OTROS CAMPOS: Usar placeholders solo si es necesario
                    if not case.get('Descripcion') or not case['Descripcion']:
                        case['Descripcion'] = f"Verificar funcionalidad según requerimientos"
                    if not case.get('Precondiciones') or not case['Precondiciones']:
                        case['Precondiciones'] = "Sistema configurado y usuario autenticado"
                    if not case.get('Tipo_de_prueba') or not case['Tipo_de_prueba']:
                        case['Tipo_de_prueba'] = "Funcional"
                    
                    # PASOS Y RESULTADOS: Asegurar formato de lista
                    if not isinstance(case.get('Pasos'), list):
                        pasos = case.get('Pasos', '')
                        if pasos:
                            case['Pasos'] = [str(pasos)]
                        else:
                            case['Pasos'] = ["Ejecutar la funcionalidad especificada"]
                    if not isinstance(case.get('Resultado_esperado'), list):
                        resultado = case.get('Resultado_esperado', '')
                        if resultado:
                            case['Resultado_esperado'] = [str(resultado)]
                        else:
                            case['Resultado_esperado'] = ["El sistema responde correctamente según especificación"]
                
                return cases_chunk
            
            try:
                cases_chunk = call_with_retry(
                    generate_matrix_chunk,
                    max_retries=Config.MAX_RETRIES,
                    retry_delay=Config.RETRY_DELAY,
                    timeout_base=Config.GEMINI_TIMEOUT_BASE,
                    timeout_increment=Config.GEMINI_TIMEOUT_INCREMENT,
                    exceptions=(Exception,)
                )
                all_cases.extend(cases_chunk)
                logger.info(f"Fragmento {i + 1}: {len(cases_chunk)} casos generados")
                
                # --- VALIDACIÓN SEMÁNTICA (SIEMPRE ACTIVA) ---
                logger.info(f"Iniciando validación semántica para {len(cases_chunk)} casos del fragmento {i+1}...")
                failed_indices = []
                issues_list = []
                
                for idx_case, case in enumerate(cases_chunk):
                    validation_result = validator.semantic_validate_case(case, chunk)
                    if not validation_result["is_valid"]:
                        failed_indices.append(idx_case)
                        issues_list.append(f"Caso {idx_case + 1}: {', '.join(validation_result['issues'])}")
                
                if failed_indices:
                    logger.warning(f"  ⚠️ {len(failed_indices)} casos tienen problemas semánticos detectados.")
                    
                    # --- SELF-HEALING (SOLO SI NO ESTÁ DESACTIVADO) ---
                    if not skip_healing:
                        # Pacing: Respiro antes de sanación
                        logger.info("Esperando 5 segundos antes de proceso de sanación...")
                        time.sleep(5)
                        
                        logger.warning(f"  🔧 Iniciando curación en bloque para {len(failed_indices)} casos...")
                        try:
                            cases_to_heal = [cases_chunk[idx] for idx in failed_indices]
                            
                            # Preparar tipos permitidos para el prompt
                            tipos_permitidos_str = ", ".join([
                                "Funcional" if "funcional" in t.lower() and "no" not in t.lower() 
                                else "No Funcional" if "no" in t.lower() and "funcional" in t.lower()
                                else t.capitalize()
                                for t in tipos_prueba
                            ])
                            
                            logger.info(f"  🔧 Tipos de prueba permitidos para healing: {tipos_permitidos_str}")
                            
                            prompt_healing = HEALING_PROMPT_BATCH.format(
                                batch_issues="\\\\n".join(issues_list),
                                batch_cases=json.dumps(cases_to_heal, indent=2, ensure_ascii=False),
                                story_context=chunk,
                                allowed_types=tipos_permitidos_str
                            )
                            
                            def heal_batch_op():
                                response = model.generate_content(prompt_healing)
                                if not response or not response.text:
                                    return None
                                return clean_json_response(response.text)

                            healed_cases_list = call_with_retry(heal_batch_op, max_retries=2)
                            
                            if healed_cases_list and isinstance(healed_cases_list, list):
                                # Reemplazar los casos fallidos con los sanados
                                # El modelo debería devolver la misma cantidad de casos
                                for j, original_idx in enumerate(failed_indices):
                                    if j < len(healed_cases_list):
                                        healed_case = healed_cases_list[j]
                                        original_case = cases_chunk[original_idx]
                                        
                                        # VALIDACIÓN POST-HEALING: Forzar que campos inmutables se mantengan
                                        immutable_fields = [
                                            'id_caso_prueba', 'Tipo_de_prueba', 'historia_de_usuario',
                                            'Nivel_de_prueba', 'Tipo_de_ejecucion', 'Ambiente', 'Ciclo', 'issuetype'
                                        ]
                                        
                                        for field in immutable_fields:
                                            if field in original_case:
                                                healed_case[field] = original_case[field]
                                        
                                        # Validar que el tipo de prueba esté en los tipos permitidos
                                        tipo_healed = healed_case.get('Tipo_de_prueba', '').lower()
                                        if tipo_healed not in tipos_prueba_normalized:
                                            logger.warning(f"  ⚠️ Caso sanado tiene tipo '{healed_case.get('Tipo_de_prueba')}' no permitido. Restaurando tipo original.")
                                            healed_case['Tipo_de_prueba'] = original_case.get('Tipo_de_prueba', 'Funcional')
                                        
                                        cases_chunk[original_idx] = healed_case
                                logger.info(f"  ✅ Curación en bloque completada para {len(healed_cases_list)} casos.")
                        except Exception as e:
                            logger.error(f"  ❌ Error en curación en bloque (batch healing): {e}")
                    else:
                        logger.info(f"  ℹ️ Self-healing desactivado. Los casos se mantendrán con sus problemas detectados.")
                else:
                    logger.info(f"  ✅ Todos los casos pasaron la validación semántica.")
                # --- FIN VALIDACIÓN SEMÁNTICA Y HEALING ---
                
            except Exception as e:
                logger.error(f"Fragmento {i + 1} falló después de {Config.MAX_RETRIES} intentos: {e}")
                # Continuar con el siguiente fragmento

        if not all_cases:
            return {
                "status": "error",
                "message": "No se pudieron generar casos de prueba. Verifica que el documento contenga información clara sobre requerimientos o funcionalidades."
            }

        # --- ELIMINACIÓN DE DUPLICADOS ---
        logger.info(f"Buscando casos duplicados entre {len(all_cases)} casos...")
        duplicate_indices = validator.find_duplicates([
            f"{c.get('titulo_caso_prueba', '')} {c.get('Descripcion', '')} {c.get('Pasos', '')}" 
            for c in all_cases
        ])
        
        if duplicate_indices:
            all_cases = [c for idx, c in enumerate(all_cases) if idx not in duplicate_indices]
            logger.info(f"Se eliminaron {len(duplicate_indices)} casos duplicados/similares.")
        # --- FIN ELIMINACIÓN DE DUPLICADOS ---

        # Reasignar todos los IDs secuencialmente para evitar saltos
        # Esto corrige cualquier problema de IDs causado por filtrado o generación del modelo
        for idx, case in enumerate(all_cases, start=1):
            case['id_caso_prueba'] = f"TC{idx:03d}"
        
        logger.info(f"IDs reasignados secuencialmente: {len(all_cases)} casos con IDs TC001-TC{len(all_cases):03d}")

        funcional_count = sum(1 for case in all_cases if case.get('Tipo_de_prueba', '').lower() == 'funcional')
        no_funcional_count = len(all_cases) - funcional_count

        return {
            "status": "success",
            "matrix": all_cases,
            "total_cases": len(all_cases),
            "funcional_cases": funcional_count,
            "no_funcional_cases": no_funcional_count
        }
    except Exception as e:
        error_message = str(e).lower()
        logger.error(f"Error general: {str(e)}")
        logger.error(f"Tipo de excepción: {type(e).__name__}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        if "blocked" in error_message or "safety" in error_message:
            return {
                "status": "error",
                "message": "La solicitud fue bloqueada por filtros de seguridad. Intenta con un documento diferente."
            }
        else:
            return {
                "status": "error",
                "message": f"Error en la lógica de procesamiento: {str(e)}"
            }

def test_matrix_generation():
    """
    Función de prueba para verificar la generación de matrices.
    """
    # Texto de prueba
    texto_prueba = """
    Requerimiento: Sistema de Login de Usuario

    El sistema debe permitir a los usuarios autenticarse usando email y contraseña.

    Funcionalidades:
    1. Campo de email con validación de formato
    2. Campo de contraseña con mínimo 8 caracteres
    3. Botón de "Iniciar Sesión"
    4. Opción "Recordar usuario"
    5. Link "Olvidé mi contraseña"
    6. Mensaje de error para credenciales inválidas
    7. Redirección al dashboard después del login exitoso

    Reglas de negocio:
    - Después de 3 intentos fallidos, bloquear la cuenta por 15 minutos
    - La sesión debe expirar después de 2 horas de inactividad
    - Debe registrar todos los intentos de login en el log de auditoría
    """

    logger.info("Ejecutando prueba de generación de matriz...")

    result = generar_matriz_test(
        contexto="Sistema web de gestión de usuarios",
        flujo="Login de usuario con email y contraseña",
        historia="Como usuario quiero poder iniciar sesión de forma segura",
        texto_documento=texto_prueba,
        tipos_prueba=['funcional', 'no_funcional']
    )

    logger.info(f"Resultado: {result['status']}")
    if result['status'] == 'success':
        logger.info(f"Casos generados: {len(result['matrix'])}")
        for i, case in enumerate(result['matrix'][:3]):  # Mostrar solo los primeros 3
            logger.debug(f"\nCaso {i + 1}:")
            logger.debug(f"  ID: {case.get('id_caso_prueba', 'N/A')}")
            logger.debug(f"  Título: {case.get('titulo_caso_prueba', 'N/A')}")
            logger.debug(f"  Tipo: {case.get('Tipo_de_prueba', 'N/A')}")
    else:
        logger.error(f"Error: {result['message']}")
