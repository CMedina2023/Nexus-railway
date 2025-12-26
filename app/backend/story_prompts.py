"""
Módulo de Prompts para Generación de Historias de Usuario.

Este módulo centraliza todos los prompts utilizados para la generación
de historias de usuario con IA.
"""

# ----------------------------
# Prompts de Calidad para Historias
# ----------------------------
STORY_HEALING_PROMPT_BATCH = """
Eres un experto Analista de Negocios Senior. Tu tarea es CORREGIR y MEJORAR un grupo de Historias de Usuario que no cumplen con los estándares de calidad.

ERRORES DETECTADOS POR EL VALIDADOR:
{batch_issues}

HISTORIAS A CORREGIR:
{batch_stories}

CONTEXTO DEL DOCUMENTO:
{doc_context}

REGLAS DE ORO PARA LA CORRECCIÓN:
1. FORMATO ESTÁNDAR: Debe seguir estrictamente el formato "COMO [rol] QUIERO [funcionalidad] PARA [beneficio]".
2. DETALLE: Incluye criterios de aceptación claros y Reglas de Negocio.
3. ESTILO: Mantén el estilo visual de los bloques con líneas dobles (╔═══, ═) y emojis (🔹, •).
4. INTEGRIDAD: Devuelve TODAS las historias corregidas, separadas claramente.

Responde ÚNICAMENTE con las historias de usuario corregidas:
"""


STORY_HEALING_PROMPT = """
Eres un experto Analista de Negocios Senior. Tu tarea es CORREGIR y MEJORAR una Historia de Usuario que no cumple con los estándares de calidad.

ERRORES DETECTADOS:
{issues}

HISTORIA ORIGINAL:
{original_story}

CONTEXTO DEL DOCUMENTO:
{doc_context}

REGLAS DE ORO PARA LA CORRECCIÓN:
1. FORMATO ESTÁNDAR: Debe seguir estrictamente el formato "COMO [rol] QUIERO [funcionalidad] PARA [beneficio]".
2. DETALLE: Incluye criterios de aceptación claros y Reglas de Negocio.
3. ESTILO: Mantén el estilo visual de los bloques con líneas dobles (╔═══, ═) y emojis (🔹, •).

Responde ÚNICAMENTE con la historia de usuario corregida:
"""


def create_analysis_prompt(document_text: str, role: str, business_context: str = None) -> str:
    """
    Crea un prompt inicial para análisis de funcionalidades.
    
    Args:
        document_text: Texto del documento a analizar
        role: Rol del usuario
        business_context: Contexto adicional de negocio (opcional)
        
    Returns:
        str: Prompt formateado para análisis
    """
    context_section = ""
    if business_context and business_context.strip():
        context_section = f"""
CONTEXTO ADICIONAL DE NEGOCIO:
{business_context}

IMPORTANTE: Debes tomar en cuenta TANTO los requerimientos del documento COMO el contexto adicional proporcionado.
"""

    return f"""
Eres un analista de negocios Senior. Tu tarea es IDENTIFICAR Y LISTAR todas las funcionalidades del siguiente documento.

DOCUMENTO A ANALIZAR:
{document_text}
{context_section}
INSTRUCCIONES:
1. Lee COMPLETAMENTE el documento
2. Identifica TODAS las funcionalidades mencionadas
3. Toma en cuenta el contexto adicional de negocio si se proporciona
4. Crea una LISTA NUMERADA de funcionalidades EXCLUSIVAMENTE para el rol: {role}.
5. Ignora cualquier funcionalidad que corresponda a otros roles diferentes a {role}.

FORMATO DE RESPUESTA:
Lista de Funcionalidades Identificadas:
1. [Nombre funcionalidad] - [Descripción breve]
2. [Nombre funcionalidad] - [Descripción breve]
...

Al final indica: "TOTAL FUNCIONALIDADES IDENTIFICADAS: [número]"

NO generes historias de usuario todavía, solo la lista de funcionalidades.
"""


def create_story_generation_prompt(
    functionalities_list: list,
    document_text: str,
    role: str,
    business_context: str,
    start_index: int,
    batch_size: int = 5
) -> str:
    """
    Crea prompt para generar historias de usuario por lotes.
    
    Args:
        functionalities_list: Lista de funcionalidades identificadas
        document_text: Texto del documento original
        role: Rol del usuario
        business_context: Contexto adicional de negocio
        start_index: Índice de inicio del lote
        batch_size: Tamaño del lote
        
    Returns:
        str: Prompt formateado para generación de historias
    """
    end_index = min(start_index + batch_size, len(functionalities_list))
    selected_functionalities = functionalities_list[start_index:end_index]

    func_text = "\n".join([f"{i + start_index + 1}. {func}" for i, func in enumerate(selected_functionalities)])

    context_section = ""
    if business_context and business_context.strip():
        context_section = f"""
CONTEXTO ADICIONAL DE NEGOCIO (OBLIGATORIO CONSIDERAR):
{business_context}

IMPORTANTE: Las historias de usuario deben integrar TANTO la información del documento COMO las consideraciones del contexto adicional.
"""

    return f"""
Eres un analista de negocios Senior. Genera historias de usuario DETALLADAS para las siguientes funcionalidades específicas.

FUNCIONALIDADES A DESARROLLAR (Lote {start_index + 1} a {end_index}):
{func_text}

DOCUMENTO DE REFERENCIA (para contexto adicional):
{document_text[:2000]}...
{context_section}
FORMATO OBLIGATORIO para CADA funcionalidad:

```
╔════════════════════════════════════════════════════════════════════════════════
HISTORIA #{start_index + 1}: [Título de la funcionalidad]
════════════════════════════════════════════════════════════════════════════════

COMO: {role}
QUIERO: [funcionalidad específica y detallada]
PARA: [beneficio de negocio claro y medible]

CRITERIOS DE ACEPTACIÓN:

🔹 Escenario Principal:
   DADO que [contexto específico]
   CUANDO [acción concreta del usuario]
   ENTONCES [resultado esperado detallado]

🔹 Escenario Alternativo:
   DADO que [contexto alternativo]
   CUANDO [acción diferente]
   ENTONCES [resultado alternativo]

🔹 Validaciones:
   DADO que [condición de error]
   CUANDO [acción que genera error]
   ENTONCES [manejo de error esperado]

REGLAS DE NEGOCIO:
• [Regla específica 1]
• [Regla específica 2]

PRIORIDAD: [Alta/Media/Baja]
COMPLEJIDAD: [Simple/Moderada/Compleja]

════════════════════════════════════════════════════════════════════════════════
```

IMPORTANTE: 
- TODAS las historias deben generarse ÚNICAMENTE desde la perspectiva del rol **{role}**.
- Integra el contexto adicional de negocio en las reglas de negocio y criterios de aceptación.
- No inventes ni incluyas otros roles diferentes a {role}.
- Numera consecutivamente desde {start_index + 1}.
"""


