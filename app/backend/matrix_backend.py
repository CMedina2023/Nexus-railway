import os
import google.generativeai as genai
import csv
import json
import re
import io
import zipfile
import logging
import traceback
from datetime import datetime
from typing import List, Dict

from app.utils.file_utils import extract_text_from_file
from app.core.config import Config
from app.utils.retry_utils import call_with_retry
from app.utils.document_chunker import DocumentChunker, ChunkingStrategy

logger = logging.getLogger(__name__)


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

def clean_json_response(response_text):
    """Limpia y extrae JSON de la respuesta del modelo."""
    if not response_text:
        return None
    try:
        data = json.loads(response_text)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'matrix' in data:
            return data['matrix']
        elif isinstance(data, dict) and 'test_cases' in data:
            return data['test_cases']
    except json.JSONDecodeError:
        pass
    json_patterns = [
        r'```json\s*\n([\s\S]*?)\n```',
        r'```\s*\n([\s\S]*?)\n```',
        r'\[[\s\S]*\]'
    ]
    for pattern in json_patterns:
        match = re.search(pattern, response_text, re.MULTILINE)
        if match:
            json_str = match.group(1).strip()
            try:
                data = json.loads(json_str)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and 'matrix' in data:
                    return data['matrix']
            except json.JSONDecodeError:
                continue
    try:
        start = response_text.find('[')
        end = response_text.rfind(']')
        if start != -1 and end != -1 and end > start:
            json_str = response_text[start:end + 1]
            data = json.loads(json_str)
            if isinstance(data, list):
                return data
    except json.JSONDecodeError:
        pass
    return None

def clean_text(text):
    """Limpia el texto eliminando caracteres problemáticos."""
    text = re.sub(r'[^\x20-\x7E\n]', '', text)
    return text.strip()

def extract_stories_from_text(text):
    """Extrae nombres de historias de usuario del texto del documento."""
    pattern = r'HISTORIA #\d+:[^\n]+'
    matches = re.findall(pattern, text, re.MULTILINE)
    return matches if matches else ['Historia de usuario general']

def generar_matriz_test(contexto, flujo, historia, texto_documento, tipos_prueba=['funcional', 'no_funcional']):
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
  "issuetype": "tests Case",
  "Prioridad": "Alta/Media/Baja",
  "historia_de_usuario": "Referencia a la historia de usuario"
}

CATEGORÍAS VÁLIDAS:
- Funcional: "Flujo Principal", "Flujos Alternativos", "Casos Límite", "Casos de Error"
- No Funcional: "Rendimiento", "Seguridad", "Usabilidad", "Compatibilidad", "Confiabilidad"

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
                # Normalizar tipos_prueba: convertir "no_funcional" a "no funcional" y viceversa
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
                    for field in ['titulo_caso_prueba', 'Descripcion', 'Precondiciones', 'Tipo_de_prueba', 'Pasos', 'Resultado_esperado']:
                        if field not in case or not case[field]:
                            case[field] = f"Campo {field} por definir"
                    if not isinstance(case.get('Pasos'), list):
                        case['Pasos'] = [str(case.get('Pasos', 'Paso por definir'))]
                    if not isinstance(case.get('Resultado_esperado'), list):
                        case['Resultado_esperado'] = [str(case.get('Resultado_esperado', 'Resultado por definir'))]
                
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
                logger.info(f"Fragmento {i + 1}: {len(cases_chunk)} casos generados y agregados")
            except Exception as e:
                logger.error(f"Fragmento {i + 1} falló después de {Config.MAX_RETRIES} intentos: {e}")
                # Continuar con el siguiente fragmento

        if not all_cases:
            return {
                "status": "error",
                "message": "No se pudieron generar casos de prueba. Verifica que el documento contenga información clara sobre requerimientos o funcionalidades."
            }

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
        import traceback
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


