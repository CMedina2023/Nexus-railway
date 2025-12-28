"""
Módulo de Extracción de Contexto Global.

Este componente es responsable de la "Primera Pasada" en la estrategia de generación.
Su objetivo es leer el documento completo (o una representación significativa) y
extraer un "Grafo de Conocimiento" o contexto compartido que evitará que
el generador de historias trabaje a ciegas (limitación de chunks aislados).
"""

import logging
import google.generativeai as genai
from app.core.config import Config
from app.utils.retry_utils import call_with_retry
from app.backend.story_prompts import GLOBAL_ANALYSIS_PROMPT

logger = logging.getLogger(__name__)

class ContextExtractor:
    """
    Clase dedicada exclusivamente al análisis de contexto global de documentos.
    Sigue el principio de responsabilidad única (SRP).
    """

    def __init__(self):
        self.api_key = Config.GOOGLE_API_KEY
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
        else:
            logger.warning("API Key no configurada en ContextExtractor")
            self.model = None

    def extract_global_context(self, document_text: str) -> str:
        """
        Analiza el documento completo para extraer definiciones, reglas y 
        dependencias globales.

        Args:
            document_text: Texto completo del documento (o resumen representativo).

        Returns:
            str: Resumen del contexto global formateado.
        """
        if not self.model:
            return "Error: Modelo no inicializado por falta de API Key."

        # Protección para ahorro de tokens en documentos masivos durante la fase de análisis
        # Si es demasiado grande, tomamos inicio y fin, o confiamos en la capacidad del modelo
        # Por ahora enviamos los primeros 15k caracteres como muestra representativa para contexto global
        # si es que el documento es inmenso. Ajustable según necesidad.
        MAX_CONTEXT_ANALYSIS_LENGTH = 30000 
        text_to_analyze = document_text[:MAX_CONTEXT_ANALYSIS_LENGTH]
        
        if len(document_text) > MAX_CONTEXT_ANALYSIS_LENGTH:
            logger.info(f"Documento extenso. Analizando los primeros {MAX_CONTEXT_ANALYSIS_LENGTH} caracteres para contexto global.")

        logger.info("Iniciando extracción de contexto global (Fase 1)...")

        prompt = GLOBAL_ANALYSIS_PROMPT.format(document_text=text_to_analyze)

        def _generate():
            response = self.model.generate_content(
                prompt, 
                request_options={"timeout": Config.GEMINI_TIMEOUT_ANALYSIS}
            )
            if not response or not hasattr(response, 'text') or not response.text:
                raise ValueError("Respuesta vacía al extraer contexto global")
            return response.text.strip()

        try:
            global_context = call_with_retry(
                _generate,
                max_retries=2, # Menos reintentos para esta fase auxiliar
                retry_delay=1,
                timeout_base=Config.GEMINI_TIMEOUT_ANALYSIS
            )
            logger.info("Contexto global extraído exitosamente.")
            return global_context

        except Exception as e:
            logger.error(f"Fallo al extraer contexto global: {e}")
            # Fallback seguro: Si falla el análisis global, devolvemos cadena vacía
            # para no bloquear el flujo principal, aunque perderemos la inteligencia extra.
            return ""
