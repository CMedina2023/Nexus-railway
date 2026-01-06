"""
Módulo de Fusión de Contexto.
Responsable de unificar el conocimiento extraído de múltiples documentos en una
única fuente de verdad (ProjectContext).
"""
import logging
import json
from typing import List, Dict, Optional
from datetime import datetime
import google.generativeai as genai
from app.core.config import Config
from app.models.project_context import ProjectContext
from app.models.project_document import ProjectDocument
from app.utils.retry_utils import call_with_retry

logger = logging.getLogger(__name__)

MERGE_PROMPT_TEMPLATE = """
Actúa como un Arquitecto de Software Senior y Analista de Negocio.
Tu tarea es FUSIONAR múltiples contextos de documentación técnica en una única "Verdad Central" coherente.

Entradas que recibirás:
1. RESUMEN ACTUAL (Puede estar vacío si es el primero)
2. NUEVA INFORMACIÓN (Extraída de un documento reciente)

Debes generar un objeto JSON con la siguiente estructura, resolviendo conflictos:
{{
    "summary": "Resumen ejecutivo actualizado del proyecto (máx 3 parrafos)",
    "glossary": {{ "Término": "Definición concisa", ... }},
    "business_rules": ["Regla 1", "Regla 2", ...],
    "tech_constraints": ["Restricción 1", "Restricción 2", ...]
}}

Reglas de Fusión:
- GLOSARIO: Si un término ya existe, mejora la definición con la nueva información. No dupliques.
- REGLAS: Elimina reglas duplicadas o muy similares. Mantén las más específicas.
- CONFLICTOS: Si hay información contradictoria, prioriza la "NUEVA INFORMACIÓN" asumiendo que es más reciente, pero nota el conflicto.
- ESTILO: Usa lenguaje técnico, claro y directo. Español neutro.

---
RESUMEN ACTUAL:
{current_summary}

GLOSARIO ACTUAL:
{current_glossary}

REGLAS ACTUALES:
{current_rules}

---
NUEVA INFORMACIÓN DEL DOCUMENTO '{filename}':
{new_content}
---

Salida JSON:
"""

EXTRACTION_PROMPT_TEMPLATE = """
Analiza el siguiente documento técnico y extrae metadata estructurada.
Documento: {filename}

Salida JSON requerida:
{{
    "summary": "Resumen del objetivo de este documento",
    "glossary": {{ "Término clave": "Definición encontrada en el texto" }},
    "business_rules": ["Regla de negocio explícita 1", "Regla 2"],
    "tech_constraints": ["Restricción técnica 1"]
}}

Contenido:
{content}
"""

class ContextMerger:
    """
    Servicio encargado de fusionar inteligencia de múltiples fuentes.
    Implementa un patrón Map-Reduce usando LLMs.
    """

    def __init__(self):
        self.api_key = Config.GOOGLE_API_KEY
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
            # Configuración para respuesta JSON
            self.generation_config = genai.GenerationConfig(
                response_mime_type="application/json"
            )
        else:
            logger.warning("API Key no configurada en ContextMerger")
            self.model = None

    def merge_documents(self, documents: List[ProjectDocument], current_context: Optional[ProjectContext] = None) -> ProjectContext:
        """
        Toma una lista de documentos y los fusiona en el contexto actual (o crea uno nuevo).
        
        Args:
            documents: Lista de documentos a procesar
            current_context: Contexto existente (opcional)
            
        Returns:
            ProjectContext actualizado
        """
        if not documents:
            return current_context or ProjectContext(project_key="unknown")

        # Inicializar contexto si no existe
        project_key = documents[0].project_key
        final_context = current_context or ProjectContext(project_key=project_key)

        # 1. Fase MAP: Extraer contexto individual de cada documento
        extracted_contexts = []
        for doc in documents:
            try:
                # Aquí asumimos que doc.content_path nos permitiría leer el archivo.
                # Por simplicidad del ejemplo, asumiremos que doc tiene un atributo 'content_preview' 
                # o que leemos el archivo aquí. En una implementación real usaríamos un FileReader.
                # Simularemos lectura:
                content = self._read_document_content(doc)
                if not content:
                    logger.warning(f"Documento vacío o no legible: {doc.filename}")
                    continue
                
                partial_context = self._extract_single_context(doc.filename, content)
                if partial_context:
                    extracted_contexts.append((doc.filename, partial_context))
            except Exception as e:
                logger.error(f"Error procesando documento {doc.filename}: {e}")

        # 2. Fase REDUCE: Fusionar secuencialmente (o jerárquicamente)
        # Para reducir alucinaciones y mantener coherencia, fusionamos incrementalmente.
        for filename, partial in extracted_contexts:
            final_context = self._merge_partial_into_global(final_context, partial, filename)

        final_context.version += 1
        final_context.updated_at = datetime.now()
        
        return final_context

    def _read_document_content(self, doc: ProjectDocument) -> str:
        """
        Lee el contenido del documento.
        Nota: Esto debería delegarse a un FileService, simplificado aquí.
        """
        # TODO: Implementar lectura real de archivos (PDF, TXT, MD)
        # Por ahora intentamos leer si es texto plano y la ruta existe
        try:
            with open(doc.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read(15000) # Límite de caracteres para evitar overflow de contexto
        except Exception:
            return ""

    def _extract_single_context(self, filename: str, content: str) -> Dict:
        """Extrae metadata estructurada de un solo documento."""
        if not self.model:
            return {}

        prompt = EXTRACTION_PROMPT_TEMPLATE.format(filename=filename, content=content[:20000])

        try:
            response = call_with_retry(
                lambda: self.model.generate_content(
                    prompt, 
                    generation_config=self.generation_config
                ),
                max_retries=2
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Error en extracción individual ({filename}): {e}")
            return {}

    def _merge_partial_into_global(self, global_ctx: ProjectContext, partial: Dict, filename: str) -> ProjectContext:
        """Fusiona un contexto parcial en el contexto global usando LLM."""
        if not self.model:
            return global_ctx

        # Preparar datos actuales para el prompt
        current_data = global_ctx.to_dict()
        
        prompt = MERGE_PROMPT_TEMPLATE.format(
            current_summary=current_data.get('summary', ''),
            current_glossary=json.dumps(current_data.get('glossary', {}), ensure_ascii=False),
            current_rules=json.dumps(current_data.get('business_rules', []), ensure_ascii=False),
            filename=filename,
            new_content=json.dumps(partial, ensure_ascii=False)
        )

        try:
            response = call_with_retry(
                lambda: self.model.generate_content(
                    prompt, 
                    generation_config=self.generation_config
                ),
                max_retries=2
            )
            merged_data = json.loads(response.text)

            # Actualizar el objeto ProjectContext
            global_ctx.summary = merged_data.get('summary', global_ctx.summary)
            global_ctx.glossary = merged_data.get('glossary', global_ctx.glossary)
            global_ctx.business_rules = merged_data.get('business_rules', global_ctx.business_rules)
            
            # Tech constraints might be missing in merge prompt output if LLM decides so, 
            # safe merge logic:
            if 'tech_constraints' in merged_data:
                global_ctx.tech_constraints = merged_data['tech_constraints']

            return global_ctx

        except Exception as e:
            logger.error(f"Error fusionando contexto: {e}")
            return global_ctx
