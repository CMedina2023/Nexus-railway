"""
Módulo de Generación de Historias de Usuario.

Este módulo contiene la lógica principal para generar historias de usuario
utilizando IA.
"""

import logging
from typing import Dict, List
import google.generativeai as genai

from app.core.config import Config
from app.utils.retry_utils import call_with_retry
from app.backend.story_prompts import create_advanced_prompt, STORY_HEALING_PROMPT
from app.backend.document_processor import process_large_document, split_document_into_chunks

logger = logging.getLogger(__name__)


def generate_story_from_chunk(
    chunk: str,
    role: str,
    story_type: str,
    business_context: str = None,
    skip_healing: bool = False
) -> Dict:
    """
    Genera una historia de usuario a partir de un fragmento de texto usando la API de Gemini.
    
    Args:
        chunk: Fragmento de texto a procesar
        role: Rol del usuario
        story_type: Tipo de historia
        business_context: Contexto adicional de negocio
        skip_healing: Si se debe omitir la auto-curación
        
    Returns:
        dict: Resultado con status y contenido generado
    """
    try:
        api_key = Config.GOOGLE_API_KEY
        if not api_key:
            return {
                "status": "error",
                "message": "API Key no configurada. Configura GOOGLE_API_KEY en el archivo .env"
            }

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(Config.GEMINI_MODEL)

        # Crear prompt avanzado y detectar si necesita procesamiento especial
        prompt = create_advanced_prompt(chunk, role, story_type, business_context)

        # Si el documento requiere procesamiento por chunks
        if prompt == "CHUNK_PROCESSING_NEEDED":
            return process_large_document(chunk, role, story_type, business_context, skip_healing)

        # Reintentos con backoff exponencial
        def generate_content():
            timeout_seconds = Config.GEMINI_TIMEOUT_BASE
            response = model.generate_content(prompt, request_options={"timeout": timeout_seconds})
            
            # Validar respuesta
            if not response or not hasattr(response, 'text') or not response.text:
                raise ValueError("Respuesta vacía o inválida del modelo")
            
            story_text = response.text.strip()
            
            # Validar longitud mínima
            if len(story_text) <= Config.MIN_RESPONSE_LENGTH:
                raise ValueError(f"Respuesta demasiado corta ({len(story_text)} caracteres)")
            
            # Verificar si la respuesta se cortó
            if "La generación completa" in story_text or "Este ejemplo ilustra" in story_text:
                logger.warning("Respuesta posiblemente incompleta detectada")
            
            return story_text
        
        try:
            story_text = call_with_retry(
                generate_content,
                max_retries=Config.MAX_RETRIES,
                retry_delay=Config.RETRY_DELAY,
                timeout_base=Config.GEMINI_TIMEOUT_BASE,
                timeout_increment=Config.GEMINI_TIMEOUT_INCREMENT,
                exceptions=(Exception,)
            )
            
            # Auto-curación para chunk individual
            if not skip_healing:
                story_text = _heal_individual_stories(story_text, chunk, model)
            
            return {"status": "success", "story": story_text}
            
        except Exception as e:
            logger.error(f"Error en la generación después de {Config.MAX_RETRIES} intentos: {e}")
            return {
                "status": "error",
                "message": f"Error en la generación después de {Config.MAX_RETRIES} intentos: {e}"
            }

    except Exception as e:
        return {"status": "error", "message": f"Error en la generación: {e}"}


