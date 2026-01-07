"""
Prompts para la generación y corrección de casos de prueba.
Responsabilidad única: Almacenar textos de prompts para IA (SRP).
"""

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

BASE_PROMPT = """
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

PROMPT_MIXED_TYPES = """
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

PROMPT_FUNCIONAL_ONLY = """
GENERA SOLO CASOS FUNCIONALES (no tengas un limite de casos generados, siempre y cuando el documento se preste para hacerlo):
- Todos los flujos principales
- Flujos alternativos y de excepción
- Validación exhaustiva de datos
- Casos límite y condiciones extremas
- Manejo completo de errores
- Estados del sistema y transiciones
"""

PROMPT_NON_FUNCIONAL_ONLY = """
GENERA SOLO CASOS NO FUNCIONALES (no tengas un limite de casos generados, siempre y cuando el documento se preste para hacerlo):
- Rendimiento bajo diferentes cargas
- Seguridad y vectores de ataque
- Usabilidad en diferentes contextos
- Compatibilidad con múltiples entornos
- Confiabilidad y recuperación ante fallos
"""

def get_generation_prompt(prompt_type: str = "mixed", context: str = "", flow: str = "", story: str = "", requirement_id: str = "", chunk: str = "", i: int = 1, total: int = 1) -> str:
    """Construye el prompt completo de generación"""
    if prompt_type == "funcional":
        type_prompt = PROMPT_FUNCIONAL_ONLY
    elif prompt_type == "no_funcional":
        type_prompt = PROMPT_NON_FUNCIONAL_ONLY
    else:
        type_prompt = PROMPT_MIXED_TYPES

    return f"""{BASE_PROMPT}
{type_prompt}
CONTEXTO DEL SISTEMA:
{context or 'Sistema de software a ser probado'}
FLUJO ESPECÍFICO:
{flow or 'Flujos generales del sistema'}
HISTORIA DE USUARIO:
{story}
REQUERIMIENTO ESPECÍFICO (ID):
{requirement_id or 'N/A'}
FRAGMENTO DEL DOCUMENTO A ANALIZAR ({i}/{total}):
{chunk}
INSTRUCCIONES:
1. Analiza este fragmento del documento
2. Genera casos de prueba específicos para el contenido encontrado
3. Asegúrate de que cada caso sea único y tenga valor específico
4. Los pasos deben ser claros y ejecutables
5. Los resultados esperados deben ser verificables
6. Usa '{story}' como valor para el campo 'historia_de_usuario' en cada caso
Responde ÚNICAMENTE con el array JSON de casos de prueba:"""