def create_advanced_prompt(
    document_text: str,
    role: str,
    story_type: str,
    business_context: str = None
) -> str:
    """
    Crea el prompt avanzado basado en el tipo de historia solicitada.
    
    Args:
        document_text: Texto del documento a analizar
        role: Rol del usuario
        story_type: Tipo de historia (funcionalidad, característica, etc.)
        business_context: Contexto adicional de negocio (opcional)
        
    Returns:
        str: Prompt formateado o "CHUNK_PROCESSING_NEEDED" si requiere procesamiento especial
    """
    from app.core.config import Config
    
    context_section = ""
    if business_context and business_context.strip():
        context_section = f"""
CONTEXTO ADICIONAL DE NEGOCIO (CRÍTICO):
{business_context}

INTEGRACIÓN OBLIGATORIA: Debes incorporar este contexto en:
- Los criterios de aceptación
- Las reglas de negocio
- Los escenarios de validación
- Las consideraciones de prioridad
"""

    if story_type == 'historia de usuario' or story_type == 'funcionalidad':
        # Para documentos grandes, usar estrategia de chunks
        if len(document_text) > Config.LARGE_DOCUMENT_THRESHOLD:
            return "CHUNK_PROCESSING_NEEDED"

        # Para documentos medianos/pequeños, prompt optimizado
        prompt = f"""
Eres un analista de negocios Senior especializado en QA y análisis exhaustivo de requerimientos.

DOCUMENTO A ANALIZAR:
{document_text}
{context_section}
INSTRUCCIONES CRÍTICAS:

1. ANÁLISIS EXHAUSTIVO:
   - Identifica TODAS las funcionalidades del documento
   - Incluye ÚNICAMENTE las que correspondan al rol que se proporciona en la UI {role}
   - Integra el contexto adicional de negocio en cada historia

2. GENERACIÓN DE HISTORIAS PARA: **{role}**

FORMATO OBLIGATORIO:

```
╔════════════════════════════════════════════════════════════════════════════════
HISTORIA #{{número}}: [Título]
════════════════════════════════════════════════════════════════════════════════

COMO: {role}
QUIERO: [funcionalidad específica]
PARA: [beneficio de negocio]

CRITERIOS DE ACEPTACIÓN:

🔹 Escenario Principal:
   DADO que [contexto]
   CUANDO [acción]
   ENTONCES [resultado]

🔹 Escenario Alternativo:
   DADO que [contexto alternativo]
   CUANDO [acción diferente]
   ENTONCES [resultado alternativo]

🔹 Validaciones:
   DADO que [error]
   CUANDO [acción error]
   ENTONCES [manejo error]

REGLAS DE NEGOCIO:
• [Regla 1]
• [Regla 2]

PRIORIDAD: [Alta/Media/Baja]
COMPLEJIDAD: [Simple/Moderada/Compleja]

════════════════════════════════════════════════════════════════════════════════
```

EXPECTATIVA: Genera entre 10-50 historias según el contenido del documento.

IMPORTANTE: 
- Si el documento es extenso y sientes que podrías cortarte, termina la historia actual y agrega al final:
"CONTINÚA EN EL SIGUIENTE LOTE - FUNCIONALIDADES PENDIENTES: [lista las que faltan]"
- SIEMPRE integra el contexto adicional proporcionado en las historias generadas.
"""

    elif story_type == 'característica':
        prompt = f"""
Eres un analista de negocios Senior especializado en requisitos no funcionales.

DOCUMENTO A ANALIZAR:
{document_text}
{context_section}
Identifica TODOS los requisitos no funcionales (rendimiento, seguridad, usabilidad, etc.) y genera historias para el rol: {role}

FORMATO:

```
╔════════════════════════════════════════════════════════════════════════════════
HISTORIA NO FUNCIONAL #{{número}}: [Título]
════════════════════════════════════════════════════════════════════════════════

COMO: {role}
NECESITO: [requisito no funcional]
PARA: [garantizar calidad]

CRITERIOS DE ACEPTACIÓN:
• [Criterio medible 1]
• [Criterio medible 2]

MÉTRICAS:
• [Métrica objetivo]

CATEGORÍA: [Rendimiento/Seguridad/Usabilidad/etc.]
PRIORIDAD: [Alta/Media/Baja]

════════════════════════════════════════════════════════════════════════════════
```

IMPORTANTE: Integra el contexto adicional de negocio en los criterios y métricas.
"""

    else:
        # Para cualquier otro tipo, usar el formato funcional por defecto
        return create_advanced_prompt(document_text, role, 'funcionalidad', business_context)

    return prompt
