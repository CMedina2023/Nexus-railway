"""
Módulo de Procesamiento de Documentos para Historias de Usuario.

Este módulo maneja el procesamiento de documentos grandes y la división
en chunks manejables.
"""

import logging
import time
import re
from typing import List, Dict
import google.generativeai as genai

from app.core.config import Config
from app.utils.document_chunker import DocumentChunker, ChunkingStrategy
from app.utils.retry_utils import call_with_retry
from app.backend.story_prompts import (
    create_analysis_prompt,
    create_story_generation_prompt,
    STORY_HEALING_PROMPT_BATCH
)

logger = logging.getLogger(__name__)


def split_document_into_chunks(text: str, max_chunk_size: int = None) -> List[str]:
    """
    Divide el documento en chunks manejables usando DocumentChunker.
    
    Args:
        text: Texto del documento a dividir
        max_chunk_size: Tamaño máximo del chunk (default: Config.STORY_MAX_CHUNK_SIZE)
        
    Returns:
        List[str]: Lista de chunks del documento
    """
    if max_chunk_size is None:
        max_chunk_size = Config.STORY_MAX_CHUNK_SIZE
    
    chunker = DocumentChunker(max_chunk_size=max_chunk_size, strategy=ChunkingStrategy.SMART)
    return chunker.split_document_into_chunks(text, max_chunk_size)


def process_large_document(
    document_text: str,
    role: str,
    story_type: str,
    business_context: str = None,
    skip_healing: bool = False
) -> Dict:
    """
    Procesa documentos grandes dividiéndolos en chunks.
    
    Args:
        document_text: Texto del documento a procesar
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

        logger.info("Documento grande detectado. Iniciando análisis por fases...")

        # Debug para verificar parámetros
        logger.debug(f"business_context recibido: {business_context}")
        logger.debug(f"role: {role}")
        logger.debug(f"story_type: {story_type}")

        # Fase 1: Análisis de funcionalidades
        logger.info("Fase 1: Identificando todas las funcionalidades...")
        analysis_prompt = create_analysis_prompt(document_text, role, business_context)

        analysis_response = model.generate_content(
            analysis_prompt,
            request_options={"timeout": Config.GEMINI_TIMEOUT_ANALYSIS}
        )

        # Extraer lista de funcionalidades
        functionalities = []
        lines = analysis_response.text.split('\n')
        for line in lines:
            if re.match(r'^\d+\.', line.strip()):
                functionalities.append(line.strip())

        logger.info(f"Identificadas {len(functionalities)} funcionalidades")

        # Fase 2: Generar historias por lotes
        all_stories = []
        batch_size = Config.STORY_BATCH_SIZE
        total_batches = (len(functionalities) + batch_size - 1) // batch_size

        for batch_num in range(total_batches):
            # Pacing: Obligar a un respiro entre lotes
            if batch_num > 0:
                logger.info("Esperando 5 segundos para respetar cuota RPM...")
                time.sleep(5)
                
            start_idx = batch_num * batch_size
            end_idx = min((batch_num + 1) * batch_size, len(functionalities))
            batch = functionalities[start_idx:end_idx]
            
            logger.info(f"Generando lote {batch_num + 1}/{total_batches} ({len(batch)} funcionalidades)...")

            story_prompt = create_story_generation_prompt(
                functionalities, document_text, role, business_context, start_idx, batch_size
            )

            # Reintentos con backoff exponencial
            def generate_story_batch():
                timeout_seconds = Config.GEMINI_TIMEOUT_BASE + (len(all_stories) * Config.GEMINI_TIMEOUT_INCREMENT)
                response = model.generate_content(story_prompt, request_options={"timeout": timeout_seconds})
                if not response or not hasattr(response, 'text') or not response.text or not response.text.strip():
                    raise ValueError("Respuesta vacía o inválida del modelo")
                if len(response.text.strip()) <= Config.MIN_RESPONSE_LENGTH:
                    raise ValueError(f"Respuesta demasiado corta ({len(response.text)} caracteres)")
                return response.text
            
            try:
                story_text = call_with_retry(
                    generate_story_batch,
                    max_retries=Config.MAX_RETRIES,
                    retry_delay=Config.RETRY_DELAY,
                    timeout_base=Config.GEMINI_TIMEOUT_BASE,
                    timeout_increment=Config.GEMINI_TIMEOUT_INCREMENT,
                    exceptions=(Exception,)
                )
                
                # Auto-curación
                if not skip_healing:
                    story_text = _heal_stories_in_batch(
                        story_text,
                        functionalities,
                        start_idx,
                        document_text,
                        model
                    )
                
                all_stories.append(story_text)
                
            except Exception as e:
                logger.error(f"No se pudo generar el lote {batch_num + 1} después de {Config.MAX_RETRIES} intentos: {e}")

        # Flatten all_stories into a single list
        from app.services.text_processor import TextProcessor
        tp = TextProcessor()
        all_individual_stories = []
        for batch_story_text in all_stories:
            all_individual_stories.extend(tp.split_story_text_into_individual_stories(batch_story_text))

        # Combinar todas las historias
        story_content_flattened = chr(10).join(all_individual_stories)

        # Preparar resumen de contexto
        context_summary = _prepare_context_summary(business_context)

        final_content = f"""