def generate_story_from_text(
    text: str,
    role: str,
    story_type: str,
    business_context: str = None,
    skip_healing: bool = False
) -> Dict:
    """
    Función wrapper para mantener compatibilidad con la API existente.
    Ahora mejorada con estrategia de DOS PASADAS (Contexto Global + Generación Local).
    
    Args:
        text: Texto del documento
        role: Rol del usuario
        story_type: Tipo de historia
        business_context: Contexto adicional de negocio
        skip_healing: Si se debe omitir la auto-curación
        
    Returns:
        dict: Resultado con status y lista de historias
    """
    # [PASO 1] Análisis Global: Extraer "memoria compartida" del documento
    from app.backend.context_extractor import ContextExtractor
    
    context_extractor = ContextExtractor()
    global_context = context_extractor.extract_global_context(text)
    
    # Combinar contexto manual (business_context) con el extraído (global_context)
    enhanced_context = business_context or ""
    if global_context:
        enhanced_context += f"\n\n{global_context}"
    
    chunks = split_document_into_chunks(text)
    stories = []

    # [PASO 2] Generación Contextual: Cada chunk ahora "sabe" lo que dice el resto del doc
    for chunk in chunks:
        result = generate_story_from_chunk(chunk, role, story_type, enhanced_context, skip_healing)
        if result['status'] == 'success':
            stories.append(result['story'])
        else:
            return result

    # Flattening and cleanup
    from app.services.text_processor import TextProcessor
    from app.services.validator import Validator
    
    tp = TextProcessor()
    validator = Validator()
    
    all_individual_stories = []
    for s in stories:
        all_individual_stories.extend(tp.split_story_text_into_individual_stories(s))
    
    stories = all_individual_stories

    # Eliminación de duplicados
    if len(stories) > 1:
        logger.info(f"Buscando historias duplicadas entre {len(stories)} elementos...")
        duplicate_indices = validator.find_duplicates(stories, threshold=0.90)
        if duplicate_indices:
            stories = [s for idx, s in enumerate(stories) if idx not in duplicate_indices]
            logger.info(f"Se eliminaron {len(duplicate_indices)} historias duplicadas.")

    return {"status": "success", "stories": stories}


def generate_stories_with_context(
    document_text: str,
    role: str,
    story_type: str,
    business_context: str = None,
    skip_healing: bool = False
) -> Dict:
    """
    Función principal para generar historias de usuario con contexto de negocio.
    
    Args:
        document_text: Contenido del documento a analizar
        role: Rol del usuario
        story_type: Tipo de historias
        business_context: Contexto adicional de negocio
        skip_healing: Si se debe omitir la auto-curación
        
    Returns:
        dict: Resultado de la generación con status y contenido
    """
    return generate_story_from_text(document_text, role, story_type, business_context, skip_healing)


def _heal_individual_stories(story_text: str, chunk: str, model) -> str:
    """
    Realiza auto-curación de historias individuales.
    
    Args:
        story_text: Texto de las historias generadas
        chunk: Fragmento de texto original
        model: Modelo de IA para curación
        
    Returns:
        str: Texto de historias curadas
    """
    from app.services.text_processor import TextProcessor
    from app.services.validator import Validator
    
    tp = TextProcessor()
    validator = Validator()
    
    individual_stories = tp.split_story_text_into_individual_stories(story_text)
    
    healed_any = False
    for idx_s, individual_story in enumerate(individual_stories):
        val_res = validator.semantic_validate_story(individual_story, chunk[:1000])
        if not val_res["is_valid"]:
            logger.warning(f"  ❌ Historia detectada con baja calidad. Intentando sanación...")
            try:
                prompt_heal = STORY_HEALING_PROMPT.format(
                    issues="\n- ".join(val_res["issues"]),
                    original_story=individual_story,
                    doc_context=chunk[:1000]
                )
                response_heal = model.generate_content(prompt_heal)
                if response_heal and response_heal.text:
                    # Si mejora el score o es válida, aceptamos
                    second_val = validator.semantic_validate_story(response_heal.text, chunk[:1000])
                    if second_val["is_valid"] or second_val["score"] > val_res["score"]:
                        individual_stories[idx_s] = response_heal.text
                        healed_any = True
                        logger.info(f"  ✅ Historia sanada exitosamente.")
            except Exception as p_e:
                logger.error(f"  Error al sanar historia: {p_e}")
    
    if healed_any:
        story_text = "\n\n".join(individual_stories)
    
    return story_text
