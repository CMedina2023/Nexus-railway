"""
Backend para Generación de Historias de Usuario con IA.

Este módulo actúa como fachada principal para la generación de historias de usuario,
delegando la funcionalidad a módulos especializados.

REFACTORIZADO: Este archivo ahora importa y delega a módulos especializados:
- story_prompts.py: Gestión de prompts
- story_parser.py: Parsing de historias
- story_generator.py: Generación con IA
- story_formatters.py: Formateo a Word, CSV, HTML
- document_processor.py: Procesamiento de documentos grandes
"""

import logging
from typing import List, Dict

# Importar funciones de módulos especializados
from app.backend.story_generator import (
    generate_story_from_chunk,
    generate_story_from_text,
    generate_stories_with_context
)

from app.backend.story_parser import (
    extract_story_titles,
    parse_story_data,
    parse_stories_to_dict
)

from app.backend.story_formatters import (
    create_word_document,
    generate_jira_csv,
    format_story_for_html,
    generate_html_document,
    get_basic_html_template,
    reconstruct_html_from_template
)

from app.backend.document_processor import (
    split_document_into_chunks,
    process_large_document
)

from app.backend.story_prompts import (
    create_analysis_prompt,
    create_story_generation_prompt,
    create_advanced_prompt,
    STORY_HEALING_PROMPT_BATCH
)

logger = logging.getLogger(__name__)

# ============================================================================
# FUNCIONES PÚBLICAS DE LA API
# ============================================================================

# Las funciones están disponibles a través de los imports de arriba
# Este archivo actúa como punto de entrada unificado

__all__ = [
    # Generación
    'generate_story_from_chunk',
    'generate_story_from_text',
    'generate_stories_with_context',
    
    # Parsing
    'extract_story_titles',
    'parse_story_data',
    'parse_stories_to_dict',
    
    # Formateo
    'create_word_document',
    'generate_jira_csv',
    'format_story_for_html',
    'generate_html_document',
    'get_basic_html_template',
    'reconstruct_html_from_template',
    
    # Procesamiento de documentos
    'split_document_into_chunks',
    'process_large_document',
    
    # Prompts
    'create_analysis_prompt',
    'create_story_generation_prompt',
    'create_advanced_prompt',
    'STORY_HEALING_PROMPT_BATCH'
]

logger.info("story_backend.py refactorizado - Usando módulos especializados")