def save_to_csv_buffer(data):
    """Guarda los datos de la matriz en un buffer de memoria como CSV."""
    if not data:
        return b""

    # Campos en el orden deseado
    fieldnames = [
        "id_caso_prueba",
        "titulo_caso_prueba",
        "Descripcion",
        "Precondiciones",
        "Tipo_de_prueba",
        "Nivel_de_prueba",
        "Tipo_de_ejecucion",
        "Pasos",
        "Resultado_esperado",
        "Categoria",
        "Ambiente",
        "Ciclo",
        "issuetype",
        "Prioridad",
        "historia_de_usuario"
    ]

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for row in data:
        # Crear una copia del row para no modificar el original
        csv_row = {}

        for field in fieldnames:
            value = row.get(field, '')

            # Convertir listas a string separado por " | "
            if field in ['Pasos', 'Resultado_esperado'] and isinstance(value, list):
                csv_row[field] = " | ".join(str(item) for item in value if item)
            elif isinstance(value, list):
                csv_row[field] = ", ".join(str(item) for item in value if item)
            else:
                csv_row[field] = str(value) if value else ''

        writer.writerow(csv_row)

    return output.getvalue().encode('utf-8')


def save_to_json_buffer(data):
    """Guarda los datos de la matriz en un buffer de memoria como JSON."""
    if not data:
        return b"[]"

    output = io.StringIO()
    json.dump(data, output, indent=4, ensure_ascii=False)
    return output.getvalue().encode('utf-8')


def create_zip_with_matrix(data, output_filename):
    """
    Crea un archivo ZIP con la matriz en formato CSV y JSON.
    """
    if not data:
        return None

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Agregar archivo CSV
        csv_data = save_to_csv_buffer(data)
        zip_file.writestr(f"{output_filename}_matriz.csv", csv_data)

        # Agregar archivo JSON
        json_data = save_to_json_buffer(data)
        zip_file.writestr(f"{output_filename}_matriz.json", json_data)

        # Agregar archivo README con información
        readme_content = f"""MATRIZ DE PRUEBAS GENERADA
============================

Archivo generado automáticamente por Matrix Generator
Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

CONTENIDO DEL ZIP:
- {output_filename}_matriz.csv: Matriz de pruebas en formato CSV
- {output_filename}_matriz.json: Matriz de pruebas en formato JSON
- README.txt: Este archivo

ESTADÍSTICAS:
- Total de casos de prueba: {len(data)}
- Casos funcionales: {sum(1 for case in data if case.get('Tipo_de_prueba', '').lower() == 'funcional')}
- Casos no funcionales: {len(data) - sum(1 for case in data if case.get('Tipo_de_prueba', '').lower() == 'funcional')}

ESTRUCTURA DE CAMPOS CSV:
- id_caso_prueba: Identificador único del caso
- titulo_caso_prueba: Título descriptivo
- Descripcion: Descripción detallada del caso
- Precondiciones: Requisitos previos
- Tipo_de_prueba: Funcional o No Funcional
- Nivel_de_prueba: Nivel de testing (UAT)
- Tipo_de_ejecucion: Manual o Automático
- Pasos: Pasos a seguir (separados por " | ")
- Resultado_esperado: Resultados esperados (separados por " | ")
- Categoria: Categoría específica del tipo de prueba
- Ambiente: Ambiente de pruebas (QA)
- Ciclo: Ciclo de testing
- issuetype: Tipo de issue (tests Case)
- Prioridad: Alta, Media o Baja
- historia_de_usuario: Referencia a la historia

INSTRUCCIONES DE USO:
1. Importa el archivo CSV en tu herramienta de gestión de casos de prueba
2. Utiliza el archivo JSON para integraciones con APIs
3. Revisa y ajusta los casos según tus necesidades específicas
"""
        zip_file.writestr("README.txt", readme_content.encode('utf-8'))

    zip_buffer.seek(0)
    return zip_buffer.getvalue()