ANÁLISIS COMPLETO - {len(functionalities)} FUNCIONALIDADES IDENTIFICADAS
{"=" * 70}
{context_summary}
FUNCIONALIDADES IDENTIFICADAS:
{chr(10).join(functionalities)}

{"=" * 70}
HISTORIAS DE USUARIO DETALLADAS
{"=" * 70}

{chr(10).join(all_stories)}

{"=" * 70}
RESUMEN FINAL
{"=" * 70}
✅ Total de funcionalidades procesadas: {len(functionalities)}
✅ Total de lotes generados: {total_batches}
✅ Contexto adicional: {'Aplicado' if business_context and not business_context.startswith("AIza") else 'No proporcionado'}
✅ Análisis completado exitosamente
"""

        logger.info("Análisis completo finalizado exitosamente")
        return {"status": "success", "story": final_content}

    except Exception as e:
        logger.error(f"Error en procesamiento por chunks: {e}", exc_info=True)
        return {"status": "error", "message": f"Error en procesamiento avanzado: {e}"}


def _heal_stories_in_batch(
    story_text: str,
    functionalities: List[str],
    start_idx: int,
    document_text: str,
    model
) -> str:
    """
    Realiza auto-curación de historias en un lote.
    
    Args:
        story_text: Texto de las historias generadas
        functionalities: Lista de funcionalidades
        start_idx: Índice de inicio del lote
        document_text: Texto del documento original
        model: Modelo de IA para curación
        
    Returns:
        str: Texto de historias curadas
    """
    from app.services.text_processor import TextProcessor
    from app.services.validator import Validator
    
    tp = TextProcessor()
    validator = Validator()
    
    individual_stories = tp.split_story_text_into_individual_stories(story_text)
    
    failed_indices = []
    issues_list = []
    
    for idx_s, individual_story in enumerate(individual_stories):
        # Usar funcionalidad específica como contexto si está disponible
        validation_context = functionalities[start_idx + idx_s] if start_idx + idx_s < len(functionalities) else document_text[:1000]
        val_res = validator.semantic_validate_story(individual_story, validation_context)
        if not val_res["is_valid"]:
            failed_indices.append(idx_s)
            issues_list.append(f"Historia {idx_s + 1}: {', '.join(val_res['issues'])}")
    
    if failed_indices:
        logger.warning(f"  ❌ {len(failed_indices)} historias fallaron validación. Iniciando curación en bloque...")
        try:
            stories_to_heal = [individual_stories[idx] for idx in failed_indices]
            prompt_heal = STORY_HEALING_PROMPT_BATCH.format(
                batch_issues="\n".join(issues_list),
                batch_stories="\n\n".join(stories_to_heal),
                doc_context=document_text[:2000]
            )
            response_heal = model.generate_content(prompt_heal)
            if response_heal and response_heal.text:
                # Re-separar las historias corregidas
                healed_stories = tp.split_story_text_into_individual_stories(response_heal.text)
                for j, original_idx in enumerate(failed_indices):
                    if j < len(healed_stories):
                        individual_stories[original_idx] = healed_stories[j]
                logger.info(f"  ✅ Curación en bloque completada para historias.")
        except Exception as p_e:
            logger.error(f"  Error al sanar historias en bloque: {p_e}")
    
    return "\n\n".join(individual_stories)


def _prepare_context_summary(business_context: str) -> str:
    """
    Prepara el resumen de contexto de negocio.
    
    Args:
        business_context: Contexto de negocio proporcionado
        
    Returns:
        str: Resumen formateado del contexto
    """
    if business_context and business_context.strip():
        # Verificar que no sea la API key
        if not business_context.startswith("AIza"):
            return f"""
CONTEXTO ADICIONAL APLICADO:
{business_context[:200]}{'...' if len(business_context) > 200 else ''}
{'-' * 70}
"""
        else:
            logger.warning("Se detectó API key en business_context, ignorando...")
            return f"""
CONTEXTO ADICIONAL APLICADO: No proporcionado
{'-' * 70}
"""
    else:
        return f"""
CONTEXTO ADICIONAL APLICADO: No proporcionado
{'-' * 70}
"""
