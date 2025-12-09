"""
Utilidad para dividir documentos en chunks
Responsabilidad única: División de documentos en fragmentos manejables
"""
import re
import logging
from typing import List, Optional
from enum import Enum

from app.core.config import Config

logger = logging.getLogger(__name__)


class ChunkingStrategy(Enum):
    """Estrategias de chunking disponibles"""
    SMART = "smart"  # Intenta dividir por secciones, luego párrafos
    LINEAR = "linear"  # División lineal por líneas/párrafos
    SENTENCE = "sentence"  # División por oraciones


class DocumentChunker:
    """Divide documentos en chunks de tamaño manejable"""
    
    def __init__(self, max_chunk_size: int = None, strategy: ChunkingStrategy = ChunkingStrategy.SMART):
        """
        Inicializa el chunker de documentos
        
        Args:
            max_chunk_size: Tamaño máximo del chunk en caracteres (default: Config.STORY_MAX_CHUNK_SIZE)
            strategy: Estrategia de chunking a usar
        """
        # Usar el tamaño máximo por defecto basado en la estrategia
        if max_chunk_size is None:
            # Por defecto usar el tamaño para historias (más conservador)
            max_chunk_size = Config.STORY_MAX_CHUNK_SIZE
        self.max_chunk_size = max_chunk_size
        self.strategy = strategy
    
    def split_document_into_chunks(self, text: str, max_chunk_size: int = None) -> List[str]:
        """
        Divide un documento en chunks de tamaño manejable
        
        Args:
            text: Texto del documento a dividir
            max_chunk_size: Tamaño máximo del chunk (opcional, usa self.max_chunk_size si no se proporciona)
            
        Returns:
            List[str]: Lista de chunks del documento
        """
        if not text or not text.strip():
            return []
        
        chunk_size = max_chunk_size or self.max_chunk_size
        
        # Si el texto es más pequeño que el tamaño máximo, retornarlo completo
        if len(text) <= chunk_size:
            return [text]
        
        # Usar estrategia según el tipo
        if self.strategy == ChunkingStrategy.SMART:
            return self._split_smart(text, chunk_size)
        elif self.strategy == ChunkingStrategy.LINEAR:
            return self._split_linear(text, chunk_size)
        elif self.strategy == ChunkingStrategy.SENTENCE:
            return self._split_by_sentences(text, chunk_size)
        else:
            return self._split_smart(text, chunk_size)
    
    def _split_smart(self, text: str, chunk_size: int) -> List[str]:
        """Estrategia inteligente: divide por secciones, luego párrafos"""
        # Primero intentar dividir por secciones/capítulos
        sections = re.split(
            r'\n\s*(?:[0-9]+\.|\b(?:CAPÍTULO|SECCIÓN|MÓDULO|FUNCIONALIDAD|CHAPTER|SECTION|MODULE|FUNCTIONALITY)\b)',
            text,
            flags=re.IGNORECASE
        )

        chunks = []
        current_chunk = ""

        for section in sections:
            if len(current_chunk) + len(section) < chunk_size:
                current_chunk += section
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = section

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        # Si no hay divisiones claras, dividir por párrafos
        if len(chunks) == 1 and len(text) > chunk_size:
            return self._split_linear(text, chunk_size)

        return chunks
    
    def _split_linear(self, text: str, chunk_size: int) -> List[str]:
        """Estrategia lineal: divide por párrafos/líneas"""
        chunks = []
        current_chunk = ""
        paragraphs = text.split('\n')

        for paragraph in paragraphs:
            if len(paragraph) > chunk_size:
                # Dividir párrafo largo por oraciones
                sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 1 < chunk_size:
                        current_chunk += sentence + " "
                    else:
                        if current_chunk.strip():
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence + " "
            else:
                if len(current_chunk) + len(paragraph) + 1 < chunk_size:
                    current_chunk += paragraph + "\n"
                else:
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                    current_chunk = paragraph + "\n"

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks if chunks else [text]
    
    def _split_by_sentences(self, text: str, chunk_size: int) -> List[str]:
        """Estrategia por oraciones: divide respetando límites de oración"""
        # Dividir por oraciones
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 < chunk_size:
                current_chunk += sentence + " "
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [text]


# Funciones helper para compatibilidad hacia atrás
def split_document_into_chunks(text: str, max_chunk_size: int = None, strategy: str = "smart") -> List[str]:
    """
    Función helper para dividir documentos en chunks (compatibilidad hacia atrás)
    
    Args:
        text: Texto del documento
        max_chunk_size: Tamaño máximo del chunk
        strategy: Estrategia de chunking ('smart', 'linear', 'sentence')
        
    Returns:
        List[str]: Lista de chunks
    """
    try:
        chunking_strategy = ChunkingStrategy(strategy.lower())
    except ValueError:
        chunking_strategy = ChunkingStrategy.SMART
    
    chunker = DocumentChunker(max_chunk_size=max_chunk_size, strategy=chunking_strategy)
    return chunker.split_document_into_chunks(text, max_chunk_size)