def process_matrix_request(file_path, contexto="", flujo="", historia="", tipos_prueba=['funcional', 'no_funcional'],
                           output_filename="matriz_pruebas"):
    """
    Función principal que procesa una solicitud completa de generación de matriz.

    Args:
        file_path (str): Ruta al archivo de requerimientos
        contexto (str): Contexto del sistema
        flujo (str): Flujo específico a probar
        historia (str): Historia de usuario
        tipos_prueba (list): Tipos de pruebas a generar
        output_filename (str): Nombre base para archivos de salida

    Returns:
        dict: Resultado de la operación
    """
    try:
        # Extraer texto del documento
        logger.info(f"Extrayendo texto del archivo: {file_path}")
        texto_documento = extract_text_from_file(file_path)

        if not texto_documento or len(texto_documento.strip()) < Config.MIN_DOCUMENT_LENGTH:
            return {
                "status": "error",
                "message": "No se pudo extraer texto del documento o el contenido es insuficiente."
            }

        logger.info(f"Texto extraído: {len(texto_documento)} caracteres")

        # Generar matriz de pruebas
        logger.info("Generando matriz de pruebas...")
        result = generar_matriz_test(contexto, flujo, historia, texto_documento, tipos_prueba)

        if result["status"] != "success":
            return result

        # Crear archivo ZIP
        logger.info("Creando archivo ZIP...")
        zip_data = create_zip_with_matrix(result["matrix"], output_filename)

        if not zip_data:
            return {
                "status": "error",
                "message": "Error al crear el archivo ZIP."
            }

        return {
            "status": "success",
            "message": "Matriz generada exitosamente",
            "zip_data": zip_data,
            "stats": {
                "total_cases": result.get("total_cases", 0),
                "funcional_cases": result.get("funcional_cases", 0),
                "no_funcional_cases": result.get("no_funcional_cases", 0)
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error procesando la solicitud: {str(e)}"
        }

def extract_stories_from_text(text):
    """Extrae nombres de historias de usuario del texto del documento."""
    pattern = r'HISTORIA #\d+:[^\n]+'
    matches = re.findall(pattern, text, re.MULTILINE)
    return matches if matches else ['Historia de usuario general']


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


def parse_test_case_data(test_case: dict) -> dict:
    """
    Parsea un caso de prueba y extrae los datos necesarios para CSV de Jira.
    
    Args:
        test_case: Diccionario con datos del caso de prueba
        
    Returns:
        dict: Diccionario con summary, description, priority, y otros campos
    """
    # Extraer summary (título) - mejorar manejo de valores por defecto
    summary = test_case.get('titulo_caso_prueba', '')
    
    # Si está vacío o es el valor por defecto, usar ID o descripción
    if not summary or summary.strip() == '' or 'por definir' in summary.lower():
        # Intentar usar ID del caso
        case_id = test_case.get('id_caso_prueba', '')
        if case_id:
            summary = f"Caso de prueba {case_id}"
        else:
            # Intentar usar descripción como fallback
            descripcion = test_case.get('Descripcion', '')
            if descripcion and descripcion.strip() and 'por definir' not in descripcion.lower():
                # Usar primeros 50 caracteres de la descripción
                summary = descripcion[:50].strip()
                if len(descripcion) > 50:
                    summary += '...'
            else:
                summary = 'Caso de prueba sin título'
    
    # Limpiar el summary de caracteres problemáticos
    summary = summary.strip()
    
    # Log para depuración si el summary sigue siendo problemático
    if not summary or len(summary) < 3:
        logger.warning(f"Summary muy corto o vacío para caso {test_case.get('id_caso_prueba', 'N/A')}: '{summary}'")
        summary = f"Caso de prueba {test_case.get('id_caso_prueba', 'TC')}"
    
    # Construir descripción completa
    description_parts = []
    
    # Descripción
    descripcion = test_case.get('Descripcion', '')
    if descripcion:
        description_parts.append(f"* Descripción: {descripcion}")
    
    # Precondiciones
    precondiciones = test_case.get('Precondiciones', '')
    if precondiciones:
        description_parts.append(f"* Precondiciones: {precondiciones}")
    
    # Pasos
    pasos = test_case.get('Pasos', [])
    if pasos:
        if isinstance(pasos, str):
            pasos = [pasos]
        pasos_text = '\n'.join([f"  {i+1}. {paso}" for i, paso in enumerate(pasos) if paso])
        if pasos_text:
            description_parts.append(f"* Pasos:\n{pasos_text}")
    
    # Resultado esperado
    resultado_esperado = test_case.get('Resultado_esperado', [])
    if resultado_esperado:
        if isinstance(resultado_esperado, str):
            resultado_esperado = [resultado_esperado]
        resultado_text = '\n'.join([f"  • {res}" for res in resultado_esperado if res])
        if resultado_text:
            description_parts.append(f"* Resultado Esperado:\n{resultado_text}")
    
    # Tipo de prueba
    tipo_prueba = test_case.get('Tipo_de_prueba', 'Funcional')
    if tipo_prueba:
        description_parts.append(f"* Tipo de Prueba: {tipo_prueba}")
    
    # Categoría
    categoria = test_case.get('Categoria', '')
    if categoria:
        description_parts.append(f"* Categoría: {categoria}")
    
    # Historia de usuario (si existe)
    historia = test_case.get('historia_de_usuario', '')
    if historia:
        description_parts.append(f"* Historia de Usuario: {historia}")
    
    description = '\n'.join(description_parts)
    
    # Prioridad
    prioridad = test_case.get('Prioridad', 'Medium')
    if isinstance(prioridad, str):
        prioridad_lower = prioridad.lower()
        if 'alta' in prioridad_lower or 'high' in prioridad_lower:
            priority = 'High'
        elif 'media' in prioridad_lower or 'medium' in prioridad_lower:
            priority = 'Medium'
        elif 'baja' in prioridad_lower or 'low' in prioridad_lower:
            priority = 'Low'
        else:
            priority = 'Medium'
    else:
        priority = 'Medium'
    
    return {
        'summary': summary[:255] if len(summary) > 255 else summary,
        'description': description,
        'priority': priority,
        'issuetype': 'tests Case',
        'tipo_prueba': tipo_prueba,
        'categoria': categoria,
        'precondiciones': precondiciones,
        'pasos': pasos if isinstance(pasos, list) else [pasos] if pasos else [],
        'resultado_esperado': resultado_esperado if isinstance(resultado_esperado, list) else [resultado_esperado] if resultado_esperado else []
    }


def parse_test_cases_to_dict(test_cases: List[dict]) -> List[dict]:
    """
    Convierte una lista de casos de prueba (dicts) a una lista de diccionarios estructurados.
    
    Args:
        test_cases: Lista de casos de prueba como diccionarios
        
    Returns:
        List[Dict]: Lista de diccionarios con estructura:
            {
                'index': int,
                'summary': str,
                'description': str,
                'issuetype': str,
                'priority': str,
                'raw_data': dict
            }
    """
    parsed_cases = []
    for idx, test_case in enumerate(test_cases, 1):
        try:
            data = parse_test_case_data(test_case)
            
            # Validar que el summary no esté vacío
            summary = data.get('summary', '').strip()
            if not summary or len(summary) < 3:
                # Fallback adicional: usar ID o índice
                case_id = test_case.get('id_caso_prueba', f'TC{idx:03d}')
                summary = f"Caso de prueba {case_id}"
                logger.warning(f"Summary vacío para caso {idx}, usando fallback: '{summary}'")
            
            parsed_cases.append({
                'index': idx,
                'summary': summary,
                'description': data.get('description', ''),
                'issuetype': data.get('issuetype', 'tests Case'),
                'priority': data.get('priority', 'Medium'),
                'tipo_prueba': data.get('tipo_prueba', 'Funcional'),
                'categoria': data.get('categoria', ''),
                'raw_data': test_case
            })
        except Exception as e:
            logger.error(f"Error al parsear caso de prueba {idx}: {e}", exc_info=True)
            # Agregar caso con valores por defecto para no perder el caso
            parsed_cases.append({
                'index': idx,
                'summary': f"Caso de prueba {test_case.get('id_caso_prueba', f'TC{idx:03d}')}",
                'description': '',
                'issuetype': 'tests Case',
                'priority': 'Medium',
                'tipo_prueba': 'Funcional',
                'categoria': '',
                'raw_data': test_case
            })
    return parsed_cases


def format_test_case_for_html(test_case: dict, case_num: int) -> str:
    """
    Formatea un caso de prueba para HTML.
    
    Args:
        test_case: Diccionario con datos del caso de prueba
        case_num: Número del caso de prueba
        
    Returns:
        str: HTML formateado del caso de prueba
    """
    html_parts = []
    
    # Título - mejorar manejo de valores por defecto
    titulo = test_case.get('titulo_caso_prueba', '')
    if not titulo or titulo.strip() == '' or 'por definir' in titulo.lower():
        case_id = test_case.get('id_caso_prueba', f'TC{case_num:03d}')
        titulo = f'Caso de Prueba {case_id}'
    html_parts.append(f'<div class="story-title">CASO DE PRUEBA #{case_num}: {titulo}</div>')
    
    # ID del caso
    id_caso = test_case.get('id_caso_prueba', f'TC{case_num:03d}')
    html_parts.append(f'''
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">ID:</span>
                            <span class="story-item-content"> {id_caso}</span>
                        </div>''')
    
    # Descripción
    descripcion = test_case.get('Descripcion', '')
    if descripcion:
        html_parts.append(f'''
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Descripción:</span>
                            <span class="story-item-content"> {descripcion[:500]}{"..." if len(descripcion) > 500 else ""}</span>
                        </div>''')
    
    # Precondiciones
    precondiciones = test_case.get('Precondiciones', '')
    if precondiciones:
        html_parts.append(f'''
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Precondiciones:</span>
                            <span class="story-item-content"> {precondiciones[:500]}{"..." if len(precondiciones) > 500 else ""}</span>
                        </div>''')
    
    # Tipo de prueba
    tipo_prueba = test_case.get('Tipo_de_prueba', 'Funcional')
    html_parts.append(f'''
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Tipo de Prueba:</span>
                            <span class="story-item-content"> {tipo_prueba}</span>
                        </div>''')
    
    # Categoría
    categoria = test_case.get('Categoria', '')
    if categoria:
        html_parts.append(f'''
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Categoría:</span>
                            <span class="story-item-content"> {categoria}</span>
                        </div>''')
    
    # Pasos
    pasos = test_case.get('Pasos', [])
    if pasos:
        if isinstance(pasos, str):
            pasos = [pasos]
        pasos_html = []
        for i, paso in enumerate(pasos, 1):
            if paso:
                pasos_html.append(f'''
                                <div class="story-sublist-item">
                                    <span class="bullet">*</span>
                                    <strong>Paso {i}:</strong> {paso[:300]}{"..." if len(paso) > 300 else ""}
                                </div>''')
        if pasos_html:
            html_parts.append('''
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Pasos:</span>
                            <div class="story-sublist">''')
            html_parts.extend(pasos_html)
            html_parts.append('''
                            </div>
                        </div>''')
    
    # Resultado esperado
    resultado_esperado = test_case.get('Resultado_esperado', [])
    if resultado_esperado:
        if isinstance(resultado_esperado, str):
            resultado_esperado = [resultado_esperado]
        resultados_html = []
        for i, resultado in enumerate(resultado_esperado, 1):
            if resultado:
                resultados_html.append(f'''
                                <div class="story-sublist-item">
                                    <span class="bullet">*</span>
                                    <strong>Resultado {i}:</strong> {resultado[:300]}{"..." if len(resultado) > 300 else ""}
                                </div>''')
        if resultados_html:
            html_parts.append('''
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Resultado Esperado:</span>
                            <div class="story-sublist">''')
            html_parts.extend(resultados_html)
            html_parts.append('''
                            </div>
                        </div>''')
    
    # Prioridad
    prioridad = test_case.get('Prioridad', 'Medium')
    html_parts.append(f'''
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Prioridad:</span>
                            <span class="story-item-content"> {prioridad}</span>
                        </div>''')
    
    # Historia de usuario (si existe)
    historia = test_case.get('historia_de_usuario', '')
    if historia:
        html_parts.append(f'''
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Historia de Usuario:</span>
                            <span class="story-item-content"> {historia[:200]}{"..." if len(historia) > 200 else ""}</span>
                        </div>''')
    
    return '<div class="story-container">\n' + '\n'.join(html_parts) + '\n                    </div>'


def generate_test_cases_html_document(test_cases: List[dict], project_name="Sistema de Gestión de Proyectos", client_name="Cliente"):
    """
    Genera un documento HTML para casos de prueba usando el template story_format_mockup.html.
    
    Args:
        test_cases: Lista de casos de prueba
        project_name: Nombre del proyecto
        client_name: Nombre del cliente
        
    Returns:
        str: Contenido HTML del documento
    """
    # Leer el template HTML (mismo que para historias)
    template_paths = [
        'docs/mockups/story_format_mockup.html',
        'mockups/story_format_mockup.html',
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'docs', 'mockups', 'story_format_mockup.html'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'mockups', 'story_format_mockup.html')
    ]
    
    template_path = None
    for path in template_paths:
        if os.path.exists(path):
            template_path = path
            break
    
    if not template_path:
        logger.warning("No se encontró el template HTML, usando template básico")
        html_template = get_basic_html_template()
    else:
        with open(template_path, 'r', encoding='utf-8') as f:
            html_template = f.read()
    
    # Generar contenido del índice
    index_items = []
    for i, test_case in enumerate(test_cases, 1):
        titulo = test_case.get('titulo_caso_prueba', '')
        if not titulo or titulo.strip() == '' or 'por definir' in titulo.lower():
            case_id = test_case.get('id_caso_prueba', f'TC{i:03d}')
            titulo = f'Caso de Prueba {case_id}'
        page_num = i + 2  # Página 3+ (después de portada e índice)
        index_items.append(f'''
                    <div class="index-item">
                        <span class="index-number">{i}.</span>
                        <span class="index-text">{titulo[:80]}</span>
                        <span class="index-page">{page_num}</span>
                    </div>''')
    
    index_html = '\n'.join(index_items)
    
    # Generar páginas de casos de prueba
    case_pages = []
    for i, test_case in enumerate(test_cases, 1):
        page_num = i + 2
        case_html = format_test_case_for_html(test_case, i)
        case_pages.append(f'''
            <!-- PÁGINA {page_num}: CASO DE PRUEBA {i} -->
            <div class="page">
                <div class="page-header">
                    <div>Documento de Casos de Prueba</div>
                    <div>Versión 1.0</div>
                </div>
                <div style="padding-top: 20px;">
                    {case_html}
                </div>
                <div class="page-footer">
                    <div>Confidencial</div>
                    <div class="page-number">Página {page_num}</div>
                    <div>© {datetime.now().year}</div>
                </div>
            </div>''')
    
    cases_html = '\n'.join(case_pages)
    
    # Portada
    portada_html = f'''
            <!-- PÁGINA 1: PORTADA -->
            <div class="page">
                <div class="cover-page">
                    <div class="cover-title">CASOS DE PRUEBA GENERADOS CON AI</div>
                </div>
            </div>'''
    
    # Índice
    indice_html = f'''
            <!-- PÁGINA 2: ÍNDICE -->
            <div class="page">
                <div class="page-header">
                    <div>Documento de Casos de Prueba</div>
                    <div>Versión 1.0</div>
                </div>
                <div style="padding-top: 20px;">
                    <div class="index-title">ÍNDICE</div>
                    {index_html}
                </div>
                <div class="page-footer">
                    <div>Confidencial</div>
                    <div class="page-number">Página 2</div>
                    <div>© {datetime.now().year}</div>
                </div>
            </div>'''
    
    # Insertar contenido en el template
    content_start_match = re.search(r'<div class="content">', html_template)
    
    html_content = None
    
    if content_start_match:
        start_pos = content_start_match.end()
        remaining = html_template[start_pos:]
        
        div_count = 1
        end_pos = start_pos
        pos = 0
        while pos < len(remaining) and div_count > 0:
            div_open = remaining.find('<div', pos)
            div_close = remaining.find('</div>', pos)
            
            if div_close == -1:
                break
            
            if div_open != -1 and div_open < div_close:
                div_count += 1
                pos = div_open + 4
            else:
                div_count -= 1
                if div_count == 0:
                    end_pos = start_pos + div_close + 6
                    break
                pos = div_close + 6
        
        if div_count == 0:
            before_content = html_template[:content_start_match.end()]
            after_content = html_template[end_pos:]
            html_content = before_content + '\n            ' + portada_html + '\n            ' + indice_html + '\n            ' + cases_html + '\n        ' + after_content
    
    # Fallback
    if html_content is None:
        html_content = html_template
        html_content = re.sub(r'<div class="header"[^>]*>.*?</div>\s*</div>', '', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<!--[^>]*PÁGINA\s*1[^>]*PORTADA[^>]*-->.*?</div>\s*</div>\s*</div>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<!--[^>]*PÁGINA\s*2[^>]*ÍNDICE[^>]*-->.*?</div>\s*</div>\s*</div>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<!--[^>]*PÁGINA\s*\d+[^>]*HISTORIA[^>]*-->.*?</div>\s*</div>\s*</div>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        insert_point = html_content.find('<div class="content">')
        if insert_point != -1:
            insert_pos = insert_point + len('<div class="content">')
            html_content = html_content[:insert_pos] + '\n            ' + portada_html + '\n            ' + indice_html + '\n            ' + cases_html + '\n        ' + html_content[insert_pos:]
        else:
            body_end = html_content.find('</body>')
            if body_end != -1:
                html_content = html_content[:body_end] + '\n        <div class="content">\n            ' + portada_html + '\n            ' + indice_html + '\n            ' + cases_html + '\n        </div>\n    ' + html_content[body_end:]
    
    # Reemplazar texto hardcodeado de "Historias de usuario" por "Casos de Prueba" en el template
    if html_content:
        html_content = html_content.replace('HISTORIAS DE USUARIO GENERADAS CON AI', 'CASOS DE PRUEBA GENERADOS CON AI')
        html_content = html_content.replace('Historias de Usuario', 'Casos de Prueba')
        html_content = html_content.replace('Documento de Requisitos', 'Documento de Casos de Prueba')
        html_content = html_content.replace('Mockup - Formato de Historia de Usuario', 'Documento de Casos de Prueba')
    
    return html_content


def get_basic_html_template():
    """Retorna un template HTML básico si no se encuentra el template completo."""
    return '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Casos de Prueba</title>
</head>
<body>
    <h1>Casos de Prueba</h1>
    <!-- CONTENT -->
</body>
</html>'''


def generate_jira_csv_for_test_cases(test_cases: List[dict]):
    """
    Genera un archivo CSV con los campos necesarios para importar casos de prueba a Jira.
    
    Args:
        test_cases: Lista de casos de prueba
        
    Returns:
        str: Contenido CSV como string
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Encabezados
    writer.writerow(['Summary', 'Description', 'Issuetype', 'Priority'])
    
    # Procesar cada caso de prueba
    for test_case in test_cases:
        data = parse_test_case_data(test_case)
        
        # Limpiar y escapar el contenido para CSV
        summary = data['summary'][:255] if data['summary'] else 'Sin título'
        description = data['description'].replace('"', '""')  # Escapar comillas
        issuetype = 'tests Case'
        priority = data['priority']
        
        writer.writerow([summary, description, issuetype, priority])
    
    return output.getvalue()


if __name__ == "__main__":
    # Ejecutar prueba si se ejecuta directamente
    test_matrix_generation()